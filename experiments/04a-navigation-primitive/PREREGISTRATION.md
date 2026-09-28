# 04a: an evolved N2 navigation primitive. Pre-registration (draft v1)

**Status:**
- Draft, written 2026-09-28, for review by Astra 6 and Fable 5.1. Nothing below has run on any of
  04a's worlds.
- **The order:** review until both agree; bind (a commit); push; a guarded smoke run on the binding
  commit; then the formal stages, each on a clean tree whose HEAD is pushed.
- **The binding commit** is the commit the first training stage records. Every later stage refuses
  to run if the code, the configuration, `requirements.txt` or this file differ from it.

**Design:** [`docs/E1/DESIGN.md`](../../docs/E1/DESIGN.md) v2.1, "04a" (agreed, D077-D078), and the
list both reviewers gave after E1's results (D101). E1's results:
[`../E1-navigation/RESULTS.md`](../E1-navigation/RESULTS.md).

**Code:**
- the runner is [`scripts/e04a.py`](../../scripts/e04a.py). Its `REGISTERED` constant holds every
  number below, and it applies every rule mechanically;
- the lockstep batch of runs is `wormwars/e04a/evolve.py`. The rollout accepts one row of world ids
  per strain, so each run's genomes play that run's worlds, and it returns each episode's progress
  and final head position beside the count;
- the shared guards are `wormwars/registration.py`, the ones E1's reviews produced (D095-D099);
- Task N and E1's controls are used unchanged, from `scripts/e1.py` and `wormwars/e1/`.
- **How it is tested:**
  - the batch of runs, with a fake simulator (`tests/test_e04a_evolve.py`): per-run seeding (a run
    evolves identically alone and in a batch), each strain on its own run's worlds, the fitness
    formula and its bound, checkpoint timing, the champion rule, the raw count at validation, the cap
    check before every rollout, and a non-finite score stopping the batch;
  - the stages, through their commands with fake rollouts, smoke sizes and a scratch folder
    (`tests/test_e04a_commands.py`): the order of stages, the once-only refusals, the champion-hash
    check before any hold-out world is touched, not-completed records on a cap hit or a crash, the
    task-configuration check against E1's gate, the id ranges, and the rules, the outcome wording,
    the gain curve and the decoy measure as functions;
  - the shared guards as functions (`tests/test_registration.py`), and the rollout's per-strain ids
    and progress (`tests/test_e1_task.py`);
  - **not exercised by any test:** the live push check and the GPU preflight. They run in the
    guarded projection and smoke run on the binding commit.

## 1. The question

Can evolution, starting from random weights on the N2 connectome, produce a brain that reaches
**moved targets** on **unseen layouts**, better than **simple movement baselines**, **because of the
cue**, and better than **where it started**?

- E1 showed the task can be done with this body and these sensors: a scripted stereo navigator
  reached 8.68 targets per episode, 98.7% of an oracle.
- **The run is the unit of analysis.** Worlds quantify uncertainty for one champion; arrivals are
  not independent replicates.
- The primary question is whether evolution finds navigation **reliably** under this budget: a
  declared share of independent runs must pass (§6).

## 2. What is fixed from E1

**Task N, exactly as E1's gate ran it:**
- σ = 6, amplitude 1.0 at sensing scale 0.35, radius 1.5, separation 8, no maximum separation,
  wall clearance 3, horizon 300 ticks; one wey, energy off;
- built by E1's own config function, `scripts/e1.py::config(6.0)`. **The runner checks that the
  resolved configuration's sha256 equals that of `experiments/E1-navigation/gate.json`'s
  `resolved_config`,** and refuses to run otherwise;
- **the world seed** (the `run_seed` argument that, with the world id, generates each world and its
  target sequence) is E1's, **1 100 001**, for every world 04a plays.

**The brain:**
- N2, the Cook 2019 hermaphrodite connectome (`BrainSpec.from_connectome`), with the chemical
  direction corrected (D050);
