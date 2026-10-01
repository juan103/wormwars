# E4s-0: diagnostics before the comparator graft (plan v2, 2026-10-01)

Status: v2, for review by Astra 6 and Fable 5.1 together with the script, before any formal run.
- **v1** (21d84b2): both reviewers said "revise" (`docs/reviews/20261001-E4s-0-plan/`).
- **v2** takes every must-fix and most suggestions; the map is the last section.
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
    95% (2.5th and 97.5th percentiles), 10 000 resamples, **seed 0, E2d's registered seed** (v1
    said 20 261 001, which contradicted "unchanged"; both reviewers). A test checks the imported
    settings;
  - E2d's `classify` for "uses" (both lower bounds above 0.5), "no material benefit" (both intervals
    inside (−0.25, 0.25)) and "unclear".

  These are imported from `scripts/e2d.py` unchanged. E2d loads its own copy of E2's stage frame, and
  E4s-0 loads another, configured for its own folder. A test checks that E4s-0's records, compute
  file and cap clock use `experiments/E4s-stereo-module/E4s-0/` (Fable).
- **The 47 distinct champions:** E2's and 04a's, deduplicated by genome hash, as `e4s_gain_probe.py`
  does.
- **Device and exactness:**
  - CUDA, inside the registration guards; each record holds its batch composition;
  - nothing is claimed across compositions;
  - single-genome evaluations use `pad_single_strain`, as in E2d.
- **Compute:** counted through `wormwars.accounting`. The stage frame is E2's (markers, the cap
  clock, not-completed records, retried atomic writes), reused as E2d reuses it.
- **World ids**, new and disjoint from E1, 04a, E2 and E2d, and from 03's timing ids (a test checks).
  v2 first placed them at 990 million, which 03's timing ids occupy (D-entry of the E2 code review;
  E2's and E2d's disjointness tests list it). Neither review caught it, since those ids are not
  written as literals in the code; the script's test did. 970 million is 02's gate ids, so they are moved
  to 940 million, where no range starts (D145):

  | Use | Ids |
  |---|---|
  | 1. the residual sweep | 940 000 000 + 512 |
  | 3. tuning, step s (s = 0..4 for L1, L2, L3, L4×2, L4×4) | 940 100 000 + 20 000·s + 128, re-scored on 940 101 000 + 20 000·s + 512 |
  | 3. qualification, step s | 940 300 000 + 10 000·s + 1 024 |
  | 3. step response and reversal | none (open loop) |
  | 3. simulated populations: selection | population i: 940 500 000 + 8·i + 0..7 |
  | 3. simulated populations: G0 bests' D | 940 510 000 + 1 024 |
  | 3. individual backgrounds | 940 520 000 + 64 |
  | 3. 04a run 2 grafted | 940 540 000 + 1 024 |
  | 4. robustness | 940 560 000 + 64 |
  | smoke and projection | 0-9 999 (reused on purpose; exempt from the disjointness test) |

- **Seeds:**
  - simulated populations: run seeds 1 150 000 + i (i < 16), drawn with 04a's
    `initial_population` on N2's spec, then embedded;
  - robustness mutations: mutant j (j < 256) uses a generator seeded 1 151 000 + j, at every scale. So
    the three scales share their draws, paired, as `e2d.children` does;
  - E4s-1 reserves 1 160 000 onwards.

## 1. The residual stereo-gain sweep

- **The residual:** the script wraps the world's motor read-out. The champion's turn command,
  0.5 × `turn_gain` × (mean tanh dorsal − mean tanh ventral), gets k·(L − R) added before the clamp
  to [−1, 1].
  - L and R are the world's `food_left` and `food_right` signals of the same tick (`last_signals`).
    These are the scaled values the interface injects at gain 1, which is what E1's S-const reads.
  - Turn > 0 is a left turn.
  - This is done in the script, not in the engine.
