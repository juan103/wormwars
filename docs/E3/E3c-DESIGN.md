# E3c design: the assembly comparison — v2.1

**Status:** v2.1, 2026-10-04. Nothing has run.
- **v2** (1e207f5) was reviewed again by both reviewers. Both said "run the pilot", with bounded corrections
  and no further round (`docs/reviews/20261004-E3c-design-2/`, D200). v2.1 takes them; §12 maps them.
- **Who decided:** the owner chose E3c after E3b-2, with a ceiling of 30 GPU-hours (D198).
- **v1** (f0bd143) was reviewed by both reviewers. Both said "revise" (`docs/reviews/20261004-E3c-design/`,
  D199). This draft takes their changes; §11 maps them, with two rulings where they differed.
- **Next:** the pilot (§5), then the power analysis and the pre-registration.

## 1. The question, narrowed

ROADMAP §E3 names four arms:
1. one task-conditioned controller of matched size;
2. pretrained modules with a fixed selector;
3. the same modules with an evolved selector;
4. a modular organism of the same size trained from scratch.

The roadmap asks for the first-use cost (pretraining included) and the cumulative reuse cost.

**E3c is a first-use assembly comparison** in the maze shuttle where E3b-1 passed its gate. It asks:
- **Q1, structure under one training recipe:** from random weights, at equal training evaluations, does an
  organism on E's modular mask beat a dense controller of the same 11 neurons? It compares two masks with one
  start distribution and one search recipe. It is not a test of "modularity" in general.
- **Q2, engineered-initialization advantage:** at equal training evaluations, do the engineered seed E + W2
  plus tuning beat E's mask trained from scratch? The two arms differ in their starting values and in their
  mutation recipe (§3), and Q2's labels say so.
  - **The expected outcome:** it is registered in advance, as "P-joint better".
  - **The informative content:** the size of the advantage, and S-mod's cost to reach the seed's level. Both
    are read beside the cost ledger (§7).
- **Descriptive, the evolved selector:** with E's modules frozen, does evolution find a working selector in
  mazes from a random selector?

**Not claimed:**
- **Cumulative reuse savings.** The only reuse here is P-sel's, on the same task. The reuse cost is reported
  as a scenario (§7), not as an empirical saving.
- **Equivalence of arms.** "Unclear" is never read as "equivalent".

**The frame:**
- the mutable 11-neuron controller sits on engineered scaffolding, common to every arm:
  - the frozen W2 reflex;
  - the carrier;
  - the interface: the noses, and the relays' inputs;
- nothing here is about worm behaviour;
- stereo sensing is a game-design choice.

**The relays' inputs** (`at_a`, `at_b`) are source-occupancy levels with a start-up cue. They are not
persistent goal bits or visit pulses.

## 2. The task

E3b-1's maze shuttle, unchanged:
- c = 5, H = 2 400;
- colonies of 8 on up to 4 spawns;
- shared trails (μ 0.01, λ 0.02, δ 0.05, d₀ 1.142);
- maze run seed 1 180 000, with Amendment 1's redraw rule;
- W2 frozen;
- E2's GA (population 32, elites 3, truncation 8), with unshaped fitness (visits per wey).

**The blocks:** new and disjoint from every earlier block for validation, the learning curve and the test.
- **The new arms' training mazes** are new as well.
- **The exception:** the reused P-joint cohort trained on E3b-1's training ids. That is stated as such.

**The units:** two reference lines are played on E3c's test block, and are the denominators and floors:
- the seed E + W2 (P-fixed);
- W2 alone on the carrier.

## 3. The arms

Every trained arm has the same 11 grafted neurons in the same interface positions, plus W2's 2 frozen
neurons and the carrier.

