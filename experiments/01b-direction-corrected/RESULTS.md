# WormWars 01b: results

**With chemical synapses running the right way, the real wiring improves faster than both kinds of
control and ends at least level with them, and ahead of the random graphs.** This reverses
experiment 01's "N2 is slower", which is now attributed to the reversed synapses, as the
pre-registration said it would be. Every number below is from the analysis fixed in
[`PREREGISTRATION.md`](PREREGISTRATION.md) before any run.

Run: `runs/exp01b-direction-corrected/` (45 runs, 1.058 h of wall time on one RTX 5080, commit
`5161e76`). The bundle is marked "dirty" only because untracked review folders sat in the working
tree; no tracked file differed from that commit.

## Against the predictions

| # | prediction | outcome |
|---|---|---|
| 1 | Final held-out score: no contrast separates | **Falsified, in part.** N2 − RD separates (N2 higher). N2 − SH and SH − RD do not. |
| 2 | SH vs RD: no separation on either measure | **Held**, on both. |
| 3 | Speed of improvement, N2 vs controls: no prediction | **N2 is faster** than both SH and RD. |

## Final held-out score (generation 25)

| | score [95% interval] |
|---|---|
| N2 | 1.629 [1.588, 1.668] |
| SH | 1.559 [1.468, 1.632] |
| RD | 1.535 [1.483, 1.586] |

| contrast | difference [95% interval] | P(first > second) | |
|---|---|---|---|
| N2 − SH | +0.069 [−0.015, +0.169] | 0.941 | no separation |
| N2 − RD | **+0.094 [+0.029, +0.160]** | 0.998 | **N2 > RD** |
| SH − RD | +0.025 [−0.079, +0.116] | 0.699 | no separation |

## Speed of improvement (mean best-of-generation fitness over 25 generations; higher = faster)

| | speed [95% interval] |
|---|---|
| N2 | 1.590 [1.574, 1.607] |
| SH | 1.523 [1.493, 1.553] |
| RD | 1.523 [1.490, 1.566] |

| contrast | difference [95% interval] | P(first > second) | |
|---|---|---|---|
| N2 − SH | **+0.068 [+0.034, +0.102]** | > 0.999 | **N2 > SH** |
| N2 − RD | **+0.067 [+0.021, +0.105]** | 0.998 | **N2 > RD** |
| SH − RD | −0.000 [−0.052, +0.045] | 0.511 | no separation |

## Side by side with experiment 01 (same seeds, graphs, budget and analysis; only the direction differs)

| | 01, synapses reversed | 01b, synapses correct |
|---|---|---|
| N2 speed | 1.359, **slowest of all 11 graphs** | 1.590, **fastest of all 11 graphs** |
| N2 − SH, speed | −0.100 [−0.129, −0.070] | +0.068 [+0.034, +0.102] |
| N2 − RD, speed | −0.112 [−0.150, −0.077] | +0.067 [+0.021, +0.105] |
| N2 final score | 1.412, 8th of 11 | 1.629, 2nd of 11 (SH5 1.651 is higher) |
| N2 − SH, final | −0.047 [−0.148, +0.039], no separation | +0.069 [−0.015, +0.169], no separation |
| N2 − RD, final | −0.041 [−0.113, +0.029], no separation | +0.094 [+0.029, +0.160], N2 > RD |
| N2's raw motor drive before calibration | 0.082, **weakest of 11 graphs** | 0.157, 2nd strongest (RD4 0.165) |

The last row matters for how 01 was read. 01 found that N2 drove the motors more weakly than every
control graph, called that a confound, and removed it by per-graph gain calibration. With the
synapses the right way round, N2 is one of the *strongest* drivers. So that confound was itself
largely a product of the reversal. Calibration is still applied, so it does not affect the
comparison above.

## How far this can be trusted

- **N2 is one graph.** Its interval carries run-to-run variation only; the controls' intervals
  also carry graph-to-graph variation. The pre-registered contrasts answer "does N2 beat the
  control *families* as sampled"; they do not show that N2 would beat an eleventh shuffle.
- **Rank among graphs.** On speed, N2's mean is the highest of the 11 graph means, but RD3 is
  within 0.007 (1.583 against 1.590). If the 11 graphs were exchangeable, one of them would rank
  first by chance 1 time in 11 (**p ≈ 0.09**). By that stricter standard, 10 control graphs are
  too few to show that N2 lies outside the control distribution. All 15 N2 runs beat the median
  control graph, and 7 of 15 beat the best one.
- **The final-score advantage is small and one-sided.** N2 > RD separates, but N2 is 2nd of 11
  graphs and its lead over SH does not separate.
- **Scope.** One hand-chosen sensor and motor interface, one foraging task, 25 generations, and an
  integrator that is adequate in this range (`DECISIONS.md` D032). Nothing here says the real
  wiring is better in general.
- **Only the headline arm was rerun.** 01's uncalibrated arm, pump-gated foraging, coevolution and
  combat tactics still describe the reversed graph.

## What this changes

- 01's "N2 is slower, and we do not know why" is answered: the reversed synapses. With the real
  direction, N2 is faster.
- 01's title calls it "a foraging null result". For the real wiring the result is no longer null on
  speed. 01 remains published as what it was, with correction C5 in `docs/RESULTS.md`.
- The obvious next test is more control graphs. With 10, the best possible rank-based p is 0.09;
  with 39 controls, first place would mean p = 0.025.
