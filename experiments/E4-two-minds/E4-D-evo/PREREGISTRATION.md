# The evolutionary E4-D: pre-registration

**Status: draft 1, for review by both reviewers. Nothing here binds yet.** It binds at the commit that is pushed after
both reviewers agree. From then on, registered text is never changed or removed; amendments are added beside it, dated
(AGENTS.md, rule 2).

**Its sources:**
- the design, `docs/E4/E4-D-EVO-DESIGN.md` v2.1 (D265, D266), and the trial's design, `docs/E4/E4-D-DESIGN.md` v2.3;
- the owner's choices (D266): δ = 0.15; F kept only if its pilot passes; a pre-committed seeded follow-up (S);
- the exploratory pilot (D269, D270): the precheck, the factor screen and arm F;
- the power analysis, `scripts/e4d_evo_power.py` → `power.json` (§8).

Choices made after seeing the pilot are marked **post-pilot** and listed in §11.

## 0. The binding sequence

1. **This text binds** at its pushed commit, together with:
   - the registered rule, `wormwars/e4/evo_stats.py`, and its tests (`tests/test_e4d_evo_stats.py`);
   - the power analysis, `scripts/e4d_evo_power.py` → `power.json`.
2. **The formal stages (§5) are written after binding:** test-first, against §10's list; reviewed by both; their
   commit recorded in a dated amendment and in every formal stage's start marker.
3. **What the formal stage code may not change:** this text, `evo_stats.py`, and the engine paths (`wormwars/`
   outside the new formal stage code, `configs`, `requirements.txt`). A change to them is an amendment, with an
   equivalence check where it touches the engine (rule 7).
4. **The owner's word** before each GPU stage.

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

**W = 8 mazes per generation** (×2 assignments) and **G = 100 generations** (post-pilot, §11): the pilot's values,
under which every pilot run succeeded and from which the power analysis is calibrated.

**Pinned files** (sha256 after CRLF → LF; checked before use, refusing on a mismatch):

| File | sha256 |
|---|---|
| `docs/E4/E4-D-EVO-DESIGN.md` | f61427e59e6d58cedb6979cfe252fae0bb5bd257219dd8a604b178bc068f2af4 |
| `docs/E4/E4-D-DESIGN.md` | 84016143855b511018c386c943ac6db57ba4cda27e9a03c0fe9dbdb070add49b |
| the pilot's `precheck.json` | d30506c306f4911455bace0ba4b773aac0e026c12a8eca34dadfd87c5a3c11c3 |
| the pilot's `screen.json` | efcbf2c931e55c0e1270e54b44711a9efc3b68534cd39b9660ac80bad75b42a5 |
| the pilot's `f.json` | 4a6cbab8f5140c7f41a661fd15528304ed60e4e1d4c8c186be9ef6bb5cde5640 |
| `power.json` | 978b37703515056e4793a09428eddcf61d6480c3a610db3d3eaef30b9a684440 |

## 3. The arms

| Arm | Start | Mutates (factor × the GA's σ) | Runs | Role |
|---|---|---|---|---|
| **L** | E-G, slots at 0 | the 32 slots only, at 0.25 (σ 0.02) | **32** | primary |
| **F** | E-G, slots at 0 | the slots at 0.25; E-G's weights and τ at 0.25; the module biases at 0.02 | 4 | secondary |
| **S** | E-G with A_CL → B_CL and A_CR → B_CR at w = 0.5 | as L | 32 | conditional (§5) |

- **L's frozen set** is checked bitwise in every saved population (`assert_frozen`); cutting an L genome's slots
  gives E-G exactly.
- **F** is `combined_scales(bias_factor=0.02, cross_factor=0.25)`, as in the pilot; it was kept by the owner's rule
  (D266, D270). Its champions are compared with their own cut versions, which are not E-G.
- **S** is the owner's pre-committed follow-up (D266): the hand-built comparator-origin wiring at w = 0.5 (0.59 in the
  feasibility calibration). It separates "cannot discover the wiring" from "cannot strengthen it". **It runs only if
  L reads "practical gain excluded; transfer not detected" or "inconclusive"** (design §8); not otherwise.
- **No X0 is trained** (design §2): any assignment-blind policy scores at most 0.5 over all trials under paired
  assignments; E-G is played on every test block as the measured baseline.

