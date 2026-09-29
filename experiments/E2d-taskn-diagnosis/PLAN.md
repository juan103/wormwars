# E2d: diagnosing Task N after E2's floor fired. Plan (v1, for review)

**Status:** written 2026-09-29, for review by Astra 6 and Fable 5.1. Nothing below has run except
Part A, which reads committed records only.

**Why:** E2's registered floor fired (`experiments/E2-optimizer-screen/`, D124-D126). Random
sampling's champions came within 0.36 targets per episode of 02's GA. The roadmap's rule is: *"E2
finds random sampling matching the GA: diagnose saturation, noise and budget before building on the
task"* (ROADMAP.md, "What would change this roadmap"). E3 waits for this diagnosis.

**What kind of study this is:** exploratory. It asks which of the three candidates limits the
optimizers on Task N, so that E3 is set up on the right footing. It makes no confirmatory claim.
The plan, its measures, its arms and the readings it will draw are fixed here, reviewed, committed
and pushed before any GPU work, as 03m's were. Anything decided after seeing data is labelled.

## Part A: what E2's records already show (done; no GPU)

From `experiments/E2-optimizer-screen/` (hold-out per-world counts, and the training and checkpoint
records). These numbers motivate Parts B and C; they are descriptive.

- **Noise.** The per-world standard deviation of a champion's count on the hold-out is 0.60-1.08
  targets, so the standard error of an 8-world training mean is **0.21-0.38**. From the 32
  champions' per-world counts, resampling k shared worlds 400 times per pair (seed 0), **the
  probability that k worlds rank two genomes correctly** is:

  | Gap between the two genomes' hold-out means | k = 8 (E2's training) | k = 32 | k = 128 |
  |---|---|---|---|
  | 0.05-0.15 (80 pairs) | 0.62 | 0.73 | 0.88 |
  | 0.15-0.30 (122 pairs) | 0.75 | 0.91 | 0.99 |
  | 0.30-0.60 (110 pairs) | 0.90 | 0.99 | 1.00 |

  Near the plateau, where most candidates sit, 8 worlds barely rank genomes better than a coin.
- **Winner's curse.** A nominee's training score overstates its validation mean: random sampling's
  320 nominees by 0.33 (1.15 to 0.81; correlation 0.64), the GA's by 0.19 (1.81 to 1.63;
  correlation 0.85).
- **The GA's population is mostly weak.** Over its last 500 generations, a generation's best scored
  1.92 in training, its mean 0.54, and 24% of its genomes scored 0. The ES's candidates, by contrast,
  averaged 1.28, with 4% zeros (generations 300-622). Mutation of every parameter at 02's scales may
  break most children.
- **A plateau at a known level.** Seven of the GA's eight champions (1.96-2.21) and all eight of the
  ES's (1.93-2.21) scored within a quarter target of **M-avg's 2.20** on the hold-out. M-avg is E1's best tuned *temporal* controller:
  it reads the mean of the two sensors, so it cannot steer by the left-right difference. The stereo
  controller S-const reached 8.65. 04a's champions behaved more like E1's temporal controller than a
  stereo steerer (04a RESULTS.md, corrected).
- **Budget.** The ES was still rising at its end (validation 2.02 at generation 622; 2.31 at 999 in
  the extension). The GA's validation plateaued from about generation 100, apart from one run's late
  jump (D125).

These suggest three readings, not exclusive: **a temporal plateau** (the optimizers find a
temporal strategy whose ceiling is about 2.2, and the stereo strategy lies out of their reach);
**noise** (8 worlds cannot rank candidates near the plateau); **the operators** (the GA's mutation
too large; the ES's σ at its grid's edge). Parts B and C test them.

## Part B: which strategy do the champions use? (GPU, minutes)

- **Genomes:** E2's 32 champions (GA, ES, random sampling, extension) and 04a's 16, from the local
  genome files, each checked against its committed hash first.
- **Probes:** `real`, `mean` (both sensors get their average: the left-right difference removed,
  the temporal signal kept) and `swapped` (the left-right difference reversed). These are 02's stereo
  ablations, already in the world (`food_probe`).
- **Scripted references under the same probes:** S-const (stereo) and M-avg (temporal), at E1's
  frozen parameters. **Expected**, as a check on the probes: S-const collapses under `mean` and
  `swapped`, while M-avg is unchanged under both (it already reads the mean).
- **Worlds:** 1 024 new diagnosis worlds (below), one strain on all of them, composition (1, 1 024,
  1), as in E2's hold-out.
- **Measures, per genome:** the mean count under each probe; **the stereo contribution**, real minus
  mean; and real minus swapped. Reported with a paired percentile bootstrap over worlds (10 000
  resamples, seed 0).
