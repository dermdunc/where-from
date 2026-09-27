"""Recompute the E3a oracle gate from scores.csv.

    python3 oracle.py                       # original grades
    python3 oracle.py independent_score_a   # re-grade A (the original grader's model family)
    python3 oracle.py independent_score_b   # re-grade B (a different model family)
    python3 oracle.py --guess guess.csv     # score your own routing guess
    python3 oracle.py --null                # is the hindsight lead more than noise?
    python3 oracle.py --bootstrap           # how much do three replicates pin it down?
    python3 oracle.py --scores other.csv    # a different scores file (same columns)

The grade column and the flags can be combined. guess.csv has two columns,
task_id,arm, with arm one of plain, ranked, template.

The rule is the one written down before the run: build a router only if the
hindsight oracle beats ALWAYS-plain and ALWAYS-template by at least +0.15,
pooled over the nine main tasks, at no more than 1.5x the cost. A template
uplift inside [0.10, 0.20] without passing both is INCONCLUSIVE.

To use your own data, keep these columns (task_id, pooled, replicate, arm,
tokens, and a score column) and mark the tasks that count with pooled=yes.
The arm names and the two defaults are fixed below in ARMS and DEFAULTS;
edit them for other strategies.
"""
import csv
import random
import sys
from pathlib import Path
from statistics import mean

ARMS = ["plain", "ranked", "template"]  # ties go to the first arm in this order
DEFAULTS = ("plain", "template")        # the fixed strategies the oracle must beat
BAR, BAND, MAX_COST = 0.15, 0.05, 1.5
FLAGS = {"--null", "--bootstrap"}
VALUED = {"--guess", "--scores"}


def fail(msg):
    sys.exit(f"oracle.py: {msg} (see --help)")


args = sys.argv[1:]
if {"-h", "--help"} & set(args):
    print(__doc__)
    sys.exit(0)
opts, positional, i = {}, [], 0
while i < len(args):
    a = args[i]
    if a in VALUED:
        if i + 1 >= len(args) or args[i + 1].startswith("--"):
            fail(f"{a} needs a file path")
        opts[a] = args[i + 1]
        i += 2
    elif a in FLAGS:
        opts[a] = True
        i += 1
    elif a.startswith("-"):
        fail(f"unknown option {a}")
    else:
        positional.append(a)
        i += 1
if len(positional) > 1:
    fail(f"expected at most one grade column, got {positional}")

scores_path = Path(opts.get("--scores", Path(__file__).with_name("scores.csv")))
rows = list(csv.DictReader(open(scores_path)))
column = positional[0] if positional else "original_score"
if column not in rows[0]:
    fail(f"no column {column!r} in {scores_path.name}; columns are {', '.join(rows[0])}")
main_tasks = sorted({r["task_id"] for r in rows if r["pooled"] == "yes"})

# runs[(task, replicate, arm)] = score, rounded to 4 dp so exact ties stay exact
runs = {(r["task_id"], r["replicate"], r["arm"]): round(float(r[column]), 4)
        for r in rows if r["pooled"] == "yes"}
replicates = {t: sorted({rep for t2, rep, _ in runs if t2 == t}) for t in main_tasks}


def cell_means(runs):
    return {(t, a): round(mean(runs[(t, rep, a)] for rep in replicates[t]), 4)
            for t in main_tasks for a in ARMS}


def oracle_leads(runs):
    """Hindsight oracle's pooled lead over each default."""
    s = cell_means(runs)
    best = mean(max(s[(t, a)] for a in ARMS) for t in main_tasks)
    return tuple(best - mean(s[(t, d)] for t in main_tasks) for d in DEFAULTS)


score = cell_means(runs)
tokens = {(t, a): mean(float(r["tokens"]) for r in rows if r["task_id"] == t and r["arm"] == a)
          for t in main_tasks for a in ARMS}
oracle = {t: max(ARMS, key=lambda a: score[(t, a)]) for t in main_tasks}

pooled = {a: mean(score[(t, a)] for t in main_tasks) for a in ARMS}
pooled_oracle = mean(score[(t, oracle[t])] for t in main_tasks)
cost_oracle = mean(tokens[(t, oracle[t])] for t in main_tasks)

print(f"grades: {column}   tasks: {len(main_tasks)} main (controls excluded)\n")
for a in ARMS:
    print(f"always-{a:9} {pooled[a]:.3f}")
print(f"hindsight oracle  {pooled_oracle:.3f}   picks: "
      + " ".join(f"{t}={oracle[t]}" for t in main_tasks))

