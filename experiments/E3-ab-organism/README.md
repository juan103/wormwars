# E3: the minimal A/B organism

**Status (2026-10-03):**
- **E3a: published on main** (2026-10-02, D170).
  - Its design was agreed (`docs/E3/DESIGN.md` v2.4, D163).
  - Its pre-registration was bound before any stage ran (`E3a/PREREGISTRATION.md`; D164, D165; Amendment
    1, D167).
  - It ran on 2026-10-02, using 5.97 of its 30 GPU-hours (D168).
  - Its results were reviewed by both ("fix") and corrected (D169).
- **E3b-0: published on main** (2026-10-03, D180). It is exploratory, at 2.62 of 3 GPU-hours: the maze
  engine, the controls and the task's feasibility (`E3b-0/README.md`).
- **E3b-1: pre-registered and bound** (2026-10-03, D181-D186; `E3b-1/PREREGISTRATION.md`), and not yet run.
  It is the roadmap's E3 gate: the tuned colony against the frozen seed in mazes, with a cap of 24
  GPU-hours.

## E3a's results

The registered readings:
- **S2-a:** "evolution found a working selector in 1 of 8 runs, not reliably".
- **S2-b:** evolution against random sampling is "unclear", −1.49 visits (90% −2.98 to +0.24).
- **S2-c:** none of 1 024 draws in either census passed the screen and the full check (rate below
  0.0036).
- **Stage 3 (joint tuning):** "better", +2.36 visits.
- **B-task:** "worse" than Stage 3, −3.73. It matches neurons, not capacity.

Descriptive:
- **The engineered organism** (two L1 copies, a one-neuron latch, saturation gating) shuttles at 12.79
  visits per 600 ticks. That is 97% of L1-switch on the same worlds, and removing its latch costs 4.83.
- **Random sampling's champions** are working selectors in 7 of 8 runs (5 latches).
- **Four tuned organisms** scored above E's mean (up to 15.98).
- **Four champions are "bistable, not a latch":** memories that hold, behind partial gates.
- **Several high scorers are classed "no memory".** The release test cannot separate a faded q from a
  weak gate, so that class is operational.


## E3b-0's results (exploratory; `E3b-0/README.md`, `E3b-0/RESULTS.md`)

E3b-0 ran on 2026-10-02/03 and used 2.62 of its 3 GPU-hours. Both reviewers reviewed it ("fix then
publish"), and it was corrected (D175-D180). It tunes nothing.

**On 256 untouched mazes** (5 × 5 trees, colonies of 8, 2 400 ticks):
- **Linear trails help** a scripted follower (+3.57 legs per 1 000 ticks) and the engineered seed E with a
  one-sided wall reflex (+0.69).
- **Peers' trails speed later discoverers** (7% and 13%).
- **Peer fields not laid by the colony itself hurt.**

**Not shown:** that weys use the trail's direction.

**Also found:**
- E3a's best tuned organism, S3r3, fails the maze;
- most of the seed's maze performance comes from the reflex;
- the trail constants are adaptively selected.

**E3b-1 must be resized:** about 71 GPU-hours as first planned.

## What it asks

Can two hand-built stereo modules, one per scent, be composed into an organism that shuttles between
two sources? A one-neuron latch remembers which source is next and gates which module steers. With
the modules frozen, can evolution find such a selector?

**The frame:** stereo sensing is a game-design choice. The organism is a hand-built circuit on a
silent worm, outside the N2 mask. Nothing here is about worm behaviour.

## Its parts

- **E3a, the shuttle:** one wey, an open arena, two fixed sources. This folder's first experiment.
- **E3b:** trails, branching mazes and the colony. It holds the roadmap's E3 gate. E3b-0, the engine and
  feasibility, is published; E3b-1, the gate, is pre-registered.
- **E3c:** the assembly comparison.

**The owner's ceilings:** 30 GPU-hours for E3a, and about the same for each of E3b and E3c (D159).

## Where things are

- **The design and its five review rounds:** `docs/E3/DESIGN.md`; `docs/reviews/20261002-E3-design*/`;
  D156-D163.
- **The geometry check:** `scripts/e3_geometry_check.py` and `docs/E3/geometry-check.json`.
- **The module it builds on:** E4s-0's L1 (`../E4s-stereo-module/E4s-0/module.json`).
