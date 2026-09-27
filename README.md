# where-from

A small, runnable exhibit. It joins records from two sources that don't know about each other, keeps a receipt for every fact, and tells you when a receipt has gone stale. No model, no database, no service, no dependencies beyond Python 3.11 or newer.

It is a clean-room rebuild, on invented data, of the one pattern that held up, narrowly, in a larger private experiment. The plan there was a federated knowledge layer plus a context compiler for small local models. The evidence cut it down to this. A companion write-up tells the whole story (linked here once published); [`docs/`](docs/) has the short version, including what didn't work.

**This is an exhibit, not a maintained tool.** In the lab it came from, the pattern clearly helped with one of three real cross-source investigations, partly helped with another, and couldn't answer the third: an overall verdict of partial. I'd set a bar of 8 genuine uses in 30 days before treating it as a real tool; as of 27 September 2026 it had 4 against that bar of 8, all from one working session. Read it, run it, borrow the idea. Don't adopt it as infrastructure.

| | |
|---|---|
| **What survived** | Joining structured records across sources with full provenance, re-checking every receipt against the current sources, and saying "unresolved" or "unsupported" instead of guessing. |
| **What didn't** | In the same lab: machine-built context packets for small local models, and a task-routing classifier (never built, because even its best case was inconclusive). The graph database and full-text projection were never needed. See [what-didnt.md](docs/what-didnt.md). |

Also here: per-run scores and a small calculator for the oracle gate, in [experiments/e3a-public](experiments/e3a-public/).
| **What you can run** | The commands below, a drift demo, and the tests. About ten minutes. |

## Run it

```sh
git clone https://github.com/dermdunc/where-from && cd where-from
python3 -m wherefrom build                 # read examples/sources into a snapshot
python3 -m wherefrom about checkout        # everything both sources say about one service
python3 -m wherefrom explain f-da4c0b550b  # the receipt for one fact (ids are in the 'about' output)
python3 -m wherefrom about notify          # one source has never heard of it: reported, not invented
python3 -m wherefrom about billing         # nothing knows it: exit 3, not an empty answer
python3 -m wherefrom about checkout --field on-call   # a field no source records: exit 4, not a guess
./examples/drift-demo.sh                   # change the sources under a snapshot and watch the receipts
python3 -m unittest discover -s tests      # no install needed
```

If you only read one file, read [`wherefrom/freshness.py`](wherefrom/freshness.py). It is about 70 lines and it is the point of the repo.

`about checkout` on the examples looks like this:

```
checkout
  owner      payments-team                                                     [fresh]        catalog.json#checkout  f-d361560a02
  tier       1                                                                 [fresh]        catalog.json#checkout  f-1ebb443f62
  lifecycle  production                                                        [fresh]        catalog.json#checkout  f-969780fbe7
  repo       shop/checkout                                                     [fresh]        catalog.json#checkout  f-1ba65354c8
  decision   ADR-0001 Retry card payments with idempotency keys (accepted)     [fresh]        adr/0001-retry-card-payments.md  f-da4c0b550b
  decision   ADR-0003 Send order emails through the notify service (proposed)  [fresh]        adr/0003-email-via-notify.md  f-fe77c2466b
```

