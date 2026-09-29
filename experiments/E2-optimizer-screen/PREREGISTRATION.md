# E2: a short optimizer screen. Pre-registration (v2, for review)

**Status:**
- Written 2026-09-29 for review by Astra 6 and Fable 5.1. Nothing below has run on E2's training,
  validation or hold-out worlds, or with its formal or pilot seeds (§11).
  - v1 (`12725de`, `docs/reviews/20260929-105911-E2-prereg/`): both said "revise": failure handling
    (a kill broke "final"), outcome wording, a stopped extension losing its champions, hold-out arms
    not durable across a kill, and two wrong exposure statements (D120). Every must-fix is adopted
    in v2, and most suggestions; §14 lists them.
- **The order:** review until both agree; bind (a commit); push; the guarded projection and a
  guarded smoke run on the binding commit; then the formal stages, each on a clean tree whose HEAD
  is pushed, with each stage's record committed and pushed before the next stage starts.
- **The binding commit** is the commit the projection records. Every later stage refuses to run if
  the code, the configuration, `requirements.txt`, this file, or E1's freeze and gate records differ
  from it.

**Design:** [`docs/E2/DESIGN.md`](../../docs/E2/DESIGN.md) v2.2, reviewed three times by both
reviewers (D117, D118; reviews under `docs/reviews/20260929-*-E2-design*`). Where this file and the
design differ, this file governs, and the difference is listed in §13.

**Code:**
- the runner is [`scripts/e2.py`](../../scripts/e2.py). Its `REGISTERED` constant holds every number
  below, and it applies every rule mechanically, the projection limit and the decision included;
