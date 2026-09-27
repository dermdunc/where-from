# What didn't work

These results come from the author's private repositories and can't be re-run from this repo. Each was tested on specific tasks, with specific models, against a bar set in advance. None of this says graphs, RAG, bigger models, context engineering or task routing "don't work" in general. It says what happened here.

### A machine-built repo map as context for a small model

- **Why we thought it would work:** small models spend their limited capability rediscovering the repository. Hand them a map and they can spend it on the task.
- **What we tested:** a structural map (files, symbols, a graph-ranked selection) against plain access, at 7B, twice.
- **What happened:** +0.084, then +0.094, against a +0.15 bar. In E1 the model mostly took the map at its word and stopped exploring; in E1b it explored much more, used 2.1x the tokens of plain access and often hit the turn limit. Why it behaved that way wasn't isolated.
- **Why we stopped:** two cycles, two misses.
- **What would reopen it:** a different consumer that can actually use structural context, shown on tasks it wasn't tuned on.

### Graph ranking inside that map

- **What happened:** keeping the graph-centrality term added only +0.012, inside grading noise. It was dropped.
- **Reopen if:** a task set where ranking by structure measurably beats a plain listing.

### A bigger model as the fix

- **Why we thought it would work:** maybe 7B was simply too small to use good context.
- **What happened:** at 24B the same map cleared the bar (+0.20) on its own benchmark (with 20 of 54 runs lost to a harness bug, never re-run). On a rotated benchmark, with new tasks and a repaired harness, it lost to a plain alphabetical file listing by 0.336 on the main tier.
- **Why we stopped:** a gain that doesn't survive new tasks can't be credited to model size. Tasks and harness changed together, so task shape is the likeliest explanation, not a proven one.
- **Reopen if:** a rotated benchmark where the gain survives.

### A better machine packet to close the gap to curated context

- **What happened:** the improved packet recovered about 13% of the gap. Its clearest gain was honesty: in E2, unsupported claims fell from 1.39 to 0.39 per task against the earlier map. (Different experiment from E3a's 0.727 vs 0.515 per run, where ranked packets were the least honest of three arms.) It also scored at least as well as the previous map on 5 of 6 tasks.

### Routing each task to its best context procedure

- **Why we thought it would work:** the curated advantage looked procedural (how to explore), not factual (what to read). Pick the right procedure per task shape and you get the advantage without an expert.
- **What we tested:** an oracle that knew, after the fact, which of three procedures scored best on each of 12 fresh tasks (9 main, 3 controls). For choosing among those three on those tasks, it is an upper bound on any classifier.
- **What happened:** +0.10 over always-plain, below the +0.15 bar. +0.16 over always-template, above it but inside the inconclusive band set in advance for that comparison. The procedure mapping chosen in advance matched the best arm on 2 of 9 tasks.
- **Why we stopped:** INCONCLUSIVE is the scientific answer. STOP is the engineering one: if perfect hindsight can't clearly clear the bar against the cheapest default, a classifier choosing among the same arms won't. The classifier was never written.
- **Reopen if:** a bigger replicate grid that moves the oracle clearly above the bar, or real work repeatedly hitting the one task shape where ranking won.

### A general knowledge platform

- **What we planned on day one:** a federated knowledge layer with a SQLite and full-text projection, a context compiler, and a graph database later.
- **What happened:** the federation question narrowed to cross-source assembly. The compiler had nothing to compile that beat a listing. The graph database was never needed.
- **Reopen if:** questions that need joins, ranges or text search at a scale where a flat file hurts. That hasn't happened.

### General question answering over the lab's records

- **What happened:** the one real question outside the sources' coverage was reported unsupported. Nothing suggested stretching the tool to answer it.
