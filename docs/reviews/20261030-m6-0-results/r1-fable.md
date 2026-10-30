**Verdict: fix then publish.** The records support every reading and every number the reader writes. The one table the reader does not write, "How the effect fades", is not traceable and two of its entries differ from what the committed records give. The interpretation needs one qualifier in two places.

## 1. Numbers

**Verified against the records (all match):** the switch counts by tag, family and mapping; the four switch comparisons and their intervals; the four persistence comparisons, runs skipped, and the restricted τ_stay medians; censored and below-floor counts; the consistency check (120 of 120, max relative 1.8e-4); both audits; the 16 seen-before genomes; the g79 cases; the "beside 02b" medians (I re-derived 0.169, 0.035, 40.5, 45.5 and the two drift medians 0.023 and 0.035 from the 24 runs); the first-pass seconds (903.9 and 798.6); the CPU hours; the summary.json entry.

**The 12 non-fading genomes:** the list is complete and correct. I rebuilt the row index map, checked each first-pass class in the run log, each second-pass record in both second-*.json files, and all 24 a values on both banks. All match the draft, including the two "unresolved → fading" arrows.

**The "after the data" table:** I re-derived it by hand from first-own.json.

| Entry | Draft | From the records (eligible genomes) |
|---|---|---|
| g39: a, d5/a, d30/a, d100/a, d30, d100, returns | all | all match exactly (0.161, 0.85, 0.20, 0.0039, 0.0262, 0.00050, 5 of 102) |
| g00: d5/a, d30/a, d100/a, d30, returns | all | match (0.79, 0.23, 0.0068, 0.0064, 16 of 99) |
| g00: a | 0.028 | **0.029** over the 99 eligible; 0.028 is the median over all 102 |
| g00: d100 | 0.00015 | **0.00016** over eligible (the 50th of 99 is 0.000157) |
| drift: a, d5/a, d100/a, returns | all | match (0.026, 0.79, 0.0088, 116 of 401) |
| drift: d30/a | 0.25 | **0.24** over the 401 eligible (203 values lie below 0.25; the 201st is 0.2446) |
| drift: d30, d100 | 0.0060, 0.00026 | not checked (802 products) |

The pattern suggests the table was computed over all genomes, including the 10 below the start floor, from the local states, while its header says "eligible genomes". The differences are one unit in the last digit and change nothing, but reading.json does not hold these medians and no committed script produces them, which breaks rule 5. **Fix:** add them to the reader's output over the eligible rows (the plan's floor), regenerate the table from reading.json, and say the population in the header.

**Also untraceable:** "about 15 and 12 minutes" for the second pass and the derived "about 28 s a genome". No record holds those minutes; second-*.json has no seconds field. What the records give is 3445 − 904 − 799 = 1742 s for the genome and bank stages plus the 57 second-pass genomes. Quote that, or say the per-bank times came from the console and were not logged.

## 2. The readings

The reader applies the plan as written. The inconclusive branch covers all four registered causes, in the registered precedence; enrichment requires at least 5 switches and an interval above zero at both unresolved bounds, which is the plan's straddle test; the negative wording is verbatim with N = 1; persistence maps the interval's sign to the three fixed phrases; a secondary-only positive would be reported as input dependence. The sabotage tests the plan promised exist in tests/test_memory_m6.py.

"Shortened" is supported by the registered rule: the primary interval (−0.170, −0.013) lies below zero. Two things the draft should say beside it, because the rule makes them invisible:

- The seven censored drift replicates (drift's switches and unresolved genomes) rank above every fading champion by the registered rule, so part of "shortened" is "drift has more non-fading genomes", not "drift's fading genomes fade slower". My rough estimate is that they contribute between −0.01 and −0.03 of the −0.095 mean. One sentence, and optionally a fading-only version marked exploratory.
- The upper bound sits at −0.013. The reading is by the rule, but the draft should not describe it as more than that.

## 3. Overclaiming

The interpretation is mostly fair, but the caveat is not stated where it matters most. "In short" does say "measured relative to its size", but the roadmap paragraph says flatly "selection on T1 made the history effect larger, not longer-lived." That is only true in the relative measure. In absolute terms the champions' difference is larger at every reported tick (about 4× drift's at tick 30, about 2× at tick 100), so under any fixed absolute threshold the effect would outlast drift's. **Fix:** add "relative to its size" there, and state the absolute-threshold reading in one sentence.

Two further points:

- **"Fades more cleanly"** (5 of 102 return above 10% against 116 of 401) is confounded by a. The threshold is 0.1a, about six times smaller in absolute terms for drift, so a small absolute wobble flips drift's flag but not the champions'. Add that caveat or cut the sentence.
- **The relative-threshold mechanism deserves naming.** A slow absolute-scale component of similar size in all genomes would, by itself, make large-a genomes read "shortened" under τ_stay. The draft hints at it; say it once, plainly.

"Fast fading", "a transient of a few tens of ticks", and "whether it is used in the task is a question for behaviour" are supported. "About six times larger" is 02b's result restated and holds here (0.161 against 0.026 and 0.028).

## 4. The roadmap step

Options 3 or 4 is the plan's branch and the right one. Options 5 and 2 were conditional on enrichment, which failed by a wide margin. Option 1 was already at most a side panel. I would lean to 4 unless the owner wants the biology anchor, since the thread now has a clean negative with a short transient as its subject.

## 5. Fixes before publishing

1. Make the "How the effect fades" table traceable: write its medians and returns counts into reading.json over eligible genomes, re-quote (g00 a 0.029, drift d30/a 0.24, g00 d100 0.00016, the drift absolute d's as the script gives them), and label the population.
2. Replace the second-pass minutes and "28 s a genome" with the figure the records support, or state the source.
3. Add "relative to its size" to the roadmap paragraph and the absolute-threshold sentence beside it.
4. Caveat or cut "fades more cleanly".
5. One sentence on the seven censored drift replicates in the persistence reading.

Nothing I found changes the reading, the wording, or the next step.