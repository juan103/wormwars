"""M4e's change to the frozen classifier's orchestration (scripts/memory_m2/pilot.py: two optional parameters,
follow_ticks and tail_from) leaves the default path unchanged: the version before the change (commit c037f7d) and
the current one classify the planted genomes (R6's check) and 64 genomes of a fresh host identically, record for
record (Fable, Astra, M4e plan review round 1).

    python scripts/memory_m4/m4e_pilot_equivalence.py     # minutes; writes runs/memory-m4e/pilot-equivalence.json

The old version is written beside the current one for the run (it locates the repository from its own path) and
removed afterwards.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BEFORE = "c037f7d"
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m4"))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def clean(x):
    """JSON round trip, so tensors and numpy scalars compare as values."""
    return json.loads(json.dumps(x, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))


def main():
    old_path = ROOT / "scripts" / "memory_m2" / f"_pilot_{BEFORE}.py"
    old_path.write_bytes(subprocess.run(["git", "show", f"{BEFORE}:scripts/memory_m2/pilot.py"], cwd=ROOT,
                                        capture_output=True, check=True).stdout)
    try:
        old = load(old_path, "pilot_old")
        new = load(ROOT / "scripts" / "memory_m2" / "pilot.py", "pilot_new")
        import m4d
        out = {"before": BEFORE}
        p_old, p_new = clean(old.planted_check()), clean(new.planted_check())
        out["planted_identical"] = p_old == p_new
        out["planted_passes"] = [p_old["passes"], p_new["passes"]]
        con, _ = m4d.build_host("SH", 2019100)
        g, cfg = m4d.host_genomes(con, 64, 8999)
        run = new.probe_states(g, cfg)
        sub = {"end": run["end"], "cur": run["cur"], "y": run["y"], "tail": run["tail"]}
        r_old, _ = old.full_classify(g, cfg, sub, compact=True)
        r_new, _ = new.full_classify(g, cfg, sub, compact=True)
        out["host_genomes"] = 64
        out["host_identical"] = clean(r_old) == clean(r_new)
        out["host_classes"] = sorted({r["class"] for r in r_new})
        out["identical"] = out["planted_identical"] and out["host_identical"]
    finally:
        old_path.unlink()
    (ROOT / "runs" / "memory-m4e").mkdir(parents=True, exist_ok=True)
    (ROOT / "runs" / "memory-m4e" / "pilot-equivalence.json").write_text(json.dumps(out, indent=1) + "\n",
                                                                          encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    if not out["identical"]:
        raise SystemExit("the default path changed")


if __name__ == "__main__":
    main()
