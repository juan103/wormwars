# M6, step 2: does the champions' foraging depend on their neural time scale? — the plan

*Draft 2, 2026-10-31.*
- **Design review:** the design note ([`M6-STEP2-DESIGN.md`](M6-STEP2-DESIGN.md)) was reviewed in one round by Astra 6
  and Fable 5.1 ([`docs/reviews/20261030-m6-step2-design/`](../reviews/20261030-m6-step2-design/)). Both said "proceed
  to a plan, with fixes".
- **Plan review:** draft 1 of this plan was reviewed in one round
  ([`docs/reviews/20261031-m6-step2-plan/`](../reviews/20261031-m6-step2-plan/)). Both said "agree with fixes".

Every fix from both rounds is taken. The owner's order (D379) put this step after the quick check and before the
stop. It is exploratory and descriptive: no pre-registration, but the genomes, the arms, the measures and the
wordings are fixed here before the run. CPU only.

## What this tests, and what it cannot

**The question, reframed (both reviewers).** The owner asked whether the champions' fading history effect matters
for their foraging. Both reviewers agree that no intervention at this cost isolates that effect, so this step asks the
nearest answerable question: **does the champions' T1 foraging depend on their neural time scale?** The history
effect is part of that time scale; so is how fast the neurons respond to input. Every wording says so.

**The prior expectation, stated now (Fable, as softened by Astra).** T1 is single-nose foraging, so a comparison over
time is a plausible way to climb a gradient. A drop when every neuron is made faster is therefore expected, though
not required by anything shown so far. The informative comparisons are:
- the asymmetry against slowing;
- T0's champions: stereo foraging, where a gradient can be read across the two sensors;
- the interior-only arm;
- the controls, each read separately.

## The intervention: an exact time rescaling

