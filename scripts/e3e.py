"""E3e: E3d's island mazes at 7 × 7 (docs/E3/E3e-DESIGN.md v2; D232-D233). A thin runner over `scripts/e3d.py`:
the same stages, gate, records and report, pointed at E3e's experiment with `use_experiment`.

    python scripts/e3e.py project --device cuda      # then g-e, calibrate, confirm, report, as for E3d
    add --smoke for toy sizes in runs/e3e-smoke (never results)

**What differs from E3d** (E3e §1):
- c = 7;
- the maze run seed 1 191 000;
- the blocks, ids 31 000-31 455;
- the label "E3e";
- the folders `experiments/E3-ab-organism/E3e/` and `runs/e3e/`.

**Both designs are bound:** E3e's and E3d's, which E3e inherits. Both runners are guarded. E3d's full-rollout
references stand, since the engine is unchanged.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "e3e"
BINDING = {
    "binding_commit": "",  # set by the binding commit
    "design_sha256": "284a55c4e2905af8a23f61869bfbcee6d48e01b0d40f4f2ab0be24f55bc97d25",  # docs/E3/E3e-DESIGN.md (v2, D234)
    "parent_design_sha256": "37ee0c39868f074446cca43fd0242ce8bf72e9f90127fdafbade60394e4b4147",  # E3d's at 202666e
}


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


D = _load("e3d_for_e3e", "e3d.py")
D.use_experiment(
    label="E3e", name=NAME, exp=ROOT / "experiments" / "E3-ab-organism" / "E3e", out=ROOT / "runs" / "e3e",
    smoke_dir=ROOT / "runs" / "e3e-smoke", design="docs/E3/E3e-DESIGN.md",
    designs={"docs/E3/E3e-DESIGN.md": "design_sha256", "docs/E3/E3d-DESIGN.md": "parent_design_sha256"},
    runners=["scripts/e3e.py", "scripts/e3d.py"],
    registry={**BINDING, "c": 7, "maze_seed": 1_191_000,
              "blocks": {"calibration": [31_000, 31_128], "confirmation": [31_200, 31_456],
                         "tree_reference": [31_200, 31_328], "tangent": [31_200, 31_264]}})


if __name__ == "__main__":
    from wormwars.accounting import run_script
    if any(a == "--out" or a.startswith("--out=") for a in sys.argv[1:]):
        raise SystemExit("--out is not accepted: E3e writes only to its own folders")
    smoke = "--smoke" in sys.argv
    out_dir = ROOT / "runs" / ("e3e-smoke" if smoke else "e3e")
    try:
        run_script(D.main, out_default=str(out_dir), default="measure", name=NAME)
    finally:
        agg = out_dir / "compute.json"
        if agg.exists() and not smoke:
            D.EXP.mkdir(parents=True, exist_ok=True)
            (D.EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