- the ES and random sampling are `wormwars/e2/optimizers.py` (the encoding, the utilities, the ES
  update, the best-since-checkpoint rule) and `wormwars/e2/loops.py` (the batched loops, mirroring
  04a's `evolve_batch`). The ES's registered constants (16 pairs, Adam's β₁, β₂ and ε, the encoding
  scales) are the code's defaults and the loop's population / 2; a test pins the equality;
- 02's GA is 04a's `wormwars/e04a/evolve.py`, `evolve_batch`, **unchanged**, with 04a's registered
  settings;
- the shared guards are `wormwars/registration.py`; Task N and E1's controls come from
  `scripts/e1.py` and `wormwars/e1/`, unchanged.

**How it is tested** (AGENTS.md rules 7 and 9; each test was seen failing first, and the checks that
could pass vacuously were sabotage-checked):
- **no engine change:** E2 adds no simulator code. The rollout, the world and the brain are 04a's
  (its engine-equivalence check, D103);
- **the GA** (`tests/test_e2_commands.py`): E2's call and a direct `evolve_batch` call with 04a's
  configuration give the same checkpoint and final-population hashes on the CPU for the same seeds
  (a fake simulator), and E2's registered GA settings equal 04a's. Sabotage: 2 elites instead of 3
  fails both;
- **the ES and random sampling as functions** (`tests/test_e2_optimizers.py`, 14 tests): the
  encoding round-trips and its scales; decoding clamps; projection lands inside the bounds; centred
  average ranks, equal fitness giving equal utility; the ES climbs a quadratic, does not move on a
  flat function, uses antithetic pairs, moves in the fitness's direction; **a flat batch after real
  updates changes nothing, not the mean, Adam's moments or its counter, and neither does a batch in
  which every pair ties within itself**; best-since-checkpoint and its ties. Sabotage: ordinal
  instead of average ranks fails 3 tests; removing the flat guard fails 2;
- **the loops** (`tests/test_e2_loops.py`, 16 tests, a fake simulator): each run's strains play that
  run's own worlds in one batch; random sampling nominates the best since the last checkpoint; the
  ES starts from the best of its start screen; it climbs on the fake score; **a flat run leaves the
  mean exactly at the start** (no projection without an update); resuming from a saved state
  reproduces the uninterrupted run; the checkpoint schedule; a run gives the same result alone and in
  a batch, for both methods; the pilot's paired settings on one seed; a non-finite score stops the
  batch; **all three methods start from the GA's generation-0 population on the GA's generation-0
  worlds**; the flat count is current at every checkpoint. Sabotage: projecting on every generation,
  nominating without a reset, seeding by batch position (random sampling, and the ES's noise), and
  updating the flat count only at the end each fail their test;
- **the stages** (`tests/test_e2_commands.py`, 62 tests, fake rollouts, smoke sizes, a scratch
  folder): every smoke id below 10 000; each stage needing the one before, running once, and not
  starting when the cap is spent; the projection gate, and an over-limit projection recording the
  experiment's outcome; the pilot's pairing, selection and tie order; the formal ES using the pilot's
  setting and saving its state (a plain sha256); the extension continuing the formal runs, refusing a
  changed state file, and keeping champions over what completed when it stops (before and after its
  first checkpoint); the extension's ties going to the formal checkpoint; one strain on all 1 024
  hold-out worlds, with the three probes; the champion-hash check before any hold-out world; a
  partial hold-out record after every arm; **the rerun rule under every combination of crash and
  kill** (crash then crash, kill then crash, crash then kill, kill then kill: each ends final, a
  killed rerun charged and recorded as final by one more `--rerun`); smoke projections on their own
  seeds; a transient permission error on an atomic write retried; the pairing check; the allowance,
  the checkpoint counts and the decision rule as functions (11 cases, and an incomplete ES's
  distinct outcome). Sabotage: `>` for "at least" in the margin or the floor, ties at the GA's
  median counted as above, no rerun required before a stage is final, a rerun counted as used only
  by an archived record, no final record for a killed rerun, an incomplete ES read as "keep", a
  stopped extension's champions dropped, no per-arm partial record, ties to the smaller σ, smoke
  projections on the formal seeds, no state-hash check, no champion-hash check, unpaired pilot
  seeds: each fails its test;
- **the command tests run with the formal guards off** (`smoke=True, guarded=False`). The guards are
  tested as functions in `tests/test_registration.py`; their wiring, the live push check and the GPU
  preflight run in the guarded projection and the guarded smoke run on the binding commit.

## 1. The question, and what E2 cannot show

**Given the same additional simulator work, does OpenAI-ES find better Task N navigators than 02's
GA, starting from random N2 genomes?** The answer chooses **E3's provisional default optimizer**
(ROADMAP.md, Track E, "E2: short optimizer screen").

- 04a showed 02's GA finds cue-following navigators in most runs, but weak ones: 2.0-2.8 targets per
  300-tick episode, 23-32% of an oracle (04a `RESULTS.md`, with its corrections, D111).
- **Random sampling is the floor**, not a candidate: if it comes within 0.5 targets of the GA, the
  task or the budget needs diagnosing before E3 builds on it (ROADMAP.md, "What would change this
  roadmap").
- **E2 measures learning from random initialisation, under unshaped fitness only.** E3 starts from
  validated modules and fine-tunes; optimizer rankings need not transfer. A better E2 champion does
  not inherit 04a's evidence: it needs 04a's reliability, baseline and cue checks before E3 uses it.
- **The run is the unit of analysis:** 8 runs per method. Worlds quantify uncertainty for one
  champion; they are not replicates of a method.
- It is not the topology × optimizer study, which belongs to Track B.

## 2. What is fixed from E1 and 04a

- **Task N exactly as E1 and 04a ran it:** σ = 6, 300 ticks, one wey, energy off, E1's world seed
  1 100 001. The resolved configuration is built by E1's own function and checked against E1's gate
  record (`experiments/E1-navigation/gate.json`) by hash, as in 04a; E1's freeze and gate records
  are guarded files.
- **N2 only**, 04a's genome: 5 404 parameters (chemical weights, gap conductances, time constants,
  biases), bounds w ∈ [−3, 3], g ∈ [0, 2], τ ∈ [0.5, 20], bias ∈ [−2, 2]; 02's initial distribution
  (`Genome.random`: anatomical magnitudes with random signs); single-strain padding on.
- **Fitness: the raw count of targets reached, averaged over the strain's 8 training worlds, for
  every method.** No shaping. Every validation and hold-out score is the raw count.

## 3. The methods

**Common to all three:** 32 genomes per run per generation, each on the run's 8 training worlds for
that generation (256 episodes); the worlds are `train_ids(run seed, generation)` in E2's training
range (§5), so **run r of every method sees the same world schedule**. **Generation 0 is each run's
start and is the same for every method:** 04a's `initial_population(run seed)`, the GA's own, on
generation 0's worlds (tested). Generations are counted from 0.

1. **Random sampling.** Each generation draws 32 fresh genomes from 02's distribution, continuing
   the run's initialisation stream (so its generation 0 is the GA's). At each checkpoint the
   candidate is **the genome with the highest training score since the previous checkpoint** (the
   generation-0 checkpoint: generation 0's best), ties to the earliest. Generations 0-999.
2. **02's GA, as 04a ran it:** 04a's `evolve_batch` unchanged: 3 elites, the top 8 as parents,
   Gaussian mutation of every parameter (w 0.08, g 0.04, τ 0.15 multiplicative, bias 0.05), one
   island; the candidate at a checkpoint is that generation's best by training fitness (with c = 0,
   the mean count). Generations 0-999. Its settings are inherited, so it pays no tuning cost in E2
   ("equal additional E2 work", not equal historical effort).
3. **OpenAI-ES:**
   - **Encoding:** z = (w / 0.08, g / 0.04, ln τ / 0.15, bias / 0.05), the GA's mutation scales, so one
     σ fits every coordinate. A candidate is decoded from z and clamped to the bounds; the gradient
     uses the unclamped perturbations.
   - **Start (generation 0):** the start screen is generation 0's 32 genomes (the GA's generation 0);
     the best by training count, ties to the earliest, becomes the mean. Its score and index are
     recorded.
   - **Each later generation:** 16 directions ε ~ N(0, I) from the run's own noise stream (seeded by
     the run seed and a fixed key), each evaluated with both signs, mean ± σε (32 candidates), on
     the generation's 8 worlds. **Utilities:** average ranks over all 32 fitnesses, centred to
     [−0.5, 0.5]. **If every fitness is equal, or every antithetic pair ties within itself, nothing
     changes:** not the mean, not Adam's moments, not its step counter (a "flat" generation).
     Otherwise the gradient estimate is g = Σᵢ (u⁺ᵢ − u⁻ᵢ) εᵢ / (2 × 16 × σ) and Adam ascends it
     (β₁ 0.9, β₂ 0.999, ε 10⁻⁸, bias correction, **no weight decay**), then **the mean is projected
     into the bounds** (decoded, clamped, re-encoded), only after a real update.
   - **σ and the learning rate are constant** within a run, chosen by the pilot (§4); the learning
     rate is a multiple of σ.
   - **The candidate at a checkpoint is the mean, decoded, after that generation's update** (at
     generation 0, the decoded start). The best sampled offspring is not used.
   - **Formal runs: generations 0-622** (the start and 622 updates; §4).
   - **Recorded per run:** the start score, the first non-flat generation, the number of flat
     generations, and per generation the share of candidate coordinates changed by more than 10⁻³ by
     clamping.
   - **Stated limitation:** 16 directions on 8 worlds is the GA's evaluation shape, chosen for equal
     composition and batching; more directions on fewer worlds might suit an ES better.

