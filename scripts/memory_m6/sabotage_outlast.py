"""Rule 9 for M6, step 1: each guarded behaviour of outlast.py and outlast_read.py broken in turn; the matching test
in tests/test_memory_m6_outlast.py must fail. Restores every file afterwards. Writes runs/outlast-sabotage.txt.

Usage: python scripts/memory_m6/sabotage_outlast.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D, RD = ROOT / "scripts" / "memory_m6" / "outlast.py", ROOT / "scripts" / "memory_m6" / "outlast_read.py"
CASES = [
    (D, 'return dict(c.S.BANK, food_left=0.0, food_right=0.0)', 'return {k: 0.0 for k in c.S.BANK}', "changed_inputs"),
    (D, 'return {k: 0.0 for k in c.S.BANK}', 'return dict(c.S.BANK, food_left=0.0, food_right=0.0)', "changed_inputs"),
    (D, '    with c.probe_input(c.S.IFACE, bank):\n        return go()', '    return go()', "wires"),
    (D, 'compact=True, initial=start.float())', 'compact=True)', "wires"),
    (D, 'return b, phase_from(g, cfg, b[0]["end"])', 'return b, phase_from(g, cfg, a_end)', "wires"),
    (D, 'N_PANEL = 1024', 'N_PANEL = 512', "rebuild or genome_list"),
    (D, 'g, cfg = c.S.genomes(census.graph_of("N2"), N_PANEL, seed)', 'g, cfg = c.S.genomes(census.graph_of("N2"), N_PANEL, seed + 1)',
     "rebuild"),
    (D, 'SWITCH = ("separate states", "separate states, read-out silent")', 'SWITCH = ("separate states",)',
     "genome_list or outcome"),
    (D, 'SEEN_SEED, SEEN_N = 7700, 4', 'SEEN_SEED, SEEN_N = 7700, 5', "genome_list"),
    (D, 'TOL = K.DISTINCT', 'TOL = 1e-4', "genome_list or root_match"),
    (D, '"swapped" if x[0][1] and x[1][0]', '"new" if x[0][1] and x[1][0]', "root_match"),
    (D, '"ambiguous" if amb else', '"ambiguous" if False else', "root_match"),
    (D, 'if cls_c == "unresolved":', 'if False:', "outcome"),
    (D, 'if cls_c in SWITCH and m == "same":', 'if cls_c in SWITCH:', "outcome"),
    (D, 'return "unresolved" if cls_b == "unresolved" else', 'return "not held" if cls_b == "unresolved" else', "outcome"),
    (D, 'cols = [(dense[:, t, 0] - dense[:, t, 1]).abs().amax(-1) for t in SEP_TICKS]',
     'cols = [(dense[:, t + 1, 0] - dense[:, t + 1, 1]).abs().amax(-1) for t in SEP_TICKS]', "separation"),
    (RD, 'n, k, u = len(values), values.count(yes), values.count("unresolved")',
     'n, k, u = len(values), values.count(yes), 0', "wordings"),
    (RD, 'f"{GAP}-tick removal of {w}{unres(rc[\'unresolved\'])}"', 'f"removal of {w}{unres(rc[\'unresolved\'])}"',
     "wordings"),
    (RD, 'if not run.get("complete") or len(got) != len(set(got)) or set(got) != want:', 'if False:', "guards"),
    (RD, 'rows = [r for r in run["rows"] if r["A"]["class"] == r["census_class"]]', 'rows = run["rows"]', "guards"),
    (RD, 'if run.get("stopped"):', 'if False:', "guards"),
    (RD, 'if failed > int(STOP_FRACTION * len(want)):', 'if False:', "guards"),
    (RD, 'Z95 = 1.959963984540054', 'Z95 = 1.644853626951472', "wilson"),
]


def main():
    lines, bad = [], 0
    for path, old, new, test in CASES:
        src = path.read_text(encoding="utf-8")
        assert src.count(old) == 1, (path.name, old)
        path.write_text(src.replace(old, new), encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", str(ROOT / "tests" / "test_memory_m6_outlast.py"),
                                "-k", test], cwd=ROOT, capture_output=True, text=True)
        finally:
            path.write_text(src, encoding="utf-8")
        caught = r.returncode != 0
        bad += not caught
        lines.append(f"{'caught ' if caught else 'MISSED '} {path.name}: {old[:60]!r} -> {new[:40]!r} ({test})")
        print(lines[-1], flush=True)
    lines.append(f"{len(CASES) - bad} of {len(CASES)} caught")
    (ROOT / "runs" / "outlast-sabotage.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(lines[-1])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