| Arm | Mask | Start | Mutates | Factor | Runs | Roadmap arm |
|---|---|---|---|---|---|---|
| **P-fixed** | E | the seed E + W2 | nothing | — | — | 2 |
| **P-sel** | E | E's modules intact (frozen); the selector's 13 parameters drawn at random (§4) | the selector's 13 | 1.0 | 4 | 3 |
| **P-joint** | E | the seed | E's 65 mutable scalars | 0.25 | 8, **reused:** E3b-1's T-F cohort | (joint tuning) |
| **S-mod** | E | random (§4) | E's 65 mutable scalars | 1.0 | 8 | 4 |
| **S-dense** | B-task's full mask: all 121 edges among the 11, plus the 32 output edges | random (§4) | 171 scalars | 1.0 | 8 | 1 |
| **R-shared** (reference) | E3a's `b_shared` plus W2: one engineered navigator, two gated nose pairs, the latch; 9 controller neurons | engineered | nothing | — | — | D144's baseline, engineered |

**The schedule:** every trained arm runs T-F's schedule, 300 generations × 8 mazes per genome. Equal training
evaluations (population × generations × mazes × horizon) is the matching unit. Evaluation and selection
compute are equal across arms, and go in the ledger, not in the matching.

**The mutation factor differs, deliberately.** P-joint ran at E3b-1's 0.25 on 02's σ. The arms that start
from random values run at 1.0, as E3a's Stage 2 and B-task did. At 0.25, an edge's mutation step has a
standard deviation of about 0.02, against working values of ±2-3. So a start near 0 is unlikely to reach them
in 300 generations (Fable; "unlikely", not "cannot": a step's σ is not a limit, Astra). So the arms compare
training recipes, not starting values alone, and the readings say so.

**P-joint, reused and reselected:**
- **The cohort:** E3b-1's T-F cohort, 8 runs at 300 × 8. T-F's schedule is the one that gained.
- **The checks:** every final population (32 genomes per run, local) is checked against E3b-1's recorded
  hashes (`train-tf.json`).
- **What is published:** every champion's grafted parameters by name, as E3a's `champions-3.json` did, so an
  outsider can rebuild P-joint and every other champion. The whole genome files stay local by the
  repository's convention (D200 corrects D199's stated reason).
- **The reselection:** they are revalidated on E3c's validation block with the same rule as the new arms
  (the best mean, ties to the lower index). The new champion is used, never a choice between the old and the
  new.
- **The engine check:** `g-e` at E3c's commit reruns E3b-1's three legs (the GPU hashes, the CPU
  equivalence, `maze-reference.json`). The T-F cohort trained at f881308. Since then only
  `e3/attribution.py` has been added under `wormwars/`.

**S-dense's mask:**
- **What it is:** B-task's full mask, neuron-matched rather than parameter-matched. It is a strict superset of
  E's mask.
- **How to read Q1,** by §6's test:
  - "modular better": E's structure beats extra capacity under this recipe;
  - "dense better": capacity and structure are not separable here.

  Both readings are stated in advance.
- **The confound it carries:** more mutable scalars at the same σ means more noise per child. σ is kept equal
  and reported; no scaling rule is invented.
- **The alternatives:** a random 65-edge subset was dropped, since one draw can lack a path or the latch's
  recurrence. A parameter-matched mask distribution sampled per run was considered, but the full mask is the
  existing, reviewed control.
- **The relays** keep their frozen τ and bias in every arm. S-dense's relays can receive recurrent inputs,
  since B-task's mask has them. This is stated as part of the dense recipe.

**Not run: a nonmodular controller with an explicit persistent goal bit.** That is the roadmap's arm 1 as
D144 frames it, but it changes the inputs. R-shared, the engineered shared navigator, is played as a reference
only.

## 4. The starting draws

Each run's generation 0 holds 32 independent draws.
- **S-dense:** `samplers.b_task_draw`, exactly:
  - every edge U[−0.5, 0.5];
  - each left/right pair's τ (log-uniform on [0.5, 20]) and bias (N(0, 0.5²), clipped to ±2) tied;
  - the within-pair blocks symmetric;
  - **two sign patterns:** the nose → comparator edges get L1's antisymmetric pattern (a, −a; −a, a), with
    one random magnitude per module, and each comparator pair's outputs are push-pull (v, −v).
