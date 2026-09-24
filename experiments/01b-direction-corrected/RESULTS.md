# WormWars 01b: results

**With chemical synapses running the right way round, the real wiring (N2) reaches higher mean
best-of-generation fitness than both shuffled (SH) and random (RD) graphs, and a higher final
held-out score than the random graphs. Its final score is not detectably different from the
shuffles'.** Experiment 01, with the synapses reversed, had found N2 *lower* on the first of those
measures.

**What this does not show: that N2 *improves* faster.** The pre-registered "speed" measure is the
mean of best-of-generation fitness over all 25 generations, generation 0 included, so it mixes where
a run starts with how much it gains. Split apart (an exploratory analysis, below), N2's edge over the
shuffles is, as a point estimate, entirely a higher starting point with the same gain afterwards.
Neither component separates statistically on its own.

The design and analysis were fixed in [`PREREGISTRATION.md`](PREREGISTRATION.md) before any run.
Everything under **Pre-registered** follows it exactly. Everything under **Exploratory** was not
pre-registered: it was chosen after seeing the data, much of it at the suggestion of two
pre-publication reviewers (`DECISIONS.md` D033), and it should be read that way.

Run: `runs/exp01b-direction-corrected/` (45 runs, 1.058 h wall time, one RTX 5080, commit `5161e76`).
The bundle is marked "dirty" only because untracked review folders were in the working tree.

---

## Pre-registered

Hierarchical bootstrap, runs nested in graphs, 20 000 resamples. **P is the fraction of bootstrap
differences above zero**: a resampling statistic, not the probability that the claim is true.
Intervals are 95% and unadjusted; a correction for multiple comparisons follows the tables.

### Against the predictions

| # | prediction | outcome |
|---|---|---|
| 1 | Final held-out score: no contrast separates | **Falsified, in part.** N2 − RD separates, N2 higher. N2 − SH and SH − RD do not. |
| 2 | SH vs RD: no separation on either measure | **Held**, on both. |
| 3 | Speed measure, N2 vs controls: no prediction | N2 higher than both SH and RD. |

### Final held-out score (generation 25)

| | score [95% interval] |
|---|---|
| N2 | 1.629 [1.588, 1.668] |
| SH | 1.559 [1.468, 1.632] |
| RD | 1.535 [1.483, 1.586] |

| contrast | difference [95% interval] | P | |
|---|---|---|---|
| N2 − SH | +0.069 [−0.015, +0.169] | 0.941 | no separation |
| N2 − RD | **+0.094 [+0.029, +0.160]** | 0.998 | **N2 > RD** |
| SH − RD | +0.025 [−0.079, +0.116] | 0.699 | no separation |

### Speed measure: mean best-of-generation fitness over generations 0 to 24

| | [95% interval] |
|---|---|
| N2 | 1.590 [1.574, 1.607] |
| SH | 1.523 [1.493, 1.553] |
| RD | 1.523 [1.490, 1.566] |

| contrast | difference [95% interval] | P | |
|---|---|---|---|
| N2 − SH | **+0.068 [+0.034, +0.102]** | > 0.999 | **N2 > SH** |
| N2 − RD | **+0.067 [+0.021, +0.105]** | 0.998 | **N2 > RD** |
| SH − RD | −0.000 [−0.052, +0.045] | 0.511 | no separation |

**Six contrasts were tested.** With Bonferroni-adjusted intervals (1 − 0.05/6, 99.17%), all three
that separate still do: final N2 − RD [+0.008, +0.181], speed N2 − SH [+0.022, +0.114], speed
N2 − RD [+0.004, +0.116].

---

## Exploratory (not pre-registered)

### Where the speed difference comes from: starting level versus gain

Best-of-generation fitness at generation 0 (the best of 32 random strains, before any selection),
and the gain from there to the mean of generations 20-24, averaged over 15 runs per condition:

| | best at generation 0 | gain by generations 20-24 |
|---|---|---|
| N2 | 1.236 | 0.446 |
| SH | 1.162 | 0.437 |
| RD | 1.215 | 0.405 |

As point estimates, N2's speed advantage over SH is all head start (+0.074 at generation 0, gain
+0.009). Against RD it starts about level (+0.021) and gains more (+0.041). **None of these
component contrasts separates** (hierarchical bootstrap, 20 000 resamples: generation 0,
N2 − SH +0.074 [−0.072, +0.206]; gain, N2 − RD +0.041 [−0.159, +0.233]). A single generation's
best-of-32 is noisy, so the data cannot say where the pre-registered difference comes from.

