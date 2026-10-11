"""E3f: E3d's 6 × 6 island mazes at H = 1 800 (docs/E3/E3f-DESIGN.md; D237-D238). A thin runner over `scripts/e3d.py`:
the same stages, gate, records and report, pointed at E3f's experiment with `use_experiment`.

    python scripts/e3f.py project --device cuda      # then g-e, calibrate, confirm, report, as for E3d
    add --smoke for toy sizes in runs/e3f-smoke (never results)

**What differs from E3d** (E3f §1):
- H = 1 800;
- k_r = 0 only;
- the maze run seed 1 192 000;
- the blocks, ids 32 000-32 455;
- the label "E3f";
- the folders `experiments/E3-ab-organism/E3f/` and `runs/e3f/`.

**Both designs are bound:** E3f's and E3d's, which E3f inherits. Both runners are guarded. E3d's full-rollout
references stand, since the engine is unchanged.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "e3f"
BINDING = {
    "binding_commit": "",  # set by the binding commit
    "design_sha256": "26ab81d504204f932a670fcc18c6066fc6ada0c6d5f1ee637f0d59fbe3d2d50e",  # docs/E3/E3f-DESIGN.md (v1.1, D239)
    "parent_design_sha256": "37ee0c39868f074446cca43fd0242ce8bf72e9f90127fdafbade60394e4b4147",  # E3d's at 202666e
}


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


D = _load("e3d_for_e3f", "e3d.py")
D.use_experiment(
    label="E3f", name=NAME, exp=ROOT / "experiments" / "E3-ab-organism" / "E3f", out=ROOT / "runs" / "e3f",
    smoke_dir=ROOT / "runs" / "e3f-smoke", design="docs/E3/E3f-DESIGN.md",
    designs={"docs/E3/E3f-DESIGN.md": "design_sha256", "docs/E3/E3d-DESIGN.md": "parent_design_sha256"},
    runners=["scripts/e3f.py", "scripts/e3d.py"],
    registry={**BINDING, "c": 6, "H": 1800, "k_r": [0], "maze_seed": 1_192_000,
              "blocks": {"calibration": [32_000, 32_128], "confirmation": [32_200, 32_456],
                         "tree_reference": [32_200, 32_328], "tangent": [32_200, 32_264]}})


if __name__ == "__main__":
    from wormwars.accounting import run_script
    if any(a == "--out" or a.startswith("--out=") for a in sys.argv[1:]):
        raise SystemExit("--out is not accepted: E3f writes only to its own folders")
    smoke = "--smoke" in sys.argv
    out_dir = ROOT / "runs" / ("e3f-smoke" if smoke else "e3f")
    try:
        run_script(D.main, out_default=str(out_dir), default="measure", name=NAME)
    finally:
        agg = out_dir / "compute.json"
        if agg.exists() and not smoke:
            D.EXP.mkdir(parents=True, exist_ok=True)
            (D.EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
