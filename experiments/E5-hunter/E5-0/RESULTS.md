# E5-0: Task H's feasibility check. Results

*Draft 2, 2026-11-06, after one round of review (Astra 6 and Fable 5.1: both "fix then publish"; every fix taken;
[`docs/reviews/20261106-E5-0-results/`](../../../docs/reviews/20261106-E5-0-results/)). Exploratory (not a
pre-registration); its decision rules were fixed in [`docs/E5/E5-0-PLAN.md`](../../../docs/E5/E5-0-PLAN.md) (draft
2, with §10's dated amendments) before it ran. The numbers come from `summary.json` (written by
`scripts/e5_0_summary.py` from the committed stage records, which hold them unrounded), except §6's, which come from
`phases.json`, written after the reading.*

## What came out

1. **The new code passed every equivalence check the plan specified.** On the CPU, the engine with E5's hooks gives
   the same bits as the engine before them on 68 arrays. A prey with no body (H1-ghost) gives the same per-world
   counts, capture ticks and path lengths as Task N for nine hunters under the `real`, `constant` and `mirrored`
   probes, and the same per-tick traces under the real scent.
2. **Every one of the 18 read settings is "solvable", and none is "too easy".** The observation-limited positive
   control (E1's S-const, tuned per setting) catches at least once in every one of the 512 evaluation episodes at
   every setting. The lower bound on its advantage over the best blind or stationary baseline is 3.61 to 8.06
   captures per episode. The best baseline scores 2.8% to 11.2% of it, so the 25% flag never fires.
3. **The reused hunters stop qualifying in three different places:**
   - **E4s-1's 16 champions** (N2 plus the stereo graft) qualify at all 18 settings, zero-shot. None falls off on any
     speed series. Each champion's captures peak at a route speed between 0.2 and 0.7, and all finish lower at 1.0.
   - **L1 on its carrier** (the 4-neuron comparator, not evolved) also qualifies at all 18. On fast prey it is the
     best neural hunter: at route speed 1.0 it makes 4.12 captures, more than any E4s-1 champion (at most 3.14; their
     mean is 2.04).
   - **E2d's 47 champions** (N2 only, 302 neurons) mostly qualify at the static rungs (45 at H1-reach, 34 at
     H1-bite), but not once the prey moves. On the route they first fail to qualify at speeds from 0.1 to 0.6. The
     most common point is 0.4, where 18 stop (12 by demonstrated failure, 6 uncertain). On the random walk they stop
     at 0.25, 0.5 or (one genome) 0.75; on the wall follower, at 0.25 or 0.5. None qualifies at a route speed of 0.6
     or more.
   - **Generation 0** never qualifies (demonstrated failure at every setting, for all 16 genomes).
4. **The stereo difference matters to E4s-1 and L1, much less to E2d.** Feeding both noses their mean costs E4s-1's
   champions 1.13 captures on average at H1-bite (from 0.10 for run 12 to 2.97 for run 13). It costs E2d's champions
   0.01 on average: 11 of 47 lose a small but bounded amount, at most 0.10. This is part of the gap between the
   families, not all of it. Under the `mean` probe E4s-1's champions still average 1.62 captures at H1-bite, more than
   E2d's intact 1.02.
5. **Route speed does not order the difficulty for the scripted hunters.** Faster route prey are caught more often by
   both fixed-parameter references: E1's frozen S-const rises from 4.57 captures at speed 0.1 to 7.72 at 1.0, and the
   pursuit reference from 4.34 to 8.11, though neither rises at every step. The tuned positive control goes from 4.57
   to 7.72. E5-1's ladder therefore cannot be set "from where the positive control falls off" (SCOPE.md §4): it does
   not fall off.

E5-0 used 7.94 of its 8 recorded CPU hours (3.8 minutes to spare), with no cut and no probe left untested. Nothing ran
on the GPU.

## What ran

All six stages ran on commit `7d25460` (D387, pushed, CI green), on the CPU, on 2026-11-06 from 01:07 to 09:04 UTC.
The stages were bench, equivalence, calibrate, evaluate, probe and read: one attempt each, each with rc 0.