passes = {}
for d in DEFAULTS:
    uplift = pooled_oracle - pooled[d]
    cost = cost_oracle / mean(tokens[(t, d)] for t in main_tasks)
    passes[d] = uplift >= BAR and cost <= MAX_COST
    print(f"oracle vs always-{d:9} {uplift:+.3f} at {cost:.2f}x cost  -> "
          f"{'clears' if passes[d] else 'does not clear'} +{BAR}")

in_band = BAR - BAND <= pooled_oracle - pooled["template"] <= BAR + BAND
if in_band and not all(passes.values()):
    verdict = "INCONCLUSIVE"
elif all(passes.values()):
    verdict = "PASS: the raw ceiling clears the bar; check the held-out gain before funding"
else:
    verdict = "FAIL"
print(f"\nverdict: {verdict}")
if not all(passes.values()):
    print("even perfect hindsight did not clear the bar against every default: "
          "a router that approximates it has not earned its build")

# Held-out oracle: pick each task's arm on the other replicates, score it on the one left out.
held = []
for t in main_tasks:
    for rep in replicates[t]:
        train = {a: mean(runs[(t, r, a)] for r in replicates[t] if r != rep) for a in ARMS}
        pick = max(ARMS, key=lambda a: train[a])
        held.append((runs[(t, rep, pick)], {a: runs[(t, rep, a)] for a in ARMS}))
print("\nheld-out oracle (the number to fund on): "
      + ", ".join(f"vs always-{d} {mean(h[0] - h[1][d] for h in held):+.3f}" for d in DEFAULTS))

if "--guess" in opts:
    guess = {r["task_id"]: r["arm"] for r in csv.DictReader(open(opts["--guess"]))}
    bad = sorted({a for a in guess.values() if a not in ARMS})
    if bad:
        fail(f"unknown arm(s) in guess file: {', '.join(bad)}; use {', '.join(ARMS)}")
    missing = [t for t in main_tasks if t not in guess]
    if missing:
        fail(f"guess file has no row for: {', '.join(missing)}")
    hits = sum(1 for t in main_tasks if guess[t] == oracle[t])
    print(f"\nyour routing guess matched the oracle on {hits}/{len(main_tasks)} tasks "
          f"(ties go to the first arm in {', '.join(ARMS)}; random picks among "
          f"{len(ARMS)} arms average {len(main_tasks) / len(ARMS):.1f})")

if "--null" in opts:
    # Shuffle arm labels within each task and replicate: if the arms were interchangeable,
    # how big a hindsight lead would we see anyway?
    observed = oracle_leads(runs)
    rng, n = random.Random(0), 2000
    null = []
    for _ in range(n):
        shuffled = {}
        for t in main_tasks:
            for rep in replicates[t]:
                vals = [runs[(t, rep, a)] for a in ARMS]
                rng.shuffle(vals)
                shuffled.update({(t, rep, a): v for a, v in zip(ARMS, vals)})
        null.append(oracle_leads(shuffled))
    first = sorted(x[0] for x in null)
    print(f"\nshuffled-label null ({n} shuffles, seed 0):")
    print(f"  observed lead vs always-{DEFAULTS[0]} {observed[0]:+.3f}; shuffled median "
          f"{first[n // 2]:+.3f}; shuffles at least as large: "
          f"{sum(x >= observed[0] for x in first) / n:.0%}")
    print(f"  shuffles clearing +{BAR} vs always-{DEFAULTS[0]}: "
          f"{sum(x[0] >= BAR for x in null) / n:.0%}; "
          f"vs every default: {sum(min(x) >= BAR for x in null) / n:.0%}")

if "--bootstrap" in opts:
    # Resample replicates within each cell: how wide is the hindsight lead from sampling alone?
    rng, n = random.Random(7), 4000
    leads = []
    for _ in range(n):
        m = {(t, a): mean(rng.choice([runs[(t, r, a)] for r in replicates[t]])
                          for _ in replicates[t])
             for t in main_tasks for a in ARMS}
        best = mean(max(m[(t, a)] for a in ARMS) for t in main_tasks)
        leads.append(tuple(best - mean(m[(t, d)] for t in main_tasks) for d in DEFAULTS))
    print(f"\nreplicate bootstrap ({n} resamples, seed 7), 90% interval for the hindsight lead:")
    for k, d in enumerate(DEFAULTS):
        xs = sorted(x[k] for x in leads)
        print(f"  vs always-{d:9} [{xs[int(.05 * (n - 1))]:+.3f}, {xs[int(.95 * (n - 1))]:+.3f}]")
