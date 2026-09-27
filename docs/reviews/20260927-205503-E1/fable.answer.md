# Review: E1 navigation primitive, design v1

The concept is right: one target, reach count, respawn, scripted control first. The parameters and gate as written do not yet test navigation. I ran nothing; the numbers are hand calculations from the code.

## Must change

1. **The odour does not reach the wey, so Task N is mostly blind search.**
   - `gaussian_blur` truncates at `ceil(3σ)` = 6 cells (`world.py:59`). With radius 1.5, the signal is exactly zero beyond about 7.5 cells along an axis, and about 3e-4 of peak at 8 cells diagonally.
   - D = 8, so every approach starts with no signal. Only about 23% of the 22×22 interior has signal above 1% of peak.
   - A blind mover sweeps a 3-cell swath over 105 cells of travel, about 65% of the arena per episode. I estimate blind at about 0.65 targets per episode and S at about 2, with most of S's time spent searching.
   - Fix: pilot σ in {2, 3, 4, 6} on tuning worlds, and state the patch amount and sensing scale so the peak stays under the 5.0 input clamp.

2. **Energy physics is still running.**
   - At full speed the cost is 0.035 + 0.02 × 0.35 = 0.042 per tick, so a wey that does not eat dies near tick 286 of 300.
   - The corpse pellet then enters the sensed field (`FOOD + PELLET`), and eating on reach couples score to energy.
   - Moving a patch also needs a rule for the energy ledger.
   - Fix: declare zero drain and `eat_rate` 0, or the equivalent. Also set `food_patches` and `hazard_patches` to zero; with one wey, `food_scales_with_headcount` scales the map by 1/20.

3. **The gate statistics need replacing.**
   - A ratio against a baseline near zero breaks the roadmap's own scoring rule on near-zero denominators.
   - "Median time to reach" is censored, because only reached targets have times.
   - "Best baseline" does not say whether K counts.
   - Fix: use a paired difference in counts, plus the score as a fraction of an oracle that steers at the true target position.

4. **The baselines are weaker than the navigators and partly not implementable as described.**
   - No scripted policy has random turns: `LevelKinesis` uses a constant turn, not random ones as the design says.
   - `ScriptedBrain` reads only food, so "turning at walls" needs collision inputs. `Straight` slides along walls and jams in corners.
   - S and M are tuned while the baselines are fixed. Tune a blind family (speed × constant turn, plus a wall-follower) with the same `tune_batched` and worlds.
   - About 26% of uniformly placed targets lie within reach of a pure wall-slider. Keep targets at least 3 cells from walls.

5. **The 04a gate has no numbers and no proof of sensor use.** An evolved champion can beat the listed baselines by sweeping better.
   - Require the score to fall to the blind level under the existing `mirrored` or `constant` probes.
   - Add a path-efficiency measure: straight-line distance over path length, per reach.
   - Add a generation-0 baseline, which the standing rules require.
   - State the number of runs and the pass rule.

## Should change

- **Pairing:** draw each world's target sequence in advance, with consecutive targets at least D apart. Rejection against the wey's position makes targets depend on the strain.
- **Replay tolerance:** T0's 1e-4 bound is for a continuous score at 200 ticks. Task N is an integer count at 300 ticks, where one flipped reach changes the score by 1. Declare a new tolerance, or claim exactness only under `replay_mode()`.
- **Scripted gains:** 02's stereo grid runs to k = 8192, which is bang-bang. Also report S at gains a brain can plausibly reach (my guess is k ≤ 32).
- **Training fitness:** counts at generation 0 will be mostly zero. Declare bounded shaping, such as fractional progress to the current target, and remove it from the benchmark.
- **M's description:** `MemoryKinesis` has one tick of memory, not a running average. Say which you mean.
- **Id ranges:** use separate ranges for the task pilot, the gate and the 04a hold-out, with gate worlds used once.

## Minor

- "T0" and "T1" mean both the roadmap foundations and 02's tasks. Disambiguate.
- Arena side is 24 with one wey (`min_side`), the same as 02's T0. Confirmed.
- State which calibrated gains are used.

## Open questions

1. **One wey per world:** yes. Crowding belongs to E3.
2. **Channel:** keep the food channel. E3 routes A and B observations to separate copies, so distinguishing them is the assembly layer's job. Record the input as "goal odour, left and right" in the saved module.
3. **Scoring:** count over a fixed horizon as primary, with path efficiency and first-target success as secondary.
4. **Thresholds:** set them from a pilot on tuning worlds plus the oracle and blind references, and fix them before the gate worlds are touched.
5. **Moved targets:** respawn after a reach. Targets that move during approach are pursuit, which is stage 05.
6. **E3 risks:**
   - E3's module follows trails, which are narrow, decaying ridges, not a static Gaussian blob.
   - Odour passes through walls, and E1 has no interior obstacles.
   - Add a non-gating probe on a line-shaped source.

## Over-built or missing

- **Bridge 1:** defer it until E3 runs. It is not on the path to the organism.
- **Event ledger and module save:** fine if they stay as counters plus the existing bundle.

E1 design: proceed to v2