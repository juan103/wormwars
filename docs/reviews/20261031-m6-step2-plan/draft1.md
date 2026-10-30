# M6, step 2: does the champions' foraging depend on their neural time scale? — the plan

*Draft 1, 2026-10-31, before review. The design note ([`M6-STEP2-DESIGN.md`](M6-STEP2-DESIGN.md)) was reviewed in one
round by Astra 6 and Fable 5.1 ([`docs/reviews/20261030-m6-step2-design/`](../reviews/20261030-m6-step2-design/)).
Both said "proceed to a plan, with fixes", and every fix is taken here. The owner's order (D379) put this step after
the quick check and before the stop. Exploratory and descriptive: no pre-registration, but the genomes, the arms, the
measures and the wordings are fixed here before the run. CPU only.*

## What this tests, and what it cannot

**The question, reframed (both reviewers).** The owner's question was whether the champions' fading history effect
matters for their foraging. Both reviewers agree that no intervention at this cost isolates that effect. This step
asks the nearest answerable question: **does the champions' T1 foraging depend on their neural time scale?** The
history effect is part of that time scale, but so is how fast they respond to input. The readings say so in every
wording.

**The prior, stated now (Fable).** T1 is single-nose foraging. With one sensor, climbing a gradient needs a
comparison of the level now with the level a moment ago. So a drop when every neuron is made faster is the expected
result, and a null would be the surprise. The informative comparisons are these:
- the asymmetry against slowing;
- T0's champions: stereo foraging, where a gradient can be read across the two sensors without comparing over time;
- the interior-only arm;
- the controls, each read separately.

## The intervention: an exact time rescaling

