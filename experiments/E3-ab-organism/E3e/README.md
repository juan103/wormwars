# E3e: E3d's island mazes at 7 × 7 (exploratory task validation)

**Status (2026-10-11):** run at 0.71 of 3 GPU-hours. **"E3e: failed at calibration":** at every k_r, G2a and
G1a failed:
- **G2a:** the scent follower fell to 0.13-0.16 of the oracle;
- **G1a:** the random walk made 0.27-0.32 of the follower's visits;
- **G1b passed:** the walk made 1.50-1.64 visits, under 2.0. G1b was E3d's failure.

The results (`RESULTS.md`) were reviewed by both reviewers and corrected before publication (D236).

**The question:** E3d's question, at 7 × 7. The owner chose a larger maze (D232) after E3d's random walk exceeded
the absolute blind limit at 6 × 6.

**The design:** `docs/E3/E3e-DESIGN.md` v2 (bound at 79de3a1, D234). It is E3d's design, pinned by hash,
unchanged except for the size, the seed and the blocks.

## Where things are

- **The decisions:** D232-D236.
- **The reviews:** `docs/reviews/20261011-E3e-*`.
- **The code:**
  - `scripts/e3e.py`, a thin runner over `scripts/e3d.py`;
  - E3d's modules, unchanged except the gate's label.
- **The records** (this folder):
  - the stage records, `project.json`, `g-e.json`, `calibrate.json` and `report.json`;
  - `summary.json` (`scripts/e3d_summary.py --exp E3e`) and `compute-record.json`.
- **E3d's full-rollout references** are in `../E3d/`.

**What stays local:** the per-condition records, `runs/e3e/records/*.npz`, hashed in `calibrate.json`; and E3c's
champion genomes.

## Reproduce it

```
python -m pytest tests/test_e3e_runner.py tests/test_e3d_*.py
python scripts/e3e.py project --smoke --device cpu    # then g-e, calibrate, confirm, report (toy sizes)
python scripts/e3e.py project --device cuda           # formal: needs E3c's local champion genomes
python scripts/e3d_summary.py --exp E3e
```
