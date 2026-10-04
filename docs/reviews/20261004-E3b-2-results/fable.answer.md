Review complete. Every number in the draft was checked against `summary.json`, the stage records and `compute-record.json`. The tables are almost all correct, but there are two factual errors, several places where the wording outruns or understates the record, and one reading the data supports that the draft misses.

## Verified correct

- **Attribution tables (§A, §B):** every Shapley, reversion, transplant, net gain and t interval matches the schedule means. The pair interaction means I recomputed from the per-champion dividends: T-A +1.444, T-F +1.899 shared; +1.039 and +1.157 under none. The trail-split table matches the joint bootstrap intervals. T-F run 4's sensing transplant is −0.508.
- **Lesion table (§C):** every mean and interval matches, for all four columns and both conditions. The intact ranges, the seed's 5.71 and W2 alone's 1.65 are right. The seed's input cut and gate cut are identical on every outcome (−0.7830), as the plan predicted.
- **Latch (§D):** switched share 1.000 in both directions for all 21, pre-aligned 0 everywhere, latencies T-A 1-2, T-F 1-3.0005, N 1-2, seed 1. Agreement 0.994-0.996 in three T-F organisms, 1.000 elsewhere.
- **Genomes (§E):** resting turn ranges are right (T-A 0.648-1.0, T-F 0.730-1.0, N all 1.0, seed 0.400). A is the high state in all 21.
- **Checks and compute:** seed exactness true in all three comparisons; lesion intact vs attribution max difference 0.0 for all 32; resting-turn max difference 0.0. Stage seconds sum to 10782 s; the compute record's 10789.5 s is 2.997 GPU-hours. Per-stage hours 0.33, 1.60, 1.01, 0.06 are right. Replication correlation 0.9857, means +0.114/+0.069 and +0.451/+0.381.
- **The lesion's name:** `without_scent` zeroes the gains of the four A/B nose channels, and each nose reads trail plus path-distance scent (`maze_world.py` line 15 and 341). "Nose inputs removed (trail and scent)" is the correct name, and under "none" only the scent remains.

## Errors

1. **"All eight in 7 champions" is wrong. It is 6.** From `hybrids_below_w2` (functional-shared), the champions with all eight mixed hybrids below W2 are T-A run 7 and T-F runs 1, 2, 5, 6, 7. T-F runs 0 and 3 have four. The same count under "none" is also 6. Appears twice (In brief and §A).

2. **"Undecided ticks number about one per leg" is not true of the band the table reports.** Under the middle-third band, 9 of 21 organisms have zero undecided ticks (T-A runs 0, 2, 6; T-F runs 4, 7; N runs 0, 1; and one direction of T-A run 5 and T-F run 6). The one-tick-per-leg pattern holds under the middle-half band. More important, the 0.994-0.996 agreement in T-F runs 0, 3 and 6 is not undecided ticks but *opposite* ticks, and their count equals the leg count (T-F run 0: 8115 opposite ticks for 8118 legs toward A; run 6: 9270 for 9275; run 3: 9362 for 9365). These are the first tick after a visit in the organisms whose latch takes 2-3 ticks to cross. That is a stronger statement than the raw percentage and the draft should make it: every disagreement is a transit tick, and there are no stray latch states.

## Wording that overruns or understates the record

3. **The mixed hybrids are not "below W2 alone"; many are dead.** T-F runs 5 and 7 have all eight mixed hybrids at exactly zero visits (gain −1.000). T-A run 0 has three at zero and the sensing transplant at −0.9998. The sensing transplant into the seed is −0.92 to −0.99 in five of eight T-A champions. These are non-functional circuits, not weaker shuttlers. This matters for reading the Shapley values: half the marginal contributions being averaged are transitions out of a dead circuit, so T-A's negative sensing allocation (−0.12) and positive gating (+0.19) are artefacts of splitting a dominant interaction, not evidence that tuned sensing hurts. The draft says the Shapley values split the interaction. It should also say how many hybrids are at zero.

