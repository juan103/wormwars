# E4 / 04c: do the two minds share?

**Status (2026-10-13):** **the main task's formal run was not run.** Its pilot and follow-ups (4.20 of 30 GPU-hours)
showed that it would most likely spend about 20 GPU-hours on an inconclusive null. On both reviewers' recommendation,
the owner re-scoped E4 to its diagnostic task, **E4-D**, where information must cross from module A to module B by
construction (D257-D258). The main task's findings are published here as exploratory (`RESULTS.md`).

**The question:** does information crossing between two grafted navigation modules, through 32 optional cross-links,
come to be used under evolution (ROADMAP, E4 / 04c)?

**The design:** `docs/E4/E4-DESIGN.md` v3, agreed by both reviewers (D242-D244); never pre-registered, since the pilot
came first. E4-D's design: `docs/E4/E4-D-DESIGN.md` v2.2.

## What was found (exploratory)

- E-G's comparator modules are mutationally fragile: on 8 paired mazes, one round of T-F's mutation at factor 0.25
  took the children from E-G's 4.03 to 1.97 visits per wey, and the whole loss came from the 8 module biases.
- In the pilot, 100 generations did not recover it: on 64 validation mazes no final X0 strain beat E-G.
- Random cross-links cost heavily at every registered size (children 4.53 against X0's 7.40 at the smallest), and the
  cost cannot be attributed to one mechanism from these tests.
- It does **not** show that evolved sharing could not help.

## Where things are

- **The decisions:** D242-D259.
- **The reviews:** `docs/reviews/20261011-E4-design*`, `20261011-E4-code`, `20261013-E4-pilot-1`,
  `20261013-E4-diagnostics`, `20261013-E4-stageA`, and E4-D's `20261012-E4-D-design*`.
- **The code:** the library `wormwars/e4/` (the gated organism, the arms, the interventions, lineages, the statistics,
  the evaluation harness, E4-D's trial world); the output gate in `wormwars/brain.py`; the scripts `scripts/e4.py`
  (the pilot), `scripts/e4_pilot_attempt1.py`, `scripts/e4_diagnose.py`, `scripts/e4_calibrate.py`,
  `scripts/e4_headroom.py`, and E4-D's `scripts/e4d.py`.
- **The records** (this folder): the pilot's attempt 1 (`pilot.json`, `pilot-started.json`, `pilot-partial.json`),
  `pilot-attempt1-summary.json`, `diagnostics.json`, `calibration.json`, `headroom.json`, and the compute records.
- **Rule 7:** `docs/E4/rule7/` (the output gate and the substep hook, CPU and GPU, identical).

**What stays local:** the pilot's populations, selection matrices and parents (`runs/e4/pilot/`); the summary records
the selection file's sha256.

## Reproduce it

```
python -m pytest tests/test_e4_*.py tests/test_e4d_*.py
python scripts/e4.py pilot --smoke --device cpu       # the pilot at toy sizes
python scripts/e4_diagnose.py --device cuda           # the diagnostics (about 22 GPU-minutes)
python scripts/e4_calibrate.py --device cuda          # stage A (about 35 GPU-minutes)
python scripts/e4_headroom.py                          # CPU
python scripts/e4_pilot_attempt1.py                   # needs the local selection matrices of attempt 1
```

The diagnostics and stage A are exact only on the same GPU and environment (D082); on the CPU they differ, as the
rollouts are chaotic.

## Extend it

E4-D is next: its feasibility check (CPU), then an evolutionary E4-D with its own design and pre-registration, on E4's
remaining GPU-hours. Other routes the main task leaves open: smaller mutation on the module biases (0.02 passed the
incremental criterion, unconfirmed), and a task where A holds information B can use in ordinary shuttling.
