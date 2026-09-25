"""Two measurements before the pre-registration, on pilot-only shuffles SH101-SH108 (no N2):

1. The corrected generation-0 input response (Astra's decision review, point 3): the
   left-right difference at a fixed common mode, signed and absolute, raw read-out and motor
   command, with each shuffle's own calibrated gains.
2. The cost of the frozen probe suite (D038) on the pilot champions: channels on the 64 probe
   worlds for generation 0 and 39, integrator and behaviour for generation 39.

Writes structure_and_timing.json next to this file."""

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from wormwars import calibration as calib  # noqa: E402
from wormwars.brain import BrainSpec  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.connectome.graphs import shuffled  # noqa: E402
from wormwars.evo import load_genome  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.exp02 import probes as P  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

dev = "cuda"
con = load_connectome()
iface = load_interface(con)
out = {"input_response": {}, "timing": {}}

for k in range(101, 109):
    name = f"SH{k}"
    graph = shuffled(con, k, name)
    cfg = grid.task_config(Config(), "T0")
    cal = calib.calibrate_in_world(graph, cfg, iface, grid.TARGET_DRIVE, n_strains=grid.CALIBRATION_STRAINS,
                                   device=dev)
    cfg.world.forward_gain, cfg.world.turn_gain = cal.forward_gain, cal.turn_gain
    spec = BrainSpec.from_connectome(graph, device=dev)
    r = P.input_response(spec, cfg, iface, 256, dev)
    summary = {key: float(np.mean(v)) for key, v in r.items()}
    out["input_response"][name] = {"gains": [cal.forward_gain, cal.turn_gain], "mean_over_ticks": summary,
                                   "traces": r}
    print(f"{name}: directional turn |raw| {summary['directional_turn_raw']:.4f} signed "
          f"{summary['directional_turn_signed_raw']:+.4f}; motor |{summary['directional_turn_motor']:.4f}| "
          f"signed {summary['directional_turn_signed_motor']:+.4f}; common turn motor "
          f"{summary['common_turn_motor']:.4f}", flush=True)

graph = shuffled(con, 101, "SH101")
spec = BrainSpec.from_connectome(graph, device=dev)
gains = out["input_response"]["SH101"]["gains"]
for task in ("T0", "T1", "A"):
    cfg = grid.task_config(Config(), task)
    cfg.world.forward_gain, cfg.world.turn_gain = gains
    for tag in ("g00", "g39"):
        # the anchor has no pilot champion; the T0 champion stands in for its cost
        src = "T0" if task == "A" else task
        champ, _ = load_genome(ROOT / f"runs/exp02-screening/pilot/{src}-M0-SH101-run00-{tag}.npz", spec, None,
                               device=dev)
        t = time.perf_counter()
        ch = P.channel_dependence(cfg, iface, champ, grid.PROBE_IDS, 31_000, dev, task == "A")
        if tag == "g39":
            P.integrator_rescore(cfg, iface, champ, grid.CHECKPOINT_IDS, 31_000, dev)
            P.behaviour(cfg, iface, champ, grid.CHECKPOINT_IDS[:4], 31_000, dev)
        took = time.perf_counter() - t
        out["timing"][f"{task}-{tag}"] = took
        means = {k: round(float(np.mean(v)), 3) for k, v in ch["scores"].items()}
        print(f"{task} {tag}: {took:.0f}s {means}", flush=True)

(Path(__file__).parent / "structure_and_timing.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
