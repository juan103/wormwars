**Verdict: fix then proceed.** The plan is faithful to the scope and to both round-1 reviews, and the ghost's bit-exact construction holds up against the engine. Two things need changing before anything runs: the E_prey calibration can return zero, and one of my own scope claims, crowding, is wrong for a two-wey world. Several rules are loose enough to be argued after the data. Note that the code is not absent: `wormwars/e5/hunt.py`, `prey.py` and the three world hooks are in the working tree, uncommitted. I read them to check the mechanics, not as a code review.

## What I checked in the repository

| Claim | Status |
|---|---|
| E1's gate settings, ids from 996 201 000, run seed 1 100 001, σ = 6 from the freeze | Correct |
| The arena is Task N's with two weys | Correct. `min_side` 24 dominates both headcounts, so the ghost's map and spawn draws are Task N's |
| The spawn hook takes the single-swarm angle branch | Correct, `world.py:472-477` switches on the hook's value |
| Respawn at D − R never skips a centre in the ghost | Correct. The code skips only on strictly less than 6.5 |
| The ledger with no pellet balances | Correct. Removed books energy plus mass, respawned books E_prey plus mass, alive count unchanged |
| Ghost runs without combat | True in the code, absent from the plan. Say it: combat samples body points, not the body field, so bites on a bodiless prey would still land |
| E2d's 47, E4s-1's 16 M runs, the carrier's turn 0.2, D262 as the model | Correct |

## Findings, by your questions

**1. Faithfulness.** Every round-1 fix is in. Three deviations from the scope: the head-point centring is labelled; the respawn distance of D − R instead of D is not labelled; and the reused-hunter rule dropped the reliability condition the scope carried from Astra's table. Label the second, restore or label the third.

**2. Mechanics.** Centring on `pos` is the right call and is forced: a mid point computed as head minus 1.2 cells in float32 cannot reproduce a centre bit for bit. The consequence to name is that the scent peak sits on the armoured head, so a scent follower meets the head first unless it arrives from behind. Log the approach bearing at first contact per life, so kill-time spread at H1-bite is explainable.

Crowding is inert here, and the scope said otherwise. Each body point splats 1.0 at its nearest cell, the blur is a normalised 3 by 3, so a cell's density is the count of body points in its neighbourhood divided by 9. Two weys have six points, so the maximum is 0.667, below the threshold of 0.8. Resist is 1 and push is 0 on every tick. Bodies also never block movement, since `_resolve_move` checks the wall only. So the pin never fires, the pin-push log will read zero, and ghost against reach measures collision input alone. Add a dated correction to SCOPE.md §2, which says crowding "can also move a `Stationary` prey". That sentence came from my review. Keep the pin as a guard with its expected zero written down.

**3. Calibration.** E_prey as written can be zero. The oracle drives at full speed through a prey that cannot stop it, so per pass its bite cell is on the body for roughly half the contact ticks, and the median over contact ticks is a coin toss between zero and the flank value. A zero E_prey makes `_reap` capture at tick 0 and every tick after. The per-tick damage is also fixed by engine constants, so the calibration is a check, not a measurement:

| Contact | Damage per tick |
|---|---|
| One flank point in the bite cell's 3 by 3 | 0.0611 |
| Two flank points | 0.1222 |
| The head | 0.0153 |

Define E_prey from a held configuration, as Astra asked: the hunter placed and held with its bite point on the prey's mid point from the side, over the 64 calibration worlds' first centres for sub-cell variety, the median over worlds. State the predicted values. Then report the three driven approaches as realised kill times at that E_prey. Add a floor: E_prey must exceed the largest single-tick damage, about 0.14, or the run stops.

The route follower's "mean speed" must be path length per tick, since a loop has no net displacement. The stall rule will fire falsely at the slowest speed, where 20 ticks is 0.7 cells of path and a U-turn has a radius near 0.1 cells. Count wall-refused moves instead, which is what the rule is for. The random walk's key is (world, life, tick) in the plan and (world, tick) in the code. Align them. The wall-following prey reacts to the hunter's body through its collision input. Label it weakly reactive, as the wall-following hunter is labelled.

The tuning settings and the rules disagree. §3.5 tunes at three settings; §6 says "each tuned for that setting" at nineteen. Either tune per setting, which is cheap for scripted grids, or fix the mapping now.

**4. Equivalence.** The bit-exact check is the right stopper, and the ghost construction should pass it. Run it on all worlds, not 256, and add the `constant` and `mirrored` probes to the compared conditions, since `_food_constant` and `_sensed_food` are reimplemented. The CUDA comparison is a platform question with no stated consequence on failure, and REPRODUCIBILITY.md records per-world divergences between platforms. Make it a reported gap, not a gate, and measure it with `navigate` on the CPU so the code and the platform are separated. Reusing the gate worlds is acceptable for an engine check, since nothing is tuned or claimed on them, but E1's pre-registration says "used once". Do the bit-exact check on E5-0's own calibration ids, which needs no reuse, and touch the gate worlds only for the gate.json comparison, noted as a second use with its reason.

**5. Decision rules.** The numbers are defensible: 0.5 is E1's registered margin, 0.80 is Astra's, and my higher H1 bar was dropped without loss because H1 will clear any floor and the sweep carries the information. Arguable points to close now:
- "too easy" needs the 0.25 flag defined as the point estimate, "best control" defined by point estimate, and the ratio evaluated only where solvable holds;
- "falls off" needs its order stated as increasing speed, non-monotone patterns reported, and the upper bound named as one-sided 95%;
- qualification at settings without probes rests on the margin alone, so label it;
- add the per-hunter ghost against reach paired difference as a reported reading with no threshold, since that contrast is the scope's reason for the ghost.

The collision-masked probe in the code zeroes the hunter's wall and own-body signals too. That asks whether the hunter needs collision input at all, which is a different question from what the prey's body does to it. Either mask the body channel only, or keep the probe and reword its question in the plan.

**6. Cost.** The probes are about a quarter of the episode count. Drop (3) presumes H1-bite is easier than H2 and H2b, which §6 disclaims, and it is data dependent. My order: generation 0 to 8 first, then trim probes, then thin H2's speeds, since those erode the plan's central question, then worlds to 256, and (3) last or never.

## Fixes before it runs

1. Redefine E_prey from a held contact, state the predicted values, add the floor.
2. Correct SCOPE.md §2 on crowding with a dated note, and write the pin's expected zero into the plan.
3. Fix the tuning-to-setting mapping or tune per setting.
4. State that ghost and reach run without combat.
5. Label the D − R respawn and the dropped reliability condition as changes from the scope.
6. Separate the CPU bit-exact stopper from the reported CUDA gap; use fresh ids for the former.
7. Close the §6 ambiguities above and add the ghost against reach reading.
8. Decide what the collision-masked probe asks and make the code match.
9. Fix the route check's speed definition and stall rule; align the random walk's key.
10. Reorder the drops.