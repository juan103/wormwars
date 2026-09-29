# Review of 03m's results

**Verdict: fix.** The runs followed the plan and every number in RESULTS.md recomputes from the JSON. The problems are in the reading: four claims are contradicted by the committed outputs, and one of them (gap junctions) reverses a headline.

## 1. Did the runs follow the plan?

Yes, as far as I can verify.

| Check | Result |
|---|---|
| Order | graphs, synapses, weights, decay, lesions (`compute-record.json`) |
| Commits | Stamps match RESULTS.md; all `dirty: false`, 2 048 genomes, cuda |
| Pushed before start | Each commit's push precedes its attempt's timestamp, from the local reflog of `origin/roadmap`, not GitHub's log |
| Reproduction | N2 relative difference 0.0 in all four files; all 81 graphs in `decay.json` at 0.0 |
| Empty deletion | Identical to intact to the last digit |
| Composition | `per_chunk` 2 048, `[2048, 1, …]` recorded |
| Compute | 11 962.9 s = 3.32 h; 5 attempts, 0 failed |
| Lesion set | 390 rows = 1 + 95 pairs + 294 singles, all valid; follow-up picks the five lowest singles correctly |

**Not verified:**
- **Guarded files unchanged.** I cannot run `git diff`, and `p4m.py` never calls `require_same_code`, so nothing machine-checked it. The commit subjects between `66edaee` and `a3f2ec1` are all documents, and N2's gaps-off values are identical in `synapses.json` and `decay.json`, which supports the claim indirectly.
- **Smoke runs on the merged code.** `runs/p4m-smoke/` is no longer present, and RESULTS.md does not say whether they were repeated after the merge.

## 2. Are the numbers right?

Yes. I recomputed the tables for Q2 to Q5 by hand from the JSON, including the Q5 shares (27/64, 29/64, 59/64), Q4's median and ranks, and the gaps-off ranges (0.051-0.143, 0.006-0.029). I found no numerical error. The figures I derive below are also hand-computed; re-derive them by script before quoting.

## 3. Must-fix

Make these as dated corrections, since RESULTS.md and D113 are pushed.

1. **Gap junctions: the reading runs against the plan's own rule.**
   - The plan says gaps off matters if N2's change lies outside the null range. It does: +0.014 against 0.051-0.143.
   - Intact, N2 (0.931) is above all 80 panel graphs; the highest is SH-mirror-40007 at 0.898.
   - With gaps off in both, N2 (0.945) is exceeded by 5 of 80: SH-route-20005 (0.952) and SH-mirror-40001, -40002, -40007 and -40015 (0.947-0.955).
   - The panel median rises from about 0.82 to about 0.91, so N2's margin over it falls from about 0.11 to about 0.04.
   - "Gap junctions are not needed for either property" holds for N2's absolute values only. "Not tied to a synapse type" does not hold for the elevation over the shuffles. N2's response does stay distinctive (0.143 against a panel maximum of 0.082).

2. **"Brings it down to the shuffles' typical level, and so does deleting the RIA pair or the AIY pair" is wrong for the deletions.**
   - RIA pair: 0.049, above 94-100% of graphs in each ensemble.
   - AIY pair: 0.061, above 97-100%.
   - Both are under the pooled maximum but more than twice the median. Only the all-weights permutation reaches the typical level. This is in "In brief" and D113.

3. **"The high P4 survives all of those" contradicts `weights.json`.**
   - Under the plan's classes, 37 of 64 independent and 35 of 64 paired permutations are "both".
   - The median drop (0.046) is about twice the largest deletion effect (0.024).
   - This affects "In brief", the README status ("every … weight permutation tested"), "Reading it together" and D113. Q5's own section is worded correctly.

4. **"They have different sources" is not shown.**
   - P4 is a ratio. Under the RIA-pair deletion the numerator falls 62% and the denominator 62%; under AIY, 53% and 53%.
   - The absolute history signal depends on RIA and AIY as much as the response does.
   - "Distributed" is an inference from negative results. What is supported is that no single or bilateral-pair deletion lowers the ratio below the threshold.

5. **"Settle with the difference intact" is not what was measured.**
   - The criterion is more than 10% remaining.
   - The null comparison is missing: SH-10007 has 171 such genomes and SH-mirror-40003 has 37, against N2's 26.
   - SH-10007's P4 is an unremarkable 0.867, so this property and P4 are not the same thing.

6. **The saturation sentence is unsupported as worded.** A lower tanh slope compresses the read-out; it does not show that part of the response "is in this final step". The stronger fact is understated: N2's 0.44 is below all 80 null graphs (0.66-0.80), not only below their median.

7. **The 03m README body is stale.** It still says "What runs next", gives the 3.6-hour estimate, and its Files table lacks RESULTS.md and the four outputs.

## 4. Suggestions

- Record the output of the guarded-path diff in RESULTS.md, and say whether the smoke runs were repeated after the merge.
- Report Q4 by ensemble. SH-mirror and SH-recip relax far more slowly than SH (medians about 2.5% and 1.5% against 0.08%), and N2 is near their top, not apart from them.
- N2's curve is flat from about tick 200, so "relaxes more slowly" mixes a rate with a plateau. Half-times from the committed curves would separate them.
- Report Q5 by ensemble; the share above each ensemble's 95th percentile runs from 28% to 75%.
- Q3's "mostly above" rests on 8 seeds that are favourable: 6 of 8, against 45% over the 64.
- "The placement of the weights adds to it" rests on 59 of 64; say that instead.
- The root README (lines 36, 133) and ROADMAP.md (line 51) still say the simulations are running.
- RESULTS.md was committed about two minutes after the lesions run ended. The overclaims are all in the summary sections, which may deserve a slower second pass.

## 5. What a confirmatory follow-up should register

Use fresh genomes (a new salt, as 03r did), null graphs outside this panel, and thresholds from matched manipulated nulls.

1. **Gaps off, first.** N2's P4 with gaps off against each ensemble's with gaps off, by 03's rank test, with wording fixed for both outcomes. About 2.3 GPU-hours for 640 graphs. This decides how much of 03's finding is about gap junctions.
2. **RIA and AIY.** A response reduction of at least 40% with a P4 change within 0.02. Controls: degree-matched random pairs in N2, and the same pairs in null graphs. Add the double deletion.
3. **Weight placement.** N2's exact rank among at least 256 fresh permutations.
4. **Residual at 300 ticks.** Per-ensemble ranks with at least 64 graphs each, and an absolute size for "settled with separation".
5. **P4 on the pre-tanh read-out state,** as a registered robustness measure against saturation.

I would not register "no deletion removes P4"; it is a null over 389 tests and is better described than tested.

**03m results: fix**