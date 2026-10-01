"""E4s design, exploratory: the evolved champions' open-loop response to a left-right difference (v3).

    python scripts/e4s_gain_probe.py     # writes experiments/E4s-stereo-module/development-records/gain-probe.json

Each distinct champion's brain (E2's 31 and 04a's 16) receives scent currents at its left and right
sensory neurons (AWA, AWC and ASE, as the interface injects them): a common level c with a left-right
difference δ, all other inputs zero, from a zero state. The turn command is read as the world reads it
(the turn neurons' mean tanh, dorsal minus ventral, times 0.5 × turn gain, clamped).

Measured, per genome and common level (review v1 of the E4s design, D141):
- **small-signal gain:** the central difference (T(+δ) − T(−δ)) / 2δ at δ = 0.001, after 40 ticks,
  averaged over the last 10. A least-squares slope over a wide δ grid (v1) caps a clipped
  controller's apparent gain (an ideal k = 256 reads about 67), so it is dropped;
- **signed response curve:** T(δ) for δ = 0, ±0.001, ±0.003, ±0.01, ±0.03, ±0.1;
- **transient:** after 40 ticks at δ = 0, the largest difference over the next 40 ticks between a
  step to δ = +0.01 and a control that stays at δ = 0 (v2 had no control, so it measured drift too;
  review v2 of the design, D142);
- **carried-state reversal:** after 40 ticks at δ = +0.01, the difference between switching to
  δ = −0.01 and a control that stays at +0.01, averaged over the last 10 of the next 40 ticks, as a
  gain (divided by 0.02); and the history effect: the switched arm against a zero start at −0.01;
- **the turn neurons:** each one's tanh at δ = 0 (after 40 ticks), and the share with |tanh v| > 0.99.

It describes weak or strong sustained differential responses under these conditions only. It does
not show why the plateau exists, nor that the champions use a temporal strategy. It informs the
design; it is not a registered measure.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.evo.genomes import genome_hash  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

OUT = ROOT / "experiments" / "E4s-stereo-module" / "development-records" / "gain-probe.json"
COMMON = [0.02, 0.08, 0.25]
SMALL = 0.001
CURVE = [-0.1, -0.03, -0.01, -0.003, -0.001, 0.0, 0.001, 0.003, 0.01, 0.03, 0.1]
TICKS, AVG, STEP = 40, 10, 0.01


def load_e2d():
    s = importlib.util.spec_from_file_location("e2d_for_probe", ROOT / "scripts" / "e2d.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


class Probe:
    def __init__(self, brain, iface, cfg, n):
        self.brain, self.cfg, self.n = brain, cfg, n
        names = list(iface.signal_names)
        self.left = [int(iface.sensor_neuron[i]) for i, s in enumerate(names) if s == "food_left"]
        self.right = [int(iface.sensor_neuron[i]) for i, s in enumerate(names) if s == "food_right"]
        self.tp = torch.as_tensor(np.asarray(iface.turn_plus))
        self.tm = torch.as_tensor(np.asarray(iface.turn_minus))
        self.S = brain.n_strains

    def current(self, c, d):
        cur = torch.zeros(self.S, 1, self.n)
        cur[..., self.left] = c + d / 2
        cur[..., self.right] = c - d / 2
        return cur

    def turn(self, v):
        act = torch.tanh(v)
        t = act[..., self.tp].mean(-1) - act[..., self.tm].mean(-1)
        return (t * 0.5 * self.cfg.world.turn_gain).clamp(-1, 1)[:, 0]

    def run(self, v, c, d, ticks=TICKS):
        cur, trace = self.current(c, d), []
        for _ in range(ticks):
            v = self.brain.step(v, cur)
            trace.append(self.turn(v))
        return v, torch.stack(trace)  # [ticks, strains]

    def settled(self, c, d):
        _, tr = self.run(self.brain.initial_state(1), c, d)
        return tr[-AVG:].mean(0).numpy()


def main():
    d = load_e2d()
    cfg = d.E.task_config()
    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con)
    champs = {k: v[0] for k, v in d.e2_champions(spec, cfg).items()}
    champs.update({k: v[0] for k, v in d.e04a_champions(spec, cfg).items()})
    seen, labels = set(), []
    for k, g in champs.items():
        h = genome_hash(g, 0)
        if h not in seen:
            seen.add(h)
            labels.append(k)
    genome = Genome.cat([champs[k] for k in labels])
    p = Probe(Brain(genome), iface, cfg, spec.n)
    per = {}
    for c in COMMON:
        small = (p.settled(c, SMALL) - p.settled(c, -SMALL)) / (2 * SMALL)
        curve = np.stack([p.settled(c, x) for x in CURVE], axis=1)  # [strains, deltas]
        v0, _ = p.run(p.brain.initial_state(1), c, 0.0)
        _, step = p.run(v0, c, STEP)
        _, stay0 = p.run(v0, c, 0.0)
        transient = (step - stay0).abs().max(0).values.numpy()
        vpos, _ = p.run(p.brain.initial_state(1), c, STEP)
        _, neg = p.run(vpos, c, -STEP)
        _, stay = p.run(vpos, c, STEP)
        switched, control = neg[-AVG:].mean(0).numpy(), stay[-AVG:].mean(0).numpy()
        zero_start_minus = curve[:, CURVE.index(-STEP)]
        act = torch.tanh(v0)[:, 0][:, torch.cat([p.tp, p.tm])]
        per[str(c)] = {"small_signal_gain": small.tolist(), "curve": curve.tolist(),
                       "transient_max_difference_from_control": transient.tolist(),
                       "reversal": {"switched": switched.tolist(), "control": control.tolist(),
                                    "carried_state_gain": ((control - switched) / (2 * STEP)).tolist(),
                                    "history_effect": (switched - zero_start_minus).tolist()},
                       "turn_neurons_tanh": act.tolist(),
                       "turn_neurons_saturated_share": (act.abs() > 0.99).float().mean(1).tolist()}
    gains = np.abs(np.array([per[str(c)]["small_signal_gain"] for c in COMMON]))
    carried = np.abs(np.array([per[str(c)]["reversal"]["carried_state_gain"] for c in COMMON]))
    history = np.abs(np.array([per[str(c)]["reversal"]["history_effect"] for c in COMMON]))
    doc = {"what": "E4s design, exploratory: the champions' open-loop response to a left-right difference (v3)",
           "genomes": labels, "genome_sha256": sorted(seen), "common": COMMON, "small_delta": SMALL, "curve_deltas": CURVE,
           "ticks": TICKS, "averaged_over_last": AVG, "step": STEP, "per_common": per,
           "summary": {"median_abs_small_signal_gain": float(np.median(gains)), "max_abs_small_signal_gain": float(gains.max()),
                       "median_abs_small_signal_gain_per_common": {str(c): float(np.median(gains[i])) for i, c in enumerate(COMMON)},
                       "median_transient_max_difference_from_control": float(np.median(
                           [per[str(c)]["transient_max_difference_from_control"] for c in COMMON])),
                       "median_abs_carried_state_gain": float(np.median(carried)),
                       "max_abs_carried_state_gain": float(carried.max()),
                       "median_abs_history_effect": float(np.median(history)),
                       "max_abs_history_effect": float(history.max()),
                       "mean_turn_neuron_saturation": float(np.mean([per[str(c)]["turn_neurons_saturated_share"] for c in COMMON])),
                       "e1_scripted_k_for_reference": {"4": 2.38, "32": 5.63, "256": 8.51, "8192": 8.78}},
           "provenance": {"git_commit": reg.git("rev-parse", "HEAD"),
                          "script_sha256": reg.file_sha256(Path(__file__)),
                          "resolved_config_sha256": d.E.config_sha256(cfg),
                          "dirty": bool(subprocess.run(["git", "status", "--porcelain", "--", "scripts", "wormwars"],
                                                       cwd=ROOT, capture_output=True, text=True).stdout.strip())},
           "note": "open-loop, zero start, other inputs zero; descriptive and design-informing, not a registered measure"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["summary"], indent=1))


if __name__ == "__main__":
    main()