- the brain configuration inside that task configuration: 32 substeps, single-strain padding on,
  the input gain, the clamp, the parameter bounds and the motor gains all as resolved and hashed
  above;
- the input mapping is the one E1 used, and the one E3 will rely on: the goal cue, left and right,
  at the existing food neurons (AWA, AWC, ASE), through `configs/interface.yaml`;
- **no calibration step.** Generation 0 is drawn from `Genome.random`, 02's initial distribution.

**The controls,** at the parameters E1's pilot froze (`experiments/E1-navigation/freeze.json`),
re-run on 04a's hold-out worlds (§5). No gate-world number is reused.

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
- moving away counts as 0, not as negative;
- it is computed once per episode, from the final position only, so relocations and repeated
  approaches cannot accumulate a bonus. **The bonus is at most c = 0.5 per episode, below one
  arrival;**
- **training only.** Every validation, hold-out and gate score is the raw count.

Why shaping: E1's pilot met the design's condition for it. 74% of 256 random N2 genomes scored
zero on every one of 64 pilot worlds, with a mean count of 0.031. That does not show unshaped
evolution cannot work, which is why the unshaped arm runs (Astra, Fable, D101).

**Random streams, all per run** (D101: seeded by run, not by batch position):
- generation 0: `Genome.random` with a CPU generator seeded 2 × run seed, then moved to the GPU;
- selection and mutation: a generator on the device seeded 2 × run seed + 1;
- the training worlds of generation g: 8 ids drawn by `numpy.random.default_rng([run seed, g,
  0xC0FFEE])` from **997 000 000 to 997 999 999**. Runs draw independently, so two runs can meet the
  same world by chance; each run's schedule depends on its seed only.

**Batching (the only thing batching changes is the simulator call):**
- runs 0-7 are batch A, and runs 8-15 batch B (the last four of which are unshaped);
- in each generation, a batch's 8 × 32 genomes play in one rollout, each on its own run's worlds;
- a test checks that a run evolves identically alone and in a batch, with a fake simulator.

**Checkpoints and the champion:**
- **the validation worlds:** 64 ids, **998 000 000 to 998 000 063**, shared by every run and never
  used for selection;
- at generation 0, every 25 generations and at generation 999 (41 checkpoints), each run's best
  genome of that generation, by its own fitness, is scored on the validation worlds, raw count;
- **the champion** of a run is the first checkpoint with the highest validation mean. It is fixed,
  and committed with its hash, before any hold-out world is used;
- **the generation-0 baseline** of a run is its generation-0 checkpoint: the best of its 32 random
  genomes on its generation-0 training worlds, by its own fitness.

**Recorded per run:** every generation's best and mean fitness, the best, largest and mean count,
the share of genomes scoring zero, and the best genome's hash; every checkpoint's validation mean,
per-world counts and genome; generation 0's per-genome, per-world counts and progress (Fable,
D101); the final population.

## 4. Compositions (D082, D091, D092)

Exactness holds only within one batch composition, (strains per chunk, worlds per strain, weys per
world), and no exact replay is claimed on CUDA default mode.

| Stage | Composition | Notes |
|---|---|---|
| training | (256, 8, 1) | batch A and batch B alike; E1 measured this shape |
| validation (checkpoints) | (8, 64, 1) | the batch's 8 candidates together |
| hold-out, each neural arm | (1, 1 024, 1), padded | as E1's gate arms |
| hold-out, each scripted arm | 1 strain, 1 024 worlds | scripted controls have no neural batch |

## 5. The evaluation (the hold-out, used once)

**The hold-out worlds:** 1 024 ids from 04a's reserved range, **996 301 000 to 996 302 023**
(`HOLDOUT_04A_IDS`, offset 1 000 as in E1). No development run has touched this range.

