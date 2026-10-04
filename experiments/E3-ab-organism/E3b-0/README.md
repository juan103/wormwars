# E3b-0: mazes, trails and colonies (exploratory)

**Status:** published on main on 2026-10-03 (D180). It used 2.62 of its 3 GPU-hours, and its results were
reviewed by both reviewers ("fix then publish") and corrected.

**The question:** before E3b-1 tests whether evolution improves a colony in mazes with trails, is there a
usable task and a usable signal at all? E3b-0 tunes nothing.

**The result** (`RESULTS.md`, reviewed by both reviewers, D180), on 256 untouched mazes:
- **Linear trails help.** In legs per 1 000 ticks:
  - a scripted trail follower: +3.57 [2.97, 4.19];
  - the engineered seed E with a one-sided wall reflex (W2): +0.69 [0.44, 0.93].
- **Peers' trails speed later discoverers** of the second source: by 7% for the follower and 13% for the
  seed.
- **Peer fields not laid by the colony itself hurt:** a replayed donor colony, or scrambled peers.
- **Not shown:** that weys use the trail's direction.
- **E3b-1, as first sized, does not fit its budget** (about 71 GPU-hours).
- **E3a's best tuned organism (S3r3) fails the maze.**

**The caveat:** the trail constants were chosen after the qualification rule changed twice. Both changes
were reviewed before they ran, but everything chosen is adaptively selected. The GPU leg of the engine's
equivalence check is still owed.

## What it is
- **The task:** a 5 × 5 tree maze (Wilson's algorithm, 3-wide corridors) and a colony of 8 weys. Each wey
  shuttles between two dead ends A and B for 2 400 ticks, with its own goal.
- **Trails:** linear, one field per wey and source. Each wey deposits a decaying amount onto the trail of
  the source it last visited; the trails diffuse through open cells and evaporate.
- **Sensing:** the noses read the trails as accessed plus a path-distance scent. A wall cuts the line of
  sight.
- **Access modes:** shared, own, peers, none, replay (a lockstep donor colony from another episode) and
  scramble.

## Where things are
- **The plan:** `docs/E3/E3b-0-PLAN.md` (v3, with Amendments 1 and 2).
- **The decisions:** D174-D180.
- **The reviews:** `docs/reviews/20261002-E3b-0-*`, `docs/reviews/20261003-E3b-0-*`.
- **The code:**
  - the engine: `wormwars/e3/maze.py` and `maze_world.py`;
  - the organisms: `maze_organisms.py`;
  - the controls: `maze_controls.py`;
  - the measures: `maze_measures.py`;
  - the drivers: `maze_runs.py`;
  - the runner: `scripts/e3b0.py`.
- **The records:** this folder. The stage records `*.json` with per-maze `*.npz`, the diagnoses in
  `development-records/`, and the compute in `compute-record.json` (2.62 GPU-hours).
- **The interim report** from when the trail search had stalled: `INTERIM-REPORT.md`, with its
  corrections.

## Reproduce it
```
python scripts/fetch_connectome.py
python -m pytest tests/test_e3b_*.py tests/test_e3b0_runner.py
python scripts/e3b0.py stage-a --smoke --device cpu     # the whole chain at toy sizes, in runs/e3b0-smoke
python scripts/e3b0.py stage-a --device cuda            # formal; then stage-b, stage-b2, stage-b3,
                                                        # recheck-a, stage-c, report, timing
python scripts/e3b0_power.py                            # the gate's power simulation (CPU)
python scripts/e3b0_diagnose.py                         # diagnoses 1-5 (CPU, except diagnosis 4's
python scripts/e3b0_diagnose2.py                        # seed part, which needs CUDA)
python scripts/e3b0_diagnose3.py
python scripts/e3b0_diagnose4.py --part seeds --device cuda
python scripts/e3b0_diagnose4.py --part follower --device cpu
python scripts/e3b0_diagnose5.py
```

- **Formal stages** require CUDA on the registered GPU, the pinned environment, a clean tree and HEAD
  pushed. Each runs once.
- **Stage A's, B's and B2's records** are reused by `stage-b3` through a hash check. A fresh rerun of the
  chain writes new records in place of those.
- **CUDA results** repeat exactly only on the same GPU with the same batch composition
  (`docs/REPRODUCIBILITY.md`).

## Extend it
- **E3b-1 followed** (published 2026-10-04; `../E3b-1/RESULTS.md`). The tuned colony beat the frozen seed
  E + W2 ("better", +0.225 of its mean), within a cap of 24 GPU-hours.
- **Open questions:**
  - whether a controller that compares readings over time can use the trails' slope;
  - why replayed and scrambled peer fields hurt;
  - why S3r3's evolved outputs leave it circling.
