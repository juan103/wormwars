# 04a: an evolved N2 navigation primitive. Pre-registration (draft v2)

**Status:**
- Written 2026-09-28 for review by Astra 6 and Fable 5.1. Nothing below has run on 04a's
  validation or hold-out worlds, or on its (moved) training range (§9).
  - v1 (`b38c7cc`, `docs/reviews/20260928-213057-04a-prereg/`): both said "revise" (D104). Every
    must-fix is adopted in v2, and most suggestions; §11 lists them.
- **The order:** review until both agree; bind (a commit); push; the guarded projection and a
  guarded smoke run on the binding commit; then the formal stages, each on a clean tree whose HEAD
  is pushed, with each stage's record committed and pushed before the next stage starts.
- **The binding commit** is the commit the projection records. Every later stage refuses to run if
  the code, the configuration, `requirements.txt`, this file, or E1's freeze and gate records differ
  from it.

**Design:** [`docs/E1/DESIGN.md`](../../docs/E1/DESIGN.md) v2.1, "04a" (agreed, D077-D078), and the
list both reviewers gave after E1's results (D101). E1's results:
[`../E1-navigation/RESULTS.md`](../E1-navigation/RESULTS.md).

**Code:**
- the runner is [`scripts/e04a.py`](../../scripts/e04a.py). Its `REGISTERED` constant holds every
  number below, and it applies every rule mechanically, the projection limit included;
- the lockstep batch of runs is `wormwars/e04a/evolve.py`. The rollout accepts one row of world ids
  per strain, so each run's genomes play that run's worlds, and it returns each episode's progress
  and final head position beside the count;
- the shared guards are `wormwars/registration.py`, the ones E1's reviews produced (D095-D099);
- Task N and E1's controls are used unchanged, from `scripts/e1.py` and `wormwars/e1/`.

**How it is tested:**
- **the engine change** (AGENTS.md rule 7): `scripts/e04a_equivalence.py` compared the rollout
  before 04a's changes (`5eaf339`) with the rollout after them, on smoke ids, for E1's navigator,
  the oracle and 4 random N2 genomes. The declared tolerance was exact on the CPU, and reported on
  CUDA. **Every score and event-table entry was identical, on the CPU and on CUDA**
  (`development-records/engine-equivalence-*.json`). The tolerance was written in the script before
  it ran, but it is committed together with the result, so the order is not independently
  verifiable;
- **the rollout and progress** (`tests/test_e1_task.py`): identical id rows reproduce the shared-ids
  rollout exactly; each strain gets its own worlds' targets; **with the composition fixed, changing
  a batch-mate's genome and worlds leaves a strain's counts, progress, final position and events
  unchanged** (real simulator, CPU); the progress formula at known head positions; and progress
  restarting at 0 on every arrival;
- **the batch of runs,** with a fake simulator (`tests/test_e04a_evolve.py`): a run evolves
  identically alone and in a batch; each strain plays its own run's worlds; the fitness formula and
  its bound; checkpoint timing; the champion rule; the raw count at validation; the cap check before
  every rollout; a non-finite score stopping the batch;
- **the stages,** through their commands with fake rollouts, smoke sizes and a scratch folder
  (`tests/test_e04a_commands.py`): the smoke cleanup touching only its own folder; every smoke id
  below 10 000; the projection gate (missing, over its limit, once only); the stage order and
  once-only refusals; the rerun rule (once, not after the cap, the stopped attempt kept); the
  champion-hash and regenerated-baseline checks and the E1-input check, all before any hold-out
  world is touched; not-completed records after a cap hit (before a stage, during training, after
  the analysis) or a crash (before the first checkpoint, during the evaluation); the verdict written
  before the extras; and the rules, the outcome, the share bound, the gain curve and the decoy
  measure as functions;
- **the guards as functions** (`tests/test_registration.py`, and `require_committed` in a temporary
  git repository);
- **the command tests run with the formal guards off** (`smoke=True, guarded=False`). The wiring of
  the formal guards, the live push check and the GPU preflight run only in the guarded projection
  and the guarded smoke run on the binding commit.

## 1. The question

Can evolution, starting from random weights on the N2 connectome, produce a brain that reaches
**moved targets** on **unseen layouts**, better than the **tested simple movement baselines**, that
is **misled by a mirrored cue and helped by the real one**, and better than **where it started**?

