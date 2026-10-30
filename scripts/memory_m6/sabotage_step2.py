"""Rule 9 for M6, step 2: each guarded behaviour of step2.py and step2_read.py broken in turn; the matching test in
tests/test_memory_m6_step2.py must fail. Restores every file afterwards. Writes runs/step2-sabotage.txt.

Usage: python scripts/memory_m6/sabotage_step2.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D, RD = ROOT / "scripts" / "memory_m6" / "step2.py", ROOT / "scripts" / "memory_m6" / "step2_read.py"
CASES = [
    (D, "    out.cfg = dataclasses.replace(out.cfg, substeps=int(round(sub)))\n", "", "exact"),
    (D, "if g.cfg.substeps != BASE_SUBSTEPS or abs(sub - round(sub)) > 1e-9:", "if False:", "never_clamps"),
    (D, "    return out\n\n\ndef arm_genome", "    out.clamp_()\n    return out\n\n\ndef arm_genome", "never_clamps"),
    (D, "        mask[keep] = False\n", "", "never_clamps"),
    (D, 'for name in ("forward_plus", "forward_minus", "turn_plus", "turn_minus", "pump_neurons"):',
     'for name in ("forward_plus", "forward_minus", "turn_plus", "turn_minus"):', "boundary"),
    (D, 'out.append((k, ["g39", *CTRL] if k in CTRL_KS else ["g39"]))', 'out.append((k, ["g39", *CTRL]))', "batch"),
    (D, 'return out + [(INTERIOR, ["g39"]), (ALONE, ["g39"])]', 'return out + [(INTERIOR, ["g39"])]', "batch"),
    (D, "return elapsed / sum(load_of(r) for r in done_runs) * sum(load_of(r) for r in recs)",
     "return elapsed / len(done_runs) * len(recs)", "forecast"),
    (RD, 'return "reduced" if iv[1] < 0 else', 'return "reduced" if iv[0] < 0 else', "null_and_increase"),
    (RD, '            return f"The reduction was smaller than that of {name}."\n', "", "smaller"),
    (RD, "REL_TOL = 0.02", "REL_TOL = 0.6", "guards"),
    (RD, "VALID_MEDIAN, VALID_SHARE = 0.5, 0.9", "VALID_MEDIAN, VALID_SHARE = 0.9, 0.9", "guards"),
    (RD, 'and out["4"]["median"] is not None and out["4"]["median"] > 1)', ")", "guards"),
    (RD, "    if why:  # every interpretive sentence is gated", "    if False:  # every interpretive sentence is gated",
     "guards"),
    (RD, "    if missing:\n", "    if False:\n", "missing_arm"),
    (RD, 'return None if base < FLOOR else s[arm]["mean"] / base - 1', 'return s[arm]["mean"] / base - 1', "floor"),
    (RD, "k0 = t0_by.get((block[k], mapping[k]))", 'k0 = t0_by.get((block[k], "M0" if mapping[k] == "MS" else mapping[k]))',
     "floor_and_t0"),
    (RD, "    r = spearmanr(x, y).statistic\n",
     "    r = float(np.corrcoef(np.argsort(np.argsort(x)), np.argsort(np.argsort(y)))[0, 1])\n", "spearman"),
    (RD, 'return "1" if arm in ("0.25", "4") else ALONE', 'return "1"', "composition_baseline"),
]


def main():
    lines, bad = [], 0
    for path, old, new, test in CASES:
        src = path.read_text(encoding="utf-8")
        assert src.count(old) == 1, (path.name, old)
        path.write_text(src.replace(old, new), encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", str(ROOT / "tests" / "test_memory_m6_step2.py"),
                                "-k", test], cwd=ROOT, capture_output=True, text=True)
        finally:
            path.write_text(src, encoding="utf-8")
        caught = r.returncode != 0
        bad += not caught
        lines.append(f"{'caught ' if caught else 'MISSED '} {path.name}: {old.strip()[:60]!r} -> {new.strip()[:40]!r} ({test})")
        print(lines[-1], flush=True)
    lines.append(f"{len(CASES) - bad} of {len(CASES)} caught")
    (ROOT / "runs" / "step2-sabotage.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(lines[-1])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
