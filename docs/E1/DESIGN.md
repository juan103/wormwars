# E1: navigation primitive (design v2.1)

Roadmap v3, Track E, step E1 (and 04a). This is a design, not a pre-registration. Nothing has been
run.

- **Order:** foundation milestones T0's GPU items and T1 come first. "T0" and "T1" in *this* file
  mean the roadmap's foundation milestones. Experiment 02's tasks are written "02-T0" and "02-T1".
- **v1 review:** Astra 6 and Fable 5.1 both answered "proceed to v2" (`docs/reviews/*-E1/`,
  D077), with largely the same must-change points. v2 adopts all of them, after the key claims
  were checked in the code.
- **v2 review:** both answered "E1 v2: ready to implement" (`docs/reviews/*-E1b/`, D078). v2.1
  makes their text edits, which are due before the pilot.

## What E1 must show (roadmap v3)

A scripted navigator reaches **moved targets** with the declared body and sensors before any
evolution. The gate is that it reaches them on **unseen layouts** and beats **simple movement
baselines**; food collection alone is not enough.

As both reviewers put it, the controller must show that *target information* improves arrival,
not merely that arrivals happen. Good search (circling, wall-following, coverage) also collects
hits. The distinction is functional, not the controller's name: a temporal or foraging-derived
policy that reliably follows the current cue to moved destinations qualifies.

## Why a new task

- In experiment 02's tasks, several food patches plus odour make staying near food a good
  strategy.
