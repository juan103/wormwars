# E3b-2 results: where E3b-1's gain comes from (exploratory, 2026-10-04)

**Draft, under review by both reviewers. Not yet published on main.**

**E3b-2 is exploratory.**
- **The plan:** `docs/E3/E3b-2-PLAN.md`, draft 3. Its analyses were fixed before the run, and reviewed by both
  reviewers at the plan, the code and a confirmation pass (D194-D196).
- **Every number is descriptive.** There is no gate and no verdict.
- **The source:** every number comes from `summary.json` and the per-maze chunks in this folder.
- **Units:** "of the seed's mean" means in units of the frozen seed's mean visits per wey with shared trails on
  the fresh block (5.71).

**The setting:**
- **Mazes:** 256 fresh mazes (7000-7255) that no organism had played.
- **Organisms:** E3b-1's 16 final T champions (T-A runs 0-7, T-F runs 0-7), N's 4 champions and the frozen
  seed E + W2.

**Compute:** 3.00 of the 5 GPU-hours capped (`compute-record.json`).
- `project`: 0.33, with no drop and no maze redrawn;
- attribution: 1.6;
- lesions: 1.01;
- latch: 0.06.

**The checks:**
- **The seed is bitwise identical** in every chunk where it appears in the same composition: A-shared, A-none
  and B.
- **The lesion stage's intact champions are bitwise identical** to the attribution's all-champion hybrids.
- **The resting turn computed from each genome** equals E3b-1's and E3b-0's probe records exactly.

## In brief

- **The gain replicates on fresh mazes.** The champions' gains here correlate 0.99 with their E3b-1 test-block
  d:

  | Schedule | Fresh mazes | E3b-1 test block |
  |---|---|---|
  | T-A | +0.114 | +0.069 |
  | T-F | +0.451 | +0.381 |

- **The engineered selector is in use.**
  - **Holding the latch fixed** at either of a champion's own states costs nearly all of its performance:
    - T-A: −0.95 and −0.97 of the seed's mean;
    - T-F: −1.25 and −1.26;
    - against −0.85 and −0.91 for the seed itself.
  - **In the maze,** every organism's latch switches after essentially every visit, in both directions,
    within 1-2 ticks, and matches the goal on 99.4-100% of decided ticks.
  - By the reading written into the plan before the run (§6), the tuned organisms still use dynamic
    selection. The premise of E3's assembly comparison and of E4 holds for them.
- **The gain sits in the comparators' co-tuned input weights and operating point.**
  - **The interaction:** the "sensing" group (the nose → comparator weights, the time constants) and the
    "gating" group (the comparator biases and the latch → comparator weights) work only together.
  - **The collapse:** the hybrids taking one from the champion and the other from the seed fall below W2
    alone (1.65 visits per wey):
    - in 15 of 16 champions, at least four of these eight hybrids fall below it (in one direction or both),
      and in 7 of them all eight do;
    - in the 16th (T-F run 4), none does, though its tuned sensing with the seed's gating still loses 0.51
      of the seed's mean;
    - no hybrid holding both or neither of the pair falls below W2 alone.
  - **The size:** their pair interaction is large: T-F +1.90 and T-A +1.44 of the seed's mean, against net
    gains of +0.45 and +0.11.
  - **The rest:** the output edges' and the latch parameters' Shapley allocations are small (≤ 0.04).
  - **E3b-1's probe finding, read again:** the tuned comparators fell short of the seed's design thresholds.
    These results suggest a moved operating point, not an abandoned comparator.
- **The noses matter to the T champions, not to N's.** With the A/B nose inputs removed (the trail and the
  path-distance scent together):
  - T-A loses 0.54 and T-F 0.71 of the seed's mean with shared trails;
  - N's champions, tuned without trails, lose nothing (+0.08).
- **T-F's added trail dependence is allocated to sensing (+0.20) and gating (+0.12),** as the difference of
  their allocations with shared trails and with none.
- **The tuned champions turn harder at rest:** their resting turn command is 0.65-1.00, against the seed's
  0.40.

## A. The functional attribution

The four parameter groups are defined in the plan, §4:
- **sensing:** the nose → comparator edges, the nose neurons' τ and bias, the comparators' τ;
- **gating:** the comparators' biases and the latch → comparator edges;
- **output:** the comparator → turn-neuron edges;
- **latch:** its self-edge, the relay → latch edges, and its τ and bias.

