# E4s-0: diagnostics before the comparator graft (plan v1, 2026-10-01)

Status: v1, for review by Astra 6 and Fable 5.1 before any code runs.
- **Exploratory:** nothing here is confirmatory, and nothing here evolves.
- **What it implements:** E4s-0 of the adopted plan (`docs/E4s/ROADMAP-PROPOSAL.md` v2.1, D144). This
  file pins what the proposal left to the script.
- **The cap:** 2 GPU-hours.
- **Outputs:** in `experiments/E4s-stereo-module/E4s-0/`, committed.

## Common settings

- **Task N, exactly as E1 froze it,** checked against E1's gate record as E2 does. The world seed is
  1 100 001, E1's: with the world id, it generates each world and its targets.
- **The intervals:**
  - E2d's `world_ci`: a paired percentile bootstrap over worlds of the mean difference, two-sided
    95% (2.5th and 97.5th percentiles), 10 000 resamples, seed 20 261 001;
  - E2d's `classify` for "uses" (both lower bounds above 0.5), "no material benefit" (both intervals
    inside (−0.25, 0.25)) and "unclear".

  These are imported from `scripts/e2d.py` unchanged.
- **The 47 distinct champions:** E2's and 04a's, deduplicated by genome hash, as `e4s_gain_probe.py`
  does.
- **Device and exactness:**
  - CUDA, inside the registration guards; each record holds its batch composition;
  - nothing is claimed across compositions;
  - single-genome evaluations use `pad_single_strain`, as in E2d.
- **Compute:** counted through `wormwars.accounting`. The stage frame is E2's (markers, the cap
  clock, not-completed records, retried atomic writes), reused as E2d reuses it.
- **World ids**, new and disjoint from E1, 04a, E2 and E2d (a test checks):

  | Use | Ids |
  |---|---|
  | 1. the residual sweep | 990 000 000 + 512 |
  | 3. tuning, step s (s = 0..4 for L1, L2, L3, L4×2, L4×4) | 990 100 000 + 20 000·s + 128, re-scored on 990 101 000 + 20 000·s + 512 |
  | 3. qualification, step s | 990 300 000 + 10 000·s + 1 024 |
  | 3. step response and reversal | none (open loop) |
  | 3. simulated populations: selection | 990 500 000 + 8 per population (16 × 8) |
  | 3. simulated populations: G0 bests' D | 990 510 000 + 256 |
  | 3. individual backgrounds | 990 520 000 + 64 |
  | 3. 04a run 2 grafted | 990 540 000 + 1 024 |
  | 4. robustness | 990 560 000 + 64 |
  | smoke | 0-9 999 |

- **Seeds:**
  - simulated populations: run seeds 1 150 000 + i (i < 16), drawn with 04a's
    `initial_population` on N2's spec, then embedded;
  - robustness mutations: 1 151 000 + j;
  - E4s-1 reserves 1 160 000 onwards.

## 1. The residual stereo-gain sweep

- **The residual:** the script wraps the world's motor read-out. The champion's turn command,
  0.5 × `turn_gain` × (mean tanh dorsal − mean tanh ventral), gets k·(L − R) added before the clamp
  to [−1, 1].
  - L and R are the world's `food_left` and `food_right` signals of the same tick (`last_signals`).
    These are the scaled values the interface injects at gain 1, which is what E1's S-const reads.
  - Turn > 0 is a left turn.
  - This is done in the script, not in the engine.
- **The check, before anything is recorded:** with k = 0, every champion's per-world counts equal the
  unwrapped world's exactly on the sweep worlds. A test also checks this on the CPU.
- **The grid:** k ∈ {0, 0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 256}; 47 champions × 13 k × 512
  worlds, paired.