- **The check, before anything is recorded:**
  - with k = 0, every champion's per-world counts equal the unwrapped world's exactly on the sweep
    worlds;
  - **the composition is fixed:** the unwrapped reference and every k use one chunking, 8 strains ×
    512 worlds per chunk (the last chunk holds 7 strains). Each champion's composition is therefore
    identical across k and the reference (rule 6; both reviewers);
  - a CPU test checks the same.
- **The grid:** k ∈ {0, 0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 256}; 47 champions × 13 k × 512
  worlds, paired.
- **The classes,** per champion, on the paired difference from k = 0. These are the proposal's
  definitions, restated in full (Fable):
  - **"improves at k"**, for k < 256: the 95% lower bounds at k and at the next larger k are both
    above 0;
  - **"is harmed at k"**, for k < 256: both upper bounds are below 0;
  - **k = 256 alone does not make a class** (Astra). Its interval is reported, descriptive;
  - **k\*:** the first improving k;
  - **the classes, exhaustive and exclusive:**
    - **rises early:** k\* exists, k\* ≤ 1, and no k below k\* is harmed;
    - **rises late:** k\* exists, k\* > 1, and no k below k\* is harmed;
    - **dips first:** k\* exists, and some k below k\* is harmed;
    - **harmed:** no k\*, and some k is harmed;
    - **no detected benefit on the tested grid:** no k\*, and no k harmed.

    v1's "unclear" could never occur under these definitions, so it is dropped.
  - **A flag, beside the class:** "harmed at a larger k" (some k above k\* is harmed).
  - **A unit test** checks the classifier on synthetic intervals, the k = 256 edge included.
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

### L4's base, and when nothing qualifies

- **L4's base:** L1's, L2's and L3's qualification candidates are re-scored on one common set, L4's
  first 512 re-score worlds, paired (Fable).
  - The best mean wins; ties go to the lower step.
  - Its recurrent coefficient (w_s or w_m) stays fixed while L4 retunes the rest (Astra).
- **If no step qualifies:**
  - items 3.1-3.5 are skipped, and the 12-of-16 reading is recorded as "not drawn";
  - item 4 runs on the candidate with the highest qualification mean among the attempted steps,
    labelled as not qualified. These are unpaired means on different worlds, and that is noted. It is
    the closest to qualifying, which is why it is preferred to L1.

### For the qualifying comparator

1. **Its open-loop dynamics on the carrier,** at c = 0 and m ∈ {0.02, 0.08, 0.25}:
   - **the conditions:**
     - each test first runs 60 ticks of preconditioning at its starting input;
     - it is then read for up to 400 ticks after the change, against a control that does not
       change;
   - **the measures:**
     - the step response from d = 0 to d = +0.01;
     - the carried-state reversal from +0.01 to −0.01;
   - **settled:** when the mean change from the control over the last 20 ticks differs by less than
     1% from the mean over the 20 before. If it never does, the response is flagged "not settled"
     (both reviewers: at w_s = 0.95 and τ = 2 the time constant is about 40 ticks or more);
   - **the response time:** the first tick at which the absolute change from the control reaches 90%
     of its settled value;
   - **edge cases:**
     - a change below 10⁻⁴ is flagged "negligible", with no time;
     - a reversal that ends with the wrong sign is flagged.