Every neuron's time constant is multiplied by k, `tau → k·tau`, and the substeps per tick are divided by k, 32 →
32/k. Then the per-substep update coefficients `c = dt/tau` and `1 + c(1 + g)` are unchanged, so one world tick of
the scaled brain is exactly 1/k ticks of the intact brain under a constant input (Fable). A test checks this bit for
bit at k = 0.5 and k = 2.
- **What it preserves.** The fixed-point equations are unchanged (Astra's wording: "preserves the fixed-point
  equations; changes temporal responses"). During foraging the inputs change on the unchanged world clock, so the
  effect on behaviour is measured, not assumed.
- **No clamping.** Scaled genomes are never clamped afterwards (Astra). At k = 0.25 a neuron at evolution's floor
  (tau 0.5) sits at 0.125, outside the evolvable range (Fable). Each genome's share of time constants at the floor and
  at the ceiling is reported before the readings.
- **Unchanged.** Each run's interface, gains, configuration, run seed and worlds stay as they are. The batch
  composition is fixed below.

## Genomes and arms

| Genomes | Count | Arms (k) |
|---|---|---|
| T1 champions (g39) | 102 | 0.25, 0.5, 1, 2, 4, and **interior 0.25** |
| T1 generation-0 champions (g00) | 102 | 0.25, 1, 4 |
| T1 drift0, M6-0's first drift replicate (same seed, parameter hash checked against `runs/memory-m6-0/genomes.json`) | 102 | 0.25, 1, 4 |
| T0 champions (g39), M0, R1 and R2 | 72 | 0.25, 0.5, 1, 2, 4 |

- **The interior arm** scales every neuron at 0.25 except the sensory neurons and the motor read-out neurons
  (turning, forward and pump), with 128 substeps for all of them. If it costs as much as full scaling, the simplest
  latency story (slower sensing or slower motor output) does not explain the drop (Fable).
- **k = 2 and k = 4 are slowing arms.** k = 2 is reciprocal to 0.5 and k = 4 to 0.25 (Astra, Fable). A loss in both
  directions is compatible with a preferred time scale; it neither establishes a tuned optimum nor counts against
  memory (Astra).
- **One drift replicate per run** measures drift's response only coarsely (Fable). Its identity is fixed: M6-0's
  drift0.
- **The batch composition is one batch per run and arm,** in a fixed order:
  - for T1 at k = 0.25, 1 and 4: g39, g00, drift0;
  - for T1's other arms, and for T0: g39 alone.

## Measures

- **Score:** T1's or T0's foraging score (`rollout(...).score`, which already normalises surviving energy by starting
  energy) on 02b's 32 criticality worlds (`grid.PROBE_IDS[:32]`). The worlds are the same for every arm, so the
  comparisons are paired.
- **Relative change** per genome and arm: the ratio of the 32-world mean scores, `score(k)/score(1) − 1`. Absolute
  changes are reported beside it. A genome whose intact mean is below 0.05 is left out of ratios and listed (Astra:
  check denominators).
- **Averaging, fixed (Astra):**
  1. worlds within a genome;
  2. paired changes within a run;
  3. runs, the mappings, within a graph-and-run block;
  4. the blocks weighted equally: 30 for T1, 24 for T0.
  - **Uncertainty:** a cluster bootstrap over blocks, with 10,000 resamples and `default_rng(20261201)`.

## The checks before the reading

- **Consistency against 02b:** for the 24 T1-M0 champions, the k = 1 score must match 02b's committed intact score
  (`experiments/02b-champion-analysis/criticality.json`, computed on the GPU) within 2% relative. The timing run matched
  to 0.02%. A failure makes the reading inconclusive.
- **Validation on the probe (Astra's design; numeric criteria per Fable).** Each T1 run's own bank, from M6-0's
  `banks.json`, is frozen across arms.
  - **Primary measure (writing held fixed):** the two ramp-end states are written at k = 1, then the same states are
    continued for 100 ticks under each arm. The measure is the read-out difference integrated over ticks 1 to 100.
  - **Supporting measures:** the whole probe under each arm (writing and decay together), with its ramp-end
    difference a and integrated difference.
  - **Pass:** among champions whose written difference is at least 1e-3, the median ratio of the integral at k = 0.25
    to k = 1 must be below 0.5, at least 90% must be below 1, and the median ratio at k = 4 must be above 1.
  - **This checks the implementation, not the hypothesis.** For an exact rescaling, the history shrinks by
    construction. A failure makes the reading inconclusive.
  - **Individual failures** are reported, not selected out. The one switch champion (T1-MS-N2 run 7) is identified in
    the records.
- **Incomplete:** any run missing from the scores or the probe makes the reading inconclusive.

## The readings, fixed now

**Primary (Astra, Fable):** the T1 champions' own paired relative change at k = 0.25, averaged over the 30 blocks.
- **Interval below zero:** "Making every neuron four times faster reduced the champions' mean T1 foraging score (mean
  change …, 95% interval … to …)."
- **Interval above zero:** "… increased …".
- **Otherwise:** "No reliable mean reduction of the champions' T1 foraging score was detected when every neuron was
  made four times faster (mean change …, 95% interval …)."
- **Always added:** "This tests the champions' dependence on neural time scale; it does not establish that the
  probe-defined fading history effect mediates any benefit, because faster neurons also respond faster."

**Secondary, each with its interval:**
- **Each control separately (Astra).** Per run, the champion's absolute change minus the control's, both divided by
  the champion's intact score, which is a common denominator (Fable), at k = 0.25 and at k = 4.
  - **If the primary is a reduction:** "The reduction exceeded that of the generation-0 champions" (or "the drift
    genomes") when the interval lies below zero. Otherwise: "A champion reduction with no detected excess over …".
  - **Caveat:** these controls score lower and do not estimate a universal generic cost. A floor in their scores
    biases the difference towards specificity (Fable, Astra). Their intact means are reported.
- **The other k:** the champions' relative change at 0.5, 2 and 4.
- **The interior arm:** its relative change, and its difference from full scaling at 0.25.
- **T0:** its champions' relative change at each k, and T1 minus T0 at 0.25 over the 24 graph-and-run blocks the two
  tasks share. A larger T1 drop supports the single-nose account. Similar drops point to something generic to evolved
  controllers at this time scale (Fable).
- **Association, not a dose-response (Astra):** Spearman, over the 102 champions, of the change at 0.25 against M6-0's
  a (own bank) and against the median tau, with intervals from resampling blocks.
- **The tau profiles:** the median tau, and the shares at the floor and the ceiling, by genome set.

**Removed from the design note:** the claim that a 10% difference should be visible (both). Precision is unknown and
is reported as found.

## Seen before this plan, disclosed

- **A timing run on T1-M0-N2 run 0's champion,** 32 worlds, with scaled tau but unchanged substeps: mean scores 2.82
  (k = 1), 2.62 (0.5), 2.08 (0.25) and 2.84 (2).
- **Timing runs of the exact rescaling** on the same champion: 2.82, 2.04 (0.25), 2.61 (0.5), 2.83 (2) and 2.23 (4).
- **A 2-world smoke run of the driver on the same run:**
  - g39: 2.88 (1), 2.05 (0.25), 2.67 (interior);
  - g00: 2.36, 2.59 and 1.90 at k = 1, 0.25 and 4;
  - drift0: 0.76, 0.75 and 1.22 at k = 1, 0.25 and 4.
- **One T0 champion's intact score** (T0-M0-N2 run 0: 2.76).

These genomes stay in the run, labelled as seen.

## Outputs, cost and tests

- **Code:** `scripts/memory_m6/step2.py` (stages `genomes`, `scores`, `probe`), `step2_read.py` and
  `sabotage_step2.py`.
- **Records:** in `runs/memory-m6-step2/` (`genomes.json`, `scores.json` with per-world scores, `probe.json`,
  `reading.json` and the compute record), all committed. The results go in `docs/memory/M6-STEP2-RESULTS.md`.
- **Cost, from the timing runs.** The cost per genome-arm is proportional to the substeps: about 4.6 s at 32, 17.6 s at
  128 and 1.4 s at 8, on 32 worlds.
  - T1 champions at five k: about 60 minutes;
  - the interior arm: about 30 minutes;
  - the g00 and drift0 controls at three k: about 80 minutes;
  - T0 at five k: about 42 minutes;
  - the probe: about 10 minutes.

  **About 3.7 CPU hours.** The cap is 5 (what the owner was told), checked before every batch, with a forecast after
  the first three runs that stops the run for the owner if it projects past 85% of the cap.
- **Tests** (`tests/test_memory_m6_step2.py`, 10), each seen failing under a sabotage of the code it checks (15 of 15,
  `runs/step2-sabotage.txt`):
  - the exact rescaling, bit for bit;
  - no clamping, the interior boundary, and a refusal of inexact k;
  - the batch composition;
  - the genomes against M6-0's hashes (local);
  - the reader's wordings: reduced, null and increased, with and without excess over a control;
  - the inconclusive guards: consistency, validation and incompleteness;
  - the floor, and T1 minus T0.