- E1 showed the task can be done with this body and these sensors: a scripted stereo navigator
  reached 8.68 targets per episode, 98.7% of an oracle.
- **The run is the unit of analysis.** Worlds quantify uncertainty for one champion; arrivals are
  not independent replicates.
- The primary question is whether this procedure, under this budget, produces passing navigators in
  a declared share of independent runs (§6).

## 2. What is fixed from E1

**Task N, exactly as E1's gate ran it:**
- σ = 6, amplitude 1.0 at sensing scale 0.35, radius 1.5, separation 8, no maximum separation,
  wall clearance 3, horizon 300 ticks; one wey, energy off;
- built by E1's own config function, `scripts/e1.py::config(6.0)`. **The runner checks that the
  resolved configuration's sha256 equals that of `experiments/E1-navigation/gate.json`'s
  `resolved_config`,** and refuses to run otherwise;
- **E1's freeze and gate records are guarded files:** part of the clean-tree and same-code checks,
  and their hashes are recorded by every stage and compared again before the evaluation;
- **the world seed** (the `run_seed` argument that, with the world id, generates each world and its
  target sequence) is E1's, **1 100 001**, for every world 04a plays.

**The brain:**
- N2, the Cook 2019 hermaphrodite connectome (`BrainSpec.from_connectome`), with the chemical
  direction corrected (D050);
- the brain configuration inside that task configuration: 32 substeps, single-strain padding on,
  the input gain, the clamp, the parameter bounds and the motor gains, all as resolved and hashed
  above;
- the input mapping is the one E1 used, and the one E3 will rely on: the goal cue, left and right,
  at the existing food neurons (AWA, AWC, ASE), through `configs/interface.yaml`;
- **no calibration step.** Generation 0 is drawn from `Genome.random`, 02's initial distribution.

**The controls,** at the parameters E1's pilot froze (`experiments/E1-navigation/freeze.json`),
re-run on 04a's hold-out worlds (§5). No gate-world number is reused.
- **A limitation carried from E1:** several tuned blind baselines won at the edge of their grids
  (the wall-follower and the random walk on every parameter), so they may be under-tuned. 04a's
  comparisons are against these frozen, tested baselines, not against the best possible simple
  movement policies.

## 3. Evolution

**The optimizer is 02's,** with one island:
- 32 genomes per run; truncation selection with 3 elites and the top 8 as parents; Gaussian
  mutation (w 0.08, g 0.04, τ 0.15 multiplicative, bias 0.05, every parameter);
- **8 training worlds per genome per generation,** the same 8 for every genome of a run in that
  generation (common random numbers);
- **1 000 generations per run.**

**Runs:** 16, each with its own run seed, **1 104 000 + run number**:
- **the shaped arm (primary):** runs 0-11, shaping c = 0.5;
- **the unshaped arm (secondary):** runs 12-15, c = 0.

**Fitness,** per genome, is the mean over its 8 worlds of

  count + c × progress,

where count is the number of targets reached in 300 ticks and progress is the fraction of the
**unfinished** leg's starting distance that the head has closed by the last tick, clipped to
[0, 1] (`World.final_progress`):
- the leg's start is where the head was when that target became current (the spawn, for the first);
  after an arrival the new leg starts where the head is, so progress restarts at 0;
- moving away counts as 0, not as negative;
- it is computed once per episode, from the final position only, so relocations and repeated
  approaches cannot accumulate a bonus;
- **the bound is per episode:** at most c = 0.5, and in fact below it, since an unfinished leg ends
  more than 1.5 cells from its target. Within an episode an arrival always gains more than it can
  lose;
- **it is not a bound per genome:** averaged over 8 worlds, a genome with no arrivals but high
  progress can outrank one with a rare arrival. That is the intended training signal, and a risk:
  selection can favour approaching or orbiting over arriving. Validation and the hold-out use the
  raw count, so such a policy cannot pass by it;
- **training only.** Every validation, hold-out and gate score is the raw count.

Why shaping: E1's pilot met the design's condition for it. 74% of 256 random N2 genomes scored
zero on every one of 64 pilot worlds, with a mean count of 0.031. That does not show unshaped
evolution cannot work, which is why the unshaped arm runs (Astra, Fable, D101).