No other method (no ARS, no sep-CMA-ES): the spare budget went to replication (D117).

## 4. Tuning (the ES's pilot) and the allowance

**The pilot** tunes the ES only, on its own worlds and seeds (§5):
- **Stage 1:** σ ∈ {0.5, 1, 2} at a learning rate of 0.3 σ, 3 runs each (9 runs, one batch).
- **Stage 2:** at the σ chosen in stage 1, learning rates {0.1, 1} × σ, 3 runs each (6 runs, one
  batch); stage 1's three runs at (σ, 0.3 σ) are reused.
- **Pairing:** replicate k of every setting uses the pilot seed 1 121 000 + k, so the settings share
  their start screens, world schedules and noise draws.
- **Each pilot run is generations 0-199**, with checkpoints at 0, 25, …, 175 and 199 on the pilot's
  256 validation worlds.
- **Selection, at the generation-199 checkpoint:** stage 1 chooses the σ whose three runs have the
  highest total validation count; stage 2 chooses the learning-rate multiple with the highest total
  at that σ among {0.1, 0.3, 1}. **Ties go to the middle setting first:** σ in the order 1, 0.5, 2,
  and the rate in the order 0.3, 0.1, 1 (Fable, review v1: "the smaller" would send an all-zero pilot
  to the setting least able to leave a plateau). A stage in which every setting has the same total is
  recorded as **uninformative**: its choice is the tie order alone, and the results say so. With 3
  runs per setting, differences under about 0.6 targets are noise; the pilot screens, it does not
  estimate.

