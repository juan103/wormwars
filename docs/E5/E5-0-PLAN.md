# E5-0: Task H's feasibility check. Plan

*Draft 2, 2026-11-05, after one round of review (Astra 6 and Fable 5.1: both "fix then proceed"; every fix taken;
[`docs/reviews/20261105-E5-0-plan/`](../reviews/20261105-E5-0-plan/), with draft 1). Exploratory (not a
pre-registration), but its decision rules are fixed here, before it runs, as D262 did for E4-D's feasibility check.
CPU only, no evolution. The scope is [`SCOPE.md`](SCOPE.md), draft 2 (D385); the owner said "go ahead" on
2026-11-05. The code (`wormwars/e5/`, three hooks in `wormwars/world.py`) was written alongside this plan's review;
its tests were seen failing under sabotage (§7).*

## 1. What E5-0 answers

1. **Is the new code right?** Old engine against new, and a prey with no body (H1-ghost) against Task N, bit for bit
   (§4).
2. **Is each rung of the ladder solvable, and is it too easy?** By an observation-limited positive control, against
   stationary and blind hunters (§6). Both can hold at once.
3. **Where do the reused hunters fall off?** E4s-1's champions, E2d's 47 champions of E2 and 04a, E4s-0's comparator
   on its carrier, and generation 0, zero-shot (§5).

It does not evolve anything, and it does not test the connectome (that is E5-1's null-graph arm).

## 2. Task H, as implemented

`wormwars/e5/hunt.py`: `HuntWorld`, a subclass of `World` (as E3b's `MazeWorld` is), with task `hunt`.
- **Built by E1's own configuration** (`e1_task_n()` reproduces `scripts/e1.py`'s `config(6.0)`, checked against
  `freeze.json`'s resolved configuration: σ = 6, A = 1, R = 1.5, D = 8, horizon 300, wall clearance 3, food sensing
  scale 0.35, 32 substeps, single-strain padding on, energy off, no food, hazards or pheromones), plus `task = hunt`
  and two swarms of one wey (`hunt_config()`).
- **The hunter** (swarm 0) spawns exactly as Task N's wey (the map's spawn step places one swarm, `_spawn_swarms`).
- **The prey** (swarm 1) lives at centres of Task N's own target sequence (the same stream). Lives and sequence
  indices are kept apart: the event table is indexed by sequence index, and a skipped centre has no activation.
- **Change from SCOPE.md (1):** the prey's scent and the reach rule are centred on **the prey's position** (its head
  point, `pos`), not its mid point. A mid point computed in float32 cannot reproduce a centre bit for bit (Fable).
  So the scent's peak sits on the prey's armoured head: a scent follower meets the head first unless it arrives from
  behind. The approach bearing at each life's first contact is logged.
- **The hunter's food channels** carry only the prey's scent (A exp(−d²/2σ²), truncated as Task N's); food and pellets
  are excluded. The prey's food channels carry the map's food and pellets (none here). Every food probe acts on the
  scent as in Task N. The stationary and route prey read nothing; the wall-following prey reads its collision inputs.
  The probes change only the food channels, so they leave every prey's observations unchanged.
- **Capture rules:**
  - `ghost`: no combat (stage 0); the prey adds nothing to the body field, so it gives the hunter no collision input;
    capture when the hunter's head is within R of the prey's position, checked after the move (Task N's rule);
  - `reach`: the same, with the prey's body in the body field;
  - `bite`: combat stage 1; the prey's attack deposit is zero (a per-swarm attack scale); capture when the prey's
    energy reaches zero. All its damage is the hunter's (no other attacker exists);
  - **the body probe:** `bite` with the prey's body kept out of the body field. Bites land (combat samples body points,
    not the body field), but the hunter's collision inputs never see the prey.
- **Crowding never acts, and bodies never block** (Fable; measured): two bodies reach a body density of 2/3, below the
  crowding threshold of 0.8, and `_resolve_move` checks walls only, so the hunter can pass through the prey. Ghost
  against reach therefore measures the prey's collision input alone. A static prey is pinned (its proposed moves are
  refused) as a guard; **the pin's log is expected to read zero.** SCOPE.md §2's sentence that crowding "can also move
  a `Stationary` prey" is corrected there, dated.
