# E3d: a maze that wall-following cannot solve (exploratory task validation)

**Status (2026-10-10):** run at 0.81 of 3 GPU-hours. **"E3d: failed at calibration"**: at every k_r, G1b
failed, and nothing else did. A random walk reached 2.34-2.53 mean visits per wey against the absolute blind
limit of 2.0. The results draft (`RESULTS.md`) is under review by both reviewers.

**The question:** can a 6 × 6 maze family be built in which every scent-free control scores well below a scent
navigator, while navigation still pays? E3c found that organisms trained from random weights solve E3b-1's tree
mazes by following walls, since every wall of a tree maze touches the perimeter.

**The family:** a Wilson tree with each goal inside a carved, free-standing ring (an "island"), plus k_r further
openings. A gate on a fixed block decides; it was fixed in advance.

**The frame:** scripted controls and frozen organisms on a silent worm. Nothing here is about worm behaviour.

## Where things are

- **The design:** `docs/E3/E3d-DESIGN.md` v2.2, bound at 65b77fb. Amendment 1, its correction and erratum
  are in §11.
- **The decisions:** D221-D228.
- **The reviews:** `docs/reviews/20261010-E3d-*`.
- **The sizing:** `scripts/e3d_sizing.py` and `docs/E3/e3d-sizing.json`.
- **The code:**
  - `wormwars/e3/islands.py`: the construction;
  - `wormwars/e3/e3d_controls.py`: the wall-follower and the tangent start;
  - `wormwars/e3/e3d_records.py`: the records;
  - `wormwars/e3/e3d_gate.py`: the gate;
  - `scripts/e3d.py`: the stages;
  - `scripts/e3d_equivalence.py`: the rule-7 leg.
- **The records** (this folder):
  - the stage records, `project.json`, `g-e.json`, `calibrate.json` and `report.json`;
  - the full-rollout references, `equivalence-reference-cpu.json` and `equivalence-reference-cuda.json`;
  - `summary.json` (`scripts/e3d_summary.py`) and `compute-record.json`.

**What stays local:** the per-condition trajectories and per-visit records, `runs/e3d/records/*.npz`, hashed in
`calibrate.json`; and E3c's champion genomes.

## Reproduce it

```
python scripts/fetch_connectome.py
python -m pytest tests/test_e3d_*.py
python scripts/e3d_sizing.py                          # the sizing (CPU)
python scripts/e3d.py project --smoke --device cpu    # then g-e, calibrate, confirm, report (toy sizes)
python scripts/e3d.py project --device cuda           # formal: needs E3c's local champion genomes
python scripts/e3d_summary.py                         # summary.json from the records
```

The formal stages refuse unless the design and the engine are those of the binding commit, and HEAD is pushed.
