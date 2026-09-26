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

ROOT = Path(__file__).resolve().parents[1]
PILOT_SEEDS = range(101, 117)

# Two instances share this runner (D059). "03" is the experiment as it ran at 132acae and must
# not change. "03r" is its full replication: fresh graph seeds (substitutions add 100 000, so
# they stay clear of 03's), independent genomes for every graph including N2 (a genome-seed
# salt), fresh worlds, run, calibration and validation seeds, 256 routing-matched graphs, and
# fresh weight permutations. The stimulus bank is 03's pilot bank: the same probe.
INSTANCES = {
    "03": {"exp": "03-generation0", "out": "runs/exp03",
           "seed_base": {"SH": 10_000, "SH-route": 20_000, "SH-class": 30_000, "SH-mirror": 40_000,
                         "SH-recip": 50_000},
           "n": {"SH": 128, "SH-route": 128, "SH-class": 128, "SH-mirror": 128, "SH-recip": 128},
           "plateau_seeds": range(90_000, 90_004),
           "worlds": 993_000_000,  # shared by every graph and task; disjoint from 02
           "run_seed": 3, "genome_salt": "", "calibration_seed": 0, "validation_seed": 1,
           "real": ["N2", "N2-rev", "N2perm1", "N2perm2", "N2perm3"],
           "max_hours": 24.0, "min_graphs": 120, "fresh_secondary_permutation": False, "pin_connectome": False},
    "03r": {"exp": "03r-replication", "out": "runs/exp03r",
            "seed_base": {"SH": 1_010_000, "SH-route": 1_020_000, "SH-class": 1_030_000, "SH-mirror": 1_040_000,
                          "SH-recip": 1_050_000},
            "n": {"SH": 128, "SH-route": 256, "SH-class": 128, "SH-mirror": 128, "SH-recip": 128},
            "plateau_seeds": range(1_090_000, 1_090_004),
            "worlds": 994_000_000,
            "run_seed": 5, "genome_salt": "03r:", "calibration_seed": 1003, "validation_seed": 1004,
            "real": ["N2", "N2-rev", "N2perm4", "N2perm5", "N2perm6"],
            # registered after review (D060): the cap, a per-ensemble completeness floor keeping 03's
            # retained fraction, a fresh permutation for the permuted-magnitude secondary, and the
            # N2 cache hashed with the other inputs
            "max_hours": 32.0,  # 03r v3 (D061): headroom to about 150 s per graph
            "min_graphs": {"SH": 120, "SH-route": 240, "SH-class": 120, "SH-mirror": 120, "SH-recip": 120},
            "fresh_secondary_permutation": True, "pin_connectome": True},
}


def use_instance(name: str) -> None:
    """Point every path, seed and size of this module at one instance. Also the initializer of
    the build's worker processes, which re-import the module."""
    global INSTANCE, EXP, OUT, GRAPHS, MEASURES, PILOT, N_PER, N_PER_ENSEMBLE, SEED_BASE, PLATEAU_SEEDS, WORLDS
    global RUN_SEED, GENOME_SALT, CALIBRATION_SEED, VALIDATION_SEED, REAL, INPUT_FILES, MAX_HOURS, MIN_GRAPHS
    global FRESH_SECONDARY_PERMUTATION
    c = INSTANCES[name]
    INSTANCE = name
    EXP = ROOT / "experiments" / c["exp"]
    OUT = Path(c["out"])
    GRAPHS, MEASURES = OUT / "graphs", OUT / "measures"
    PILOT = ROOT / "experiments" / "03-generation0" / "pilot.json"
    N_PER = dict(c["n"])
    N_PER_ENSEMBLE = 128  # the pilot's and 03's ensemble size
    SEED_BASE, PLATEAU_SEEDS = dict(c["seed_base"]), c["plateau_seeds"]
    WORLDS = np.arange(c["worlds"], c["worlds"] + 16)
    RUN_SEED, GENOME_SALT = c["run_seed"], c["genome_salt"]
    CALIBRATION_SEED, VALIDATION_SEED = c["calibration_seed"], c["validation_seed"]
    REAL = list(c["real"])
    MAX_HOURS, MIN_GRAPHS = c["max_hours"], c["min_graphs"]
    FRESH_SECONDARY_PERMUTATION = c["fresh_secondary_permutation"]
    INPUT_FILES = {"ensembles.json": EXP / "ensembles.json", "graphs_manifest.json": EXP / "graphs_manifest.json",
                   "pilot.json": PILOT,
                   "mirror_pairs.yaml": ROOT / "configs" / "mirror_pairs.yaml",
                   "remaps.json": ROOT / "experiments" / "02-screening" / "remaps.json"}
    if c["pin_connectome"]:
        from wormwars.connectome.loader import DEFAULT_CACHE
        INPUT_FILES["cook2019_herm.npz"] = DEFAULT_CACHE


