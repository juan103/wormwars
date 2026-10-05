# E3c pre-registration: the assembly comparison in the maze shuttle

**Status: draft 1, for review by both reviewers.** It binds at the commit that is pushed after their
agreement. From then on, registered text is never changed or removed; amendments are added beside it, dated
(AGENTS.md, rule 2).

**Its sources:**
- the design, `docs/E3/E3c-DESIGN.md` v2.1 (D200);
- the exploratory pilot and its replay and probe (`PILOT.md`, D203-D206);
- the owner's choices: E3c then E4 (D198), the replay first, running as designed if scent-free (D205), and
  the dual practical margin (2026-10-05).

Everything here that changed after the pilot is marked **post-pilot** and listed in §13.

## 1. The question, narrowed by the pilot

**The pilot changed what E3c can say.**
- **What it found:** the from-scratch champions solve this maze task as scent-free wall-followers.
  - They keep 100% of their visits with the noses removed, and repeat a full circuit of the tree (D206).
  - W2's reflex with a constant turn bias makes 5.6-5.8 visits, above the engineered seed's 4.82.
- **The consequence for E3c's questions:** they compare **training routes on a task that a scent-free
  circuit solves**. They do not compare assemblies of stereo navigators.
- **The task is not changed,** as the design's §5 requires.