- 02 found the left-right difference worth little score.
- 02b found the champions' turn commands *covaried* with the food side in replays: an
  association, not evidence of steering (02b's corrected wording).
- E1 needs a task where scoring requires going to a specific place that changes.

## Task N: all mechanics specified (both reviewers)

**The world:**
- one swarm, one wey per world. Its own body still enters the body field and the collision
  sensors;
- walls: the boundary ring only;
- hazards, pheromones and combat off; `food_patches` = 0; `hazard_patches` = 0.

**Energy is off for this task:**
- **the target is sensing-only.** It is added in `_sensed_food` and never written into
  `fields[FOOD]`. `total_energy` sums the FOOD channel, so a relocatable blob there would show up
  as ledger error (both, D078). The ledger test covers relocations;
- metabolic drain 0, movement cost 0, eating off (`eat_rate` 0);
- the wey lives for the whole horizon, and there are no corpse pellets;
- the target is a scent source, not food: it is never depleted, and moving it creates or destroys
  no energy. The ledger stays balanced by construction, and T0's ledger check still runs;
- (v1 left the energy physics running: a non-eating wey would die near tick 286 of 300, and its
  corpse would enter the sensed field. Fable.)

**The target:**
- a scent source written into the sensed food field;
- its physical radius R, amplitude A and blur σ are set directly, and **bypass the map builder's
  headcount scaling**. With one wey, that scaling would shrink a radius of 1.5 to about 0.34
  (checked: `world.py`, around line 370);
- **reached** when the head is within R of the centre;
- the sensing scale keeps the peak below the input clamp.

**The pilot chooses σ, A, R and D**, and the chosen values go in the pilot configuration. σ is one
of 2, 3, 4 or 6.
- **The blur is truncated at ceil(3σ) along each axis** (checked: `world.py`, `gaussian_blur`), so
  its support is a square, reaching farther diagonally. Amplitude cannot restore signal where the
  field is zero. So coverage is measured from the **actual sampled field** (Astra, D078).
- **The σ rule works on actual leg starts,** from each previous centre to the next, which do not
  depend on the controller (Fable, D078). The pilot picks the smallest σ at which a declared share
  of leg starts sit above a declared **usable-signal floor**. The support edge, about 1% of peak on
  an axis, steers nothing at realistic gains. Clamp saturation is measured too.
- **Geometry:**
  - consecutive goal discs are disjoint, D > 2R, so each arrival is a new approach;
  - a maximum separation may be declared;
  - wall clearance is checked against the chosen R (Astra).

**Target sequence, pairable across strains (Astra, Fable):**
- a fixed sequence per world: target k's centre is a function of (evaluation seed, world id, k)
  only;
- consecutive centres are at least D apart, and every centre is at least 3 cells from a wall.
  About 26% of uniformly placed targets would otherwise be in reach of a pure wall-slider (Fable);
- the first target is at least D from the spawn;
- nothing depends on the wey's position, so every controller faces the same destinations;
- layouts depend on both `run_seed` and world id, and every comparison shares both (Astra);
- controller state persists across relocations. Resetting it would be hidden help (Astra).

**The score** is targets reached in a fixed horizon (300 ticks), which is what selection and tuning
use. It needs plumbing: `rollout`'s `_play` hard-codes `foraging_score` (checked), so rollouts
and `tune_batched` gain a score selector, not only a world mode (Astra).

**Event record** (a fixed-shape table, not a framework): controller or run id, world, target
index, target position, activation tick, reach tick (or none), and leg path length. Unfinished
legs are kept, for failure-aware timing.

**Reproducibility:**
- the score is an integer count;
- the declared check is exact equality of counts and event sequences under deterministic replay
  (CPU, or CUDA `replay_mode`) with the same code version;
- default CUDA is not expected to reproduce counts exactly. A flipped reach changes the score by
  1, and T0's 1e-4 bound for a continuous score does not transfer (both).

## Controls, described correctly and all tuned the same way

**Existing families** (`wormwars/exp02/scripted.py`), with v1's descriptions corrected:
- **K:** level kinesis. Speed depends on level, with a **constant** turn (not random turns).
- **M:** `OneStepMemory` and `MemoryKinesis` compare with the **previous tick** (not a running
  average).
- **S:** stereo steering added to a constant turn, with a two-level speed.

**Navigator variants for arrival:**
- **S-const:** constant-speed stereo steering. Slowing near food helped eating, not arrival.
- **M-avg:** M on the average of the two stereo readings, for a clean comparison with S.

**S-const is defined as `StereoKinesis` with slow = fast and the turn in the grid,** including 0.
`StereoProportional` has no constant turn: with no signal it would go straight and jam in a
corner (Fable, D078).

**Blind baselines**, tuned on the same tuning worlds with `tune_batched` (both):
- constant speed × constant turn, which covers circling at any curvature;
- a persistent random walk (turn persistence and rate tuned);
- a **wall-follower** using the declared collision inputs. Its thresholds sit above the collision
  readings the wey's own body produces (Fable, D078). `ScriptedBrain` passes policies food
  readings only, so it gains the collision readings, and every control gets the same access.
  There are no privileged coordinates.

**Reference points:**
- tuned K;
- an **oracle** that steers at the true target position. It is not a control; it gives the
  achievable ceiling (Fable). Its position, heading and target plumbing is privileged, so it stays
  outside `ScriptedBrain`'s observation path (Fable, D078);
- optionally, a few frozen 02 champions, as a check only.

**Gain:** 02's stereo grid runs to k = 8192, which is effectively bang-bang. S is also reported at
gains k ≤ 32, which a brain can plausibly reach (Fable).

## The gate for the positive control

**Pilot first.** On tuning worlds only, and counted with T0's accounting, the pilot measures:
- zero-signal coverage and clamp saturation for each σ;
- every control's arrival counts;
- the share of episodes with at least 1 and at least 2 arrivals;
- the share of generation-0 random genomes scoring zero, since sparse counts may give no selection
  pressure;
- throughput on Task N.

From the pilot, the task parameters, controller settings, margins and sample sizes are fixed.
Which navigator (S-const or M-avg) goes forward is chosen **on tuning data**. Everything is frozen
before the gate worlds are used, and the gate worlds are used once.

**The freeze is a committed file,** whose hash the gate run records (Fable, D078). It fixes:
- the task configuration (σ, A, R, D, the horizon);
- the gains;
- the selected navigator, tuned or k ≤ 32 as declared;
- the tuned baselines;
- every numerical threshold;
- the interval method (paired, with the sidedness stated);
- the cue intervention;
- the sample sizes;
- the execution mode.

**Gate rules** (the numbers are set by the pilot; the structure is fixed now):
1. **Absolute reliability:** the navigator reaches at least 2 targets in at least a declared share
   of hold-out episodes. The second arrival tests relocation.
2. **Beats the baselines:**
   - the paired difference in counts over hold-out worlds, navigator minus *each* tuned blind
     baseline and tuned K;
   - the lower 95% bound must exceed a declared margin;
   - no ratio against a near-zero baseline (the roadmap's own scoring rule).
3. **Uses the cue:**
   - with the scored target unchanged but its scent displaced, the navigator's count must fall
     by a declared amount (Astra).
   - **The displacement:** the existing `mirrored` probe reads the field at the point reflection
     of each sample point, about (11.5, 11.5), not the arena centre. That creates a consistent
     decoy at the reflected target.
   - A navigator will park at the decoy, so its count can fall *below* the blind level, not only
     toward it (Fable, D078).
   - The `constant` probe is reported, non-gating, as each controller's own blind level;
   - reported as a fraction of the oracle.
4. **Secondary:**
   - first-arrival success;
   - latency as the mean of min(first-arrival time, horizon), so failures count;
   - leg times reported separately;
   - path efficiency: straight-line distance over path length per reach.

**Id ranges:** separate ranges for the task pilot, tuning, the positive-control gate and 04a's
hold-out.

**If no navigator passes:**
- the implementation, the signal availability, constant-speed steering and the search behaviour
  are diagnosed first;
- the sensors or body change only if that diagnosis points there (Astra). Head oscillation is
  one option, a stronger or wider cue another;
- one valid passing navigator is enough to establish that the task can be done.

## 04a: the evolved navigation primitive (after the gate)

**Evolution:**
- N2 brains, 02's optimizer settings (one island), and the Task N count as fitness;
- the budget is fitted to T1's measured throughput;
- the number of independent runs is set before the runs. The run is the unit of analysis. Worlds
  quantify uncertainty for one controller; arrivals are not independent replicates (Astra).

**Shaping:**
- if the pilot shows generation-0 counts mostly zero, a bounded shaping term is declared: the
  fractional progress toward the current target;
- it is used in training only, recorded, and removed from the benchmark (the roadmap's scoring
  rules);
- it is capped below the value of one arrival per episode (Fable, D078).

**Gate** (numbers fixed before the hold-out, from the pilot and the scripted results):
- reaches moved targets on unseen layouts, with the same reliability, baseline and cue-use rules
  as the positive control;
- beats a **generation-0** baseline (the standing rules);
- reported beside S-const, M-avg and the oracle;
- the pass rule: at least a declared share of the independent runs pass.

**Module save and load:**
- the existing bundle and genome file, plus the interface. The input is recorded as "goal cue,
  left and right, at AWA, AWC and ASE";
- the world settings, the evidence (hold-out counts, gate result), and a deterministic replay
  check;
- nothing more, because of the tripwire.

**Bridge 1:** deferred until E3 runs. It is not on the path to the organism (both).

## What E1 does and does not establish for E3 (the A/B shuttle)

**The input mapping is a commitment now** (Astra):
- one canonical left/right goal-cue input, at the existing food neurons;
- in E3, A's observations go to those inputs of copy A, and B's to the same inputs of copy B;
- the A/B identity and the visit confirmation stay world-level and selector-level, not new sensor
  channels;
- a frozen module is never fed through other neurons (ASK, ADL) it was not trained on.

**E1 validates** approach to a *localised* source with no interior walls.

**It does not validate:**
- following narrow, decaying trails;
- junctions;
- wall occlusion (the blur ignores walls);
- colony robustness.

**E3 will begin with a small bent-trail and junction check,** and will declare what walls block. A
non-gating probe on a line-shaped source may be added to E1's pilot (Fable). No maze framework is
built now.

## Implementation scope (the tripwire)

- a target mode in the world, sensing-only;
- the oracle's privileged plumbing, kept outside scripted observations;
- a score selector in rollouts;
- the collision readings for scripted controls;
- the fixed event table;
- the new scripted variants and baselines.

**Targeted tests:** target sequencing and pairing, score selection, ledger balance with energy
off, deterministic replay of counts and events, and batch and chunk invariance.

**Not built:** a general event framework, a module registry, a channel router, or a reusable task
framework.
