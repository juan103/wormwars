# E3c: the assembly comparison in the maze shuttle (pre-registered)

**Status (2026-10-06):** run at 22.65 of 30 GPU-hours; results drafted (`RESULTS.md`), for review by both
reviewers.
- **Q1 (modular against dense, from random weights):** "no relevant difference" (approximate); the exact test
  detects no difference.
- **Q2 (the engineered start plus its tuning against E's mask from scratch):** "unclear". The tuned
  engineered organisms are ahead by 0.66 visits per wey on average, with a wide spread.
- **The coverage hypothesis:** "supported". Every organism trained from random weights solves the maze as a
  scent-free wall-follower; every tuned engineered organism navigates with its noses.

**The question:** does assembling validated modules make a better or cheaper organism than training one from
scratch?

**How it asks it,** in E3b-1's maze shuttle, under equal training evaluations:
- **E's modular mask from random weights (S-mod)** against a dense controller of the same 11 neurons (S-dense);
- **the engineered seed plus its tuning (P-joint, E3b-1's T-F cohort, reused)** against S-mod;
- **E's modules frozen with a selector evolved from random (P-sel),** descriptive.

**The exploratory pilot changed the question's scope** (`PILOT.md`): the from-scratch organisms were scent-free
wall-followers. So E3c compares training routes on a task that a scent-free circuit solves. It does not compare
assemblies of stereo navigators.

**The frame:** a hand-built circuit on a silent worm. Nothing here is about worm behaviour.

## Where things are

- **The design:** `docs/E3/E3c-DESIGN.md` (v2.1).
- **The pre-registration:** `PREREGISTRATION.md`, bound at 69d7cd5, with Amendments 1 and 2 (§14).
- **The pilot, its replay and probe:** `PILOT.md`, `pilot.json`, `replay.json`, `diagnostics/`.
- **The power analysis:** `power.json` (`scripts/e3c_power.py`).
- **The results:** `RESULTS.md`, from `report.json`.
- **The decisions:** D198-D218.
- **The reviews:** `docs/reviews/20261004-E3c-*`, `20261005-E3c-*`.
- **The code:**
  - `wormwars/e3/assembly.py`: the arms' draws and masks;
  - `wormwars/e3/e3c_stats.py`: the registered statistics;
  - `wormwars/e3/e3c_formal.py`: the formal plan;
  - `scripts/e3c.py`: every stage.
- **The records:** this folder:
  - the stage records `*.json`;
  - the published champions' grafted parameters, `champions-grafted.json`;
  - `compute-record.json`.

**What stays local:** the genomes (`runs/e3c/genomes`) and the full path files (`runs/e3c/paths`). Their
hashes are in the records. E3b-1's T-F genomes, which P-joint reuses, stay local too, and are hash-checked at
load.

## Reproduce it

```
python scripts/fetch_connectome.py
python -m pytest tests/test_e3c_assembly.py tests/test_e3c_stats.py tests/test_e3c_power.py tests/test_e3c_formal.py tests/test_e3c_stages.py
python scripts/e3c_power.py                                 # power.json (CPU)
python scripts/e3c.py project --smoke --device cpu          # then g-e, train-smod, train-sdense, train-psel,
                                                            # champions, evaluate, report (toy sizes)
python scripts/e3c.py project --device cuda                 # formal: needs E3b-1's local genomes for champions
```

**Two limits on reproducing it:**
- the formal stages refuse unless the engine and the registered text are unchanged since the binding commit;
- `g-e`'s CPU leg is bitwise against a Windows reference (rule 6).

**Extend it:** a question about assembled navigators needs a task that coverage cannot solve, such as a horizon
too short for a lap of the tree. See `RESULTS.md`, "What this does and does not show".