2. **The simulated generation-0 populations** (the statistic E4s-1 uses):
   - 16 populations of 32 random N2 genomes, each with the comparator grafted;
   - each population's G0 best is picked by Task N fitness (unshaped mean count) on 8 selection
     worlds, as `evolve_batch` picks generation 0's best (ties to the lowest index);
   - each G0 best is classified for D (E2d's classes under the module probes) on **1 024 worlds**,
     as E4s-1's hold-out will be (both reviewers);
   - the counts of D, "unclear" and "no material benefit" are reported separately;
   - **a toy-size CPU test:**
     - the simulated G0 best is the genome `evolve_batch` logs as generation 0's `best_sha256`, given
       the same population through its `initial` hook and the same selection worlds;
     - a constructed test checks ties (the lowest index wins), population boundaries, and that
       selection reads the selection worlds, not the diagnostic ones (Astra).
3. **The individual backgrounds** (descriptive): all 512 genomes of those populations, on 64 worlds
   each. On 64 worlds, D will mostly be "unclear"; it is labelled so (Fable). Measured:
   - the score;
   - D;
   - the forward command and the turn command, and the share of saturated turn neurons
     (|tanh| > 0.99), each the mean over the episode's ticks.
4. **04a run 2 with the comparator grafted,** on 1 024 worlds: the score, D, and the same motor
   measures.
5. **The module file:** every neuron, edge, weight, τ and bias, plus the carrier's f and c. It is
   written to `experiments/E4s-stereo-module/E4s-0/module.json`, with its sha256 in the record. It is
   committed and pushed before E4s-1's pre-registration.

**The readings, as the proposal fixed them, with Astra's correction:**
- If fewer than 12 of the 16 simulated G0 bests are D, E4s-1's design must change its background,
  its reading, or both.
- Otherwise E4s-1 proceeds on random N2.
- **This is a design trigger, not a prediction.**
  - The proposal (v2.1) said a "retained" majority would then be "out of reach by construction".
    That holds only for the same 16 runs' own G0 classifications.
  - 16 pilot populations are neither necessary nor sufficient for 12 retained outcomes in E4s-1's
    future runs.
  - A dated note corrects the proposal (D145).

## 4. Mutational robustness

- The qualifying comparator, on its carrier, is mutated in its module parameters only. The worm's
  are pinned at scale 0, and the carrier's biases too.
- 256 mutants at each of 0.125×, 0.25× and 1× 02's scales, through `Genome.mutate`'s scales.
  Mutant j uses seed 1 151 000 + j at every scale, so the scales are paired.
- **Module parameters** are the module's neurons' τ and bias, and every edge with a module neuron at
  either end, the outputs onto the turn neurons included.
- **A test checks ownership:**
  - every mutant's worm block (weights, conductances, τ, biases, the carrier's biases included) is
    bit-identical to the parent's;
  - its module parameters, the graft-to-host weights included, differ (both reviewers).
- 64 robustness worlds.
- **Recorded:** each child's score, and the median child's score as a share of the parent's on the
  same worlds.
- **The fallback reading for E4s-1:** if the median child at 0.25× keeps less than half its parent's
  score, and at 0.125× keeps at least half, E4s-1's module factor is 0.125×.

## Budget, smoke and projection

- **Episodes:**
  - item 1: 313 k, plus the unwrapped reference, 24 k (Astra);
  - item 3:
    - at most 1 944 candidates × 128, plus re-scores, about 0.26 M;
    - L4's common re-score, 2 k;
    - simulated populations and backgrounds about 0.15 M (the G0 bests now on 1 024 worlds);
    - 04a run 2 and qualifications about 0.02 M;
  - item 4: about 0.05 M.

  About 0.82 M in total.
