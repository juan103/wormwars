# The evolutionary E4-D: pre-registration

**Status: draft 2, for the reviewers' confirmation. Nothing here binds yet.** Draft 1 (1bec549) was reviewed by both
(`docs/reviews/20261014-E4-D-evo-prereg/`; both "bind after these fixes", D272); §12 lists the changes. It binds at the
commit that is pushed after both reviewers agree. From then on, registered text is never changed or removed;
amendments are added beside it, dated (AGENTS.md, rule 2).

**Its sources:**
- the design, `docs/E4/E4-D-EVO-DESIGN.md` v2.1 (D265, D266), and the trial's design, `docs/E4/E4-D-DESIGN.md` v2.3;
- the owner's choices (D266): δ = 0.15; F kept only if its pilot passes; a pre-committed seeded follow-up (S);
- the exploratory pilot (D269, D270): the precheck, the factor screen and arm F;
- the power analysis, `scripts/e4d_evo_power.py` → `power.json` (§8).

Choices made after seeing the pilot are listed in §11.

## 0. The binding sequence

1. **This text binds** at its pushed commit, together with:
   - the registered rule, `wormwars/e4/evo_stats.py`, and its tests (`tests/test_e4d_evo_stats.py`);
   - the power analysis, `scripts/e4d_evo_power.py` → `power.json`.
2. **The formal stages (§5) are written after binding:** test-first, against §10's list; reviewed by both; their
   commit recorded in a dated amendment and in every formal stage's start marker.
3. **What the formal stage code may not change:** this text, `evo_stats.py`, `power.json`, and the engine paths
   (`wormwars/` outside the new formal stage code, `configs`, `requirements.txt`). A change to them is an amendment,
   with an equivalence check where it touches the engine (rule 7). The formal script's guarded files include this
   text, `evo_stats.py`, `power.json` and §2's pinned files; every stage refuses if any of them differs from its
   registered state.
4. **The owner's word:** before `check` (it covers the L and F stages that follow it in §5's order), and again before
   S's stages if S is triggered. Nothing else asks.

## 1. The question

**Starting from E-G with the 32 cross-link slots at 0, does selection on the trial's outcome recruit cross-links that
carry A's engineered cue into B?** (design §1)

**Its scope** (Astra): it tests whether this GA recruits transfer through 32 available links between already
engineered modules, at this budget. It does not test the discovery of communication in general.

**What the pilot already showed** (exploratory, D270): in all 20 pilot runs the champion beat E-G, at 0.68-0.96
real-first; the formal run asks whether that holds, by the registered rule, on fresh seeds and fresh mazes.

**What the labels claim:** a statement about the mean real-first share of the arm's champions, on their own test
blocks, against the bound 0.5 for any assignment-blind policy (design §6). The interval is approximate (model-based).
- **Not claimed:** anything about naive modules, other tasks, or cues that are not engineered; nor that a champion's
  gain flows only through the links, beyond the cut control (§7.3).

## 2. Fixed inputs

**The trial** (E4-D design v2.3, unchanged): the island family, c = 6, k_r = 0; one wey in mode B from the first
substep (latch at −1); two candidate goals, A's noses reading the real one, B's the sum; the relays silent, the start
cue off, the goal pinned; the untruncated scent at σ_D = 6; H_t = 600 ticks; the first entry into either candidate
decides the trial; both assignments per maze (one observation). Maze run seed **1 420 000** (the pilot's; fresh ids,
§4).

**The organism:** E-G (`docs/E4/E4-DESIGN.md` v3), with the 32 cross-link slots at 0.

**The GA** (E3c's frame, as in the pilot): population 32, elites 3, truncation 8; mutation w σ 0.08, τ σ 0.15, bias
σ 0.05, p 1.0, scaled per parameter by the arm's mask (§3); **random tie-breaking on** (`random_ties`, the per-run
stream `tie_rng(run seed)`); fitness = the real-first count / 2W over the generation's W mazes; shaping 0, asserted;
the integrity check every generation (every strain whose slots are all zero has equal real-first and decoy-first
counts, else the rollout raises).

