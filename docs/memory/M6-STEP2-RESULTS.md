# M6, step 2: does the champions' foraging depend on their neural time scale? — results

*Draft 2, 2026-10-31, after one round of review (Astra 6 and Fable 5.1: both "fix then publish"; every fix taken;
draft 1, the prompt and the reviews are in
[`docs/reviews/20261031-m6-step2-results/`](../reviews/20261031-m6-step2-results/)). Astra reproduced `reading.json`
exactly, re-derived 31 statistics with their bootstraps and forced each failure gate; Fable re-derived the figures from
the records and the validation ratios from `probe.json`. Exploratory and descriptive: the plan ([`M6-STEP2-PLAN.md`](M6-STEP2-PLAN.md),
draft 2, D382, 0d841d1) fixed the genomes, the arms, the measures, the checks and the wordings before the run.
Nothing here is a pre-registration.

Numbers come from `runs/memory-m6-step2/`:
- `genomes.json`, the manifest with each genome's tau profile;
- `scores.json`, per-world scores for every genome and arm;
- `probe.json`, the validation probe on each T1 champion's own bank;
- `reading.json`, written by [`step2_read.py`](../../scripts/memory_m6/step2_read.py), with no simulation;
- the logs `run_log.txt` and `read_log.txt` (written as `runs/step2-run-log.txt` and `runs/step2-read-log.txt`, the
  names the review prompt uses), and the plan's test and sabotage logs `tests_log.txt` and `sabotage_log.txt` (the plan
  names them `runs/step2-tests.txt` and `runs/step2-sabotage.txt`);
- the compute record `step2-compute-record.json`.

A few descriptive figures the plan did not fix come from
[`check_step2.py`](../reviews/20261031-m6-step2-results/check_step2.py), archived with this review, and its output
`check_step2.txt`; the text marks them. Interpretations the plan did not fix are marked **after the data**.*

## In short

**In the fixed wordings, as the reader writes them:**
- "Making every neuron four times faster reduced the champions' T1 foraging score (mean within-champion change
  -24.5%, 95% interval -26.4% to -22.5%)."
- "This tests the champions' dependence on neural time scale; it does not establish that the probe-defined fading
  history effect mediates any benefit, because faster neurons also respond faster."
- "The reduction exceeded that of the generation-0 champions." "The reduction exceeded that of the drift genomes."
- **Sensitivity** (prespecified): without the switch champion, -24.5% (-26.4% to -22.5%), the same.

**But the champions lose at least as much when slowed, and T0's stereo champions lose about as much as T1's.**
- **Both directions cost.** Over the blocks (30 for T1, 24 for T0), the champions' mean relative change is:

  | k | 0.25 | 0.5 | 1 | 2 | 4 |
  |---|---|---|---|---|---|
  | T1 champions | -24.5% | -7.5% | 0 | -12.7% | -35.1% |
  | T0 champions | -23.3% | -7.7% | 0 | -12.4% | -34.8% |

  Making the neurons slower by a factor cost more than making them faster by the same factor.
- **T1 against T0, matched by graph, run and mapping** (72 runs, 24 blocks): -2.8 percentage points (-6.1 to +0.4).
  No difference was detected; the interval allows T1 to drop up to about 6 points more than T0.
- **Scaling only the interior** (the 39 of 302 neurons that are sensory or motor read-out neurons left at their own
  tau) at 0.25: -6.0% (-7.0% to -5.0%), 18.5 points (16.7 to 20.4) less than scaling every neuron.

**What this means (after the data).**
- **Mean score was highest at the intact time scale among the five scalings tested.** It fell on both sides, more
  steeply on the slow side. That is compatible with a preferred time scale at or near the evolved one; five values of k
  do not locate an optimum, and not every champion peaks at k = 1 (Astra): of the 102 T1 champions, 91 scored best
  at k = 1, 5 at 0.5 and 6 at 2 (T0: 61, 4 and 7 of 72; `check_step2.txt`). The plan said that a loss in both
  directions "neither establishes a tuned optimum nor counts against memory".
  - **The slow side carries a warm-up hazard.** Every brain starts from zero state, and tau runs up to 20 ticks, so at
    k = 4 a neuron at the ceiling has an 80-tick time constant inside a 200-tick episode, and the median neuron about
    13 ticks (Fable). Some of the larger loss on the slow side may be start-up cost; it was not separated.
  - **A two-sided loss is not by itself evidence that selection did the tuning.** The generation-0 champions also
    lost in both directions: 8.6% at 0.25 and 14.2% at 4 (Fable).
- **No difference between T1's single-nose task and T0's stereo task was detected.** The plan's prior was that
  single-nose foraging might rely on a comparison over time. T0's stereo champions, which can read a gradient across
  two sensors, gave descriptively similar profiles, and the matched difference at 0.25 includes zero. Equivalence is not
  established: the interval allows a T1 drop up to about 6 points larger.