- **The classes,** per champion, on the paired difference from k = 0 (the proposal's adjacency rule):
  - "improves at k": the 95% lower bounds at k and at the next larger k are both above 0;
  - "is harmed at k": both upper bounds are below 0;
  - the classes: rises early (the first improving k is at most 1), rises late, dips first, harmed, no
    detected benefit on the tested grid, and unclear.

  At k = 256, the last grid point, "improves" or "is harmed" needs only its own bound, and that is
  flagged.
- **Recorded:** per champion and k, the mean, the interval and the class; the counts per class; and
  each champion's first improving k.

## 2. Where the response is attenuated (descriptive)

- **Open loop, as gain probe v3:** zero start, other inputs zero, 40 ticks, averaged over the last
  10.
- **The differential gain** K_D is a central difference in d (±0.001) at fixed m. **The common-mode
  gain** K_C is a central difference in m (±0.01) at fixed d = 0. The levels are m ∈ {0.02, 0.08,
  0.25}.
- **Read as tanh activity at:**
  - ASEL/R, AWAL/R and AWCL/R;
  - AIYL/R, AIZL/R, AIAL/R and AIBL/R;
  - RIAL/R;
  - SMDDL/R, SMDVL/R, RMDDL/R and RMDVL/R;
  - and the turn command.
- There is no decision rule.

## 3. The comparator ladder

### The circuit (every edge and value)

- **Neurons:**
  - noses E4S_NL and E4S_NR (τ 0.5, bias 0), fed `food_left` and `food_right` at interface gain 1;
  - comparators E4S_CL and E4S_CR (τ ∈ {0.5, 2}, bias ∈ {−0.5, 0}, both tuned, the same for both).
- **L1's 20 edges:**

  | From | To | Weight |
  |---|---|---|
  | NL | CL | +w_n |
  | NL | CR | −w_n |
  | NR | CR | +w_n |
  | NR | CL | −w_n |
  | CL | SMDDL, SMDDR, RMDDL, RMDDR | +w_o |
  | CL | SMDVL, SMDVR, RMDVL, RMDVR | −w_o |
  | CR | SMDDL, SMDDR, RMDDL, RMDDR | −w_o |
  | CR | SMDVL, SMDVR, RMDVL, RMDVR | +w_o |

- **L2:** L1 plus CL → CL and CR → CR, at w_s ∈ {0.5, 0.8, 0.95}.
- **L3:** L1 plus CL → CR and CR → CL, at w_m ∈ {−0.5, −0.8, −0.95}.
- **L4×P (P = 2, then 4):**
  - P comparator pairs E4S_CL_p and E4S_CR_p, each wired to the same two noses and the same eight
    turn neurons, as the base.
  - The base is whichever of L1, L2 and L3 had the best re-scored mean on its tuning worlds, with its
    own w_s or w_m.
  - It has 2 + 2P neurons (6, then 10).
- **The sign:** a stronger left nose excites CL, which raises the dorsal turn neurons and lowers the
  ventral ones, so the turn command rises. That is a left turn, toward the stronger side. A test checks
  the sign on the CPU before any GPU run: a wey with the source on its left turns left.

### The carrier

- **The worm's 302 neurons are silent:** weights, conductances and biases are 0, and every τ is 1.
- **Two exceptions:**
  - **The forward command f:** bias b_f = atanh(f/2) on AVBL/R and PVCL/R, since forward = 2·tanh(b_f).
  - **The turn command c:** bias b_t = atanh(c/2) on SMDDL/R and RMDDL/R, and −b_t on SMDVL/R and
    RMDVL/R, since turn = 2·tanh(b_t).
- **The genome** is built by `graft.seeded_genome` with no background, then given the carrier's
  biases through `with_params`.

### Tuning, qualification and stopping

- **The grid for each step:**
  - w_n and w_o ∈ {1, 2, 3};
  - comparator τ ∈ {0.5, 2} and bias ∈ {−0.5, 0};
  - f ∈ {0.5, 1} and c ∈ {0, 0.1, 0.2};
  - and the step's own parameter.

  That is 216 candidates for L1 and L4×P, and 648 for L2 and L3.
- **Tuning:**
  - every candidate on the step's 128 tuning worlds;
  - the best 5 by mean (ties to the first in grid order, the order of the grid's product as listed)
    re-scored on the step's 512 worlds;
  - the best re-scored mean (ties the same way) goes to qualification.
- **Qualification** on the step's own 1 024 worlds:
  - the mean's lower bound is at least 5.0. That is the 2.5th percentile of the bootstrap of the mean,
    by `world_ci` against zero;
  - **and** "uses" under the module probes: real against module mean, and real against module
    swapped (`graft.graft_interface`).
- **The order is L1, L2, L3, L4×2, L4×4.** Each step is tuned only if the previous one failed
  qualification. **The first step that qualifies stops the ladder.**
- If none qualifies, the record says "none of the tested candidates passed within the search budget".
  E4s-0 still runs items 1, 2 and 4 (item 4 then on L1's tuned candidate, labelled as not qualified).

### For the qualifying comparator

1. **Its open-loop dynamics on the carrier,** at c = 0 and m ∈ {0.02, 0.08, 0.25}. Each is read over
   40 ticks after the change, against a control that does not change:
   - the step response from d = 0 to d = +0.01;
   - the carried-state reversal from +0.01 to −0.01;
   - the response time: the first tick after the change at which the turn command reaches 90% of its
     settled change (the mean of the last 10 ticks).
2. **The simulated generation-0 populations** (the statistic E4s-1 uses):
   - 16 populations of 32 random N2 genomes, each with the comparator grafted;
   - each population's G0 best is picked by Task N fitness (unshaped mean count) on 8 selection
     worlds, as `evolve_batch` picks generation 0's best (ties to the lowest index);
   - each G0 best is classified for D (E2d's classes under the module probes) on 256 worlds.
3. **The individual backgrounds** (descriptive): all 512 genomes of those populations, on 64 worlds
   each:
   - the score;
   - D;
   - the forward command and the turn command, and the share of saturated turn neurons
     (|tanh| > 0.99), each the mean over the episode's ticks.
4. **04a run 2 with the comparator grafted,** on 1 024 worlds: the score, D, and the same motor
   measures.
5. **The module file:** every neuron, edge, weight, τ and bias, plus the carrier's f and c. It is
   written to `experiments/E4s-stereo-module/E4s-0/module.json`, with its sha256 in the record. It is
   committed and pushed before E4s-1's pre-registration.

**The readings, as the proposal fixed them:**
- If fewer than 12 of the 16 simulated G0 bests are D, E4s-1's design must change its background,
  its reading, or both.
- Otherwise E4s-1 proceeds on random N2.

## 4. Mutational robustness

- The qualifying comparator, on its carrier, is mutated in its module parameters only. The worm's
  are pinned at scale 0, and the carrier's biases too.
- 256 mutants at each of 0.125×, 0.25× and 1× 02's scales, through `Genome.mutate`'s scales, on
  seeds 1 151 000 + j.
- 64 robustness worlds.
- **Recorded:** each child's score, and the median child's score as a share of the parent's on the
  same worlds.
- **The fallback reading for E4s-1:** if the median child at 0.25× keeps less than half its parent's
  score, and at 0.125× keeps at least half, E4s-1's module factor is 0.125×.

## Budget, smoke and projection

- **Episodes:**
  - item 1, 313 k;
  - item 3: at most 1 944 candidates × 128, plus re-scores, about 0.26 M; populations and
    backgrounds about 0.11 M; 04a run 2 and qualifications about 0.02 M;
  - item 4, about 0.05 M;

  about 0.76 M in total.
- **The smoke:** every item at toy sizes (worlds 0-9 999; 2 champions, 2 values of k, 4 candidates,
  1 population). It times the shapes, and its rates project the formal run.
- **If the projection exceeds 1.8 h,** the sizes shrink in a pre-stated order before anything formal
  runs:
  1. sweep worlds 512 → 256;
  2. tuning worlds 128 → 64;
  3. backgrounds' worlds 64 → 32.

  If it still exceeds 1.8 h, E4s-0 stops for a new plan.
- **The cap clock** stops a stage when 2 GPU-hours are reached; the stage leaves a not-completed
  record.

## Tests, before any formal run (each seen failing first; sabotage where a check could not fail)

1. The world-id ranges are disjoint from each other and from E1's, 04a's, E2's and E2d's.
2. With k = 0, the residual wrapper reproduces the unwrapped counts exactly (CPU, 2 genomes, 8
   worlds). With k ≠ 0, it changes the turn.
3. L1's wiring has the 20 edges with the signs above. A source on the left produces a left turn
   command, on the carrier, open loop.
4. The carrier's forward and turn commands equal f and c, within 10⁻⁶ after settling.
5. The module probes change only the noses' currents.
6. The simulated populations' worm blocks equal `initial_population`'s draws exactly.
7. L4×P builds 2 + 2P neurons with P copies of the base's edges.
8. The ladder stops at the first qualifying step, and each step reads its own worlds.

## What E4s-0 cannot show

- What mutations would do: the sweep inserts a policy change from outside.
- Whether the comparator survives evolution: that is E4s-1.
- Anything about the worm's own chemotaxis: the stereo sensing is a game-design choice.