**W = 8 mazes per generation** (×2 assignments) and **G = 100 generations:** the pilot's values, the conditions under
which the power analysis is calibrated (§11).

**Pinned files** (sha256 after CRLF → LF; checked before use, refusing on a mismatch):

| File | sha256 |
|---|---|
| `docs/E4/E4-D-EVO-DESIGN.md` | f61427e59e6d58cedb6979cfe252fae0bb5bd257219dd8a604b178bc068f2af4 |
| `docs/E4/E4-D-DESIGN.md` | 84016143855b511018c386c943ac6db57ba4cda27e9a03c0fe9dbdb070add49b |
| the pilot's `precheck.json` | d30506c306f4911455bace0ba4b773aac0e026c12a8eca34dadfd87c5a3c11c3 |
| the pilot's `screen.json` | efcbf2c931e55c0e1270e54b44711a9efc3b68534cd39b9660ac80bad75b42a5 |
| the pilot's `f.json` | 4a6cbab8f5140c7f41a661fd15528304ed60e4e1d4c8c186be9ef6bb5cde5640 |
| `power.json` | 46d579ed56a67c8b18f923852a36b99e854390776a5cb118d1157c7b42702d2a |

**The pilot's generation-10 populations** (local, `runs/e4d-evo/pilot/L-run*-gen010.npz`, gitignored), for `check`:
each population's digest is the sha256 of its 32 strains' `genome_sha256s` (as recorded in the file) concatenated in
order; the 16 digests concatenated in run order (0-3, 100-103, 200-203, 300-303) hash to
**e5a300013c12ba7b23338cdba9569249e41fa4a1e12ffb9977e7c08c8b5da9b5**.

## 3. The arms

| Arm | Start | Mutates (factor × the GA's σ) | Runs | Role |
|---|---|---|---|---|
| **L** | E-G, slots at 0 | the 32 slots only, at 0.25 (σ 0.02) | **32** | primary |
| **F** | E-G, slots at 0 | the slots at 0.25; E-G's weights and τ at 0.25; the module biases at 0.02 | 4 | secondary |
| **S** | E-G with A_CL → B_CL and A_CR → B_CR at w = 0.5 (S₀) | as L | 32 | conditional (§5) |

- **L's and S's frozen sets** are checked bitwise in every saved population (`assert_frozen`); cutting an L or S
  genome's slots gives E-G exactly.
- **F** is `combined_scales(bias_factor=0.02, cross_factor=0.25)`, as in the pilot; it was kept by the owner's rule
  (D266, D270). Its champions are compared with their own cut versions, which are not E-G.
- **S** is the owner's pre-committed follow-up (D266): the hand-built comparator-origin wiring at w = 0.5 (0.59 in the
  feasibility calibration), `control_genome(E-G, "comparator", 0.5)`. **It is triggered only if L reads "practical
  gain excluded; transfer not detected" or "inconclusive"** (design §8). If L is "not evaluable" or "not completed",
  S is not triggered and the owner is asked.
- **No X0 is trained** (design §2): any assignment-blind policy scores at most 0.5 over all trials under paired
  assignments; E-G is played on every test block as the measured baseline.

**The runs:** L's runs are numbered 0-31, F's 100-103, S's 200-231 (the `RunSpec.run` numbers and file names); run k
of an arm has seed 1 440 000 + its number (L 1 440 000-1 440 031, F 1 440 100-1 440 103, S 1 440 200-1 440 231). Each
run's training mazes (`train_ids`) and tie stream (`tie_rng`) are functions of its seed only.

## 4. The maze blocks and ids

All under maze seed 1 420 000, fresh, disjoint from the pilot's (control 53 000-53 063, visibility 53 100-53 611,
validation 53 700-53 763, assessment 53 800-53 863; training 70 000 000-79 999 999; timing 90 000 000 onward) and from
the smokes'.

