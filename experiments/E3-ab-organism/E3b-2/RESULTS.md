# E3b-2 results: where E3b-1's gain comes from (exploratory, 2026-10-04)

**Reviewed by both reviewers** (Astra 6, Fable 5.1: "fix then publish"); corrected (D197;
`docs/reviews/20261004-E3b-2-results/`). Both recomputed the readings from the committed records: Astra from all 70
chunks, Fable from `summary.json`. Neither found a calculation defect.

**E3b-2 is exploratory.**
- **The plan:** `docs/E3/E3b-2-PLAN.md`, draft 3. Its analyses were fixed before the run, and reviewed by both
  reviewers at the plan, the code and a confirmation pass (D194-D196).
- **Every number is descriptive.** There is no gate and no verdict.
- **The source:** every number comes from `summary.json` and the per-maze chunks in this folder.
- **Units:** "of the seed's mean" means in units of the frozen seed's mean visits per wey with shared trails on
  the fresh block (5.71).
- **The intervals:** the run-level t intervals are conditional on this maze block. The maze-bootstrap
  intervals address the other source of variation.

**The setting:**
- **Mazes:** 256 fresh mazes (7000-7255) that no organism had played.
- **Organisms:** E3b-1's 16 final T champions (T-A runs 0-7, T-F runs 0-7), N's 4 champions and the frozen
  seed E + W2.

**Compute:** 3.00 of the 5 hours capped (10 790 accounted seconds of synchronised wall time; no failed
attempt, no drop; `compute-record.json`).
- `project`: 0.33;
- attribution: 1.60;
- lesions: 1.01;
- latch: 0.06.

**The checks.** All six saved per-maze outcome arrays are identical:
- for the seed, in every chunk where it appears in the same composition (A-shared, A-none, B);
- for the lesion stage's intact champions, against the attribution's all-champion hybrids.

These are equalities of the saved outcomes, not of whole trajectories. The resting turn computed from each
genome equals E3b-1's and E3b-0's probe records exactly.

## In brief

- **The gain replicates on fresh mazes.** Across the 16 champions, the pooled correlation with their E3b-1
  test-block d is 0.99:

  | Schedule | Fresh mazes | E3b-1 test block |
  |---|---|---|
  | T-A | +0.114 | +0.069 |
  | T-F | +0.451 | +0.381 |

- **The selector's switching is used.**
  - **Holding the latch at either of a champion's own stable states removes 85-87% of its shared-trail
    visits.** The schedules' means fall to about one visit per wey, below W2 alone's 1.65:

    | | Intact | Latch held at A | Latch held at B |
    |---|---|---|---|
    | T-A | 6.36 | 0.96 | 0.80 |
    | T-F | 8.28 | 1.17 | 1.10 |
    | The seed | 5.71 | 0.87 | 0.54 |

  - **The recorder is an integrity check, not the evidence of use.** It shows the latch is neither stuck nor
    bypassed: every leg that did not run into the horizon crossed toward the new goal, in every organism. In
    total there were 294 084 legs after visits, none pre-aligned and 179 censored. The latch is visit-driven
    by design, so the clamps carry the evidence that its switching is used.
  - **The reading written into the plan before the run** (§6): the tuned organisms still use dynamic
    selection, so the premise of E3's assembly comparison and of E4 holds for them.
    - **What it shows:** that the tuned organisms are suitable starting points for those experiments.
    - **What it does not show:** that their comparators keep the seed's computation, that modular assembly
      helps, or that information crosses between the modules.
- **The sensing and gating parameter groups interact strongly.** Under the specified seed-champion
  substitutions, mixing them often causes severe losses.
  - **The groups:** "sensing" holds the nose → comparator weights, the nose neurons' τ and biases, and the
    comparators' τ. "Gating" holds the comparator biases and the latch → comparator weights.
  - **The mixed hybrids:** the eight that take one group from the champion and the other from the seed fall
    below W2 alone:
    - in 15 of 16 champions, at least four of the eight (all eight in 6);
    - in T-F run 4, none, though its tuned sensing with the seed's gating still loses 0.51;
    - many of them score zero visits: all eight mixed hybrids of T-F runs 5 and 7, and three of T-A run 0's.
  - **The tuned pair on the seed's output edges and latch** reaches 70% of T-A's gain (+0.080 of +0.114) and
    79% of T-F's (+0.358 of +0.451).