**The run seeds:** L 1 440 000 + k (k = 0 … 31); F 1 440 100 + k (k = 0 … 3); S 1 440 200 + k (k = 0 … 31). Each run's
training mazes (`train_ids`) and tie stream (`tie_rng`) are functions of its seed only.

## 4. The maze blocks and ids

All under maze seed 1 420 000, fresh, disjoint from the pilot's (control 53 000-53 063, visibility 53 100-53 611,
validation 53 700-53 763, assessment 53 800-53 863; training 70 000 000-79 999 999; timing 90 000 000 onward) and from
the smokes'.

| Block | Ids | Use |
|---|---|---|
| Check | 54 000-54 063 | §5's `check` (the control, E-G, the oracle) |
| L, run k: validation | 55 000 + 128k … + 63 | the champion's choice |
| L, run k: test | 55 064 + 128k … + 63 | every reading of run k |
| F, run k: validation / test | 60 000 + 128k … + 63 / 60 064 + 128k … + 63 | as L |
| S, run k: validation / test | 61 000 + 128k … + 63 / 61 064 + 128k … + 63 | as L |
| Training | 100 000 000-109 999 999 | every arm's training mazes |

- **Independent blocks per run** (Astra): no two runs share a validation or test maze.
- **The pre-flight,** before any training: every block is resolved as it will be played (`evo_trial.qualifying`: an
  id without a qualifying start becomes the next qualifying id not already in its block), and every replacement is
  recorded. The resolved blocks must be pairwise disjoint and disjoint from the pilot's; if they are not, nothing
  runs and an amendment follows. (E4-D's scouting found no maze without a qualifying start; design v2.3 §2.) Training
  ids are resolved the same way as they are drawn, as in the pilot.

## 5. The stages, in order

**The frame:** E2's, as in the pilot (`scripts/e4d_evo.py`'s successor): a start marker carrying the formal commit;
the once-only rule; partial records as results complete; a salvage record if a stage stops; each stage refuses unless
its predecessors completed under the same code and registration; the cap checked before every rollout.

1. **`check`** (GPU, minutes):
   - **the positive control** on the check block, one genome per batch: the comparator-origin control at w = 3, E-G
     and the oracle, with every integrity check. It passes if the control's real-first share is at least 0.75 and
     E-G's real-first and decoy-first counts are equal (the pilot's precheck: 0.883 and 63 = 63).
   - **the pilot's replay:** the screen's batch (all 16 runs, its seeds, factors and composition) for 10 generations
     at the formal commit; its generation-10 populations must equal the pilot's saved `gen010` populations bitwise
     (rule 6: same GPU, environment and composition).
   - **On a failure** nothing else runs, and the owner is asked.
2. **`train-l`:** L's 32 runs in one batch (composition [1 024, 16, 1], chunks of 512 worlds), random ties.
   Populations and the selections so far saved every 10 generations and at the last; the final populations saved
   before the lineage replay, which must match bitwise; L's frozen set checked in every saved population.