**Random streams, all per run** (D101: seeded by run, not by batch position):
- generation 0: `Genome.random` with a CPU generator seeded 2 × run seed, then moved to the GPU;
- selection and mutation: a generator on the device seeded 2 × run seed + 1;
- the training worlds of generation g: 8 ids drawn by `numpy.random.default_rng([run seed, g,
  0xC0FFEE])` from **999 000 000 to 999 999 999**. Runs draw independently, so two runs can meet the
  same world by chance; each run's schedule depends on its seed only. (v1's range, 997 000 000
  onward, was abandoned after a smoke run touched 24 of its ids; §9.)

**Batching (the only thing batching changes is the simulator call):**
- runs 0-7 are batch A, and runs 8-15 batch B (the last four of which are unshaped);
- in each generation, a batch's 8 × 32 genomes play in one rollout, each on its own run's worlds;
- independence is tested with a fake simulator (a run alone and in a batch) and, in the real
  simulator on the CPU, at a fixed composition (a batch-mate's genome and worlds changed). **It is
  not tested between solo and batched execution on CUDA,** where the composition differs;
- **failure is coupled within a batch:** a non-finite score in one run, or a crash, stops all 8.

**Checkpoints and the champion:**
- **the validation worlds:** 256 ids, **998 000 000 to 998 000 255**, shared by every run. They
  select the champion; they never breed;
- at generation 0, every 25 generations and at generation 999 (41 checkpoints), each run's best
  genome of that generation, by its own fitness, is scored on the validation worlds, raw count;
- **the champion** of a run is the first checkpoint with the highest validation mean (ties go to the
  earliest). It is fixed, and committed with its hash, before any hold-out world is used.
  Selecting among 41 checkpoints makes the champion's validation mean optimistic; the hold-out is
  separate;
- **the generation-0 baseline** of a run is its generation-0 checkpoint: the best of its 32 random
  genomes on its generation-0 training worlds, by its own fitness. It measures improvement over the
  run's own start, not the value of mutation over an equal-budget random search.

**Recorded per run** (in `train-A.json` and `train-B.json`): every generation's best and mean
fitness, the best, largest and mean count, the share of genomes scoring zero, the best genome's
hash and the batch's wall time; every checkpoint's validation mean, per-world counts and genome
hash; generation 0's per-genome, per-world counts and progress (Fable, D101); and the final
population's hashes.

**Genome files are not published.** Generation 0 is drawn with weights proportional to the
connectome's anatomical weights, which this project does not redistribute (D028), and early
checkpoints may stay close to them. The candidates and final populations stay local
(`runs/e04a/genomes/`, `runs/e04a/runNN-final.npz`, `runs/e04a/modules/`); the records carry every
hash, and the evaluation checks the local files against them. Each generation-0 baseline is also
checked against its run's initial population, regenerated from the seed. Publishing any genome
later needs the hygiene check (`tests/test_publication_hygiene.py`) first.

## 4. Compositions (D082, D091, D092)

Exactness holds only within one batch composition, (strains per chunk, worlds per strain, weys per
world), and no exact replay is claimed on CUDA default mode.

| Stage | Composition | Notes |
|---|---|---|
| training | (256, 8, 1) | batch A and batch B alike; E1 measured this shape |
| validation (checkpoints) | (8, 256, 1) | the batch's 8 candidates together |
| hold-out, each neural arm | (1, 1 024, 1), padded | as E1's gate arms |
| hold-out, each scripted arm | 1 strain, 1 024 worlds | scripted controls have no neural batch |
| the projection | (256, 8, 1) and (8, 256, 1) | on smoke ids |

## 5. The evaluation (the hold-out, used once)

**The hold-out worlds:** 1 024 ids from 04a's reserved range, **996 301 000 to 996 302 023**
(`HOLDOUT_04A_IDS`, offset 1 000 as in E1). No run has touched this range.

**Before the first hold-out world:** both training records must be completed, committed and
unchanged; the code and environment must equal the training stages'; E1's input hashes must equal
batch A's; every champion and baseline file must match its committed hash; and every generation-0
baseline must appear in its run's regenerated initial population.

**Arms,** each one strain on all 1 024 worlds in one rollout:
- **per run (16 runs):** the champion; the champion with the scent read at the mirrored decoy
  (`food_probe = "mirrored"`); the champion under the constant probe (the scent replaced by a
  constant, so no direction information); the generation-0 baseline;
- **the gating baselines,** at E1's frozen parameters: constant motion, the persistent random walk,
  the wall-follower, and level kinesis (K);
- **references (non-gating):** E1's navigator (S-const), S-const with k ≤ 32, M-avg and the oracle;
- **the gain curve (non-gating):** for each k in E1's S-const grid (1, 2, 4, 8, 16, 32, 64, 256,
  1 024, 8 192), the first maximum over speed and turn among E1's tuned S-const means at that k,
  re-run here.

