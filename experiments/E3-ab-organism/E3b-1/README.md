# E3b-1: the E3 gate in mazes (confirmatory)

**Status (2026-10-04): run, reviewed by both reviewers ("fix then publish"), corrected and published
(D192).** The results are in `RESULTS.md`:
- **G is "better":** +0.225 of the seed's mean, +0.069 for T-A and +0.381 for T-F;
- **the secondary tests:** S-gen, S-trail and S-peer are all significant after Holm;
- **the probes:** no tuned champion meets the seed's comparator criteria.

**Its course:**
- **Pre-registration:** bound at 1c65e4e (D186), before any stage ran: `PREREGISTRATION.md`.
- **Amendment 1:** infeasible mazes redraw their walls. Its text and a dated correction are in §14 of the
  pre-registration (D190, D191).
- **Code:** reviewed by both reviewers before any formal stage. Their blocking findings were fixed
  (D188, D189).
- **The stages:**
  - `project` completed, on its one rerun after Amendment 1. It applied cut 1 (N to runs 0-3); the planned
    total is 22.85 of 24 GPU-hours.
  - `g-e` passed: E2's GPU batch was identical, and so were the CPU and maze equivalences.
  - Every training run completed on its first attempt.
  - `champions` and `evaluate` completed, at 18.73 of 24 GPU-hours.

**The question:** does joint tuning of the maze-ready seed E + W2 improve a colony's shuttling in 5 × 5 tree
mazes with shared trails, against the frozen seed, on 256 prespecified test mazes? The answer is read from gate G. Three
secondary questions:
- more generations (S-gen);
- trail dependence (S-trail);
- peers' trails speeding later discoverers (S-peer).

**The frame:**
- the organism is a hand-built circuit on a silent worm, so nothing here is about worm behaviour;
- the claim is about tuning under the two schedules run, from this seed, with this GA;
- no claim is made that weys follow a trail's direction.

## The arms

| Arm | Runs | Generations | Mazes per genome per generation | Access | Start |
|---|---|---|---|---|---|
| T-A | 8 | 125 | 16 | shared | the seed |
| T-F | 8 | 300 (read also at index 124) | 8 | shared | the seed |
| N | 4 (6 registered; cut 1) | 125 | 16 | none | the seed |
| R | 2 | 125 | 16 | shared | the degraded start (no latch) |

The champions are evaluated on the 256 prespecified test mazes against the frozen seed, together with W2
alone on the carrier, a scripted trail follower, an oracle and a random walk.

## Where things are

- **The design:** `docs/E3/E3b-1-DESIGN.md` (v2, D183).
- **The decisions:** D181-D192 in `DECISIONS.md`.
- **The reviews:** `docs/reviews/20261003-E3b-1-*`:
  - the design;
  - the three pre-registration rounds;
  - the code review and its confirmation pass;
  - Amendment 1 and its check;
  - the results (`docs/reviews/20261004-E3b-1-results/`).
- **The code:**
  - `scripts/e3b1.py`, the runner;
  - `wormwars/e3/tuning.py`;
  - `wormwars/e3/maze.py` (`walls_for`, Amendment 1);
  - `wormwars/e3/maze_runs.py` (`play_batch`);
  - `wormwars/e04a/evolve.py`;
  - `scripts/e3b1_maze_audit.py`, the maze equivalence and redraw audit;
  - `scripts/e3b1_power.py`, the gate's power simulation.
- **The results:** `RESULTS.md`.
- **The records:** this folder. Each stage has a record `<stage>.json` and its start marker; the stopped
  `project` attempt is kept as `project-attempt1.json`. `evaluate.json` holds the readings and the probes.
  Also here:
  - `maze-reference.json` and `maze-redraws.json`;
  - `power.json`;
  - `compute-record.json`;
  - the evaluation's per-maze arrays `eval-*.npz`, and the replay pre-pass's `calib-*.npz`.

  Genomes stay local (`runs/e3b1/genomes`); their hashes are in the records.

## Reproduce it

```
python scripts/fetch_connectome.py
python -m pytest tests/test_e3b1_runner.py tests/test_e3b1_tuning.py tests/test_e3b_maze.py
python scripts/e3b1.py readings                         # recompute the readings from the committed records (CPU;
                                                       # writes readings.json here and records its own compute)
python scripts/e3b1.py project --smoke --device cpu    # then each later stage with --smoke: toy sizes in runs/e3b1-smoke
python scripts/e3b1_maze_audit.py --compare experiments/E3-ab-organism/E3b-1/maze-reference.json
python scripts/e3b1.py project --device cuda           # formal: then g-e, train-ta, train-tf, train-n, train-r,
                                                       # champions, evaluate; `readings` recomputes the readings
```

- **Formal stages** require CUDA on the registered GPU, the pinned environment, the guarded files committed,
  and HEAD pushed.
- **Each stage runs once,** with one rerun after a crash or a kill. Training has up to three attempts (§5).
- **CUDA results** repeat exactly only on the same GPU with the same batch composition
  (`docs/REPRODUCIBILITY.md`).

## Extend it

- **Next: E3b-2** (exploratory; D193): knock out or freeze parts of the tuned champions to see where the gain
  comes from. The parts are the latch, the comparators, the reflex and the turn biases.
- **Open questions:**
  - **Why T-F gained more:** at 125 generations its champions matched T-A's (S-worlds), so the extra
    generations look like the reason. That is descriptive, not tested.
  - **What the tuned organisms use** in place of the designed selector.
  - **Whether weys follow a trail's direction.**
  - **Why replayed and scrambled peer fields hurt.**
- **After E3b-2:** the roadmap's E3 assembly comparison (E3c) or E4.