- **The prey never drains, eats, heals or bites** (energy off; attack scale 0). Its starting energy is E_prey (§3).
- **After a capture** (at most one per tick, one prey per world): no pellet is left. The new life starts at the next
  centre of the sequence that is at least **D − R = 6.5 from the hunter's head**, with energy E_prey, a fresh policy
  state, a heading from its own stream, and its activation at the next tick; the hunter's state is untouched; the
  geometry and body field are refreshed. **Change from SCOPE.md (2):** the scope asked for D; D − R keeps the ghost on
  Task N's sequence (for a static prey reached within R the next centre is always at least D − R away, by the triangle
  inequality), and still keeps every new life 6.5 cells away.
- **The ledger** (`HuntLedger`: Task N's terms plus `removed` and `respawned`):

  | Capture rule | Booked as removed | Booked as respawned |
  |---|---|---|
  | ghost, reach | the prey's remaining energy + its body mass | E_prey + body mass |
  | bite | its body mass (its energy is 0; the bites' losses are combat's) | E_prey + body mass |

  It must balance every tick, at T0's relative tolerance (1e-5 of each world's starting total).
- **`done()` is the horizon:** the hunter cannot die (energy off, no attacker), and a caught prey is replaced in the
  same tick.
- **Events,** per sequence index: activation tick, capture tick (−1: none), the hunter's and the prey's path lengths,
  contact ticks (the hunter's head within 1.5 of a prey body point), attributed damage, first-contact tick and bearing.
  Per episode: captures, the hunter's energy gained from bites (logged, never scored), the pin's log, and the prey's
  wall-refused moves.

**The score is captures in 300 ticks.** Nothing else enters any rule.

## 3. Calibration

**World ids** (none used before with run seed 1 500 001; 04a once abandoned 997 000 000 onwards after a smoke run, so
this plan uses 991 million): calibration 991 000 000 to 991 000 063; the equivalence check 991 200 000 to
991 200 511; evaluation 991 100 000 to 991 100 511, the same 512 for every hunter (paired). Run seed 1 500 001.

1. **E_prey, from a held contact.** The prey pinned at each calibration world's first centre, with its own heading
   (sub-cell variety); the hunter placed with its bite point (0.9 ahead of its head) on the prey's mid point, from the
   prey's left side, facing it, and held still (forward and turn 0); the prey's energy 10⁶ while measuring, so no
   damage is capped. Per world, the damage over 20 ticks divided by 20; **E_prey = 10 × the median over the 64
   worlds**. Predicted from the engine's constants (Fable): about 0.061 per tick with one flank body point in the bite
   cell's neighbourhood, 0.122 with two, 0.015 on the head; so E_prey near 0.6 to 1.2. **Stop** if the median is zero,
   or if E_prey is not larger than the largest single-tick damage seen in this fixture and in the driven approaches
   below (predicted about 0.14). Then, at that E_prey, the pursuit reference drives at the prey's head, mid point and
   tail from 3 cells away (head-on, side, rear), 64 worlds each; the realised kill times (ticks from first contact to
   capture, median and range) are reported.
2. **The route follower** (H2): a privileged scripted prey steering at its next waypoint with turn = clamp(gain × the
   heading error, ±1), gain 2, at forward command s. A route is a closed loop through 4 waypoints: waypoint 0 is the
   life's centre; waypoints 1 to 3 are drawn per (world id, life) from the route's own stream, uniform inside the wall
   clearance, each at least 6 from the previous, and waypoint 3 at least 6 from waypoint 0. The prey starts with its
   life's heading and steers first at waypoint 1; it visits them in order; reaching one is coming within 1.0; a lap ends
   on returning to waypoint 0. **The check,** alone (the bite rule with the hunter's attack at zero, so it is never
   caught), for 3 000 ticks, at every speed in the grid, on the 64 calibration worlds: in at least 95% of worlds, (i)
   path length per tick at least 0.8 × s × 0.35, (ii) at least one completed lap, and (iii) walls refuse at most 1% of
   its moves. If any speed fails, the turn gain is raised to 4 for every speed, then the minimum spacing to 8 for every
   speed, and the check repeated; if it still fails, **E5-0 stops for a revision of the route follower.**
3. **H2b's movers** (bite rule), at s ∈ {0.25, 0.5, 0.75}:
   - a random-walk prey: turn = clamp(0.4 × u, ±1), u_t = 0.9 u_(t−1) + √(1 − 0.81) e_t, u = 0 at each life's start,
     e_t a standard normal (Box-Muller) from uniforms keyed to (run seed, world id, tick), so every hunter meets the
     same prey path until contact changes it; realised speed and wall-refused moves reported;
   - a wall-following prey: E1's tuned wall-follower parameters (`freeze.json`), its speed replaced by s. Its collision
     inputs include the hunter's body, so it is **weakly reactive**; labelled so.
4. **The speed grid** (H2, bite rule): s ∈ {0.1, 0.2, …, 1.0} of one physical maximum (0.35 cells per tick at forward
   command 1), shared by every hunter and prey. All ten are evaluated; E5-1's ladder is chosen from the results, not
   here. Realised prey speeds are reported.
5. **Tuning per setting:** at each of the 19 evaluated settings (§6), on the 64 calibration worlds, with E1's grids and
   its rule (the first maximum in grid order): S-const (the observation-limited positive control), `constant`,
   `random-walk` (seed 0) and `wall-follower` (the blind hunters). The wall-follower's thresholds are offsets from the
   hunter's own-body level, E1's measured 0.452 (`freeze.json`): the hunter's own body is Task N's. Their E1-frozen
   parameters are also evaluated, as transfer references.

## 4. The equivalence checks (before any evaluation)

1. **Old engine against new** (T1's contract, `docs/foundations/T1.md`): the engine at `ab749bb` (before the hooks),
   in a separate worktree, against the working tree, on the CPU, bit for bit: Task N (`navigate`) with E1's frozen
   S-const, the oracle, E4s-1 run 0's champion and one E2d champion, on the 512 equivalence worlds (per-world counts and
   event tables), with per-tick positions, headings, input currents and neural states on 8 of them; and a two-swarm
   combat world (`forage`, combat stage 1, two random strains of 6 weys, 100 ticks, 64 worlds), comparing energies,
   positions and the combat ledger. Required: identical.
2. **H1-ghost against Task N, in the new engine, bit for bit:** the same 512 worlds, run seed 1 500 001; E1's frozen
   S-const, the oracle against the pursuit reference, the three blind controls, E4s-1 run 0's champion, L1 on its
   carrier, one E2d champion and one generation-0 genome; under the `real`, `constant` and `mirrored` probes; per-world
   counts, capture ticks and path lengths, and per-tick traces on 8 worlds. Required: identical. **A difference in 1 or
   2 stops E5-0 until it is explained.**
3. **The CUDA gap, reported, not a gate:** E1's frozen navigator under `navigate` on the CPU against `gate.json`'s
   per-world counts (CUDA) on E1's 1 024 gate worlds, so the platform's share is separated from the code's (H1-ghost
   equals `navigate` by check 2). This is a second use of E1's gate worlds, for an engine comparison only; nothing is
   tuned or claimed on them.
