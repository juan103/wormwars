"""E5-1a's state-level stop (2026-11-11), diagnosis (exploratory; docs/E5/E5-1-DESIGN.md §7.3 says a failure is
diagnosed and amended). The CUDA stage found CPU against CUDA open-loop state differences of 2.5e-3 to 1.1e-2 for the
16 E4s-1 C genomes over 300 ticks, against a 1e-4 tolerance, while generation-0 genomes stayed near 1e-5.

Question: is CUDA special, or do the evolved champions amplify any float32 rounding difference? Under the same
imposed inputs as the stage (uniform [0, 1] x gain at every sensor, seed 7), per genome and per tick:
- CPU float32 against CUDA float32 (the stage's comparison);
- CPU float32 against CPU float64 (rounding against a near-exact reference);
- CUDA float32 against CPU float64;
- CPU float32 at two compositions (the 16 genomes as 16 strains, and each alone, padded), 8 rows each;
and where the largest difference sits (neuron), and what it does to the motor read-out (forward and turn commands).

    python experiments/E5-hunter/E5-1/E5-1a/diagnosis/state_level_diagnosis.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from wormwars.brain import Brain  # noqa: E402
from wormwars.connectome.loader import load_connectome  # noqa: E402
from wormwars.e04a.evolve import moved  # noqa: E402
from wormwars.e4s import arms as EA  # noqa: E402
from wormwars.e4s import comparator as CMP  # noqa: E402
from wormwars.e5 import graphs as GR  # noqa: E402
from wormwars.e5 import hunters as HN  # noqa: E402
from wormwars.e5.hunt import hunt_config  # noqa: E402

torch.set_grad_enabled(False)
TICKS, ROWS = 300, 8


def as64(g):
    return g.with_params(**{k: v.double() for k, v in g.params().items() if v is not None})


def run(brain, inputs, device, dtype):
    v = brain.initial_state(ROWS).to(device, dtype)
    out = []
    for cur in inputs:
        v = brain.step(v, cur.to(device, dtype))
        out.append(v.detach().cpu().double())
    return torch.stack(out)  # [ticks, S, B, N]


def main():
    con = load_connectome()
    cfg = hunt_config()
    l1 = EA.load_l1()
    ext, spec, gface = GR.grafted(con, l1)
    champs = HN.e4s1_champions(con, cfg.brain)
    labels = list(champs)
    gen = None
    from wormwars.brain import Genome
    gen = Genome.cat([g for g, _ in champs.values()])
    S = gen.n_strains
    idx = torch.as_tensor(np.asarray(gface.sensor_neuron), dtype=torch.long)
    gain = torch.as_tensor(np.asarray(gface.sensor_gain), dtype=torch.float32)
    rng = torch.Generator().manual_seed(7)
    inputs = []
    for _ in range(TICKS):
        cur = torch.zeros(S, ROWS, spec.n)
        cur[:, :, idx] = torch.rand(S, ROWS, len(idx), generator=rng) * gain
        inputs.append(cur)
    cpu32 = run(Brain(gen), inputs, "cpu", torch.float32)
    cpu64 = run(Brain(as64(gen)), [c.double() for c in inputs], "cpu", torch.float64)
    cuda32 = run(Brain(moved(gen, "cuda")), inputs, "cuda", torch.float32)
    alone = torch.cat([run(Brain(gen.select([s])), [c[s:s + 1] for c in inputs], "cpu", torch.float32)
                       for s in range(S)], dim=1)

    def gap(a, b):  # [ticks, S]: the largest |difference| over rows and neurons, per tick and genome
        return (a - b).abs().amax(dim=(2, 3))

    pairs = {"cpu32 - cuda32": gap(cpu32, cuda32), "cpu32 - cpu64": gap(cpu32, cpu64),
             "cuda32 - cpu64": gap(cuda32, cpu64), "cpu32 batch - cpu32 alone": gap(cpu32, alone)}
    act = lambda v: torch.tanh(v)  # noqa: E731
    fwd = lambda v: (act(v[..., list(gface.forward_plus)]).mean(-1) - act(v[..., list(gface.forward_minus)]).mean(-1)) \
        * 0.5 * cfg.world.forward_gain  # noqa: E731
    turn = lambda v: (act(v[..., list(gface.turn_plus)]).mean(-1) - act(v[..., list(gface.turn_minus)]).mean(-1)) \
        * 0.5 * cfg.world.turn_gain  # noqa: E731
    d = (cpu32 - cuda32).abs()
    where = d.amax(dim=(0, 2)).argmax(dim=-1)  # per genome, the neuron with the largest difference
    out = {"ticks": TICKS, "rows": ROWS, "genomes": labels, "by_genome": {}}
    for s, lab in enumerate(labels):
        row = {k: {"max": float(v[:, s].max()), "at_tick_50": float(v[49, s]), "at_tick_100": float(v[99, s]),
                   "at_tick_300": float(v[-1, s]),
                   "first_tick_above_1e-4": int(torch.nonzero(v[:, s] > 1e-4)[0, 0]) + 1
                   if bool((v[:, s] > 1e-4).any()) else None}
               for k, v in pairs.items()}
        n = int(where[s])
        row["neuron_of_largest_cpu_cuda_difference"] = ext.names[n]
        row["motor_command_max_abs_difference"] = {
            "forward": float((fwd(cpu32[:, s]) - fwd(cuda32[:, s])).abs().max()),
            "turn": float((turn(cpu32[:, s]) - turn(cuda32[:, s])).abs().max())}
        out["by_genome"][lab] = row
    summary = {k: {"median_max": float(v.max(0).values.median()), "worst": float(v.max())} for k, v in pairs.items()}
    out["summary"] = summary
    path = Path(__file__).with_name("state_level_diagnosis.json")
    path.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1))
    for lab, r in out["by_genome"].items():
        print(lab, {k: round(v["max"], 6) for k, v in r.items() if isinstance(v, dict) and "max" in v},
              r["neuron_of_largest_cpu_cuda_difference"],
              {k: round(v, 5) for k, v in r["motor_command_max_abs_difference"].items()})


if __name__ == "__main__" and "--shapes" not in sys.argv:
    main()


def stage_shapes():
    """The stage's own shapes and inputs (scripts/e5_1a.py `state_level`: seed 7 per group, the genomes in groups of
    the shape's strains): per shape, the largest CPU-CUDA difference against each side's distance from float64."""
    con = load_connectome()
    cfg = hunt_config()
    l1 = EA.load_l1()
    ext, spec, gface = GR.grafted(con, l1)
    from wormwars.brain import Genome
    gen = Genome.cat([g for g, _ in HN.e4s1_champions(con, cfg.brain).values()])
    idx = torch.as_tensor(np.asarray(gface.sensor_neuron), dtype=torch.long)
    gain = torch.as_tensor(np.asarray(gface.sensor_gain), dtype=torch.float32)
    out = {}
    for shape, (S, B) in {"training": (128, 8), "validation": (4, 256), "suite": (8, 512)}.items():
        worst = {"cpu32 - cuda32": 0.0, "cpu32 - cpu64": 0.0, "cuda32 - cpu64": 0.0}
        for lo in range(0, gen.n_strains, S):
            g = gen.select([(lo + i) % gen.n_strains for i in range(S)])
            rng = torch.Generator().manual_seed(7)
            b32, b64, bg = Brain(g), Brain(as64(g)), Brain(moved(g, "cuda"))
            v32, v64, vg = b32.initial_state(B), b64.initial_state(B).double(), bg.initial_state(B)
            for _ in range(TICKS):
                cur = torch.zeros(S, B, spec.n)
                cur[:, :, idx] = torch.rand(S, B, len(idx), generator=rng) * gain
                v32, v64, vg = b32.step(v32, cur), b64.step(v64, cur.double()), bg.step(vg, cur.to("cuda"))
                c = vg.cpu().double()
                worst["cpu32 - cuda32"] = max(worst["cpu32 - cuda32"], float((v32.double() - c).abs().max()))
                worst["cpu32 - cpu64"] = max(worst["cpu32 - cpu64"], float((v32.double() - v64).abs().max()))
                worst["cuda32 - cpu64"] = max(worst["cuda32 - cpu64"], float((c - v64).abs().max()))
        out[shape] = worst
        print(shape, worst)
    path = Path(__file__).with_name("state_level_diagnosis_shapes.json")
    path.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__" and "--shapes" in sys.argv:
    stage_shapes()