## 6. The rules

**A run passes** if its champion meets all five, on the hold-out:
1. **reliability:** at least **80%** of the 1 024 episodes reach at least **2** targets;
2. **beats each gating baseline:** for each of constant, random walk, wall-follower and K, the
   one-sided 95% lower bound of the paired mean difference (champion − baseline) is **above 0.5**;
3. **misled by the mirrored cue:** the one-sided 95% lower bound of the mean of
   (0.5 × real − mirrored), per world, is **at least 0** (E1's rule);
4. **helped by the real cue:** the one-sided 95% lower bound of the paired mean difference
   (champion − the champion under the constant probe) is **above 0.5** (Astra, Fable, review v1).
   Rule 3 alone would pass a champion that the mirror harms but the real cue does not help;
5. **beats generation 0:** the one-sided 95% lower bound of the paired mean difference (champion −
   its run's generation-0 baseline) is **above 0.5**.

Lower bounds are the 5th percentile of a paired percentile bootstrap over worlds, 10 000 resamples,
seed 0, exactly as E1's.

**The outcome, in fixed wording, from the shaped arm's 12 runs:**
- **"04a: passed"** if at least **6 of 12** shaped runs pass;
- **"04a: some runs passed (k of 12)"** if 1 to 5 pass;
- **"04a: not passed"** if none pass;
- **"04a: not completed"** if a stage stops before its result (the cap, a crash or an interrupt).

**What the outcome does and does not mean:**
- 6 of 12 is a declared operational benchmark: at least half of these registered runs passed. It
  does not establish that a new run succeeds with probability at least 0.5. The record reports the
  observed share with its **exact (Clopper-Pearson) one-sided 95% lower bound**: for 6 of 12 it is
  0.245, and a lower bound above 0.5 would need 10 of 12;
- every run is judged on the same hold-out worlds, so the passes are conditional on that sample of
  worlds, and each run's bounds are marginal, not simultaneous across the 16 runs. No claim is made
  that each passing champion is individually certified at 95% after selection among runs;
- within a run the five rules are a conjunction, so no correction is applied across them;
- "not passed" means this procedure did not meet the criterion within this budget, not that N2
  cannot be evolved to navigate.

**The unshaped arm** gets the same per-run rules and its count of passing runs, but no verdict. With
4 runs, a shaped-versus-unshaped comparison is descriptive only.

**For E3:** any passing champion is a valid module. The one carried forward is the passing shaped
champion with the highest hold-out mean. That is a selection on the hold-out, so its hold-out mean
is optimistic; E3 re-measures it on its own fresh worlds.

## 7. Reported, not gating

These are written to `evaluation-extras.json` after the verdict, except the gain curve and the
secondary measures, which are computed from the arms and written with it. An error in the extras is
recorded there and cannot change the verdict.
- **Effective steering gain (D101):** each champion's hold-out mean placed on the hold-out gain
  curve. The performance-equivalent k is interpolated linearly in log k inside the first pair of
  neighbouring grid points (in increasing k) whose means satisfy mean(lower k) ≤ champion ≤
  mean(higher k); it is "< 1" below k = 1's mean, and "> 8 192" above every point of the curve.
  **It is a performance equivalence, not a measured steering gain,** and no threshold is set on it.
  Both scripted references, S-const (unrestricted) and S-const with k ≤ 32, are reported beside it.
- **E1's secondary measures** per arm: first-arrival success, latency as the mean of
  min(first arrival, horizon), the median time of finished legs, and path efficiency.
- the fraction of the oracle's mean; training and validation curves; the generation-0 zero share
  per run;
- **the mirrored-decoy capture:** for the mirrored arm, the head's final distance to the decoy point
  (23 − x, 23 − y) of the unfinished leg's target, against its distance to the true target (Fable,
  D101);
- **a replay check:** the champion's checkpoint batch is reloaded from disk and replayed in the same
  composition on the validation worlds; the per-world counts are compared with the recorded ones.
  Agreement is reported, not claimed exact;
- **the modules:** each champion saved locally with its world settings, interface and evidence
  (`save_genome`), and its hash recorded.

## 8. Execution, budget and guards

**Stages,** each once, in order, each record committed and pushed before the next stage:
0. `e04a.py project`: the budget projection on smoke ids; writes `projection.json`.
1. `e04a.py train --batch A`: refuses to start without a completed projection within its limit, on
   the same code and environment; writes `train-A.json` (records; genomes stay local).
2. `e04a.py train --batch B`: refuses to start unless batch A completed, is committed, and ran the
   same code and environment; writes `train-B.json`.
3. `e04a.py evaluate`: the checks in §5; writes `evaluation.json` and `evaluation_events.npz` (the
   verdict), then `evaluation-extras.json`.

**Execution:** CUDA only, on one RTX 5080, Python 3.13 with the torch and numpy pinned in
`requirements.txt`; a clean tree (code, configuration, requirements, this file and E1's two
records) and a pushed HEAD. The environment and the connectome's hashes are recorded at every stage
and must match the earlier stages'.

**The budget.** Measured on this code's predecessors, on smoke ids (§9): 4.749 s per training
generation in the (256, 8, 1) composition, against E1's 4.676 s per rollout; about 3 s per neural
hold-out arm and 2.2 s per scripted arm. The development pilot (§9) measured the (8, 256, 1)
checkpoint only within its total time: 200 generations and 9 checkpoints took 1 044 s, which leaves about 10 s per checkpoint beyond 4.749 s per generation, a conservative figure.

| Part | Calculation | Estimate |
|---|---|---|
| training | 2 batches × 1 000 generations × 4.749 s | 9 498 s |
| checkpoints | 82 × about 10 s | about 820 s |
| hold-out, neural arms | 64 arms × 3 s | 192 s |
| hold-out, scripted arms and replays | 18 × 2.2 s, plus 16 replays | about 100 s |
| projection | 6 generations and 2 checkpoints | about 45 s |
| **total** | | **about 10 650 s, 2.96 GPU-hours** |

- **The cap is 6 GPU-hours** for every stage together, counted by the accounting across all
  attempts, the projection included. It is checked before every rollout and after each stage's
  analysis.
- **The projection is a gate** (`e04a.py project`, once, guarded, on the binding commit): 6
  generations of batch A's shape at full size on smoke ids, with checkpoints at generations 0 and 5.
  Training is projected as 2 000 × the median time of generations 1-4, plus 82 × the last
  generation's excess over that median (one checkpoint). **If the projection exceeds 4.5 hours,
  batch A refuses to start;** the generations are then reduced by a dated amendment, before any
  formal data exist.

**Guards,** as in E1 and tested the same way:
- exclusive start markers, one per stage, written before the stage touches its worlds;
- a preflight (the connectome, the interface and one device operation) before each marker;
- the cap: a stage that would start with the cap spent does not start;
- a stage that stops (the cap, a crash or an interrupt) writes its result as **not completed**.
  Training keeps every completed checkpoint (records and local genomes, written atomically after
  each); the evaluation keeps every completed arm;
- **the rerun rule, fixed now:** a stage stopped by a crash or an interrupt may be rerun **once**,
  from scratch with the same seeds (`--rerun`). The stopped attempt's record, marker and partial
  files are kept beside it, renamed `-attempt1`, and disclosed. A stage stopped by the cap is not
  rerun. Anything else needs a dated amendment;
- JSON written with LF endings; files hashed normalised to LF;
- a smoke mode with tiny sizes, ids 0-9 999 (outside every E1 and 04a range) for every stage, and a
  scratch folder, `runs/e04a-smoke/`. Its cleanup removes files only inside that folder.

## 9. Development exposure

**Worlds touched before binding,** all recorded in `development-records/`:
- **v1's CPU smoke run drew 24 training worlds from v1's formal training range** (Astra, review v1):
  the smoke mode did not rebind the training ids. The 24 ids are reconstructed exactly from the
  deterministic schedule and match the attempt records' world counts
  (`smoke-training-exposure.json`). They were the first two draws of the formal schedule for runs
  0, 1, 12 and 13 at generations 0-2, played by 4 random or barely mutated genomes for 40 ticks.
  **The training range is moved** to 999 000 000 onward, which no run has touched; a test checks
  that none of the 24 ids lies in it. No validation or hold-out world was touched.
- **The same run's records were then deleted by a test** whose fixture cleaned the real smoke folder
  before redirecting to a scratch folder (Astra, review v1). The attempt records and genome files
  survived, and they are what the reconstruction uses. The fixture is fixed and tested.
- **On smoke ids only (0-9 999):** v1's development projection (`dev-projection-v1.json`: 6
  generations of batch A's shape, 4.749 s per generation); a timing of one random N2 genome and one
  scripted arm on ids 0-1 023 (`dev-arm-timing.json`); the engine-equivalence check
  (`engine-equivalence-*.json`, ids 0-63 and 100-115); and a **development pilot** of 200
  generations of batch A's shape (training ids 0-4 999, validation ids 5 000-5 255;
  `pilot-evolution.json`), run after review v1 to see whether this optimizer makes progress on Task N
  at all (Fable, review v1). **What it showed:** in all 8 (shaped) runs, the best genome's validation
  mean rose from 0.05-0.34 targets at generation 0 to 1.2-2.1 by generation 25, then stayed between
  about 1.0 and 2.1 through generation 199. E1's blind baselines reached at most 0.65 on its gate
  worlds, and its navigator 8.68. The pilot does not show whether these genomes use the cue. **It
  suggests that with 02's optimizer many runs may not reach rule 1 (80% of episodes with at least
  2 targets) within 1 000 generations.** The generation count was not changed on that basis; the
  question is put to the reviewers (§11).
