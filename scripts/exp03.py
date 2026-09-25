"""Experiment 03: generation-0 structure and task specificity (design v3,
experiments/03-generation0/DESIGN.md).

    python scripts/exp03.py build      # the four ensembles, plateau checks, validation (structure only)
    python scripts/exp03.py pilot      # pilot shuffles SH101-SH116 only: bank, margins, precision, timing
    python scripts/exp03.py run        # every graph, N2 included: only after the pre-registration
    python scripts/exp03.py report     # the registered verdicts

Graphs carry permuted anatomical weights, so they live under runs/exp03/ (git-ignored); only
validation statistics and measures are written to experiments/03-generation0/.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wormwars import calibration as calib  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.evo import rollout  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.exp02 import probes as P  # noqa: E402
from wormwars.exp03 import measures as M  # noqa: E402
from wormwars.exp03 import samplers as S  # noqa: E402

EXP = Path(__file__).resolve().parents[1] / "experiments" / "03-generation0"
OUT = Path("runs/exp03")
GRAPHS = OUT / "graphs"
N_PER_ENSEMBLE = 128
SEED_BASE = {"SH": 10_000, "SH-route": 20_000, "SH-class": 30_000, "SH-mirror": 40_000}
PILOT_SEEDS = range(101, 117)
PLATEAU_SEEDS = range(90_000, 90_004)
WORLDS = np.arange(993_000_000, 993_000_016)  # shared by every graph and task; disjoint from 02
RUN_SEED = 3
GENOMES = 64
PROBE_GENOMES = 512
FIT_CELLS = [("T0", m) for m in ("M0", "R1", "R2")] + [("T1", m) for m in ("M0", "R1", "R2")] + [("T1const", "M0")]


def _json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1), encoding="utf-8")


# ----------------------------------------------------------------------------- build

def _graph_stats(con, g, info):
    m = S.mirror_map(con)
    from wormwars.interface import load_interface
    iface = load_interface(con)
    mapped = sorted(int(i) for i in iface.mapped_neurons)
    ch, n2c = g.chem > 0, con.chem > 0
    rows = np.zeros_like(ch)
    rows[mapped, :] = rows[:, mapped] = True
    return {"jaccard_chem": S.jaccard(ch, n2c), "jaccard_gap": S.jaccard(g.gap > 0, con.gap > 0),
            "interface_turnover_chem": 1 - S.jaccard(ch & rows, n2c & rows),
            "acceptance_chem": info["chem"]["accepted"] / info["chem"]["attempted"],
            "acceptance_gap": info["gap"]["accepted"] / info["gap"]["attempted"],
            "mirror_chem": S.mirror_share(ch, m), "mirror_gap": S.mirror_share(g.gap > 0, m),
            "autapses": int(np.diag(ch).sum()), "reciprocal_chem": int((ch & ch.T).sum() // 2)}


def _build_one(args):
    kind, seed, passes, save = args
    con = load_connectome()
    tries = []
    while True:
        try:
            g, info = S.build(con, kind, seed=seed, passes=passes)
            break
        except S.SamplerFailure as e:  # disclosed substitution: the next seed
            tries.append({"seed": seed, "error": str(e)})
            seed += 100_000
    stats = _graph_stats(con, g, info)
    name = f"{kind}-{seed}"
    if save:
        GRAPHS.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(GRAPHS / f"{name}.npz", chem=g.chem, gap=g.gap)
    return {"kind": kind, "name": name, "seed": seed, "passes": passes, "failed_seeds": tries, **stats,
            "counts": info}


def cmd_build(args):
    t0 = time.perf_counter()
    # plateau check: 4 chains per ensemble at 20 and 40 passes (design v3)
    jobs = [(k, s, p, False) for k in S.KINDS for s in PLATEAU_SEEDS for p in (20, 40)]
    jobs += [(k, SEED_BASE[k] + i, 20, True) for k in S.KINDS for i in range(N_PER_ENSEMBLE)]
    with Pool(args.workers) as pool:
        res = pool.map(_build_one, jobs, chunksize=1)
    plateau = {}
    for k in S.KINDS:
        r20 = [r for r in res[:len(S.KINDS) * 8] if r["kind"] == k and r["passes"] == 20]
        r40 = [r for r in res[:len(S.KINDS) * 8] if r["kind"] == k and r["passes"] == 40]
        plateau[k] = {m: {"at20": float(np.mean([r[m] for r in r20])), "at40": float(np.mean([r[m] for r in r40]))}
                      for m in ("jaccard_chem", "jaccard_gap")}
        plateau[k]["passes"] = all(abs(v["at40"] - v["at20"]) < 0.01 for v in plateau[k].values() if isinstance(v, dict))
    graphs = res[len(S.KINDS) * 8:]
    validation = {}
    for k in S.KINDS:
        gs = [r for r in graphs if r["kind"] == k]
        ceiling = plateau[k]["jaccard_chem"]["at20"] + 0.02
        validation[k] = {
            "graphs": len(gs), "substituted": sum(1 for r in gs if r["failed_seeds"]),
            "acceptance_min": min(min(r["acceptance_chem"], r["acceptance_gap"]) for r in gs),
            "jaccard_ceiling_chem": ceiling,
            "over_ceiling": [r["name"] for r in gs if r["jaccard_chem"] > ceiling],
            **{m: [float(np.min([r[m] for r in gs])), float(np.median([r[m] for r in gs])), float(np.max([r[m] for r in gs]))]
               for m in ("jaccard_chem", "jaccard_gap", "interface_turnover_chem", "mirror_chem", "mirror_gap",
                         "autapses", "reciprocal_chem")}}
    con = load_connectome()
    n2 = _graph_stats(con, con, {"chem": {"accepted": 1, "attempted": 1}, "gap": {"accepted": 1, "attempted": 1}})
    _json(EXP / "ensembles.json", {"plateau": plateau, "validation": validation, "N2": n2, "graphs": graphs,
                                   "seconds": time.perf_counter() - t0})
    for k in S.KINDS:
        v = validation[k]
        print(f"{k:10} plateau {'ok' if plateau[k]['passes'] else 'FAILED'}; {v['graphs']} graphs, "
              f"{v['substituted']} substituted, min acceptance {v['acceptance_min']:.2f}, "
              f"Jaccard chem median {v['jaccard_chem'][1]:.3f}, over ceiling {len(v['over_ceiling'])}")


# ----------------------------------------------------------------------------- measures

def _load_graph(con, name):
    if name in ("N2",) or name.startswith("N2perm"):
        return con
    if name == "N2-rev":
        return con.with_masks(con.chem.T.copy(), con.gap.copy(), "N2-rev")
    if name.startswith("pilotSH"):
        return S.build(con, "SH", seed=int(name[7:]), passes=20)[0]
    z = np.load(GRAPHS / f"{name}.npz")
    return con.with_masks(z["chem"], z["gap"], name)


def _genome_seed(name: str) -> int:
    return int.from_bytes(name.encode(), "little") % (2 ** 31)


def measure_graph(con, name, device, bank=None, only=None):
    """Every registered measure for one graph, per genome. `only` restricts to a subset
    (used by the pilot's first pass, which only needs the stimulus-bank replays)."""
    remap_sets = json.loads((EXP.parent / "02-screening" / "remaps.json").read_text(encoding="utf-8"))["sets"]
    graph = _load_graph(con, name)
    spec = BrainSpec.from_connectome(graph, device=device)
    base0 = grid.brain_config_for_graph(grid.task_config(Config(), "T0"), name)
    out, t = {"name": name}, {}
    t0 = time.perf_counter()
    cal = calib.calibrate_in_world(graph, base0, grid.interface_for(con, "M0", remap_sets), grid.TARGET_DRIVE,
                                   n_strains=1024, device=device)
    gains = (cal.forward_gain, cal.turn_gain)
    out["gains"] = list(gains)
    t["calibration"] = time.perf_counter() - t0

    def cfg_for(task):
        base = "T1" if task == "T1const" else task
        c = grid.brain_config_for_graph(grid.task_config(Config(), base), name)
        c.world.forward_gain, c.world.turn_gain = gains
        if task == "T1const":
            c.world.food_probe = "constant"
        return c

    gen = torch.Generator(device=device).manual_seed(_genome_seed(name))
    genomes = Genome.random(spec, cfg_for("T1").brain, GENOMES, generator=gen, device=device)
    if only is None or "fitness" in only:
        t0 = time.perf_counter()
        out["fitness"] = {f"{task}-{m}": rollout(cfg_for(task), grid.interface_for(con, m, remap_sets), genomes,
                                                 WORLDS, RUN_SEED, device, chunk_worlds=4096).score.tolist()
                          for task, m in FIT_CELLS}
        t["fitness"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        cc = M.task_c_config(Config())
        cc = grid.brain_config_for_graph(cc, name)
        cc.world.forward_gain, cc.world.turn_gain = gains
        cov = M.coverage(cc, grid.interface_for(con, "M0", remap_sets), genomes, WORLDS, RUN_SEED, device, 4096)
        out["coverage"] = cov["cells"].tolist()
        out["coverage_checks"] = {"food_left": cov["food_left"], "deaths": cov["deaths"]}
        t["coverage"] = time.perf_counter() - t0
    if only is None or "response" in only:
        t0 = time.perf_counter()
        pg = torch.Generator(device=device).manual_seed(_genome_seed(name) + 1)
        cfg1 = cfg_for("T1")
        probe_g = Genome.random(spec, cfg1.brain, PROBE_GENOMES, generator=pg, device=device)
        resp = {}
        for m in ("M0", "R1", "R2", "MS"):
            resp[m] = P.input_response(spec, cfg1, grid.interface_for(con, m, remap_sets), None, device,
                                       genome=probe_g, per_genome=True)
        no_gap = Genome(probe_g.spec, probe_g.cfg, probe_g.w, torch.zeros_like(probe_g.g), probe_g.tau,
                        probe_g.bias, probe_g.dale_sign)
        resp["M0-gaps-off"] = P.input_response(spec, cfg1, grid.interface_for(con, "M0", remap_sets), None, device,
                                               genome=no_gap, per_genome=True)
        for mode in ("uniform", "permuted"):
            cm = cfg1.copy()
            cm.brain.init_chem_magnitude = cm.brain.init_gap_magnitude = mode
            gm = Genome.random(spec, cm.brain, PROBE_GENOMES,
                               generator=torch.Generator(device=device).manual_seed(_genome_seed(name) + 1), device=device)
            resp[f"M0-{mode}"] = P.input_response(spec, cm, grid.interface_for(con, "M0", remap_sets), None, device,
                                                  genome=gm, per_genome=True)
        keep = ("directional_turn_signed_raw", "directional_turn_raw", "common_turn_raw", "common_forward_raw")
        out["response"] = {m: {k: np.asarray(r[k]).mean(0).tolist() for k in keep} for m, r in resp.items()}
        t["response"] = time.perf_counter() - t0
        if bank is not None:
            t0 = time.perf_counter()
            h = M.history(probe_g, cfg1, grid.interface_for(con, "M0", remap_sets), bank)
            out["history"] = {k: {kk: vv.tolist() for kk, vv in v.items()} for k, v in h.items() if k.startswith("raw")}
            t["history"] = time.perf_counter() - t0
    if only is not None and "bank" in only:
        out["bank"] = _typical_signals(cfg_for("T1"), grid.interface_for(con, "M0", remap_sets), genomes, device)
    out["seconds"] = t
    return out


def _typical_signals(cfg, iface, genomes, device):
    """Mean sensed signals over ticks 20-60 of generation-0 replays (alive weys), for the bank."""
    from wormwars.brain import Brain
    from wormwars.world import World
    sub = genomes.select(list(range(16)))
    n = 4
    strain_of = torch.arange(16, device=device).repeat_interleave(n).reshape(-1, 1)
    world = World(cfg, iface, Brain(sub), strain_of, run_seed=RUN_SEED, world_ids=np.tile(WORLDS[:n], 16), device=device)
    sums, count = {}, 0
    for tick in range(60):
        world.tick()
        if tick >= 20 and bool(world.alive.any()):
            for k, v in world.last_signals.items():
                sums[k] = sums.get(k, 0.0) + float(v[world.alive].mean())
            count += 1
    return {k: v / max(count, 1) for k, v in sums.items()}


# ----------------------------------------------------------------------------- signals

def signals(m) -> dict:
    """The four primary signals for one graph's measures (design v3)."""
    f = {k: np.asarray(v) for k, v in m["fitness"].items()}
    r = m["response"]["M0"]
    out = {"P1": float(np.mean(r["directional_turn_signed_raw"]) / max(np.mean(r["common_turn_raw"]), 1e-12))
           if np.mean(r["common_turn_raw"]) >= 1e-4 else float("nan"),
           "P2": float(f["T1-M0"].mean() - (f["T1-R1"].mean() + f["T1-R2"].mean()) / 2),
           "P3": float(f["T1-M0"].mean() - f["T1const-M0"].mean())}
    if "history" in m:
        num = np.abs(np.asarray(m["history"]["raw_turn"]["final"])).mean()
        den = np.abs(np.asarray(m["history"]["raw_turn"]["steady_contrast"])).mean()
        out["P4"] = float(num / den) if den >= 1e-4 else float("nan")
    return out


# ----------------------------------------------------------------------------- pilot

def cmd_pilot(args):
    """Pilot shuffles only (SH101-SH116), never N2. First the stimulus bank, then everything."""
    con = load_connectome()
    t0 = time.perf_counter()
    names = [f"pilotSH{s}" for s in PILOT_SEEDS]
    first = [measure_graph(con, n, args.device, only={"bank"}) for n in names]
    keys = first[0]["bank"].keys()
    bank = {k: float(np.median([f["bank"][k] for f in first])) for k in keys}
    print("stimulus bank (median over pilot shuffles):", {k: round(v, 4) for k, v in bank.items() if k.startswith("food")}, flush=True)
    full = []
    for n in names:
        m = measure_graph(con, n, args.device, bank=bank)
        m["signals"] = signals(m)
        full.append(m)
        print(n, {k: round(v, 5) for k, v in m["signals"].items()}, {k: round(v) for k, v in m["seconds"].items()}, flush=True)
    sig = {k: [m["signals"][k] for m in full] for k in ("P1", "P2", "P3", "P4")}
    sd = {k: float(np.nanstd(v, ddof=1)) for k, v in sig.items()}
    margins = {k: {"effect": 0.5 * v, "equivalence": 0.5 * v, "between_graph_sd": v} for k, v in sd.items()}
    per_graph_seconds = float(np.mean([sum(m["seconds"].values()) for m in full]))
    _json(EXP / "pilot.json", {"bank": bank, "margins": margins, "signals": sig,
                               "per_graph_seconds": per_graph_seconds,
                               "projected_run_hours": per_graph_seconds * (5 + 4 * N_PER_ENSEMBLE) / 3600,
                               "seconds": time.perf_counter() - t0, "graphs": full})
    print("margins:", margins)
    print(f"per graph {per_graph_seconds:.0f}s -> projected run {per_graph_seconds * (5 + 4 * N_PER_ENSEMBLE) / 3600:.1f} h")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["build", "pilot"])
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    {"build": cmd_build, "pilot": cmd_pilot}[args.command](args)


if __name__ == "__main__":
    main()