**Arms,** each one strain on all 1 024 worlds in one rollout:
- **per run (16 runs):** the champion; the champion with the scent read at the mirrored decoy
  (`food_probe = "mirrored"`); the champion under the constant probe (its own blind level,
  non-gating); the generation-0 baseline;
- **the gating baselines,** at E1's frozen parameters: constant motion, the persistent random walk,
  the wall-follower, and level kinesis (K);
- **references (non-gating):** E1's navigator (S-const), S-const with k ≤ 32, M-avg and the oracle;
- **the gain curve (non-gating):** for each k in E1's S-const grid (1, 2, 4, 8, 16, 32, 64, 256,
  1 024, 8 192), the first maximum over speed and turn among E1's tuned S-const means at that k,
  re-run here.

**Before the first arm,** the evaluation stage checks that every champion and baseline genome file
matches the hash committed with the training records.

## 6. The rules

**A run passes** if its champion meets all four, on the hold-out:
1. **reliability:** at least **80%** of the 1 024 episodes reach at least **2** targets;
2. **beats each gating baseline:** for each of constant, random walk, wall-follower and K, the
   one-sided 95% lower bound of the paired mean difference (champion − baseline) is **above 0.5**;
3. **uses the cue:** the one-sided 95% lower bound of the mean of (0.5 × real − mirrored), per
   world, is **at least 0**;
4. **beats generation 0:** the one-sided 95% lower bound of the paired mean difference (champion −
   its run's generation-0 baseline) is **above 0.5**.

Lower bounds are the 5th percentile of a paired percentile bootstrap over worlds, 10 000 resamples,
seed 0, exactly as E1's.

**The outcome, in fixed wording, from the shaped arm's 12 runs:**
- **"04a: passed"** if at least **6 of 12** shaped runs pass. Half is the declared share: the claim
  is that evolution finds navigation under this budget at least as often as not, not that one run
  got lucky;
- **"04a: some runs passed (k of 12)"** if 1 to 5 pass;
- **"04a: not passed"** if none pass;
- **"04a: not completed"** if a stage stops before its result (the cap, a crash or an interrupt).

**The unshaped arm** gets the same per-run rules and its count of passing runs, but no verdict. With
4 runs, a shaped-versus-unshaped comparison is descriptive only.

**For E3:** any passing champion is a valid module. The one carried forward is the passing shaped
champion with the highest hold-out mean; that is a choice among passing modules, not part of the
test.

## 7. Reported, not gating

- **Effective steering gain (D101):** each champion's hold-out mean placed on the hold-out gain
  curve. The performance-equivalent k is interpolated linearly in log k between the two grid points
  whose means bracket the champion's, at the first crossing; below k = 1's mean it is reported as
  "< 1", and above k = 8 192's as "> 8 192". **It is a performance equivalence, not a measured
  steering gain,** and no threshold is set on it. Both scripted references, S-const (unrestricted)
  and S-const with k ≤ 32, are reported beside it.
- **E1's secondary measures** per champion: first-arrival success, latency as the mean of
  min(first arrival, horizon), the median time of finished legs, and path efficiency.
- the fraction of the oracle's mean; the constant-probe level; training and validation curves; the
  generation-0 zero share per run;
- **the mirrored-decoy capture:** for the mirrored arm, the head's distance at the end of each
  unfinished leg to the decoy point (23 − x, 23 − y), against its distance to the true target
  (Fable, D101);
- **module save and a replay check:** each champion is saved with its world settings, interface
  and evidence (`save_genome`). The replay check reloads the champion's checkpoint batch from disk
  and replays it in the same composition on the validation worlds; the per-world counts are
  compared with the recorded ones. Agreement is reported, not claimed exact.

## 8. Execution, budget and guards

**Stages,** each once, in order:
0. `e04a.py project`: the budget projection above, on smoke ids; it writes `projection.json`.
1. `e04a.py train --batch A`: writes `train-A.json` (records), `train-A-candidates.npz` and
   `train-A-final.npz` (genomes). Committed and pushed before the next stage.
2. `e04a.py train --batch B`: the same, for batch B. It refuses to run unless the code and
   environment equal batch A's.
3. `e04a.py evaluate`: needs both training records committed, unchanged and pushed; the same code
   and environment; writes `evaluation.json` and `evaluation_events.npz`.

**Execution:** CUDA only, on one RTX 5080, Python 3.13 with the torch and numpy pinned in
`requirements.txt`; a clean tree (code, configuration, requirements and this file) and a pushed
HEAD. The environment and the connectome's hashes are recorded at batch A and must match later.

**The budget.** E1 measured 4.676 s per rollout in 04a's training shape (`freeze.json`,
`throughput_04a_shape`, 256 strains × 8 worlds × 1 wey). A development projection on smoke ids
(§9), with selection, mutation and checkpoints included, measured **4.749 s per generation**; one
neural arm on 1 024 worlds took about 3 s, and one scripted arm about 2.2 s.

