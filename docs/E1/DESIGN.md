# E1: navigation primitive (design v1, for review)

Roadmap v3, Track E, step E1 (and 04a). This is a design, not a pre-registration. Nothing below
has been run.

**Order:** T0's GPU items and T1 come first. This design is drafted early, while the GPU is busy,
so the reviewers can shape it.

## What E1 must show (roadmap v3)

- **A positive control first.** A scripted navigator must reach **moved targets** with the
  declared body and sensors, before any evolution. If it cannot, the body or sensors are
  redesigned first, for example by adding head oscillation for sensing over time.
- **The gate:** it reaches moved targets on **unseen layouts** and beats **simple movement
  baselines**. Food collection alone is not enough.
- **Bridge 1 (optional):** also build the module on two of 03's validated null ensembles.

## Why a new task

Experiment 02's champions circled rather than navigated. 02b found them slowing on food and
steering weakly by side, and 02 found the left-right difference worth little score. In 02's
tasks, several food patches plus odour make circling near food a good strategy, so reaching a
place is never required. E1 needs a task where the only way to score is to go somewhere
specific, and where the place changes.

## Task N (proposed)

- **One target at a time, per wey.** A single small target, sensed as odour through the existing
  food channel. That is the same sensors (AWA, AWC and ASE left and right) and the same blur.
  - **Proposed:** a single food patch of radius 1.5, `food_odour_sigma` 2.
- **Reached** when the wey's head is within the target radius. The target then **moves**: it
  respawns at a uniformly random free location at least D = 8 cells away, drawn from a per-world
  keyed RNG, so that respawns are reproducible and pair across strains.
- **Score:** targets reached per episode. The secondary measure is the median time to reach.
  Energy and eating are switched off as score components, so "food collection alone" cannot score.
- **World:**
  - one swarm and one wey per world, so there is no crowding or contact, and it is cheap;
  - hazards, pheromones and combat off;
  - walls on;
  - 300 ticks;
  - arena and spawn as T0.
- **Unseen layouts:** targets and spawns come from world ids. Training, tuning and hold-out ids are
  disjoint, as in `SeedPool`.
- **Implementation:** a target mode in the world. It reuses the food field for the odour, places
  one patch, detects the reach, and respawns. It records every reach in an event ledger, with the
  tick, the world and the distance travelled, as E3 will need.

## The positive controls (scripted, same body and sensors)

- **K, from 02:** level kinesis. Speed depends on the sensed level, and turns are random. This is a
  *baseline*, not a navigator.
- **S, stereo klinotaxis:** turn toward the stronger side, with a gain proportional to (L − R) and
  forward speed scaled by level. This is 02's StereoKinesis family, retuned for Task N.
- **M, temporal (klinokinesis with memory):** compare the current level with a running average,
  and turn more when it falls. This is 02's MemoryKinesis, retuned. It uses mono or averaged
  sensing, so it does not rely on stereo.
- **Tuning:** each is tuned on tuning worlds by `tune_batched`, and scored on hold-out worlds.

## The simple movement baselines

- **Straight, turning at walls.**
- **A random walk** matched to S's mean speed and turn rate.
- **Circling** at 02's typical champion curvature.

## The gate for the positive control

- **Primary:** the best of S or M reaches at least 2 times as many targets per episode as the best
  baseline on hold-out worlds, with a paired 95% interval over worlds excluding a ratio of 1.5.
- **Also required:** a median time to reach below half the episode, for the navigator.
- **If neither S nor M passes:** the task or body is changed before any evolution. The options are
  head oscillation, a larger sensing offset, or a stronger gradient. The change is recorded, and
  the controls are rerun.

*All thresholds here are proposals for review.*

## 04a: the evolved navigation primitive (after the gate)

- **Evolution:**
  - N2 brains, the T1 optimizer settings from 02 (single island), on Task N's training worlds;
  - the budget is fitted to T1's measured throughput;
  - several independent runs, which are the unit of analysis.
- **Gate (roadmap v3):**
  - reaches moved targets on unseen layouts;
  - beats the simple movement baselines;
  - reported against the scripted navigators S and M as positive references.
- **Module save and load:**
  - saving and loading a champion, with the interface it was evolved on, its world settings and
    its evidence: the hold-out scores and the gate result;
  - a replay reproducing the hold-out score. Exact on CPU, and within T0's declared tolerance on
    CUDA;
  - only what 04a needs. The full assembly layer waits for 04b (the roadmap's tripwire).
- **Bridge 1 (optional, reported separately):** the same on SH and SH-route ensembles from 03,
  with several graphs each.

## Open questions for review

1. **Is one wey per world right?** Or does the primitive need to cope with others' bodies
   (collisions) from the start, since E3 has a colony?
2. **Should the target be sensed through the food channel,** reusing the food neurons, or through
   a new channel? E3 needs A and B targets that are distinguishable. Reusing food for A and a
   pheromone channel for B is one option.
3. **Should reaching be scored as a count**, which rewards speed and repetition, or as time to
   first reach?
4. **Are the gate thresholds (2 times, 1.5, half the episode) reasonable,** or should they come from
   a pilot, as 03's margins did?
5. **Does "moved targets" mean respawn after a reach, as proposed,** or targets that move during
   approach?
6. **Anything that would make E1 uninformative for E3** (the A/B shuttle)?
