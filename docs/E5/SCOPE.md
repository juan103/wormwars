# E5 (stage 05): the hunter. Scope and design note

*Draft 2, 2026-11-04, after one round of review (Astra 6 and Fable 5.1: both "fix then proceed"; every fix taken;
[`docs/reviews/20261104-E5-scope/`](../reviews/20261104-E5-scope/), with draft 1). Not a pre-registration: nothing
here has run and no code is written. Exploratory until a stage is pre-registered. The numbers for E5-0's decision
rules are fixed in its own plan, before it runs (§6).*

## 1. What the owner asked for

The owner chose stage 05 (2026-11-04, D385): "For the hunter let's start with a static prey, and then let the prey
increase in complexity. Like one that has a defined route. Then we use the ones we develop in the previous
experiments. Maybe we can use some of the things we built before?"

So the prey ladder is the owner's:
1. **a static prey;**
2. **a prey on a defined route;**
3. **prey taken from earlier experiments** (frozen organisms evolved there).

Asked whether 05 should also test the connectome, by running the same hunters on null graphs, the owner said "Sure"
(the same day, D385). **So 05 is both a build and a test:** a hunter that works, reusing what earlier stages built,
and a comparison of N2 with null graphs (§8).

The roadmap's stage 05 ("Direction after E4") asks for a prey progression ending in "a frozen suite of competent
prey; food other than prey limited", with the gate "captures moving prey from the frozen suite on unseen maps", and
coevolution only after that, "with historical opponents and a frozen evaluation suite". The owner's ladder prepares
for that gate: H1 to H3 below supply the stationary and moving prey and the frozen suite. **The gate itself needs
H4**: competent moving prey on held-out maps with obstacles. Fresh world ids in an empty arena test new placements,
not new map geometry (Astra).

## 2. What already exists and is reused

Checked in the code on 2026-11-04, and by both reviewers.

