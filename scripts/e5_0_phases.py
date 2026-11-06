"""E5-0, after the data (exploratory): how the hunt's phases change with the route prey's speed. For each captured
life with a logged first contact, the ticks from activation to first contact (the approach), from first contact to
capture (the kill), and the contact ticks (the hunter's head within 1.5 of a prey body point) in the life; captured
lives without a logged contact are counted apart, since a bite can land before that criterion is met (the bite point is
0.9 ahead of the head). Medians are over captured lives only. Also the attack-disabled check's damage total, which
the evaluate stage enforces by a stop but no committed record holds. From the local event tables in
runs/e5-0/evaluation/.

    python scripts/e5_0_phases.py        # writes experiments/E5-hunter/E5-0/phases.json

Written after seeing reading.json; it decides nothing. CPU only, no simulation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "E5-hunter" / "E5-0"
EVAL = ROOT / "runs" / "e5-0" / "evaluation"
SETTINGS = ["H1-bite"] + [f"H2-{s}" for s in ("0.1", "0.3", "0.5", "0.7", "1")]
HUNTERS = ["S-const tuned", "S-const E1-frozen", "pursuit", "L1 carrier", "e4s1 M run00", "e4s1 M run03",
           "e2 ga run00"]


def median(x: np.ndarray):
    return float(np.median(x)) if x.size else None


def phases(z, label: str) -> dict:
    act, cap = z[f"{label}|ev activation_tick"], z[f"{label}|ev capture_tick"]
    first = z[f"{label}|ev first_contact_tick"]
    caught = cap >= 0
    timed = caught & (first >= 0)
    return {"captures_mean": float(z[f"{label}|captures"].mean()), "captured_lives": int(caught.sum()),
            "captured_without_contact": int((caught & (first < 0)).sum()),
            "approach_median": median((first - act)[timed]), "kill_median": median((cap - first)[timed]),
            "contact_ticks_median": median(z[f"{label}|ev contact_ticks"][timed])}


def main():
    out = {"note": "exploratory, written after the reading; medians over captured lives with a logged first contact, "
                   "on the 512 evaluation worlds", "settings": {}}
    for s in SETTINGS:
        z = np.load(EVAL / f"{s}.npz", allow_pickle=False)
        out["settings"][s] = {h: phases(z, h) for h in HUNTERS}
        if s == "H1-bite":
            out["attack_disabled"] = {"captures": int(z["pursuit attack-disabled|captures"].sum()),
                                      "damage": float(z["pursuit attack-disabled|ev damage"].sum())}
    (EXP / "phases.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for s, row in out["settings"].items():
        print(s, {h: (round(v["captures_mean"], 2), v["approach_median"], v["kill_median"], v["contact_ticks_median"],
                      v["captured_without_contact"]) for h, v in row.items()})
    print("attack-disabled", out["attack_disabled"])


if __name__ == "__main__":
    main()
