# E2d: diagnosing Task N after E2's floor fired. Plan (v4, agreed)

**Status:** written 2026-09-29, for review by Astra 6 and Fable 5.1. Nothing below has run except
Part A, which reads committed records only.
- v1 (`35e0140`, `docs/reviews/20260929-175712-E2d-plan/`): both said "revise" (D129). Part C's
  comparisons were unpaired and C3 changed two settings. The readings claimed more than the probes
  measure. Part A's numbers had no committed script, and two statements in it were wrong. v2 takes
  every must-fix and most suggestions; "Changes from v1" lists them.
- v2 (`213c79e`, `docs/reviews/20260929-181658-E2d-plan-v2/`): both said "revise", narrowly; both
  found the pairing sound (D130). Six gaps remained:
  - GA run 2 could carry an arm's reading by itself;
  - the controls were never replayed;
  - Part B's reading had gaps;
  - the budget reading was already decided by E2's data;
  - C4 could not show an interaction as framed;
  - reruns bypassed the reserve.

  C0 was also underspecified, and three table cells were misrounded. v3 takes all of it; "Changes
  from v2" lists it.
- v3 (`3dad1c7`, `docs/reviews/20260929-182751-E2d-plan-v3/`): both said "revise", text only, for
  two contradictions in C0: the seed table, and a tie rule claimed to match E2's sort (D131).
  Fable: no further round if taken as written. Astra: the last corrections before implementation.
  v4 takes them and the suggestions; "Changes from v3" lists them. **This is the agreed plan:** the
  runner is written and tested against it, and the runner goes to both reviewers before any GPU
  work.

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
  pair with replacement (seed 0), and comparing with the 1 024-world means:

  | Gap | Pairs | k = 8: correct, tied (ties half) | k = 32 | k = 128 |
  |---|---|---|---|---|
  | 0.05-0.15 | 74 | 0.54, 0.16 (0.62) | 0.70, 0.06 (0.73) | 0.86, 0.02 (0.87) |
  | 0.15-0.30 | 113 | 0.69, 0.12 (0.75) | 0.89, 0.03 (0.91) | 0.99, 0.00 (0.99) |
  | 0.30-0.60 | 106 | 0.87, 0.06 (0.90) | 0.99, 0.00 (0.99) | 1.00, 0.00 (1.00) |

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
  formal ES's are within 0.25 of **M-avg's 2.20** on the hold-out (ES run 0 by 0.001). M-avg is E1's best tuned
  controller that reads the mean of the two sensors, so it cannot steer by their difference. The
  stereo controller S-const reached 8.65. Six of the extension's eight champions are above M-avg,
  one at 2.91, so M-avg's level is not a ceiling for these optimizers. (v1 said "all eight of the
  ES's", which was wrong: run 7 is 0.27 below; and "where most candidates sit", which contradicted
  the population figures.)