- **The schedules differ in where the rest sits.**
  - **T-F:** sensing and gating take 95% of the summed gain in Shapley allocation. Reverting T-F's output
    edges to the seed's costs −0.084 [−0.156, −0.012], about a fifth of its gain.
  - **T-A:** the output edges take 36% of its summed gain (+0.041 of the seed's mean, +0.23 visits per wey).
    Its sensing allocation is negative and its gating allocation larger.
  - **The latch parameters** take about 2% (T-F) and 7% (T-A).
  - **E3b-1's probe finding, read again:** E3b-1 found that the tuned comparators fall short of the seed's
    design thresholds. These results are consistent with a moved operating point of comparators that are
    still in use. They do not show how the moved point produces better shuttling.
- **The nose inputs** (the trail and the path-distance scent together, the noses' biases and τ kept):
  - **The T champions use them:** removing them costs T-A −0.54 and T-F −0.71 of the seed's mean with shared
    trails.
  - **N's champions use the scent but not the trails.**
    - Under "none", their tuned condition, removing the noses costs −0.15 [−0.25, −0.06].
    - With shared trails it changes nothing (+0.08, interval including 0).
    - Shared trails cost them: their intact visits are 4.92-5.50 with shared trails and 6.28-6.76 without.
- **T-F's added trail dependence:** the shared − none difference of the allocations (+0.360 in total) goes
  primarily to sensing (+0.20) and gating (+0.12). Output and latch take small positive parts.
- **The secondary outcomes separate the schedules** (shared trails):

  | | T-A | T-F | The seed |
  |---|---|---|---|
  | Later-leg rate, per 1 000 ticks | 2.82 | 3.83 | 2.76 |
  | Unvisited share | 0.034 | 0.055 | 0.097 |
  | Round-trip share | 0.862 | 0.885 | 0.665 |

  T-A's gain comes mostly from more weys reaching the sources and completing round trips. T-F also shuttles
  faster.

## A. The functional attribution

All 16 seed/champion hybrids of each champion were played (plan §4, §5A).

**Schedule means** (shared trails; t interval over runs):

| | T-A | T-F |
|---|---|---|
| Net gain | +0.114 [+0.076, +0.153] | +0.451 [+0.328, +0.575] |
| The tuned sensing + gating pair alone | +0.080 | +0.358 |

| Group | T-A Shapley | T-F Shapley | T-A reversion | T-F reversion | T-A transplant | T-F transplant |
|---|---|---|---|---|---|---|
| sensing | −0.121 [−0.362, +0.119] | +0.201 [+0.011, +0.391] | −0.562 | −1.180 | −0.822 | −0.777 |
| gating | +0.186 [−0.062, +0.434] | +0.230 [+0.068, +0.391] | −0.903 | −1.221 | −0.541 | −0.764 |
| output | +0.041 [+0.026, +0.056] | +0.012 [−0.021, +0.045] | −0.036 | −0.084 | +0.032 | −0.060 |
| latch | +0.008 [+0.001, +0.016] | +0.009 [+0.001, +0.017] | −0.005 | −0.019 | +0.018 | +0.020 |

**Schedule shares of the summed gain** (Shapley; negative allocations push shares outside [0, 1]):

| Group | T-A | T-F |
|---|---|---|
| sensing | −1.06 | +0.45 |
| gating | +1.63 | +0.51 |
| output | +0.36 | +0.03 |
| latch | +0.07 | +0.02 |

**The pair interaction** (the Harsanyi dividend of {sensing, gating}, mean per schedule):

| | Shared trails | None |
|---|---|---|
| T-A | +1.44 | +1.04 |
| T-F | +1.90 | +1.16 |

**How to read these:**
- **The reversions and transplants of sensing and gating are large and negative,** because the hybrids
  holding one of the pair without the other perform very poorly, often at zero visits. There are individual
  exceptions: transplanting T-A run 2's gating into the seed gains +0.012.
- **The large positive pair dividend partly reflects recovery from those very poor singleton hybrids.** It is
  not that much extra performance delivered by a separately identified mechanism.
- **T-A's Shapley values:** its negative sensing allocation and larger gating allocation come from splitting
  this interaction. They are not evidence that tuned sensing hurts.
- **What the allocations depend on:** they are exact for this baseline, partition and substitution table, not
  the route evolution took (plan §9).
- **What the groups cannot separate:** whole groups are exchanged. Sensing includes the noses' biases and
  τ; gating includes both the comparators' biases and the latch's weights onto them. So the attribution does
  not separate sensory computation from changes in tonic output or response timing.
- **The latch parameters barely moved:** the latch's self-weight is 1.66-2.44 across the 20 champions,
  against the seed's 2.0. That is consistent with their small allocation.

**With trails off** ("none"), the gains are T-A +0.172 and T-F +0.091. Gating carries the largest
allocation, and sensing and gating again interact strongly.

**The trail dependence, split** (Shapley with shared trails minus with none; joint maze-bootstrap 95%):

| Group | T-A | T-F |
|---|---|---|
| sensing | −0.018 [−0.053, +0.018] | +0.197 [+0.147, +0.247] |
| gating | −0.059 [−0.095, −0.023] | +0.124 [+0.072, +0.175] |
| output | +0.012 [−0.005, +0.028] | +0.025 [+0.006, +0.044] |
| latch | +0.008 [−0.002, +0.020] | +0.014 [+0.003, +0.027] |
| Total (= the shared − none gain difference) | −0.057 | +0.360 |

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
- **Hybrids off the path:** here too, some hybrids fall below W2 alone (`hybrids_below_w2`).

## C. Lesions

Each cost is the lesioned minus the intact organism. Visits are in units of the seed's mean. The other
outcomes are raw differences in `summary.json` (`lesions`).
- **The values:** schedule means, with t intervals over runs.
- **The intact means with shared trails, visits per wey:**
  - T-A 6.07-6.90;
  - T-F 6.89-9.52;
  - N 4.92-5.50;
  - the seed 5.71;
  - W2 alone 1.65 (all 32 outputs silenced, the same for every organism).

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

**As a share of each organism's own performance,** the latch clamps remove about 85-87% of the T schedules'
visits, 82-85% of N's and 85-91% of the seed's. The differences in the table above are mostly the
champions' higher intact levels.

**With trails off:**
- **Both clamps and the reflex lesion stay strongly harmful:**
  - the clamps: T-A −0.76 and −0.78, T-F −0.61 and −0.61, N −0.98 and −1.00;
  - the reflex held at rest: T-A −0.93, T-F −0.85, N −1.14.
- **The order of the smaller costs changes:** for T-F and N, the gate cut costs less than A's outputs.
- **Removing the noses**, which then carry only the path-distance scent, costs T-A −0.35, T-F −0.10 and
  N −0.15.

**The nose lesion** tests the net contribution of those inputs in the tested condition. It does not isolate
stereo comparison or trail following.

## D. The latch in the maze

The recorder ran with shared trails on the intact organisms, with each organism's own unstable root and
coding (plan §5D; D195).

| | T-A | T-F | N | The seed |
|---|---|---|---|---|
| Agreement with the goal (decided ticks, middle-third band; range over organisms and goals) | 1.000 | 0.994-1.000 | 1.000 | 1.000 |
| Agreement in the middle-half band | 1.000 | 1.000 | 1.000 | 1.000 |
| Uncensored legs crossed toward the new goal | all | all | all | all |
| Pre-aligned legs | 0 | 0 | 0 | 0 |
| Mean latency per organism, ticks (over crossings) | 1-2 | 1-3 | 1-2 | 1 |

**The middle-third band's readings:**
- **The disagreements are transit ticks.** T-F runs 0, 3 and 6 fall below 1.000 because of opposite-side
  ticks, and their number equals the number of legs (run 0: 8 115 for 8 118 legs toward A). They are the
  first tick after a visit in latches that take 2-3 ticks to cross.
- **No stray latch state:** no organism shows another kind of disagreement.
- **The undecided ticks vary:** from zero in 7 of the 21 organisms (and in one goal in 2 more) to about one per
  leg. In total they number 161 395, against 294 084 legs.

`summary.json` (`latch`) holds:
- the per-goal counts, the occupancy and the eligible weys;
- the censored legs per direction;
- both bands, with maze-bootstrap intervals.

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

## Where the supporting readings are

`summary.json` holds:
- **`attribution.tables`:** per champion, the gain, the Shapley allocations (also in visits per wey), the
  reversions, the transplants, the full dividend and hybrid tables, and, per schedule, both interval types and
  the shares;
- **`attribution.trail_split`;**
- **`variants`:** every variant's absolute outcomes, median legs included;
- **`attribution.hybrids_below_w2`;**
- **`lesions`:** every outcome;
- **`latch`;**
- **`genomes`;**
- **`replication`.**

`python scripts/e3b2.py summary` rebuilds it from the committed chunks.

## What this does and does not show

**Shown, within these organisms and these substitutions:**
- **The latch's switching is used:** E3b-1's tuned colonies need their latch to switch, and it does after
  visits.
- **The comparators' gating and the reflex's wall response are needed.** The T champions also need their
  nose inputs.
- **The sensing and gating parameter groups interact strongly.** Most of the gain is reached with both tuned
  together, while the output edges carry a substantial part of T-A's smaller gain.

**Not shown:**
- **How the changed parameters produce better shuttling.** The attribution exchanges whole groups and does
  not separate sensory computation from tonic output or timing.
- **That the comparators still compute what the seed's did.**
- **That a group with a small allocation is unused.** The output edges are clearly needed (C).
- **Anything about worm behaviour,** or that weys follow a trail's direction.

**For the next step** (the plan's non-binding reading, §6): the selector is in use in these organisms, so E3's
assembly comparison and E4 keep their premise. Which follows is the owner's decision, with both reviewers.

## Notes on the plan

- **The benchmark block** 7300-7555 is the one stated in plan draft 3 (drafts 1-2 said "smoke mazes"; D195).
- **The lesion the plan calls "scent removed"** zeroes the four A/B nose channels, which carry the trail and
  the path-distance scent together. It is named for what it removes here. The intervention is the one
  planned.
