# Methodology

How the private lab ran its experiments. You can't re-run them from here: the tasks were drawn from the author's own private repositories. This page exists so you can judge the numbers, and borrow the method.

**Cheap baseline first.** Every expensive idea was measured against the simplest thing that could work (plain access to the repo, or an unranked alphabetical file listing; in E2 and E3a that listing was capped at about 20 files per repository to fit a fixed budget, with a list-directory tool for the rest, so it was never a complete listing) before anything was built on top of it.

**Bars set in advance.** Each experiment wrote down, before any run, what counted as a material effect (+0.15 on a 0 to 1 task score), what counted as noise (0.05), and what each outcome would mean. E3a also set an *inconclusive* band, [0.10, 0.20], on its comparison against the template, so a borderline result couldn't be rounded to whichever answer was more convenient.

**Benchmarks frozen, then rotated.** Tasks were committed before the models saw them. When a result looked good (E1c), the next experiment used fresh tasks and files. That rotation is where the result stopped holding.

**Replicates.** E1b, E1c and E2 ran every task and condition three times with fixed seeds. E3a ran its nine main tasks three times and its three control tasks twice. E1 ran once per cell, and one of its headline figures did not replicate.

**Grading.** Answers were graded against per-task fact lists. E1 was graded unblinded. In E1b, E1c, E2 and E3a the programme that ran the grid also did the grading, with the arm labels hidden. E3a's answers were later re-graded independently: fresh sessions of the same model family as the original grader that saw only the task, the rubric and the answer, and a second model family under the same conditions. Both used the original rubrics, and neither could check cited paths against the repositories. No human graded. The decision held under every grading. Hiding labels did not hide the arm everywhere: on convention-audit tasks a reviewer could tell the arm from the answer alone every time. E1 to E2 were not re-graded.

**Ablations.** When a map had several ingredients, the experiment removed them one at a time. That is how the graph-ranking term was found not to earn its place (+0.012).

**Oracle before classifier.** Before building something to choose a procedure per task, E3a computed the best any chooser among the same three arms could do on those tasks, using hindsight. E3a's rule let the raw oracle decide the build. The reusable version splits it: the raw hindsight ceiling answers "keep investigating?" (check it against shuffled labels, `oracle.py --null`), and the held-out gain (pick on some runs, score on others) answers "fund?". See the [template](../experiments/e3a-public/preregistration.md#a-template-you-can-reuse).

**Separate the verdict from the decision.** The experiment returns PASS, FAIL or INCONCLUSIVE. What to build next is a separate engineering call, and changing a hypothesis's recorded status is a separate human one. Keeping those apart is why E3a reads "inconclusive" and "stopped" at the same time.

**Report the inconvenient cells.** Where a result had a clean win (one needle task for the ranked packet) or a sharp loss (confident false negatives on a census task), it's reported next to the pooled number, not folded into it.

## Try it yourself

The part worth copying is the ordering, not the code: pick the cheapest baseline, write the bar down, run the oracle before you build the thing that approximates it. If the oracle can't clear the bar, you've saved yourself a classifier. If it can, fund on the held-out gain, not the raw one.