| Block | Ids | Use |
|---|---|---|
| Check | 54 000-54 063 | `check`'s control, E-G and the oracle |
| Checkpoints | 54 100-54 107 | every run's training checkpoints (the generation-best, every 10 generations; descriptive) |
| L, run k: validation | 55 000 + 128k … + 63 | the champion's choice |
| L, run k: test | 55 064 + 128k … + 63 | every reading of run k |
| F, run k: validation / test | 60 000 + 128(k − 100) … + 63 / 60 064 + 128(k − 100) … + 63 | as L |
| S, run k: validation / test | 61 000 + 128(k − 200) … + 63 / 61 064 + 128(k − 200) … + 63 | as L |
| Training | 100 000 000-109 999 999 | every arm's training mazes |
| Timing | 110 000 000-119 999 999 | `check`'s timing generations only |

- **Independent blocks per run** (Astra): no two runs share a validation or test maze.
- **The pre-flight,** before any training: every block is resolved as it will be played (`evo_trial.qualifying`: an
  id without a qualifying start becomes the next qualifying id not already in its block), and every replacement is
  recorded. The resolved blocks must be pairwise disjoint and disjoint from the pilot's; if they are not, nothing
  runs and an amendment follows. (E4-D's scouting found no maze without a qualifying start; design v2.3 §2.)
- **Training ids** are resolved the same way as they are drawn, as in the pilot; every resolved training id must lie
  in [100 000 000, 110 000 000), else the stage stops ("not evaluable").

## 5. The stages, in order

**The frame:** E2's, as in the pilot: a start marker carrying the formal commit; the once-only rule; partial records
as results complete; a salvage record if a stage stops. Each stage refuses unless its predecessors completed under the
same code and registration (§0.3), and the cap is checked before every rollout.

**The order:** `check` → `train-l` → `evaluate-l` → `report-l` → `train-f` → `evaluate-f` → `report-f`, then, only if
triggered (§3) and after the owner's word, `train-s` → `evaluate-s` → `report-s`. L's reading never waits on F, and F
or S never changes it.

1. **`check`** (GPU, minutes):
   - **the positive control** on the check block, one genome per batch: the comparator-origin control at w = 3, E-G
     and the oracle. It passes if the control's real-first share is at least 0.75 and E-G's real-first and decoy-first
     counts are equal per maze (the pilot's precheck: 0.883, and 63 = 63). The oracle is exempt from the balance
     assertion by design (its B reads the real candidate) and is played with that check off.
   - **the pilot's replay:** the screen's batch (all 16 runs, their seeds, factors and composition [512, 16, 1], its
     validation ids 53 700-53 707 for the checkpoints) through `evolve_batch` with 11 generations and a snapshot at
     index 10. Each run's generation-10 population must equal the local `gen010` population bitwise (§2's digest),
     and each run's generation-10 checkpoint candidate's sha256 must equal `screen.json`'s (rule 6: same GPU,
     environment and composition).
   - **the formal composition's timing:** 3 generations of L's batch ([1 024, 16, 1]; `trial_rollout` plays the whole
     batch as one `TrialWorld` of 16 384 worlds, without chunking) on timing ids, recording seconds per generation and
     peak memory. `train-l` refuses if 100 generations at that rate, plus 20% for checkpoints and saving, exceed 80% of
     the L cap's remainder (§9).
   - **On any failure** nothing else runs, and the owner is asked.
2. **`train-l`:** L's 32 runs in one batch, random ties. Populations and the selections so far saved every 10
   generations and at the last; the final populations saved before the lineage replay, which must match bitwise; the
   frozen set checked in every saved population; the training checkpoints on the checkpoint block.
