## 1. Verdict

**Fix then run.** The staging, update order and failure branches are sound, but several rules as written can make E3b-0 pass while being uninformative. I ran nothing: the engine claims come from reading `world.py`, `fields.py`, `config.py` and `wormwars/e3/`, and the arithmetic is my own estimate.

Fixes, in priority order:

1. **Decouple λ from μ in the trail grid.** By my arithmetic the grid misses, or only touches at one corner, the region that can work (§3, search grids).
2. **Make diffusion symmetric.** "A fraction δ equally to its open neighbours" is a random walk whose equilibrium is proportional to degree. A 3-wide corridor settles to roughly 3:4:3 across its width, a built-in centre ridge on every trail. Use flux form instead: x_i += (δ/4)·Σ over open neighbours of (x_j − x_i). It also conserves mass, and its equilibrium is flat.
3. **Say which trail constants the (c, H) search uses.** Conditions 2 and 4 need the shared-trail follower, but the constants are chosen afterwards. Either pin provisional constants, or restrict the (c, H) rule to trail-free controls and move condition 2 to the trail search.
4. **Put a threshold or a branch on shared − own.** Criterion 3 requires shared − none and own − none, but only reports the one contrast that is a peer effect.
5. **Give the polarity test a null.** The follower falls back to wall following, which finds any dead end of a tree anyway. Run the same placements with the trail removed and with a no-polarity trail (λ = −ln(1 − μ)), and select on the difference.
6. **Change the variant selection rule.** "Highest seed score" will pick W2, the most engineered variant (§3, maze-ready).
7. **Add the missing pins** (§2).
8. **Check the generator's dead-end count on the CPU before anything else** (§3, mazes).
9. **Pin the unstated numbers:** the scent amplitude A, W1's gain, W2's bias, and criterion 6's power level and scaling rule.

## 2. Pins

All of D173's pins are present, though the range pin is only measured: the inequality is not a constraint on the grid. From the two design-v2 reviews, these are not carried:

- **The free sabotage test (my pin 2).** Before a wey's first B visit, own-only and none must give bitwise-identical trajectories on the CPU. The plan states the fact in §3c but has no test. It holds exactly for the scripted follower; for the seed, any difference measures leakage through the gated-off module, which is worth knowing.
- **The seed under own-only (my review, §4).** Criterion 3 reports only shared − none for the seed.
- **Replay and scramble (Astra's pin; my pin 9).** Criterion 3 requires each to "remove information in a scripted example", but the plan never defines donor selection, donor timing, the scramble, or Astra's route-overlap measure. Only the timing appears, in criterion 5.
- **First-leg times as the primary peer measure (design v2).** They are now only reported. On first discovery own ≡ none, so shared − own on the first-B time of later discoverers is the cleanest peer contrast available. It is the natural endpoint for fix 4.
- **Compute accounting (rule 8; Astra).** Presumably implied by "E2's stage frame"; say so.

## 3. The numbers and rules

**Update order.** It is consistent: the goal switches in step 4, the timer resets in step 5, so the first deposit is d₀ on the trail of the source just visited. Two gaps:
- The linearity test "shared = Σ own, bitwise" is tautological if shared is defined as that sum. If it is compared with a separately evolved single field, it will fail bitwise in float32. State which, and give the second a tolerance.
- The shuttle is not in `scripts/e3_equivalence.py` today. Its reference must be produced by the extended script on 84ff98a's engine; say that.

**Occlusion.** It is correct against leakage: bilinear reads from an open cell never reach across a 1-cell wall.
- **A side effect to declare:** a nose 0.78 from the head in a 3-wide corridor is zeroed often, so one nose at 0 and the other on the trail is a strong, trail-dependent wall-avoidance signal. Report the share of ticks with an occluded nose. This reinforces that trails on/off is not a peer contrast.
- **The segment test** must be an exact grid traversal, not endpoint plus midpoint.
- **A second test is needed:** an unoccluded nose reads bitwise the same as before, or the occlusion test can pass vacuously.

**Deposit and polarity guide.** The guide is right, but two things are loose:
- **"On-trail" is undefined.** If it means "reads at least 0.005", the 90% range condition is circular. Define it geometrically, for example cells on the A–B route.
- **"Ages up to the horizon" has no aggregation.** At age H everything has evaporated. Pin the ages, for example 1, 2 and 4 oracle legs.
- **The polarity test** also needs the trail's age and contributor count, which leg time is meant, and a heading jitter: exactly anti-aligned on a symmetric ridge gives L = R.

**Maze-ready variants.**
- **Selection:** W2 is a wall follower and solves trees, so it will likely win on score. The seed then sits near the blind ceiling with trails possibly irrelevant. Choose the earliest (least engineered) variant that meets criterion 2. Add a branch for the seed's shared − none lower bound at or below 0.
- **The count:** with P ∈ {40, 80} there are 7 variants, not 5. The tie order needs P.
- **W2's bias** must be stated relative to the carrier's existing 0.2 turn: replace it or add to it.
- **The generator:** from memory, randomised depth-first search gives about 10% dead ends, so about 2–3 at c = 5. A, B and up to 4 spawns may not fit, and A–B distances often exceed 2c. Measure the dead-end count and rejection rate, and state the redraw rule. If that is confirmed, use Wilson's or Kruskal's algorithm (about 30% dead ends); otherwise the mazes barely branch.

**Search grids.**
- **(c, H):** conditions 2 and 3 are not binding. A wall follower's tour is about 550 ticks at c = 5, so about 4 visits in 1 200 ticks against the oracle's roughly 15. The rule will likely stop at (5, 1 200); be content with that being the "branching maze".
- **Trail constants:** three constraints bound the feasible region.
  - **Turning round:** k = 32 needs a slope (λ − m) of about 0.015 per tick or more, where m = −ln(1 − μ). At μ = 0.002, f = 1.5 the slope is 0.3% per cell, and a U-turn takes about 500 ticks.
  - **Reach:** a trail spanning an 80–140-tick leg inside the 70× window needs λ of at most about 0.027–0.045.
  - **Saturation:** 8 weys revisiting sum to about (visit rate / m) × one pass. That is about 16× at μ = 0.002, far over 0.35, and about 3× at μ = 0.01.
  - **The result:** the feasible region is roughly μ ≈ 0.01–0.02 with λ ≈ 0.02–0.04. The grid reaches it only at (μ = 0.01, f = 3). Use λ ∈ {0.01, 0.02, 0.04} × μ ∈ {0.005, 0.01, 0.02}, and add a branch for a winner on the grid's edge.

**Exit criteria.**
- **Criterion 2's headroom is too thin for criterion 6.** A seed at 0.8 of the oracle leaves at most 25% improvement, which equals the allowed minimum detectable effect. Require headroom of at least twice that effect.
- **Later-trip visits are confounded.** A wey that finishes its first round trip sooner has more time left. Use a rate per remaining tick, or say it is a total effect.

**Power.**
- A minimum detectable effect needs a stated power and α; the plan gives only "90%".
- "Scaled to E3b's units" needs a rule; use the coefficient of variation.
- Say that the assumption comes from E3a's 8 single-wey, open-arena runs, so it is weak.

**Failure branches.** They are adequate. Add three: shared − own null, the seed's trail effect null, and a trail optimum on the grid's edge.

## 4. Feasibility

**Yes on both counts.**
- **Engine:** the work is substantial but each piece is straightforward: per-wey goals and ledgers (the shuttle is hard-wired to one wey per world), a side override in place of `arena_side`, interior walls, a separate trail tensor, masked diffusion, occlusion, and the BODY term removed from `obstacle`. The risk is the bitwise task-off equivalence, so keep every change behind a flag.
- **Memory:** about 285 MB at c = 8 for the trails, perhaps 1 GB with diffusion buffers.
- **GPU time:** the scripted searches are small, and most can run on the CPU. Only the seed's variant search, the report and the timing at 4 096 × 8 need the GPU. I expect well under 1 GPU-hour; the cost is engineering time.