**The primary questions** (as in the design's §1, narrowed in wording):
- **Q1, structure under one training recipe:** from random weights, at equal training evaluations, does an
  organism on E's modular mask score differently from a dense controller of the same 11 neurons? It compares
  two masks under one start distribution and one search recipe. It is not a test of modularity in general.
- **Q2, the engineered initialization:** at equal training evaluations, do the engineered seed E + W2 plus
  tuning (P-joint) score differently from E's mask trained from scratch (S-mod)? The two arms differ in their
  starting values and in their mutation recipe (factor 0.25 against 1.0); the labels say so.

**A registered mechanistic question, post-pilot:**
- **The coverage hypothesis:** the from-scratch champions solve the task by scent-free coverage. P-joint's
  champions depend more on their noses.
- It is read by the noses-removed reading and the path measures (§7.3). It does not change Q1's or Q2's
  labels; it is reported beside them.

**Descriptive:**
- P-sel: whether evolution finds a working selector in mazes, with E's modules frozen;
- R-shared, the engineered shared navigator, against P-fixed;
- the scent-free reference, W2 with a constant turn (§3).

**Not claimed:**
- cumulative reuse savings;
- the equivalence of arms ("unclear" is never read as "equivalent");
- anything about stereo navigation that the noses-removed reading does not support.

## 2. Fixed inputs

**The task:** E3b-1's maze shuttle, unchanged:
- c = 5, H = 2 400;
- colonies of 8 on up to 4 spawns;
- shared trails (μ 0.01, λ 0.02, δ 0.05, d₀ 1.142);
- maze run seed 1 180 000, with Amendment 1's redraw rule (`maze.walls_for`);
- W2 frozen;
- E2's GA (population 32, elites 3, truncation 8), with unshaped fitness (visits per wey).

**Pinned files** (sha256 after CRLF → LF):
- **E4s-0's `module.json`:** 9613cd155a20ed2cfb891c1bd10fed16814f24a04f912a1940524f2378e877d4;
- **the pilot's `pilot.json`:** 6f6402ebecdf34633a77f8e4df97f8cf9a1e86316179116a63a668286d9ee41e;
- **E3b-1's `train-tf.json`:** P-joint's 8 final populations are checked against its recorded hashes;
- **E3b-1's `maze-reference.json`:** the maze generator, bitwise, through `g-e`.

**The engine:**
- E3b-1's T-F cohort trained at f881308. E3c's own code is bound at this registration's commit.
- `g-e` (§5) reruns E3b-1's three legs at that commit: the GPU hashes, the CPU equivalence and the maze
  reference.

## 3. The arms

| Arm | Mask | Start | Mutates | Factor | Runs |
|---|---|---|---|---|---|
| **P-fixed** | E | the seed E + W2 | nothing | — | — |
| **P-sel** | E | E's modules frozen; the 13 selector parameters drawn by `samplers.ga_draw` | the selector's 13 | 1.0 | 4 |
| **P-joint** | E | the seed | E's 65 | 0.25 | 8, **reused:** E3b-1's T-F cohort |
| **S-mod** | E | B-task's draw projected onto E's mask (`assembly.draw`) | E's 65 | 1.0 | 8 |
| **S-dense** | B-task's full mask | B-task's draw (`assembly.draw`) | 171 | 1.0 | 8 |
| **R-shared** (reference) | E3a's `b_shared` plus W2 | engineered | nothing | — | — |
| **W2-turn** (reference, post-pilot) | W2 alone with a constant resting turn | a grid, one chosen on validation | nothing | — | — |

**The schedule:** every trained arm runs T-F's schedule, 300 generations × 8 mazes per genome. Equal training
evaluations is the matching unit.

**The seeds:**
- **The run seeds:** 1 300 000 + run, with S-mod's runs 0-7, S-dense's 10-17 and P-sel's 20-23.
- **The draws:** `default_rng([run seed, 0xE3C])`, as in the pilot.
- **The training ids:** base 40 000 000, span 10 000 000. They are new, and disjoint from E3b-1's (10-20 M)
  and the pilot's (30-40 M).

**The frozen sets** are as in the pilot (`assembly.arm_scales`). They are checked bitwise against each run's
draw, in every saved population (D201).

**The mutation factor stays 1.0.** The pilot permitted changing it (design §5), and the from-scratch arms
learned at 1.0.

**The W2-turn reference** (post-pilot):
- **The grid:** the resting turns −0.8, −0.4, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4 (as in the probe).
- **The choice:** the one with the best mean visits on E3c's validation block, ties to the smaller |turn|.
  It is then played on the test block.

**P-joint:**
- **The checks:** its 8 final populations (index 299, 32 genomes each, local) are checked against
  `train-tf.json`'s recorded hashes before use.
- **Its champions** are reselected on E3c's validation block by the rule of §6, the same as every arm's.

## 4. The maze blocks (new, and disjoint from every earlier block)

| Block | Ids | Use |
|---|---|---|
| Validation | 10 000-10 127 (128) | champion selection; the W2-turn choice |
| Learning curve | 10 200-10 327 (128) | the checkpoints of the new arms; P-joint's two points |
| Test | 10 400-10 655 (256) | every reading |
| Training | 40 000 000-49 999 999 | the new arms' training mazes |

**The check:** every id, the training ids the schedule will draw included, is pre-flighted by `walls_for`
before training. Redraws are recorded (Amendment 1's rule).

**Unused by E3c:**
- the earlier blocks: E3b-0's, E3b-1's, E3b-2's, the pilot's 7 600-7 727 and the smokes';
- the audit ids 9 900-9 902.

## 5. The stages, in order

Every stage runs on E2's frame (`scripts/e3c.py`). Each has:
- a start marker;
- the once-only rule, and one rerun with a stated reason;
- a partial record each minute;
- a salvage record if it stops.

The stages:
1. **`project`:** the benchmark.
   - It times one generation of each training composition, and the checkpoint and evaluation chunks.
   - It projects the formal total against the cap, and applies §10's cuts if needed.
2. **`g-e`:** the engine check at E3c's commit: E3b-1's GPU hashes, the CPU equivalence and the maze
   reference.
   - **Off Windows,** the CPU leg's bitwise reference is not expected to match (rule 6; D202), and `g-e` is
     read on the tested platform only.
3. **`train-s`:** S-mod and S-dense, as two batches.
   - **Each batch:** 8 runs × 32 strains × 8 worlds × 8 weys, that is [256, 8, 8].
   - **The checkpoints** (post-pilot, denser early): every 5 generations to 50, then every 25, and at 299.
     They are played on the learning-curve block.
   - **Saved locally:** every run's final population and checkpoint candidates, with their hashes in the
     record.
4. **`train-psel`:** P-sel, 4 runs, [128, 8, 8], with the same checkpoints and saving.
5. **`champions`:** every arm's final populations (32 genomes per run) on the validation block.
   - P-joint's 8 runs are included; its populations are checked against `train-tf.json` first.
   - The W2-turn choice is made here.
6. **`evaluate`:** every champion, P-fixed, W2 alone, W2-turn and R-shared on the test block, under shared
   trails.
   - **Each champion** is also played with the noses removed, and with each wey's cell path recorded.
   - **The secondary condition,** trails off, is the first cut (§10).
7. **`report`:** the readings of §7, from the records only.

## 6. Champions

**The rule, the same for every trained arm:**
- **The candidates:** the 32 genomes of the run's final population (index 299).
- **The champion:** the genome with the best mean visits per wey on the validation block, ties to the lower
  index.
- **P-joint's champions** are reselected by this rule on E3c's block. The new champion is used, never a choice
  between E3b-1's and E3c's.

**Saved and published:**
- **Saved locally:** every champion's genome.
- **Published:** every champion's grafted parameters by name (as E3a's `champions-3.json`), so that an
  outsider can rebuild each champion (D200).

## 7. The readings

### 7.1 The unit and the primary contrasts

**The unit:** d = (the champion's mean visits per wey on the 256 test mazes − P-fixed's) / P-fixed's mean.
- The run is the independent unit.
- Inference is conditional on the test block.
- A maze-paired bootstrap is a supplement.

**The contrasts** (`wormwars/e3/e3c_stats.py`, tested):
- Q1 = mean d (S-mod) − mean d (S-dense);
- Q2 = mean d (P-joint) − mean d (S-mod).

**The test:**
- each contrast is a two-sided Welch test, with Holm's step-down over the two at 5%;
- **its interval** is the Welch interval at its Holm level, 1 − 0.05 / (2 − rank). After a contrast that is
  not rejected, later ones keep that step's level. A contrast is rejected exactly when its interval excludes
  0.

**The practical margin** (post-pilot; the owner's choice; both reviewers' proposals kept):
- **The two margins:**
  - 0.10 of P-fixed's mean (Fable; E3b-1's "at least 10%");
  - 0.5 visits per wey (Astra), that is 0.5 / P-fixed's mean in d.