- **The projection stage** (Fable, Astra; as E2d's `project`):
  - it times one chunk of each formal composition on smoke ids, the instrumentation included:

    | Shape | Composition |
    |---|---|
    | sweep | 8 strains × 512 |
    | tuning | 32 strains × 128 |
    | re-score | 5 × 512 |
    | qualification | 1 padded strain × 1 024 |
    | population selection | 512 × 8, own ids per row |
    | G0 bests | 4 × 1 024 |
    | backgrounds | 64 × 64 |
    | robustness | 64 × 64 |
  - it projects the formal work from those rates.
- **Admission and the cap:**
  - each stage starts only if the GPU-hours already spent plus the projected remaining work stay
    within 1.8 h;
  - the projection stage and the unwrapped reference count against the 2-hour cap.
- **If the projection exceeds 1.8 h,** the sizes shrink in a pre-stated order before anything formal
  runs:
  1. the backgrounds' worlds 64 → 32 (descriptive; Astra);
  2. the tuning worlds 128 → 64 (a screen with a re-score behind it; Fable);
  3. the sweep worlds 512 → 256 (the only interval-based classes, so shrunk last).

  The chosen sizes are frozen in the projection record before any formal measurement. If even the
  smallest sizes exceed 1.8 h, E4s-0 stops for a new plan.
- **The cap clock** stops a stage when 2 GPU-hours are reached; the stage leaves a not-completed
  record.
- **Per-world counts** are committed with every summary (Astra).

## Tests, before any formal run (each seen failing first; sabotage where a check could not fail)

1. The formal world-id ranges are disjoint from each other and from E1's, 04a's, E2's and E2d's.
2. **The residual wrapper:**
   - with k = 0 it reproduces whole episodes exactly (CPU);
   - **the residual goes in before the clamp:** a raw turn of 1.5 plus a residual of −0.75 gives
     0.75, not 0.25 (Astra, Fable);
   - k > 0 with L > R raises the turn (the sign);
   - forward and pump are unchanged;
   - the patch is removed after its block, even after an error.
3. L1's wiring has the 20 edges with the signs above. A source on the left produces a left turn
   command, on the carrier, open loop.
4. The carrier's forward and turn commands equal f and c, within 10⁻⁶ after settling.
5. The module probes change only the noses' currents.
6. The simulated populations' worm blocks equal `initial_population`'s draws exactly.
7. L4×P builds 2 + 2P neurons with P copies of the base's edges.
8. The ladder stops at the first qualifying step, and each step reads its own worlds.
9. The sweep's classifier, on synthetic intervals.
10. The simulated G0 best matches `evolve_batch`'s generation 0, with ties, boundaries and the
    selection worlds.
11. Robustness mutates only the module.
12. E4s-0's stage frame writes to its own folder and compute file, and the imported analysis
    settings are E2d's.

## What E4s-0 cannot show

- What mutations would do: the sweep inserts a policy change from outside.
- Whether the comparator survives evolution: that is E4s-1.
- Anything about the worm's own chemotaxis: the stereo sensing is a game-design choice.

## Changes from v1

| v1 review item | v2 |
|---|---|
| The wrapper's tests miss "before the clamp", the sign and removal (Fable 1, Astra 1) | Tests for 1.5 − 0.75 → 0.75, for the sign, for forward and pump unchanged, and for removal after an error |
| The k = 0 composition (Fable 2, Astra 1) | One chunking for the reference and every k, 8 × 512 |
| The bootstrap seed contradicts the code (both) | Seed 0, E2d's, imported and tested |
| Incomplete classes; "unclear" unreachable; the k = 256 bypass (Fable 4, Astra) | The full definitions; "unclear" dropped; k = 256 descriptive; a "harmed at a larger k" flag; a classifier unit test |
| The simulated statistic: untested against `evolve_batch`; 256 worlds (Fable 5, Astra 3) | 1 024 worlds; D, unclear and no-benefit reported separately; a test against `evolve_batch`'s generation 0 with ties, boundaries and selection worlds |
| "Out of reach by construction" (Astra 3) | A design trigger, not a prediction; the proposal gets a dated note (D145) |
| The smoke cannot project (Fable 6, Astra 5) | A projection stage timing each formal composition; admission on spent plus projected; the reference and the projection count; the shrink frozen first |
| Robustness ownership and seeds (Fable 7, Astra 6) | A per-mutant seed shared across scales; an ownership test including graft-to-host weights |
| "Settled" at 40 ticks (both) | 60 ticks of preconditioning, up to 400 ticks, a declared convergence rule and flags |
| The shrink order (both suggestions) | Backgrounds first, then tuning, the sweep last |
| L4's base on different worlds; its coefficient while retuning (Fable, Astra) | A common paired re-score; ties to the lower step; the coefficient fixed |
| No step qualifies (Fable) | Items 3.1-3.5 skipped and the reading "not drawn"; item 4 on the closest candidate, labelled |
| Explicit selection ids; smoke ids; the stage frame's folder; per-world counts (both) | All pinned |
| Not taken: dropping comparator bias −0.5 from the grid (Fable: harmless, half of L1's grid) | Kept, since the grid is cheap; it can only lower L1's gain, and that is noted |