- **The design saw E1's results,** including the gain curve and the generation-0 zero share, before
  this registration. Those shaped the choices of shaping, budget and references.

## 10. What 04a does not establish

- anything about trails, junctions, occluding walls or colonies (E3 begins with its own checks);
- that N2's wiring helps: there is no null-graph comparison here (Bridge 1 is deferred);
- that unshaped evolution cannot work, whatever the unshaped arm shows with 4 runs;
- that mutation beats an equal-budget random search: generation 0 is a best-of-32 baseline;
- a population success rate: 6 of 12 is a benchmark on these runs and these hold-out worlds (§6);
- a mechanism: the effective gain is a performance equivalence;
- that the champions beat the best possible simple movement policies: the blind baselines may be
  under-tuned (§2).

## 11. Changes from v1 (review v1, D104)

**Must-fixes, both reviewers:**
- the projection is enforced: a completed projection within its limit, on the same code and
  environment, is required before batch A; it runs once, under the cap, with a registered number of
  generations (Astra 3, Fable 3);
- E1's freeze and gate records are guarded and hashed (Astra 4, Fable 5);
- the outcome wording: the "at least as often as not" claim is withdrawn; the exact share bound, and
  the marginal-bound and shared-worlds caveats, are added (Astra 5, Fable 6);