def _gseed(name: str) -> int:
    return M.genome_seed(name, GENOME_SALT)


def secondary_permutation_seed(name: str, current: int) -> int:
    """The weight-permutation seed of the permuted-magnitude secondary condition. 03 kept the
    graph's configured seed (0 for every graph but N2perm); 03r draws a fresh one per graph from
    its salted genome seed, so N2's permutation is not 03's (Astra, D060)."""
    return _gseed(name) + 2 if FRESH_SECONDARY_PERMUTATION else current


def cap_hours(requested) -> float:
    """The registered cap; a different value on the command line is refused, so the cap is never
    silently changed or extended (Fable, D060)."""
    if requested is not None and float(requested) != MAX_HOURS:
        raise ProvenanceError(f"the registered cap for {INSTANCE} is {MAX_HOURS} GPU-hours, not {requested}")
    return MAX_HOURS


# Allocation, design v3.2 (D053): precision where the primary signals need it.
GENOMES = 64                  # the secondary fitness cells and coverage
P3_GENOMES = 256              # T1-M0 and T1const-M0, the two cells of P3 (primary)
PRIMARY_PROBE_GENOMES = 2048  # P1 (input response at M0) and P4 (history)
SECONDARY_PROBE_GENOMES = 256 # every other input-response condition
FIT_CELLS = [("T1", "M0"), ("T1const", "M0"), ("T1", "R1"), ("T1", "R2"), ("T0", "M0")]
P3_CELLS = {("T1", "M0"), ("T1const", "M0")}


class ProvenanceError(RuntimeError):
    """A graph file, an input or a measurement does not match what the pre-registration fixed."""




def _sha(path: Path) -> str:
    """SHA-256 with line endings normalised to LF, so a checkout's CRLF files hash like the
    committed blobs registered in the pre-registration (Fable, D055)."""
    import hashlib
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _sha_raw(path: Path) -> str:
    """SHA-256 of the raw bytes, for binary files such as the graph .npz (D056)."""
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _input_sha(path: Path) -> str:
    """Binary inputs (.npz) are hashed raw (D056); text inputs with line endings normalised."""
    return _sha_raw(path) if path.suffix == ".npz" else _sha(path)


def provenance(device) -> dict:
    """The code commit, the registered inputs' hashes and the device, stored in every
    measurement file; the report refuses a mixture (D054)."""
    import subprocess
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "wormwars", "scripts", "configs",
                                              EXP.relative_to(ROOT).as_posix(), PILOT.relative_to(ROOT).as_posix(),
                                              "experiments/02-screening/remaps.json"],
                                             cwd=ROOT, text=True).strip())
    except Exception:  # noqa: BLE001
        commit, dirty = "unknown", True
    return {"instance": INSTANCE, "git_commit": commit, "code_dirty": dirty, "device": str(device),
            "inputs": {k: _input_sha(v) for k, v in INPUT_FILES.items()}}


def check_provenance(measurements) -> None:
    """Every measurement must share one commit, one set of input hashes and one device."""
    keys = {json.dumps(m["provenance"], sort_keys=True) for m in measurements}
    if len(keys) != 1:
        raise ProvenanceError(f"measurements come from {len(keys)} different code, input or device versions")


