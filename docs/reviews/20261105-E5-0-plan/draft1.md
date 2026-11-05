# E5-0: Task H's feasibility check. Plan

*Draft 1, 2026-11-05, before review. Exploratory (not a pre-registration), but its decision rules are fixed here,
before it runs, as D262 did for E4-D's feasibility check. CPU only, no evolution. The scope is
[`SCOPE.md`](SCOPE.md), draft 2 (D385); the owner said "go ahead" on 2026-11-05.*

## 1. What E5-0 answers

1. **Is the new code right?** H1-ghost (a prey with no body) is Task N, and must reproduce it (§4).
2. **Is each rung of the ladder solvable, and not trivial?** By an observation-limited positive control, against
   stationary and blind hunters (§6).
3. **Where do the reused hunters fall off?** E4s-1's champions, E2d's 47 champions of E2 and 04a, E4s-0's comparator
   on its carrier, and generation 0, zero-shot (§5).

It does not evolve anything, and it does not test the connectome (that is E5-1's null-graph arm).

## 2. Task H, as implemented

`wormwars/e5/hunt.py`, a subclass of `World` (as E3b's `MazeWorld` is), with task `hunt`. Settings:
- **built by E1's own `config(6.0)`** (`scripts/e1.py`: σ = 6, A = 1, R = 1.5, D = 8, horizon 300, wall clearance 3,
  food sensing scale 0.35, 32 substeps, single-strain padding on, energy off, no food, hazards or pheromones), plus
  `task = hunt`, two swarms of one wey;
- **the hunter** (swarm 0) spawns exactly as Task N's wey does (the same draws of the same stream);
- **the prey** (swarm 1) is placed at the centres of Task N's own target sequence (the same stream): life k at
  centre k. *A change from SCOPE.md:* the prey's scent and the reach rule are centred on **the prey's position** (its
  head point, `pos`), not its mid point, so that a ghost prey's scent is Task N's to the bit. The body extends 2.4
  cells behind it;
- **the hunter's food channels** carry only the prey's scent (A exp(−d²/2σ²), truncated as Task N's, summed over live
  prey); food and pellets are excluded. The prey's food channels carry the map's food and pellets (zero here). Every
  food probe (`constant`, `mirrored`, `mean`, `swapped`, `jitter`, `hold`) acts on the scent as it does in Task N;
  with scripted prey, which read nothing, every probe is hunter-only;
- **capture rules:**
  - `ghost`: the prey adds nothing to the body field (so no crowding and no collision input); capture when the
    hunter's head is within R of the prey's position (Task N's rule, checked after the move, as Task N);
  - `reach`: the same rule, with the prey's body in the body field;
  - `bite`: combat stage 1, with the prey's attack deposit at zero (a per-swarm attack scale); capture when the
    prey's energy reaches zero. Every unit of damage the prey takes is the hunter's (no other attacker exists).
- **the prey never drains, eats, heals or bites** (energy off; attack scale 0). Its starting energy is E_prey (§3);
- **a static prey is pinned:** its proposed move is refused, so crowding cannot push it (logged: the push it would
  have had);
- **after a capture:** no pellet is left (the body mass is booked as removed); a new prey appears at the next centre
  of the sequence that is at least D − R = 6.5 from the hunter's head (for a static prey reached within R, the next
  centre always is, by the triangle inequality, so the ghost keeps Task N's sequence), with energy E_prey, a fresh
  brain or policy state, and a heading from its own stream; its energy and body mass are booked as respawned. The
  ledger (`HuntLedger`: Task N's terms plus `respawned` and `removed`) must balance every tick (T0's 1e-5);
- `done()` is the horizon: the hunter cannot die (energy off, no attacker), and a captured prey is replaced in the
  same tick;
- **events,** per prey life: activation tick, capture tick (−1: none), the hunter's path length, the prey's path
  length, contact ticks (hunter head within 1.5 cells of any prey body point), attributed damage, the prey's start
  position. Per episode: captures, and the hunter's energy gained from bites (logged, never scored).

**The score is captures in 300 ticks.** Nothing else enters any rule.

## 3. Calibration (on calibration worlds, before evaluation)

World ids: calibration 997 000 000 to 997 000 999, evaluation 997 100 000 to 997 199 999 (outside every earlier
range); run seed 1 500 001. Calibration uses 64 worlds per item below (Astra's proposal); evaluation 512 fresh worlds
per condition, the same 512 for every hunter (paired).

1. **E_prey, from controlled contact.** The privileged pursuit controller (§5) drives into a pinned prey from three
   approach geometries: at the prey's head (head-on), at its mid point from the side (flank), and at its tail from
   behind (rear), 64 worlds each, starting 3 cells away. Per geometry, the median attributed damage per contact tick
   over the first 20 contact ticks. **E_prey = 10 × the flank median**, so a held flank contact kills in about ten
   ticks; the head-on and rear kill times at that E_prey are reported (the head is armoured, so head-on is slower).
2. **The route follower** (H2): a privileged scripted prey steering at its next waypoint with turn = clamp(2 × the
   heading error, ±1) at forward command s. A route is a closed loop through 4 waypoints: waypoint 0 is the prey's
   start (its centre in the sequence), waypoints 1 to 3 drawn per (world id, life) from the route's own stream,
   uniform inside the wall clearance, each at least 6 from the previous; direction and starting phase follow from
   the draw; reaching a waypoint is coming within 1.0. **Check:** alone in the arena for 300 ticks, at every speed s,
   its realised mean speed is at least 0.8 × s × 0.35 in at least 95% of the 64 calibration worlds, and it never
   stalls (no 20-tick window with net displacement below 0.5 cells). If it fails, its turn gain is raised to 4, then
   the minimum waypoint spacing to 8, in that order, and the check repeated; the outcome is recorded.
3. **H2b's movers** (bite rule), at s ∈ {0.25, 0.5, 0.75}: a random-walk prey (turn = 0.4 × u, u_t = 0.9 u_(t−1) +
   √(1 − 0.81) e_t, with e_t keyed to (run seed, world id, life, tick), so every hunter meets the same prey path until
   their contact differs), and a wall-following prey (E1's tuned wall-follower parameters, its speed replaced by s).
4. **The speed grid** (H2, bite rule): s ∈ {0.1, 0.2, …, 1.0} of the shared physical maximum (0.35 cells per tick at
   forward command 1), every hunter's and every prey's. All ten are evaluated; the ladder for E5-1 is chosen from the
   results, not here. Realised prey speeds are reported.
5. **Tuning, as E1 did** (E1's grids, the first maximum in grid order), on the calibration worlds, for each of three
   settings: H1-bite, H2 at s = 0.5, and H2b's random walk at s = 0.5. Tuned: S-const (the observation-limited
   positive control), `constant`, `random-walk`, `wall-follower` (the blind hunters). Their E1-frozen parameters are
   also evaluated, as transfer references.

## 4. The equivalence checks (before any other evaluation)

- **H1-ghost against Task N, on the CPU, bit for bit:** on the first 256 of E1's gate worlds (996 201 000 onwards,
  E1's run seed), the frozen S-const navigator, the oracle, the three blind controls and one E4s-1 champion
  (run 0's) must give identical per-world counts and identical event tables (activation and capture ticks, path
  lengths) under `hunt` with `ghost` as under `navigate`. A difference stops E5-0 until it is explained. (E1's gate
  worlds were used once for E1's claim; reusing them here tests the engine, not the navigator.)
- **Against E1's gate record:** the frozen navigator's per-world counts on all 1 024 gate worlds, under H1-ghost on
  the CPU, against `gate.json` (CUDA). Required: the means within 0.05 and at least 99% of worlds identical (CUDA and
  CPU arithmetic differ; E1's counts are integers, so most should agree).
- **Every existing task unchanged:** the world's new hooks (§7) leave the full test suite, and its bitwise CPU
  references, passing.
- **The prey graft** is not needed in E5-0 (no organism prey), so its check waits for H3.

## 5. The hunters

**Controls (scripted):**
- **the observation-limited positive control:** S-const, tuned per setting (§3.4); E1's frozen S-const is the
  transfer reference;
- **the privileged pursuit controller:** E1's oracle (k = 2, speed 1) steering at the nearest live prey's position;
  the ceiling, not a control;
- **stationary:** forward and turn 0;
- **blind:** `constant`, `random-walk` (seed 0), each tuned per setting; `wall-follower`, tuned per setting and
  labelled **not blind to bodies** (its collision input includes the prey's body);
- **the attack-disabled check:** the oracle with its own attack scale at 0, at H1-bite: captures must be exactly zero.

**Neural, zero-shot (frozen):**
- **E4s-1's 16 M-arm champions** (each run's validation champion, whole brains, N2 + L1), checked against their
  recorded sha256;
- **E4s-0's L1 on its carrier** (forward 1.0, turn 0.2; `experiments/E4s-stereo-module/E4s-0/module.json`, sha256
  checked), the neural positive control;
- **E2d's 47 champions** (E2's and 04a's, loaded and hash-checked by E2d's own functions);
- **generation 0:** 16 random N2 genomes (02's initialisation, genome seed 1 500 011).
- The grafted hunters have 306 neurons, the others 302; the prey is scripted, so the world's one current width is
  the hunter's.

**Probes** (neural hunters, at H1-bite and at H2 with s = 0.5 only): `constant`, `mean`, `mirrored`, and the
hunter's collision inputs set to zero (`collision_masked`, new).

## 6. Decision rules (fixed before evaluation)

All intervals are paired percentile bootstraps over evaluation worlds (10 000 resamples, seed 0), one-sided 95%;
each genome is reported on its own before any family summary.

- **Solvable** (a setting: H1-reach, H1-bite, each H2 speed, each H2b mover and speed): the tuned positive control's
  share of episodes with at least one capture has a lower bound of at least 0.80, **and** its paired advantage in
  captures over each of stationary, `constant`, `random-walk` and `wall-follower` (each tuned for that setting) has
  a lower bound above 0.5. A setting that fails is reported as "not shown solvable by the positive control"; the
  oracle's result beside it says whether pursuit is geometrically possible there.
- **Too easy:** the best blind or stationary control's mean is at least 0.5 of the positive control's (the ratio's
  lower bound at least 0.5 to call it; an interval crossing 0.5 is "inconclusive"). A ratio above 0.25 is flagged.
- **A reused hunter qualifies** at a setting when its paired advantage over the best blind or stationary control at
  that setting has a lower bound above 0.5 captures per episode, **and** its intact scent beats its `constant` probe
  (paired lower bound above 0), where the probe was run.
- **Falls off:** within each speed series (H2's ten speeds; H2b's two movers at three speeds each), the first
  setting where it does not qualify. "Demonstrated failure" when the advantage's upper bound is below 0.5;
  otherwise "uncertain". No order of difficulty is assumed between H2, H2b and H1.
- **The attack-disabled check** must give zero captures; anything else is a bug and stops E5-0.

## 7. The code

- **`wormwars/world.py`, hooks only** (each a no-op for every existing task): `_spawn_swarms()` (how many swarms the
  map's spawn step places; default all), a per-swarm attack scale (default none, no multiplication), and
  `_wants_food_field()` (whether sensing samples the food field; the existing condition by default).
- **`wormwars/e5/hunt.py`:** `HuntWorld`, `HuntLedger`, the capture rules, respawn, events.
- **`wormwars/e5/prey.py`:** the scripted prey (stationary, the route follower, the random walk and the wall
  follower as prey) and the privileged pursuit hunter.
- **`wormwars/e5/play.py`:** batched episodes (hunters as strains, worlds as columns), returning per-world counts and
  events; a scripted hunter grid as one batch, as E1's tuning did.
- **`scripts/e5_0.py`:** `bench`, `calibrate`, `equivalence`, `evaluate`, `read`; start markers, provenance, the
  compute record (`wormwars.accounting`), a CPU-hour cap.
- **Tests,** each seen failing first: ghost against Task N on a few worlds; the ledger with respawn; the pin; the
  attack scale (zero captures); respawn distance; the route follower's loop; the collision mask; `done()`; and the
  hooks' no-op on an existing task.

## 8. Cost

`bench` measures scripted and neural hunters on the CPU, with combat and events, at the intended batches, before
anything else runs. The plan then counts its episodes:
- settings: H1 (ghost, reach, bite), H2 (10 speeds), H2b (2 movers × 3 speeds: 0.25, 0.5, 0.75): 19;
- hunters: about 81 neural genomes (16 + 1 + 47 + 16) and about 9 scripted, × 512 worlds × 19 settings, plus the
  probes (4 × the neural hunters × 2 settings) and calibration.
- **The cap is 8 CPU hours.** If `bench` projects more, these are dropped in order until it fits, and the drops
  recorded: (1) H2's speeds thinned to {0.1, 0.3, 0.5, 0.7, 0.9}; (2) generation 0 down to 8 genomes; (3) at H2 and
  H2b, the E2d champions that did not qualify at H1-bite are skipped (labelled, not "fell off"); (4) evaluation
  worlds down to 256.

## 9. Outputs

`experiments/E5-hunter/E5-0/`: `bench.json`, `calibration.json`, `equivalence.json`, `evaluation.json` (per-world
counts per hunter and setting), `events.npz` (local if large), `reading.json`, `compute-record.json`, start markers,
and `RESULTS.md` after review. Reviewed by both models: this plan, then the code, then the results.
