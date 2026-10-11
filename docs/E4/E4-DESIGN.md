# E4 / 04c: do the two minds share? (design v1, for review)

**Status:** draft v1, for review by both reviewers. No GPU is used until the owner says so (the owner,
2026-10-11).
- **Planned process:** design, reviews, a pre-registration for the confirmatory readings, code test-first, an
  exploratory pilot sized by a power analysis, the formal run, results.
- **The ceiling:** 30 GPU-hours (D198).

**The question** (`ROADMAP.md`, "E4 / 04c"). Three separate questions, from easiest to hardest:
1. **Shared dependence:** does the same circuitry support both behaviours?
2. **Useful transfer** (the primary question): does information crossing between the two modules improve
   behaviour?
3. **Consolidation:** can the organism keep both abilities with less circuitry? This needs a mechanism that lets
   evolution silence circuitry with a cost that differs between candidates. There is none, so it is **deferred to
   stage 09**, as the roadmap allows.

**The frame:** a hand-built circuit on a silent worm. Nothing here is about worm behaviour.

## 1. The task and the organism

**The task:** E3f's validated family (`experiments/E3-ab-organism/E3f/`).
- **The mazes:** 6 × 6 carved island mazes, k_r = 0;
- **the run:** H = 1 800 ticks, colonies of 8, shared trails (μ 0.01, λ 0.02, δ 0.05, d₀ 1.142);
- **the score:** visits per wey.
- **The blind references are re-played on E4's own mazes** as a precondition (§4), not quoted from E3f (D237).