4. **The most interpretable attribution number is missing.** The coalition with tuned sensing and gating on the seed's output edges and latch, read off the per-champion tables:

   | | s+g coalition | net gain | share |
   |---|---|---|---|
   | T-A | +0.080 | +0.114 | 70% |
   | T-F | +0.358 | +0.451 | 79% |

   This supports the headline directly, without Shapley conventions. The remainder is carried by the output edges at the champion end: T-F's output reversion is −0.084 [−0.156, −0.012], about a fifth of T-F's gain. "Carry little of the gain" is fair but say "about a fifth of T-F's".

5. **"The cause: a champion's tuned comparator inputs need its tuned biases" is a mechanism claim.** Plan §9 rules out "any mechanism beyond what C and D measure directly". The hybrid table supports it as a reading, so write "the reading" or "consistent with", not "the cause".

6. **"The noses matter to the T champions, not to N's" overstates.** N's intact visits are higher without trails (6.28-6.76) than with shared trails (4.92-5.50), and under "none" the nose lesion costs N −0.15 [−0.25, −0.06]. So N's champions do use the nose input (the scent); the shared trails are net harmful to them, which is why removing everything is neutral (+0.08). The right statement is "N's champions use the scent but not the trails, and shared trails cost them". Both numbers are in `lesions.intact.none` and the N "none" scent row.

7. **The clamp comparison reads as though champions depend more on the latch.** Costs of −1.25 (T-F) against −0.85 (seed) are in units of the seed's mean, so the gap is mostly T-F's higher intact level. As a share of own performance all three lose about 85%. The clearer fact: clamped T-A, T-F and seed all land at about one visit per wey (0.96, 1.17, 0.87), the first visit and nothing after. State that instead of, or beside, the contrast.

8. **"Switches after every visit" is a latch-integrity check, not evidence of use.** With relay weights of magnitude 2.37-3.0 (the seed's are ±3) a cross within 1-3 ticks is nearly guaranteed. Section D already frames it right; In brief should weight the two: the clamps carry the evidence, the recorder rules out the "latch stuck or bypassed" arm of §6. Also worth one line: the latch parameters barely moved (self-weight 1.66-2.44 against 2.0), consistent with the ~0.01 allocation.

9. **Smaller fixes:**
   - "≤ 0.04": T-A's output allocation is 0.0409. Write "about 0.04 or less".
   - "With trails off, the costs keep the same order": gate cut and A's outputs swap for T-F and N under none. Write "nearly the same order".
   - Deviations: "7300-7555, not 'smoke mazes', as stated in plan draft 3" reads as if draft 3 said smoke mazes. Draft 3 §7 already says 7300-7555; drafts 1-2 said smoke mazes. This is not a deviation from draft 3.

## Missing against plan §5

- §5A promised schedule-level shares of summed gain. They are in `summary.json` (T-A: sensing −1.06, gating +1.63) but not reported. Either report them with the note that negative allocations push shares outside [0, 1], or say they are omitted and why.
- §5A's Shapley in visits per wey, the maze-bootstrap intervals for the attribution table and the full dividend table exist only in `summary.json`. A pointer sentence like the one in §C would do.
- §5D's middle-half band result (agreement 1.000 for every organism, zero opposite ticks) and the denominators are not mentioned. One line.

## Verdict

**Fix then publish.** Required: items 1 and 2 (wrong numbers), 3 and 6 (the record says more than the draft), 5 (a mechanism claim the plan forbids), and the small fixes in 9. Strongly recommended: 4 (the s+g coalition value), 7 and 8 (weighting the selector evidence), and the §5 pointers. The central reading survives all of these: the selector is still in use, and the gain sits in sensing and gating together. The draft's headline is right, but it is under-supported in one place (the coalition value) and over-worded in three (the cause, N's noses, the agreement figure).