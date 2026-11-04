# E5 (stage 05): the hunter. Scope and design note

*Draft 1, 2026-11-04, before review. Not a pre-registration: nothing here has run. Exploratory until a stage is
pre-registered.*

## 1. What the owner asked for

The owner chose stage 05 (2026-11-04, D385): "For the hunter let's start with a static prey, and then let the prey
increase in complexity. Like one that has a defined route. Then we use the ones we develop in the previous
experiments. Maybe we can use some of the things we built before?"

So the prey ladder is the owner's:
1. **a static prey;**
2. **a prey on a defined route;**
3. **prey taken from earlier experiments** (frozen organisms evolved there).

The roadmap's stage 05 ("Direction after E4") asks for a prey progression ending in "a frozen suite of competent
prey; food other than prey limited", with the gate "captures moving prey from the frozen suite on unseen maps", and
coevolution only after that, "with historical opponents and a frozen evaluation suite". The owner's ladder fits that
row: levels 1 and 2 are the stationary and moving prey, and level 3 supplies the frozen suite.

**What this stage is for.** The owner has not said whether 05 is for the game (a hunter that works) or for the
project's scientific question (does N2's wiring help). This note is written for the first: building a hunter, reusing
what earlier stages built. A null-graph arm that would make it a connectome test is listed as an option (§8), for the
owner to choose or not.

## 2. What already exists and is reused

Checked in the code on 2026-11-04.

**The world** (`wormwars/world.py`) already has, from experiment 01's game:
- several swarms per world, each with its own brain (`World(brain=[...])`), so a hunter and a prey can be
  different controllers in the same world;
- automatic biting (`combat_stage >= 1`): every live wey deposits an attack field one cell ahead of its head, a victim
  takes `damage_k` per unit sampled at head, mid and tail (head armoured), half of it reaches the attacker; no friendly
  fire; a wey with no energy dies and leaves a corpse pellet; the energy ledger checks every transfer;
- the sensors a hunter could use: food scent (stereo, left and right of the head), ally and enemy pheromone, damage
  left and right, collisions;
- Task N's machinery (`task: navigate`, `wormwars/e1/task.py`): a sensing-only scent of a target that moves to the
  next centre of a pre-drawn sequence when the head comes within R; the event table (activation, reach, path
  length); energy off; a 300-tick horizon.

**Scripted controllers** (`wormwars/exp02/scripted.py`, `wormwars/e1/controllers.py`): `Stationary`, `Straight`,
`ConstantMotion`, `PersistentRandomWalk`, `WallFollower`, stereo-proportional steering, and the privileged
`OracleBrain`, which sees the world (`attach_world`). A scripted prey is a scripted brain in the prey's swarm.

**Earlier organisms** (genomes on the local disk, not committed: `runs/exp02-screening/`, `runs/e2/genomes/`,
`runs/e4s1/genomes/`, `runs/e3*/genomes/`, `runs/e4d-evo/`):
- **as hunters**, the navigators of Task N, which is "steer to a scent, reach it, the next one appears":
  - E4s-1's evolved brains (N2 plus the 4-neuron stereo comparator graft): 7.14 targets per 300-tick episode;
  - E1's scripted stereo navigator: 8.68, 98.7% of an oracle that steers at the true target;
  - E2's and 04a's champions (N2 only, no graft): 2.0 to 2.8, on E2d's "non-stereo plateau";
- **as prey**, anything that moves on its own: 02's T1 and T0 foraging champions (N2 or null graphs, 02's interface),
  E2's and 04a's navigators, E4s-1's navigators, and later E3's shuttlers.

**Coevolution** (`wormwars/evo/coevolve.py`): a hall of fame and a frozen opponent suite, for after the gate.