Every neuron's time constant is multiplied by k, `tau → k·tau`, and the substeps per tick are divided by k, 32 →
32/k, on the genome's own configuration, which `Brain` reads. The per-substep update coefficients `c = dt/tau` and
`1 + c(1 + g)` are then unchanged. Under a constant input, one world tick of the scaled brain is exactly 1/k ticks of
the intact brain (Fable). A test checks this bit for bit at k = 0.5 and k = 2, and Astra confirmed it at all five k.
- **What it preserves.** The fixed-point equations ("preserves the fixed-point equations; changes temporal
  responses", Astra). During foraging the inputs change on the unchanged world clock, so the effect on behaviour is
  measured, not assumed.
- **No clamping.** Scaled genomes are never clamped afterwards (Astra). At k = 0.25, a neuron at evolution's floor
  (tau 0.5) sits at 0.125, outside the evolvable range (Fable). Each genome's shares of time constants at the floor
  and at the ceiling are reported.
- **The slowing arms carry a hazard (Fable).** Every brain starts from zero state, so at k > 1 the warm-up transient
  lengthens within the 200-tick episode. A loss at k > 1 can come partly from that.
- **Unchanged.** Each run's interface, gains, configuration, run seed and worlds.

## Genomes, arms and batches

| Genomes | Count | Arms (k) |
|---|---|---|
| T1 champions (g39) | 102 | 0.25, 0.5, 1, 2, 4, interior 0.25, and k = 1 alone |
| T1 generation-0 champions (g00) | 102 | 0.25, 1, 4 |
| T1 drift0, M6-0's first drift replicate (parameter hashes of all three T1 labels checked against `runs/memory-m6-0/genomes.json`) | 102 | 0.25, 1, 4 |
| T0 champions (g39), M0, R1 and R2 | 72 | 0.25, 0.5, 1, 2, 4 |

- **The interior arm** scales every neuron at 0.25 except the sensory neurons and the motor read-out neurons (turning,
  forward and pump), with 128 substeps for all.
  - **What it can show:** whether "the drop also occurs without directly changing sensory and motor time constants"
    (Astra's wording). It cannot rule out sensory or motor response explanations, because the boundary neurons'
    recurrent inputs change.
  - **Integration:** the boundary neurons also integrate more finely than intact (128 substeps with unchanged tau),
    which is negligible at these coefficients (Fable).
- **k = 2 and k = 4 are slowing arms,** reciprocal to 0.5 and 0.25. A loss in both directions is compatible with a
  preferred time scale. It neither establishes a tuned optimum nor counts against memory (Astra).
- **One drift replicate per run** measures drift's response only coarsely (Fable).
- **Batches: one per run and arm, in a fixed order.**
  - For T1 at k = 0.25, 1 and 4: g39, g00, drift0. These arms and the controls are compared within this
    three-strain composition.
  - For T1's other arms (0.5, 2 and interior) and for **k = 1 alone**: g39 by itself. The one-strain arms are read
    against **k = 1 alone**, in the same composition (Astra).
  - The difference between k = 1 alone and k = 1 in three strains is reported as a composition check.
  - For T0: g39 alone at each k.

## Measures and averaging

- **Score:** the task's foraging score (`rollout(...).score`, which normalises surviving energy by starting energy)
  on 02b's 32 criticality worlds (`grid.PROBE_IDS[:32]`). The worlds are the same in every arm, so the comparisons are
  paired.
- **Relative change** per genome and arm: the ratio of the 32-world mean scores against k = 1 in the same composition,
  minus 1.
  - **The primary percentage** is the mean within-champion relative change, not the change in a pooled mean score
    (Astra).
  - **Absolute changes** and the intact baselines are reported beside it, weighted by block like the effects (Astra).
  - **The floor:** a genome whose intact mean is below 0.05 is left out of ratios and listed.
- **Averaging, fixed (Astra):**
  1. worlds within a genome;
  2. paired changes within a run;
  3. runs within a graph-and-run block;
  4. the blocks weighted equally: 30 for T1, 24 for T0.
- **Uncertainty:** a cluster bootstrap over blocks, with 10,000 resamples and `default_rng(20261201)`, for the means
  and for the association intervals.

## The checks before the reading

- **Completeness (Astra).** Every required genome, label, arm and probe field must be present. Every score must have
  32 finite world values whose mean is the recorded mean. Anything missing makes the reading inconclusive.
- **Consistency against 02b.** For the 24 T1-M0 champions, the k = 1 score must match 02b's committed intact score
  (`experiments/02b-champion-analysis/criticality.json`, computed on the GPU) within 2% relative. The timing run matched
  to 0.02%. A failure makes the reading inconclusive.
- **Validation on the probe** (Astra's design; Fable's numeric criteria). Each T1 run's own bank, from M6-0's
  `banks.json`, is frozen across arms. Only the champions are probed (both: the controls' probes are cut).
  - **Primary measure (writing held fixed):** the two ramp-end states are written at k = 1, then the same states are
    continued for 100 ticks under each arm. The measure is the read-out difference integrated over ticks 1 to 100.
  - **Supporting measure:** the whole probe under each arm (writing and decay together), summarised as a median ratio.
  - **Pass:** among champions whose written difference is at least 1e-3, the median ratio of the integral at k = 0.25
    to k = 1 is below 0.5, at least 90% are below 1, and the median ratio at k = 4 is above 1.
  - **The success is empirical (Astra).** An exact rescaling makes it expected, not guaranteed, for nonlinear
    trajectories over a finite window. It checks the implementation, not the hypothesis.
  - **Reported:** the individual champions not below 1 (or not above 1 at k = 4), zero denominators, and the switch
    champion's row (T1-MS-N2 run 7).
- **Any failed check gates every interpretive sentence,** including the controls'. The numbers are still reported
  (Astra, Fable).

## The readings, fixed now

**Primary:** the T1 champions' mean within-champion relative change at k = 0.25, over the 30 blocks.
- **Interval below zero:** "Making every neuron four times faster reduced the champions' T1 foraging score (mean
  within-champion change …, 95% interval … to …)."
- **Interval above zero:** "… increased …".
- **Otherwise:** "No reliable mean reduction of the champions' T1 foraging score was detected when every neuron was
  made four times faster (…)."
- **Always added:** "This tests the champions' dependence on neural time scale; it does not establish that the
  probe-defined fading history effect mediates any benefit, because faster neurons also respond faster."
- **Sensitivity, prespecified (Astra):** the same without the switch champion.

**Secondary, each with its interval:**
- **Each control separately.** Per run, the champion's absolute change minus the control's, over the champion's
  intact score (a common denominator; Fable), at k = 0.25 and at k = 4.
  - **If the primary is a reduction:**
    - interval below zero: "The reduction exceeded that of the generation-0 champions" (or "the drift genomes");
    - interval above zero: "The reduction was smaller than that of …" (Fable);
    - otherwise: "A champion reduction with no detected excess over …".
  - **Otherwise:** "The champions' change compared with …: reduced / increased / none detected (champion minus
    control)."
  - **Caveat:** these controls score lower and do not estimate a universal generic cost. A floor in their scores
    biases the difference towards specificity (Fable, Astra). Their baselines are reported, weighted by block.
- **The other k:** the champions' relative and absolute changes at 0.5, 2 and 4.
- **The interior arm:** its relative change, and its difference from full scaling at 0.25.
- **T0 against T1.**
  - **Matched:** at 0.25, matched by graph, run and **mapping** (M0, R1 and R2; T1's MS runs have no T0 counterpart),
    then averaged within blocks (Astra).
  - **T0's own changes** at each k, and its baseline.
  - **Interpretation:** a larger T1 drop supports the single-nose account; similar drops point to something generic
    to evolved controllers at this time scale (Fable).
- **Association, not a dose-response (Astra).** Spearman with average ranks for ties (scipy), over the 102 champions,
  of the change at 0.25 against M6-0's a (own bank) and against the median tau, with intervals from resampling blocks.
  Undefined draws are counted.
- **The tau profiles:** the median tau, and the shares at the floor and the ceiling, by genome set.

**Removed:** the design note's claim that a 10% difference should be visible (both). Precision is reported as found.

## Seen before this plan, disclosed

All of the following are archived in [`timing-runs.md`](../reviews/20261030-m6-step2-design/timing-runs.md):
- **Timing runs on T1-M0-N2 run 0's champion,** 32 worlds:
  - tau scaled, substeps unchanged: 2.82 (k = 1), 2.62 (0.5), 2.08 (0.25), 2.84 (2), 2.23 (4);
  - the exact rescaling: 2.82, 2.04 (0.25), 2.61 (0.5), 2.83 (2), 2.23 (4).
- **T0-M0-N2 run 0's intact score:** 2.76.
- **A 2-world smoke run of the driver on T1-M0-N2 run 0:**
  - g39: 2.88 (1), 2.05 (0.25), 2.67 (interior);
  - g00: 2.36, 2.59, 1.90 at k = 1, 0.25 and 4;
  - drift0: 0.76, 0.75, 1.22 at k = 1, 0.25 and 4.

These genomes stay in the run.

## Outputs, cost and tests

- **Code:** `scripts/memory_m6/step2.py` (stages `genomes`, `scores`, `probe`), `step2_read.py` and
  `sabotage_step2.py`.
- **Records:** in `runs/memory-m6-step2/` (`genomes.json`, `scores.json` with per-world scores, `probe.json`,
  `reading.json` and a committed copy of the compute record). The results go in `docs/memory/M6-STEP2-RESULTS.md`.
- **Resumable.** The scores stage saves after every run (`scores.partial.json`) and resumes from it after a stop
  (Fable, Astra).
- **Cost, from the timing runs.** A run's load is strains times substeps, summed over its batches: 744 for a T1 run and
  248 for a T0 run, at about 0.144 s a unit on 32 worlds.
  - the scores: about 3.75 hours;
  - the probe: about 15 to 30 minutes.

  **About 4 to 4.3 CPU hours.** The cap is 5, what the owner was told. It is checked before every batch and every
  probe arm. After the first three runs, a forecast weighted by load stops the run for the owner if the scores alone
  would leave less than 30 minutes of the cap for the probe.
- **Tests** (`tests/test_memory_m6_step2.py`; 15 pass, log `runs/step2-tests.txt`). Each was seen failing under a
  sabotage of the code it checks (19 of 19, `runs/step2-sabotage.txt`):
  - the exact rescaling, bit for bit;
  - no clamping, the interior boundary, and a refusal of inexact k;
  - the batch composition, including k = 1 alone;
  - the forecast weighted by load;
  - the genomes against M6-0's hashes, and the real `score_run` and `probe_one` paths on one world (both local);
  - the reader's wordings: reduced, null and increased; exceeded, no excess and smaller than;
  - every sentence gated on a failed check;
  - a missing arm making the reading incomplete;
  - the floor;
  - T1 minus T0 matched by mapping;
  - Spearman with ties;
  - the composition baseline.