3. **`train-f`:** F's 4 runs in one batch ([128, 16, 1]), the same saving and checks.
4. **`evaluate`:** for every L and F run, on its own blocks:
   - **the champion** (§6) from the whole final population on its validation block;
   - **on its test block,** one genome per batch: the champion intact; the cue reversed (A's noses read the decoy);
     the cue removed (A's noses read nothing); the cue held fixed (A's noses read the first candidate in the sorted
     order, whatever the assignment); the slots cut; and E-G;
   - every condition's real-first, decoy-first and neither counts, per maze.
5. **`report`:** the readings of §7, computed from the records by one function, `evo_stats.reading`.
6. **Conditional, only if L's state is "practical gain excluded; transfer not detected" or "inconclusive":
   `train-s`, `evaluate-s`, `report-s`,** as stages 2, 4 and 5 for S. The owner is told first.

**Eligibility:** a run counts only if it completed all 100 generations, passed every integrity check, and its champion
was played on every validation and test maze. **A stage that stops for infrastructure** (a crash, a driver failure,
the machine) is rerun once, as a whole, from the same seeds and batch membership, with the reason recorded; no seed is
replaced and no run is dropped. A second stop, or a stop for any other reason, is reported and the owner is asked.

## 6. The champion

The run's whole final population (32 strains) on its validation block; the highest real-first share over all 128
trials; ties to the higher final-generation fitness, then the smaller cross-link norm, then the lowest index
(`evo_trial.champion`, design §5).

## 7. The readings

### 7.1 The estimand and the rule (L; confirmatory)

**Per run:** the champion's real-first share over all 128 trials of its own test block, minus 0.5. Reported beside:
the champion minus E-G on the same block, and all three counts.

**The rule** (`evo_stats.reading`; Astra, the owner's δ = 0.15): the mean gain's one-sided 95% t bounds L and U across
the 32 runs:

| Condition | L's reading |
|---|---|
| L > 0.15 | **"practically relevant transfer found"** |
| 0 < L and U < 0.15 | **"weak transfer found"** |
| L > 0, otherwise | **"transfer detected; its practical size unresolved"** |
| L ≤ 0 and U < 0.15 | **"practical gain excluded; transfer not detected"** |
| otherwise | **"inconclusive"** |
| an integrity failure in a counted run | **"not evaluable"** |

The exact one-sided sign-flip p is reported beside, labelled distributional (sign symmetry; smallest 1/2^R).

**The outcome's wording keeps its limits:** an engineered cue, 32 links between engineered modules, selected junction
starts, this GA at 100 generations of 8 mazes. A null says that this GA, at this budget, did not recruit the transfer
from E-G, not that evolution cannot.

### 7.2 F and S (secondary)

- **F:** the same estimand and rule on its 4 runs, labelled secondary; its power is in §8. F against L is descriptive.
- **S (if run):** the same rule on its 32 runs. Read with L's:
  - L null or inconclusive, S found (any of the first three states): **"the GA strengthens a weak engineered link but
    did not discover one from zero at this budget"**;
  - L and S both not found: **"the GA neither discovered nor strengthened the transfer at this budget"**.

### 7.3 Each champion's controls (descriptive)

Expected if the champion uses A's cue through the links: **reversed** → mostly decoy-first; **removed** and **held
fixed** → near 0.5 or below (no assignment information); **cut** → E-G exactly in L (bitwise: the cut genome equals
E-G, and its counts equal E-G's), balanced real-first and decoy-first in F. Reported per champion, with the counts;
not tests.

### 7.4 Descriptive

The champions' wiring (each slot's weight; comparator-origin against nose-origin) beside the hand-built control's; the
fitness curves and the generation at which each run's best fitness first exceeds 0.65; the tie rates and parent-pool
turnover; the lineages' mutation counts; between-run variation.

## 8. Power (`power.json`)

**What it simulates** (`scripts/e4d_evo_power.py`; Astra's whole-rule requirement): per run, a final population of 32
strains with real-first probabilities 0.5 + g_r m_i; every strain played on a 64-maze validation block; the champion by
the best share; the champion played on a fresh 64-maze test block; R runs read by `evo_stats` (δ = 0.15, one-sided 95%
t bounds). 40 000 simulated runs and 20 000 simulated arms per cell.

**Calibrated on the pilot** (L at 0.25 and F, 8 runs): the population profile m_i from the final populations'
validation shares (256 strains); the success level, a top gain of 0.399, at which the champions' mean test gain equals
the pilot's 0.383; the maze overdispersion of the champions' pair shares, 0.99 of two independent trials (none), so
σ = 0 is the calibrated case and σ = 1 a sensitivity case.

**The scenarios,** each placed so that the mean champion test gain is μ: **H** (every run near one level, SD 0.03),
**M** (each run succeeds at the pilot's level or not at all), **U** (top gains uniform from 0 to twice their centre);
**P** (the pilot's 8 champions resampled).

**P("practically relevant transfer found")** at μ = 0.25 (μ = 0.20 in brackets):

| R | H, σ 0 | M, σ 0 | U, σ 0 | H, σ 1 | M, σ 1 | U, σ 1 |
|---|---|---|---|---|---|---|
| 8 | 1.00 (0.80) | 0.38 (0.16) | 0.47 (0.24) | 1.00 (0.77) | 0.45 (0.18) | 0.41 (0.21) |
| 16 | 1.00 (0.98) | 0.61 (0.25) | 0.79 (0.44) | 1.00 (0.97) | 0.72 (0.28) | 0.75 (0.40) |
| 24 | 1.00 (1.00) | 0.78 (0.34) | 0.93 (0.58) | 1.00 (1.00) | 0.87 (0.37) | 0.90 (0.54) |
| **32** | **1.00 (1.00)** | **0.89 (0.43)** | **0.98 (0.71)** | **1.00 (1.00)** | **0.94 (0.45)** | **0.96 (0.66)** |

- **R = 32 runs for L (and S):** the smallest R in the grid (4, 6, 8, 12, 16, 20, 24, 32) with at least 0.80 in every scenario at
  μ = 0.25. R = 24 misses by M at σ 0 (0.78).
- **At the pilot's own level** (P, μ = 0.383): 1.00 at every R from 4.
- **At μ = 0.20** (Astra's number, set against δ = 0.10) the mixed scenarios reach only 0.43-0.71 at R = 32: a mean
  gain only 0.05 above the margin, spread over runs that succeed or fail, is not resolved at an affordable R. The
  reading would then most likely be "transfer detected; its practical size unresolved".
- **The rule's false rates:** "practically relevant" at μ = δ, 0.025-0.059 across scenarios and R (the bound is
  approximate; U at σ 1 is the highest); any detection (L > 0) at μ = 0, 0.045-0.055.
- **F's 4 runs:** 0.88-0.90 at μ = 0.25 if its runs are homogeneous (H), 0.19-0.28 if mixed or spread. F is secondary.
- **S** uses L's R and is read by the same rule; its power is L's at the same μ.

## 9. The budget and the cap

**Projected GPU-hours** (`power.json`, from the pilot's timing at W = 8 and G = 100, evaluation included at twice
the pilot's per-run time for the four extra conditions):

| Stage | Pilot-based | Conservative (the precheck's 8-run rate, no intercept) |
|---|---|---|
| `check` | ≈ 0.15 | 0.3 |
| `train-l` (32 runs) + `train-f` (4) + `evaluate` | 2.6 | 5.7 |
| conditional S (32 runs) + its evaluation | 2.3 | 5.1 |

**E4's remaining budget** is 23.95 of 30 GPU-hours (D270). **The caps:** 8 GPU-hours for `check`, `train-l`, `train-f`,
`evaluate` and `report` together; 7 for S's stages. A stage that reaches its cap stops, is recorded as "not completed
(the cap was reached)", and the owner is asked; it is never read as a result.

**Order and words:** the owner's word before `check`, and again before S if S runs. `train-f` follows `train-l`, so
an F failure cannot touch L.

## 10. Tests before the formal run

New code is test-first (rule 9), at the formal compositions where it matters:
- the block layout: every block's ids as §4, disjoint from each other and from the pilot's; the pre-flight's
  replacement rule;
- the seeds as §3; S's start genome equals `control_genome(E-G, "comparator", 0.5)` and differs from E-G only in the
  two slots;
- the cue conditions: reversed, removed and fixed reach A's noses as specified, at a multi-strain composition; the
  real-first and decoy-first counts swap under reversal for a cue-following control;
- the cut control: an L genome cut equals E-G bitwise;
- S's condition: S's stages refuse unless L's report exists and reads one of the two states;
- the report: computed only through `evo_stats.reading`; a sabotaged reading fails a test;
- the check stage: the replay comparison fails on a perturbed population (a sabotage check).

## 11. Post-pilot choices (from the pilot, D269-D270)

- **The slot factor is 0.25,** by the screen's declared rule.
- **F is kept,** by the owner's rule.
- **W = 8:** fixed by the precheck's rule. The precheck noted that W = 16 costs 8% more per generation and halves the
  fitness noise (D269); it stays 8, because the pilot's populations, which calibrate the power analysis, were trained
  at 8 and all succeeded.
- **G = 100,** the pilot's: every pilot run's best training fitness exceeded 0.65 by generation 6 (L at 0.25 and F).
- **R = 32 runs for L and S,** from the power analysis (§8).
- **The power target's spacing:** Astra proposed 80% power at a mean gain of 0.20 against δ = 0.10; with the owner's
  δ = 0.15, the target keeps the spacing (0.10 above the margin, a mean gain of 0.25), and 0.20 is reported beside.
- **The `check` stage's replay** of the pilot (new): the formal code must reproduce the pilot's populations before any
  formal training.