**The world** (`wormwars/world.py`) already has, from experiment 01's game:
- several swarms per world, each with its own brain (`World(brain=[...])`);
- automatic biting (`combat_stage >= 1`): every live wey deposits an attack field one cell ahead of its head; a victim
  takes `damage_k` per unit sampled at head, mid and tail, with the head armoured at 0.25 (so a head-on bite does about
  a quarter of a flank bite's damage); half of it reaches the attacker; no friendly fire; a wey with no energy dies and
  leaves a corpse pellet; the energy ledger checks every transfer;
- the sensors: food scent (stereo or mono), ally and enemy pheromone, damage left and right, collisions;
- Task N's machinery (`task: navigate`, `wormwars/e1/task.py`): a sensing-only target scent that moves to the next
  centre of a pre-drawn sequence when the head comes within R; the event table; energy off; a 300-tick horizon.
  **E1's gate ran σ = 6, A = 1, R = 1.5, D = 8** (`experiments/E1-navigation/`), not the config's default σ = 3.

**Four things the world does that matter for a one-against-one hunt** (Fable; Astra on the first two). Each becomes a
code item in §5:
- **Bodies are obstacles.** The collision signals sample the wall field plus the body field (`world.py:885`), so the
  hunter's ALM, AVM and PLM fire on the prey's body. The reused navigators evolved their collision reflexes on walls
  alone, and may turn away at the last cell. The wall-follower is therefore not blind to the prey.
- **Crowding resists and pushes.** Above a body density of 0.8, movement is slowed by up to 60% and pushed 0.10 cells
  per tick down the density gradient (`world.py:1021-1037`), against a top speed of 0.35. It was tuned for melees of
  hundreds, and it opposes holding contact. It can also move a `Stationary` prey. *Corrected 2026-11-05 (D386):
  this is wrong for one hunter and one prey. Each body point splats 1.0 into its nearest cell under a normalised 3 × 3
  blur, so two bodies reach a density of 2/3, below the threshold of 0.8 (Fable's arithmetic, measured: 0.667), and
  crowding never acts; bodies also never block movement (`_resolve_move` checks walls only). The pin stays as a
  guard. The sentences above are kept as written; they hold for the melees crowding was tuned for.*
- **A kill leaves a sensed corpse and can end the episode.** The prey's pellet (6.0, in one cell) is sensed on the
  food channels (food plus pellet, `world.py:836`) and, with Task N's eat rate of zero, stays all episode: a strong
  trap beside a prey scent of peak 1. And `done()` ends a two-swarm world once either swarm is empty (`world.py:1349`).
- **The prey senses what the world gives it.** With no food patches, 02's champions receive no food input and move
  on their default gait. Adding food would put it on the hunter's food channels too. And the sensing settings are
  world-level, while 02's T1 ran mono food sensing and T0 stereo, both with food blur and a reduced food sensing
  scale, with graph-specific motor gains and sometimes remapped interfaces (`wormwars/exp02/grid.py`; Astra).

**Scripted controllers** (`wormwars/exp02/scripted.py`, `wormwars/e1/controllers.py`): `Stationary`, `Straight`,
`ConstantMotion`, `PersistentRandomWalk`, `WallFollower`, stereo-proportional steering, the memory controls (M-avg,
K), and the privileged `OracleBrain`, which sees the world (`attach_world`).

**E1's instruments** (missed in draft 1): the world's scent probes (`mirrored`, `constant`, `jitter`, `hold`) act on
the sensed food and so apply to the prey scent unchanged; E1's cue interventions, its event table and statistics;
and the registration guard (`wormwars/registration.py`), which can check that H1's configuration is E1's gate
configuration by hash.

**Earlier organisms** (genomes on the local disk, not committed: `runs/exp02-screening/`, `runs/e2/genomes/`,
`runs/e4s1/genomes/`, `runs/e3*/genomes/`, `runs/e4d-evo/`):
- **as hunters**, the navigators of Task N:
  - E4s-1's M arm (N2 plus the 4-neuron stereo comparator graft): its final brains average 7.14 targets per 300-tick
    episode. They are reused as **whole brains**: the module alone does not carry them (the selected run 10's
    module scored zero on both carriers);
  - E4s-0's designed comparator, L1, on its carrier: a neural positive control;
  - E1's scripted stereo navigator: 8.68, 98.7% of an oracle that steers at the true target;
  - E2's and 04a's champions (N2 only): typically 1.9 to 2.9, with one failed GA champion at 0.75, on E2d's
    operational "non-stereo plateau";
- **as prey**, anything that moves on its own: 02's T1 and T0 foraging champions (N2 and null graphs), E2's, 04a's
  and E4s-1's navigators, and later E3's shuttlers.

**Coevolution** (`wormwars/evo/coevolve.py`): its hall of fame and paired schedule are reusable after the gate. Its
frozen suite is not: it is six random-weight strains at spread scales, not competent prey, and its match score is the
surviving-energy difference of 50-to-200-wey swarms (Fable, Astra).

**E3's maze code** (`wormwars/e3/`): geometry, collision and sensing are reusable for H4, but `MazeWorld` allows one
swarm, so H4 is an adaptation, not a choice of maps (Astra).

**A lesson from experiment 01** (`docs/RESULTS.md`, its corrections; D026 is the related flank retraction): coevolved
swarms got 0.1 to 0.3% of their energy from biting. The fuller lesson (Astra): **damage can happen because the other
animal approaches, and a metric can encode its own success.** With prey that never bite, 01's "unanswered damage"
share is 1 by construction and shows nothing. The evidence 05 needs is captures above stationary and blind hunters,
and dependence on the scent.

## 3. The task: Task H

Task H is Task N with a living target.

- **Two swarms per world:** one hunter (swarm 0) and one prey (swarm 1; later several). Boundary wall only, until H4.
- **Built from E1's gate:** `task_n_config` at σ = 6, A = 1, R = 1.5, D = 8, horizon 300, plus a hunt flag, so the
  resolved configuration can be compared with E1's gate record.
- **The prey's scent:** a sensing-only Gaussian around the prey's mid point, Task N's form at σ = 6 and A = 1, on **the
  hunter's food channels only**, excluding food and corpse pellets. Every navigator steers on food scent, so they
  transfer with no retraining. The prey's pheromone trail is a later, separately named condition: no reused navigator
  ever used ADL, and Task N turns pheromone off (both reviewers).
- **Capture, in steps:**
  - **H1-ghost:** the prey has no body (no body field, no crowding, no collision input). This is Task N, and it must
    reproduce E1's gate numbers within a declared tolerance: an equivalence test of the new task.
  - **H1-reach:** the prey has a body. The same reach rule (head within R of the mid point). The difference from the
    ghost measures what the body's collisions and crowding do to the reused hunters. Reach is a navigation bridge,
    not a capture.
  - **H1-bite:** the prey's energy brought to zero by **damage attributed to the hunter**. The prey energy is
    calibrated in controlled contact geometries first (orientations and offsets, since the head armour changes the
    damage about fourfold), to a reference of about ten ticks in a specified sustained contact, with the spread
    reported; then free pursuit is measured.
- **After a capture:** the prey's pellet is removed, and a new prey appears with a fresh brain state. The respawn
  point is drawn from a pre-drawn sequence per world id, but placed at least D from **the hunter's actual position**
  and clear of the wall (Task N guarantees separation between consecutive centres only; Astra). The removed pellet and
  the new prey's energy and body mass are booked in the ledger. `done()` is overridden.
- **The prey does not bite back, starve or heal** in E5-0: no attack deposit, no drain, no eating.
- **Energy off for the hunter** (Task N's setting). The roadmap's "food other than prey limited" is **deferred**, not
  met: it needs energy on, a later level. The hunter's energy from bites is logged and kept out of selection.
- **The score is captures in 300 ticks.** Draft 1's tie-break by the unfinished leg's progress is withdrawn: D103
  defines progress as training shaping only, and the roadmap's scoring rules keep shaping out of the benchmark. If
  E5-1 uses shaping, it is redefined for a moving target (distance at the leg's start against the last tick,
  clipped). Logged raw: contacts, attributed bite damage, time to first capture, path length, distance to the prey.

## 4. The prey ladder

| Level | Prey | Controller | Complexity knob |
|---|---|---|---|
| H1 | static | scripted `Stationary`, position pinned if crowding moves it (checked) | ghost, reach, then bite |
| H2 | a defined route | a scripted route follower (new; privileged like `OracleBrain`) on a closed loop through 3 to 5 waypoints | prey speed |
| H2b | other scripted movers | `PersistentRandomWalk`, `WallFollower` | unpredictability, wall contact |
| H3 | earlier organisms, frozen | a small qualified suite (below) | how purposeful the motion is; whether they react to the hunter |
| H4 | the same on held-out maps with obstacles | E3's maze code, adapted to two swarms | the roadmap's gate |

- **H2's routes** are drawn per world id from Task N's stream: waypoint layout, starting phase, direction and
  orientation vary by episode; each route is deterministic once drawn, so no loop can be learned by heart. The route
  follower is checked to complete its loop at the commanded speed without wall stalls or impossible turns.
- **H2's speeds are not fixed in advance.** E5-0 sweeps prey speed from 0.1 to 1.0 of one fixed physical maximum,
  shared by every hunter, reports the realised speeds, and sets the ladder from where the positive control falls off.
  Turning limits, starting separation, route geometry and the horizon all matter, so a slower prey is not assumed
  catchable.
- **H3's suite** starts small, with each candidate's movement and own-task competence qualified independently of how
  easily a hunter catches it ("previously evolved" does not make a competent prey):
  - whole E4s-1 navigators chasing their own targets, and E2's and 04a's navigators as weaker or different movers.
    These need per-swarm targets (Task N allows one swarm of one wey), the largest code item;
  - 02's T0 and T1 champions with their native sensing (mono or stereo, blur, scale) and motor gains, which needs
    role-specific settings, or an openly documented change of conditions. Without food they are labelled movers,
    not competent prey;
  - E3's organisms once their task signals and mazes are supported.
  In the **transfer condition** the prey's novel inputs (enemy pheromone, damage, the hunter's body on collision) are
  masked; a separately named **interaction condition** exposes them. Exposure is an experiment, not preserved
  behaviour, and does not show learned evasion. No bite-back at H3: it changes the energy game, which is where 01 went
  wrong, and belongs with coevolution.

The frozen suite for the gate is chosen from H2, H2b, H3 and H4 before any hunter is evolved, and split into
training, validation and test prey; the test suite is used once and kept out of E5-0 entirely.

## 5. What is new code

Each with a test seen failing first; every existing task is checked unchanged (rule 7):
1. **The hunt task:** two roles; the prey scent on the hunter's food channels only, without food or pellets; the
   ghost, reach and bite rules with attributed damage; pellet removal, respawn at least D from the hunter, the ledger
   bookings and `done()`; the event table. H1-ghost's equivalence with E1's gate is the first test.
2. **Per-swarm settings:** attack strength (the prey's zero), energy (no drain, no eating, no healing for the prey),
   and, for H3's 02 prey, food sensing mode, blur, scale and motor gains.
3. **Body effects as switches:** the prey's contribution to the body field, crowding and collisions, so the ghost and
   the masked conditions exist.
4. **The route follower**, a scripted prey policy, with its completion check.
5. **Organisms as prey:**
   - the world builds one input current of one neuron count for all swarms. A grafted hunter has 306 neurons, 02's
     champions 302. Each prey genome goes on **its own original graph** (N2 or its null graph) with the graft inert
     (`Module.without_outputs`; E4s-1 also has a construction keeping the output edges at zero weight). The check is
     E4s's declared tolerance (1e-5 over 100 CPU neural steps, 1e-4 over 300 on CUDA) plus E4s's score-level check
     (each genome's mean within 0.05 over 256 worlds), over the intended horizon and batch composition. Draft 1's
     "behaves exactly as before" was wrong. A per-swarm current width (`world.py:941`) is the cleaner alternative,
     but an engine change with its own equivalence check;
   - per-swarm targets for navigator prey (H3's second half);
   - input masks for the transfer condition.

## 6. The first step: E5-0, a feasibility check on the CPU

Like E4-D's feasibility check (D262): no evolution, scripted and frozen controllers only, calibration separated from
evaluation. **Its decision rules are fixed in numbers in a short committed plan, reviewed, before it runs.**

**Controls:**
- **an observation-limited positive control:** a scripted hunter using only declared observations, adapted if
  needed, which establishes that a level is solvable. E1's navigator is kept as a transfer reference and is not
  required to catch every slower prey: finite-horizon pursuit need not succeed (Astra);
- **a privileged pursuit controller** (an oracle that sees the prey), to separate geometric feasibility from a
  steering policy's failure;
- **E4s-0's designed comparator on its carrier**, a neural positive control;
- **a stationary hunter**, which measures captures made by the prey's own approach;
- **blind hunters,** each tuned separately: `ConstantMotion` and `PersistentRandomWalk`; and `WallFollower`, labelled
  not blind to bodies;
- **an attack-disabled check:** bite captures must be zero.

**Probes on each frozen hunter** (hunter-only; the prey's observations unchanged): constant scent, the two sides'
mean, mirrored scent, and collision inputs masked.

**Reused hunters, zero-shot:** E4s-1's whole M-arm brains, E2's and 04a's champions, and generation 0, on H1 (ghost,
reach, bite), H2's speed sweep and H2b. This answers "can we use what we built": where each one stops capturing.

**The decision rule's form** (the numbers go in the plan; the reviewers proposed two sets, recorded in
`docs/reviews/20261104-E5-scope/`):
- calibration on a small set of worlds (Astra: 64), then fresh paired evaluation worlds per frozen condition (Astra:
  512; Fable: 1 024), settings and controller choices frozen in between;
- **solvable:** H1-ghost matches E1's gate within its tolerance; at the other levels, a lower confidence bound on the
  positive control's captures (Astra: at least one capture in 300 ticks in over 80% of episodes; Fable: at least 3
  captures per episode at H1-bite and 2 at H2's slowest speed);
- **separated from accidents:** the positive control's paired advantage over every blind control (Astra: a lower
  bound above 0.5 captures per episode);
- **too easy:** a blind control scores a large fraction of the positive control (Astra: 80%, with an interval
  crossing it inconclusive; Fable: a quarter);
- **a reused hunter qualifies** when it meets the reliability and blind-control margins and its intact scent beats
  its constant-scent probe;
- **falls off:** the first failed rung within each speed series, with demonstrated failure separated from
  uncertainty; H2b and H3 are not assumed harder than H2;
- intervals by bootstrap over independent worlds and routes, paired, never over individual captures; each frozen
  genome reported separately before any family summary.

**What it answers:** whether the ladder is solvable and not trivial, and where the reused hunters fall off. It does
not evolve a hunter.

**Cost:** not yet supported. Draft 1's "one to a few CPU hours" rested on a GPU rate (306 episodes per second at one
composition in E4s-0, different at others). E5-0's plan will benchmark scripted and neural hunters separately, with
combat, the intended batches and event logging, and count genomes × conditions × probes × worlds, before stating
hours (Astra; Fable's rough arithmetic, about 2 GFLOP per two-wey episode, makes an hour or two plausible). The code
(§5) is the larger part: several working sessions, each reviewed.

## 7. E5-1, evolution, and the null-graph arm

E5-1 evolves hunters up the ladder and tests them on the frozen suite. It needs the GPU and the owner's word, and is
designed after E5-0. **Draft 1's forecast of 5 to 20 GPU hours is withdrawn:** it took E4s-1's 16.61 GPU hours as 16
runs, when they covered 80 (Astra). A forecast waits for E5-0's measured rates.

**The null-graph arm (the owner's choice, D385):** hunters evolved on N2 and on null graphs at matched budgets, from
matched starts, and compared on the frozen suite, so 05 also asks whether N2's wiring helps a hunter. Which null
families (03's validated ensembles, or 02's graphs), how many graphs, and what start is fair (E4s-1's graft was built
and settled on N2 only) are E5-1's design questions. It roughly doubles E5-1's cost or more.

**Before E5-1 is authorised:**
- mutations are tested around the chosen hunter seed, since E4's comparator modules were mutationally fragile
  (bias-only perturbations roughly halved E-G's score on one diagnostic block; E4s-1's sensitivity is not known);
- the graft's mutation is pinned or scaled as E4s-1 did;
- frozen references are kept, and inherited function (Task N) is tested during adaptation.

## 8. Risks

- **D026's lesson:** accidental captures, and metrics that encode their own success. Answered by the stationary and
  blind hunters, the attack-disabled check and the scent probes, not by damage-share metrics.
- **E2d's plateau** is operational, not a proven ceiling. The N2-only hunters may fall off early; a moving source may
  break whatever strategy they use. E5-0 measures this; more optimisation is not assumed to fix it.
- **Bodies, crowding and corpses** (§2) are the likeliest reasons a reused hunter fails at H1-reach where it succeeds
  at H1-ghost. The ghost makes that visible.
- **E4's fragility** matters for E5-1 (§7).
- **Scope:** the ladder to H4 is a lot of engine work. E5-0 covers H1, H2 and H2b first; H3 and H4 follow only if E5-0
  finds the task solvable and the reuse worth it.

## 9. Options for the owner, not decided here

- **Prey that bite back, and energy on,** after H3.
- **The pheromone-trail scent,** as a named later condition.
- **Coevolution** after the gate, as the roadmap says.