For comparison, in experiment 01 (synapses reversed) the gains were N2 0.303, SH 0.391 and RD 0.402
from generation-0 bests of 1.136, 1.109 and 1.148: N2 started level and gained less. That gain
deficit is gone in 01b. Whether it was ever statistically distinct was not tested separately.

### Calibration equalises motor drive only approximately

Each graph's motor gain is fitted so that a random population, measured at unit gain, would produce
N2's reference drive. The mean |forward| of a random population actually achieved **at the fitted
gains** (24 strains, 80 ticks, seed 0; first measured by a reviewer, reproduced here):

| | N2 | SH1-SH5 | RD1-RD5 |
|---|---|---|---|
| share of the target |forward| reached | 95% | 84-93% | 86-97% |

|turn| reaches 92-100% for every graph. The response to gain is not linear, because commands are
clipped and moving changes what the sensors see. The residual favours N2 over the shuffles on
average, and it could contribute to N2's higher starting point against SH. The mean fitness of the
whole generation-0 population is N2 0.464, SH 0.433, RD 0.463, which fits the same pattern. The
comparison is therefore of the whole pre-registered pipeline, recalibration included. It does not
isolate the synapse direction with the motor gains held fixed.

### N2 among the eleven graphs

On the speed measure, N2's mean is the highest of the 11 graph means, with RD3 0.007 behind (1.583
against 1.590). All 15 N2 runs exceed the median control graph and 7 of 15 exceed the best one. On
final score N2 is 2nd of 11, behind SH5 (1.651). This is descriptive only, and **no rank p-value is
offered**. N2's mean averages 15 runs where each control's averages 3; SH and RD are different
families; and N2 is the calibration reference. So the graphs are not exchangeable, and the
bootstrap contrasts above compare N2 with the control-family *means*. Neither they nor the rank
show that N2 lies outside the distribution of individual graphs. More control graphs would be
needed for that.

### Side by side with experiment 01

Same seeds, graphs, budget, protocol and analysis; only the synapse direction differs. The
**contrasts** are comparable across the two. The **absolute** scores are not, because N2 is the
calibration reference and its stronger drive with correct synapses doubled the target everyone was
calibrated to (reference |forward| 0.326 in 01, 0.626 in 01b). Every condition scored higher in
01b: the controls by 0.05-0.10 and N2 by 0.22-0.23. Part of every rise is the higher calibration
target, and the two effects cannot be separated here.

| | 01, synapses reversed | 01b, synapses correct |
|---|---|---|
| N2 − SH, speed measure | −0.100 [−0.129, −0.070] | +0.068 [+0.034, +0.102] |
| N2 − RD, speed measure | −0.112 [−0.150, −0.077] | +0.067 [+0.021, +0.105] |
| N2 − SH, final score | −0.047 [−0.148, +0.039] | +0.069 [−0.015, +0.169] |
| N2 − RD, final score | −0.041 [−0.113, +0.029] | +0.094 [+0.029, +0.160] |
| N2's rank of 11, speed measure | last | first |
| N2's raw random-population drive at unit gain | 0.082, weakest of 11 | 0.157, 2nd strongest |

The last row bears on how 01 was read. 01 found N2 driving the motors more weakly than every
control, treated that as a confound, and removed it by calibration. With the synapses the right way
round, N2 is among the strongest drivers, so that confound was largely a product of the reversal.

### Integrator accuracy on 01b's own champions

The pre-registration cited 01's champions (0 of 1440 weys with a motor read-out error above 0.05
between 8 and 32 substeps). The same check on **01b's** 45 champions (32 weys each, 40 ticks, input
seed 300) gives 0 of 1440 above 0.05, with a maximum of 0.049. A reviewer running a similar check
with different inputs (seed 200) found 8 of 1440 above 0.05, with a maximum of 0.26. Errors of that
size are rare and affect all three conditions, but their effect on fitness was not measured. The
exposure is not symmetric: error grows with in-degree, N2 and SH share a degree sequence, and RD's is
flatter.

### Not a result: score per GPU-hour

`REPORT.md` also reports held-out score per GPU-hour, with N2 > SH > RD. Disregard it. Runs were
executed in the order N2, SH1-SH5, RD1-RD5, and wall time per run rose from 74-77 s (all of N2, SH1
and most of SH2) to 87-97 s from SH3 on. The work per run is identical, so something else was using
the machine. Per-hour figures measure run order, not the graphs.

---

## Scope

One hand-chosen sensor and motor interface, one foraging task, 25 generations, 8 integrator
substeps. Only experiment 01's headline arm was rerun. Its uncalibrated arm, pump-gated foraging,
coevolution and combat tactics still describe the reversed graph.
