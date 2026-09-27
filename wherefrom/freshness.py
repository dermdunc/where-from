"""Recompute receipts at read time. Nothing is fresh because we assume so.

fresh        the record's content and everything it cites hash the same as
             at build
stale        the record or a cited file has changed since build (including a
             source that no longer reads cleanly)
missing      the record or a cited file no longer exists
unverifiable something cited can't be hashed (a URL, a path that is or now
             resolves outside the sources); we say so rather than pretend

Freshness answers "has what we read changed?". It does not answer "is
the claim true?", and it does not re-run the readers: a fresh fact can be
wrong; it just hasn't moved.
"""
from pathlib import Path

from wherefrom.facts import Fact, sha256
from wherefrom.sources import SOURCES, SourceError

ORDER = ["fresh", "unverifiable", "stale", "missing"]  # worst wins


def current_records(root: Path) -> dict:
    """{source: {record path: sha256}} as the sources stand now; None if a
    source no longer reads cleanly."""
    now = {}
    for name, (records, _, _) in SOURCES.items():
        try:
            now[name] = {path: digest for path, (digest, _) in records(root).items()}
        except SourceError:
            now[name] = None
    return now


def cite_state(root: Path, c: dict) -> str:
    if c.get("unverifiable"):
        return "unverifiable"
    path = (root / c["target"]).resolve()
    if root.resolve() not in path.parents:
        return "unverifiable"  # e.g. now a symlink pointing outside the sources
    if not path.is_file():
        return "missing"
    if c["sha256"] is None:
        return "stale"  # absent when we built, present now: it changed
    return "fresh" if sha256(path.read_bytes()) == c["sha256"] else "stale"


def assess(root: Path, fact: Fact, now: dict) -> dict:
    records = now[fact.source]
    if records is None:
        record = "stale"
    else:
        digest = records.get(fact.source_path)
        record = "missing" if digest is None else ("fresh" if digest == fact.source_sha256 else "stale")
    cites = [{**c, "freshness": cite_state(root, c)} for c in fact.cites]
    overall = max([record] + [c["freshness"] for c in cites], key=ORDER.index)
    return {"record": record, "cites": cites, "freshness": overall}


def not_in_snapshot(built: dict, now: dict, facts: list) -> list:
    """Records the snapshot can't speak for: new since build, or changed
    since build without having produced any fact (so no receipt goes stale).
    Receipts can't cover what was never read, so these are reported apart."""
    covered = {f.source_path for f in facts}
    return sorted(
        path for s, records in now.items() if records
        for path, digest in records.items()
        if path not in built.get(s, {}) or (digest != built[s][path] and path not in covered)
    )