def check_resumable(existing, current: dict) -> None:
    """A resumed run may only add to measurements taken with the same code, inputs and device;
    any mid-run code change means re-measuring every graph (registered, D055)."""
    for m in existing:
        if m.get("provenance") != current:
            raise ProvenanceError(f"{m.get('name', '?')}: saved with other code, inputs or device; "
                                  "re-measure every graph or restore the binding commit")


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
            "autapses": int(np.diag(ch).sum()),
            "reciprocal_chem": int((ch & ch.T & ~np.eye(ch.shape[0], dtype=bool)).sum() // 2)}


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
    if (EXP / "ensembles.json").exists():  # 03's record is binding; a build never replaces one
        raise ProvenanceError(f"{EXP / 'ensembles.json'} exists: refusing to rebuild over it")
    t0 = time.perf_counter()
    # plateau check: 4 chains per ensemble at 20 and 40 passes (design v3)
    jobs = [(k, s, p, False) for k in S.KINDS for s in PLATEAU_SEEDS for p in (20, 40)]
    jobs += [(k, SEED_BASE[k] + i, 20, True) for k in S.KINDS for i in range(N_PER[k])]
    with Pool(args.workers, initializer=use_instance, initargs=(INSTANCE,)) as pool:
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
    # every graph file pinned by its raw bytes (D054, D056)
    _json(EXP / "graphs_manifest.json", {r["name"]: _sha_raw(GRAPHS / f"{r['name']}.npz") for r in graphs})
    for k in S.KINDS:
        v = validation[k]
        print(f"{k:10} plateau {'ok' if plateau[k]['passes'] else 'FAILED'}; {v['graphs']} graphs, "
              f"{v['substituted']} substituted, min acceptance {v['acceptance_min']:.2f}, "
              f"Jaccard chem median {v['jaccard_chem'][1]:.3f}, over ceiling {len(v['over_ceiling'])}")


# ----------------------------------------------------------------------------- measures

def _validated(name: str) -> bool:
    """The first 8 graphs of each ensemble get the same calibration check as N2."""
    for k, base in SEED_BASE.items():
        if name.startswith(k + "-") and name[len(k) + 1:].isdigit():
            return int(name[len(k) + 1:]) - base < 8
    return False


def _load_graph(con, name):
    if name in ("N2",) or name.startswith("N2perm"):
        return con
    if name == "N2-rev":
        return con.with_masks(con.chem.T.copy(), con.gap.copy(), "N2-rev")
    if name.startswith("pilotSH"):
        return S.build(con, "SH", seed=int(name[7:]), passes=20)[0]
    path = GRAPHS / f"{name}.npz"
    manifest = json.loads((EXP / "graphs_manifest.json").read_text(encoding="utf-8"))
    if manifest.get(name) != _sha_raw(path):  # the committed manifest pins every graph (D054); raw bytes (D056)
        raise ProvenanceError(f"{name}: graph file does not match graphs_manifest.json")
    z = np.load(path, allow_pickle=False)
    return con.with_masks(z["chem"], z["gap"], name)


def measure_graph(con, name, device, bank=None, only=None):
    """Every registered measure for one graph, per genome. `only` restricts to a subset
    (used by the pilot's first pass, which only needs the stimulus-bank replays)."""
    remap_sets = json.loads(INPUT_FILES["remaps.json"].read_text(encoding="utf-8"))["sets"]
    graph = _load_graph(con, name)
    spec = BrainSpec.from_connectome(graph, device=device)
    base0 = grid.brain_config_for_graph(grid.task_config(Config(), "T0"), name)
    out, t = {"name": name}, {}
    t0 = time.perf_counter()
    try:
        cal = calib.calibrate_in_world(graph, base0, grid.interface_for(con, "M0", remap_sets), grid.TARGET_DRIVE,
                                       n_strains=1024, seed=CALIBRATION_SEED, device=device)
    except RuntimeError as e:  # registered: excluded from every signal and counted (D055)
        return {"name": name, "calibration_failed": str(e), "seconds": {"calibration": time.perf_counter() - t0}}
    gains = (cal.forward_gain, cal.turn_gain)
    out["gains"] = list(gains)
    out["calibration"] = cal.as_dict()
    if name in ("N2",) or _validated(name):
        # independent 2048-genome check; it never replaces the 1024-genome gains (registered)
        check = base0.copy()
        check.world.forward_gain, check.world.turn_gain = gains
        out["calibration_validation"] = calib.achieved_drive(graph, check, grid.interface_for(con, "M0", remap_sets),
                                                             n_strains=2048, seed=VALIDATION_SEED, device=device).as_dict()
    t["calibration"] = time.perf_counter() - t0

    def cfg_for(task):
        base = "T1" if task == "T1const" else task
        c = grid.brain_config_for_graph(grid.task_config(Config(), base), name)
        c.world.forward_gain, c.world.turn_gain = gains
        if task == "T1const":
            c.world.food_probe = "constant"
        return c

    gen = torch.Generator(device=device).manual_seed(_gseed(name))
    big = Genome.random(spec, cfg_for("T1").brain, P3_GENOMES, generator=gen, device=device)
    genomes = big.select(list(range(GENOMES)))  # the first 64 are shared by every cell: paired
    if only is None or "fitness" in only:
        t0 = time.perf_counter()
        out["fitness"] = {f"{task}-{m}": rollout(cfg_for(task), grid.interface_for(con, m, remap_sets),
                                                 big if (task, m) in P3_CELLS else genomes,
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
        pg = torch.Generator(device=device).manual_seed(_gseed(name) + 1)
        cfg1 = cfg_for("T1")
        probe_g = Genome.random(spec, cfg1.brain, PRIMARY_PROBE_GENOMES, generator=pg, device=device)
        small_g = probe_g.select(list(range(SECONDARY_PROBE_GENOMES)))
        resp = {"M0": P.input_response(spec, cfg1, grid.interface_for(con, "M0", remap_sets), None, device,
                                       genome=probe_g, per_genome=True)}
        for m in ("R1", "R2", "MS"):
            resp[m] = P.input_response(spec, cfg1, grid.interface_for(con, m, remap_sets), None, device,
                                       genome=small_g, per_genome=True)
        no_gap = Genome(small_g.spec, small_g.cfg, small_g.w, torch.zeros_like(small_g.g), small_g.tau,
                        small_g.bias, small_g.dale_sign)
        resp["M0-gaps-off"] = P.input_response(spec, cfg1, grid.interface_for(con, "M0", remap_sets), None, device,
                                               genome=no_gap, per_genome=True)
        for mode in ("uniform", "permuted"):
            cm = cfg1.copy()
            cm.brain.init_chem_magnitude = cm.brain.init_gap_magnitude = mode
            if mode == "permuted":
                cm.brain.init_permutation_seed = secondary_permutation_seed(name, cm.brain.init_permutation_seed)
            gm = Genome.random(spec, cm.brain, SECONDARY_PROBE_GENOMES,
                               generator=torch.Generator(device=device).manual_seed(_gseed(name) + 1), device=device)
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
           # P2 (secondary) on the 64 genomes every cell shares, so its three terms are paired
           "P2": float(f["T1-M0"][:GENOMES].mean() - (f["T1-R1"].mean() + f["T1-R2"].mean()) / 2),
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
    sig = {k: [m["signals"][k] for m in full] for k in ("P1", "P2", "P3", "P4")}  # P2 secondary
    sd = {k: float(np.nanstd(v, ddof=1)) for k, v in sig.items()}
    margins = {k: {"effect": 0.5 * v, "equivalence": 0.5 * v, "between_graph_sd": v} for k, v in sd.items()}
    per_graph_seconds = float(np.mean([sum(m["seconds"].values()) for m in full]))
    _json(EXP / "pilot.json", {"bank": bank, "margins": margins, "signals": sig,
                               "per_graph_seconds": per_graph_seconds,
                               "projected_run_hours": per_graph_seconds * (5 + len(S.KINDS) * N_PER_ENSEMBLE) / 3600,
                               "seconds": time.perf_counter() - t0, "graphs": full})
    print("margins:", margins)
    print(f"per graph {per_graph_seconds:.0f}s -> projected run {per_graph_seconds * (5 + len(S.KINDS) * N_PER_ENSEMBLE) / 3600:.1f} h")


PRIMARY = ("P1", "P3", "P4")


def _ratio_se(num, den, n_boot=2000, seed=0):
    """Bootstrap SE over genomes of mean(num) / mean(den)."""
    rng = np.random.default_rng(seed)
    num, den = np.asarray(num, float), np.asarray(den, float)
    idx = rng.integers(0, len(num), (n_boot, len(num)))
    return float(np.std(num[idx].mean(1) / den[idx].mean(1), ddof=1))


def _crossed_se(d, common_world=None):
    """SE of the grand mean of a genome x world table under crossed random effects (two-way
    ANOVA without replication), after removing a world profile common to every graph: shared
    worlds cancel in rank comparisons. Returns (se, components)."""
    d = np.asarray(d, float)
    if common_world is not None:
        d = d - common_world[None, :]
    g, w = d.shape
    grand = d.mean()
    rm, cm = d.mean(1), d.mean(0)
    ms_g = w * np.sum((rm - grand) ** 2) / (g - 1)
    ms_w = g * np.sum((cm - grand) ** 2) / (w - 1)
    resid = d - rm[:, None] - cm[None, :] + grand
    ms_e = np.sum(resid ** 2) / ((g - 1) * (w - 1))
    s_g, s_w, s_e = max((ms_g - ms_e) / w, 0.0), max((ms_w - ms_e) / g, 0.0), ms_e
    return float(np.sqrt(s_g / g + s_w / w + s_e / (g * w))), {"genome": s_g, "world": s_w, "residual": s_e}


def cmd_variance(args):
    """Design v3.2 (D053): per-graph measurement SE for each primary signal on all 16 pilot
    graphs; latent between-graph SD tau (observed variance minus mean SE^2); reliability."""
    pilot = json.loads((EXP / "pilot.json").read_text(encoding="utf-8"))
    graphs = pilot["graphs"]
    d3 = [np.asarray(m["fitness"]["T1-M0"]) - np.asarray(m["fitness"]["T1const-M0"]) for m in graphs]
    common = np.mean([d.mean(0) for d in d3], axis=0)
    se = {"P1": [], "P3": [], "P4": []}
    comps = []
    for m, d in zip(graphs, d3):
        r = m["response"]["M0"]
        se["P1"].append(_ratio_se(r["directional_turn_signed_raw"], r["common_turn_raw"]))
        e3, c3 = _crossed_se(d, common)
        se["P3"].append(e3)
        comps.append(c3)
        h = m["history"]["raw_turn"]
        se["P4"].append(_ratio_se(np.abs(h["final"]), np.abs(h["steady_contrast"])))
    out = {}
    for k in PRIMARY:
        vals = np.asarray(pilot["signals"][k], float)
        obs_var = float(np.var(vals, ddof=1))
        mse = float(np.mean(np.square(se[k])))
        tau2 = max(obs_var - mse, 0.0)
        out[k] = {"observed_sd": float(np.sqrt(obs_var)), "mean_se": float(np.sqrt(mse)), "latent_sd": float(np.sqrt(tau2)),
                  "reliability": float(tau2 / (tau2 + mse)) if tau2 + mse > 0 else float("nan"),
                  "se_range": [float(min(se[k])), float(max(se[k]))]}
    out["P3_components_mean"] = {c: float(np.mean([x[c] for x in comps])) for c in ("genome", "world", "residual")}
    pilot["variance"] = out
    _json(EXP / "pilot.json", pilot)
    for k in PRIMARY:
        v = out[k]
        print(f"{k}: observed SD {v['observed_sd']:.4f}, mean SE {v['mean_se']:.4f}, latent SD {v['latent_sd']:.4f}, "
              f"reliability {v['reliability']:.2f}")
    print("P3 components (mean over pilots):", out["P3_components_mean"])


def cmd_power(args):
    """Simulated operating characteristics of the registered rule (§6), D054 version.
    Assumptions, stated: every ensemble has the pilot's SH latent SD and per-graph SE for the
    signal; values are Gaussian. N2 is measured *once*: one observation compared with all five
    ensembles. The margin and the effect interval are computed from the *observed* ensemble
    values, as the report does, with a normal approximation to the joint bootstrap. The other
    two primary signals sit at the null. Also the probability that N2, a true member (z = 0), is
    'consistent' with every ensemble."""
    pilot = json.loads((EXP / "pilot.json").read_text(encoding="utf-8"))
    rng = np.random.default_rng(0)
    n, k_ens, sims = N_PER_ENSEMBLE, len(S.KINDS), args.sims
    zs = (0.0, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0)
    par = {k: (pilot["variance"][k]["latent_sd"], pilot["variance"][k]["mean_se"]) for k in PRIMARY}

    def one(signal, z):
        tau, se = par[signal]
        ens = rng.normal(0, tau, (k_ens, n)) + rng.normal(0, se, (k_ens, n))
        # a true member (z = 0) is a random draw from the ensemble, not its mean (both, D055)
        n2 = (z * tau if z > 0 else rng.normal(0, tau)) + rng.normal(0, se)
        p = ((ens >= n2).sum(1) + 1) / (n + 1)
        mean, var = ens.mean(1), ens.var(1, ddof=1)
        margin = 0.5 * np.sqrt(np.maximum(var - se ** 2, 0.0))
        lo = (n2 - mean) - 1.645 * np.sqrt(se ** 2 + var / n)
        q05, q95 = np.quantile(ens, 0.05, axis=1), np.quantile(ens, 0.95, axis=1)
        consistent = np.all((q05 <= n2 - 1.645 * se) & (n2 + 1.645 * se <= q95))
        return p.max(), bool(np.all(lo > margin)), bool(consistent)

    table, consistent_null = {}, {}
    for s in PRIMARY:
        others = [o for o in PRIMARY if o != s]
        rows = {}
        for z in zs:
            hits = cons = 0
            for _ in range(sims):
                pmax, beyond, c = one(s, z)
                ps = sorted([pmax] + [one(o, 0.0)[0] for o in others])
                rank = ps.index(pmax)
                holm = max(min(1.0, (len(ps) - i) * ps[i]) for i in range(rank + 1))
                hits += holm <= 0.05 and beyond
                cons += c
            rows[str(z)] = hits / sims
            if z == 0.0:
                consistent_null[s] = cons / sims
        table[s] = rows
        print(s, rows, "P(consistent | member)", consistent_null[s], flush=True)
    p4 = pilot["variance"]["P4"]
    p4_mean = float(np.mean(pilot["signals"]["P4"]))
    pilot["power"] = {"sims": sims, "table": table, "consistent_if_member": consistent_null,
                      "P4_ratio_at_z": {str(z): p4_mean + z * p4["latent_sd"] for z in zs},
                      "assumptions": "one N2 draw per simulation compared with all five ensembles; SH pilot "
                                     "parameters for every ensemble; Gaussian values; normal approximation to "
                                     "the joint-bootstrap interval; other primary signals at the null"}
    _json(EXP / "pilot.json", pilot)


def interleave(by: dict, kinds) -> list[str]:
    """Graphs in order of their position within their own ensemble, as a fraction of its size,
    so any prefix holds every ensemble in proportion to its size (03r's 256 SH-route graphs
    come twice as often). With equal sizes it is plain graph-by-graph interleaving."""
    from fractions import Fraction
    keyed = [(Fraction(i, len(by[k])), j, name) for j, k in enumerate(kinds) for i, name in enumerate(by[k])]
    return [name for _, _, name in sorted(keyed)]


def run_order() -> list[str]:
    """The ensembles interleaved, so a budget stop removes graphs evenly, then N2 and its
    variants *last*, so no mid-run decision is taken with N2's numbers on disk (Fable, D054).
    N2 and its variants are exempt from the cap."""
    e = json.loads((EXP / "ensembles.json").read_text(encoding="utf-8"))
    by = {k: [g["name"] for g in e["graphs"] if g["kind"] == k] for k in S.KINDS}
    return interleave(by, S.KINDS) + REAL


def spent_hours() -> float:
    """GPU time already spent, summed over every saved measurement, so the cap is cumulative
    across restarts (Astra, D054)."""
    total = 0.0
    for path in MEASURES.glob("*.json"):
        total += sum(json.loads(path.read_text(encoding="utf-8")).get("seconds", {}).values())
    return total / 3600


def cmd_run(args):
    """Every graph, N2 last. Only after the pre-registration is committed. Stopping or resuming
    may not depend on any measured value (registered)."""
    con = load_connectome()
    bank = json.loads(PILOT.read_text(encoding="utf-8"))["bank"]
    MEASURES.mkdir(parents=True, exist_ok=True)
    prov = provenance(args.device)
    if prov["code_dirty"]:
        raise ProvenanceError("uncommitted changes in code, configs or registered inputs: commit before running")
    check_resumable([json.loads(p.read_text(encoding="utf-8")) for p in MEASURES.glob("*.json")], prov)
    cap = cap_hours(args.max_hours)  # refused before anything is measured if it differs from the registered cap
    for name in run_order():
        path = MEASURES / f"{name}.json"
        if path.exists():
            continue
        if name not in REAL and spent_hours() > cap:
            print(f"cap reached ({spent_hours():.2f} h): skipping ensemble graph {name}")
            continue
        m = measure_graph(con, name, args.device, bank=bank)
        m["provenance"] = prov
        _json(path, m)
    print(f"run finished: {len(list(MEASURES.glob('*.json')))} graphs measured, {spent_hours():.2f} h")


def accounting(planned: dict, measures: dict, counts: dict) -> dict:
    """Per ensemble: planned, measured and calibration-failed graphs, and valid and signal-invalid
    counts per signal (03r's §6, D060)."""
    out = {}
    for e, names in planned.items():
        measured = [n for n in names if n in measures]
        failed = [n for n in measured if "calibration_failed" in measures[n]]
        usable = len(measured) - len(failed)
        out[e] = {"planned": len(names), "measured": len(measured), "calibration_failed": len(failed),
                  "valid": {s: counts[s][e] for s in counts},
                  "signal_invalid": {s: usable - counts[s][e] for s in counts}}
    return out


def side_by_side(signals: dict, report03: dict, signal: str = "P4") -> dict:
    """03's and 03r's N2 value, effect interval, valid n and count at or above N2, per ensemble
    (03r's §5, descriptive; Fable, D060)."""
    def row(r):
        return {"n2": r["n2"], "effect_interval": r.get("effect_interval"), "graphs": r["graphs"],
                "at_or_above": int(sum(v >= r["n2"] for v in r["values"]))}
    old = report03["signals"][signal]
    return {e: {"03": row(old[e]) if e in old else None, "03r": row(r)} for e, r in signals[signal].items()}


def cmd_report(args):
    from wormwars.exp03 import report as R
    e = json.loads((EXP / "ensembles.json").read_text(encoding="utf-8"))
    registered = {g["name"] for g in e["graphs"]} | set(REAL)
    measures = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in MEASURES.glob("*.json")
                if p.stem in registered}  # unregistered files are never read
    check_provenance(measures.values())
    ensembles = {k: [g["name"] for g in e["graphs"] if g["kind"] == k and g["name"] in measures] for k in S.KINDS}
    out = R.build(measures, "N2", ensembles, descriptive=tuple(REAL[1:]), min_graphs=MIN_GRAPHS)
    out["provenance"] = next(iter(measures.values()))["provenance"]
    if INSTANCE == "03r":  # 03r's registered primary test (D059), written even when withheld (D060)
        planned = {k: [g["name"] for g in e["graphs"] if g["kind"] == k] for k in S.KINDS}
        out["accounting"] = accounting(planned, measures, out["counts"])
        out["accounting"]["N2"] = {"measured": "N2" in measures, "calibration_failed": "calibration_failed" in measures.get("N2", {})}
        if out["signals"]["P4"]:  # descriptive, whenever N2 is valid, withheld or not (D061)
            report03 = json.loads((ROOT / "experiments" / "03-generation0" / "report.json").read_text(encoding="utf-8"))
            out["P4_beside_03"] = side_by_side(out["signals"], report03)
        out["replication_primary"] = rp = R.replication_primary(out)
        print("03r primary (P4 alone)", rp["overall"], "p_max", rp.get("p_max"), rp.get("gates"))
    out["descriptive"] = {n: out["per_graph"][n] for n in REAL if n in out["per_graph"]}
    _json(EXP / "report.json", out)
    print("valid graphs per signal and ensemble", out["counts"])
    for s in R.PRIMARY:
        summ = out["signals"][s + "_summary"]
        print(s, summ["overall"], "p_holm", round(summ["p_holm"], 4), summ["verdicts"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["build", "pilot", "variance", "power", "run", "report"])
    ap.add_argument("--sims", type=int, default=2000)
    ap.add_argument("--max-hours", type=float, default=None, help="must equal the instance's registered cap")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--instance", choices=sorted(INSTANCES), default="03")
    args = ap.parse_args()
    use_instance(args.instance)
    if args.instance != "03" and args.command in ("pilot", "variance", "power"):
        raise SystemExit("the pilot, variance and power stages belong to 03 only; 03r reuses 03's pilot")
    {"build": cmd_build, "pilot": cmd_pilot, "variance": cmd_variance, "power": cmd_power,
     "run": cmd_run, "report": cmd_report}[args.command](args)


use_instance("03")

if __name__ == "__main__":
    main()