**The allowance: selection episodes, training plus the checkpoint validations that select champions**
(design v2.2). Checkpoints are at generation 0, every 25th, and the last.

| Method | Calculation | Episodes |
|---|---|---|
| GA | 8 runs × (1 000 × 256 + 41 × 256) | 2 131 968 |
| random sampling | the same | 2 131 968 |
| ES, pilot | 15 runs × (200 × 256 + 9 × 256) | 802 560 |
| ES, formal | 8 runs × (623 × 256 + 26 × 256) | 1 329 152 |
| **ES, total** | | **2 131 712** |

The ES's formal length, 623 generations (0-622), is the largest whole number that keeps its total
at or below the GA's: 256 episodes below, one generation of one run. The hold-out and the controls
are common to every method and counted separately. `allowance()` in the runner computes this table
from `REGISTERED`, and a test pins it.

## 5. Runs, seeds, worlds and checkpoints

- **8 runs per method,** run numbers 0-7, run seed 1 120 000 + r, **shared by the three methods**
  (paired starts and world schedules; §3). The GA's breeding stream and the ES's noise stream are
  their own functions of the seed.
- **Each method's 8 runs are one batch** in 04a's measured composition (256 strains, 8 worlds, 1 wey;
  the pilot's batches 288 and 192 strains). Floating-point results are exact only within one
  composition (D082, D091); no exact replay is claimed. A non-finite score stops one method's batch
  only.
- **World ids,** all new, in a block no earlier experiment used (02: 0 + span and 900 million; 02's
  checkpoints and probes: 950 and 980 million; 03's timing: 990 million; 03: 993-994 million; E1
  and 04a: 996-999 million; a test checks the disjointness, and a search of the repository found no
  id in the 995 million block):

| Use | Ids |
|---|---|
| pilot training | 995 000 000 + [0, 200 000) |
| pilot validation | 995 200 000 - 995 200 255 (256) |
| formal training (and the extension) | 995 300 000 + [0, 500 000) |
| formal validation | 995 800 000 - 995 800 255 (256) |
| hold-out | 995 900 000 - 995 901 023 (1 024) |

- **Seeds,** disjoint from each other and from 04a's (1 104 000-1 109 999): formal 1 120 000-1 120 007,
  pilot 1 121 000-1 121 002, projection 1 129 100-1 129 108 (moved from 1 129 000, §11), smoke
  1 128 000+, smoke pilot 1 128 500+, smoke projection 1 128 900+.
- **Checkpoints** at generation 0, every 25th and the last, on the 256 validation worlds, raw count,
  in the composition (runs, 256, 1). **A run's champion is its first checkpoint with the highest
  validation mean.** Validation worlds select champions and never drive selection or updates.
- **Records:** each stage writes a JSON record (per generation: the best, mean and zero share of the
  training scores, the best genome's hash, the batch's seconds; per checkpoint: the validation
  counts, the candidate's hash, and for random sampling and the ES's start the training score).
  **Genome files and the ES's saved state stay local** (`runs/e2/`): they derive from the
  connectome's weights, which this project does not redistribute (D028). Every hash is in the
  records, and the state file's hash is in the ES's training record.

## 6. The descriptive extension

After the formal ES record is committed (its champions locked at generations 0-622), each formal ES
run resumes from its saved state at generation 622 (the mean, Adam's moments and counter, the noise
stream, the start genome) and runs **generations 623-999** on the continuing training schedule, with
checkpoints at 625, 650, …, 975 and 999. The extension refuses to start if the state file's hash
differs from the formal record's (a plain sha256 of the file). **Its champion per run is the first
best checkpoint over generations 0-999** (formal checkpoints first, so a tie goes to the formal
one). That choice is over 42 checkpoints (the formal 26, generation 622 included, and the
extension's 16) against the GA's 41: one more chance at a lucky validation score, disclosed. It is
evaluated in the same hold-out pass, **never enters the decision**, and shows whether a "keep the
GA" result reflects the tuning charge. Its episodes are a separate ledger line (8 × (377 × 256 + 16
× 256) = 804 864).

