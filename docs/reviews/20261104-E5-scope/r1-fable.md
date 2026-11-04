Verdict: **fix then proceed.** Task H as "Task N with a living target" is the right minimal step, and most of the note's claims about the code check out. But the note misses four things the engine already does that will bite a 1-versus-1 hunt, overstates the inert graft's exactness, misreads what `coevolve.py` offers, and puts a training-only shaping term into the benchmark score.

## Claims checked against the repository

| Claim in the note | Status |
|---|---|
| Per-swarm brains, automatic biting, corpse pellet, ledger, no friendly fire, half the damage reaches the attacker | Correct (`wormwars/world.py:1141-1229`, `config.py:236-241`) |
| Task N: one swarm of one wey, sensing-only scent, pre-drawn centres, event table, energy off, 300 ticks | Correct; the one-swarm rule is enforced at `wormwars/world.py:289` |
| Scripted controllers exist as named | Correct |
| E4s-1 7.14; E1 8.68 and 98.7%; E4s-1 16.6 GPU-hours; E4s-0 about 300 episodes/s | Correct (306/s at 1×1024, 863/s at 4×1024) |
| E2's and 04a's champions "2.0 to 2.8" | Slightly low: E2d's band is 1.90-2.50 for medians, best champions 2.64, 2.84, 2.92 |
| D026 is the source of "0.1 to 0.3% from biting" | Wrong pointer. D026 is the flank retraction. The biting share is in `docs/RESULTS.md:508-520` (01's results). The lesson is right |
| D103 gives "the unfinished leg's progress as Task N's tie-break" | Misread. D103 defines progress as a *training* shaping term, "Training only" (`DECISIONS.md:3167-3169`). The roadmap's scoring rules say shaping is removed from the benchmark |
| The inert graft "behaves exactly as before" | Overclaimed. E4s's own test says up to rounding, not bit-exact: 1e-5 on the CPU over 100 ticks, 1e-4 on CUDA over 300 (`tests/test_graft.py:105-109`, `docs/E4s/DESIGN.md:214`) |
| `coevolve.py` offers "a hall of fame and a frozen opponent suite" | Half right. The hall of fame is reusable. The suite is random initialisations at spread scales, not competent prey (`coevolve.py:256-283`), and the match score is surviving-energy difference for 50-200-wey swarms (`coevolve.py:178-180`). Neither fits the stage 05 gate |
| D385 records the owner's choice | Not yet written; DECISIONS.md ends at D384 |
| Task N's σ, A, truncation | Unnumbered. E1's gate ran σ = 6, A = 1, R = 1.5, D = 8 (not the config default σ = 3). Pin σ = 6 |

## What the engine already does that the note does not see

These are the most likely causes of a failed positive control, and all four are in code the note says it reuses.

- **Bodies are obstacles.** The collision signals sample WALL plus BODY (`world.py:885`). The hunter's ALM, AVM and PLM neurons will fire on the prey's body. Every reused navigator evolved its collision reflexes on walls alone. A zero-shot hunter may turn away from the prey at the last cell, and the note would read that as a scent failure. The WallFollower "blind" hunter is also not blind to the prey for the same reason.
- **Crowding resists and pushes.** Each wey splats 1.0 at three body points, blurred, and movement is slowed up to 60% and pushed 0.10 cells per tick down the density gradient above a threshold of 0.8 (`world.py:1021-1037`, `config.py:120-124`). Against a max speed of 0.35, the hunter closing on the prey is slowed and shoved away from it. This was tuned for melees of hundreds. It directly opposes "holding contact" for the bite rule and must be in E5-0's calibration.
- **A kill leaves a sensed corpse, and may end the episode.** At zero energy the prey dies and leaves a pellet of 6.0 in one cell (`world.py:1231-1244`). The hunter's food channels sense FOOD plus PELLET (`world.py:836`), and with Task N's eat rate of zero the pellet persists all episode. A pellet of 6 next to a prey scent whose peak is 1 is a strong local trap for a stereo steerer. Also `done()` ends a two-swarm world once either swarm is empty (`world.py:1349`). The hunt task must remove the pellet at capture, book it and the respawned prey's energy and body mass in the ledger, and override `done()`. Otherwise T0's per-tick ledger check fails.
- **The prey has no food to sense.** The note says the prey "senses the world as it did where it evolved". In Task H as proposed there are no food patches, so 02's champions receive nothing and move on their default gait. If you add food to make them purposeful, the hunter smells it through the shared FOOD field. A per-swarm food-sense mask is needed either way, and `food_sensing` is world-level, so a T1 (mono) champion would get stereo input it never had (`exp02/grid.py:60`).

Two smaller points. Under Task N's settings pheromone deposit is zero, so ADL receives nothing from the hunter; the note's worry about ADL only applies if deposit is turned on. And the head is armoured at 0.25, so a head-on approach kills about four times slower than a flank; time-to-capture for a static prey will vary with approach angle, a geometric artifact to log.

## Answers to §7, questions 1 to 5

1. **Scent.** Gaussian on the hunter's food channels, sensing-only, σ = 6 as E1's gate ran it. Not the pheromone trail first: no reused navigator ever used ADL, so transfer would be zero, and the trail's gain is a fresh calibration. Keep the trail as a later level or an E5-1 option, not "both" at the start.
2. **Capture.** "Reach" first, as the exact Task N rule, so H1-reach with a stationary prey reproduces E1's gate numbers. That is a free equivalence test; register it as one. Then "bite", with the prey's energy set from the positive control's measured dwell so that a held contact kills in about 10 to 20 ticks. Remove the pellet at capture and respawn. Corpse eating belongs with energy on, later.
3. **Route.** A closed loop through 3 to 5 waypoints drawn per world id from Task N's target stream, so no loop repeats across episodes and "unseen maps" stays "unseen ids". Do not fix 0.25, 0.5 and 0.75 now. Sweep prey speed from 0.1 to 1.0 of the hunter's max in E5-0 with the scripted hunter, then set the ladder from where it falls off.
4. **H3.** The frozen suite should hold prey that move under Task H's inputs: the navigators chasing their own targets, which needs per-swarm targets. 02's champions with no food are H2b-class movers, not competent prey; label them so. No bite-back at H3. It changes the energy game, which is exactly where 01 went wrong, and belongs to coevolution. Keep ADL, ASH and collision inputs live but add a masked-input probe per reused organism.
5. **Inert graft.** Sound in mechanism, wrong in wording. Say "within E4s's declared tolerances" and add E4s's score-level check (each genome's mean within 0.05 over 256 worlds). The cleaner alternative is a per-swarm current width in `_build_current` (`world.py:941`), which avoids re-embedding every prey genome, but it is an engine change needing its own equivalence check. The graft is the lower-risk path for E5-0.