3. **`evaluate-l`:** for every L run, on its own blocks:
   - **the champion** (§6) from the whole final population on its validation block;
   - **on its test block,** one genome per batch: the champion intact; the cue reversed (A's noses read the decoy);
     the cue removed (A's noses read zero); the cue held fixed (A's noses read candidate 0 of the sorted placement,
     whatever the assignment); the slots cut; and E-G;
   - every condition's real-first, decoy-first and neither counts, per maze.
4. **`report-l`:** §7.1's reading, computed from the records by `evo_stats.reading(gains, n_expected=32)`.
5. **`train-f`, `evaluate-f`, `report-f`:** as 2-4 for F's 4 runs ([128, 16, 1]); `n_expected=4`.
6. **`train-s`, `evaluate-s`, `report-s`** (conditional): as 2-4 for S's 32 runs, starting from S₀; `evaluate-s` also
   plays **S₀ itself** on each S run's test block, one genome per batch.

**The registered assertions.** Each failure raises a dedicated integrity error; the stage stops; **the arm reads "not
evaluable"**; it is never rerun, and the owner is asked:
- every generation, every strain whose slots are all zero has equal real-first and decoy-first counts;
- the frozen sets, bitwise, in every saved population; the lineage replay, bitwise; shaping zero;
- in every evaluation, for each maze: the cue-removed and cue-fixed champions, the cut champion and E-G each have
  equal real-first and decoy-first counts (an assignment-blind policy enters the same candidate under both
  assignments);
- an L or S champion with its slots cut equals E-G bitwise;
- the resolved blocks and training ids as §4.

**Stops that are not integrity failures.** A stage that stops for infrastructure (a crash, a driver failure, the
machine) is rerun once, as a whole, from the same seeds and batch membership; the rerun needs a recorded reason
naming the infrastructure cause, and the frame refuses a second rerun or a rerun after an integrity error. A second
stop makes the arm **"not completed"**; reaching a cap makes it **"not completed (the cap was reached)"**. In either
case the owner is asked, and nothing is read.

**No reduced arm:** a reading needs exactly the registered number of complete runs (32, 4, 32), each with its full
final population, every validation and test maze, and every condition. No run is dropped and no seed is replaced.

## 6. The champion

The run's whole final population (32 strains) on its validation block; the highest real-first share over all 128
trials; ties to the higher final-generation fitness, then the smaller cross-link norm, then the lowest index
(`evo_trial.champion`, design §5).

## 7. The readings

### 7.1 The estimand and the rule (L; confirmatory)

**Per run:** the champion's real-first share over all 128 trials of its own test block, minus 0.5 (a whole number of
trials out of 128). Reported beside: the champion minus E-G on the same block, and all three counts.

**The rule** (`evo_stats.reading`; Astra, the owner's δ = 0.15): the mean gain's one-sided 95% t bounds LB and UB
across the 32 runs, every edge strict:

| Condition | L's reading |
|---|---|
| LB > 0.15 | **"practically relevant transfer found"** |
| 0 < LB and UB < 0.15 | **"weak transfer found"** |
| LB > 0, otherwise | **"transfer detected; its practical size unresolved"** |
| LB ≤ 0 and UB < 0.15 | **"practical gain excluded; transfer not detected"** |
| otherwise | **"inconclusive"** |
| a registered assertion failed (§5) | **"not evaluable"** |
| a stage stopped twice or reached its cap (§5) | **"not completed"** |

The exact one-sided sign-flip p is reported beside, labelled distributional (sign symmetry; smallest 1/2^R); it is
counted exactly in integers on the 1/128 grid (`sign_flip_one_sided`).

**The outcome's wording keeps its limits:** an engineered cue, 32 links between engineered modules, selected junction
starts, this GA at 100 generations of 8 mazes. A null says that this GA, at this budget, did not recruit the transfer
from E-G, not that evolution cannot.

### 7.2 F and S (secondary)

- **F:** the same estimand and rule on its 4 runs, labelled secondary; its power is in §8. F against L is descriptive.
- **S (if triggered):** two readings, both secondary.
  - **S against chance:** the same rule on its 32 champions' gains, reported as **"after seeded initialization"**
    (S₀ already carries some transfer, so this label alone says nothing about what the GA did).
  - **S against its start** (both reviewers): per run, the champion's real-first share minus S₀'s on the same test
    block; the one-sided 95% t lower bound of the mean across the 32 runs. LB > 0: **"the GA improved on the seeded
    wiring"**; otherwise **"no improvement on the seeded wiring detected"**.
- **Read with L's** (S runs only after these two L states):

| L | S against its start | The joint wording |
|---|---|---|
| practical gain excluded; transfer not detected | improved | "transfer not detected from zero; the GA improved a seeded weak link, at this budget" |
| practical gain excluded; transfer not detected | not detected | "transfer not detected from zero, and no improvement on a seeded weak link detected, at this budget" |
| inconclusive | improved | "discovery from zero unresolved; the GA improved a seeded weak link, at this budget" |
| inconclusive | not detected | "discovery from zero unresolved; no improvement on a seeded weak link detected, at this budget" |

### 7.3 Each champion's controls (descriptive, beside §5's assertions)

Expected if the champion uses A's cue through the links: **reversed** → mostly decoy-first; **removed** and **held
fixed** → exactly balanced per maze (asserted), and their real-first share against the champion's shows how much the
cue carries; **cut** → E-G exactly in L and S (asserted), balanced in F (asserted). Reported per champion, with the
counts.

### 7.4 Descriptive

The champions' wiring (each slot's weight; comparator-origin against nose-origin) beside the hand-built control's; the
training checkpoints' real-first shares on the 8-maze checkpoint block (noisy: 16 trials); the tie rates and
parent-pool turnover; the lineages' mutation counts; between-run variation.

