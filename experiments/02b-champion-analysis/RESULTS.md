# WormWars 02b: what experiment 02's champions compute

**Exploratory and descriptive.** This analysis was not pre-registered, and nothing here is a
confirmatory claim. It is roadmap item 1: experiment 02's saved genomes, no evolution. The script
is `analyse.py` (v2). Every number below is computed by its `summarise` stage (`summary.json`).
Each stage's raw output is in this folder.
- **Champions,** unless stated: generation 39 of cells T0-M0 and T1-M0, 8 N2 runs and 16 SH runs
  (8 graphs × 2).
- **Intervals:** Student t over runs; SH graph clustering is not modelled.
- **GPU time:** about 1.5 hours.

**This is v2.** v1 was reviewed by Astra 6 and Fable 5.1 (`docs/reviews/20260925-184331-02b/`).
Both confirmed its numbers and the deletion operator. Both found a computation bug, a weak
control, and three readings stated too strongly. What changed is at the end (D049).

## Summary

1. **Evolved champions circle, and slow down on food and near obstacles.** In stereo foraging
   (T0, biological mapping), their turn command is also *associated* with which side the food
   is on. N2 and shuffles do this equally: the within-wey standardised coefficient is 0.27 for
   N2 and 0.22 for SH.
   - **This is a replay correlation,** not evidence that the left-right difference drives the
     turning. Removing each wey's mean does not remove time-varying confounds from the trajectory
     (Astra).
   - **It does not revise 02's registered result.** That result is about fitness: feeding both
     noses the mean costs the champions only +0.027 (N2) and +0.023 (SH), below 02's threshold of
     0.10 for meaningful use. A turn can covary with the side difference and still be worth
     little score. Section 1 gives the details.
2. **Selection, not parameter drift, made the champions' turning history-dependent.** After
   identical current input, the turn read-out differs by food history far more at generation
   39 than at generation 0, or after 39 generations of mutation without selection. This holds in
   every group. But the difference is about 95% of the difference between the two starting
   levels' steady states, and 85% of it is still there five ticks later. So it is a slow memory
   of the recent food *level*, not a computation on its change.
3. **Deletion criticality has a mapping-independent core in N2.** AIZ and RIA are critical in
   most runs under all three food mappings, including R2, whose food neurons are not amphid.
   Beyond that core, the critical set shifts with the mapping. The ranking of neurons by mean
   deletion cost correlates 0.84 (M0 against R1) and 0.80 (M0 against R2). The 20 most critical
   neurons overlap only 10 and 9 times. RIA is a high-degree neuron (98th percentile); AIY is not
   (58-65th).
4. **For 03a:** 94 of the 96 most critical N2 targets connect directly to interface neurons.
   Deleting only those edges costs a median 35% of what full deletion costs, and 03a keeps those
   edges fixed.
5. **Anatomical magnitudes are largely eroded by generation 39:** the rank correlation with
   anatomy falls from 1.0 to 0.35 (N2) and 0.36 (SH).

## 1. Behaviour and steering

**Replays:** 8 probe worlds, per tick, weys tracked individually, alive on both ticks. Standardised
regression of the motor commands on five sensed quantities: pooled, and within wey (each wey's own
mean removed). Means over champions:

| | turn-sign persistence (same wey, next tick) | turn on food left minus right: pooled / within wey | forward, within wey: food level / food change / collision total |
|---|---|---|---|
| T0 N2 | 0.997 | 0.225 / 0.267 | −0.24 / +0.27 / −0.27 |
| T0 SH | 0.997 | 0.217 / 0.224 | −0.30 / +0.19 / −0.19 |
| T1 N2 | 0.998 | (no difference) | −0.25 / +0.17 / −0.30 |
| T1 SH | 0.999 | (no difference) | −0.17 / +0.14 / −0.23 |

These are correlations, not causes. Moving fast changes the food reading, so the food-change
coefficient is not evidence of temporal sensing. The history test (section 2) is the controlled
version.

**How this relates to 02's registered result** (reconciled before publication; the owner's
publishing plan, D063). The two measure different things, and neither revises the other:

| | 02's registered primary | 02b's "turn on food left minus right" |
|---|---|---|
| task and cell | stereo foraging, T0-M0 | the same cell's champions, T0-M0 |
| measure | fitness lost when both noses get the mean food, generation 39 | standardised regression coefficient in replays, within wey |
| output | the task score | the turn motor command, per tick |
| result | N2 +0.027 [+0.000, +0.060], SH +0.023 [+0.003, +0.047]; meaningful use needs 0.10 | 0.27 (N2), 0.22 (SH) |
| reads as | the side difference is worth little score | the turn covaries with the side difference |

