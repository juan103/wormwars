# E4 / 04c: do the two minds share?

**Status (2026-10-13):**
- **The main task's formal run was not run.** Both reviewers judged it poor value and recommended against spending its
  estimated 20 GPU-hours. The owner re-scoped E4 to its diagnostic task, **E4-D**, where information must cross from
  module A to module B by construction (D257-D258). The main task's pilot and follow-ups (4.20 GPU-hours) are published
  as exploratory: [`RESULTS.md`](RESULTS.md).
- **E4-D's feasibility check passed** (CPU; D262; [`E4-D/README.md`](E4-D/README.md)). A hand-configured cross-link
  control carries an engineered A → B signal: 0.83 real-first against X0's exact 0.5. The next step is an evolutionary
  E4-D: its own design, review, pre-registration and pilot, on E4's remaining 25.80 GPU-hours (D258).
- **The evolutionary E4-D (pre-registered; 2026-10-15, D280): "practically relevant transfer found."** From E-G with
  the slots at 0, selection on the slots alone recruited the transfer: the 32 champions' mean real-first 0.912 on fresh
  test mazes, lower bound of the gain 0.401 against the margin 0.15 ([`E4-D-evo/RESULTS.md`](E4-D-evo/RESULTS.md)). E4 has
  used 9.30 of its 30 GPU-hours.

**The question:** does information crossing between two grafted navigation modules, through 32 optional cross-links,
come to be used under evolution ([ROADMAP](../../ROADMAP.md), E4 / 04c)?

**The designs:**
- E4: [`docs/E4/E4-DESIGN.md`](../../docs/E4/E4-DESIGN.md) v3, agreed by both reviewers (D242-D244); never
  pre-registered, since the pilot came first.
- E4-D: [`docs/E4/E4-D-DESIGN.md`](../../docs/E4/E4-D-DESIGN.md) v2.3.

## What was found (exploratory)

- **The modules are mutationally fragile.** On 8 paired mazes, one round of T-F's mutation at factor 0.25 took the
  children from E-G's 4.03 to 1.97 visits per wey. Bias-only mutation of the 8 module neurons reproduced nearly all of
  that loss.
- **The pilot did not recover it.** After 100 scored generations, none of the four final X0 populations contained a
  strain with a higher mean than E-G on 64 validation mazes.
- **Random cross-links cost heavily** at every tested factor, 0.25-4.0, on one block (children 4.53 against X0's 7.40
  at the smallest). The mechanism is unresolved.
- **None of this shows that evolved sharing could not help.**
- **In E4-D,** the cross-link weights that carry a signal (about 2-3) are about a hundred times the random steps that
  cost in the main task.

## Where things are

- **The decisions:** D242-D263.
- **The reviews:** `docs/reviews/` `20261011-E4-design*`, `20261011-E4-code`, `20261013-E4-pilot-1`,
  `20261013-E4-diagnostics`, `20261013-E4-stageA`, `20261013-E4-results`, and E4-D's `20261012-E4-D-design*` and
  `20261013-E4-D-code`.
- **The library:** `wormwars/e4/`:
  - the gated organism and the arms;
  - the interventions and lineages;
  - the statistics and the evaluation harness;
  - E4-D's trial world and rules.

  The output gate and the substep hook live in `wormwars/brain.py`.
- **The scripts:**
  - `scripts/e4.py` (the pilot) and `scripts/e4_pilot_attempt1.py`;
  - `scripts/e4_diagnose.py`, `scripts/e4_calibrate.py` and `scripts/e4_headroom.py`;
  - E4-D's `scripts/e4d.py`.
- **The records** (this folder):
  - the pilot's attempt 1: `pilot.json`, `pilot-started.json`, `pilot-partial.json`;
  - `pilot-attempt1-summary.json`, `diagnostics.json`, `calibration.json`, `headroom.json`;
  - the compute records;
  - E4-D's records in `E4-D/`.
- **Rule 7:** `docs/E4/rule7/` (the output gate and the substep hook, CPU and GPU, identical). E4-D's trial world is a
  subclass that changes no engine file (v2.3).

**What stays local:** the pilot's populations, selection matrices and parents (`runs/e4/pilot/`). The summary records
the selection file's sha256.

## Reproduce it

```
python -m pytest tests/test_e4_gate.py tests/test_e4_organism.py tests/test_e4_arms.py tests/test_e4_train.py tests/test_e4_means.py tests/test_e4_lineage.py tests/test_e4_scale_rule.py tests/test_e4_stats.py tests/test_e4_evaluate.py tests/test_e4_runner.py tests/test_e4_calibration.py tests/test_e4d_trial.py tests/test_e4d_feasibility.py tests/test_e4d_runner.py
python scripts/e4.py pilot --smoke --device cpu       # the pilot at toy sizes
python scripts/e4_diagnose.py --device cuda           # the diagnostics; their last section needs the local final populations
python scripts/e4_calibrate.py --device cuda          # stage A
python scripts/e4_headroom.py                          # CPU
python scripts/e4_pilot_attempt1.py                   # needs the local selection matrices of attempt 1
python scripts/e4d.py scout                            # then calibrate, evaluate (CPU; each once, from a clean tree)
```

**To rerun E4-D's stages** in a disposable checkout: each stage runs once and refuses if its record exists. Copy
`experiments/E4-two-minds/E4-D/scout.json`, `calibrate.json` and `evaluate.json` outside the repository, delete them
from the checkout, run `scout`, `calibrate` and `evaluate`, and compare the new records with the copies.

- **The GPU runs can be repeated exactly** only on the same GPU, in the pinned environment, with the same batch
  composition. These scripts do not use `replay_mode()`, so an exact replay is not claimed (rule 6, D082).
- **On the CPU the results differ:** the rollouts are chaotic.
- **E4-D's CPU stages are deterministic:** the rerun scouting reproduced its first attempt exactly (D261-D262).

## Extend it

- **The evolutionary E4-D** (D258): its design (`docs/E4/E4-D-EVO-DESIGN.md`, D265-D266), its exploratory pilot
  (`E4-D-evo/`, D269-D270: all 20 runs recruited the transfer) and its pre-registration
  (`E4-D-evo/PREREGISTRATION.md`, bound at D274), its formal code (D275-D278) and its formal run (D279-D281, "practically
  relevant transfer found"; [`E4-D-evo/README.md`](E4-D-evo/README.md)).
- **Routes the main task leaves open:**
  - smaller mutation on the module biases (0.02 met the incremental criterion, unconfirmed);
  - a task where A holds information that B can use in ordinary shuttling.