- **S-mod:** the full B-task draw, then projected onto E's mask: the edges outside E's mask are dropped.
  W2 and the carrier's compensation are kept as in every arm.
  - The two arms then share one start distribution on their common positions.
  - **What "structure" means:** E's mask, plus the draw's pair ties and antisymmetric patterns, inherited by
    both arms with random orientation and magnitudes. It does not include E's engineered orientation or
    magnitudes (Fable, Astra: v2 said "without E's engineered signs", which was wrong).
- **P-sel:** `samplers.ga_draw`, E3a Stage 2's start, for the 13 selector parameters:
  - a gate weight U[−0.5, 0.5] and a bias N(0, 0.5²) per module, tied within the module;
  - w_qq, w_aq and w_bq U[−0.5, 0.5];
  - b_q N(0, 0.5²);
  - every bias clipped to ±2;
  - τ_q log-uniform on [0.5, 20].

  The modules' 52 other mutable scalars stay at E's frozen values. No engineered latch survives: the
  self-weight and the relay → latch weights are drawn.
  - **The module boundary is not innocuous:** the 13 include the 4 comparator biases, which set the
    comparators' operating points and resting output.
  - **The expected outcome,** fixed in advance: in E3a's open arena, evolution from this start found a working
    selector in 1 of 8 runs. So P-sel may end below P-fixed. That is a reading of the reuse cost, not a
    failure of the experiment.

## 5. The pilot (exploratory, before the pre-registration)

**The aim:** to see whether the from-scratch arms leave the floor in mazes, and to fix the formal schedule.
- **The arms:** S-mod, S-dense and P-sel, 3 runs each.
- **The schedule:** factor 1.0 (P-sel's selector included), 100 generations × 8 mazes per genome.
- **The checkpoints:** every 25 generations, on a pilot learning-curve block of 128 mazes.
- **The references:** W2 alone and P-fixed are played on the pilot's own block.
- **The cost:** about 2.5 GPU-hours, from T-F's rate (about 76 s a generation for 2 048 worlds; the pilot
  runs 2 304). It is benchmarked on the actual compositions first. v2's 1.5 was an underestimate (both).
- **What the pilot may change:** only the mutation factor of the arms starting from random values. The
  schedule is fixed by P-joint's match. The pre-registration then fixes the factor.
- **Its own blocks:** pilot ids, disjoint from every other.
- **The diagnostics:**
  - the generation-0 distribution of visits, against W2 alone;
  - the turn offsets at generation 0, as E3a logged;
  - the learning curves;
  - the legs per wey.

**The floor is W2 alone,** about 1.7 visits per wey, not zero. A random controller with large outputs can
fight the reflex and score below it.

**The criterion:** an arm is "off the floor" if at least one of its runs has a generation-best above W2 alone
+ 1 visit per wey on the pilot learning-curve block by generation 100. The 1 visit is E3b-0's seed margin over
W2 alone.

**The decision branches** (fixed now):
- **Either S arm off the floor:** E3c runs in mazes, as designed. One arm learning while the other fails is a
  relevant result. Both arms need not learn.
- **Neither S arm off the floor:**
  - Q1 runs in E3a's open shuttle instead, at 8 runs × 800 generations × 16 worlds per arm. That is about
    2.4 GPU-hours per arm; E3a measured a dense arm there.
  - Q2 and P-sel are then not run in mazes, and E3c is narrowed to the open-arena structure question.
  - Shaping, an easier maze or another fitness are not used. They would also break P-joint's match.
- **An incomplete pilot** (stopped by a crash or the budget) is "inconclusive". It does not trigger the
  fallback.
- **The pilot's limits:** 3 runs cannot estimate rare successes or power. The power analysis therefore
  examines a range of success mixtures.

## 6. The readings (to be registered)

**The unit:** d = (the champion's mean visits per wey on the 256 test mazes − the seed's) / the seed's mean.
- The run is the independent unit.
- Absolute visits are reported beside it.
- Inference is conditional on the test block, as in E3b-1. A maze-paired bootstrap is reported as a
  supplement.