- the engine-equivalence check is declared and run, and identical (Astra 7, Fable 8);
- the text now matches the code: file names and places, the validation worlds "never breed" rather
  than "never used for selection", the gain curve's edges, and the projection rule (Fable 2).

**Must-fixes, Astra:**
- the smoke mode now rebinds every id range, a test checks every id passed to the simulator, the
  exposure is reconstructed and disclosed, and the training range is moved (1);
- the test fixture no longer deletes real records, and a test checks where cleanup acts (2);
- a new gating rule, 4: the real cue must beat the champion's own constant probe (6). The grid-edge
  limitation is stated (§2, §10);
- direct tests of the progress formula and its restart after an arrival (7).

**Must-fixes, Fable:**
- genome files are not published (the connectome rule); records carry hashes, and generation-0
  baselines are checked against their regenerated populations (1);
- `require_committed` is tested in a temporary git repository (4);
- the development records are committed (7).

**Suggestions adopted:**
- 256 validation worlds instead of 64 (both);
- a real-simulator independence test at a fixed composition (Fable);
- the rerun rule declared in advance (Fable);
- the verdict written before the non-gating extras, and the modules saved after it (both);
- a non-finite check at validation (Astra);
- more command tests: cap and crash paths, the generation-0 check (Astra);
- a development pilot on smoke ids (Fable);
- §10's additions: the best-of-32 baseline, the per-episode bound, the E3 selection bias, the
  tie-breaking (Fable).

**Not adopted:** none of the must-fixes. S-const was not made a gate, as both advised.

**Open for review v2:** the pilot's plateau near 2 targets (§9). Keep 1 000 generations and accept a
likely "some runs passed" or "not passed", which E2's optimizer screen would then address; or
change the budget or the optimizer settings now, before binding?
