"""Recompute the E3a oracle gate from scores.csv.

    python3 oracle.py                       # original grades
    python3 oracle.py independent_score_a   # re-grade A (fresh Claude sessions)
    python3 oracle.py independent_score_b   # re-grade B (Codex, a different model family)
    python3 oracle.py original_score --guess guess.csv   # score your own routing guess

guess.csv has two columns, task_id,arm (arm is plain, ranked or template).

The rule is the one written down before the run: build a router only if the
hindsight oracle beats ALWAYS-plain and ALWAYS-template by at least +0.15,
pooled over the nine main tasks, at no more than 1.5x the cost. A template
uplift inside [0.10, 0.20] without passing both is INCONCLUSIVE.
"""
import csv
import sys
from statistics import mean

ARMS = ["plain", "ranked", "template"]  # ties go to the first arm in this order
BAR, BAND, MAX_COST = 0.15, 0.05, 1.5

column = next((a for a in sys.argv[1:] if not a.startswith("--") and not a.endswith(".csv")),
              "original_score")
rows = list(csv.DictReader(open("scores.csv")))
main_tasks = sorted({r["task_id"] for r in rows if r["pooled"] == "yes"})


def cell(task, arm, key):
    return mean(float(r[key]) for r in rows if r["task_id"] == task and r["arm"] == arm)


score = {(t, a): cell(t, a, column) for t in main_tasks for a in ARMS}
tokens = {(t, a): cell(t, a, "tokens") for t in main_tasks for a in ARMS}
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
for a in ("plain", "template"):
    uplift = pooled_oracle - pooled[a]
    cost = cost_oracle / mean(tokens[(t, a)] for t in main_tasks)
    passes[a] = uplift >= BAR and cost <= MAX_COST
    print(f"oracle vs always-{a:9} {uplift:+.3f} at {cost:.2f}x cost  -> "
          f"{'clears' if passes[a] else 'does not clear'} +{BAR}")

in_band = BAR - BAND <= pooled_oracle - pooled["template"] <= BAR + BAND
if in_band and not all(passes.values()):
    verdict = "INCONCLUSIVE"
elif all(passes.values()):
    verdict = "PASS: the oracle earned a router"
else:
    verdict = "FAIL"
print(f"\nverdict: {verdict}")
if not all(passes.values()):
    print("even perfect hindsight did not clear the bar against both defaults: "
          "a router that approximates it has not earned its build")

# Held-out oracle: pick each task's arm on two replicates, score it on the third.
held = []
for t in main_tasks:
    for rep in ("1", "2", "3"):
        train = {a: mean(float(r[column]) for r in rows if r["task_id"] == t and r["arm"] == a
                         and r["replicate"] != rep) for a in ARMS}
        pick = max(ARMS, key=lambda a: train[a])
        test = {r["arm"]: float(r[column]) for r in rows if r["task_id"] == t and r["replicate"] == rep}
        held.append((test[pick], test))
print(f"\nheld-out oracle (a fairer stand-in for a real router): "
      f"vs always-plain {mean(h[0] - h[1]['plain'] for h in held):+.3f}, "
      f"vs always-template {mean(h[0] - h[1]['template'] for h in held):+.3f}")

if "--guess" in sys.argv:
    path = sys.argv[sys.argv.index("--guess") + 1]
    guess = {r["task_id"]: r["arm"] for r in csv.DictReader(open(path))}
    hits = sum(1 for t in main_tasks if guess.get(t) == oracle[t])
    print(f"\nyour routing guess matched the oracle on {hits}/{len(main_tasks)} tasks "
          f"(random picks among three arms average {len(main_tasks) / 3:.1f})")
