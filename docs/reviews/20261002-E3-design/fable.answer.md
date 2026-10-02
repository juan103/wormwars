**Verdict: revise.** The staging and the overall shape are right, and nothing needs a rethink. But the latch as specified will not switch, the gate has a bound problem, and one control is missing; fix these in a v2 before pre-registration.

## Must-fix

1. **The latch does not flip on a one-tick pulse of weight 1 (task "Visit signals", Stage 1 "The latch").**
   - The fixed points (±1.915) and the threshold (0.533) are correct. But from the opposite settled state a unit input needs about 3.06 τ_q to cross q = 0 (my integration).
   - The design's own source says so: `astra.review.md:460` gives 3.08 τ_q and states "A one-tick pulse is insufficient". Even at τ_min = 0.5 that is about 1.5 ticks.
   - Change: make `at_a`/`at_b` a level signal while the head is inside the radius, or raise the drive to about 3 or more (roughly 0.7 τ_q to cross). Register τ_q, and test it in the real integrator at 32 substeps, including grazing passes of 1-2 ticks.

2. **The latch starts on its unstable point (Stage 1).** `Brain.initial_state` is zeros, and q = 0 is the unstable fixed point, so until the first visit neither module is properly selected. Define the initial mode: a start pulse from the world, or a small bias with its asymmetric thresholds (0.533 ∓ b) accounted for. Fix the starting goal at A; a per-world draw is unsolvable without a cue.

3. **The gate needs the bias shift, and `b_max` = 2.0 limits it (Stage 1 "The gate").**
   - The first variant (common input only) saturates a module in both latch states, since q's output is ±0.957. Only the bias-shifted variant works.
   - It needs a comparator bias of about 0.957 g, so g ≤ about 2.09, not 3 (`config.py:40`).
   - At g = 2 the inactive pair sits near −3.83, with slope about 0.002, so residual K_D is about 0.07 against 36. That is adequate; state these numbers and register the K_D ratio.
   - Also register the inactive module's net turn offset: once w_o mutates in Stage 3, a saturated pair gives a turn bias that switches with the latch.

4. **Add the positive control for the artefact itself (Stage 0).** The roadmap says each artefact needs "E3's own positive control" (`ROADMAP.md:38-39`). S-shuttle tests the task, not L1.
   - Add L1 with a scripted switch: one L1 on the carrier whose noses the world feeds the current goal's scent. This is Stage 1's true ceiling and separates a module failure from a latch or gate failure.
   - L1 qualified at a 5.10 lower bound, only with turn command 0.2, on separations of at least 8. D_AB of 12-18 is the hard tail: at 18 cells the far scent is about 0.011 of peak and sits at the truncation edge (ceil(3σ) = 18).
   - Give S-shuttle's k. E1's 8.51 is k = 256; a gain of about 32 scores 5.63.

5. **The N2 interface collides with live signals; drop it from E3a (task "The interface").** ALML, ALMR and AVM already carry `collision_front_*` (`configs/interface.yaml:47-49`), and the wall ring makes those live. E3a uses the carrier only, so move the N2 interface to Bridge 2 or E4.

6. **Stage 2 and B-task cannot start "from random" at E4s-1's mutation scale.** In E4s-1's R arm no edge changed sign in 1 000 generations at the module's σ of 0.02; the smallest |w| was 1.73 from 3.0.
   - Register the initial distribution and a mutation scale that can cross zero.
   - Add random sampling as a comparator: E2's floor fired, and the selector has under 10 parameters.
   - Run a generation-0 census of random selectors first, as E4s-0 did for populations.
   - B-task needs its mask, size and budget stated.

7. **Stage 3 is under-specified and the budget is not itemised.**
   - Say which parameters evolve. If "everything" includes the silent worm's 302 neurons, it becomes N2-host evolution, which the design says it avoids. The carrier's turn bias is a first-order variable (E4s-0).
   - Say how each module's component skill is evaluated with the latch present, and what Stage 3's question is. Otherwise label it descriptive.
   - The carrier still steps about 311 neurons, so it costs what N2 costs. E4s-1 used 16.61 GPU-hours for 80 runs at 300 ticks, about 0.2 h per run. At 600 ticks, 12 hours buys roughly 28 runs across Stage 2, Stage 3, B-task and pilots (my estimate). Give the run counts.

8. **Smaller specifications to pin down.**
   - `graft.py` hard-codes `food_left`/`food_right` in its noses and probes and takes one module per graft. Two L1 copies need new neuron names, so the organism carries L1's parameters, not the hashed `module.json`. Say so.
   - Geometry: Task N's arena has `min_side` 24 (`freeze.json`), which I read as a 16×16 box for centres. A spawn at least 8 from both sources with D_AB of 12-18 forces them to opposite sides near the walls. Check feasibility and add a maximum spawn distance.
   - Add the carrier's own blind circle (forward 1.0, turn 0.2) to the blind baselines.

## The seven questions

1. **Staging:** right. Keep trails and mazes out of E3a. The amendment must say the roadmap's gate ("unseen branching mazes, better than the seed design") is not met by E3a.
2. **Task:**
   - Separate channels: fine.
   - Pulses: firing regardless of the goal is good, because it makes the latch self-correcting. Make them levels (item 1).
   - Horizon: 600 ticks is plausible, at about 58 ticks per leg from L1's 5.18 targets in 300.
   - Starting goal: fixed at A.
   - Geometry: I would use D_AB of 8-14, or justify 12-18 with item 4's control.
3. **N2 interface:** avoid an N2 host entirely in E3a (item 5).
4. **Latch and gate:** sound in tanh units with items 1-3 fixed. Common-mode saturation is the standard way to gate without multiplication. I know of no better design at this size; Astra's suggested preference-based arbitration selector is an optional third arm.
5. **Gates and baselines:**
   - The no-latch and one-module controls are fine; I expect about 1 visit each.
   - B-shared is well posed but nearly the same organism (7 neurons against 9, the gate moved from comparators to noses). Expect a tie and register it as descriptive; it cannot say anything about modularity.
   - Bound Stage 1 against the L1 scripted switch, not S-shuttle.
6. **L1 rather than run 10:** agreed. Run 10's module scores 0 alone, and 10 of 16 evolved modules do; it is a whole-brain artefact.
7. **Trivial failures and successes:**
   - Failures: items 1-3, and Stage 2 stuck by mutation scale (item 6).
   - Trivial successes: a slow leaky trace (τ up to 20 against legs of about 60 ticks) can pass as a latch, so register a hysteresis or hold test with pulses withheld. A switching turn bias from the saturated module is another (item 3). A blind circle through both discs is possible in a few worlds.
   - A purely reactive policy cannot solve the task: "follow the weaker scent" oscillates at the midpoint. That is good.

## Reuse and contradictions

- **Contradiction:** the one-tick pulse, against `astra.review.md:460` (item 1).
- **From Astra's review, line 472-474:** log both modules' proposed turn commands at every tick, since a high score can hide an unused module. Define repeated pulses, simultaneous set and reset, and hysteresis at the radius boundary.
- **From E4s-1:** part of M − N was not stereo use (1.26 targets kept with the noses on the mean). Apply the same mean-nose probe per module here. Declare every per-world array's dtype; the int16 cast lost the motor audit trail.
- **From E2d:** 8 worlds rank close genomes poorly. Stage 2's selection needs more worlds, or large effects only.
- **Reuse:** Task N's `_build_targets` and event ledger extend naturally (alternate between two centres); the self-edge test exists (`tests/test_graft.py:167`).

I did not run anything, did not check the E2 hash-equivalence claim, and read only the latch sections of the literature reviews.