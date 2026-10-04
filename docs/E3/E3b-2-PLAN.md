# E3b-2 plan: where E3b-1's gain comes from (exploratory) — draft 1

**Status:** draft 1, 2026-10-04, for review by both reviewers (Astra 6, Fable 5.1). Nothing has run.
- **Why:** the owner chose this step after E3b-1 (D193).
- **Kind:** exploratory. Every analysis is fixed here before it runs, and none is a registered test. The
  results will be reported as descriptions with intervals, not as verdicts.

## 1. The question

**What do E3b-1's tuned colonies use to beat the frozen seed?** E3b-1's gate read "better": +0.225 of the
seed's mean on the test mazes, with T-A at +0.069 and T-F at +0.381. Its probes found that no tuned champion
still meets the seed's comparator criteria, and three of T-F's best champions show zero measured active K_D
at every level. E3b-1 did not test which tuned parameters carry the gain, or whether the latch still tracks
the goal in the maze.

**Why it comes first:** the roadmap's next steps, E3's assembly comparison and E4 (information crossing
between the modules), both assume the engineered selector is in use.

**The frame:**
- the organism is a hand-built circuit on a silent worm, so nothing here is about worm behaviour;
- stereo sensing is a game-design choice;
- E3b-2 evolves nothing.

## 2. Inputs (fixed, checked at load)

- **The organisms:** E3b-1's 16 final T champions (T-A runs 0-7 at index 124, T-F runs 0-7 at index 299)
  and the frozen seed E + W2.
  - The champions' genomes are local (`runs/e3b1/genomes`). Each is checked against its sha256 in
    `experiments/E3-ab-organism/E3b-1/champions.json`.
  - N's and R's champions and T-F's champions at index 124 are not used.
- **The task:** E3b-1's configuration exactly: c = 5, H = 2 400, colonies of 8 on up to 4 spawns, the trail
  constants μ 0.01, λ 0.02, δ 0.05, d₀ 1.142, maze run seed 1 180 000, episode 0. Amendment 1's redraw rule
  applies.
- **The fixed-input hashes:** E3b-1's `champions.json`, `evaluate.json` and `PREREGISTRATION.md`, and E4s-0's
  `module.json`.

## 3. The mazes

- **A fresh block:** ids 7000-7255 (256 mazes), at maze run seed 1 180 000.
  - It lies outside every block of E3b-0 and E3b-1. No organism has played it.
  - Its feasibility and any redraws are listed by a pre-flight before the first stage.
- **Smoke ids:** 9600 and up, never results.
- **Not used:** E3b-1's test block (6000-6255), and its validation, learning and calibration blocks.
- **The measure:** visits per wey (the colony mean), as in E3b-1. Where noted, also the later-leg rate.

A champion's **gain** on this block is (its mean visits − the seed's) / the seed's mean, both with shared
trails: E3b-1's d, re-measured on fresh mazes.

## 4. The parameter groups

Tuning in E3b-1 could change 47 chemical edges and 9 neurons' τ and bias (`tuning.scales`). The W2 reflex,
the relays' τ and bias, the worm block (the carrier's turn and forward biases) and the gap junctions were
frozen. They are partitioned two ways.

**The functional partition (4 groups):**

| Group | Parameters |
|---|---|
| **sensing** | the 8 nose → comparator edges (A's and B's), the 4 nose neurons' τ and bias, and the 4 comparators' τ |
| **gating** | the 4 comparators' biases and the 4 latch → comparator edges |
| **output** | the 32 comparator → turn-neuron edges |
| **latch** | the latch's self-edge, the 2 relay → latch edges, and the latch's τ and bias |

**The side partition (3 groups):**

| Group | Parameters |
|---|---|
| **module A** | A's nose → comparator edges, A's 16 output edges, and A's 4 neurons' τ and bias |
| **module B** | the same, for B |
| **selector** | the latch's self-edge, the relay → latch edges, the latch's τ and bias, and the 4 latch → comparator edges |

A test checks that each partition covers every mutable parameter exactly once, and no frozen one.

## 5. The analyses

### A. The functional attribution

- **The hybrids:** for each champion, all 2⁴ = 16 hybrids that take each group's values from either the
  champion or the seed. The all-seed hybrid is the seed and the all-champion hybrid is the champion, each
  checked bitwise.