Four facts came from a service catalogue, two from architecture decision records. Neither source knows the other exists. The join happens on the service name, and every line says where it came from. (Both sources sit in one folder here for convenience; the tool reads a single `--sources` root. Joining sources that live in different repos would mean adapting the readers, which this exhibit doesn't do.)

## What it does

`examples/sources/` holds two sources with different shapes: `catalog.json` (one record per service) and `adr/*.md` (decision records with a small `key: value` header, citing code files). Two readers turn them into the same **fact** shape: subject, field, value, source, the record that said it, a sha256 receipt for that record's content, the reader that extracted it, and the hashes of any files it cites.

`build` writes those facts to `.wherefrom/facts.jsonl`. `about`, `explain` and `check` read the snapshot and **recompute every receipt against the live sources**. Each fact comes back as one of:

- `fresh`: the record's content and everything it cites are unchanged since build
- `stale`: the record, or something it cites, has changed (or the source no longer reads cleanly)
- `missing`: the record, or something it cites, is gone
- `unverifiable`: at build time it cited something that can't be hashed (a URL, or a path outside the sources), so it says so

Receipts are per record, not per field. When the `search` entry in the catalogue changes owner, all of search's catalogue facts go stale, including the tier that didn't change. The `checkout` entry's facts stay fresh.

The snapshot is disposable. Delete `.wherefrom/` and rebuild; the answers are the same. It happens to be JSON lines. Nothing about the receipts depends on that.

## What it deliberately doesn't do

- **Tell you whether a fact is true.** `fresh` means "hasn't changed since we read it", not "correct", and the readers aren't re-run. A fresh fact can be wrong.
- Answer free-text questions. There are four commands and one optional `--field`. Anything else is unsupported, and it says so.
- Search, embed, rank, summarise, or call a model. Store anything in a graph or vector database. Run as a service. Act as agent memory or a knowledge platform.
- Detect renames. A renamed cited file reads as `missing`.
- Put records added after `build` into answers. It lists them as not in the snapshot and tells you to rebuild.
- Fuzzy-match names. The join is an exact match on the subject name, after trimming spaces.

Mechanics worth knowing:

- An ADR receipt is the sha256 of the file. A catalogue receipt is the sha256 of that one record's canonical JSON (sorted keys), so reformatting the catalogue without changing a value stays `fresh`.
- A cited file that becomes a symlink pointing outside the sources reads `stale`, and a record file that does the same is refused at build and reads `stale` after it.
- The snapshot is trusted input. Receipts prove the sources haven't changed since *your* build; they don't prove a snapshot someone hands you was built honestly, so don't accept one from anyone you wouldn't let edit your sources. The snapshot also names which files are read and hashed, so a hostile one can make the tool read any file you can read and confirm its contents.
- Control characters in source values (an ANSI escape planted in a catalogue, say) are printed as visible escapes like `\x1b`, not passed to your terminal.
- Run the commands from the directory you built in.
- Exit codes: `0` ok; `1` `check` found stale or missing receipts, or records the snapshot doesn't cover (unverifiable ones are reported but don't fail it); `2` no snapshot, or a source that won't read; `3` nothing in the snapshot knows the subject; `4` a field no source records.

## The experiments behind it

The private lab asked two separate questions under the same rule: measure the cheap option before building the expensive one.

1. **Can records from separate sources be joined with provenance and honest staleness, without a model?** In a small sample, yes: one real cross-source question answered correctly, drift detected in the two scenarios tested (an edit, a deletion), and a narrow usefulness verdict. That pattern is what this repo rebuilds.
2. **Does machine-prepared context let a small local model do more useful work?** Hand-curated context helped in all four cycles where it was tested (though on one benchmark tier a plain file listing matched it, inside the noise). The machine-built versions didn't earn promotion. A final test let an oracle pick, after the fact, the best of three context procedures for each task. It beat always using a capped plain file listing by +0.10 (below the +0.15 bar) and always using a procedural template by +0.16 (inside the inconclusive band set before the run). The science said INCONCLUSIVE. The engineering decision was to stop, so no classifier was built.

The numbers come from the author's private repositories and can't be re-run from here. This repo reproduces the federation *behaviour*, not the experiments. Details: [experiment-lineage.md](docs/experiment-lineage.md), [what-didnt.md](docs/what-didnt.md), [methodology.md](docs/methodology.md). The oracle result's per-run scores, an independent re-grade and a small calculator are in [experiments/e3a-public](experiments/e3a-public/).

## Licence

MIT, see [LICENSE](LICENSE), except `CODE_OF_CONDUCT.md` (CC BY 4.0, adapted from the Contributor Covenant). Found a receipt that says `fresh` when it shouldn't? See [CONTRIBUTING.md](CONTRIBUTING.md).