4. **The prey graft** is not needed in E5-0 (no organism prey); its check waits for H3.

## 5. The hunters

**Scripted (10):**
- **the observation-limited positive control:** S-const, tuned per setting;
- **the blind controls:** `constant` and `random-walk`, tuned per setting; `wall-follower`, tuned per setting and
  labelled **not blind to bodies** (its collision input includes the prey's body);
- **the transfer references:** the same four at E1's frozen parameters;
- **the pursuit reference:** E1's oracle (k = 2, speed 1) steering at the live prey's position. Privileged; its success
  shows a setting is feasible, and its failure does not show it is impossible (E1's navigator sometimes beat the
  oracle; `experiments/E1-navigation/RESULTS.md`);
- **stationary:** forward and turn 0, which measures captures made by the prey's own approach;
- **the attack-disabled check** (at H1-bite only): the pursuit reference with its attack scale at 0. It must capture
  nothing.

**Neural, zero-shot, frozen (80):**
- **E4s-1's 16 M-arm champions** (each run's validation champion, whole brains, N2 + L1), each checked against its
  committed sha256;
- **E4s-0's L1 on its carrier** (forward 1.0, turn 0.2; `module.json`'s bound sha256 checked), the neural positive
  control;
- **E2d's 47 champions** of E2 and 04a (loaded and hash-checked from E2's and 04a's records; one duplicate by sha256
  dropped, which gives E2d's 47);
