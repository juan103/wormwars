# 03m corrections: confirmation

**Verdict: fix, but small.** Every must-fix from both reviews is corrected in substance, and the quotes match. Two figures in the Corrections are wrong in the last digit and one sentence still overstates. These are three small edits; I don't need another round for them.

## What I checked

I recomputed the Corrections' figures by hand from `synapses.json`, `weights.json`, `decay.json` and `lesions.json`, and compared each quote with the original text.

Not verified:
- **Git claims.** I cannot run git, so the guarded-files and smoke-run statements rest on Astra's check.
- **The README's former status line.** I could only compare it with the fragments the two reviews quoted.
- **The 60% and 58% figures.** They need the pooled null median P4, which is in none of 03m's outputs. They are consistent with a median near 0.816, which fits 03's per-ensemble medians (0.76-0.85).

## Must-fixes

| Must-fix | Corrected accurately? |
|---|---|
| Gap junctions against the plan's rule | Yes. Panel median 0.822 to 0.908, 5 of 80 above N2's 0.945, highest intact 0.898, gaps-off response at most 0.082: all recompute |
| RIA/AIY and "typical level" | Yes, apart from one figure (below) |
| P4 under weight permutations | Yes, apart from one figure (below). 37 + 35 "both", 27 and 29 above, 59 of 64, 2 of 8 chemical-only all recompute |
| "Different sources", "distributed" | Yes. 61.5%/61.7% and 53.1%/52.8% recompute |
| Settling | Yes. 26, 171 and 37 recompute; SH-10007's P4 is 0.867 |
| Saturation | Yes. 0.44 against 0.66-0.80 |
| Stale experiment README; Q1 wording; D113 | Yes |

## Figures to fix

1. **"AIY pair 0.061, 2.7 times"** should be 2.6. The ratio is 0.060645 / 0.022893 = 2.649. This looks like Astra's 2.65 rounded again.
2. **"the lowest are 0.733 and 0.730"** should be 0.729. The paired minimum is 0.72946. Same cause, from Astra's 0.7295.
3. **Name the pooled null median P4 and its source** beside the 60% and 58%, so the figure is traceable (rule 5).

## Remaining overclaims

1. **"Only the weight permutations reach the typical level"** holds for the all-weight medians only (0.023-0.024).
   - Individual all-weight permutations run from 0.013 to 0.052.
   - Three of the eight chemical-only seeds give 0.045-0.048, the same level as the RIA pair's 0.049.
   - The corrected summary's own wording, "bring it to the null range", is right.
2. **"The slower relaxation holds throughout the window"** is stronger than the four ticks cited.
   - N2 is above all 80 at every recorded tick from 5 to 50, so D114's "ticks 5-50" is right.
   - The tick-50 margin is thin: 0.3000 against SH-10007's 0.2976.
   - SH-10007 passes N2 at tick 60, and SH-mirror-40014 at tick 150.
   - I traced only the six slowest graphs beyond tick 50, so 79 and then 78 of 80 are upper bounds until tick 300, where 78 is exact.

## Small omissions

- The single-deletion range changed from 0.088 to 0.089 without a quote. 0.089 is right (RIAR 0.0885), but rule 4 asks for the quote. It also qualifies the top note's "The numbers are right".
- Astra's point on the 26-versus-23 split is not addressed: "The rest of the remaining separation is in trajectories still moving" still stands uncorrected.
- "Leaves no route" is corrected but not quoted.
- The median drop of 0.046 is the independent design's; the paired one is 0.047.

## Before main

The root `README.md` (lines 36 and 133) and `ROADMAP.md` (lines 50-52) still say the simulations are running.

**03m results: fix**