- **They fit together, and 02 already pointed this way.**
  - The left-right swap's point estimates are larger than the mean probe's: +0.079 [+0.000,
    +0.179] for N2 and +0.082 [+0.021, +0.158] for SH. The intervals are wide.
  - 10 of 72 T0 champions (all mappings) are meaningfully swap-sensitive. 02
  concluded that a few champions depend on the side the food is on, but that the probes cannot
  say whether that is a left-right comparison or one-sided sampling.
- **02b adds that the association is present in the group means** in replays.
- **What 02b cannot say:** whether the turn *uses* the difference in a way that matters for
  score. 02 says it mostly does not.
- **02's primary reading is unchanged.**

**Input-response probe on the evolved genomes** (fixed artificial input from rest; T0-M0). N2's
signed turn toward food is +0.009 [−0.007, +0.026] at generation 39 (5 of 8 positive). It is
−0.003 at generation 0 (3 of 8). Two champions carry the mean. SH: +0.0003 [−0.003, +0.003], 9 of
16 positive. So no group-level change is shown. In the world, both groups show side-dependent
turning (above) and the same swap cost in 02. Across the 24 champions, the probe's signed
response correlates with the swap cost at about 0.31 (Spearman).

## 2. History: matched current input after different food histories

**Method:**
- One stimulus bank per run: the mean sensed signals, ticks 20-60, of the generation-39
  champion's replay. It is shared by every genome tested for that run.
- The food level reaches the same final value from a quarter of it (rising) or 1.75 times it
  (falling), over 10 ticks, after 100 ticks at the starting level. Every other signal is held at
  its typical value.
- Measured: the *raw* read-out, before the motor gain and clip, on the final tick.
- Tested on generation 0 (the best of 32 random genomes), on generation 39, and on a
  **mutation-only drift control**: the generation-0 champion mutated 39 times with the run's
  settings and no selection, 4 replicates.

| | turn: \|rising − falling\|, g0 / g39 / drift | forward: \|rising − falling\|, g0 / g39 / drift |
|---|---|---|
| T0 N2 | 0.095 / **0.452 [0.196, 0.707]** / 0.106 [0.052, 0.160] | 0.060 / 0.106 [0.023, 0.190] / 0.068 |
| T0 SH | 0.030 / **0.111 [0.076, 0.146]** / 0.040 [0.026, 0.053] | 0.038 / 0.079 [0.053, 0.105] / 0.029 |
| T1 N2 | 0.104 / **0.281 [0.157, 0.405]** / 0.097 [0.041, 0.152] | 0.057 / 0.070 [0.015, 0.124] / 0.062 |
| T1 SH | 0.035 / **0.158 [0.127, 0.189]** / 0.045 [0.028, 0.061] | 0.039 / 0.059 [0.037, 0.081] / 0.032 |

- **Turn:** in every group the evolved effect is above both generation 0 and the drift control.
  Selection produced it.
- **Forward:** not distinguishable from drift in N2. In SH it is modestly above.
- **What kind of history it is.** The generation-39 turn difference is a median 0.90-0.95 of the
  difference between the two starting levels' steady states, and 0.83-0.87 of it survives five
  more ticks of identical input. The brains are still in a state set by the earlier food level.
  That is a slow or persistent memory of level, not a transient derivative.
- **Direction:** after a rising history, 7 of 8 N2 and 12 of 16 SH champions move faster
  (raw forward).
- **Whether it helps foraging is not tested.** N2's random champions carry more history than the
  shuffles' at generation 0 (0.095 against 0.030), a structural property for 03 to register.

## 3. Deletion criticality

**Method.** A true deletion operator was added (`wormwars/deletion.py`):
- it removes every chemical edge and gap junction touching the neuron, and its bias;
- it is tested against a separately built 301-neuron network, for several kinds of neuron, and
  against silencing;
- it rejects out-of-range indices.

Each of the 245 eligible neurons (not mapped, not pharyngeal) was deleted from each T1 champion
in turn, scored on 32 probe worlds with the run's seed. Every batch carried a null strain: the
largest null drop was 5.6 × 10⁻⁴, so batching is invisible to that precision. "Critical" means a
drop above 5% of the intact score, 03a's performance margin.

