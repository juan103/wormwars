"""E4s design, exploratory: the evolved champions' open-loop stereo gain.

    python scripts/e4s_gain_probe.py     # writes experiments/E4s-stereo-module/development-records/gain-probe.json

Each champion's brain (E2's 31 distinct champions and 04a's 16) receives a fixed scent current at
its left and right sensory neurons (AWA, AWC and ASE, as the interface injects it): a common level
c with a left-right difference δ, held for 40 ticks, all other inputs zero. The turn command is read
as the world reads it (the turn neurons' mean tanh, dorsal minus ventral, times 0.5 × turn gain,
clamped) and averaged over the last 10 ticks. The slope of the turn command against δ, at each c, is
the brain's effective stereo gain, comparable with E1's scripted k (turn = bias + k(L − R)).

It tests one hypothesis from the E4s literature report: that the champions' stereo gain is tiny
next to the k of about 250 a stereo steerer needs. It is open-loop (no world, no movement) and
descriptive; it informs the design and is not a registered measure.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.brain import Brain, BrainSpec  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

OUT = ROOT / "experiments" / "E4s-stereo-module" / "development-records" / "gain-probe.json"
COMMON = [0.02, 0.08, 0.25]  # the report's range of common-mode currents
DELTAS = [-0.02, -0.01, -0.005, 0.0, 0.005, 0.01, 0.02]
TICKS, AVG = 40, 10


def load_e2d():
    spec_ = importlib.util.spec_from_file_location("e2d_for_probe", ROOT / "scripts" / "e2d.py")
    mod = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(mod)
    return mod


def turn_of(brain, iface, cfg, currents: torch.Tensor) -> np.ndarray:
    """Mean turn command over the last AVG of TICKS ticks, per strain; `currents` [strains, 1, n]."""
    v = brain.initial_state(1)
    tp = torch.as_tensor(np.asarray(iface.turn_plus))
    tm = torch.as_tensor(np.asarray(iface.turn_minus))
    out = []
    for t in range(TICKS):
        v = brain.step(v, currents)
        if t >= TICKS - AVG:
            act = torch.tanh(v)
            turn = act[..., tp].mean(-1) - act[..., tm].mean(-1)
            out.append((turn * 0.5 * cfg.world.turn_gain).clamp(-1, 1)[:, 0])
    return torch.stack(out).mean(0).numpy()


def main():
    d = load_e2d()
    cfg = d.E.task_config()
    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con)
    champs = {k: v[0] for k, v in d.e2_champions(spec, cfg).items()}
    champs.update({k: v[0] for k, v in d.e04a_champions(spec, cfg).items()})
    shas = {}
    labels = []
    for k, g in champs.items():  # one entry per distinct genome
        from wormwars.evo.genomes import genome_hash
        h = genome_hash(g, 0)
        if h not in shas:
            shas[h] = k
            labels.append(k)
    from wormwars.brain import Genome
    genome = Genome.cat([champs[k] for k in labels])
    brain = Brain(genome)
    names = list(iface.signal_names)
    left = [int(iface.sensor_neuron[i]) for i, s in enumerate(names) if s == "food_left"]
    right = [int(iface.sensor_neuron[i]) for i, s in enumerate(names) if s == "food_right"]
    S, n = genome.n_strains, spec.n
    table = {}
    for c in COMMON:
        turns = []
        for dl in DELTAS:
            cur = torch.zeros(S, 1, n)
            cur[..., left] = c + dl / 2
            cur[..., right] = c - dl / 2
            turns.append(turn_of(brain, iface, cfg, cur))
        turns = np.stack(turns, axis=1)  # [strains, deltas]
        slope = np.polyfit(np.asarray(DELTAS), turns.T, 1)[0]  # per strain
        table[str(c)] = {"turn_at_zero": turns[:, DELTAS.index(0.0)].tolist(), "slope_k": slope.tolist()}
    ks = np.array([table[str(c)]["slope_k"] for c in COMMON])  # [commons, strains]
    doc = {"what": __doc__.strip().splitlines()[0], "genomes": labels, "common": COMMON, "deltas": DELTAS,
           "ticks": TICKS, "averaged_over_last": AVG, "per_common": table,
           "summary": {"median_abs_k": float(np.median(np.abs(ks))), "max_abs_k": float(np.abs(ks).max()),
                       "median_abs_k_per_common": {str(c): float(np.median(np.abs(ks[i]))) for i, c in enumerate(COMMON)},
                       "share_turn_saturated_at_zero": float(np.mean([np.abs(np.asarray(table[str(c)]["turn_at_zero"])) >= 0.99
                                                                       for c in COMMON])),
                       "e1_scripted_k_for_reference": {"4": 2.38, "32": 5.63, "256": 8.51, "8192": 8.78}},
           "note": "open-loop, descriptive, design-informing; not a registered measure"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["summary"], indent=1))


if __name__ == "__main__":
    main()
