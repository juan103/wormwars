# E3f: E3d's 6 × 6 island mazes at a horizon of 1 800 ticks (exploratory task validation)

**Status (2026-10-11):** run at 1.06 of 3 GPU-hours. **"E3f: passed"**: calibration and a fresh confirmation block
met every criterion of E3d's gate, at k_r = 0 and H = 1 800.
- **G2a,** the follower against the oracle, is the narrowest: 0.361 on confirmation, with an interval crossing ⅓.

The results (`RESULTS.md`) were reviewed by both reviewers and corrected before publication (D241).

**The question:** E3d's question, at the horizon chosen from E3d's records (D237), on fresh mazes. It is the last
horizon adjustment in the sequence of E3d, E3e and E3f.

**The design:** `docs/E3/E3f-DESIGN.md` v1.1, bound at ef7609b (D239). It is E3d's design, pinned by hash,
unchanged except H, k_r, the seed and the blocks.

## Where things are

- **The decisions:** D237-D241.
- **The reviews:** `docs/reviews/20261011-after-E3e/` and `docs/reviews/20261011-E3f-*`.
- **The code:** `scripts/e3f.py`, a thin runner over `scripts/e3d.py`.
- **The records** (this folder):
  - the stage records, `project.json`, `g-e.json`, `calibrate.json`, `confirm.json` and `report.json`;
  - `summary.json` (`scripts/e3d_summary.py --exp E3f`) and `compute-record.json`.

**What stays local:** the per-condition records, `runs/e3f/records/*.npz`, hashed in the stage records; and E3c's
champion genomes.

## Reproduce it

```
python -m pytest tests/test_e3f_runner.py tests/test_e3d_*.py
python scripts/e3f.py project --smoke --device cpu    # then g-e, calibrate, confirm, report (toy sizes)
python scripts/e3f.py project --device cuda           # formal: needs E3c's local champion genomes
python scripts/e3d_summary.py --exp E3f
```
