# E2d: diagnosing Task N after E2's floor fired. Plan (v2, for review)

**Status:** written 2026-09-29, for review by Astra 6 and Fable 5.1. Nothing below has run except
Part A, which reads committed records only.
- v1 (`35e0140`, `docs/reviews/20260929-175712-E2d-plan/`): both said "revise" (D129). Part C's
  comparisons were unpaired and C3 changed two settings. The readings claimed more than the probes
  measure. Part A's numbers had no committed script, and two statements in it were wrong. v2 takes
  every must-fix and most suggestions; the last section lists them.

**Why:** E2's registered floor fired (`experiments/E2-optimizer-screen/`, D124-D126). Random
sampling's champions came within 0.36 targets per episode of 02's GA. The roadmap's rule is: *"E2
finds random sampling matching the GA: diagnose saturation, noise and budget before building on the
task"*. E3 waits for this diagnosis.

**What kind of study this is:** exploratory. It looks for leads on what limits the optimizers on
Task N, so that E3's design starts from evidence. It makes no confirmatory claim and cannot
overturn E2's registered outcome. The plan, its measures, arms, pairing and readings are fixed
here, reviewed, committed and pushed before any GPU work. Anything decided after seeing data is
labelled.

## Part A: what E2's records already show (done; no GPU)

Computed by `scripts/e2d_records.py` from E2's committed records and written to `part-a.json`
(committed; tested in `tests/test_e2d_records.py`). Descriptive.

- **Noise, as a proxy.** A champion's per-world count on the hold-out has an SD of 0.60-1.08
  targets, so the standard error of its mean over 8 worlds is **0.21-0.38**. This is a proxy: the
  training worlds come from the same generator, but the per-world spread of training candidates was
  not recorded.
- **Ranking two champions by k shared worlds.** For pairs of distinct champions (31: ES run 6 and
  extension run 6 are the same genome), resampling k of their 1 024 hold-out worlds 400 times per
  pair (seed 0), and comparing with the 1 024-world means:

  | Gap | Pairs | k = 8: correct, tied (ties half) | k = 32 | k = 128 |
  |---|---|---|---|---|
  | 0.05-0.15 | 74 | 0.54, 0.16 (0.62) | 0.70, 0.07 (0.73) | 0.87, 0.02 (0.87) |
  | 0.15-0.30 | 113 | 0.69, 0.12 (0.75) | 0.89, 0.03 (0.91) | 0.99, 0.00 (0.99) |
  | 0.30-0.60 | 106 | 0.87, 0.06 (0.90) | 0.99, 0.01 (0.99) | 1.00, 0.00 (1.00) |

  **What this does not model:** selection compares a parent's children (the GA), antithetic pairs
  (the ES) or draws since a checkpoint (random sampling), not unrelated champions. Part C0 measures
  those comparisons directly. (v1 gave 80, 122 and 110 pairs, counting the shared genome twice, and
  did not state the tie convention.)
- **Nominees overstate themselves.** From training to validation:
  - random sampling's 320 nominees fall from 1.15 to 0.81 (correlation 0.64);
  - the GA's fall from 1.81 to 1.63 (0.85).

  The two are not comparable: a random-sampling nominee is the best of 800 draws, a GA nominee the
  best of its generation's 32.
- **The GA's population is mostly weak, in every run.** Over generations 500-999, per run, the
  generation's best averaged 1.09-2.26 in training, its mean 0.44-0.63, and 11-31% of its genomes
  scored 0. The ES's candidates, over generations 300-622, averaged 0.96-1.41, with 1-7% zeros.
- **A plateau at a reference level, not a ceiling.** Seven of the GA's champions and seven of the
  formal ES's are within 0.25 of **M-avg's 2.20** on the hold-out. M-avg is E1's best tuned
  controller that reads the mean of the two sensors, so it cannot steer by their difference. The
  stereo controller S-const reached 8.65. Six of the extension's eight champions are above M-avg,
  one at 2.91, so M-avg's level is not a ceiling for these optimizers. (v1 said "all eight of the
  ES's", which was wrong: run 7 is 0.27 below; and "where most candidates sit", which contradicted
  the population figures.)
- **Budget.** The ES was still rising at its end (validation 2.02 at generation 622, 2.31 at 999 in
  the extension). The GA's validation mean stayed about level from generation 100 on, apart from one
  run's late jump (D125).

## Part B: do the champions use the left-right difference? (GPU, minutes)

- **Genomes:** E2's 31 distinct champions (the GA, the formal ES, random sampling, and the
  extension, with ES run 6 counted once) and 04a's 16, from the local genome files, each checked
  against its committed hash first.