**A lesson from experiment 01** (D026): coevolved swarms got 0.1 to 0.3% of their energy from biting. Biting is
automatic once bodies touch, contact is made by whichever side approaches, and nothing in 01's world made hunting pay.
05 has to make capture the thing that is scored, and check that it is not won by accident (§6's blind controls).

## 3. The task: Task H

Task H is Task N with a living target. The proposal, for review:

- **Two swarms per world:** one hunter (swarm 0) and one prey (swarm 1; later several). Boundary wall only at first;
  "unseen maps" means fresh world ids, and walls or obstacles come in a later level (§4).
- **The prey's scent** is a Gaussian around the prey's mid point, A exp(-d² / 2σ²), Task N's form and settings
  (σ, A, truncation), and it reaches **the hunter's food channels only**. Proposed because every navigator above
  steers on food scent, so they transfer with no retraining. The prey senses the world as it did where it evolved
  (food, for 02's champions). *Alternative for review:* the prey's pheromone trail on the existing
  enemy-pheromone channel (ADL), which needs no new signal but points to where the prey was, not where it is.
- **Capture.** Two rules, one per sub-level, so the first step is exactly a known task:
  - **reach** (Task N's rule): the hunter's head within R of the prey's mid point;
  - **bite:** the prey's energy brought to zero by the hunter's bites, with a prey energy calibrated so that a
    hunter holding contact captures in a fixed number of ticks (to be measured with the scripted hunter).
  After a capture a new prey appears at the next centre of a pre-drawn sequence (Task N's rule: at least D from the
  hunter, clear of the wall), with a fresh brain state.
- **The prey does not bite back** at levels 1 and 2 (its attack deposit is zero). At level 3 this is a choice (§7).
- **Energy off for the hunter** at first (Task N's setting: no drain, no movement cost), so the score is captures per
  episode. "Food other than prey limited" is then trivially true; energy on is a later level.
- **The score:** captures in a fixed horizon (300 ticks, as Task N), with the unfinished leg's progress as Task N's
  tie-break (D103). Logged raw: contacts, bite energy, time to first capture, path length per leg, prey distance.

## 4. The prey ladder

| Level | Prey | Controller | Complexity knob |
|---|---|---|---|
| H1 | static | scripted `Stationary` | reach, then bite |
| H2 | a defined route | scripted route follower (new; privileged like `OracleBrain`): a closed loop through 3 to 5 pre-drawn waypoints, constant speed | prey speed as a fraction of the hunter's maximum, for example 0.25, 0.5, 0.75 |
| H2b | other scripted movers | `PersistentRandomWalk`, `WallFollower` (they exist) | unpredictability, wall contact |
| H3 | earlier organisms, frozen | 02's T1 and T0 champions; E2's, 04a's and E4s-1's navigators chasing their own targets | how purposeful the motion is; whether they react to the hunter |
| H4 (later) | the same on unseen maps with obstacles | E3d's island mazes | the roadmap's gate |

The frozen suite for the gate is chosen from H2, H2b and H3 before any hunter is evolved, and split into training,
validation and test prey (the test suite used once).

## 5. What is new code

Each with a test seen failing first, and an equivalence check that every existing task is unchanged (rule 7):
1. **The hunt task** in the world: two roles, the prey scent on the hunter's food channels only, the capture rules,
   the respawn from a pre-drawn sequence, the event table.
2. **Per-swarm attack strength** (the prey's zero) and, if needed, per-swarm energy settings.
3. **The route follower**, a scripted prey policy.
4. **Organisms as prey:**
   - the world builds one input current of one neuron count for all swarms. A hunter with E4s-1's graft has 306
     neurons and 02's champions 302. Proposed: place each prey genome on the same grafted connectome with the graft
     inert (`Module.without_outputs`), so its worm part is unchanged; an equivalence test checks that it behaves
     exactly as before.
   - one interface is shared by all swarms. 02's champions never sensed an enemy; at H3 their ADL (enemy pheromone)
     and ASH (damage) neurons would receive the hunter for the first time. Kept as it is, and measured (§7).
   - prey that need their own task (navigators chasing hidden targets) need per-swarm targets: Task N allows one swarm
     of one wey. This is the largest piece; it can wait for H3's second half.

## 6. The first step: E5-0, a feasibility check on the CPU

Like E4-D's feasibility check (D262): no evolution, scripted and frozen controllers only.

- **Positive control:** the scripted stereo hunter (E1's navigator on the prey scent) must capture at H1 (reach and
  bite) and at H2 at every prey speed below its own. If it fails, the task is redesigned before anything evolves
  (the roadmap's rule after E1).
- **Blind controls:** `ConstantMotion`, `PersistentRandomWalk` and `WallFollower` hunters, which cannot sense the
  prey, give the accidental capture rate at each level. A level where they score near the positive control is too
  easy.
- **Reused hunters, zero-shot:** E4s-1's evolved navigators, E2's and 04a's champions, and generation 0, on H1, H2 and
  H2b. This answers the owner's "can we use what we built": at which level each one stops capturing.
- **Calibration:** the bite rule's prey energy, and the speed ladder's values, from the positive control.
- **What it answers:** whether the ladder is solvable and not trivial, and where the reused hunters fall off. It does
  not evolve a hunter.
- **Cost (rough, to be checked):** Task N ran at about 300 episodes per second on the GPU in E4s-0; on the CPU with
  two weys per world, perhaps tens per second. A few thousand episodes per controller and level is about one to a
  few CPU hours in all. The code (§5, items 1 to 3) is the larger part: several working sessions, with reviews.

**E5-1, evolution** (GPU, needs the owner's word; designed after E5-0): evolve hunters up the ladder from the best
reused seed, with a scripted ceiling and a seed that is not reused as comparisons, and test on the frozen suite.
A rough guess, before any design: 5 to 20 GPU hours, by analogy with E4s-1 (16.6 GPU hours for 16 runs on Task N).

## 7. Questions for the reviewers

1. **The scent:** a Gaussian on the hunter's food channels (transfer from Task N), or the prey's trail on the enemy
   pheromone channel (no new signal, a trail rather than a position)? Or both, as levels?
2. **Capture:** is "reach, then bite" right for H1? How should the bite rule's prey energy be calibrated, and should a
   capture end in a corpse the hunter can eat (energy on) or simply respawn?
3. **H2's route and speed ladder:** a closed loop at constant speed, at 0.25, 0.5 and 0.75 of the hunter's speed?
   Does a route the hunter could learn by heart (the same loop every episode) need varying?
4. **H3:** which earlier organisms belong in the frozen suite? Should they bite back, and is it acceptable that
   02's champions sense the hunter on ADL and ASH, inputs they never had?
5. **The inert graft** as the way to put 302-neuron prey in a world with a 306-neuron hunter: sound?
6. **E5-0's controls and its decision rule:** what should "solvable" and "too easy" be, in numbers, before it runs?
7. **What is missing** for the roadmap's gate, or from the lesson of 01's coevolution?

## 8. Options for the owner, not decided here

- **A null-graph arm:** the same hunters on 02's or 03's null graphs, which would make 05 a test of the connectome
  rather than only a build. It roughly doubles E5-1's cost.
- **Prey that bite back, and energy on,** at H3 and after.
- **Coevolution** after the gate, as the roadmap says.
