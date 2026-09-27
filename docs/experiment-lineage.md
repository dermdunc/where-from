# Experiment lineage

Two hypotheses shared one private lab. They were kept separate on purpose and do not currently share code or data. This page shows how each moved, why each pivot happened, and what survived. All results come from the author's own private repositories and cannot be re-run from this repo.

Setup for the context experiments: local models via Ollama on one 24 GB laptop, `qwen2.5-coder:7b` for E1 and E1b, `devstral-small-2:24b` (Q4_K_M) from E1c on, temperature 0.2, 16k context. No frontier model answered any task. A result had to beat its comparison by **+0.15** on a 0 to 1 task score to count; differences within **0.05** were treated as grading noise. Grading: see [methodology.md](methodology.md).

## H2: can machine-prepared context make a small model more useful?

```
E1   repo map at 7B                    +0.084 vs plain access      below bar
      |  hand-curated context: +0.320 (single runs; +0.233 without a leaky task)
E1b  better map, 3 replicates          +0.094                      below bar; recorded dead as built at 7B
      |  graph-ranking term added +0.012 -> dropped
      |  hand-curated context: +0.311
E1c  same map at 24B                   +0.20 vs a plain listing    cleared the bar, on its own benchmark
      |  (20 of its 54 runs lost to a harness bug; results left as recorded)
E2   new tasks, repaired harness, 24B  plain listing 0.726, maps 0.390 and 0.431
      |  machine map loses by 0.336    -> the E1c gain did not carry over
E3a  oracle routing, 12 fresh tasks    +0.10 vs always-plain (below bar)
      |                                 +0.16 vs always-template (inside pre-set band [0.10, 0.20])
      v
     INCONCLUSIVE (science)  ->  STOP (engineering)  ->  no classifier built
```

**Why each pivot.** E1 missed while hand-curated context passed easily, so the map's content looked like the problem. E1b improved the content and still missed, so the next question was model size. E1c at 24B cleared the bar on its own benchmark, which suggested closing the remaining gap to curated context. E2 tried that on a *rotated* benchmark, with new tasks and a repaired harness, and went the other way: on sweep-shaped tasks the ranked packet pointed the model at a few files and it reached the same wrong conclusion across seeds, while a plain alphabetical listing let it sweep everything. E1c's number stands as measured; because E2 changed tasks and harness together, task shape is the best-supported explanation for the difference, not an isolated one. That pointed at procedure (how to explore) rather than facts (what to read). Before building anything to choose procedures, E3a measured the best case: an oracle that picked, after the fact, which of three procedures scored best on each task.

**What E3a found.** The oracle beat always-plain by +0.10 at 0.91x the cost, below the +0.15 bar. It beat always-template by +0.16 at the same cost: above the bar, but inside the inconclusive band written down before the run for that comparison. The shape-to-procedure mapping chosen in advance agreed with the best arm on 2 of the 9 main tasks.

**Three separate words.** The experiment's verdict is *inconclusive*. The engineering decision was *stop*: a classifier choosing among the same three arms can't beat that oracle on these tasks, so it had nothing to earn. The hypothesis's mechanisation claims were then recorded as disproven, narrowly: the specific mechanisms built here, not context engineering in general, with "curated context helps" kept as a surviving observation. An independent re-grade of every E3a answer (two graders from different model families, plus a design audit) left the verdict and the decision unchanged; see [the E3a evidence](../experiments/e3a-public/).

**One watch item.** On one needle-hunting task the ranked packet scored 1.000 in all three replicates, against 0.333 for the plain listing, under all three gradings; the ranked packet for that task named the file and the exception class outright, so part of that win was handed to the model. On one census task two of three ranked runs stated that several repositories lacked a file they actually had, also under all three gradings. The original grading had ranked packets carrying the most unsupported claims per run overall; the independent re-grades did not (plain had the most), so that grid-level claim is withdrawn. One winning cell is a reason to watch, not to build.

## H1: can structured records be federated with provenance and honest staleness?

```
E3     one real cross-source query            45/45 records matched; answer correct   PARTIAL (not shown cheaper at n=1)
E5     edit + delete under a snapshot         2 stale, 43 fresh, 0 false-fresh        PASS (renames not tested)
E3b-S  SQLite -> JSON lines                   same answers*, 81 vs ~230 backend lines PASS
E3b-U  three real investigations              1 helped, 1 partly, 1 unsupported       PARTIAL
organic use, 30 days                          4 of 8 genuine queries                  gate not passed (as of 2026-09-27)
```

\* equal after normalising run-specific ids.

**Why each step.** E3 checked the join against an answer derived by hand before any code was written (formalised as a file afterwards). It matched, and where one source had no identity for the subject it said "unresolved" instead of inventing a link. E5 asked whether it would ever call changed data fresh; in the two scenarios tested it didn't, and the test found and fixed one real bug in a summary field. E3b asked whether the database was earning its place; the proven queries were two string lookups that didn't need one. E3b-U used it on real questions and found its useful scope was narrow: questions that genuinely span sources. All four organic queries came from one working session.

## What survived

**Usable, and rebuilt in this repo:** joining records across sources with a receipt per fact; recomputing receipts at read time instead of trusting the last build; saying "unresolved" and "unsupported" out loud; a snapshot you can delete and rebuild. The day-one design (federated sources, a SQLite and full-text projection, a context compiler, a graph database held in reserve) came down to this.

**Observations, true in the lab but not built into anything:** hand-curated context helped in all four cycles where it was tested (though on E2's main tier a plain listing matched it inside the noise, 0.726 to 0.702; the curated packets were written by an expert agent). Exploration procedure can matter by task shape in at least one clean cell. Measuring the cheap baseline first decided more than any single result.

**Derived engineering output:** a harness fix. One experiment lost 20 of 54 runs because the harness recorded the model's last tool call as its answer at the turn limit. The repaired harness produced clean answers in 78 runs and then got through a 99-run grid with no infrastructure failures. It hasn't been validated anywhere else, so it isn't published here.

Total: 333 local-model runs across the five H2 grids.
