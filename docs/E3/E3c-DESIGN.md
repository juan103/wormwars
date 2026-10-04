# E3c design: the assembly comparison — v1 (draft, for review)

**Status:** draft v1, 2026-10-04. Nothing has run.
- **Who decided:** the owner chose E3c after E3b-2, with a ceiling of 30 GPU-hours (D198).
- **The review:** both reviewers (Astra 6, Fable 5.1) review this design before a pre-registration is
  written.
- **The questions to settle:** §9 lists the decisions this draft makes and wants attacked.

## 1. The question

ROADMAP §E3: "after the minimal organism works, the assembly comparison". It names four arms:
1. one task-conditioned controller of matched size;
2. pretrained modules with a fixed selector;
3. the same modules with an evolved selector;
4. a modular organism of the same size trained from scratch.

The roadmap asks for the first-use cost (pretraining included) and for the cumulative cost as later organisms
reuse the modules. It notes: "one loss on first use does not settle the value of modularity."

**E3c asks two things, in the maze shuttle where E3b-1 passed its gate:**
- **Q1, structure:** at equal training effort from random weights, does the modular structure (E's mask: two
  comparator modules, relays and a latch) beat a dense controller of matched size and trainable capacity?
- **Q2, reuse:** at equal training effort, do pretrained modules beat the same modular organism trained from
  scratch? And what do the modules' pretraining and later reuse cost?