**The primary contrasts:**
- **Q1:** Δ₁ = mean d (S-mod) − mean d (S-dense).
- **Q2:** Δ₂ = mean d (P-joint) − mean d (S-mod).
- **The test:** each a two-sample, two-sided Welch test, with Holm's correction over the two at 5%.
- **The labels:**
  - Q1: "modular better", "dense better" or "unclear";
  - Q2: "engineered initialization better", "worse" or "unclear".
- **A practical margin:** to be fixed in the pre-registration from the power analysis.
- **Q1's floor guard:** Q1 is "not read: both at the floor" unless at least one arm's mean over its
  champions' test visits exceeds W2 alone by the pilot's margin.
- **The practical margin** is chosen for scientific relevance. The power analysis says whether it is
  detectable; it does not set it.

**The cost curve (registered, secondary):** each run's generations to threshold, as the first learning-curve
checkpoint (every 25 generations, on one block shared by the new arms) whose generation-best exceeds:
- W2 alone + 1;
- the seed's level.

Each is right-censored at 299.
- **The checkpoint candidate** is the generation-best by fitness, as in `evolve_batch`.
- **A run reaching a threshold at 299** is a success. A run not reaching it is censored, and is never counted
  as reaching at 299.
- **For each arm, the record gives:**
  - the number of runs reaching each threshold. Fisher's exact test is used for S-mod against S-dense, with
    Holm's correction over the two thresholds;
  - the median generation, reported as "not reached" when fewer than half the runs reach it.

**Descriptive:**
- **P-sel:** against P-fixed and P-joint.
- **R-shared:** against P-fixed.
- **The learning curves.**
- **P-joint's curve** is two points on E3c's block (its populations at index 124 and 299), read
  descriptively beside the new arms' curves.
- **The secondary outcomes,** as in E3b-2: the later-leg rate, the unvisited and round-trip shares.

**The power analysis** comes before the pre-registration. It covers the two-sample contrasts, including
mixtures of successful and failed runs from the pilot's distributions.

## 7. The cost ledger (descriptive)

| Line | GPU-hours | What it bought |
|---|---|---|
| E4s-0 | 0.23 | L1's calibration and diagnostics |
| E4s-1 | 16.6 | L1's confirmatory validation |
| E3a | 5.97 | the selector, E and its gates |
| E3b-0 | 2.62 | W2, the maze-ready additions and the task |
| E3b-1's T-F | 6.44 | P-joint's tuning |
| E3c's new arms | measured | S-mod, S-dense, P-sel |

**How it is kept:**
- **The categories, separately:** measured artifact production and selection; shared infrastructure; the
  downstream adaptation and validation; and unmeasured design and review effort. No hours are invented for the
  last.
- **P-joint's first-use cost** is given as a range: from 6.7 hours (T-F plus E4s-0) to 31.9 hours (the full
  lineage, T-F included). v2's "32 hours plus the reused arm" double-counted T-F (both).
- **Common costs:** S-mod inherits E's mask, and every arm inherits W2 and the interface. These costs are
  common and noted as such.
- **E3c's incremental cost** is reported apart from the historical first-use cost.
- **The reuse cost** is the library cost paid once plus each downstream adaptation (P-sel here). It is shown
  as scenarios, not as a measured saving.

## 8. Compute (the ceiling is 30 GPU-hours)

From E3b-1's measured rates. T-F's batch, 8 runs at 300 × 8, took 6.44 h. R's batch, 2 runs at 16 mazes,
took 42.7 s a generation.

| Part | GPU-hours |
|---|---|
| Pilot (exploratory) | about 2.5 |
| `project`, `g-e` | about 1.5 |
| S-mod, S-dense (8 × 300 × 8 each) | 2 × 6.44 = 12.9 |
| P-sel (4 × 300 × 8) | about 3.8 |
| P-joint's reselection (8 × 32 × 128 validation mazes) | about 0.3 |
| Champions (20 runs × 32 × 128) | about 0.8 |
| Evaluation (6 arms and W2 alone, on 256 test mazes; the secondary conditions) | about 1.2 |
| **Total** | **about 23.0**; 27.2 with × 1.25 on training |

