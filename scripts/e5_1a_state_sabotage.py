"""Amendment 1's state-level check, seen failing (AGENTS.md rule 9; docs/E5/E5-1-DESIGN.md §14.3). At the formal
training shape (128 strains x 8 rows), 300 ticks, on the 16 E4s-1 C genomes: the CUDA copy of one stable genome
(E4s-1 run 2, whose float32 error is small) is changed, while it shares the batch with run 1, the most sensitive one.
The change must fail that genome's row and leave the others passing; the clean run must pass. GPU.

    python scripts/e5_1a_state_sabotage.py   -> runs/e5-1/amend1-sabotage-formal.txt
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "e5-1" / "amend1-sabotage-formal.txt"
STABLE = 2  # E4s-1 run 2's strain in the champion family (its float32 error is about 5e-5 at 16 x 8)
SIZES = {"bias + 1e-3": 1e-3, "bias + 1e-5": 1e-5}


def main():
    spec = importlib.util.spec_from_file_location("e5_1a_for_sabotage", ROOT / "scripts" / "e5_1a.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.OUT = ROOT / "runs" / "e5-1a-sabotage"  # its own cap clock, apart from E5-1a's
    env = m.Env()
    shape = {"training": (128, 8)}
    lines = []

    def perturbed(size):
        def f(g):
            bias = g.bias.clone()
            bias[STABLE::16] += size  # every copy of run 2 in the tiled batch
            return g.with_params(bias=bias)
        return f

    for label, size in SIZES.items():
        r = m.state_level(env, "cuda", perturb=perturbed(size), shapes=shape, families=["E4s-1 C"])
        row = r["strains"]["e4s1 M run02 | training"]
        others = [k for k in r["failed"] if not k.startswith("e4s1 M run02")]
        lines.append(f"{label}: run 2 passed={row['passed']} checks={row['checks']} one step={row['one step']:.3g} "
                     f"cuda32-cpu64={row['cuda32 - cpu64']:.3g} bound={row['bound']:.3g}; other rows failing: {others}")
    r = m.state_level(env, "cuda", shapes=shape, families=["E4s-1 C"])
    lines.append(f"clean: passed={r['passed']} failed={r['failed']} worst one step={r['worst_one_step']:.3g} "
                 f"worst cpu-cuda={r['worst_cpu_cuda']:.3g}")
    lines.append(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "checks"} for k, v in r["strains"].items()}))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines[:-1]))


if __name__ == "__main__":
    torch.set_grad_enabled(False)
    sys.exit(main())