- **The reading, fixed now:** a champion **uses the left-right difference** if both real − mean and
  real − swapped have 95% lower bounds above 0.5 targets. If at most 2 of the 48 champions do, and
  the champions sit near M-avg's level, **the temporal-plateau reading is supported**.

## Part C: do more worlds, gentler mutation or a smaller σ break the plateau? (GPU, about 3.5 h)

**Three arms, 8 runs each, on new seeds and new training worlds.** Each arm changes one thing from
E2, and is compared with E2's own GA or ES re-evaluated on the same diagnosis hold-out (Part B does
that):

| Arm | What changes | From | Generations | Training episodes per run |
|---|---|---|---|---|
| C1, GA with 32 worlds | worlds per genome 8 → 32 | E2's GA | 0-249 | 256 000 (the same) |
| C2, gentle GA | mutation scales halved (w 0.04, g 0.02, τ 0.075, bias 0.025) | E2's GA | 0-999 | 256 000 |
| C3, ES with σ 0.25 | σ 0.5 → 0.25, learning rate 0.3 σ (0.075); no pilot | E2's formal ES | 0-622 | 159 488 |

- Everything else is E2's: Task N, unshaped fitness, 32 genomes per generation, checkpoints every 25
  generations and the last on 256 validation worlds, the champion as the first best checkpoint, the
  code in `scripts/e2.py` and `wormwars/e2/` unchanged.
- **Each arm's 8 champions** go to the same 1 024 diagnosis hold-out worlds, real probe, and
  also `mean`, so Part B's strategy reading covers them too.
- **Comparisons,** each on the same hold-out worlds:
  - C1 and C2 against E2's GA champions;
  - C3 against E2's formal ES champions.

  Reported: the arm's mean minus the reference mean, and a percentile bootstrap over runs (8
  against 8; 10 000 resamples, seed 0). The runs are the unit.
- **The reading, fixed now (descriptive thresholds, not tests):**
  - an arm that beats its reference by **at least 0.3 targets per episode**, with a 90% bootstrap
    interval above 0, supports its reading: **noise** (C1), **the GA's mutation** (C2) or **the ES's
    σ** (C3);
  - an arm within 0.3 of its reference does not.
- **C1 changes the checkpoint schedule's meaning:** 250 generations give 11 checkpoints, not 41.
  Fewer candidates reach validation, which works against C1, and this is stated.

## What the diagnosis decides

Guidance for E3's design, fixed now; E3's own design and review make the choice:
- **A temporal plateau, and no arm breaks it:** the optimizer is not the bottleneck on Task N as it
  stands. The next step is to make the stereo strategy reachable (the sensing geometry, the
  interface, shaping toward left-right steering, or a seeded start), or to build E3 on the temporal
  module knowingly. That is a new design, reviewed.
- **C1 breaks it:** noise limits selection. E3 uses at least 32 worlds per genome, or a comparable
  noise reduction.
- **C2 or C3 breaks it:** the operator was mis-set. E3 uses the better setting.
- **Several arms break it:** they are reported side by side; no combination is run here.

## Worlds, seeds, budget and guards

- **World ids,** in a block no earlier experiment used (991-992 million; a test checks it against
  every earlier range):
  - training: 992 000 000 + [0, 500 000);
  - validation: 992 600 000 + 256;
  - diagnosis hold-out: 992 700 000 + 1 024.

  Seeds: 1 130 000 and up for each arm's runs, disjoint from E2's and 04a's.
- **Budget:**
  - Part B: 48 champions and 2 references under 3 probes, 150 arms × about 3 s, **about 10
    minutes**;
  - Part C: C1 and C2 about 1.3 h each, C3 about 0.85 h, and the hold-out about 5 minutes, **about
    3.5 GPU-hours**.

  **Cap: 5 GPU-hours**, counted by the accounting across attempts.
- **Guards,** E2's: start markers, the cap clock checked before every rollout, not-completed
  records, the rerun rule (once, with a reason), atomic and retried writes. The runner will be
  `scripts/e2d.py`, reusing `scripts/e2.py`'s stage frame and loops. It is written and tested
  (test-first, sabotage-checked) after this plan is agreed. Its exact arm settings are pinned by a
  test against this table.
- **Order:** Part B first (minutes). Then Part C's three arms, one batch each. Then the hold-out
  pass for Part C's champions. Each record is committed and pushed before the next stage.

## What E2d cannot show

- Whether a combination of the changes, or a larger budget, would break the plateau.
- Why a champion uses the strategy it does. Part B measures dependence on the left-right difference,
  not mechanism.
- Anything about other tasks, other graphs (N2 only), or E3's fine-tuning setting.
- With 8 runs per arm, a difference under about 0.3 targets per episode is not resolved.