**If the extension does not complete** (it stops, and its rerun stops too), its champions are chosen
over the formal checkpoints and the extension checkpoints that completed, labelled incomplete, and
evaluated the same way. An incomplete extension does not change E2's outcome.

## 7. The evaluation (the hold-out, used once)

- **1 024 fresh worlds** (§5), used once, after every training record and the extension record are
  committed. Every champion's hash is checked against its committed record, and the local genome
  files' brain configuration against the task's, **before any hold-out world is used.**
- **Arms:** each method's 8 champions, **one strain on all 1 024 worlds** (composition (1, 1 024, 1),
  padded), under three probes: **real, mirrored and constant** (04a's probes); the extension's 8
  champions, real only; **E1's scripted controls** at their frozen parameters: constant, random-walk,
  wall-follower, K, S-const, S-const k≤32, M-avg and the oracle. 80 neural arms and 8 scripted ones.
- **The primary measure:** each method's mean hold-out count over its champions (real probe).
- **Champions from a batch that did not complete** (its checkpoints so far) are evaluated and
  reported the same way, labelled incomplete; the decision rule says what they can decide (§8).
- **Durability:** a partial record is written atomically after every arm, so even a kill keeps the
  completed arms.

## 8. The decision, and the outcome wording (fixed now)

In exact arithmetic on the per-world counts (the runner's `decide`). Every comparison is under
unshaped fitness only, and the outcome sentences say so. "Incomplete" means final and not completed
(§10); a first stop awaiting its obligatory rerun is not an outcome.
1. **If the GA's batch is incomplete:** **"E2: no decision (02's GA did not complete)"**; the floor
   check is not made.
2. **If the ES's batch is incomplete:** **"E2: keep 02's GA (unshaped fitness; the ES's batch did not
   complete, so no comparison was made)"**, whatever its champions scored (Fable, Astra, review v1).
3. Otherwise **the ES replaces the GA** only if **both**: its mean is at least the GA's mean + **0.5
   targets per episode**, **and** at least **6 of its 8** champions are strictly above the GA's median
   champion.
   - Yes: **"E2: the ES replaces 02's GA as E3's provisional default (unshaped fitness)"**.
   - No: **"E2: keep 02's GA (unshaped fitness; the ES did not satisfy both replacement criteria after
     paying for its tuning)"**. This does not say the ES is no better at equal length (the extension
     speaks to that, descriptively).
4. **The floor, reported beside the outcome:**
   - random sampling's mean ≥ the GA's mean − 0.5 (which includes random sampling beating the GA):
     **"diagnose first: random sampling's mean is at least the GA's minus 0.5; saturation, noise and
     budget are diagnosed before building on the task, whatever the ES did"**. This takes precedence
     over proceeding to E3;
   - otherwise: **"the GA clears the random-sampling floor (random sampling's mean is more than 0.5
     below it)"**;
   - random sampling's batch incomplete: **"the floor check is not made (a batch did not
     complete)"**, and the ES-GA outcome is reported as **provisional**.
5. **When E2 cannot reach a decision:**
   - the projection completes over its limit: **"E2: not started (the projection exceeds its
     limit)"** (recorded in `projection.json`);
   - the cap is reached at any stage: **"E2: not completed (the registered cap was reached)"**;
   - the projection, a pilot stage or the evaluation is final and not completed (stopped, and its
     rerun stopped or was killed): **"E2: not completed (the run stopped)"**.
   - An incomplete extension changes none of these (§6).

