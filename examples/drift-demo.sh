#!/bin/sh
# Build a snapshot, change the sources underneath it, and watch the receipts.
# Works on a temp copy; your checkout is not touched.
set -eu
HERE=$(cd "$(dirname "$0")/.." && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
cp -R "$HERE/examples/sources" "$WORK/sources"
cd "$WORK"
export PYTHONPATH="$HERE"
wf() {  # only `check` may exit 1 (it found drift); anything else stops the demo
  echo "\$ python3 -m wherefrom $*"; rc=0; python3 -m wherefrom "$@" || rc=$?
  if [ "$rc" -gt 1 ] || { [ "$rc" -eq 1 ] && [ "$1" != check ]; }; then exit "$rc"; fi; echo
}

wf build --sources sources
wf check

echo "# someone raises the retry limit, deletes the notify templates,"
echo "# and the search service changes hands in the catalogue"
echo "MAX_ATTEMPTS = 5" > sources/code/checkout/retry.py
rm sources/code/notify/templates.py
python3 - <<'PY'
import json
p = "sources/catalog.json"
cat = json.load(open(p))
[svc for svc in cat["services"] if svc["name"] == "search"][0]["owner"] = "platform-team"
json.dump(cat, open(p, "w"), indent=2)
PY
echo

wf check
wf about checkout
wf about search
FACT=$(python3 -m wherefrom about checkout --json | python3 -c 'import json,sys; print([f["id"] for f in json.load(sys.stdin)["facts"] if "ADR-0001" in f["value"]][0])')
wf explain "$FACT"
