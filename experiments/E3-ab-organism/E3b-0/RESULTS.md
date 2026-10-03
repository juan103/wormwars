# E3b-0 results: the maze engine, the controls and the task's feasibility (2026-10-03)

**E3b-0 is exploratory** (plan: `docs/E3/E3b-0-PLAN.md` v3, with Amendments 1 and 2; decisions D175-D179).
**Everything chosen after Stage B is adaptively selected:** the trail rule was changed twice after seeing
data, each change reviewed by both reviewers (Astra 6, Fable 5.1) before it ran.

**Compute:** 2.62 of the 3 GPU-hours capped (`compute-record.json`).

## In brief

- **The task works at c = 5, H = 2 400.** Colonies of 8 weys shuttle between two dead ends of a 5 × 5 tree
  maze. The oracle makes 34.5 visits per wey; the random walk 2.07.
- **Linear trails help, on the untouched report mazes (1000-1255).**
  - **The scripted follower:**
    - shared − none +3.57 [2.97, 4.19] legs per 1 000 ticks after the first visit;
    - own − none +2.06 [1.54, 2.61].
  - **The seed, E with the one-sided wall reflex W2:**
    - shared − none +0.69 [0.44, 0.93];
    - own − none +0.43 [0.28, 0.59].
- **Peers help: later discoverers find B sooner with shared trails than with own trails only.**

  | | shared − own, first-B time | As a share of own's |
  |---|---|---|
  | Follower | −61 ticks [−107, −18] | −7% |
  | Seed | −196 ticks [−242, −150] | −13% |

- **Trails from another episode mislead.**
  - Replaying a donor colony's trails, from another episode on the same walls with different sources, is
    far worse than the wey's own trail alone.
  - So is the peers' trail with its open cells scrambled.
  - Exposure was matched.

  | | replay − own | scramble − own |
  |---|---|---|
  | Follower | −3.58 | −4.13 |
  | Seed | −1.06 | −1.24 |

- **Not shown:** that weys use the trail's direction. The registered polarity test was not passed by the
  scripted follower, at any setting, even on a reference slope. It is reported, not claimed.
- **E3b-1 as sized does not fit:** about 71 GPU-hours projected for two training arms, against the plan's
  24 and the owner's ceiling of about 30. Its design must cut (§5 below).

## The stages

| Stage | Record | Outcome |
|---|---|---|
| A: maze size and horizon | `stage-a.json` (41fcb68) | c = 5, H = 2 400 (the four H = 1 200 candidates failed on the follower's legs) |
| B: the trail grid, 24 live settings | `stage-b.json` (4ac36b6) | none passed |
| B2: Amendment 1 | `stage-b2.json` (19a1b12) | none qualified |
| B3: Amendment 2 | `stage-b3.json` (ab5cdbe) | μ 0.01, λ 0.02, δ 0.05, d₀ 1.142 chosen; 23 of 54 settings qualified, 30 of them widened |
| Stage A's recheck | `recheck-a.json` (6c7dd17) | passed |
| C: variants and seeds | `stage-c.json` (82fb7e0) | the seed E, variant W2 |
| Report | `report.json` (b55e32e) | below |
| Timing | `timing.json` (c769a49) | below |

**Stage B: none passed.**
- Polarity read at most +0.02, against 0.3.
- The nose range read at most 0.46, against 0.9.
- The gradient failed in 2 settings (0.797).

**What the diagnoses found** (`development-records/`, `INTERIM-REPORT.md` with its corrections):
- the polarity test, as registered, could not be passed by a bilateral, memoryless follower facing away;
- the 90% range target could not be reached with occluded noses reading 0.

**Amendment 1 (D178)** kept the gradient and added two gates:
- a cap on the follower's inputs: at most 5% above 0.35, the seeds' qualified range;
- a positive trail effect.

**Amendment 1 qualified nothing.** The two gates did not meet: strong trails exceeded the cap, and weak ones
gave no effect.

**The seeds diagnosed, on all 256 selection mazes** (diagnosis 4):
- **E + W2 gained from linear trails:** +1.27 [1.01, 1.53] at Stage B's best-rate setting.
- **The cap had been set at the wrong level, on the wrong agent** (Fable). Along a linear trail the
  response to a relative difference is K_D × level, and E's stays above its value at 0.35 up to 1.0. The
  follower's inputs run about twice the seed's.

**Amendment 2 (D179)** moved the cap to 1.0 and onto the seed E + W2's own inputs.

**Stage C chose the seed E with the variant W2.**
- E + W0 and E + W1 barely move through the maze.
- E + W1+M40 and E + W1+M80 exceed the random walk's mean visits (by 1.10 and 0.69), and their trail
  effects are positive (+0.77 and +0.61), but each has a median of 1 leg per wey, below criterion 2's 2.
- **S3r3 fails with every variant.** It circles with a turn bias of −0.76: its evolved, asymmetric outputs
  leave a net turn that W2's resting turn does not cancel (D179). That is a property of the organism, not
  a wiring bug.

## The exit criteria (plan §5), on the report mazes 1000-1255 unless stated

**1. Mechanics: passed on the CPU; the GPU leg was not run.**
- Every test passes, test-first, with sabotage checks for each mechanism.
- On the CPU, every earlier task is bitwise identical to the engine at 84ff98a: Task N, foraging, E3a's
  shuttle and E4s-1's graft (`development-records/compare-*.json`).
- **The plan's GPU leg (E2's GA generations 0-25, hashed) was not run in E3b-0.** It is owed before
  E3b-1's runs.
