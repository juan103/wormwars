You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

A focused design question for experiment 02's screening, before any N2 run. Please be concrete.

Context: the working directory is the WormWars repo. Read `experiments/02-screening/DESIGN.md`,
`wormwars/world.py` (`_build_maps`, `_sensor_signals`, `_eat`), `wormwars/config.py` (MapConfig,
WorldConfig), `wormwars/exp02/scripted.py` and `experiments/02-screening/diagnostics.json`.

## What was found

T1 ("mono" chemotaxis: one food sample at the head, copied to both sides) was meant to require
temporal comparison. Its pre-N2 gate was: a one-step-memory scripted controller must clearly beat
the best memoryless one. On the first, narrow tuning grid it did (0.923 vs 0.597 on 1408 held-out
worlds). But the memoryless controller's tuned values sat on the grid edges, and on a widened grid
it scores **1.457** (fast 1.0 off food, slow 0.45 on food, threshold 0.01, constant gentle turn
0.15), while a widened memory controller scores **0.943**. The memoryless controller also beats the
tuned *stereo* steering controller on T0 (~1.38). Tuning worlds, 400 ticks, single swarm of 20.

The reason, as I read the code: food is compact patches (radius 2.5-5 cells, 3-6 patches), and
sensing samples the food field directly, so there is no signal at all beyond a patch edge. Foraging
here is "search, then slow down on food" (kinesis). Neither mono nor stereo sensing needs a
gradient, and in 01b stereo added nothing over kinesis either.

## Proposed redesign (not yet built)

Give food a long-range odour. A new, opt-in world option: the sensed food signal is a Gaussian
blur of (food + pellet) with sigma S cells (default 0, meaning today's behaviour, so every earlier
experiment reproduces). It is recomputed each tick as food is eaten. Both T0 (stereo) and T1 (mono)
use the odour world, so they differ only in the number of noses. The 01b anchor keeps today's
settings. Map parameters (patch count and radius, S) are re-tuned on scripted controllers only, so
that for T1 a klinotaxis-style memory controller clearly beats the best tuned memoryless one (with
wide grids, on held-out worlds). T0's stereo controller should beat both. N2 never touches tuning.

## Questions

1. Is this the right fix? Is there a cheaper or cleaner way to make T1 require temporal comparison
   in this simulator?
2. What new failure modes does an odour field introduce? For example, a gradient so smooth that a
   fixed-heading or kinesis policy still wins, blur edge effects at the walls, the speed of
   pheromone-like diffusion vs body speed, eaten patches leaving stale odour, or cost.
3. What should the gate be, exactly: which controllers, which grids, what margin, on which worlds,
   so that "T1 needs memory" is actually established, and "T0 benefits from stereo" too?
4. Does anything already measured (calibration, remap selection, the probes) need redoing if the
   sensed food signal changes? Calibration is measured in-world, so I expect it does.
5. Anything else that would make continuing a mistake?

Numbered answers; mark each MAJOR or MINOR. Check the code where you can.