## Reuse: wrong, and missed

- **Wrong:** the frozen suite and match scorer in `coevolve.py` (above). Reuse the hall of fame and the paired schedule only.
- **Wrong:** D103's progress term in the score. Benchmark is captures; progress is training shaping only, and with a moving target it must be redefined (distance at leg start versus at last tick, clipped).
- **Missed:** E1's scent probes (mirrored, mean, swapped) act on `_sensed_food` and transfer to the prey scent for free. The mirrored probe is the per-hunter cue-dependence test; add it to E5-0 beside the blind controls.
- **Missed:** build H1-reach from `task_n_config` plus a hunt flag, so the resolved-config hash can be compared with E1's gate record under `registration.py`.

## E5-0: controls, decision rule, cost

Controls are nearly enough. Add the mirrored-scent probe and a collision-masked probe for the reused hunters. Fix these rules in a short committed plan before it runs, as D262 did:

- **Solvable:** H1-reach matches E1's gate within its tolerance. H1-bite: the scripted hunter's lower 95% bound over 1 024 worlds is at least 3 captures per episode. H2: at least 2 at the slowest ladder speed.
- **Too easy:** the best blind control's mean is at least a quarter of the positive control's at that level.
- **Falls off:** the first level where a reused hunter's lower 95% bound drops below the best blind control's upper bound.

The cost estimate is plausible. A 306-neuron brain at 32 substeps over 300 ticks for two weys is about 2 GFLOP per episode, so tens of episodes per second on a CPU over a batch of 1 024 worlds is reasonable, and a few thousand episodes per controller and level is an hour or two. Measure it before committing a figure.

## Risks the note should name

- D026's lesson is half applied. Scoring captures directly is right, but the hunter still gains energy from bites (start 12, max 40, so there is headroom). Log it, and keep the hunter's energy out of selection.
- E2d's plateau means the N2-only hunters will fall off at H1. The interesting zero-shot case is E4s-1's grafted navigators, which were evolved at σ = 6 and A = 1. Keep those values or the comparison is against a different task.
- E4's fragile modules matter for E5-1, not E5-0: if hunters are evolved from a grafted seed, pin or scale the graft's mutation as E4s-1 did, or the comparator breaks before anything hunts.

## Fixes before proceeding

1. Add the four engine facts above (bodies as obstacles, crowding, corpse and `done()`, no food for prey) to §2 and §5, each with its new-code item and test.
2. Replace "exactly" for the inert graft with E4s's tolerances and score check.
3. Correct the `coevolve.py` reuse claim.
4. Take progress out of the score; keep it as training shaping only, redefined for a moving target.
5. Pin σ = 6, A = 1, R = 1.5, D = 8, and cite E1's gate record.
6. Point the biting share to `docs/RESULTS.md`, write D385 or mark it pending, and widen the champion range to 1.9 to 2.9.
7. Fix E5-0's decision rules in numbers before it runs, and sweep prey speed rather than fixing three values.