| | champions | critical neurons: mean [t interval] (range) | largest single drop |
|---|---|---|---|
| N2 | 8 | 54.5 [40.9, 68.1] (34-77) | 2.11 |
| SH | 16 | 88.1 [77.0, 99.2] (54-135) | 2.15 |

**N2's critical neurons under three food mappings.** Each mapping has its own separately evolved
champions, 8 per mapping. The count is how many runs a neuron is critical in:

| neuron | M0 (AWA, AWC, ASE) | R1 (ASJ, ASI, ASG) | R2 (PLN, IL2D, IL2V; not amphid) |
|---|---|---|---|
| AIZL / AIZR | 8 / 8 | 6 / 7 | 7 / 4 |
| RIAL / RIAR | 8 / 8 | 7 / 8 | 7 / 6 |
| AIYL / AIYR | 6 / 7 | 8 / 7 | 5 / 6 |
| RIBL / RIBR | 7 / 5 | 3 / 6 | 4 / 3 |
| RIS | 6 | 2 | 4 |

- Correlation of mean deletion cost with M0, over 239 neurons eligible under both: R1 0.84, R2
  0.80. The 20 most critical neurons overlap 10 (R1) and 9 (R2).
- Under R2, the neurons critical in 8 of 8 runs are RIH and RMDR. Others critical in 6 or more
  include CEPV, URYVL, OLL and IL1VR, head neurons next to the turn read-out.
- Under R1, AWC and ASE, eligible there because they are not mapped, are critical in 7-8 runs.
  R1's ASI connects to AWC, AIY, AIZ and RIA, so R1 does not bypass that pathway.
- Across N2's M0 neurons, mean deletion cost correlates 0.47 with degree and 0.29 with summed
  anatomical weight onto the motor read-out. Degree percentiles: RIA 98-99th, AIZ 78-89th, AIY
  58-65th.

**Reading.** AIZ and RIA are critical whatever the food mapping, even when food enters outside the
amphid pathway. Much of the rest of the critical set depends on where food enters and on the
read-out side. RIA is a hub by degree; AIY and AIZ are not unusually connected. The three
mappings used separately evolved champions, so mapping and evolutionary history are not separated
here. A cross-mapping test on frozen genomes would separate them.

## 4. What 03a should take from this

- **The kept-edge concern is partly real.** 03a keeps a target's edges to interface neurons
  fixed. For N2's 12 most critical neurons in each T1-M0 champion (96 targets), 94 have such
  edges. Deleting only those edges costs a median 35% of what full deletion costs, so about a
  third of a typical high-criticality target's headroom is carried by edges 03a keeps.
  Reinsertion with those edges fixed starts partly recovered. 03a's headroom attribute measures
  what is left, and this makes "no headroom" more likely for read-out-adjacent targets.
- **N2's high-criticality panel will contain the AIZ and RIA core** under any food mapping, and
  RIA is a hub. Whether hubs are easier or harder to recover is open.

## 5. Magnitudes

The Spearman correlation (average ranks for ties) between |w| and the anatomical magnitude over
each champion's chemical edges: generation 0, 1.00 for both; generation 39, 0.35 (N2) and 0.36
(SH). Mutation alone predicts erosion of this kind. It supports placing the strength control at
generation 0 (roadmap).

## Changes from v1 (review by Astra 6 and Fable 5.1, D049)

- **Bug:** turn persistence compared neighbouring weys, not the same wey over time. The true
  value is 0.997-0.999 in every group, and v1's "N2 circles a little less" is withdrawn.
- **History control:** the stimulus is now shared by all genomes of a run. The raw read-out
  replaces the clipped motor command, which censored v1's forward numbers. The warm-up is 100
  ticks, not 30. A mutation-only drift control was added. The level-memory reading comes from
  the new steady-state and decay measures.
- **Criticality:** "hubs" is replaced by measured degree percentiles. An R2 control (non-amphid
  food) was added, and "AWC and ASE become critical" is corrected: they were not eligible under
  M0. The kept-edge check for 03a was added.
- **Steering claim withdrawn:** "evolved N2 champions steer toward food; shuffles do not" rested on
  two champions. Within-wey regression shows the turn associated with the food side equally in
  both groups; that is an association, not fitness use (see section 1 and D063).
- **Also:** rank correlations use average ranks, every number comes from `summarise`, a null
  strain goes in every deletion batch, and the wording on maxima and ratios is corrected.