- **Probes** (the world's `food_probe`; `wormwars/world.py`, `_sensor_signals`, applied to the raw
  readings before scaling and the clamp):
  - `real`;
  - `mean`: both sensors get their instantaneous average, so the left-right difference is removed.
    The history of the average is not preserved once the path diverges;
  - `swapped`: the difference is reversed.
- **References** at E1's frozen parameters, under the same probes:
  - **S-const**, the stereo controller (8.65);
  - **S-const at k = 4**, a low-gain stereo steerer from E1's gain curve, near the champions' level.
    It checks that the rule detects stereo use at low performance;
  - **M-avg**, which reads only the mean.
- **Checks, fixed now:**
  - both S-const references lose under `mean` and `swapped` (95% lower bound of real − probe above
    0.5);
  - M-avg under `swapped` is identical on all 1 024 worlds;
  - M-avg under `mean` is within 0.05 of real in aggregate. Its comparisons can flip on rounding, so
    per-world identity is not expected.

  If a check fails, Part B's reading is not drawn, the failure is reported, and Part C's "leaves the
  plateau" falls back to the score alone.
- **Worlds:** 1 024 new diagnosis worlds, one strain on all of them, composition (1, 1 024, 1), as in
  E2's hold-out.
- **Measures, per genome, reported per set** (E2's GA, formal ES, random sampling and extension;
  04a's shaped and unshaped runs): the mean count under each probe; the contrasts real − mean and
  real − swapped, each with a paired percentile bootstrap over worlds (10 000 resamples, seed 0) and
  a 95% interval. Continuous effects are reported for every genome. 04a's run 2 (the module chosen
  for E3), 04a's run 12 and the extension's run 3 are named individually.
- **Classes, fixed now:**
  - **uses the left-right difference:** both contrasts have 95% lower bounds above 0.5;
  - **no detectable use:** both contrasts have 95% upper bounds below 0.25;
  - **unclear:** otherwise.

  These classes measure a benefit from intact bilateral input, not a mechanism.
- **The reading:**
  - **"a non-stereo plateau"** if, in every set, at most 2 champions use the difference, and most
    champions sit within 0.3 of M-avg's level (1.90-2.50);
  - **"stereo use present"** if any set has 3 or more that use it. The plateau is then not simply
    non-stereo.
- **The budget reading, on the same worlds.** The formal ES's champions against the extension's,
  paired by run (run 6 is the same genome), beside cumulative selection episodes:
  - formal: 2 131 712 with the pilot;
  - extended: 804 864 more.

  Reported: per-run differences, their mean and median, and runs improved. **Reading, fixed now:**
  "budget-limited" if the extension beats the formal champion by at least 0.2 in at least 6 of the 7
  distinct pairs. This speaks for more generations of this ES; it does not establish a ceiling.

## Part C0: how reliably do 8 worlds rank the comparisons selection makes? (GPU, about 0.45 h)

- **The GA's siblings:** for each of E2's 8 GA champions, 64 children at 02's mutation scales × 1,
  × 0.5 and × 0.25, each child on 256 probe worlds.
- **The ES's pairs:** for each of E2's 8 formal ES champions, taken as a mean, 32 antithetic pairs
  at σ 0.5 and at σ 0.25, each candidate on the same 256 probe worlds.
- **Measures:**
  - the children's mean counts: their mean, the share scoring under half the parent's, and the share
    scoring 0, per scale;
  - for sibling pairs whose 256-world means differ by 0.05-0.15, 0.15-0.30 and 0.30-0.60: how often 8
    of the 256 worlds, resampled 400 times with seed 0, rank them like the 256 (correct, tied);
  - truncation's agreement: the overlap of the top 8 of 64 children by 8 resampled worlds with the top
    8 by 256;
  - for the ES's pairs: how often an 8-world pair difference has the sign of the 256-world
    difference, and how often it ties.

  The 256-world means are references with their own error, about 0.05, which is stated.
- **Reading (descriptive):** "selection noise is material" if 8 worlds rank siblings 0.15-0.30
  apart correctly, ties counted half, less than 0.8 of the time at 02's mutation scale.

## Part C: one-change arms, paired with E2's own runs (GPU, about 4.9 h)

**Pairing.** Every arm reuses E2's run seeds (1 120 000 + r, for r = 0-7), E2's training range and
E2's validation ids. Run r of an arm therefore starts from the same generation-0 population, and
draws its training worlds from the same per-run schedule, as E2's run r.
- E2's runs are the controls; no control arm is rerun.
- Differences are paired by run: the arm's champion minus E2's reference champion with the same run
  seed, both on the diagnosis hold-out.