All 16 seed/champion hybrids of each champion were played.

**Schedule means** (shared trails; t interval over runs):

| | T-A gain | T-F gain |
|---|---|---|
| Net gain | +0.114 [+0.076, +0.153] | +0.451 [+0.328, +0.575] |

| Group | T-A Shapley | T-F Shapley | T-A reversion | T-F reversion | T-A transplant | T-F transplant |
|---|---|---|---|---|---|---|
| sensing | −0.121 [−0.362, +0.119] | +0.201 [+0.011, +0.391] | −0.562 | −1.180 | −0.822 | −0.777 |
| gating | +0.186 [−0.062, +0.434] | +0.230 [+0.068, +0.391] | −0.903 | −1.221 | −0.541 | −0.764 |
| output | +0.041 [+0.026, +0.056] | +0.012 [−0.021, +0.045] | −0.036 | −0.084 | +0.032 | −0.060 |
| latch | +0.008 [+0.001, +0.016] | +0.009 [+0.001, +0.017] | −0.005 | −0.019 | +0.018 | +0.020 |

**What the reversions and transplants show:**
- **Reversion** (the champion with one group set back to the seed's values) and **transplant** (the seed
  given that group's tuned values) are both large and negative for sensing and gating.
- **The cause:** a champion's tuned comparator inputs need its tuned comparator biases, and the seed's
  inputs need the seed's biases.
- **Off the evolutionary path:** the hybrids that mix the two are the 8 that hold one of the pair without
  the other. Below W2 alone (`hybrids_below_w2`), counting these eight per champion:
  - **shared trails:** at least four in 15 of 16 champions, all eight in 7, none in T-F run 4;
  - **trails off:** at least three in 15 of 16;
  - no other hybrid falls below W2 alone.
- **How to read the Shapley values:** they split the pair's large positive interaction between the two
  groups. They are exact for this table of hybrids, not the route evolution took (§9).

**The pair interaction** (the Harsanyi dividend of {sensing, gating}, mean per schedule):

| | Shared trails | None |
|---|---|---|
| T-A | +1.44 | +1.04 |
| T-F | +1.90 | +1.16 |

**With trails off** ("none"), the gains are T-A +0.172 and T-F +0.091, with the same pattern: gating carries
the largest allocation, and sensing and gating are co-adapted.

**The trail dependence, split** (Shapley with shared trails minus with none; joint maze-bootstrap 95%):

| Group | T-A | T-F |
|---|---|---|
| sensing | −0.018 [−0.053, +0.018] | +0.197 [+0.147, +0.247] |
| gating | −0.059 [−0.095, −0.023] | +0.124 [+0.072, +0.175] |
| output | +0.012 [−0.005, +0.028] | +0.025 [+0.006, +0.044] |
| latch | +0.008 [−0.002, +0.020] | +0.014 [+0.003, +0.027] |

"None" removes the own and the peers' trails together, so this does not isolate peer effects.

## B. The side attribution (shared trails)

| Group | T-A Shapley | T-F Shapley | T-A reversion | T-F reversion |
|---|---|---|---|---|
| module A | −0.056 | +0.219 | −0.258 | −1.079 |
| module B | +0.088 | +0.001 | −0.344 | −0.532 |
| selector | +0.082 | +0.232 | −0.597 | −1.196 |

**How to read it:**
- **A different question:** the side partition puts the comparator biases inside the modules, and the
  latch → comparator edges in the selector. So its "selector" is not the functional "gating" (plan §4).
- **Hybrids off the path:** here too, mixing a module's tuned weights with the seed's selector, or the
  reverse, puts some hybrids below W2 alone.

## C. Lesions

Each cost is the lesioned minus the intact organism, in units of the seed's mean. The values are schedule means
with t intervals over runs. The intact means with shared trails, visits per wey:
- **T-A:** 6.07-6.90;
- **T-F:** 6.89-9.52;
- **N:** 4.92-5.50;
- **the seed:** 5.71;
- **W2 alone** (all 32 outputs silenced, the same for every organism): 1.65.

| Lesion (shared trails) | T-A | T-F | N | The seed |
|---|---|---|---|---|
| latch held at its A state | −0.95 [−0.98, −0.91] | −1.25 [−1.36, −1.13] | −0.75 | −0.85 |
| latch held at its B state | −0.97 [−1.01, −0.94] | −1.26 [−1.37, −1.15] | −0.77 | −0.91 |
| visit input cut (q drifts by its own bias) | −0.97 | −1.25 | −0.76 | −0.78 |
| gate cut (tuned biases kept) | −0.87 [−0.96, −0.78] | −1.18 [−1.28, −1.09] | −0.63 | −0.78 |
| reflex held at rest | −1.11 [−1.15, −1.07] | −1.45 [−1.57, −1.33] | −0.91 | −0.95 |
| A's outputs silenced | −0.72 | −1.13 | −0.56 | −0.56 |
| B's outputs silenced | −0.57 | −0.94 | −0.39 | −0.49 |
| nose inputs removed (trail and scent) | −0.54 [−0.67, −0.40] | −0.71 [−0.89, −0.52] | +0.08 [−0.02, +0.19] | −0.71 |

**With trails off,** the costs keep the same order:
- **the latch clamps:** T-A −0.76 and −0.78, T-F −0.61 and −0.61, N −0.98 and −1.00;
- **the nose inputs removed:** T-A −0.35, T-F −0.10, N −0.15. With trails off, the noses carry only the
  path-distance scent.

`summary.json` (`lesions`) holds every outcome: the later-leg rate, the unvisited and round-trip shares, the
first-B time and median legs.

**The reading:**
- **Every organism needs:**
  - the latch to switch;
  - the comparators' gating;
  - the reflex's wall response.
- **The T champions also need their nose inputs.**
- **N's champions,** tuned without trail access, still need the latch and the comparators' outputs, but not
  the nose inputs when trails are shared.

## D. The latch in the maze

The recorder ran with shared trails on the intact organisms. It reads each organism's own unstable root and
coding (plan §5D; D195).

| | T-A | T-F | N | The seed |
|---|---|---|---|---|
| Agreement with the goal (decided ticks, middle-third band) | 1.000 | 0.994-1.000 | 1.000 | 1.000 |
| Legs switched after a visit (both directions) | 1.000 | 1.000 | 1.000 | 1.000 |
| Pre-aligned legs | 0 | 0 | 0 | 0 |
| Latency, ticks | 1-2 | 1-3 | 1-2 | 1 |

- **Undecided ticks** number about one per leg: the transit through the middle band during a switch.
- **The latch's design:** it is driven by the visit relays, so switching after a visit is what it was built to
  do. The tuned latches still do it.
- **The latch's use:** C's clamps show the switching is used. Without it, the champions fall to about W2
  alone's level or below.

## E. Genome descriptives

`summary.json` (`genomes`) holds, for every organism:
- the latch's states and unstable root, and its relay signs (A = the high state in all 21);
- the gate edges;
- the comparators' effective biases at each latch state;
- the resting turn at each state.

**The resting turn command:**
- **the seed:** 0.40 at both states;
- **T-A's champions:** 0.65-1.00;
- **T-F's champions:** 0.73-1.00;
- **N's champions:** 1.00 at both states.

## What this does and does not show

**Shown, within these organisms and these substitutions:**
- **The selector is used:**
  - E3b-1's tuned colonies need their latch to switch, and it switches after every visit;
  - they need the comparators' gating;
  - the T champions need their nose inputs.
- **The gain lives in co-adapted comparator parameters.**
  - The comparators' input weights and their operating point (biases and latch weights) changed together.
  - Neither works with the other's seed values.
  - Within this attribution scheme, the output edges and the latch parameters carry little of the gain.

**Not shown:**
- **How the moved operating point produces better shuttling.** The probes measure local sensitivity under
  imposed states; the attribution measures substitutions.
- **That a group with a small allocation is unused.** The output edges are clearly used (C), even though
  their tuned values add little.
- **Anything about worm behaviour,** or that weys follow a trail's direction.

**For the next step** (the plan's non-binding reading, §6): the selector is in use in these organisms, so E3's
assembly comparison and E4 keep their premise. Which follows is the owner's decision, with both reviewers.

## Deviations

- **The benchmark block:** 7300-7555, not "smoke mazes", as stated in plan draft 3 (D195).
- **The scent lesion's name:** it removes all nose input (the trail and the path-distance scent), as its
  implementation (`without_scent`) zeroes the four A/B nose channels. The plan called it "scent removed".
- **No other departure** from plan draft 3.