**What the decision can carry:** with 8 runs, if the ES's between-run spread matched the GA's in 04a
(SD 0.17-0.30), a false switch would be very unlikely and a true gain of 0.75 targets would usually be
found (Fable's estimate, review v1). The ES's spread is untested, so this is conditional. It is a
coarse switch-or-keep rule, not evidence of a population-level advantage, and **the winner's hold-out
score is subject to selection optimism**; E3 evaluates on new worlds.

## 9. Reported, not gating

- per method: the champions' means, SD, fraction of the oracle, and each champion's mirrored and
  constant-probe means (the probes let cue dependence be assessed; a higher count alone is not
  evidence of better cue use);
- the training and validation curves; the ES's start scores, first non-flat generations, flat
  generations and clipping; the pilot's table;
- the extension's champions and their hold-out means;
- **the pairing:** each run's ES-minus-GA hold-out difference, and a check that the GA's and random
  sampling's generation-0 candidates and the ES's start genome are the same genome (by hash);
- the controls' means (for scale);
- **the ledger:** per stage, episodes (from the records), and ticks, neural updates (padding
  included) and wall time (from the accounting), with the allowance of §4 beside it.

## 10. Execution, budget and guards

**Stages,** each once, in order, each record committed and pushed before the next:
0. `e2.py project` → `projection.json`;
1. `e2.py pilot --stage 1` → `pilot-1.json` (needs the projection, completed and within its limit);
2. `e2.py pilot --stage 2` → `pilot-2.json`, with the selected setting (needs pilot stage 1 completed);
3. `e2.py train --method ga` → `train-ga.json` (needs pilot stage 2 completed);
4. `e2.py train --method random` → `train-random.json` (needs the GA's stage final);
5. `e2.py train --method es` → `train-es.json` (needs random sampling's stage final and pilot stage 2);
6. `e2.py extend` → `extension.json` (needs the ES's stage completed and its state file unchanged);
7. `e2.py evaluate` → `evaluation.json` (needs the three training stages final, and the extension
   final if the ES completed; the hash checks of §7).

**"Final"** means completed, or not completed after the registered rerun: the rerun is "used" once
it has been applied (its note, `<record>-rerun.json`, is written), and it then either writes a
stopped record, or is killed. **A killed rerun** leaves a marker and no record; the next stage
refuses and names it, and one more `--rerun` charges its compute, writes its record (final, not
completed, built from the marker and the last partial record), and refuses to run it again. So
every combination (crash or kill, then crash or kill) ends final (Fable, Astra, review v1). A
training stage or the extension that is final and not completed does not block the later stages;
the decision rule says what it means (§8). The projection and both pilot stages must complete;
otherwise E2 ends with §8.5's wording.

**Execution:** CUDA only, on one RTX 5080, Python 3.13 with the pinned torch and numpy; a clean tree
(code, configuration, requirements, this file and E1's two records) and a pushed HEAD. The
environment and the connectome's hashes are recorded at every stage and must match the earlier
stages'.

**The budget,** from 04a's rates: 4.75 s per training generation at (256, 8, 1), measured in 04a's
training (medians 4.741 and 4.716 s); and a **conservative planning figure of 10 s** per (8, 256, 1)
checkpoint, 04a's own planning figure, **not a measurement**: 04a measured about 3.3 s (its
projection 3.29 s; Fable, Astra, review v1). The pilot's compositions are scaled by strain count.

| Part | Calculation | Estimate |
|---|---|---|
| GA | 1 000 × 4.75 s + 41 × 10 s | 5 160 s |
| random sampling | the same | 5 160 s |
| ES, formal | 623 × 4.75 s + 26 × 10 s | 3 220 s |
| ES pilot, stage 1 (288 strains) | 200 × 5.35 s + 9 × 11 s | 1 170 s |
| ES pilot, stage 2 (192 strains) | 200 × 3.8 s + 9 × 8 s | 830 s |
| extension | 377 × 4.75 s + 16 × 10 s | 1 950 s |
| hold-out | 80 neural arms × 3 s + 8 scripted × 2.2 s | about 260 s |
| projection | 5 shapes × 6 generations | about 170 s |
| **total** | | **about 17 900 s, 5.0 GPU-hours** |

This is an upper estimate: at 04a's measured checkpoint cost (about 3.3 s), the 142 checkpoints cost
about 950 s less, **about 4.7 GPU-hours**. 04a's projection ran slower than its training (5.25 s per
generation against 4.75 s); at that rate E2's training would project at about 5.1 hours, inside the
5.5-hour limit, and a projection at the limit would leave about 1.4 hours of the cap, less than one
GA rerun (Fable).

- **The cap is 7 GPU-hours** for every stage together, counted by the accounting across all
  attempts, the projection included. It is checked before every rollout and after each stage.
- **The projection is a gate** (`e2.py project`, once, guarded, on the binding commit): every
  training shape (the GA, random sampling and the ES at 8 runs, and the pilot's 9 and 6 runs) for 6
  generations at full size, on smoke ids 0-9 999 and the projection's own seeds, with checkpoints at
  generations 0 and 5, their genome files written as in training. Each training stage is projected
  as its generations × its shape's median time of generations 1-4, plus its checkpoints × that
  shape's last-generation excess (one checkpoint); `training_plan()` derives both counts from
  `REGISTERED`. **If the projected training exceeds 5.5 hours, the pilot refuses to start**, and E2
  does not start without a dated amendment reviewed by both reviewers (the generations are tied to
  the allowance, so they are not reduced mechanically).
- **Guards,** as in 04a and tested the same way: exclusive start markers, written before a stage
  touches its worlds; a preflight (the connectome, the interface, one device operation); a stage that
  would start with the cap spent does not start; a stage that stops writes its record as **not
  completed**, keeping every completed checkpoint (records and local genomes, written atomically) or
  every completed hold-out arm (a partial record after every checkpoint and every arm, so a kill,
  which skips every handler, keeps them too). Atomic writes retry briefly when Windows refuses a
  replace for a moment (another process holding the file), which the test suite hit.
- **The rerun rule (04a's, D107):** a stage stopped by a crash, an interrupt, or a kill that left a
  start marker and no record, **is rerun once**, from scratch with the same seeds (`--rerun --reason
  "..."`), obligatorily; a killed attempt's compute is charged first (from its start marker to its
  last file write, plus 900 s), and the cap check follows. The stopped attempt's files are kept
  beside, renamed `-attempt1`, and disclosed. A stage stopped by the cap is not rerun; a second stop
  or a killed rerun is final (above). A crash caused by the guarded code itself cannot be fixed inside this registration:
  fixing it changes the binding commit, so it needs a dated amendment and a new projection.
- **Amendments** go in `AMENDMENTS.md`, which is not guarded. This file is guarded: editing it after
  binding would stop the next stage.

## 11. Development exposure

- **Nothing has used E2's id ranges, or its formal or pilot seeds.** Development used smoke ids
  0-9 999 (inside 02's old training span, outside every range above): the loop and command tests
  (fake simulators), and one CPU smoke run of the whole chain on 2026-09-29 (`runs/e2-smoke/`, local,
  40 ticks, 4 genomes, 2 worlds). Every neural score in it was 0, as expected at that size; the
  scripted controls were not (the oracle and S-const 0.81 targets per episode on 16 worlds).
  - **Correction (review v1, Astra):** v1 said "every score 0", which was wrong for the controls;
    and v1 said smoke seeds only, but **that smoke run's projection used E2's projection seeds,
    1 129 000-1 129 002**, because the smoke setting changed the projection's length and not its
    seeds. A projection only times generations on smoke ids, so nothing about E2's results was
    exposed; still, the formal projection seeds are moved to 1 129 100+, and smoke projections now
    use their own seeds, 1 128 900+ (tested).
- **The pilot's settings, σ grid and learning-rate grid were fixed in the design before any ES ran
  on Task N.** No ES has been run on Task N at full size.
- **What is known from 04a:** its GA's curves, champions and hold-out results on 04a's worlds, and
  its zero share (78-97% of random genomes score zero everywhere). E2's GA arm repeats 04a's
  unshaped arm on new worlds and seeds, with 8 runs instead of 4.

## 12. What E2 does not establish

- which optimizer is best for E3's stages (module fine-tuning, a selector), or for other tasks;
- whether the ES would win with shaped fitness, more directions, fewer worlds, a σ schedule, or a
  larger tuning budget;
- anything about topology (Track B);
- a population-level advantage: 8 runs per method support a coarse switch-or-keep decision;
- a comparison of search distributions alone: E2 compares **procedures**, including how each
  nominates its candidate (the GA and random sampling a best-of-32 genome by training score, the ES
  its mean, never scored in training). Some of any difference may come from that choice (Fable).

**ENOMAD** (Churchland and Garcia-Ojalvo, *iScience* 2025, PMC12803941), the closest prior work,
differs from E2 in ways that stop its result transferring directly. Each point is from the journal
version:
- a discrete-time leaky integrate-and-fire network (STAR Methods, "Neuronal dynamics"), 3 682 trained
  weights ("Population initialization"), initialised from contact counts (STAR Methods,
  "Connectome"); the GABAergic negation is in the authors' loader, not the paper's text;
- shaped rewards: partial reward by distance in foraging (STAR Methods, "Fitness evaluation"), and a
  dense gradient-ascent reward in chemotaxis (Results, "ENOMAD optimizes the C. elegans connectome
  for classical chemotaxis");
- ENOMAD: 64 worms, the top half as parents, fitness-weighted crossover ("Population
  initialization", "Crossover"), NOMAD on blocks of 49 weights ("Local dimensionality refinement"),
  a penalty −λ|W ≠ W₀|^1.3 ("Cardinality regularization"); variants rENOMAD and mENOMAD (Results,
  "ENOMAD combines nonlinear optimization with evolutionary search");
- baselines: a pure GA of 64 that mutates 5 weights per offspring (Table 2), unlike 02's GA, which
  mutates every parameter; OpenAI-ES with population 512, σ from 0.07 decaying to a floor of 0.01,
  Adam at 0.02 (Table 1); a crossover-free NOMAD (STAR Methods, "Baseline strategies");
- **equal wall-clock time, 20 minutes, not equal evaluations**: 14 to 1 300 generations by method
  (Figure 4 caption), 30 runs each; both ENOMAD variants beat the others (Results, "ENOMAD compares
  favorably with other optimization methods").

## 13. Differences from the design (v2.2)

- **Paired starts, made explicit:** the design said all methods draw from 02's distribution; here
  run r of every method starts from the same generation-0 population and sees the same world
  schedule (same run seed). This removes start-to-start variation from the comparison; it is
  tested.
- **The pilot's pairing, made concrete:** replicate k of every setting shares seed 1 121 000 + k.
- **The ES's σ grid values are in z units** (the GA's mutation scales), as the design's encoding
  implies.
- **"Final" defined** for a training stage that stops twice, so an incomplete GA or random-sampling
  batch reaches the decision rule's "no decision" or "not made" branches instead of stopping E2.
- **The projection gate has no mechanical reduction:** 04a reduced generations by amendment if over
  its limit; here the generations are tied to the allowance, so an over-limit projection needs a
  reviewed amendment.
- **The budget** is recomputed from 04a's rates: about 5.0 GPU-hours with the extension (an upper
  estimate; about 4.7 at 04a's measured checkpoint cost), under a cap of 7.
- **The pilot's ties** go to the middle setting first, not to the smaller value (v2, §4).
- **An incomplete ES** has its own outcome (v2, §8).

## 14. Changes from v1 (review v1, D120)

Both reviewers said "revise"; neither asked for a redesign, and both accepted §13's departures.
- **"Final" survives kills** (both): a rerun counts as used once applied; a killed rerun is charged,
  recorded as final and not completed by one more `--rerun`; the four crash/kill combinations are
  tested (§10).
- **A stopped extension keeps its champions** (Astra): chosen over the formal checkpoints and the
  extension checkpoints that completed, in the partial record and the stopped record alike; tested
  before and after the first extension checkpoint (§6).
- **The hold-out's arms survive a kill** (Astra): a partial record after every arm (§7).
- **The outcomes are complete** (both): an incomplete ES's own wording; "not started" after an
  over-limit projection; the evaluation and pilot stopping; "unshaped fitness" in every decision
  sentence; a first stop awaiting its rerun is not an outcome (§8).
- **The exposure account is corrected** (Astra): the smoke projection's seeds and the controls'
  scores; the projection seeds moved (§11).
- **The budget's checkpoint figure is labelled** a planning figure, with the measured one beside it
  (both, §10).
- **The ES's registered constants** are pinned to the code by a test (Fable).
- Suggestions taken: the pilot's tie order and "uninformative" flag (Fable); the flat count current
  at every checkpoint (Astra); a plain sha256 for the binary state file (Fable); the extension's 42
  checkpoints disclosed (Fable); incomplete batches' champions evaluated and labelled (Fable); the
  procedure-level caveat (Fable); the pairing check and per-run differences reported (Fable); 03's
  timing ids added to the disjointness test (Fable); a README for the folder (Fable).
- **Found while fixing:** Windows refused an atomic replace in the test suite when the per-arm
  partial record was written in quick succession. Atomic writes and the genome and state files'
  replaces now retry briefly (tested). In the formal run arms take seconds, but a transient refusal
  there would otherwise stop a stage.