- **How they combine:**
  - m_lo is the smaller of the two, m_hi the larger;
  - "beyond the margin" needs the interval to clear m_hi;
  - "no relevant difference" needs it inside ±m_lo.
- **What it means:** both margins must agree before a difference is called relevant, or negligible. On a
  block where P-fixed makes 5.0, the two coincide at 0.10.

**The labels** (Q1: "modular" / "dense"; Q2: "engineered initialization" / "from scratch"):

| Holm | The interval | Label |
|---|---|---|
| rejected | beyond m_hi | "X better, beyond the margin" |
| rejected | entirely inside m_lo, on X's side | "X better, within the margin" |
| rejected | otherwise | "X better, margin unresolved" |
| not rejected | inside ±m_lo | "no relevant difference" |
| not rejected | otherwise | "unclear" |

**Q1's floor guard:** Q1 is "not read: both at the floor" unless at least one S arm's mean test visits exceed
W2 alone + 1. If so, it enters Holm with p = 1.

**The supplement:** a two-sided Mann-Whitney U test per contrast, unadjusted. It is reported, never a label.

**The expectations, registered:**
- **Q2:** the design registered "engineered initialization better" (§1, v2.1). That sentence stands.
  - **Annotation (post-pilot):** the pilot makes the direction uncertain. On different blocks, the S arms'
    gain over the seed (+0.38 in d) equals T-F's (+0.381), so "unclear" is the likeliest label (§8).
- **Q1:** "no relevant difference" is expected (post-pilot). The two S arms differed by about 0.08 visits per
  wey in the pilot.

### 7.2 The cost curve (secondary)

**What it measures:** each new run's generations to threshold. That is the first learning-curve checkpoint
whose generation-best exceeds:
- W2 alone + 1;
- P-fixed's level, both measured on the learning-curve block.

**The checkpoints** are denser early (post-pilot). In the pilot, both S arms passed both thresholds before
generation 25.

**The rules:**
- A threshold is right-censored at 299.
- A run reaching it at 299 is a success; one not reaching it is censored.

**Per arm:**
- the number of runs reaching each threshold. Fisher's exact test compares S-mod with S-dense, with Holm
  over the two thresholds;
- the median generation, or "not reached" when fewer than half the runs reach it.

### 7.3 Scent dependence and the coverage hypothesis (secondary; post-pilot)

**For every champion** (P-joint's and P-sel's included), and for P-fixed, on the test block:
- **The retained fraction** r = visits with the noses removed / intact visits.
  - **"Noses removed":** the four A/B nose channels at gain 0. The relays' source-occupancy inputs and W2's
    collision sensing stay on.
  - **The classes** (Fable): r ≥ 0.9 "scent-independent", r ≤ 0.5 "scent-dependent", else "partial".
  - **The paired loss** L = mean over mazes of (intact − noses removed) visits, with each arm's run-level
    interval (Astra).
  - **"No material loss"** for an arm: the upper end of its 95% interval for mean L is below m_lo in visits.