**The organism:** E3a's engineered E with E3b-0's W2 wall reflex (`wormwars/e3/organism.py`,
`maze_organisms.py`):
- two renamed copies of E4s-0's L1 comparator, module A (noses on A's channel) and module B (noses on B's);
- two relays (`at_a`, `at_b`);
- the latch E3_Q, gating the comparators by saturation: their biases at −1.914, Q → A at +2, Q → B at −2.

**What links the two modules today:** only the latch (Q drives both) and the world (behaviour, trails). On the
carrier the worm's own network is silent, and the motor neurons do not feed back. So **cross-links**, edges
between A's neurons and B's, are new.

**Module isolation** (Astra, D237): the inactive module is suppressed by saturation, not disconnected; its motor
edges stay live. Two uses need it, and they need different things.
- **The primary question (§2) does not need exact isolation.** Both arms share the same gating, and the contrast
  is cross-links present against absent.
- **Shared dependence (§3) needs it** to read "an A-neuron whose deletion hurts B mode acts through the
  cross-links".
  - **The proposal:** an evaluation-only **mode clamp**. During a probe, the inactive module's neurons are held at
    the gated state they take with no input, from the moment the latch switches.
  - **Its properties:** an intervention on states, not an engine change to rollouts, so rule 7 is not engaged
    for training.
  - **The alternative:** an engine change, output edges multiplied by a mode indicator. It is an open question in
    §8.

## 2. The primary question: useful transfer

**The arms** (both start from the seed E + W2 and tune on E3b-1's T-F mask: every chemical edge with a grafted
end, every grafted neuron's τ and bias; the relays, W2, the worm block and the gap junctions stay frozen):
- **X0 (cross-links impossible):** the T-F mask.
- **X+ (cross-links possible):** the same mask plus every directed edge between a neuron of A and a neuron of B,
  in both directions, initialised at 0 and mutable at the same mutation factor.
  - **What it adds:** with L1's comparator neurons and noses, this is on the order of 32-50 edges. The exact list
    will be fixed in code.
  - **Everything else matched:** the population, the elites, the generations, the training evaluations and the
    mazes. The only difference is the mutable cross-link set.

**Training:** E3c's GA frame (population 32, elites 3, truncation 8, mutation σ as E3c), with **G generations ×
W mazes per genome** sized by the pilot and the ceiling. Runs per arm: **R**, also sized by the pilot's power
analysis; E3c used 8. The training mazes, the validation block for champion selection, and a fresh test block
come from E3f's family under a new run seed.

**The readings** (confirmatory, to be pre-registered with E3c's statistics, `wormwars/e3/e3c_stats.py`):
- **T1, training:** the X+ champions' mean test score against X0's, over runs.
  - **The tests:** the exact permutation test at 0.025, Welch's interval, and E3c's dual margin, max(0.5, 0.10 × the
    X0 mean).
  - **The wording:** E3c's: "distributions differ (exact test); observed mean higher for X" and "approximate
    (model-based): …".
- **T2, acute, within X+ champions** (paired over champions and test mazes):
  - **cut** every cross-link, against **cutting the same number of within-module links**. The within-module links
    are chosen to match the cross-links' summed absolute weight, from a declared draw; several draws, averaged;
  - **scramble** the cross-links (permute their weights among the cross-link slots);
  - **sham:** cut zero links through the same code path.

  **The reading:** "cross-links carry useful information" only if cutting them costs more than the matched
  within-module cut, and scrambling costs more than the sham.
- **A failure mode stated in advance** (`ROADMAP.md`): if X+ evolves no useful transfer, check whether the latch or
  the module interfaces block transfer before concluding anything about evolution. The diagnostic task (§5) is
  that check.

**Eligibility, a precondition per arm** (D237: the blind references are a precondition, not an effect threshold):
- an arm's champions enter T1 only if their mean exceeds the best blind reference on E4's test block by E3c's dual
  margin;
- a champion is classified by E3c's registered nose rule (retained fraction with its noses removed);
- an arm whose champions are coverers reads "not evaluable: coverage".

## 3. Shared dependence (descriptive)

- **The lesions:** in each champion of both arms, delete each grafted neuron in each mode, under the mode clamp.
  Measure the visits in the other mode's legs.
- **The reading:** an A-neuron whose deletion hurts B-mode legs acts through the cross-links, X+ only. In X0 it
  must not, which makes X0 the check.
- **Pruning protocol** (D144, Fakhar & Hilgetag 2022):
  - importance recomputed after each removal;
  - several removal orders;
  - pairs tested;
  - acute results reported separately;
  - the claim limited to "the smallest circuit found under this procedure".

## 4. Controls and references (re-played on E4's mazes)

- **Blind:** the E3d blind family as E3f played it (wall-followers, W2, W2-turn, W2+M, the random walk grid, every
  champion with its noses removed).
- **Navigators:** the scripted follower (shared and trails off), the oracle.
- **The seed at generation 0,** the unevolved duplicate modules.
- **The selector removed:** `no_latch`.
- **Trails:**
  - every champion and the seed under shared trails, own trails only, and no trails;
  - the trails-off split for the seed and its champions, which E3f did not measure (D241).

  On this family the trails carry most of the scripted follower's advantage. So a cross-link effect must be read
  against trail-mediated transfer: information passing between modules through the world, not through the edges.
- **Per run, descriptively:** each run's gene-duplication fate (do A and B diverge?).

## 5. The diagnostic task: one module senses what the other needs

The roadmap asks for a task in which one module senses something the other needs, so that transfer is
**necessary**, not merely possible. A concrete proposal, to be judged in review:
- **The hazard:** hazard patches placed on corridors used by B-mode routes.
- **Who senses it:** a third nose channel reads the hazard field, and is wired only to module A.
- **The penalty:** hazard contact in B mode costs (for example, resets the wey's goal, or ends its current leg).
- **What it tests:** X0 cannot avoid hazards in B mode except by luck or by A's influence through the latch. X+
  can, if information crosses. The pre-registered reading: X+'s hazard-contact rate in B mode below X0's.
- **The cost:** the maze world zeroes the hazard channel today, so this needs engine work and an equivalence
  check (rule 7). It is a separate, smaller experiment (E4-D), run after T1 and T2 or instead of part of them.

## 6. Compute (estimates; no GPU until the owner says so)

| Item | Estimate |
|---|---|
| Pilot (exploratory: 2 arms × 3 runs × 100 generations, plus the probes) | 2-3 GPU-h |
| T1 training (2 arms × R runs × G generations; E3c's 3 arms × 8 runs at H = 2 400 took about 18 h) | 10-14 GPU-h |
| T2 probes, references, trails conditions, shared dependence | 2-3 GPU-h |
| E4-D (the diagnostic task), if run | 6-8 GPU-h |
| Total | 20-28 GPU-h, against 30 |

The pilot sizes R, G and W; E4-D may need a separate ceiling.

## 7. Prior results to compare against (as the roadmap lists; to be verified before citing)

- goals varying across modular subtasks (Kashtan and Alon, 2005);
- connection costs (Clune, Mouret and Lipson, 2013);
- duplicated modules specialising (Calabretta and colleagues, 2000).

They are cited from the roadmap; per the literature standard, they are checked before the pre-registration
relies on them.

## 8. Decisions open for the reviewers

1. **The mode clamp** (evaluation only) against an engine-level output gate, for §3. Is the clamp sound?
2. **The cross-link set:** every A↔B directed edge, or a declared subset (comparator to comparator only)?
   Initialised at 0, or small random values?
3. **T2's matched control:** matched by link count, by summed absolute weight, or both?
4. **The diagnostic task:** is the hazard design right, and should E4-D replace part of T1's budget or follow it?
5. **Trail-mediated transfer:** how to separate it from cross-link transfer beyond the trail conditions in §4.
6. **The arms' start:** both from the seed (as here), or also a from-scratch pair? E3c showed from-scratch arms
   become coverers in trees; on islands they may not.
7. **Anything missing** from the roadmap's E4 list: shared dependence, useful transfer, the diagnostic, the
   gene-duplication fate, the three controls, the pruning protocol.
