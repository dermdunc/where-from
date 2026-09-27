**What this changes, and why**

<!-- Link the issue if there is one. Anything larger than a bug fix should have one first. -->

**Checklist**

- [ ] `python3 -m unittest discover -s tests` passes
- [ ] `./examples/drift-demo.sh` runs to the end and exits 0
- [ ] A test in `tests/test_wherefrom.py` fails without this change and passes with it (for a bug fix)
- [ ] No new dependencies beyond the Python 3.11+ standard library
- [ ] Doesn't add something the README lists under "What it deliberately doesn't do" (or explains why it should)
- [ ] Example data is invented, not real records
