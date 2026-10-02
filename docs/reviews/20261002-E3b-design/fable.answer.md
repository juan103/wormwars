## 1. Verdict

**Proceed to E3b-0's plan, with the fixes below carried into it.** The staging is right. E3b-1 as sketched is not yet a design: its budget, two of its controls and its gate reading need E3b-0's numbers and a v2 first. I ran nothing; the engine claims below come from reading `world.py`, `fields.py` and `config.py`.

## 2. The seven questions

1. **Staging and budget: the staging is right, but E3b-1 does not fit as sketched.**
   - E3a's Stage 3 took 1.47 h for 8 runs × 32 genomes × 16 worlds × 600 ticks × 500 generations with one wey.
   - Eight weys and 1 200 ticks is 16× the wey-ticks, so about 23.5 h for one tuned arm by linear scaling. The no-trails arm at "the same budget" doubles it to about 47 h.
   - A cut of about 3× is needed (weys, worlds per genome, generations or horizon). E3b-0 must measure the real rate at the colony composition, since larger batches may not scale linearly.
   - Evaluation is cheap: 256 mazes × 8 weys × 1 200 ticks is under a tenth of one training generation.

2. **The gate: tuned seed against seed on unseen mazes is an acceptable reading, but insufficient alone.**
   - E3a's Stage 3 already gained +2.36 in the open arena, so "better" could be generic locomotion tuning with no trail use.
   - Add a 2×2 at evaluation: trail-evolved and no-trail-evolved colonies, each tested with trails on and off.
   - Do not evolve a selector from scratch; E3a's 1 of 8 answers that.

3. **Wall reflex: wall sliding yes, reflex not until E3b-0 shows a jam.**
   - The jam premise is unverified. Heading updates before the blocked check (`world.py:950`, then 973-979), so a blocked wey keeps rotating at the carrier's 0.06 rad/tick until free. That is slow (about 26 ticks per 90°), not a jam.
   - `blocked` can never fire today: `proposed.clamp(1.02, side − 1.02)` keeps heads off the ring, so the boundary already slides per axis. Per-axis sliding at interior walls matches that behaviour; "stay in place" would be the new one.
   - If a reflex proves necessary, engineer and label it, and give it to every arm and the seed. Note that `collision_*` reads WALL + BODY, so a reflex also reacts to peers.

4. **Local scents: keep them, short-range and by path distance.**
   - Without them a visit needs a blind hit on an R = 1.5 disc.
   - Pin the summed trail + scent level inside L1's qualified nose range (0.005-0.35 after scaling) and rerun the component test at trail levels. A deposit of 1.0 per tick per wey can saturate the noses.

5. **Trees only for E3b.** Loops add route choice (the double-bridge question), which is a different experiment and budget.

6. **Literature: yes, a bounded and verified check before E3b-1's pre-registration.** It need not block E3b-0's engine work. The control design (replayed and scrambled trails) is where prior art matters, and D143 was written for this situation.

7. **Own-trails control: use exact per-wey fields, not a mask.**
   - They are cheap: 16 channels × 33² × 4 096 worlds is about 285 MB, and a grouped 3×3 convolution is small beside 313 neurons × 32 substeps.
   - Diffusion is linear, so shared is the sum of the per-wey fields. That also gives a **peer-only** condition (shared minus own) for free; add it.

## 3. What would make it uninformative, unfair or infeasible

- **Replayed trails on the same maze are not decoupled.** A tree has one A-B route, so another episode's trail marks the correct route. The control tests timing, not information. Replay from the same walls with different A/B placements instead. "Displaced" scrambling must be defined so trails do not land in walls.
- **Bodies are a second peer channel.** Crowding (`crowd_resist`, `crowd_push`) and BODY in the collision signals stay on in every arm, so "no trails" is not "no peer signal". Turn crowding off and take BODY out of collision, or declare it.
- **Eight weys spawned in one 3×3 dead end** exceeds `crowd_threshold` at once.
- **Deposit decay against evaporation.** For one wey leaving A, the field at path distance x is s(x/v)·λ^(T − x/v). Unless the deposit timer decays faster than evaporation, the A trail rises away from A and leads followers the wrong way.
- **The default `pheromone_decay` of 0.93** (half-life about 10 ticks) is useless for legs of 100+ ticks. The trail constants are free parameters and must be fixed before E3b-1.
- **Own trails may make peers redundant.** After one round trip a wey has laid both trails itself. The peer benefit sits in the first one or two legs, so first-A and first-B times by discovery order should be the primary peer measure, not visits over the episode.
- **The seed has no exploration mechanism.** If the seed scores about 0, the gate is trivial or fitness is flat.
- **The geometry is inconsistent.** A 5 × 5 grid of 3-wide corridors with 1-cell walls is 21 × 21; 33 × 33 is 8 × 8. At 0.35 cells per tick, 8 × 8 gives legs of roughly 230-340 ticks even for an oracle, so few journeys in 1 200 ticks.
- **`arena_side` returns 24 for 8 weys;** the maze needs its own side.
- **Wall masking:** declare whether masked diffusion conserves mass. Bilinear noses beside walls read lower trail, which is an implicit wall repulsion confounded with trails being on.

## 4. What E3b-0 must establish before E3b-1 is pre-registered

1. Each engine change passes its equivalence check with the task off, and sliding is a flag.
2. The task is solvable and trail-dependent with scripted controls: oracle well above the scripted follower, which is well above the blind baselines; and the follower ordered shared > own-only > none, with the size of the gap.
3. The seed's score in the maze is well above the blind baselines and below the follower, with and without trails and with and without the reflex, so there is headroom and a gradient.
4. The trail constants, maze size, horizon and colony size are fixed, with L1's gains verified at trail levels.
5. The cost per rollout at the real composition is measured, giving a projected E3b-1 of at most about 24 h with reserve.
6. The peer effect in the scripted follower is large enough for the planned number of runs to detect. If it is not, say so and redesign before registering.