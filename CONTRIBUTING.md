# Contributing

where-from is an exhibit that goes with a write-up, not a maintained tool. There's no roadmap, and the list of things it deliberately doesn't do (see the README) is part of the point.

## One maintainer, irregular replies

This repo has one maintainer, working on it in spare time. Issues are read, but there's no promise of a fix or a reply time, and a quiet week (or month) is not a rejection. Please calibrate accordingly.

## What's useful

- **A false `fresh`.** The one bug I will fix is a receipt reporting `fresh` when what it cites has changed. Please include the source files that reproduce it (the bug report template asks for the commands too).
- **What happened when you tried the pattern.** If you try it on your own records, an issue saying what happened is worth more than code.

New source types, storage backends, a query language, embeddings or a server will probably be declined. The write-up explains why.

## Pull requests

Small and focused, please: one fix per PR, with a test in `tests/test_wherefrom.py` that fails before the change and passes after it. Before opening one, run:

```sh
python3 -m unittest discover -s tests   # no install, no dependencies
./examples/drift-demo.sh                # should still end with the explain output, exit 0
```

Please open an issue first for anything larger than a bug fix, so neither of us wastes time on something that won't be merged.

By contributing you agree that your contribution is licensed under the MIT licence in [LICENSE](LICENSE). Conduct: see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