- E2's training and validation worlds are reused, which is disclosed; the diagnosis hold-out is
  fresh.
- A 32-world draw begins with the 8 worlds of the 8-world draw for the same run and generation.

| Arm | What changes | Reference (paired) | Generations | Checkpoints | Selection episodes per run |
|---|---|---|---|---|---|
| C1, GA with 32 worlds | worlds per genome 8 → 32 | E2's GA, champion re-chosen at matched checkpoints | 0-249 | 11 | 258 816 |
| C2, gentle GA | mutation scales halved (w 0.04, g 0.02, τ 0.075, bias 0.025) | E2's GA, its registered champion | 0-999 | 41 | 266 496 |
| C4, both | 32 worlds and halved mutation | as C1 | 0-249 | 11 | 258 816 |
| C3, the ES at σ 0.25 | σ 0.5 → 0.25; the learning rate kept at 0.15 | E2's formal ES, its registered champion | 0-622 | 26 | 166 144 |

- **Matched checkpoints for C1 and C4.** Their 250 generations are checkpointed at 0, 25, …, 225 and
  249. E2's GA covers the same fractions of training work at generations 0, 100, …, 900 and 999.
  E2's GA champion is re-chosen among those 11 of its saved checkpoint candidates (the first with the
  best validation mean) and evaluated on the diagnosis hold-out. Its selection episodes match C1's:
  258 816. E2's registered champion (41 checkpoints) is reported beside it.
- **Everything else is E2's:** Task N, unshaped fitness, 32 genomes per generation, 256 validation
  worlds, the champion rule, and the code in `scripts/e2.py` and `wormwars/e2/`, with only the
  arm's settings changed. C3 needs no pilot: its setting is fixed here. It is compared with E2's
  formal ES as a different setting, not as another equal-work contest.
- **Each arm's champions** go to the diagnosis hold-out under `real`, `mean` and `swapped`, so
  Part B's classes cover them. So do the re-chosen matched references.
- **Reported per arm:** each run's paired difference; their mean and median; runs improved, of 8;
  failures (champions below 1.0); and a paired percentile bootstrap over runs (10 000 resamples,
  seed 0) with a 90% interval.