- **Bugs found and fixed during E3b-0,** each found by a reviewer and each before it affected a recorded
  result:
  - shared exposure was recorded as 0, which would have set the replay coefficient to 0;
  - the recheck was not enforced;
  - the "toward" polarity start faced a wall at bends;
  - the M oscillator never started.

**2. A usable task: passed** (`report.json`, `criterion2`):

| E + W2 | Value | Needed |
|---|---|---|
| Visits per wey above the random walk (paired over mazes) | +3.71 [3.22, 4.23] | lower bound above 0 |
| Median legs per wey | 3.56 | at least 2 |
| Headroom: oracle − seed | 28.7 visits | at least 2.5 (2 × 0.22 × the seed's mean) |

- **Reported beside it:**
  - the seed is above W2 alone by +1.09 [0.44, 1.77] visits per wey;
  - it is well below the scripted follower, by −11.6 [−13.0, −10.4].

**3. A usable signal: passed.** Legs per 1 000 ticks, 95% intervals over the 256 report mazes:

| Contrast | Follower | Seed E + W2 |
|---|---|---|
| shared − none | +3.57 [2.97, 4.19] | +0.69 [0.44, 0.93] |
| own − none | +2.06 [1.54, 2.61] | +0.43 [0.28, 0.59] |
| shared − own | +1.52 [1.03, 1.98] | +0.26 [0.00, 0.50] |
| peers − none | +3.14 [2.59, 3.71] | +0.62 [0.38, 0.86] |
| replay − own | −3.58 [−4.18, −3.02] | −1.06 [−1.32, −0.81] |
| scramble − own | −4.13 [−4.73, −3.56] | −1.24 [−1.53, −0.97] |
| First-B time of later discoverers, shared − own | −61 ticks [−107, −18] | −196 ticks [−242, −150] |

- **What passed:**
  - **The follower:** shared − none and own − none each have a lower bound above 0.5, and shared is
    faster on the peer measure.
  - **The seed:** its shared − none has a lower bound above 0.
- **Replay and scramble (reported):**
  - the replay coefficient was frozen from a selection-maze pre-pass: 0.80 for the follower, 0.64 for the
    seed;
  - the replay's exposure matched the live peers' to within −0.018 (follower) and −0.007 (seed) per nose;
  - its route overlaps the recipient's by 0.37 on average.
  - **The reading:** another episode's trails on the same walls mislead, since they mark the wrong route.
    The peers' benefit depends on their trails marking the colony's own sources.
- **Single-wey colonies:** the seed makes 5.25 visits per wey and the follower 14.33.
- **Behavioural polarity** at the chosen setting (`stage-b3.json`), as real − max(none, permuted):

  | Start | At 2 × the oracle's time | At 4 × |
  |---|---|---|
  | Facing away from A | −0.04 | +0.09 |
  | Facing toward A | +0.09 | +0.02 |
  | Uniform heading | +0.08 | +0.07 |
  | Reference slope, facing toward A | +0.18 | +0.09 |

  The wording fixed in advance: Stage B failed the registered behavioural polarity criterion.
  Gradient-sign qualification does not establish directional trail use; the amended stage reports
  behavioural polarity separately. **E3b-1 makes no claim of directional trail use.**
- **Gradient signs** at the chosen setting: 0.82 of route cells rise toward the source with 1 contributor,
  and 0.84 with 8, at age 1 leg.

**4. Frozen settings: passed.**
- **The settings:**
  - c = 5, H = 2 400, a colony of 8;
  - trails: μ 0.01, λ 0.02, δ 0.05, d₀ 1.142;
  - scents: σ 3 path cells, zero beyond 9;
  - the seed E with W2.
- **The component tests,** at the seed's own measured levels (`report.json`, `component_tests`):
  - 0.001, 0.003 and 0.04-0.23: active K_D 34.6-32.8;
  - 0.35: 30.6;
  - 0.89 and 1.0: K_D × level 15.1 and 14.5, against the required 10.5;
  - the one-nose checks pass at every level up to 1.0;
  - the 99th percentile, 1.82, is above the cap's level and only reported (K_D 3.4).
- **The seed's own inputs:** 4.0% exceed 1.0, against a cap of 5%.
- **The memory assays' delay D:** the seed's median later leg is 141 ticks.

**5. A feasible E3b-1: failed as sized** (`timing.json`):
- **The measured cost** at E3b-1's composition (256 strains × 16 worlds × 8 weys):
  - 0.057 s per tick, 1.2 GB peak;
  - 0.121 s and 2.2 GB with the lockstep replay donors (8 192 worlds).
- **The projection:** 500 generations of 12 runs at H = 2 400 cost 28.3 GPU-hours per training arm. Two
  arms with a 25% reserve need 71 hours, against the 24 planned. Validation and evaluation come on top.
- **The plan's cut order applies:** generations, then worlds per genome, then horizon. Stage A showed that
  H = 1 200 does not support 4 follower legs at c = 5, so the horizon is the last resort. If the gate alone
  exceeds 24 hours after the cuts, the owner is asked.

**6. Power for the gate.** 12 runs per gate arm with a calibrated test (`power.json`, `fine`).
- This assumes a run-level CV of 0.28, taken from E3a's open-arena champions.
- E3b-0's own between-maze CV of the seed's visits is 0.74. That is a different quantity, the spread of
  maze difficulty, not of tuned runs, and it is reported beside the assumption.
- The run-level spread in mazes is unknown until E3b-1's own runs.

## What this does and does not show

**Shown, exploratory:**
- on 256 untouched mazes, linear trails raise the shuttle rate of an engineered, wall-following seed and of
  a scripted follower;
- peers' trails speed later discoverers;
- trails from another episode on the same walls mislead.

**Not shown:**
- that the weys follow the trail's slope toward a source (polarity was not passed);
- anything about evolution: E3b-0 tunes nothing;
- that S3r3 or any variant other than W2 is maze-ready.

**The trail setting was chosen after two changes of rule,** each made after seeing data. The selection used
mazes 0-255. The report mazes were opened once, after every choice was frozen.

## Records

- Stage records and per-maze arrays: this folder.
- Diagnoses: `development-records/`.
- Reviews: `docs/reviews/20261002-E3b-0-*` and `docs/reviews/20261003-E3b-0-*`.
- Decisions: D175-D179.

## Corrections
- None yet. Those to the interim report are in `INTERIM-REPORT.md`.