| Part | Calculation | Estimate |
|---|---|---|
| training | 2 batches × 1 000 generations × 4.749 s | 9 498 s |
| checkpoints | 2 × 41 rollouts of 8 × 64 worlds, about 2 s each | 164 s |
| hold-out, neural arms | 64 arms × 3 s | 192 s |
| hold-out, scripted arms and replays | 18 × 2.2 s, plus 16 replays | about 60 s |
| **total** | | **about 9 900 s, 2.75 GPU-hours** |

- **The cap is 6 GPU-hours,** about 2.2 × the estimate, for every stage together, counted by the
  accounting across all attempts. It is checked before every rollout and after each stage's
  analysis.
- **The projection before the formal stages** (`e04a.py project`, guarded, on the binding commit):
  6 generations of batch A's shape at full size on smoke ids, timed. If 2 000 × the median time of
  the generations after the first exceeds **4.5 hours**, the formal stages do not start, and the
  generations are reduced by a dated amendment before any formal data exist.

**Guards,** as in E1 and tested the same way:
- exclusive start markers, one per stage, written before the stage touches its worlds;
- a preflight (the connectome, the interface and one device operation) before each marker;
- the cap: a stage that would start with the cap spent does not start;
- a stage that stops (the cap, a crash or an interrupt) writes its result as **not completed**.
  Training keeps every completed checkpoint (records and genomes, written atomically after each);
  the evaluation keeps every completed arm;
- **no resume.** A stopped stage is not rerun without a dated amendment, which is disclosed;
- JSON written with LF endings; files hashed normalised to LF;
- a smoke mode with tiny sizes, ids 0-9 999 (outside every E1 and 04a range) and a scratch folder,
  `runs/e04a-smoke/`.

## 9. Development exposure

- None of 04a's training, validation or hold-out ranges has been used by any run. The tests use a
  fake simulator or ids outside these ranges.
- **Development runs, all on smoke ids 0-9 999:** a CPU smoke run of all three stages at tiny sizes;
  a development projection on the GPU (6 generations of batch A's shape, training ids 0-4 999,
  validation ids 5 000-5 063), which gave 4.749 s per generation; and a timing of one random N2
  genome and one scripted arm on ids 0-1 023. None of these is a result.
- E1's pilot measured generation 0 and the throughput on E1's pilot worlds and smoke ids, not on
  04a's.
- **The design saw E1's results,** including the gain curve and the generation-0 zero share, before
  this registration. Those shaped the choices of shaping, budget and references.

## 10. What 04a does not establish

- anything about trails, junctions, occluding walls or colonies (E3 begins with its own checks);
- that N2's wiring helps: there is no null-graph comparison here (Bridge 1 is deferred);
- that unshaped evolution cannot work, whatever the unshaped arm shows with 4 runs;
- a mechanism: the effective gain is a performance equivalence.