- **The controls lose less, but they also have less to lose.** Their intact scores are 1.77 (generation 0) and 0.93
  (drift), against the champions' 2.73. The "exceeded" wordings hold, under the plan's caveat that a floor in the
  controls' scores biases the difference towards specificity. The lower baselines are a caution; they were not shown
  to explain the contrast (Astra).
- **Sparing the sensory and motor neurons greatly reduced the cost.** With those 39 neurons left at their own tau, the
  cost fell from about a quarter to about 6%. The rest of the cost appears only when they are sped up too; whether
  speeding only them would cost that much was not tested (Fable). This leaves the simplest response-speed account
  standing; it does not establish it, and it does not separate response speed from memory:
  - the interior arm also shortened the probe's history effect less, to a median 0.57 of intact against 0.23;
  - the probe reads the turn read-out neurons, which the interior arm leaves unscaled, so its 0.57 is seen through
    neurons whose own time constants did not change (Fable);
  - the boundary neurons' recurrent inputs still changed.
- **The owner's question stays open.** Whether the fading history effect itself helps the champions forage is not
  answered by any test in this thread, as the plan said it could not be at this cost.

**Every check passed:**
- the run was complete, in 3.64 CPU hours, under the 5-hour cap;
- the 24 T1-M0 champions reproduced 02b's intact scores within 0.05% (the tolerance was 2%);
- the "k = 1 alone" arm reproduced k = 1 exactly for every champion, so batch composition did not move the scores;
- the probe validation passed;
- no genome fell below the score floor of 0.05.

## The run

- **One attempt, completed.** The compute record shows 13,092 s in category measure, no failed attempts, at commit
  0d841d1, the plan's. The scores stage took 12,579 s and the probe 445 s.
- **The scores** covered 102 T1 runs (champion g39 at seven arms, g00 and drift0 at three) and 72 T0 runs (g39 at
  five), on 02b's 32 criticality worlds each.
- **Consistency against 02b:** 24 of 24 within 2%, with a largest relative difference of 0.048%.
- **Composition:** the champion's "k = 1 alone" score equals its k = 1 score in a mixed batch for all 102 runs, a
  block mean of exactly 0.

## The validation probe

Each T1 champion's two ramp-end states, written at k = 1 on its own bank, were continued for 100 ticks under each arm.
The ratio is the integrated read-out difference over those ticks, against k = 1. All 102 champions were above the start
floor of 1e-3, with no zero denominators.

| Arm | Median ratio | Below 1 | Full-probe median ratio |
|---|---|---|---|
| 0.25 | 0.233 | 102 of 102 | 0.108 |
| 0.5 | 0.490 | 102 of 102 | 0.374 |
| 2 | 1.925 | 1 of 102 | 2.150 |
| 4 | 3.156 | 1 of 102 | 3.198 |
| interior 0.25 | 0.572 | 98 of 102 | 0.502 |

- **The pass criteria were met:** at 0.25 the median is below 0.5 and all are below 1; at 4 the median is above 1.
- **The one exception at k = 2 and 4** is T1-MS-N2 run 3, whose ratio fell below 1 at both.
- **Not below 1 in the interior arm:** T1-M0-N2 run 1, T1-MS-N2 run 7 (the switch champion), T1-MS-SH4 run 0 and
  T1-R2-N2 run 2.
- **The switch champion** (T1-MS-N2 run 7) had continued integrals of 8.86, 10.14, 12.58, 15.27 and 16.63 at k = 0.25,
  0.5, 1, 2 and 4, and 13.03 in the interior arm. It shrank least at 0.25 (ratio 0.70), as a switch that holds two
  states should.
- **A note on the record:** for k = 2 the reader's list is named `not_below_1`, as the plan's reporting rule says, so
  it lists the 101 champions that rose as expected. The one that did not is run 3 above. k = 2 is not in the pass
  criteria.

## The measures

**The champions** (T1 g39; 30 blocks; 95% intervals from resampling blocks):

| k | Relative change | Absolute change | Lower than intact (of 102) |
|---|---|---|---|
| 0.25 | -24.5% (-26.4 to -22.5) | -0.68 (-0.73 to -0.62) | 100 |
| 0.5 | -7.5% (-8.3 to -6.6) | -0.21 (-0.23 to -0.18) | 97 |
| 2 | -12.7% (-14.3 to -11.1) | -0.35 (-0.40 to -0.31) | 96 |
| 4 | -35.1% (-37.2 to -33.2) | -0.97 (-1.04 to -0.91) | 102 |
| interior 0.25 | -6.0% (-7.0 to -5.0) | | |

The intact score is 2.73 (2.68 to 2.78). The last column is from `check_step2.txt`.

**The controls,** each read separately. The difference is the champion's absolute change minus the control's, over
the champion's intact score, per run:

| | Intact score | Own relative change at 0.25 | Difference at 0.25 | Difference at 4 |
|---|---|---|---|---|
| Generation-0 champions (g00) | 1.77 (1.69 to 1.86) | -8.6% (-12.0 to -5.4) | -19.0% (-21.7 to -16.2) | -24.8% (-28.9 to -20.5) |
| Drift genomes (drift0) | 0.93 (0.86 to 1.02) | -1.8% (-4.1 to +0.3) | -23.7% (-25.8 to -21.5) | -35.1% (-38.3 to -31.3) |

From `check_step2.txt`, with no interval: the controls' own relative change at k = 4 is -14.2% (g00) and +2.5%
(drift0). The drift genomes' mean score changed little in either direction. Individual drift genomes did respond:
Astra found absolute relative changes above 10% in 28 of 102 at 0.25 and 42 of 102 at 4 (`check_step2.txt`).

**T0's champions** (24 blocks): intact 2.72 (2.67 to 2.76); relative change -23.3% (-26.2 to -20.4) at 0.25, -7.7%
(-8.8 to -6.7) at 0.5, -12.4% (-15.7 to -9.5) at 2, and -34.8% (-38.2 to -31.5) at 4. T1 minus T0 at 0.25, matched:
-2.8 points (-6.1 to +0.4) over 72 runs.

**Association over the 102 champions** (Spearman with average ranks; intervals from resampling blocks; no undefined
draws):
- the change at 0.25 against M6-0's a on the own bank: rho -0.39 (-0.56 to -0.18). Champions with a larger history
  effect lost more.
- against the median tau: rho 0.06 (-0.16 to 0.27).
- **But a tracks the intact score** (from `check_step2.txt`, no interval): rho 0.64 between a and intact score, and
  -0.28 between the change at 0.25 and intact score. Better foragers have larger history effects and lose more, so the
  association with a cannot be read as a dose-response, as the plan said. Nor was it shown that the intact score
  explains the association away (Astra).

**The tau profiles** (medians over genomes): median tau 3.19 (T1 champions), 3.09 (g00), 3.10 (drift0) and 3.04 (T0
champions). The T1 champions have 2.3% of their neurons at the floor and 2.6% at the ceiling; g00 none; drift0 2.6% and
2.6%; T0 2.6% and 2.3%.

## What this does and does not establish

**It establishes:**
- **The champions' foraging depends on their neural time scale,** in both directions, by a quarter to a third of
  their score at a factor of four.
- **T0's stereo champions showed a descriptively similar dependence,** and no matched difference from T1's was
  detected at 0.25.
- **Leaving the 39 sensory and motor neurons at their own tau greatly reduced the cost** of speeding the rest.

**It does not establish:**
- **That the history effect matters for foraging,** or that it does not. Faster neurons also respond faster, and the
  slowing arms cost more, though they lengthen the history effect.
- **That selection tuned the champions' time scale,** or that the evolved scale is an optimum.
- **That T0 and T1 depend on time scale equally.**
- **That the cost sits in the sensory and motor neurons.** The complementary arm, scaling only those, was not run.
- **That the champions depend on time scale more than evolved controllers in general.** The controls forage worse and
  have less to lose; they are not a generic-cost baseline (the plan's caveat).
- **Why slowing costs more.** The longer warm-up within the episode is one candidate; it was not separated.
- **That the interior arm isolates memory from response speed.** It shortened the history effect less, its probe
  ratio is read through unscaled read-out neurons, and the boundary neurons' recurrent inputs changed.

## What this means for the roadmap

**On the owner's question** (does the champions' fading history effect matter for their foraging?): not answerable
at this cost, as both reviewers said in the design round. The nearest answerable question has a clear answer: the
champions' foraging depends on their neural time scale, in both directions. No difference between the stereo task and
the single-nose one was detected, and sparing the sensory and motor neurons greatly reduced the cost of speeding. The
tested interventions do not establish whether the probe-defined fading history effect benefits foraging (Astra).
**Next, by the owner's order (D379):** the thread stops.
Steps 1 and 2 and M6-3's literature check are folded into [`SYNTHESIS.md`](SYNTHESIS.md).

## Deviations and notes

- **None from the plan.** The run, the checks, the measures and the wordings are as fixed.
- **The run took 3.64 CPU hours,** below the plan's forecast of 4 to 4.3 and under the 5-hour cap.
- **The plan was pushed before the run:** Fable checked that the plan's commit was pushed at 23:16:39 UTC and the
  run's attempt file is stamped 23:17:00 UTC.
- **The sensitivity reading is the same at the displayed precision,** not to every digit (-24.4787% against -24.4813%).
- **The timing and smoke genomes stayed in** (T1-M0-N2 run 0's champion, controls and T0 counterpart). The full run's
  scores for that champion match the timing run's exact rescaling: 2.824, 2.043, 2.611, 2.831 and 2.227 at k = 1,
  0.25, 0.5, 2 and 4.