- **generation 0:** 16 random N2 genomes (02's initialisation, genome seed 1 500 011).
- The grafted hunters have 306 neurons and the rest 302; the prey are scripted, so the world's one current width is
  the hunter's.

**Probes** (hunter-only):
- `constant`: for every neural hunter, at **every** setting where it meets the capture criteria (§6), run after the
  main pass, for qualification;
- `mean`, `mirrored` and the body probe: for every neural hunter at H1-bite and at H2 with s = 0.5.

## 6. Decision rules (fixed before evaluation)

**The 19 settings:** H1-ghost, H1-reach, H1-bite; H2 at the ten speeds; H2b's random walk and wall follower at three
speeds each. H1-ghost is the bridge to Task N; the rules below are read at the other 18.

**Intervals:** paired percentile bootstraps over the 512 evaluation worlds, 10 000 resamples, seed 0, every quantity
in one resample computed on the same resampled worlds. A lower bound is the 5th percentile, an upper bound the 95th
(one-sided 95%). "The best baseline" is the stationary, `constant`, `random-walk` or `wall-follower` control (each tuned
for that setting) with the highest mean, **recomputed inside each resample**, both for differences and for ratios.

- **Solvable** at a setting: the tuned positive control's share of episodes with at least one capture has a lower
  bound of at least 0.80, **and** its advantage over the best baseline has a lower bound above 0.5 captures per
  episode. Otherwise "not shown solvable by the positive control", with the pursuit reference beside it.
- **Too easy**, read only where solvable holds: the ratio of the best baseline's mean to the positive control's.
  "Too easy" if its lower bound is at least 0.5; "not too easy" if its upper bound is below 0.5; otherwise
  "inconclusive". Flagged if its point estimate is at least 0.25. **Solvable and too easy can both hold.**
- **A reused hunter qualifies** at a setting when (a) its share of episodes with at least one capture has a lower
  bound of at least 0.80, (b) its advantage over the best baseline has a lower bound above 0.5, and (c) its intact
  scent beats its `constant` probe (paired difference, lower bound above 0). (a) and (b) are "the capture criteria";
  (c) is run wherever they hold. Where (c) could not be run, the result reads "capture criteria met; cue dependence
  untested".
- **Demonstrated failure,** per criterion: (a) its upper bound below 0.80; (b) its upper bound below 0.5; (c) its
  upper bound at most 0. A hunter that neither qualifies nor demonstrably fails a criterion is "uncertain".
- **Falls off:** within each speed series, in increasing speed (H2's ten; each H2b mover's three), **the first tested
  speed where it does not qualify**, with every later recovery shown. It is not a monotone cutoff. No order of
  difficulty is assumed between H1, H2 and H2b.
- **Readings without a threshold,** per hunter: ghost minus reach at H1 (what the prey's collision input costs it);
  bite minus the body probe (the same, under bites); `mean` and `mirrored` against intact.
- **The attack-disabled check** must give zero captures and zero damage; anything else is a bug and stops E5-0.
- Each genome is reported on its own before any family summary.

## 7. The code

- **`wormwars/world.py`, hooks only,** each a no-op for every existing task: `_spawn_swarms()` (how many swarms the
  map's spawn step places; default all), `attack_scale` (per-swarm deposit multipliers; default `None`, no
  multiplication), and `_wants_food_field()` (the existing condition, moved into a method).
- **`wormwars/e5/hunt.py`:** `HuntWorld`, `HuntLedger`, `e1_task_n`, `hunt_config`.
- **`wormwars/e5/prey.py`:** the scripted prey (`stationary`, `route`, `random_walk`, `wall_follower`) and the pursuit
  reference.
- **`wormwars/e5/play.py`:** batched episodes (hunters as strains, worlds tiled per strain).
- **`wormwars/e5/hunters.py`:** the reused hunters' loaders, each hash-checked.
- **`scripts/e5_0.py`:** `bench`, `calibrate`, `equivalence`, `evaluate`, `probe`, `read`; start markers, provenance,
  the compute record (`wormwars.accounting`), the cap (§8). `scripts/e5_0_reference.py` runs the old engine's side of
  §4.1 in its worktree.
- **Tests** (`tests/test_e5_hunt.py`): ghost against Task N; the ledger through captures; the pin and the absence of
  crowding; the attack scale (zero captures) and the prey's zero deposit; respawn distance; the route follower's
  speed, laps, ordered visits and wall refusals; the body probe; `done()`; the task guards; the attack hook's no-op
  in an existing fight. The code came before its tests, so each was seen failing under a sabotage of the behaviour it
  checks (`scripts/e5_0_sabotage.py`, `runs/e5-0/sabotage_log.txt`).

## 8. Cost

`bench` measures scripted and neural hunters on the CPU, with combat and events, at the intended batches, before
anything else runs; the plan then counts its episodes. Before probes and calibration the main pass is about 0.88
million episodes: 80 neural genomes and 10 scripted evaluations × 19 settings × 512 worlds; the tuning adds about
0.46 million scripted episodes (E1's four grids, 379 points, × 64 worlds × 19 settings), the fixed probes about 0.25
million, and the qualification probes up to 0.78 million more.

**The cap is 8 hours of the script's recorded elapsed time** (the accounting's records, summed over every attempt, as
`CapClock` does). If `bench` projects more for the main pass, the fixed probes and the calibration, these are cut in
order until it fits, and the cuts recorded: (1) generation 0 down to 8 genomes; (2) the `mean` and `mirrored` probes
kept at H1-bite only; (3) H2's speeds thinned to {0.1, 0.3, 0.5, 0.7, 1.0}; (4) evaluation worlds down to 256. Hunters
are never filtered by an earlier setting's result. If all four cuts still do not fit, E5-0 stops before evaluating and
returns to the plan. **The qualification probes are staged:** after the main pass, if they do not fit in what is left,
they run in this order (E4s-1's champions, L1, E2d's champions, generation 0) until the cap, and the rest read "cue
dependence untested".

## 9. Outputs

`experiments/E5-hunter/E5-0/`: `bench.json`, `calibration.json`, `equivalence.json`, `evaluation.json` (per-world
counts per hunter and setting), `probes.json`, `reading.json`, `compute-record.json`, start markers, and `RESULTS.md`
after review; the event tables in `runs/e5-0/` (local if large). Reviewed by both models: this plan, then the code,
then the results.

## 10. Amendments after the code review (2026-11-06, D387)

The code review (`docs/reviews/20261106-E5-0-code/`; Astra and Fable, both "fix then run") changed no decision rule
and no number. Four places in the text above now read differently in the code, and are recorded here instead of
being edited:
- **§3.2 (iii):** "walls refuse at most 1% of its moves" cannot fail in an arena with only the boundary ring, where
  no move is ever refused (Fable). The check counts **the moves the arena limits, clamped at the wall ring or refused**,
  at most 1% of the prey's moves; the 95% applies to (i), (ii) and (iii) **jointly** in each world (Astra), with each
  share also reported.
- **§3.1:** the prediction of 0.6 to 1.2 for E_prey was indicative, not a rule: the held fixture can also catch the
  head's damage, and on the smoke worlds the per-tick rates were 0.1375 and 0.0764 (Astra). The smoke's 1.25 was
  wrong: the damage was taken as a float32 energy difference near the measuring energy of 10⁶, which rounds to
  multiples of 0.0625. Damage is now combat's own capped damage, summed in float64.
- **§4 and §8, the order of the stages:** bench, equivalence, calibrate, evaluate, probe, read. Bench comes first, as
  §8 says, with a provisional E_prey of 1.0, and projects the equivalence checks and the calibration as well as the
  evaluation and the fixed probes; the cuts then apply to the calibration's tuning too.
- **§9:** `evaluation.json` and `probes.json` hold the per-world counts (rule 5); the full event tables, the hunter's
  bite energy and the prey's movement are kept in `runs/e5-0/`.

The code also now enforces what the plan already said: the ledger is checked at every tick and a residual above
1e-5, or a non-finite one, stops E5-0; a capture or any damage in the attack-disabled check stops it; the cap's clock
counts the running stage; every stage after bench refuses to run unless the code is unchanged since the stages it
builds on, and a resumed stage checks its own start marker's commit; the reference worktree's head and cleanliness
are checked; the traces cover every hunter of §4.2, and the oracle in §4.1; the `constant` probe replaces the
hunter's food channels only.