## 8. Power (`power.json`)

**What it simulates** (`scripts/e4d_evo_power.py`): per run, a final population of 32 strains with real-first
probabilities 0.5 + g_r m_i; every strain played on a 64-maze validation block; the champion by the best share; the
champion played on a fresh 64-maze test block; R runs read by `evo_stats` (δ = 0.15, one-sided 95% t bounds). 40 000
simulated runs and 20 000 simulated arms per cell (Monte Carlo SE at most 0.0035).

**Calibrated on the pilot** (L at 0.25 and F, 8 runs): the population profile m_i from the final populations'
validation shares (256 strains; validation noise included, which is not necessarily conservative); the success level,
a top gain of 0.399, at which the champions' mean test gain equals the pilot's 0.383; the maze overdispersion of the
champions' pair shares, 0.99 of two independent trials (none), so σ = 0 is the calibrated case and σ = 1 a
sensitivity case (σ = 1 also shifts the marginal means and so the mixture proportions; it is not only added maze
variance).

**The scenarios,** each placed so that the mean champion test gain is μ: **H** (every run near one level, SD 0.03),
**M** (each run succeeds at the pilot's level or sits at 0), **U** (top gains uniform from 0 to twice their centre);
**P** (the pilot's 8 champions resampled).

**P("practically relevant transfer found")** at μ = 0.25 (μ = 0.20 in brackets):

| R | H, σ 0 | M, σ 0 | U, σ 0 | H, σ 1 | M, σ 1 | U, σ 1 |
|---|---|---|---|---|---|---|
| 8 | 1.00 (0.79) | 0.39 (0.17) | 0.45 (0.24) | 1.00 (0.78) | 0.45 (0.18) | 0.42 (0.21) |
| 16 | 1.00 (0.98) | 0.62 (0.26) | 0.79 (0.44) | 1.00 (0.97) | 0.72 (0.28) | 0.74 (0.37) |
| 24 | 1.00 (1.00) | 0.79 (0.35) | 0.92 (0.59) | 1.00 (1.00) | 0.86 (0.37) | 0.90 (0.53) |
| **32** | **1.00 (1.00)** | **0.89 (0.44)** | **0.97 (0.71)** | **1.00 (1.00)** | **0.95 (0.47)** | **0.96 (0.65)** |
| 40 | 1.00 (1.00) | 0.94 (0.51) | 0.99 (0.80) | 1.00 (1.00) | 0.97 (0.54) | 0.99 (0.74) |

- **R = 32 runs for L (and S):** the smallest R in the grid (4, 6, 8, 12, 16, 20, 24, 32, 40, 48) with at least 0.80
  in every main scenario at μ = 0.25. R = 24 misses by M at σ 0 (0.79).
- **At the pilot's own level** (P, μ = 0.383): 1.00 at every R from 4.
- **At μ = 0.20** (Astra's number, set against δ = 0.10) the mixed scenarios reach only 0.44-0.71 at R = 32: a mean
  gain 0.05 above the margin, spread over runs that succeed or fail, is not adequately powered in the tested grid.
  The reading would then most likely be "transfer detected; its practical size unresolved".
- **The rule's false rates:** "practically relevant" at μ = δ, 0.026-0.065 across scenarios and R (the bound is
  approximate; H is the highest); any detection (LB > 0) at μ = 0, 0.047-0.055.

**The approximations, and their sensitivity cases** (Astra, D272; `sensitivity` in the record):
- **Ties:** the simulation breaks the champion's exact ties at random, not by the final fitness and the norm.
- **Structure:** the main grid draws strains independently, each with its own maze effects; the pilot's populations
  show a within-population correlation of per-maze scores of 0.26-0.39. With whole pilot populations' profiles and a
  maze effect shared by every strain of a population (σ_s 1 and 1.5: correlations 0.25-0.26 and 0.40-0.42), the
  power at μ = 0.25 and R = 32 is 1.00 (H), 0.94-0.98 (M) and 0.95 (U).
- **Other failure and success levels** (champion-level two-point mixtures at μ = 0.25, a 128-trial test block): at
  R = 32: failures at 0 and successes at the pilot's level, 0.89; failures at 0 and successes at a perfect 0.5, 0.71;
  failures at −0.10 (harmful) and successes at the pilot's level, 0.77. R = 40 would give 0.80 and 0.85 there.
- **So the 80% is conditional** on runs that fail landing near E-G (an L population keeps E-G-like strains, so its
  champion cannot easily sit far below 0) and successes near the pilot's level (its best champion was 0.96, not 1).
  Outside these the power at R = 32 can fall to about 0.7.
- **F's 4 runs:** 0.88-0.89 at μ = 0.25 if its runs are homogeneous (H), 0.19-0.28 if mixed or spread. F is
  secondary.
- **S:** its 32 runs are read by the same rule, but its run distribution starts from S₀ and need not resemble L's, so
  L's power is not S's; S's reading against its start (§7.2) has no power analysis.

## 9. The budget and the caps

**Projected GPU-hours** (`power.json`, from the pilot's timing at W = 8 and G = 100; evaluation at twice the pilot's
per-run time, for the extra conditions):

| Stages | Pilot-based (a line through the pilot's 16-run and 4-run batches) | Conservative (the precheck's measured per-run rate, 16 runs at W = 8, no intercept, × 1.5) |
|---|---|---|
| `check` (11 generations of the screen's batch at its measured 38 s, the control, 3 timing generations) | ≈ 0.15 | 0.3 |
| L: `train-l`, `evaluate-l` (32 runs) | 2.3 | 3.9 |
| F: `train-f`, `evaluate-f` (4 runs) | 0.4 | 0.5 |
| S, if triggered: `train-s`, `evaluate-s` (32 runs, with S₀) | 2.3 | 3.9 |

**E4's remaining budget** is 23.95 of 30 GPU-hours (D270). **The caps,** each counting every attempt's recorded
seconds (`CapClock`): **6 GPU-hours for `check` and L's stages; 1.5 for F's; 6 for S's.** At most 13.5 in all. A stage
that reaches its cap stops, the arm reads "not completed (the cap was reached)", and the owner is asked; it is never
read as a result. F's and S's caps are separate from L's, so neither can consume L's.

## 10. Tests before the formal run

New code is test-first (rule 9), at the formal compositions where it matters:
- the block layout: every block's ids as §4, disjoint from each other and from the pilot's; the pre-flight's
  replacement rule; a resolved training id outside its range stops the stage;
- the runs' numbers and seeds as §3; S₀ equals `control_genome(E-G, "comparator", 0.5)` and differs from E-G only in
  the two slots;
- the cue conditions: reversed, removed and fixed reach A's noses as specified, at a multi-strain composition; the
  real-first and decoy-first counts swap under reversal for a cue-following control;
- each registered assertion of §5 raises the integrity error on a sabotaged input, and the error makes the arm "not
  evaluable" and is not rerunnable;
- the cut control: an L genome cut equals E-G bitwise;
- the order and refusals: a stage refuses without its completed predecessors, under changed guarded files or
  registration, with an existing start marker, for a second rerun, for a rerun without an infrastructure reason, and
  after an integrity error; S's stages refuse unless `report-l` exists and reads one of the two triggering states;
- the reports: computed only through `evo_stats.reading` with `n_expected`; a reduced arm is refused;
- `check`: the replay comparison fails on a perturbed population and on a wrong snapshot index (sabotage checks); the
  timing refusal fires on an inflated projection.

## 11. Post-pilot choices (from the pilot, D269-D270)

- **The slot factor is 0.25,** by the screen's declared rule.
- **F is kept,** by the owner's rule.
- **W = 8:** fixed by the precheck's rule. The precheck noted that W = 16 costs 8% more per generation and halves the
  fitness noise (D269); it stays 8, because the pilot's populations, which calibrate the power analysis, were trained
  at 8.
- **G = 100,** the pilot's, for the same reason. (Draft 1 also cited the generation at which the best training fitness
  first exceeded 0.65; at W = 8 the best of 32 strains reaches 11/16 by chance in most generations, so that is not a
  reason: Fable, D272.)
- **R = 32 runs for L and S,** from the power analysis (§8).
- **The power target's spacing:** Astra proposed 80% power at a mean gain of 0.20 against δ = 0.10; with the owner's
  δ = 0.15, the target keeps the spacing (0.10 above the margin, a mean gain of 0.25), and 0.20 is reported beside.
- **The `check` stage** (new): the control, a bitwise replay of the pilot's first 10 generations, and the formal
  composition's timing.

## 12. Changes from draft 1 (both reviews, D272)

- **S** (both, high): S₀ is played on every S test block; S is read against its start as well as against chance; the
  joint wording is a per-state table that keeps "inconclusive" unresolved (§7.2).
- **Failures** (both, high): one rule. A registered assertion failing makes the arm "not evaluable", never rerun;
  infrastructure stops are rerun once with a recorded reason; a second stop or the cap makes the arm "not
  completed"; no reduced arm (§5). `evo_stats.reading` refuses malformed gains and a wrong count.
- **F cannot block L** (Astra, high): L is trained, evaluated and reported before F starts; separate caps (§5, §9).
- **The rule's tests** (both): the constants pinned; the strict edges tested independently (Astra's `>=` sabotage now
  fails); malformed inputs; the sign-flip counted exactly in integers (2^32 patterns were unenumerable), checked
  against enumeration with zeros and ties.
- **`check`** (both): 11 generations with a snapshot at index 10; the local populations pinned by digest and the
  committed checkpoint hashes compared; the formal composition timed, with a refusal; "chunks of 512 worlds" removed
  (the trial rollout does not chunk).
- **The assertions** (Astra): exact per-maze balance for the cue-removed, cue-fixed, cut and E-G conditions; the
  oracle's exemption stated (§5).
- **The power analysis** (Astra; Fable): its approximations disclosed, the "conservative profile" claim removed,
  sensitivity cases added (structured populations with shared maze effects; champion-level mixtures with harmful
  failures or a higher success level), wording made conditional, S's power no longer equated with L's (§8).
- **The timing** (both): the precheck's 42.8 s per generation was 16 runs, not 8; the conservative column is now the
  measured per-run rate times 1.5, read from the record; S's rows added (§9).
- **The execution contract** (both): run numbers, the checkpoint block, the training-id range, the guarded files,
  the owner's word stated once (§0.4), the bounds renamed LB and UB (the arm is L).
- **G's rationale** (Fable): the calibration's condition only (§11); the descriptive learning curve is on the
  checkpoint block, labelled noisy (§7.4).
