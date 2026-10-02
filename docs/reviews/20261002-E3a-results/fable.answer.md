## 1. Verdict: **fix** (no revision of the readings needed)

All five registered readings are correct, and almost every number checks out. The fixes are to descriptive wording, one rounding error, and some registered descriptive measures that RESULTS.md leaves out.

I checked by recomputing from `summary.json`, `evaluate.json`, `g1.json`, `champions-3.json` and the `*-started.json` files. I did not rerun the bootstrap intervals, read the `.npz` files, or review `scripts/e3a.py` itself.

## 2. Registered readings: all follow the bound rules

- **S2-a:** one working champion (run 4: lower bound 14.60 against 10.23, clamps 93.0% and 94.1%), so the 1-6 wording "…in 1 of 8 runs, not reliably" is right. Classes are given, as §8 requires.
- **S2-b:** the eight paired differences average −1.49, as I recomputed from the test means. Rule 1 does not apply, the lower bound is not above 0.5, the upper bound is not below −0.5, and the interval is not within ±0.5, so "unclear" is right. The fixed description is quoted correctly.
- **S2-c:** zero qualifiers in both censuses. The screen is 0.8 × 13.0625 = 10.45, and the Clopper-Pearson upper bound 1 − 0.025^(1/1024) = 0.0036. The wording is the registered one, and the "generation 0" clause is correctly not triggered.
- **Stage 3:** +2.36 recomputed; the lower bound 1.32 exceeds 0.5, so "better".
- **B-task:** −3.73 recomputed; the upper bound −1.55 is below −0.5, so "worse". The capacity wording is present.
- **Gates:** every G0 and G1 threshold checks arithmetically.

## 3. Numbers: three to fix

- **Wrong rounding:** the inactive module's |K_D| is given as "0.060 to 0.067". The minimum in `g1.json` is 0.05948, so it should read 0.059.
- **Ambiguous or wrong:** "against 0.5 to 0.7 elsewhere" for nose τ. If it means run 7's other two noses, say so. Across all Stage 3 champions it is false: run 0's A_NL is 0.78 and run 6's A_NR is 1.11 (`champions-3.json`).
- **Traceability:** the τ figures (2.3, 2.39, 2.82) are correct but live only in `champions-3.json`, not in `summary.json` as the header implies. Either cite the file or add them to the summary script.
- **Smaller points:**
  - "12:20 to 18:20" is local time; the records say 10:20 UTC onward. State the zone.
  - Both censuses have a best of exactly 9.8125. That is possible on 16 worlds, but check `census-counts.npz` that they are different draws.
  - "Committed and pushed before the next stage" is not checkable from the files. Calibrate and evaluate start 16 seconds apart, so cite the push log.

Everything else I checked matches, including the champions table, the 0.18 to 0.48 ratios, the E contrasts, 97%, generation 0, the offsets and the compute.

## 4. Descriptive claims

- **"Leaky gate, not lost memory": supported, with one omission.**
  - In all four champions, `hold_detail` shows q at its fixed point to four decimals and the active K_D within 0.01 of its fixed-point value; only the inactive ratio fails.
  - RESULTS.md does not say that all four also fail the release test, for the same gate reason. §6 registers that test for this class, so report it.
  - GA run 4 also fails the two-tick settable test (q ends at −1.18 when set towards A). §6 says the two-tick versions are reported beside the champion's own; they are absent.
  - "Leak" undersells Stage 3 run 3, where the inactive module steers at 48% of the active one. "Partial gate" is more accurate, and these are the top scorers.
- **"Memory-less champions can still score": overreads, and so does "where the memory… lives".**
  - The release test cannot separate a decayed q from a weak gate. `release_detail` records only K_D (the other module at 14 to 26 against an active 27 to 34), not q after D.
  - The records point at q itself. The phase medians of q differ, and clamping q to them gives the right first entry in 82% to 92% of worlds; Stage 3 run 2 passes both.
  - Stage 3 run 2 has τ_q 4.9 and w_qq 0.95. By my calculation from those parameters (not measured), its effective time constant near q = 0 is about 96 ticks, longer than D = 39. It may be a slow trace behind a partial gate.
  - Stage 3 mutates only existing edges, so q's self-loop is the only recurrence in the brain. "Elsewhere" can only mean the body and world.
  - Fix: retitle to "champions classed 'no memory'", state the confound, and drop the presupposition from the "cannot show" list.
  - Stage 3 run 7 is the one real case: both modules fully on (28.3 and 27.6), clamps not applicable, 14.50 visits. Say so separately.
- **Mean-nose: numbers right, wording loose.**
  - "Uses" is E2d's rule-bound term, and no intervals are given for the champions. Prefer "every champion's score depends on each module's left-right difference".
  - "Every champion" excludes B-task; "selector champions" silently includes Stage 3.
  - The run 7 hedge is appropriate.
- **GA against random sampling: honest, needs three additions.**
  - "7 of 8" for random sampling is descriptive, not a registered reading; label it.
  - Five GA runs end where they began (final checkpoints 7.2 to 8.4 against first 7.8 to 8.2, the ungated level). That is a fact worth stating.
  - GA runs 2 and 3 outscore or match most random-sampling champions, and miss "working" only on clamp assays at calibration medians. So the 1-against-7 contrast rests partly on the assay, not on score.
- **"Four tuned organisms beat E":** there is no paired test, and the untuned GA run 4 (14.98) also exceeds E. Write "scored above E's mean" and include it.

## 5. Deviations: honest but incomplete

- **Deviation 1:** "E and every rule were bound" omits that Amendment 1 was written after the peek. Add that no amendment item uses D or the level duration, which is true on my reading of §13.
- **Deviation 3:** it is stated plainly, which is good. Add that the rewritten runner which produced these numbers was never reviewed, and whether the §11 item 23 smoke of every stage was rerun after the rewrite. Either this results review covers the runner or that gap stays open; I did not cover it.
- **Missing from RESULTS.md:** the two-tick assays, the hysteresis sweep, module skill, the per-tick turn contributions, and B-shared's component tests are registered descriptive measures (§6, §8, Amendment 1). They are in the records but not reported or pointed to. Add a short pointer section, or list them as not written up.