**The frame, as in E3b:**
- the organisms are hand-built or grafted circuits on a silent worm, so nothing here is about worm behaviour;
- stereo sensing and the maze-ready additions (the W2 reflex, the relays' visit input) are game-design
  choices, common to every arm.

**What we know already:**
- **E3a's B-task** (the open arena) found a dense controller of the same 11 neurons, trained from scratch,
  worse than joint tuning (−3.73 visits). It was not matched in trainable capacity, and it says nothing about
  mazes.
- **E3b-1** gives a joint-tuned arm at a known cost.
- **E3b-2** shows the tuned organisms use the selector.

## 2. The task (fixed by E3b-1)

E3b-1's maze shuttle, unchanged:
- c = 5, H = 2 400;
- colonies of 8 on up to 4 spawns;
- shared trails (μ 0.01, λ 0.02, δ 0.05, d₀ 1.142);
- maze run seed 1 180 000, with Amendment 1's redraw rule;
- the W2 reflex frozen in every arm;
- E2's GA (population 32, elites 3, truncation 8), unshaped fitness (visits per wey).

The test, validation and training blocks are new and disjoint from every earlier block.

## 3. The arms

Every arm has the same 11 grafted neurons in the same input and output positions (the noses, the relays' visit
inputs, the turn neurons), plus W2's 2 frozen neurons. The arms differ in their mask, their start and what
mutates.

| Arm | Mask | Start | What is trained in E3c | Its roadmap arm |
|---|---|---|---|---|
| **P-fixed** | E | the seed E + W2 (E4s-0's L1 copies, the engineered latch) | nothing | 2 |
| **P-sel** | E | E's modules, ungated: E3b-1's degraded start (gate weights and comparator biases at 0) | the selector only: the gating and latch groups (E3b-2 §4: 13 scalars); the modules frozen | 3 |
| **P-joint** | E | the seed | everything mutable (65 scalars). **E3b-1's T-A champions, reused** | (joint tuning) |
| **S-mod** | E | random weights on E's mask | everything mutable (65 scalars) | 4 |
| **S-dense** | dense among the 11, matched in trainable scalars (§4) | random weights | everything mutable (≈ 65 scalars) | 1 |

**Reuse:** P-joint reuses E3b-1's 8 T-A champions instead of retraining.
- **Their schedule:** 125 generations × 16 mazes per genome, from the seed, under E3b-1's code. Their
  training compute is recorded: 5.12 GPU-hours.
- **The other trained arms get exactly that schedule,** so every trained arm has equal training effort.
- **What reuse saves:** about 5 GPU-hours.
- **The cost:** P-joint's champions were chosen on E3b-1's validation block. E3c's other arms choose on
  E3c's. Both are disjoint from E3c's test block.

## 4. The matched dense controller (S-dense)

**The criticism of E3a's B-task:** matching neurons is not matching capacity.

**The proposal:** S-dense has the same 11 neurons and the same input and output positions as E.
- **Its mutable edges:** chosen to equal E's 65 mutable scalars as nearly as possible. They form a dense
  random subset of the possible edges among the 11 neurons and from the comparator-position neurons to the
  turn neurons. The subset is drawn once, with a registered seed.
- **Its τ and biases:** the same as E's.
- **Its relays** still read the visit levels. Every arm then has the same task conditioning: a goal signal
  derived from visits, which the controller must hold itself. The relays are game-design inputs.
- **The alternative,** for review: a dense controller with an explicit persistent goal input, as the
  roadmap's D144 baseline ("one shared navigator plus a persistent goal bit"). It is easier for the
  controller but not matched in inputs.

## 5. The readings (to be registered)

Every reading is on a new test block (256 mazes), against the frozen seed (P-fixed), with shared trails. Its
unit is d, as in E3b-1: (champion − seed) / the seed's mean.
- **Q1 (structure):** S-mod against S-dense at equal training effort. A two-sample comparison over 8 runs
  each. The labels and test are to be fixed in the pre-registration.
- **Q2 (reuse):** P-joint (pretrained, then tuned) against S-mod (from scratch), at equal training effort.
- **Descriptive:**
  - P-sel against P-joint and P-fixed: does evolving only the selector recover the seed's level, or exceed
    it?
  - Every arm's learning curve against the cumulative training compute.
- **The cost accounting (descriptive):**
  - the first-use cost of each arm: its training compute plus the compute that produced its starting
    modules;
  - the cumulative cost when the modules are reused for a second organism, here the selector-only arm.

  E4s-0's L1 was hand-built and calibrated with diagnostics, not evolved, so its "pretraining compute" is
  E4s-0's recorded GPU-hours. They are a design cost, stated as such.

## 6. Feasibility: a pilot first (exploratory)

From random weights, a maze colony may score at the floor for a long time. If S-mod and S-dense both stay
near zero, Q1 is degenerate ("both fail").
- **Before the pre-registration:** a short exploratory pilot (under 1 GPU-hour), on pilot blocks.
  - **The organisms:** random S-mod and S-dense genomes at generation 0.
  - **The training:** 2 runs per arm for 25 generations.
  - **What it measures:** the distribution of visits and the early learning curves.
- **If both are at the floor:** the design is revised before registration, for example with a shaped
  fitness, an easier maze, or more generations.

## 7. Compute (the ceiling is 30 GPU-hours)

From E3b-1's measured rates (T-A's batch: 8 runs × 32 × 16 mazes, 143.5 s a generation, 5.12 h for 125
generations with checkpoints):

| Part | GPU-hours |
|---|---|
| Pilot (exploratory) | ≤ 1.0 |
| `project`, `g-e` | about 1.5 |
| P-sel, S-mod, S-dense training (8 × 125 × 16 each) | 3 × 5.1 = 15.4 |
| Champions (3 arms × 8 runs × 32 × 128 validation mazes) | about 0.9 |
| Evaluation (5 arms + the seed on 256 test mazes; plus none and own conditions for the descriptive readings) | about 1.0 |
| **Total** | **about 19.8**; 23.7 with × 1.25 on training |

**If generations must grow:** 300 generations at 8 mazes (T-F's schedule) per arm would cost about 6.4 h
each. But equal effort with P-joint then needs T-F's champions as the pretrained arm instead (§9).

## 8. What would follow

- **E4** follows E3c: do the two minds share? Its design will build on E3c's organisms.
- **A null on Q1** (modular no better than dense at equal effort) would be published as such. One loss on
  first use does not settle modularity, so the reuse cost is reported alongside.

## 9. Decisions for the reviewers to attack

1. **The task:** E3b-1's mazes, against E3a's open shuttle (about 30× cheaper a world, so more runs and
   generations are possible). The mazes are where the gate passed.
2. **Reusing E3b-1's T-A champions as P-joint,** at a known matched schedule, against retraining them in E3c.
3. **The matched controller:** matched in trainable scalars (≈ 65) and in inputs, with the relays as the
   goal conditioning. The alternative is an explicit goal bit.
4. **P-sel's start:** E3b-1's degraded start, the ungated modules. E3a's S2 started near-ungated and found a
   working selector in 1 of 8 runs.
5. **Equal training effort** as the matching unit, against equal compute including evaluation.
6. **The schedule:** 125 × 16 (matching T-A), against 300 × 8 (matching T-F, which gained more), within 30 h.
7. **The cost accounting** for hand-built modules: E4s-0's recorded GPU-hours as the pretraining cost.
8. **The pilot's floor criterion,** and what changes if it is not met.
9. **The registered tests:** Q1 and Q2 as two-sample comparisons over runs, with how many runs and which
   labels.
