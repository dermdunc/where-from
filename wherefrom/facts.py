"""The canonical fact, and the disposable snapshot it is stored in.

A fact is one thing one source said about one subject, plus the receipt:
which file (or record inside a file) said it, the sha256 of that record's
content when we read it (file bytes for an ADR, canonical JSON for one
catalogue entry, so reformatting that changes no value isn't drift), which reader extracted it, and the hashes of anything it cites.
The snapshot is a JSONL file you can delete and rebuild at any time; nothing
about the trust semantics depends on it being JSONL.
"""
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class Fact:
    subject: str
    field: str
    value: str
    source: str          # which source family: "catalog", "adr"
    source_path: str     # relative to the sources root; "#name" selects a record
    source_sha256: str
    extractor: str
    cites: list = field(default_factory=list)  # [{"target": ..., "sha256": ... or None}]

    @property
    def id(self) -> str:
        key = "\0".join([self.source_path, self.subject, self.field, self.value])
        return "f-" + sha256(key.encode())[:10]


def write_snapshot(path: Path, sources_root: Path, facts: list, records: dict) -> None:
    """records: {source: {record path: sha256}}, kept so records that are new,
    or changed without producing a fact, can be reported."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as out:
        out.write(json.dumps({"sources_root": str(sources_root), "records": records}) + "\n")
        for f in facts:
            out.write(json.dumps(asdict(f)) + "\n")


def read_snapshot(path: Path):
    lines = path.read_text().splitlines()
    header = json.loads(lines[0])
    facts = [Fact(**json.loads(line)) for line in lines[1:]]
    return Path(header["sources_root"]), facts, header["records"]