- **The readings, fixed now:**
  - **supports:** a mean paired gain of at least 0.3, with the 90% interval above 0;
  - **harmful:** a mean paired loss of at least 0.3, with the interval below 0;
  - **inconclusive:** anything else, including a gain of 0.3 or more whose interval crosses 0;
  - **leaves the plateau,** reported separately from gains: at least 4 of the arm's 8 champions
    either use the left-right difference (Part B's class) or score at least 2.5 (M-avg + 0.3). A
    gain can come from avoiding a failed run without exceeding the successful runs' level, and
    that is shown per run.

## What the diagnosis can suggest for E3

**Leads for E3's design, not conclusions.** E3's own design and review make the choices.
- **Noise (C1, or C0's reading):** E3 should spend more work per evaluation (more worlds, or
  re-evaluation of the best). How much is E3's design question.
- **Mutation (C2):** gentler mutation is a promising setting for the GA.
- **Only together (C4 supports, C1 and C2 do not):** the two changes interact, and E3 uses both.
- **The ES's σ (C3):** a smaller σ is promising for the ES. This does not reopen E2's decision.
- **Budget (Part B's budget reading):** longer runs are promising for the ES.
- **Harmful arms** are reported as such; E3 avoids those settings.
- **If no arm leaves the plateau, and Part B finds a non-stereo plateau:** these changes do not
  reach the stereo strategy. The next design question is whether to make it reachable (the sensing
  geometry, the interface, shaping toward left-right steering, or a seeded start), or to build E3
  on the non-stereo module knowingly. **This does not show that the optimizer is not a bottleneck:**
  search, representation, budget and their interactions remain open.

## Worlds, seeds, budget and guards

- **World seed:** E1's, 1 100 001.
- **World ids,** new ones in a block no earlier experiment used (991-992 million; a test checks it
  against every earlier range, E2's 995 million block included):
  - diagnosis hold-out: 992 700 000 + [0, 1 024);
  - C0's probe worlds: 992 800 000 + [0, 256).

  Part C reuses E2's training range and validation ids, as above.
- **Seeds:**
  - Part C: E2's (1 120 000-1 120 007), as above.
  - Part C0: the children's and the pairs' noise streams, 1 131 000 + 10 × champion + scale index,
    for GA champions 0-7 and ES champions 0-7 (ES offset by 100).
  - Smoke: 1 138 000 and up. The projection: 1 139 100 and up, on smoke ids 0-9 999.
- **The projection first:** it times every new composition at full size on smoke ids:
  - C1 and C4: (256, 32, 1), 8 192 worlds per rollout;
  - C2: (256, 8, 1);
  - C3: 8 runs at (256, 8, 1);
  - C0: its batches;
  - Part B: (1, 1 024, 1).

  **If the projected total exceeds 6.2 hours, nothing further starts** until a reviewed amendment.
- **Budget:**

  | Part | Estimate |
  |---|---|
  | projection | about 0.1 h |
  | Part B | about 10 minutes (47 genomes and 3 references under 3 probes) |
  | C0 | about 0.45 h |
  | C1, C2, C4 | about 1.35 h each |
  | C3 | about 0.85 h |
  | Part C's hold-out pass | about 10 minutes (32 champions and 8 matched references, 3 probes) |
  | **total** | **about 5.7 GPU-hours** |

  **Cap: 7 GPU-hours,** counted by the accounting across attempts.
- **Order:** projection → Part B → C0 → C1 → C2 → C4 → C3 → Part C's hold-out pass. Each record is
  committed and pushed before the next stage.
- **The hold-out pass is protected:** an arm starts only if the cap's remainder covers its projected
  time plus a 0.5-hour reserve. Otherwise it is skipped, and recorded as skipped. The order puts the
  least central arm (C3) last.
- **Incomplete arms:** an arm that stops is rerun once, as in E2, and is otherwise final and not
  completed. Its reading is not drawn, and the other arms' are unaffected.
- **Guards,** E2's:
  - start markers with attempt numbers, the cap clock, not-completed records, and the rerun rule;
  - atomic, retried writes;
  - binding inputs: the code, the configuration, `requirements.txt`, this plan, E1's freeze and gate
    records, and E2's training records (the pairing and the checkpoint candidates' hashes).
- **The runner,** `scripts/e2d.py`, reuses `scripts/e2.py`'s stage frame and loops. It is written and
  tested (test-first, sabotage-checked) after this plan is agreed. Tests pin the arm table, the seed
  and id mappings, and that `mean` and `swapped` act on Task N's sensors.

## What E2d cannot show

- Whether untried combinations, representations or budgets would break the plateau.
- A mechanism: Part B measures a benefit from intact bilateral input, not how a champion uses it.
- Anything about other tasks, other graphs (N2 only), or E3's fine-tuning setting.
- Clean causal attribution: 8 paired runs per arm give screening evidence. An effect near the 0.3
  threshold may be inconclusive, especially against the GA's between-run spread (SD 0.50 in E2,
  largely one failed run).

## Changes from v1 (review v1, D129)

- **Part C is paired with E2's own runs** (Fable; Astra asked for a declared pairing policy): the same
  seeds and world schedules, with paired per-run differences. No unpaired seed luck, and no control
  arm to rerun.
- **C3 changes only σ**; the learning rate is kept at 0.15 (both).
- **C1's checkpoints are matched,** not only disclosed (Fable, Astra): E2's champion is re-chosen
  among the 11 matching checkpoints, at equal selection episodes.
- **C4 is added** (Fable): the two GA changes together.
- **Part C0 is added** (Fable's operator probe, Astra's fixed-genome comparisons): ranking among
  siblings and antithetic pairs, the comparisons selection actually makes.
- **Part B's reading is renamed and completed** (both):
  - "non-stereo", not "temporal";
  - a middle class, and continuous effects with intervals;
  - per-set counts, and the shared genome counted once;
  - a low-gain stereo reference;
  - check tolerances, and what happens if a check fails;
  - `swapped` for Part C's champions.
- **Budget has a reading** (both): the paired formal-against-extended ES comparison.
- **The decision guidance** no longer says the optimizer is not the bottleneck (both). Leaving the
  plateau is defined apart from gains. Harmful and inconclusive outcomes are defined.
- **Part A is committed as a script and tested** (both). Its tie convention is stated (both), and
  the shared genome counted once. "All eight of the ES's" is corrected to seven, and "where most
  candidates sit" removed (both). The extension's champions above M-avg are noted (Fable).
- **The specification is completed** (Astra): exact seeds, the world seed, the projection with a
  limit, a hold-out reserve, incomplete arms, and binding inputs. The cap rises to 7 GPU-hours for
  C0 and C4.
- **Not taken:** the `hold` probe with M-avg and K (Fable offered it as an alternative to renaming the
  reading; the rename was taken). An ES arm with more worlds (both advised against it for now).
