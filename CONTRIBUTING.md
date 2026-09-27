# Contributing

where-from is an exhibit that goes with a write-up, not a maintained tool. There's no roadmap, and the list of things it deliberately doesn't do (see the README) is part of the point.

Issues are read, but there's no promise of a fix or a reply time. The one bug I will fix is a receipt reporting `fresh` when what it cites has changed; please include the source files that reproduce it. If you try the pattern on your own records, an issue saying what happened is worth more than code.

New source types, storage backends, a query language, embeddings or a server will probably be declined. The write-up explains why.

Run the tests with `python3 -m unittest discover -s tests` (no install, no dependencies).
