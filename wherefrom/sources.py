"""Two readers for two differently shaped sources.

- catalog.json: a service catalogue a platform team maintains (one record
  per service).
- adr/*.md: architecture decision records, with a small key: value header.

Each source has two halves. `records` lists every record with the hash of
what was read; build uses it, and so does every freshness check, so the two
can never disagree about what a record is. `facts` turns records into the
canonical fact shape. Neither source knows the other exists; the join
happens later, on the subject name (exact match after trimming spaces).
"""
import json
from pathlib import Path

from wherefrom.facts import Fact, sha256

CATALOG_FIELDS = ("owner", "tier", "lifecycle", "repo")


class SourceError(Exception):
    """A source can't be read cleanly. Build refuses; checks report stale."""


def catalog_records(root: Path) -> dict:
    try:
        services = list(json.loads((root / "catalog.json").read_text())["services"])
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise SourceError(f"catalog.json: can't read services ({e})")
    records = {}
    for svc in services:
        name = svc.get("name") if isinstance(svc, dict) else None
        if not isinstance(name, str) or not name.strip():
            raise SourceError("catalog.json: every service needs a string 'name'")
        key = f"catalog.json#{name.strip()}"
        if key in records:
            raise SourceError(f"catalog.json: duplicate service name '{name.strip()}'")
        # The receipt is the sha256 of the record's canonical JSON, so a change
        # to one service doesn't make every other service stale.
        records[key] = (sha256(json.dumps(svc, sort_keys=True).encode()), svc)
    return records


def catalog_facts(root: Path, records: dict) -> list:
    return [
        Fact(subject=key.split("#", 1)[1], field=name, value=str(svc[name]),
             source="catalog", source_path=key, source_sha256=digest,
             extractor="catalog-reader/1")
        for key, (digest, svc) in records.items()
        for name in CATALOG_FIELDS if name in svc
    ]


def parse_header(text: str) -> dict:
    """Read the '---' delimited key: value header. Lists are comma-separated."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing '---' header")
    header = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return header
        key, colon, value = line.partition(":")
        if line.strip() and not colon:
            raise ValueError(f"header line without ':': {line.strip()!r}")
        if line.strip():
            header[key.strip()] = value.strip()
    raise ValueError("unterminated header")


def adr_records(root: Path) -> dict:
    if not (root / "adr").is_dir():
        raise SourceError(f"adr/: not a directory under {root}")
    records = {}
    for path in sorted((root / "adr").glob("*.md")):
        rel = str(path.relative_to(root))
        try:
            raw = path.read_bytes()
            header = parse_header(raw.decode("utf-8-sig"))
        except (OSError, ValueError) as e:
            raise SourceError(f"{rel}: {e}")
        missing = [k for k in ("id", "title", "status", "services") if not header.get(k)]
        if missing:
            raise SourceError(f"{rel}: header missing {', '.join(missing)}")
        records[rel] = (sha256(raw), header)
    return records


def cite(root: Path, target: str) -> dict:
    """Hash a cited file. URLs and anything outside the sources root can't be
    checked, so they are recorded as unverifiable rather than trusted."""
    if "://" in target:
        return {"target": target, "sha256": None, "unverifiable": "not a file"}
    path = (root / target).resolve()
    if root.resolve() not in path.parents:
        return {"target": target, "sha256": None, "unverifiable": "outside the sources root"}
    return {"target": target, "sha256": sha256(path.read_bytes()) if path.is_file() else None}


def split(value: str) -> list:
    return list(dict.fromkeys(v.strip() for v in value.split(",") if v.strip()))


def adr_facts(root: Path, records: dict) -> list:
    facts = []
    for rel, (digest, header) in records.items():
        cites = [cite(root, t) for t in split(header.get("cites", ""))]
        value = f"{header['id']} {header['title']} ({header['status']})"
        for subject in split(header.get("services", "")):
            facts.append(Fact(
                subject=subject, field="decision", value=value, source="adr",
                source_path=rel, source_sha256=digest, extractor="adr-reader/1", cites=cites,
            ))
    return facts


# name -> (records, facts, fields it can answer)
SOURCES = {
    "catalog": (catalog_records, catalog_facts, CATALOG_FIELDS),
    "adr": (adr_records, adr_facts, ("decision",)),
}