The records are in this folder: `bench.json`, `equivalence.json`, `calibration.json`, `evaluation.json` (per-world
counts), `probes.json`, `reading.json`, `compute-record.json` and the start markers. The per-setting summaries of the
event tables are committed in `runs/e5-0/evaluation/*.json`. The tables themselves stay local in
`runs/e5-0/evaluation/*.npz` (440 MB).

**Compute** (`compute-record.json`: the accounting's synchronised wall-clock seconds, by category):

| Category | Hours |
|---|---|
| tuning (the scripted controls, per setting) | 1.60 |
| final (the evaluation) | 3.74 |
| probe (fixed and qualification probes) | 2.34 |
| measure (bench, equivalence with its reference runs, read) | 0.21 |
| calibration (route check, E_prey) | 0.05 |
| **total** | **7.94** of the 8-hour cap |

**Bench's projection:** 7.32 hours for what it covers, which is the equivalence check, the calibration with its
tuning, the evaluation and the fixed probes. The plan stages the qualification probes after the main pass instead of
projecting them (§8). All of them fit, with 228 seconds left. The margin was thin: on a slower machine some genomes'
cue dependence would have read "untested", as §8 allows. The plan's §8 also miscounts the tuning grids as 379 points;
there are 487, which gives the 592 192 tuning episodes that ran. Bench used the actual grids. A dated note in §10
records this.

## 1. Is the new code right? (plan §4)

- **Old engine against new** (`equivalence.json`, `old_against_new`): **identical** on 68 arrays, on the CPU. The old
  side is the engine at `ab749bb`, in a clean worktree whose head was checked; the new side is `7d25460`. The arrays
  cover:
  - Task N on the 512 equivalence worlds with E1's frozen S-const, the oracle, E4s-1 run 0's champion and E2's GA run
    0 champion;
  - per-tick positions, headings, input currents and neural states for all four on 8 worlds;
  - a random two-swarm fight, and a placed fight that bites from the first tick.
- **H1-ghost against Task N** (`ghost_against_task_n`), on the same 512 worlds: **identical**. This covers the
  per-world counts, capture ticks and path lengths of the nine hunters of §4.2 under the `real`, `constant` and
  `mirrored` probes. The per-tick traces on 8 worlds, also identical, were run under the real scent only.
- **The CUDA gap** (reported, not a gate): E1's frozen navigator on the CPU, against E1's committed CUDA gate record
  on its 1 024 worlds. The CPU gives 8.6846 targets per episode, the record 8.6797; 92.7% of worlds are identical.
  This uses E1's committed counts; nothing ran on the GPU.
- **Checks during the run:**
  - **The ledger** balanced at every tick of every episode: the largest relative residual is 2.3 × 10⁻⁷, against the
    limit of 10⁻⁵.
  - **The pin's log** reads zero at every setting, as predicted, since crowding never acts one-on-one.
  - **The attack-disabled pursuit** at H1-bite made no capture (`reading.json`) and did no damage (`phases.json`,
    0.0, from the local event table). The evaluate stage stops on either, so its completion is also evidence.

## 2. Calibration (plan §3)

- **E_prey = 1.375:** 10 × the median damage per tick in the held contact, 0.1375, over the 64 calibration worlds
  (minimum 0.0764). The stop rule did not fire: 1.375 is larger than the largest single-tick damage seen in the held
  fixture and the driven approaches, 0.1375. The plan's indicative prediction of 0.6 to 1.2 was low (§10). So a kill
  needs at least 10 ticks in which a bite lands.
- **Driven approaches** by the pursuit reference, starting 3 cells away, 64 worlds each, every first life captured.
  Kill times (first contact to capture), median and range:

  | Approach | Median | Range |
  |---|---|---|
  | from the head | 26 | 23 to 46 |
  | from the side | 18 | 7 to 24 |
  | from the rear | 22 | 8 to 25 |

  Kill times below 10 ticks do not contradict the 10-tick minimum. "Contact" is the hunter's head within 1.5 of a
  prey body point, and the bite point is 0.9 ahead of the head, so bites can land before contact is logged. Kill time
  from first contact is therefore not a count of biting ticks. Placements outside the arena were clamped: 1 (head),
  0 (side) and 12 (rear) of 64.
- **The route follower passed** at its first settings (gain 2, spacing 6), at every speed, in 64 of 64 worlds jointly:
  - its median path per tick equals the commanded speed, from 0.035 at s = 0.1 to 0.35 at s = 1.0;
  - its median laps in 3 000 ticks run from 2 to 23.5;
  - every world stays within the 1% limit on moves the arena limits.

  In the evaluation, no route prey's move was limited at any H2 setting.
- **H2b's movers.** The realised speed is the median with a stationary hunter. The share of moves the arena limits
  pools every hunter's evaluation at that setting.

  | Mover | s = 0.25 | s = 0.5 | s = 0.75 |
  |---|---|---|---|
  | random walk: realised speed (nominal) | 0.087 (0.0875) | 0.163 (0.175) | 0.230 (0.2625) |
  | random walk: moves limited | 4.7% | 16.8% | 27.4% |
  | wall follower: realised speed (nominal) | 0.087 (0.0875) | 0.175 (0.175) | 0.262 (0.2625) |
  | wall follower: moves limited | 0.01% | 0.43% | 2.0% |

  **At the two faster speeds, the random-walk prey spends much of its time pressed against the wall.** The plan set a
  limit only for the route follower, so this is reported, not a failure. It does mean H2b's random walk is partly a
  wall-hugging prey.
- **Tuning** (`calibration.tuned`): `summary.json` gives each setting's winners and their tuned means on the 64
  calibration worlds. The tuned S-const's parameters vary by setting:
  - its gain ranges from k = 64 to E1's 8192, its speed from 0.6 to 1 and its constant turn from −0.2 to 0.2;
  - at route speeds 0.4 to 0.7 the winner is a low-gain, slower follower (k = 64, speed 0.6 or 0.8), where E1 used
    k = 8192 and speed 1.

## 3. Is each rung solvable, and is it too easy? (plan §6)

Means are over the 512 evaluation worlds, in captures per 300-tick episode.
- **Advantage LB** is the lower bound of the positive control's paired advantage over the best baseline, which is
  recomputed in each resample.
- **Ratio** is the best baseline's mean over the positive control's, with its 90% interval.

| Setting | Positive control (advantage LB) | E1-frozen S-const | Pursuit | Best baseline | Ratio | Reading |
|---|---|---|---|---|---|---|
| H1-ghost (bridge) | 8.65 | 8.67 | 8.75 | | | no rule read |
| H1-reach | 8.65 (8.06) | 8.67 | 8.75 | wall-follower 0.51 | 0.059 [0.054, 0.065] | solvable; not too easy |
| H1-bite | 4.60 (4.26) | 4.52 | 4.48 | constant 0.28 | 0.060 [0.052, 0.069] | solvable; not too easy |
| H2-0.1 | 4.57 (4.17) | 4.57 | 4.34 | constant 0.34 | 0.074 [0.065, 0.083] | solvable; not too easy |
| H2-0.2 | 4.86 (4.54) | 4.90 | 4.87 | constant 0.27 | 0.056 [0.049, 0.064] | solvable; not too easy |
| H2-0.3 | 5.01 (4.66) | 5.05 | 5.02 | constant 0.29 | 0.059 [0.051, 0.067] | solvable; not too easy |
| H2-0.4 | 5.32 (4.99) | 5.02 | 4.99 | constant 0.26 | 0.048 [0.043, 0.055] | solvable; not too easy |
| H2-0.5 | 5.70 (5.39) | 4.97 | 4.90 | constant 0.24 | 0.042 [0.039, 0.049] | solvable; not too easy |
| H2-0.6 | 6.22 (5.88) | 4.88 | 4.85 | constant 0.26 | 0.042 [0.038, 0.048] | solvable; not too easy |
| H2-0.7 | 6.46 (6.13) | 5.29 | 5.25 | stationary 0.25 | 0.038 [0.033, 0.044] | solvable; not too easy |
| H2-0.8 | 7.12 (6.80) | 6.23 | 6.47 | stationary 0.25 | 0.036 [0.032, 0.041] | solvable; not too easy |
| H2-0.9 | 7.40 (7.07) | 7.26 | 7.66 | stationary 0.26 | 0.035 [0.032, 0.040] | solvable; not too easy |
| H2-1 | 7.72 (7.40) | 7.72 | 8.11 | stationary 0.26 | 0.034 [0.030, 0.038] | solvable; not too easy |
| H2b-walk-0.25 | 4.59 (4.37) | 4.60 | 4.65 | constant 0.16 | 0.035 [0.029, 0.042] | solvable; not too easy |
| H2b-walk-0.5 | 4.38 (4.19) | 4.36 | 4.46 | random-walk 0.12 | 0.028 [0.025, 0.034] | solvable; not too easy |
| H2b-walk-0.75 | 4.37 (4.16) | 4.37 | 4.55 | wall-follower 0.14 | 0.032 [0.029, 0.038] | solvable; not too easy |
| H2b-wall-0.25 | 4.37 (4.06) | 4.27 | 4.24 | wall-follower 0.24 | 0.055 [0.047, 0.063] | solvable; not too easy |
| H2b-wall-0.5 | 4.14 (3.61) | 4.12 | 4.18 | wall-follower 0.46 | 0.112 [0.101, 0.123] | solvable; not too easy |
| H2b-wall-0.75 | 4.68 (4.39) | 4.60 | 4.68 | constant 0.22 | 0.048 [0.041, 0.055] | solvable; not too easy |

- **The positive control catches in every episode:** its share of episodes with a capture is 1.0 at every setting,
  with bounds [1.0, 1.0].
- **Biting roughly halves the static rung:** 8.65 captures at H1-reach, 4.60 at H1-bite.
- **At fast route prey, the best baseline is the stationary hunter** (0.25 to 0.26 from s = 0.7): the prey's own path
  brings it to a motionless hunter's mouth. It is still a small fraction of what the positive control catches.
- **The pursuit reference is not an upper bound.** It aims at the prey's head. The tuned S-const's mean is above it by
  0.33 to 1.37 captures at route speeds 0.4 to 0.8, and by smaller amounts at a few other settings; it is below it at
  H2-0.9 and H2-1. These are point comparisons, without intervals.
- **E1's frozen S-const falls below the tuned one at route speeds 0.4 to 0.8.** The tuned parameters do better there.
  Gain, speed and turn changed together, so this does not isolate any one of them.
- **Tuning on 64 worlds is slightly noisy.** At H1-ghost the tuned S-const scores 8.65 and E1's frozen one 8.67 on the
  same worlds.

## 4. Where do the reused hunters stop qualifying? (plan §5, §6)

[`genomes.md`](genomes.md) reports every genome on its own: its mean and reading at all 19 settings. The table below
gives, by family, the mean of the genomes' means and how many genomes qualify:

| Setting | E4s-1 (16) | L1 carrier | E2d (47) | Generation 0 (16) |
|---|---|---|---|---|
| H1-ghost (bridge) | 7.41 | 5.15 | 2.09 | 0.06 |
| H1-reach | 7.33 (16) | 5.15 (Q) | 2.09 (45) | 0.06 (0) |
| H1-bite | 2.75 (16) | 2.13 (Q) | 1.02 (34) | 0.03 (0) |
| H2-0.1 | 3.06 (16) | 2.84 (Q) | 1.31 (41) | 0.10 (0) |
| H2-0.2 | 3.52 (16) | 3.24 (Q) | 1.30 (40) | 0.19 (0) |
| H2-0.3 | 3.56 (16) | 3.44 (Q) | 1.16 (30) | 0.22 (0) |
| H2-0.4 | 3.55 (16) | 3.61 (Q) | 0.92 (12) | 0.22 (0) |
| H2-0.5 | 3.59 (16) | 3.75 (Q) | 0.69 (1) | 0.22 (0) |
| H2-0.6 | 3.54 (16) | 4.04 (Q) | 0.56 (0) | 0.22 (0) |
| H2-0.7 | 3.29 (16) | 4.38 (Q) | 0.48 (0) | 0.23 (0) |
| H2-0.8 | 2.93 (16) | 4.51 (Q) | 0.43 (0) | 0.23 (0) |
| H2-0.9 | 2.47 (16) | 4.40 (Q) | 0.38 (0) | 0.24 (0) |
| H2-1 | 2.04 (16) | 4.12 (Q) | 0.35 (0) | 0.24 (0) |
| H2b-walk-0.25 | 3.06 (16) | 2.89 (Q) | 0.93 (23) | 0.05 (0) |
| H2b-walk-0.5 | 2.77 (16) | 2.89 (Q) | 0.54 (1) | 0.10 (0) |
| H2b-walk-0.75 | 2.44 (16) | 3.11 (Q) | 0.32 (0) | 0.12 (0) |
| H2b-wall-0.25 | 2.99 (16) | 3.01 (Q) | 0.81 (10) | 0.06 (0) |
| H2b-wall-0.5 | 2.55 (16) | 3.14 (Q) | 0.23 (0) | 0.12 (0) |
| H2b-wall-0.75 | 2.05 (16) | 3.30 (Q) | 0.12 (0) | 0.12 (0) |

**Falls off** is the first tested speed in each series where a genome does not qualify (`summary.json`, `falls_off`).
Not qualifying covers both demonstrated failure and "uncertain".

| Series | E4s-1 | L1 | E2d | Generation 0 |
|---|---|---|---|---|
| H2 (0.1 … 1.0) | none (16) | none | 0.1: 6, 0.2: 2, 0.3: 9, 0.4: 18, 0.5: 11, 0.6: 1 | 0.1: 16 |
| H2b random walk | none (16) | none | 0.25: 24, 0.5: 22, 0.75: 1 | 0.25: 16 |
| H2b wall follower | none (16) | none | 0.25: 37, 0.5: 10 | 0.25: 16 |

- **One recovery:** 04a run 4 fails the route at 0.1 and qualifies at 0.2. It is uncertain at 0.3, and demonstrably
  fails from 0.4.
- **E2d fails by reliability first.** With about one capture per episode, its share of episodes with any capture drops
  below 0.80 before its advantage over the baselines drops below 0.5. Of the 18 that stop at H2-0.4, 12 fail on
  reliability alone and 6 are uncertain.
- **E4s-1's champions at speed 1.0** range from 1.39 captures (run 10) to 3.14 (run 13). They all qualify everywhere:
  - their family mean is about 3.5 to 3.6 from s = 0.2 to 0.6, and 2.04 at s = 1.0;
  - L1 rises to 4.51 at s = 0.8 and is at 4.12 at 1.0;
  - after their peak, runs 4, 10 and 14 rise again at one or two speeds, before falling.
- **E2d at the static rungs:**
  - at H1-reach, GA run 2 fails, with 0.81 captures; it is also E2d's weakest at H1-ghost, which is Task N on these
    worlds (0.80). Random run 2 is uncertain;
  - at H1-bite, 9 fail, each failure including reliability, and 4 are uncertain.
- **Generation 0:** its best genome makes 0.60 captures at H1-reach. On the route its family means (0.10 to 0.24) are
  close to what the stationary hunter gets from the prey's own path: 0.04 at s = 0.1, and 0.21 to 0.26 from
  s = 0.4.

## 5. The readings without a threshold (plan §6)

These are paired differences over the 512 worlds, per genome (`summary.json`, `ghost_minus_reach` and
`intact_minus_probe`). Each cell gives the family's mean, the range of its genomes' means, and how many genomes' 90%
intervals lie above or below zero.

| Contrast | E4s-1 (16) | L1 | E2d (47) | Generation 0 (16) |
|---|---|---|---|---|
| ghost − reach (the prey's collision input, H1) | 0.07 (−0.06 to 0.94); 6 above, 5 below | 0.00 | 0.00 (−0.03 to 0.03); 6 above, 3 below | 0.00 |
| intact − body probe, H1-bite | −0.05 (−0.15 to 0.06); 1 above, 8 below | 0.00 | −0.00 (−0.05 to 0.04); 4 above, 8 below | −0.00 |
| intact − `mean`, H1-bite | **1.13** (0.10 to 2.97); 16 above | **1.91** | 0.01 (−0.14 to 0.10); 11 above, 3 below | −0.00 |
| intact − `mirrored`, H1-bite | **2.70** (2.36 to 3.01); 16 above | **2.05** | **0.95** (0.00 to 1.63); 46 above | −0.00 |
| intact − body probe, H2-0.5 | −0.08 (−0.24 to 0.06); 1 above, 10 below | 0.00 | 0.00 (−0.04 to 0.05); 6 above, 3 below | −0.00 |
| intact − `mean`, H2-0.5 | **1.96** (0.89 to 3.83); 16 above | **3.51** | 0.00 (−0.04 to 0.04); 4 above, 3 below | 0.00 |
| intact − `mirrored`, H2-0.5 | **3.37** (2.96 to 4.31); 16 above | **3.59** | **0.29** (0.01 to 0.72); 44 above | 0.00 |

- **The prey's body has small effects.** Seeing it as a collision input costs E4s-1 run 5 0.94 captures at H1. For
  the other champions the effect is small either way, though 11 of 16 have intervals that exclude zero (6 above,
  5 below). Under bites, 8 of 16 E4s-1 champions do better with the prey's body taken out of their collision inputs,
  and one does worse. The tuned wall-follower baseline, which reads collisions, loses 0.18 to the prey's body.
- **The `mean` probe** (both noses fed their mean) costs every E4s-1 champion something and L1 a lot.
  - The cost to E4s-1 is larger at the moving prey: 1.96 on average at H2-0.5, against 1.13 at H1-bite.
  - It varies widely between champions: at H1-bite run 12 loses 0.10 (bounds 0.02 to 0.17), and run 13 loses 2.97
    of its 3.05.
  - It costs E2d nothing material: at most 0.10. On Task N, too, no E2d champion met E2d's "uses the left-right
    difference" criterion (D136, as corrected there).
  - The stereo dependence explains only part of the gap between the families. With the mean fed, E4s-1's champions
    still average 1.62 captures at H1-bite and 1.64 at H2-0.5, against E2d's intact 1.02 and 0.69. They were already
    far ahead at H1-ghost (Task N): 7.41 against 2.09.
- **The `mirrored` probe** reads the scent at the point reflection of each sample point through the arena's centre.
  It costs 46 of 47 E2d champions at H1-bite. This shows they depend on where the scent is. It does not show which
  computation they use.
- **The qualification probe `constant`** compares the intact scent against one held at its tick-0 mean. It ran
  wherever a genome met the capture criteria, and every such genome passed it. No genome reads "fails cue dependence"
  or "untested". This probe is the evidence that every qualifying genome depends on the scent.

## 6. The phases of a hunt (exploratory, after the reading)

`scripts/e5_0_phases.py` reads the local event tables and writes `phases.json`. It was written after seeing
`reading.json`, and it decides nothing. For each captured life with a logged first contact, it gives medians of:
- **the approach:** the ticks from activation to first contact;
- **the kill:** the ticks from first contact to capture;
- **the contact ticks:** the ticks in that life with the hunter's head within 1.5 of a prey body point.

Captured lives with no logged contact are counted apart. They are possible because bites can land before contact is
logged (§2): 0 to 6 per cell for the hunters below, except L1 at s = 1.0, with 23 of its 2 111 captures. The medians
are conditional on capture: unfinished lives are left out, and worlds weigh by their number of captures.

| Setting | E1-frozen S-const | Tuned S-const | Pursuit | L1 carrier | E4s-1 run 0 | E4s-1 run 3 | E2 GA run 0 |
|---|---|---|---|---|---|---|---|
| H1-bite | 29 / 25 / 17 | 29 / 25 / 17 | 29 / 25 / 17 | 33 / 57 / 16 | 40 / 33 / 15 | 39 / 28 / 16 | 112 / 62 / 16 |
| H2-0.1 | 28 / 26 / 19 | 28 / 26 / 19 | 28 / 28 / 19 | 30 / 46 / 15 | 36 / 51 / 18 | 35 / 42 / 19 | 97.5 / 55 / 15 |
| H2-0.5 | 21 / 32 / 24 | 29 / 14 / 14 | 20 / 33 / 24 | 25 / 32 / 13 | 33 / 36 / 14 | 33 / 31 / 14 | 86 / 72 / 13 |
| H2-1 | 18 / 15 / 14 | 18 / 15 / 14 | 17 / 15 / 13 | 24 / 21 / 10 | 36 / 59 / 12 | 35 / 61 / 12 | 87 / 90 / 13 |

(approach / kill / contact ticks, medians)

What the table shows:
- **The fixed-parameter references** (E1's frozen S-const and the pursuit) approach and kill faster at s = 1.0 than at
  s = 0.1. They are not faster at every step: at s = 0.5 their kill is the slowest.
- **The tuned positive control** is a different controller at each setting, so its column compares controllers as
  well as prey.
- **One possible reason** fast prey are easier for these references is that the prey closes part of the gap itself.
  Another is that its body sweeps more body points past the bite point per tick. Neither was tested.
- **The two E4s-1 champions shown** approach as quickly at every speed. Their kill phases lengthen, from 31 to 36
  ticks at s = 0.5 to 59 to 61 at s = 1.0, while their contact ticks stay at 12 to 14. That fits losing contact
  with fast prey and re-acquiring it, but it is a hypothesis, and these are two champions of sixteen.
- **L1**, with its carrier's constant turn, kills fast prey faster than slow ones (57 ticks at H1-bite, 21 at
  s = 1.0).

## What this means for E5-1 (proposals for its design, not decisions)

- **The ladder:** H1, H2 and H2b are solvable and not too easy at every setting tested. The speed series separates
  the reused families, but the positive control does not fall off, so E5-1 needs a rule other than SCOPE.md §4's.
  Candidate ranges, chosen from what is described above:
  - the route speeds where most of E2d stops qualifying (0.3 to 0.5);
  - the movers' 0.25 and 0.5;
  - the speeds above 0.6, where E4s-1's champions decline.
- **A frozen comparator to keep:** L1 on its carrier. At route speed 1.0 it beats every tested E4s-1 champion. Fast
  prey also separates the two on the kill: L1 kills fast prey faster than slow ones, while the two E4s-1 champions
  inspected take longer. This bears on what an evolved hunter should start from: the carrier's gait may matter as
  well as the comparator.
- **The null-graph arm:**
  - E5-0 tested whole brains, N2 plus graft (E4s-1) or N2 alone (E2d), zero-shot. It says nothing about null graphs,
    and nothing about how well N2-only hunters would evolve on Task H.
  - A fair start for a null arm stays E5-1's design question (SCOPE.md §7): E4s-1's graft was built and settled on
    N2 only.
- **Cost:**
  - E5-0 measured CPU rates only: about 0.016 s per neural episode at its batch (`bench.json`, in `summary.json`).
  - E5-1 needs a GPU benchmark at its intended batches before any forecast, and the owner's word for the GPU.
- **H3** (earlier organisms as prey) is still to be built; nothing here tests it.

## Limits

- **One arena and one horizon:** 300 ticks, with Task N's geometry (σ = 6, D = 8). The scent peaks on the prey's head
  (plan §2), so a scent follower meets the head first.
- **The movers:** the wall-following prey is weakly reactive, since its collision inputs include the hunter's body.
  The random-walk prey spends up to 27% of its moves against the wall (§2).
- **Tuning and transfer:** the positive control was tuned on 64 calibration worlds with E1's grids, and evaluated on
  512 fresh ones; tuning on 64 is slightly noisy (§3). The reused hunters are zero-shot.
- **No correction for multiple comparisons:** readings are per setting, and nothing corrects for the 18 settings or
  the 80 genomes, as the plan set none.
- **Bootstrap intervals are over worlds,** with routes and walks drawn per world, never over captures.
- **CPU only.** CPU exactness is claimed on this machine and platform only (rule 6).

## Reproduce it

To regenerate the summaries from the committed records:

```
python scripts/e5_0_summary.py      # summary.json and genomes.md
python scripts/e5_0_phases.py       # phases.json; needs the local event tables
```

**To repeat the formal run**, start from a checkout without this folder's stage records. Each stage refuses to start
where its start marker exists, and refuses to run on a dirty or unpushed tree, or on code that changed since the
stages it builds on. Then run the stages in order:

```
python scripts/e5_0.py bench        # then equivalence, calibrate, evaluate, probe, read
```

The equivalence stage needs a worktree of the engine at `ab749bb` at `../wormWars-e5ref`. With `--smoke`, any stage
runs a tiny version into `runs/e5-0-smoke/` instead.
