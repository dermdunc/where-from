# E3a: the oracle gate, with its numbers

The companion write-up describes an experiment (E3a) that asked whether routing each task to its
best context procedure was worth building a classifier for. This folder publishes the minimum
needed to check that decision yourself: the per-run scores and a small calculator. It does not
reproduce the experiment. An *arm* is one context procedure: `plain`, `ranked` or `template`
(defined in `preregistration.md`).

## What is here

- `scores.csv`: one row per run (99 rows). Task label and type, whether it counts towards the
  decision, replicate, arm, token count, and three scores for the same frozen answer:
  - `original_score`: graded by the programme that ran the grid, arm labels hidden.
  - `independent_score_a`: re-graded later by fresh sessions of the same model family as the
    original grader, which saw only the task, the rubric and the answer.
  - `independent_score_b`: re-graded by a different model family under the same conditions.
  - `original_unsupported`, `unsupported_a`, `unsupported_b`: unsupported claims (concrete false
    assertions) each grader found. No human graded.
- `oracle.py`: standard-library Python. Computes each fixed strategy's mean, the hindsight oracle,
  its uplift over the defaults, the registered bar and verdict, and a held-out oracle.
- `preregistration.md`: what was fixed before the run, and what was added afterwards.
- `example-guess.csv`: the routing guess written down before the run, in the calculator's format.

## Run it

```text
cd experiments/e3a-public
python3 oracle.py                        # original grades
python3 oracle.py independent_score_a
python3 oracle.py independent_score_b
python3 oracle.py --guess example-guess.csv
python3 oracle.py --null                 # shuffled-label check (see below)
python3 oracle.py --bootstrap            # 90% interval from resampling replicates
```

Run from anywhere; `--scores` points it at another file with the same columns. To use it on
your own strategies, edit `ARMS` and `DEFAULTS` at the top of `oracle.py`; the pre-registration
template below needs no edits.

Replace `example-guess.csv` with your own task-to-arm guesses to see how a hand-written routing
table would have done against the oracle, and against random picks.

## Is the hindsight lead more than noise?

A best-of-three pick always looks better than any single arm, even when the arms are
interchangeable. `--null` shuffles the arm labels at random within each task and replicate, many
times, and recomputes the oracle's lead. If shuffled labels produce a lead as large as the real
one, the real lead is not evidence that the arms differ by task. On these scores the shuffled
median is about as large as the observed lead over always-plain. This is also why the gate requires
beating *every* default, not just one: noise alone clears the bar against one default more often
than against all of them.

## What the numbers support

Under all three gradings the oracle beats always-plain by about +0.10 to +0.11, below the +0.15
bar. Against always-template it clears the bar narrowly under the original grades (+0.163) but not
under either re-grade (+0.133, +0.131). The verdict is INCONCLUSIVE by the rule fixed in advance.
The rule's kill clause (do not
build if the oracle misses the bar against either default) applies under every grading, so the
classifier was not built. The held-out oracle, which picks each task's arm from the other
replicates, is the fairer stand-in for a real router and earns much less: roughly +0.00 to +0.05
over always-plain. The pre-written routing guess matched the oracle on 2 or 3 of 9 tasks (ties broken
plain, ranked, template; counting ties as matches, up to 4); random picks average 3.
Resampling the three replicates per cell (`--bootstrap`) puts the 90% interval for the
oracle's lead over always-plain at about +0.05 to +0.20 under every grading: either side of the
bar, which is what inconclusive looks like.

Unsupported claims (concrete false assertions, counted only where the rubric could adjudicate
them) cut against the plain listing: under both independent re-grades it drew the most per run across all 99 runs (same order on the
nine main tasks alone)
(A: plain 0.82, ranked 0.73, template 0.45; B: 2.12, 1.61, 1.33). The original grading had put
ranked highest; that finding did not survive. Absolute counts differ a lot between graders, so
only the ordering is worth reading.

## What it does not show

- The tasks came from private repositories. Task subjects, prompts, model answers, packets and
  rubrics are not published, so you cannot re-run the experiment or re-grade the answers.
- Three replicates per cell at temperature 0.2 is small; some cells range from 0.00 to 1.00.
- The graders could not inspect the repositories to confirm cited paths, only judge them against
  the rubric.
- A separate design audit found biases, most pushing toward a PASS that did not happen: the
  hindsight oracle's winner's-curse; a template arm given a short generic procedure while the
  other arms got a file map; ranked packets that contained some rubric facts verbatim; a plain
  listing capped at about 20 files per repository, whose alphabetical cut-off favoured plain on the
  tasks it happened to surface; and a nine-task mix chosen to suit
  routing.
- On convention-audit tasks, a reviewer could identify the arm from the answer alone every time,
  so "blind to arm" did not hold there.
- One model, ten small repositories, one benchmark. None of this says routing, ranking or
  retrieval don't work elsewhere.

## Try the sweep comparison on your own code

A methodology sketch, not a benchmark claim. Pick three "find every X across these repos"
questions whose full answer you know. Run your agent on each three times with (1) an unranked
listing that names everything in scope (the lab's was capped at about 20 files per repository,
with a list-directory tool available to both arms), and (2) your ranked context. Count missed
items per answer, and note whether the same wrong answer repeats across runs. The lab never
tested a complete listing, or any listing at monorepo scale; nothing here tells you which cheap
baseline to use there.