**The cuts, in order, if the benchmark exceeds the ceiling:**
1. the evaluation's secondary conditions;
2. P-sel to 2 runs;
3. S-dense and S-mod to 6 runs each.

The primary contrasts are kept whole as long as possible.

## 9. What would follow

E4 follows E3c and builds on its organisms. A null result on Q1 is published as such.

## 10. Decisions still open for the reviewers

1. **P-sel's start:** a random selector on frozen intact modules, the roadmap's "evolved selector". The
   alternative is selector tuning from the intact E (Astra's alternative).
2. **The neuron-matched dense control** (171 scalars), against a parameter-matched mask distribution.
3. **The pilot's criterion** (+1 visit by generation 100) and its branches.
4. **The tests:** two-sided Welch with Holm over Q1 and Q2; the cost curve with Fisher's exact test.
5. **The cuts' order.**

## 11. Changes from v1 (the reviews, D199)

| Point | From | Change |
|---|---|---|
| At factor 0.25 a start near 0 cannot reach working values in the schedule; the pilot could not detect it | Fable | Factor 1.0 for the arms starting from random values, stated as a recipe difference |
| The schedule | both | T-F's 300 × 8; the T-F cohort reused |
| Reuse of P-joint | both | Hashes checked; revalidated on E3c's block under the same rule (Astra); `g-e` reruns E3b-1's legs (Fable); the genomes stay local (rule 1) |
| Q2 is not "pretrained modules" | Astra | Renamed "engineered-initialization advantage"; its outcome expected and stated |
| The random 65-edge subset | both | B-task's full mask, neuron-matched; the confound stated |
| The starting draws were unspecified | both | §4: E3a's samplers, one rule for both S arms |
| P-sel's degraded start kept an engineered latch | Astra; Fable would keep it | **Ruling:** a random selector on frozen intact modules, the roadmap's arm 3 |
| The floor is not zero; the pilot was too short | both | W2 alone; 100 generations at factor 1.0; the branches, with the open-arena fallback fixed now |
| The tests | both | Two-sided Welch, Holm, labels, a margin, the floor guard; the cost curve as a secondary reading |
| The cost ledger | both | The lineage table, by category; reuse as scenarios |
| The relays' inputs were called goal signals | Astra | Source-occupancy levels |
| D144's goal-bit baseline | both | Not run; R-shared as an engineered reference |
| Learning curves on different blocks | both | One block for the new arms; P-joint's two points descriptive |
| The power analysis | Astra | Before the pre-registration, with mixtures of failed runs |
| Commit P-joint's genomes | Fable | **Not taken:** rule 1, D104 |

## 12. Changes from v2 (the second review, D200)

| Point | From | Change |
|---|---|---|
| B-task's draw keeps L1's antisymmetric and push-pull patterns; "without E's engineered signs" was wrong | both | §4 restated; S-mod is the full draw projected onto E's mask |
| `ga_draw` clips every bias to ±2 | Astra | Stated |
| The pilot costs about 2.5 h, not 1.5 | both | §5, §8 |
| An incomplete pilot is inconclusive; W2 and P-fixed are measured on the pilot's block | Astra | §5 |
| Only the factor may change after the pilot; the block is 128 mazes | Fable | §5 |
| "Cannot reach" → "unlikely to reach"; Q2 also compares mutation recipes | Astra | §3, §1 |
| "S-mod ≥ S-dense" is not an inference | Astra | §3 reads Q1 by §6's test |
| R-shared has 9 controller neurons; P-sel's 13 include the comparator biases | Astra | §3, §4 |
| The engine reference is T-F's commit (f881308), not T-A's | both | §3 |
| The ledger range double-counted T-F | both | 6.7 to 31.9 h |
| The floor guard's mean; the margin set by relevance; the threshold tests' multiplicity, censoring and medians | both | §6 |
| D199's reason for keeping the genomes local was wrong: the cohort's worm-block weights are all zero | Astra | D200 corrects it; the champions' grafted parameters are published by name |
