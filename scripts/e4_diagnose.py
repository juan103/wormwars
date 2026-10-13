"""E4's pilot diagnostics (exploratory; D253, after both reviewers read attempt 1, D252): why one round of mutation
drops E-G's population from about 6 to about 2 visits per wey, when the same kernel on E + W2 did not in E3b-1.

    python scripts/e4_diagnose.py --device cuda      # writes experiments/E4-two-minds/diagnostics.json
    add --smoke for toy sizes (runs/e4-smoke/diagnostics.json)

**Generation 1, children only** (each condition: 32 copies bred once, 3 elites copied and 29 mutated children; 4
replicate generator seeds, the same for every condition; every condition on the same 8 mazes, the pilot's load block
40 500-40 507, maze seed 1 400 000):
- E-G unbred (the paired baseline) and **bred with every scale at 0** (a bug check: it must equal the baseline
  exactly, Astra);
- X0's mask at the inherited factor 0.25 (the pilot's), 0.10 and 0.05 (Astra);
- X0's mask restricted to one class at 0.25: w, τ, bias, module A, module B, the gated comparator → motor edges
  (Fable);
- one parameter per child on average (p_mutate = 1/56 over X0's 56 mutable parameters, at 0.25; Fable);
- **the 2 × 2 of organism and arena** (Fable): E + W2 (ungated, E3b-1's T-F mask) on E4's 6 × 6 islands, and E-G and
  E + W2 on 5 × 5 tree mazes at H = 2 400 (E3b-1's arena; ids 40 700-40 707), each unbred and at 0.25.

**The saved final X0 populations** (attempt 1, 4 × 32 strains) and E-G on the pilot's validation block (64 mazes,
40 000-40 063): has anything moved above E-G by generation 99 (Fable, Astra)?
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e3 import tuning as T  # noqa: E402
from wormwars.e4 import arms as AR  # noqa: E402
from wormwars.e4 import train as TR  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.evo.evolve import breed  # noqa: E402
from wormwars.evo.genomes import load_population  # noqa: E402
from wormwars.evo.rollout import rollout  # noqa: E402


def _load(name, file):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


X = _load("e3c_for_e4_diag", "e3c.py")
P4 = _load("e4_for_diag", "e4.py")

OUT = ROOT / "experiments" / "E4-two-minds" / "diagnostics.json"
SEED = 1_400_000
LOAD_IDS = np.arange(40_500, 40_508)
TREE_IDS = np.arange(40_700, 40_708)
VAL_IDS = np.arange(40_000, 40_064)
REPLICATES, REP_SEED = 4, 1_400_950
P, ELITES = 32, 3
CLASSES = ("w", "tau", "bias", "module_A", "module_B", "gated_edges")
SMOKE = False


def cfg_e4(**kw):
    return P4.cfg_for("shared")


def cfg_tree():
    cfg = MW.maze_config(X.base_config(), c=5, horizon=2400, colony=8, access="shared", spawns=4,
                         mu=0.01, lam=0.02, delta=0.05, d0=1.142)
    g = P4.REGISTERED["ga"]
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation = g["population"], g["elites"], g["truncation"]
    for k, v in g["mutation"].items():
        setattr(cfg.mutation, k, v)
    return cfg


def generation1(cfg, iface, base: Genome, sc, ids, dev, *, gate=None, p_mutate=None) -> dict:
    """Per replicate: 32 copies of `base` bred once with scales `sc`, played on `ids`; children's and elites' means."""
    fn = TR.gated_rollout(gate) if gate is not None else rollout
    start = Genome.cat([base.select([0])] * P)
    mcfg_p = cfg.mutation.p_mutate
    if p_mutate is not None:
        cfg.mutation.p_mutate = p_mutate
    pops = []
    try:
        for rep in range(REPLICATES):
            gen = torch.Generator(device=dev).manual_seed(REP_SEED + rep)
            pops.append(breed(EV.moved(start, dev), np.zeros(P), cfg, gen, sc) if sc is not None else EV.moved(start, dev))
    finally:
        cfg.mutation.p_mutate = mcfg_p
    res = fn(cfg, iface, Genome.cat(pops), np.asarray(ids), SEED, dev, chunk_worlds=len(pops) * P * len(ids))
    s = np.asarray(res.score).reshape(REPLICATES, P, len(ids)).mean(axis=2)  # [replicates, strains]
    kids, el = s[:, ELITES:], s[:, :ELITES]
    return {"children_mean": float(kids.mean()), "children_se": float(kids.mean(axis=1).std(ddof=1) / np.sqrt(REPLICATES)),
            "children_share_at_least_5": float((kids >= 5).mean()), "elites_mean": float(el.mean()),
            "all_mean": float(s.mean()), "per_replicate_children": np.round(kids.mean(axis=1), 4).tolist()}


def save_partial(doc: dict) -> None:
    """Written after each section, so a failure later keeps what was measured."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    reg.write_json(OUT.with_name(OUT.stem + "-partial.json"), doc, atomic=True)