- **Budget.** The ES was still rising at its end (validation 2.02 at generation 622, 2.31 at 999 in
  the extension; E2's RESULTS.md §5, not produced by the Part A script). The GA's validation mean stayed about level from generation 100 on, apart from one
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
  - **S-const at k = 4** (speed 1.0, turn 0.1, the gain curve's first maximum at k = 4 among E1's
    tuned means), a low-gain stereo steerer. It scored 2.18 on 04a's hold-out, the champions' level,
    so it checks that the rule detects stereo use at the plateau's performance;
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
  - **no material benefit detected:** both contrasts' 95% intervals lie inside (−0.25, 0.25),
    two-sided, so a large negative contrast does not count here. It does not show that the sensors
    are unused;
  - **unclear:** otherwise.

  These classes measure a benefit from intact bilateral input, not a mechanism.
- **The reading, per set.** Sets: E2's GA, formal ES and extension (8 genomes each), and 04a's 12
  shaped and 4 unshaped runs (counted apart, with their own denominators). The
  extension's run 6 is the same genome as the formal ES's run 6; it is counted in both sets, and
  the pooled count of distinct genomes is given beside. Random sampling's champions are classified
  and reported but not read: they sit below the plateau.
  - **"non-stereo"** for a set if at least three-quarters of its genomes have "no material benefit
    detected" and at most 2 "use the left-right difference";
  - **"stereo use present"** for a set if 3 or more use it;
  - **"mixed"** otherwise.

  **"A non-stereo plateau"** is read only if every read set is "non-stereo" and each such set's
  median champion (real probe) lies within 1.90-2.50 (fixed numbers; about M-avg ± 0.3 on E2's
  hold-out, not re-measured).
- **The budget reading, on the same worlds.** The formal ES's champions against the extension's,
  paired by run, all 8 (run 6 is the same genome, a difference of 0), beside selection episodes per
  run: 166 144 formal (plus a share of the pilot's 802 560), and 100 608 more in the extension. The
  extension's champion is chosen over 42 checkpoints, which include the formal ones. Validation
  curves against cumulative episodes are reported.
  - **Already known from E2's hold-out** (disclosed, so this reading is largely a replication on
    fresh worlds): the seven distinct pairs differ by +0.38, +0.11, +0.04, +0.69, +0.24, +0.08 and
    +0.42 (mean 0.28, all positive, 4 of 7 at 0.2 or more; over all 8, with run 6's 0, mean 0.25). v2's "6 of 7 at 0.2" rule would not
    have fired on them, which is why v3 replaces it.
  - **Reading, fixed now:** "budget-limited" if the mean paired gain over the 8 runs is at least 0.2,
    with Part C's intervals (below) above 0. **On E2's hold-out this rule already fires** (mean 0.25
    over 8, none negative, with about 0.01 of world-sampling error), so "budget-limited" is the
    expected result, and the new worlds test whether it holds (Fable). It speaks for more generations of this ES, with more
    checkpoint opportunities; it does not establish a ceiling.

## Part C0: how reliably do 8 worlds rank the comparisons selection makes? (GPU, about 0.45 h)

**A local selection surrogate:** one parent's 64 children, not E2's population of 32 with its
mixed parents and elites. It measures the noise of the comparisons, not the GA's dynamics.
- **The GA's siblings:** for each of E2's 8 GA champions, 64 children at 02's mutation scales × 1,
  × 0.5 and × 0.25, each child on 256 probe worlds. **The same noise draws at every scale:** the
  children's generator is reset to the same per-champion seed (1 131 000 + 10 × champion) for each
  scale, so a child at × 0.5 takes the same draws as at × 1, halved. That holds in the mutation's
  coordinates before clamping; τ is perturbed multiplicatively and the bounds clamp, so the decoded
  genomes are not exactly halfway (Astra). A test checks the draws are equal. **The parent is evaluated too**, on the same 256
  worlds. Composition per champion and scale: (65, 256, 1).
- **The ES's pairs:** for each of E2's 8 formal ES champions, taken as a mean, 32 antithetic pairs
  at σ 0.5 and at σ 0.25, with the same noise draws at both σ (seed 1 131 100 + 10 × champion), each
  candidate and the mean on the same 256 probe worlds. Composition per champion and σ: (65, 256, 1).
- **Measures:**
  - the children's mean counts: their mean, the share scoring under half the parent's, and the share
    scoring 0, per scale;
  - for sibling pairs, pooled over the 8 champions and also per champion: how often 8 worlds rank
    them like the reference (correct, tied). **Each pair is binned once, by its 256-world difference**
    (0.05-0.15, 0.15-0.30, 0.30-0.60). The same 400 draws of 8 worlds, without replacement (seed 0),
    serve every measure. **Each draw is scored against its complement, the other 248 worlds**, so the
    two never share a world. A draw whose complement shows no difference is excluded from that
    pair's rate and counted apart; a draw whose complement reverses the 256-world order is scored
    against the complement, as it stands. The minimum below counts distinct pairs (Fable, Astra);
  - truncation's agreement: the overlap of the top 8 of 64 children by 8 worlds with the top 8 by the
    other 248. Ties in a ranking go to the lower child index, a convention of this measure, tested.
    E2's own sort (`np.argsort` of the negated fitness, not stable) does not guarantee it (Astra);
  - for the ES's pairs: how often an 8-world pair difference has the sign of the 248-world
    difference, and how often it ties. A draw whose 248-world difference is 0 is excluded, per draw,
    and counted apart. This is a proxy: the ES's update uses ranks over all 32 candidates, not pair
    signs;
  - the reference's own uncertainty, as the bootstrap standard error of the 248-world means over
    these candidates (not assumed).
- **Reading (descriptive):** "selection noise is material" if, at 02's mutation scale, 8 worlds rank
  siblings 0.15-0.30 apart correctly (ties counted half) less than 0.8 of the time, pooled. **The
  reading is not drawn for a bin with fewer than 30 distinct pairs.** Per-champion rates are reported
  beside it, because the pooled pairs come from only 8 parents.

## Part C: one-change arms, paired with E2's own runs (GPU, about 4.9 h)

**The controls, replayed first.** "No control arm" holds only if today's code and environment
reproduce E2's runs. Before C1, E2's GA and ES are replayed for generations 0-25, with E2's seeds,
ids and composition (256, 8, 1), and **their generation-0 and generation-25 checkpoint hashes must
equal E2's committed ones** (about 5 GPU-minutes; Fable). They run, like E2 and like the arms, in
the default CUDA mode, not `replay_mode`. **The replay runs twice.** If the two replays agree with
each other and with E2, Part C starts. If they agree with each other but not with E2, that is drift
in the engine or environment. If they disagree with each other, that is nondeterminism in the
default mode, which `docs/REPRODUCIBILITY.md` does not rule out. In either case Part C does not
start, and the difference is reported and reviewed (Fable).

**Pairing.** Every arm reuses E2's run seeds (1 120 000 + r, for r = 0-7), E2's training range and
E2's validation ids. Run r of an arm therefore starts from the same generation-0 population, and
draws its training worlds from the same per-run schedule, as E2's run r.
- E2's runs are the controls; no control arm is rerun.
- Differences are paired by run: the arm's champion minus E2's reference champion with the same run
  seed, both on the diagnosis hold-out.
- E2's training and validation worlds are reused, which is disclosed; the diagnosis hold-out is
  fresh.
- A 32-world draw begins with the 8 worlds of the 8-world draw for the same run and generation.
  This follows from numpy drawing in sequence, not from a guarantee of its interface, so a test
  pins it.
- **A pairing check per arm, recorded:** for C2 and C3, each run's generation-0 checkpoint hash
  equals E2's; for C1 and C4, each run's first 8 training ids at generation 0 equal E2's recorded
  ones, and at generation 249 equal `train_ids` regenerated at 8 worlds (E2 recorded generation 0's
  only).
- **What pairing removes, and what it does not:** it shares the start and the world schedule. The
  trajectories diverge within a generation or two, so it removes start-to-start variation, not
  all seed luck. The arm-reference correlation across runs is reported.

| Arm | What changes | Reference (paired) | Generations | Checkpoints | Selection episodes per run |
|---|---|---|---|---|---|
| C1, GA with 32 worlds | worlds per genome 8 → 32 | E2's GA, champion re-chosen at matched checkpoints | 0-249 | 11 | 258 816 |
| C2, gentle GA | mutation scales halved (w 0.04, g 0.02, τ 0.075, bias 0.025) | E2's GA, its registered champion | 0-999 | 41 | 266 496 |
| C4, both | 32 worlds and halved mutation | as C1 | 0-249 | 11 | 258 816 |
| C3, the ES at σ 0.25 | σ 0.5 → 0.25; the learning rate kept at 0.15 | E2's formal ES, its registered champion | 0-622 | 26 | 166 144 |

- **Matched checkpoints for C1 and C4.** Their 250 generations are checkpointed at 0, 25, …, 225 and
  249. E2's GA covers about the same fractions of training work at generations 0, 100, …, 900 and
  999 (they differ by one generation's work at most, depending on whether the checkpointed
  generation is counted).
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
  failures (champions below 1.0); a paired percentile bootstrap over runs (10 000 resamples, seed 0)
  with a 90% interval; and an exact sign-flip test over the 8 runs (all 256 sign patterns), because
  a percentile bootstrap over 8 runs is narrow. **The bootstrap interval decides the readings**; the
  sign-flip p-value is reported beside it, and a disagreement between them is stated (Fable).
- **Every reading over all 8 runs and over the 7 without run 2** (Fable). E2's GA run 2 started from
  a generation-0 population that scored 0 everywhere and ended at 0.75. An arm's run 2 alone can move
  the mean by about 0.17, and in C1 and C4 the 32 training worlds change that start itself.
- **The readings, fixed now:**
  - **supports:** a mean paired gain of at least 0.3, with the 90% interval above 0, over all 8 runs
    **and** over the 7 without run 2. If it holds over the 8 only: **"supports, carried by run 2"**;
  - **harmful:** a mean paired loss of at least 0.3, with the interval below 0, over all 8 runs and
    over the 7 without run 2 ("harmful, carried by run 2" if over the 8 only);
  - **inconclusive:** anything else, including a gain of 0.3 or more whose interval crosses 0;
  - **leaves the plateau,** reported separately from gains: at least 4 of the arm's 8 champions
    either use the left-right difference (Part B's class) or score at least 2.5 (fixed; about
    M-avg + 0.3 on E2's hold-out). A
    gain can come from avoiding a failed run without exceeding the successful runs' level, and
    that is shown per run.
- **The combined arm, contrasted directly** (both), paired by run, all at 11 matched checkpoints:
  - C4 − C1: only the mutation scale differs, at 32 worlds;
  - C4 − C2′: a work-allocation contrast at halved mutation, since more worlds per genome also
    means fewer generations (Astra). C2′ is C2's champion re-chosen at its 11 matched checkpoints,
    as for E2's GA;
  - **(C4 − C1) − (C2′ − E2's GA′)**, the interaction estimate, with the same intervals.

  **An interaction is claimed only if that estimate's 90% interval excludes 0,** over all 8 runs and
  over the 7 without run 2. Otherwise, a supporting C4 says only that the combined setting is
  promising. **A contrast that needs an incomplete arm is not drawn** (Fable).

## What the diagnosis can suggest for E3

**Leads for E3's design, not conclusions.** E3's own design and review make the choices.
- **Noise:**
  - **C1 supports:** spending more work per evaluation helped here. How much, and in what form (more
    worlds, or re-evaluating the best), is E3's design question;
  - **C0's reading alone:** test increased evaluation effort in E3's design. Noisy rankings do not
    show that more worlds improve the search.
- **Mutation (C2):** gentler mutation is a promising setting for the GA.
- **C4:** the combined setting is promising; an interaction only under the rule above.
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
  - Part C0: the children's noise, 1 131 000 + 10 × champion, reset for each scale; the ES's pairs'
    noise, 1 131 100 + 10 × champion, reset for each σ (champions 0-7). The same draws at every scale
    or σ, as above. (v3 added a scale index here, contradicting C0; Fable, Astra.)
  - Smoke: 1 138 000 and up. The projection: 1 139 100 and up, on smoke ids 0-9 999.
- **The projection first:** it times every new composition at full size on smoke ids:
  - C1 and C4: (256, 32, 1), 8 192 worlds per rollout;
  - C2: (256, 8, 1);
  - C3: one eight-run batch at (256, 8, 1);
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
  | the controls' replay | about 5 minutes |
  | Part C's hold-out pass | about 15 minutes (32 champions and 16 matched references: E2's GA′ and C2′, 3 probes) |
  | **total** | **about 6.0 GPU-hours** (the parts sum to 5.95) |

  **Cap: 7 GPU-hours,** counted by the accounting across attempts.
- **Order:** projection → Part B → C0 → the controls' replay → C1 → C2 → C4 → C3 → Part C's hold-out
  pass. Each record is
  committed and pushed before the next stage.
- **The hold-out pass is protected, in two ways** (both reviewers; E2's own rule exempted reruns):
  - **admission:** any training stage, a rerun included, starts only if the cap's remainder covers its
    projected time plus a 0.5-hour reserve. Otherwise it is skipped (a first attempt) or final and not
    completed (a rerun), recorded as such, and the later stages go on;
  - **a hard stop:** training stages run under a clock whose cap is 7 − 0.5 = 6.5 hours, so an overrun
    stops the stage as "cap reached" before it can spend the reserve. Only the hold-out pass uses the
    full 7 hours. At most one rollout (seconds) can be in flight past the stop.

  The order puts the least central arm (C3) last.
- **Incomplete arms:** an arm that stops is rerun once, as in E2, if admitted; otherwise it is final
  and not completed. Its reading is not drawn, and the other arms' are unaffected. **The hold-out pass
  runs with whatever arms completed**, and records the missing ones.
- **Guards,** E2's:
  - start markers with attempt numbers, the cap clock, not-completed records, and the rerun rule;
  - atomic, retried writes;
  - binding inputs: the code, the configuration, `requirements.txt`, this plan, E1's freeze and gate
    records, E2's training records (the pairing and the checkpoint candidates' hashes), and 04a's
    training records (Part B's genome hashes). The replay above checks, separately, that today's
    engine reproduces E2's runs.
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
  seeds and world schedules, with paired per-run differences, and no control arm to rerun. (v2 said
  "no unpaired seed luck"; pairing removes start-to-start variation, not all seed luck, as v3 says.)
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

## Changes from v2 (review v2, D130)

- **Run 2** (Fable): every Part C reading over all 8 runs and over the 7 without run 2; "supports,
  carried by run 2" otherwise.
- **The controls are replayed** (Fable): E2's GA and ES, generations 0-25, must reproduce E2's
  hashes before Part C starts; plus a recorded pairing check per arm. What pairing does not remove
  is stated, and the arm-reference correlation reported.
- **Part B's reading** (both):
  - "no material benefit detected", two-sided;
  - three-quarters of a set required for "non-stereo", and "mixed" otherwise;
  - the read sets named, with random sampling's excluded;
  - denominators given for the shared genome;
  - the k = 4 reference pinned (speed 1.0, turn 0.1).
- **The budget reading** (Fable, Astra): E2's hold-out figures disclosed; all 8 runs; a mean-gain rule
  with Part C's intervals in place of the count; per-run episodes; the 42 checkpoints; curves against
  cumulative work.
- **The combined arm** (both): explicit paired contrasts, and an interaction only from the
  difference-of-differences, all at 11 matched checkpoints; C0 alone suggests testing evaluation
  effort, not spending it.
- **The reserve** (both): admission for reruns too, and a hard stop at 6.5 hours for training; the
  hold-out pass runs with the arms that completed.
- **C0** (both):
  - labelled a local surrogate;
  - the parents evaluated;
  - the same noise at every scale;
  - disjoint reference worlds, sampled without replacement;
  - pooling, a minimum of 30 pairs, tie rules, zero differences, compositions and seeds;
  - the reference's uncertainty estimated.
- **Part A:** three cells corrected (both); the resampling's replacement stated, and the budget
  figures' source cited (Fable).
- **Also:**
  - a sign-flip test beside the bootstrap (Fable);
  - the 32-world prefix pinned by a test (Fable);
  - 04a's records bound (Astra);
  - the budget recomputed to 5.9 hours with the replay and the larger pass (both noted 5.8 for v2).

## Changes from v3 (review v3, D131)

- **C0's seeds** (both): one seed per champion, reset for each scale or σ, so the draws are equal (as C0
  says); the contradicting scale index removed; "half as far" qualified to the mutation's
  coordinates before clamping (Astra).
- **C0's tie rule** (Astra): lower child index, as this measure's own convention; the claim that E2's
  sort does the same removed (it uses an unstable `argsort`).
- **C0's bins** (Fable, Astra): each pair binned once by its 256-world difference; each draw scored
  against its 248-world complement; zero and reversed complements handled; the minimum counts distinct
  pairs; per-champion rates reported; the same 400 draws for every measure.
- **The replay** (Fable): run twice, in the default CUDA mode like E2, to tell drift from
  nondeterminism.
- **Also:**
  - the budget rule's expected result stated (Fable);
  - C1's and C4's generation-249 ids checked against regenerated `train_ids` (Fable);
  - contrasts that need an incomplete arm not drawn (Fable);
  - the bootstrap decides and the sign-flip test is reported beside it (Fable);
  - run 2's two-way rule applied to "harmful" and the interaction too (Fable);
  - C4 − C2′ called a work-allocation contrast (Astra);
  - the plateau band and 2.5 fixed as numbers (Fable);
  - the matched-fraction wording (Fable);
  - "no unpaired seed luck" corrected in "Changes from v1" (Fable);
  - the budget total 6.0 hours (both).
