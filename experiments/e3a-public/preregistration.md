# E3a pre-registration (public subset)

## Fixed before any model ran

Committed to the private lab's history on 2026-09-26 at 07:27. The benchmark and packets were
frozen by 08:06 and the first model output was written at 08:41. What follows restates that
record without private task subjects.

**Question.** If you knew in hindsight which of three context procedures works best for each
task, would always picking that procedure beat simply using one procedure for everything, by
enough to justify building a classifier that tries to pick it in advance?

**Arms.** One local model (24B coder model, via Ollama) answers every task three ways, each with
the same file-reading tools:
- `plain`: an unranked, alphabetical listing of the files in scope, capped at about 20 files per
  repository to fit the context window (the rest reachable through the list-directory tool). It
  was not a complete listing.
- `ranked`: a ranked packet of the files judged most relevant to the task, with extracted leads.
- `template`: a generic step-by-step exploration procedure for the task's type, naming no files.

**Population.** 12 tasks: 9 main tasks (3 census-sweep, 3 convention-audit, 3 needle-discovery)
and 3 controls (2 mechanical lookups, 1 synthesis). Controls are diagnostic only and never
pooled into the decision. 3 replicates per main-task cell, 2 per control cell: 99 runs (the plan's
stated reduced grid; the full grid would have been 108).

**Oracle.** Per task, the arm with the highest mean score, chosen after the fact. Pooled over the
9 main tasks.

**Bar.** The oracle must beat BOTH always-plain AND always-template by at least +0.15 (task score
on a 0 to 1 scale), at no more than 1.5x the cheaper baseline's token cost.

**Kill rule.** If the oracle cannot clear the bar against either baseline, do not build a
classifier. Clearing it against always-plain only is not a pass: that just means "always use the
procedure".

**Inconclusive band.** If the oracle's uplift over always-template lands in [0.10, 0.20], or more
than 15% of runs fail the harness protocol, report INCONCLUSIVE rather than forcing a pass or
fail, and escalate to a human.

**Scoring.** Each task has a list of expected facts. found = 1.0 (stated correctly with a real
supporting path), partial = 0.5, missed = 0. Task score = sum / number of facts. Unsupported
claims (concrete false assertions) are counted separately and never netted against the score.

**Diagnostic, not the decision.** A pre-written guess of which procedure each task type needs:
census-sweep -> plain, convention-audit -> template, needle-discovery -> ranked.

## Added after the run (not pre-registered)

- The hindsight-oracle computation's tie rule (ties go to the first arm in plain, ranked,
  template order) is the analysis code's; it was frozen before results but is not stated in the
  plan text.
- The independent re-grade (grades A and B), the held-out oracle, the replicate bootstrap, the
  construction-bias audit and the arm-detectability test were all added on 2026-09-27, after the
  original verdict. Their own design was registered before any new grade existed.
- The +/-0.05 band was a setting, not a measured noise level.

## A template you can reuse

```text
Question:        Would perfect hindsight among <strategies> beat <cheapest default> by enough to build a selector?
Arms:            <strategy A>, <strategy B>, <strategy C>   (same tools, same instructions, comparable context size)
Cheapest default: <the simplest thing that keeps everything visible>
Population:      <tasks>, <replicates per cell>, <which tasks are controls and excluded>
Bar:             oracle beats <each default> by >= <X> at <= <Y>x cost, pooled over <tasks>
Inconclusive:    <band around the bar, and any data-quality trigger>
Stop / build:    raw oracle below the bar against any default -> stop (not enough upside to pursue)
Null check:      the same oracle on shuffled strategy labels; a raw lead no bigger than that is noise
Fund on:         the held-out gain (pick on some runs, score on others) against the same bar;
                 clearing the raw ceiling is necessary, not sufficient
Written down on: <date, commit>, before any result exists
```
