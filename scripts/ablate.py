"""Ablation, convergence and tactics report for evolved champions.

    python scripts/ablate.py --champions runs/m4/champion-run*.npz --out runs/ablation

Two sections, labelled, because they mean different things:

  IMPLEMENTATION CHECKS  -- silencing neurons the sensor/motor map names. The deficits follow by
                            construction; they verify the interface is wired as configured and say
                            nothing about biology.
  EMERGENT TESTS         -- silencing interneurons the map does not name, each against matched
                            random ablations of the same size, class and degree.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys as _sys
from pathlib import Path as _Path

import numpy as np
import torch

_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from wormwars.analysis.ablation import (
    AblationSpec,
    emergent_checks,
    evaluate_ablations,
    implementation_checks,
    matched_random,
    profile_correlation,
    sensitivity,
)
from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo import SeedPool, load_genome
from wormwars.evo.genomes import apply_world_meta, brain_config_for
from wormwars.interface import load_interface


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--champions", nargs="+", default=["runs/m4/champion-run*.npz"])
    ap.add_argument("--controls", type=int, default=12, help="matched random ablations per target")
    ap.add_argument("--worlds", type=int, default=16)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--out", default="runs/ablation")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    paths = sorted({p for pat in args.champions for p in glob.glob(pat)})
    if not paths:
        raise SystemExit(f"no champions matched {args.champions}")

    cfg = Config()
    cfg.world.max_ticks = args.ticks
    con = load_connectome()
    iface = load_interface(con)
    out = _Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    impl = implementation_checks(con, iface)
    emergent = emergent_checks()
    rng = np.random.default_rng(0)
    controls = {e.name: matched_random(con, e, args.controls, rng) for e in emergent if e.neurons}

    specs: list[AblationSpec] = [AblationSpec("baseline", [], kind="none")]
    specs += impl + emergent
    for group in controls.values():
        specs += group

    print(f"{len(paths)} champions x {len(specs)} ablations x {args.worlds} held-out worlds")
    records = {}
    profiles = {}
    for path in paths:
        graph = json.loads(_load_meta(path))["graph"]
        spec = BrainSpec.from_connectome(_graph_for(con, graph), device=args.device)
        # each genome runs in the synapse direction it evolved with (DECISIONS.md D031)
        genome, meta = load_genome(
            path, spec, brain_config_for(path, cfg.brain), device=args.device
        )
        # Motor gains are calibrated per graph. Replaying an SH or RD champion at N2's gain is not
        # the strain that was evolved, and its scores are meaningless.
        gcfg, had = apply_world_meta(cfg, meta)
        if not had:
            # Older genomes predate the world metadata, but the run bundle beside them recorded the
            # calibration that was actually used. Prefer that over guessing.
            gains = _gains_from_bundle(_Path(path).parent, graph)
            if gains:
                gcfg = cfg.copy()
                gcfg.world.forward_gain, gcfg.world.turn_gain = gains
                print(f"  (gains {gains[0]:.3f}/{gains[1]:.3f} recovered from the run bundle)")
            else:
                print(f"  !! {path} was saved without its world settings and no bundle records "
                      f"them; running at the default gains, which may not be the ones it "
                      f"evolved under")
        pool = SeedPool(gcfg, meta.get("run_seed", 0))
        ids = pool.holdout[: args.worlds]
        scores = evaluate_ablations(
            gcfg, iface, con, genome, specs, ids, run_seed=meta.get("run_seed", 0),
            device=args.device,
        )
        baseline = float(scores[0])
        sens = sensitivity(scores, baseline)
        records[path] = {
            "graph": graph,
            "nickname": meta.get("nickname"),
            "baseline": baseline,
            "sensitivity": {s.name: float(x) for s, x in zip(specs, sens)},
        }
        profiles[path] = sens
        print(f"\n=== {path}  ({meta.get('nickname')}, {graph}) baseline {baseline:.3f} ===")
        _section("IMPLEMENTATION CHECKS (true by construction; not evidence about biology)",
                 impl, specs, sens)
        _section("EMERGENT TESTS (vs matched random ablations)", emergent, specs, sens,
                 controls=controls, all_specs=specs, sens_all=sens)

    # --- convergence: do champions of the same graph rely on the same neurons? ---
    print("\n=== CONVERGENCE: correlation between ablation-sensitivity profiles ===")
    keys = list(profiles)
    conv = {}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            r = profile_correlation(profiles[keys[i]], profiles[keys[j]])
            conv[f"{_short(keys[i])} vs {_short(keys[j])}"] = r
            print(f"  {_short(keys[i]):<28} vs {_short(keys[j]):<28} r = {r:+.3f}")
    if conv:
        vals = [v for v in conv.values() if np.isfinite(v)]
        print(f"  mean r = {np.mean(vals):+.3f} over {len(vals)} pairs")

    (out / "ablation.json").write_text(
        json.dumps({"records": records, "convergence": conv}, indent=2), encoding="utf-8"
    )
    print(f"\nwrote {out / 'ablation.json'}")
    print(
        "\nInterpret with care. These weys have no neuromodulation, no plasticity and no "
        "biophysics, and the task is a game. A result that resembles a real worm experiment is a "
        "resemblance, not a replication."
    )


def _section(title, group, specs, sens, controls=None, all_specs=None, sens_all=None):
    print(f"  -- {title}")
    index = {s.name: i for i, s in enumerate(specs)}
    for g in group:
        s = sens[index[g.name]]
        line = f"     {g.name:<38} sensitivity {s:+.3f}"
        if controls and g.name in controls:
            cs = np.array([sens_all[index[c.name]] for c in controls[g.name]])
            z = (s - cs.mean()) / cs.std() if cs.std() > 1e-9 else float("nan")
            pct = float((cs < s).mean())
            line += (
                f"   matched random {cs.mean():+.3f} +- {cs.std():.3f}"
                f"   z {z:+.2f}   above {pct:.0%} of controls"
            )
        print(line)


def _short(path: str) -> str:
    return _Path(path).stem


def _gains_from_bundle(directory: _Path, graph: str):
    bundle = directory / "bundle.json"
    if not bundle.exists():
        return None
    try:
        info = json.loads(bundle.read_text(encoding="utf-8"))
        cal = (info.get("graphs") or {}).get(graph, {}).get("calibration")
        if cal:
            return float(cal["forward_gain"]), float(cal["turn_gain"])
        world = (info.get("config") or {}).get("world") or {}
        if "forward_gain" in world:
            return float(world["forward_gain"]), float(world["turn_gain"])
    except (ValueError, KeyError, TypeError):
        return None
    return None


def _load_meta(path):
    d = np.load(path, allow_pickle=False)
    return str(d["meta"])


def _graph_for(con, label):
    if label == "N2":
        return con
    from wormwars.connectome.graphs import random_graph, shuffled

    kind, num = label[:2], int(label[2:])
    return shuffled(con, num, label) if kind == "SH" else random_graph(con, num, label)


if __name__ == "__main__":
    main()
