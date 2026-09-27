"""build / about / explain / check.

Exit codes: 0 ok, 1 check found stale or missing receipts or records the
snapshot doesn't cover, 2 no snapshot or a
source that won't read, 3 nothing in the snapshot knows the subject (or fact
id), 4 a question no source can answer.
"""
import argparse
import json
import sys
from pathlib import Path

from wherefrom.facts import read_snapshot, write_snapshot
from wherefrom.freshness import assess, current_records, not_in_snapshot
from wherefrom.sources import SOURCES, SourceError

SNAPSHOT = Path(".wherefrom/facts.jsonl")  # relative to where you run it

# Source values reach the terminal. Show control characters (e.g. ANSI escapes planted in a
# catalogue) as visible escapes instead of letting the terminal act on them.
_CONTROL = {c: f"\\x{c:02x}" for c in [*range(32), *range(127, 160)] if c not in (9, 10)}


class _Visible:
    def __init__(self, stream):
        self._stream = stream

    def write(self, text):
        return self._stream.write(text.translate(_CONTROL))

    def __getattr__(self, name):
        return getattr(self._stream, name)


def load():
    if not SNAPSHOT.exists():
        print("no snapshot here: run `python3 -m wherefrom build` in this directory first", file=sys.stderr)
        raise SystemExit(2)
    root, facts, built = read_snapshot(SNAPSHOT)
    now = current_records(root)
    gaps = not_in_snapshot(built, now, facts)
    for path in gaps:
        print(f"note: {path} is new or changed since build and is in no answer. Rebuild to include it.", file=sys.stderr)
    return root, facts, now, gaps


def cmd_build(args):
    root = Path(args.sources)
    facts, records = [], {}
    try:
        for name, (read_records, to_facts, _) in SOURCES.items():
            found = read_records(root)
            records[name] = {path: digest for path, (digest, _) in found.items()}
            facts += to_facts(root, found)
    except SourceError as e:
        print(f"build failed, previous snapshot kept: {e}", file=sys.stderr)
        return 2
    write_snapshot(SNAPSHOT, root, facts, records)
    print(f"built {len(facts)} facts from {len(SOURCES)} sources into {SNAPSHOT}")
    return 0


def cmd_about(args):
    known = {f for _, _, fields in SOURCES.values() for f in fields}
    if args.field and args.field not in known:
        print(f"unsupported: no source records '{args.field}'. "
              f"Fields the sources cover: {', '.join(sorted(known))}")
        return 4
    root, facts, now, gaps = load()
    args.subject = args.subject.strip()
    mine = [f for f in facts if f.subject == args.subject]
    if not mine:
        print(f"unresolved: nothing in the snapshot knows '{args.subject}'")
        return 3
    if args.field:
        mine = [f for f in mine if f.field == args.field]
        asked = [s for s, (_, _, fields) in SOURCES.items() if args.field in fields]
    else:
        asked = list(SOURCES)
    unresolved = [s for s in asked if not any(f.source == s for f in mine)]
    rows = [{"id": f.id, **vars(f), **assess(root, f, now)} for f in mine]
    if args.json:
        print(json.dumps({"subject": args.subject, "facts": rows, "unresolved": unresolved,
                          "not_in_snapshot": gaps}, indent=2))
        return 0
    width = max([len(r["value"]) for r in rows] + [0])
    print(args.subject)
    for r in rows:
        print(f"  {r['field']:<10} {r['value']:<{width}}  {'[' + r['freshness'] + ']':<14} {r['source_path']}  {r['id']}")
    for s in unresolved:
        print(f"  ({s}: nothing for '{args.subject}'{' ' + args.field if args.field else ''}. Unresolved, not invented.)")
    return 0


def cmd_explain(args):
    root, facts, now, _ = load()
    match = [f for f in facts if f.id == args.fact_id]
    if not match:
        print(f"no fact with id {args.fact_id} in the snapshot (ids change when a value changes and you rebuild)")
        return 3
    f = match[0]
    a = assess(root, f, now)
    print(f"{f.id}: {f.subject}.{f.field} = {f.value}")
    print(f"  said by   {f.source}, record {f.source_path}")
    print(f"  read by   {f.extractor}")
    print(f"  receipt   sha256 {f.source_sha256[:12]}... at build -> record is {a['record']} now")
    for c in a["cites"]:
        why = f" ({c['unverifiable']})" if c.get("unverifiable") else ""
        print(f"  cites     {c['target']} -> {c['freshness']}{why}")
    print(f"  overall   {a['freshness']}")
    return 0


def cmd_check(args):
    root, facts, now, gaps = load()
    counts = {}
    for f in facts:
        state = assess(root, f, now)["freshness"]
        counts[state] = counts.get(state, 0) + 1
        if state != "fresh":
            print(f"  {state:<12} {f.id}  {f.subject}.{f.field}  {f.source_path}")
    print("  ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    if gaps:
        print(f"not in snapshot: {len(gaps)} record(s)")
    return 1 if counts.get("stale") or counts.get("missing") or gaps else 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m wherefrom")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="read the sources into a fresh snapshot")
    b.add_argument("--sources", default="examples/sources")
    b.set_defaults(fn=cmd_build)
    a = sub.add_parser("about", help="everything the snapshot says about one subject")
    a.add_argument("subject")
    a.add_argument("--field")
    a.add_argument("--json", action="store_true")
    a.set_defaults(fn=cmd_about)
    e = sub.add_parser("explain", help="the receipt for one fact")
    e.add_argument("fact_id")
    e.set_defaults(fn=cmd_explain)
    c = sub.add_parser("check", help="re-verify every receipt")
    c.set_defaults(fn=cmd_check)
    args = p.parse_args(argv)
    sys.stdout, sys.stderr = _Visible(sys.stdout), _Visible(sys.stderr)
    return args.fn(args)