def main_body(dev: str) -> dict:
    t0 = time.perf_counter()
    cfg = cfg_e4()
    con, l1 = load_connectome(), A.load_l1()
    cx = AR.context(con, l1, cfg.brain)
    org = cx["org"]
    eg = org.genome.select([0])
    zero = {k: torch.zeros_like(v) for k, v in AR.scales(cx, "x0").items()}
    out = {"inputs": {"load_ids": LOAD_IDS.tolist(), "tree_ids": TREE_IDS.tolist(), "validation_ids": VAL_IDS.tolist(),
                      "replicates": REPLICATES, "replicate_seed": REP_SEED}, "e4_6x6": {}, "arena_2x2": {}}
    e = out["e4_6x6"]
    with acct.category("probe"):
        e["eg_unbred"] = generation1(cfg, org.iface, eg, None, LOAD_IDS, dev, gate=org.gate)
        e["eg_bred_zero"] = generation1(cfg, org.iface, eg, zero, LOAD_IDS, dev, gate=org.gate)
        for f in (0.25, 0.10, 0.05):
            e[f"x0_all_{f:g}"] = generation1(cfg, org.iface, eg, AR.class_scales(cx, "all", factor=f), LOAD_IDS, dev,
                                             gate=org.gate)
        for c in CLASSES:
            e[f"x0_{c}_0.25"] = generation1(cfg, org.iface, eg, AR.class_scales(cx, c), LOAD_IDS, dev, gate=org.gate)
        n_mut = AR.mutable_count(cx, "x0")
        e["x0_one_parameter_per_child_0.25"] = {**generation1(cfg, org.iface, eg, AR.class_scales(cx, "all"), LOAD_IDS, dev,
                                                              gate=org.gate, p_mutate=1.0 / n_mut), "mutable": n_mut}
        save_partial(out)
        # the 2 x 2 of organism and arena
        seed_org = T.start_organism("seed", con, l1, cfg.brain)
        sc_seed = T.scales(seed_org.ext)
        a = out["arena_2x2"]
        a["seed_6x6_unbred"] = generation1(cfg, seed_org.iface, seed_org.genome, None, LOAD_IDS, dev)
        a["seed_6x6_0.25"] = generation1(cfg, seed_org.iface, seed_org.genome, sc_seed, LOAD_IDS, dev)
        tcfg = cfg_tree()
        a["eg_tree5_unbred"] = generation1(tcfg, org.iface, eg, None, TREE_IDS, dev, gate=org.gate)
        a["eg_tree5_0.25"] = generation1(tcfg, org.iface, eg, AR.class_scales(cx, "all"), TREE_IDS, dev, gate=org.gate)
        a["seed_tree5_unbred"] = generation1(tcfg, seed_org.iface, seed_org.genome, None, TREE_IDS, dev)
        a["seed_tree5_0.25"] = generation1(tcfg, seed_org.iface, seed_org.genome, sc_seed, TREE_IDS, dev)
        save_partial(out)
        # the saved final X0 populations against E-G on the validation block
        pops, files = [], {}
        for r in range(4):
            f = ROOT / "runs" / "e4" / "pilot" / f"final-x0-run{r:02d}.npz"
            if f.exists():
                g, _ = load_population(f, org.genome.spec, cfg.brain)
                pops.append(g)
                files[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
        if pops:
            batch = EV.moved(Genome.cat([eg, *pops]), dev)  # the loaded populations are on the CPU
            res = TR.gated_rollout(org.gate)(cfg, org.iface, batch, VAL_IDS, SEED, dev,
                                             chunk_worlds=batch.n_strains * len(VAL_IDS))
            v = np.asarray(res.score)  # [1 + 128, 64]
            d = v[1:] - v[0]  # each strain's per-maze difference from E-G, paired by maze
            se = d.std(axis=1, ddof=1) / np.sqrt(len(VAL_IDS))
            out["final_x0_validation"] = {
                "files_sha256": files, "eg_mean": float(v[0].mean()),
                "per_run": [{"run": r, "means": np.round(v[1 + 32 * r:1 + 32 * (r + 1)].mean(axis=1), 4).tolist(),
                             "best_mean": float(v[1 + 32 * r:1 + 32 * (r + 1)].mean(axis=1).max()),
                             "share_above_eg": float((d[32 * r:32 * (r + 1)].mean(axis=1) > 0).mean()),
                             "share_above_eg_by_2se": float((d[32 * r:32 * (r + 1)].mean(axis=1) > 2 * se[32 * r:32 * (r + 1)]).mean())}
                            for r in range(len(pops))],
                "note": "the best of 32 on 64 mazes is selected on the same mazes: optimistic"}
    out["seconds"] = time.perf_counter() - t0
    return out


def main():
    global LOAD_IDS, TREE_IDS, VAL_IDS, REPLICATES, OUT
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        OUT = ROOT / "runs" / "e4-smoke" / "diagnostics.json"
        LOAD_IDS, TREE_IDS, VAL_IDS, REPLICATES = LOAD_IDS[:1], TREE_IDS[:1], VAL_IDS[:1], 2
        P4.REGISTERED["H"] = 40
        P4.configure()
    prov = reg.provenance(P4.GUARDED + ["scripts/e4_diagnose.py"])
    doc = {"provenance": prov, "device": args.device, **main_body(args.device)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    reg.write_json(OUT, doc, atomic=True)
    e = doc["e4_6x6"]
    print({k: round(v["children_mean"], 3) for k, v in e.items()})
    print({k: round(v["children_mean"], 3) for k, v in doc["arena_2x2"].items()})


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    run_script(main, out_default=str(ROOT / "runs" / ("e4-smoke" if smoke else "e4-diag")), default="measure",
               name="e4-diagnose")