- **Each hybrid's gain** on the fresh block, with shared trails.
- **Per champion, from the 16 gains:**
  - each group's Shapley value: its average marginal contribution over the orders, which sums exactly to
    the champion's gain;
  - each group's **reversion effect** (the champion with that group set back to the seed's values);
  - its **transplant effect** (the seed given that group's champion values);
  - the interaction terms (the Harsanyi dividends) of every pair and higher set.
- **Reported:**
  - per champion;
  - each schedule's mean, with a two-sided 95% t interval over its 8 runs;
  - the mean of the two schedules' means.

### B. The side attribution

The same over the side partition: 2³ = 8 hybrids per champion, with Shapley values, reversions,
transplants and interactions.

### C. Lesions

On each champion and on the seed, with shared trails and with trails off ("none"):
1. **gate cut:** the 4 latch → comparator edges at 0;
2. **latch frozen:** the 2 relay → latch edges at 0, so the latch never switches from its start;
3. **A's outputs silenced:** A's 16 output edges at 0;
4. **B's outputs silenced:** B's 16 output edges at 0;
5. **both silenced:** all 32 output edges at 0, leaving W2 and the carrier.

**Reported:** each lesion's cost, (lesioned − intact) / the seed's shared mean, per organism, by schedule
and for the seed.

### D. Does the latch track the goal in the maze?

A recorder reads, every tick, each wey's latch state q and its current goal (A or B).
- **The agreement:** the share of wey-ticks after the wey's first confirmed visit at which sign(q) matches
  the goal, taking q > 0 as goal A, the seed's coding.
- **Also reported:** the share for the opposite coding (1 − agreement), and the share of ticks with |q| below
  the probe's separation threshold (an undecided latch).
- **Organisms:** the 16 intact champions and the seed, with shared trails.

### E. The resting turn (no new compute)

From E3b-1's probe records: each champion's turn command with no nose input at each latch state, against
the seed's. This is descriptive context for C.

### F. Replication on fresh mazes

The 16 intact champions' gains on this block, set beside their E3b-1 test-block d: the per-champion pairs,
their correlation, and the two means. Descriptive.

## 6. Compute

**The projection,** from E3b-1's timed chunk of 16 organisms × 256 mazes (149 s):
- A: 256 organism-variants, 16 chunks;
- B: 128 variants, 8 chunks;
- C: 102 variants × 2 conditions, about 13 chunks;
- D: 17 organisms with the recorder, 2 chunks;
- F: shared with A.

That is about 39 chunks, or about 1.6 GPU-hours, plus a pre-flight and a short CPU benchmark.

**The cap:** 5 GPU-hours, counted through `wormwars.accounting`. If the benchmark projects more than 4, B is
dropped first, then C's "none" condition.

## 7. How it runs

- **A runner, `scripts/e3b2.py`,** with stages `project`, `attribution` (A, B and F), `lesions` (C) and
  `latch` (D), and a `report` (E and the summaries).
- **Each stage:**
  - checks its fixed inputs and the champions' hashes;
  - runs a maze pre-flight;
  - saves per-maze arrays as each chunk completes, and resumes at the first incomplete chunk;
  - runs on the GPU, in E2's stage frame, once, with one rerun after a crash.
- **Tests first** (rule 9), each seen failing:
  - each partition covers every mutable parameter exactly once;
  - the all-seed and all-champion hybrids are bitwise the seed and the champion;
  - each lesion zeroes exactly its edges;
  - the Shapley values sum to the gain, checked on synthetic gains;
  - the recorder's agreement on a scripted case;
  - the fresh block is disjoint from every earlier block;
  - the champions' hash check refuses a changed genome;
  - a smoke run of every stage.
- **The review:** both reviewers review this plan before code, and the code before the GPU run.

## 8. What would be reported, and how

- **Every number is descriptive.** There is no gate, no "better" or "worse", and no p-value used as a
  verdict.
- **The fixed wording frame:** "In E3b-1's tuned champions, on 256 fresh mazes, the share of the gain
  attributable to <group> is …". Attribution is within this organism and these groups. It says which tuned
  parameters carry the gain, not how the behaviour works.
- **Reversion and transplant are reported beside Shapley values.** They answer different questions:
  whether the champion still needs the group's tuned values, and whether those values help on their own.
- **Not claimed:**
  - that a group with a small share is unused;
  - any mechanism beyond what C and D measure directly.