- **The path measures,** intact, as in the probe (D205):
  - the coverage of the 25 cells, averaged over weys and mazes;
  - the tour match: directed moves at lag 48, averaged over weys with more than 48 moves;
  - the best lag over 44-52, beside it.
- **"Coverer"** (D205's criterion, per champion): r ≥ 0.9, coverage ≥ 0.95 and tour match ≥ 0.5.

**The coverage hypothesis:**
- **"supported"** if at least 6 of 8 champions in each S arm are coverers, and P-joint has fewer coverers than
  either S arm;
- **"not supported"** if at most 2 of 8 in each S arm are coverers;
- **"mixed"** otherwise.

**The qualifier:** each arm's class counts are appended to Q1's and Q2's labels as a qualifier. For example:
"no relevant difference (S-mod: 8/8 coverers; S-dense: 8/8)".

### 7.4 Descriptive

- **P-sel:**
  - the runs whose champion exceeds W2 alone + 1 (E3a: 1 of 8; the pilot: 1 of 3);
  - each run against P-fixed and P-joint.
- **R-shared and W2-turn** against P-fixed and W2 alone.
- **The learning curves.** P-joint's curve has two points on the learning-curve block, its populations at
  index 124 and 299.
- **The secondary outcomes,** as in E3b-2: the later-leg rate, and the unvisited and round-trip shares.
- **Per champion:**
  - the Spearman correlation of its per-maze test visits with P-fixed's, and with the A-B tree distance
    (Fable);
  - its resting turn offset and module A's K_D at q = 0.
- **Trails off,** if not cut.

## 8. Power (`power.json`, simulated as the readings are computed: `scripts/e3c_power.py`)

**The simulation:**
- 2 000 trials per scenario, seed 20 261 005;
- Q1 and Q2 computed jointly by the registered functions, so one S-mod sample enters both;
- P-fixed's test mean set to 5.0, so both margins are 0.10 in d (0.5 visits), with 4.82 and 5.84 as
  sensitivity checks;
- the inputs as in the script's docstring (both reviewers, D204).

**Base case** (8 runs per arm; the S arms' spread at the pilot's 0.06 visits; no failed run):

| True difference | Q1's labels | Q2's labels |
|---|---|---|
| 0 | "no relevant difference" 0.98; any "better" 0.02 | "unclear" 0.97; any "better" 0.02 |
| 0.5 visits | rejected 1.00 (it sits at the margin, so "margin unresolved" 0.98) | rejected 0.19; beyond the margin 0.01-0.02 |
| 1.0 visits | "beyond the margin" 1.00 | rejected 0.65-0.67; beyond the margin 0.19 |

**Failed runs dominate Q1.** Each S run stays near the floor with probability p:

| S arms' spread | p | Q1 at 0: "no relevant difference" | Q1 at 1.0 visits: rejected |
|---|---|---|---|
| 0.06 | 0 | 0.98 | 1.00 |
| 0.06 | 1/8 | 0.12 | 0.35 |
| 0.06 | 1/4 | 0.01 | 0.12 |
| 0.4 | 0 | 0.15 | 0.99 |
| 0.4 | 1/8 | 0.02 | 0.30 |

**What the table says:**
- **A single failed run inflates its arm's spread to about 1.5 visits.** Q1 then most likely reads "unclear",
  whatever the truth. That is the honest label for such data, not an error. The Mann-Whitney supplement is
  reported beside it.
- **Q1's false-positive rate stays at or below 0.03** in every scenario.

**Q2's false positives under failures:**
- with S-mod failing in a quarter of its runs, Q2's rate of any "better" at a true difference of 0 is
  0.054-0.062, above the nominal 0.05. Welch's test is fragile to such mixtures;
- otherwise it is at most 0.03.
- **This is disclosed, not corrected.** The run count stays as designed.

**Q2 is powered only for about a visit:**
- **its power to detect ±1.0 visit:**
  - 0.65 with 8 runs;
  - 0.45 with 6;
  - 0.61 under T-F's empirical shape;
  - 0.69 if P-fixed's test mean is 4.82, and 0.51 if it is 5.84, since the d spread in visits grows with it;
- **at ±0.5 visits:** 0.19;
- **"beyond the margin"** is reached in at most about 0.3 of trials at 1.0 visit.
- **So Q2 is expected to read "unclear"** unless the true difference is near a visit or more. The
  registration says so in advance (§7.1).

**P-sel** (descriptive): the chance that none of its 4 runs finds a working selector is 0.59 at E3a's rate
(1/8), and 0.20 at the pilot's (1/3).

**The cut to 6 runs:**
- leaves Q1 decisive without failures ("no relevant difference" 0.97 at spread 0.06);
- lowers Q2's power at 1 visit to about 0.45.

## 9. The benchmark (`project`)

**What it times:** one generation of each training composition ([256, 8, 8] for S-mod and S-dense, [128, 8, 8]
for P-sel), and the checkpoint, champion and evaluation chunks.

**The projection:** the formal total is projected from those times, with × 1.25 on training. It is checked
against the cap before any training starts.

## 10. The cap, admission and cuts

**The ceiling** is 30 GPU-hours for all of E3c (D198). It is a running total from every attempt's compute
record, the pilot's and the replay's included (3.95 so far).

**The projected formal total** comes from E3b-1's and the pilot's measured rates:

| Part | GPU-hours |
|---|---|
| `project`, `g-e` | about 1.5 |
| S-mod, S-dense (8 × 300 × 8 each) | 2 × 6.44 = 12.9 |
| P-sel (4 × 300 × 8) | about 3.6 |
| Denser checkpoints | about 0.2 |
| Champions (28 runs × 32 × 128) | about 1.0 |
| Evaluation (with the noses-removed condition and the paths) | about 1.5 |
| **Formal total** | **about 20.7**; 24.8 with × 1.25 on training |
| **With the 3.95 spent** | **about 24.7**; 28.8 with × 1.25 |

**The cuts, in order,** if `project`'s projection exceeds the remaining budget:
1. the trails-off condition;
2. P-sel to 2 runs;
3. S-mod and S-dense to 6 runs each.

The primary contrasts, the noses-removed reading and the path measures are kept whole as long as possible.

**The stop:** every stage checks the cap before each rollout. A stage stopped by the cap records what it
finished.

## 11. Budget

**E3c's 30 GPU-hours:**
- 3.95 spent: the pilot 2.82, its seed diagnostic about 0.03, and the replay 1.10;
- the formal run as projected in §10.

## 12. Tests before the formal run

Each test is seen failing first. Where a check could not otherwise fail, it gets a sabotage test.
- **The arms:**
  - the masks, the frozen sets and the draws (`tests/test_e3c_assembly.py`);
  - the bitwise frozen check on every saved population.
- **The statistics:** Welch, Holm with its intervals, the dual margin and the labels
  (`tests/test_e3c_stats.py`).
- **The blocks:** disjoint from every earlier block. Every id is pre-flighted.
- **The stages:**
  - the stage order;
  - the once-only rule and the rerun;
  - the salvage on failure;
  - a CPU smoke of every stage.
- **P-joint:** the hash check against `train-tf.json` is sabotaged: one changed byte must fail.
- **The champion rule:** ties go to the lower index.
- **The W2-turn choice** is made on the validation block only.
- **The noses-removed condition and the path measures:** as tested for the replay (D205).
- **The registered readings** are computed from records by one function. It is tested on synthetic records
  for every label.

## 13. Post-pilot departures from design v2.1

1. **The question's wording is narrowed** (§1). E3c does not compare assemblies of stereo navigators. D206.
2. **The coverage hypothesis is registered,** with the noses-removed reading and the path measures (§7.3).
   D205's consequence for "coverage"; both reviewers.
3. **A scent-free reference is added:** W2 with a constant turn, chosen on validation (§3; Fable).
4. **The practical margin is dual** (§7.1). It is the owner's choice, keeping Fable's 0.10 and Astra's
   0.5 visits.
5. **The labels are interval-based,** at Holm's levels (§7.1). Fable proposed the scheme; the Holm-consistent
   levels are added here.
6. **A Mann-Whitney supplement** is added (Fable).
7. **Q2's expectation is annotated,** and Q1's added (§7.1). Both reviewers.
8. **The early checkpoints are denser** (§5; Fable). The pilot's S runs passed both cost-curve thresholds
   before the first checkpoint.
9. **Genomes are saved,** and published by name (§5, §6). Both reviewers; D200.
10. **The new arms' run seeds and training ids are new** (§3). They are not the pilot's.
11. **`share_above_w2` is dropped.** Fable: it compared different blocks.

## 14. Amendments

None yet.
