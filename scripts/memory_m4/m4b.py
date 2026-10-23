"""M4b (docs/memory/M4B-PLAN.md): the switch, from its roots, on every separate-states genome of M2's census.
Q2, location against graph identity: per genome, the chemical edges among the 30 neurons where its two stable roots
differ most ("own"), cut for ticks 1 to 30, against 5 sets of as many edges with both ends outside those neurons,
stratified on anatomical weight. Q1, the dissection of N2's core: C3's internal edges by neuron and by read-out
partition, on N2's separate-states genomes. Each history is assigned by M2's reaching rule (float64) after the cut and
300 ticks of the intact network (M4a's Part 2). Writes runs/memory-m4b/<panel>.json; readings by m4b_read.py.
Usage: python scripts/memory_m4/m4b.py"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
import m4a  # noqa: E402

census, P, c, E = m4a.census, m4a.P, m4a.c, m4a.E
from wormwars import accounting as acct  # noqa: E402

torch.set_grad_enabled(False)
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("MEMORY_M4B_OUT", ROOT / "runs" / "memory-m4b"))
OUT.mkdir(parents=True, exist_ok=True)
CENSUS = ROOT / "runs" / "memory-m2-census"
TOP, N_CTRL, SEED_CTRL = 30, 5, 20261111
CUT, TICKS = (1, 30), 330
MAX_GENOMES = int(os.environ.get("MEMORY_M4B_MAX", 10**9))  # a smoke run takes the first few per panel
if MAX_GENOMES < 10**9 and OUT.resolve() == (ROOT / "runs" / "memory-m4b").resolve():  # a smoke must not land where the real run reads
    raise SystemExit("a smoke run (MEMORY_M4B_MAX) needs MEMORY_M4B_OUT set to another folder (Fable)")


def out_edges(spec, nodes):
    """The off-diagonal chemical edges from a neuron in nodes to one outside them (Fable, round 1: they share the own
    cut's asymmetry, since their presynaptic neurons differ between the histories)."""
    i, j = spec.chem_i.numpy(), spec.chem_j.numpy()
    inn = np.zeros(spec.n, bool)
    inn[list(nodes)] = True
    return np.where(inn[i] & ~inn[j] & (i != j))[0]


def set_edges(spec, nodes):
    """The off-diagonal chemical edges with both ends in nodes, and those with both ends outside."""
    i, j = spec.chem_i.numpy(), spec.chem_j.numpy()
    inn = np.zeros(spec.n, bool)
    inn[list(nodes)] = True
    off = i != j
    return np.where(inn[i] & inn[j] & off)[0], np.where(~inn[i] & ~inn[j] & off)[0]


def top_difference(roots_one, k=TOP):
    """The k neurons where a genome's two stable roots differ most (|v1* - v2*|), ties broken by index."""
    d = np.abs(roots_one[0] - roots_one[1])
    return np.lexsort((np.arange(len(d)), -d))[:k]


def masks_from(g, edge_lists):
    """A [S, E_chem] mask from one edge list per strain."""
    m = np.zeros(tuple(g.w.shape), bool)
    for s_, e in enumerate(edge_lists):
        m[s_, e] = True
    return m


def outcomes(g, roots, cur, mask):
    """Every genome's outcome after the cut on mask for ticks CUT and the intact network to tick TICKS (float64), by
    M2's reaching rule against its two stored roots (m4a.assign). mask None: the intact arm."""
    b_int = E.brain64(g)
    b_cut = None if mask is None else E.brain64(m4a.cut(g, mask))
    v = roots.clone()
    for t in range(1, TICKS + 1):
        v = (b_cut if (b_cut is not None and CUT[0] <= t <= CUT[1]) else b_int).step(v, cur)
    res, found = P.locate_and_reach(b_int, v, cur, compact=True)
    return [m4a.assign(roots[s_].numpy(), found[s_].numpy(), [str(res["reach"][s_, h]) for h in range(2)])
            for s_ in range(g.n_strains)]


def run_panel(name, gname, seed, role):
    f = OUT / f"{name}.json"
    if f.exists():
        return
    cen = json.load(open(CENSUS / f"{name}.json"))
    ids = [gr["genome"] for gr in cen["genomes"] if gr["class"].startswith("separate states")][:MAX_GENOMES]
    if not ids:
        return
    t0 = time.time()
    z = np.load(CENSUS / f"{name}.npz", allow_pickle=False)
    row = {int(i): r for r, i in enumerate(z["idx"])}
    roots = torch.from_numpy(np.stack([z["roots"][row[i]] for i in ids])).double()
    g = c.S.genomes(census.graph_of(gname), m4a.N_PANEL, seed)[0].select(ids)
    cfg = c.S.genomes(census.graph_of(gname), 1, seed)[1]
    food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
    cur = c.at(cfg, g.spec.n, len(ids), [food, food]).double()
    key = g.spec.chem_anat.numpy()
    c3 = m4a.core()
    own, ctrl, outc, info = [], [[] for _ in range(N_CTRL)], [[] for _ in range(N_CTRL)], []
    for s_, gid in enumerate(ids):
        nodes = top_difference(roots[s_].numpy())
        inside, outside = set_edges(g.spec, nodes)
        outgoing = out_edges(g.spec, nodes)
        empty = [np.zeros(0, int)] * N_CTRL
        draws = m4a.stratified_draws(g.spec, inside, outside, N_CTRL, SEED_CTRL + gid, key=key) if len(inside) else empty
        n_out = min(len(inside), len(outgoing))  # as many outgoing edges as the own set, if there are enough
        if n_out == 0:
            drawo = empty
        elif n_out == len(inside):  # weight-stratified like the exterior controls
            drawo = m4a.stratified_draws(g.spec, inside, outgoing, N_CTRL, SEED_CTRL + 100000 + gid, key=key)
        else:  # fewer outgoing edges than own edges: all of them, every set (recorded as out_edges < own_edges)
            drawo = [outgoing.copy() for _ in range(N_CTRL)]
        own.append(inside)
        for d in range(N_CTRL):
            ctrl[d].append(draws[d])
            outc[d].append(drawo[d])
        d2 = (roots[s_, 0] - roots[s_, 1]).numpy() ** 2
        info.append({"genome": gid, "own_edges": int(len(inside)), "own_neurons": [c.NAMES[k] for k in nodes],
                     "overlap_C3": int(len(set(nodes.tolist()) & set(c3))),
                     "location_own": float(d2[nodes].sum() / d2.sum()), "location_C3": float(d2[c3].sum() / d2.sum()),
                     "sum_anat_own": float(key[inside].sum()),
                     "sum_anat_ctrl": [float(key[ctrl[d][-1]].sum()) for d in range(N_CTRL)],
                     "outgoing_available": int(len(outgoing)), "out_edges": int(n_out),
                     "sum_anat_out": [float(key[outc[d][-1]].sum()) for d in range(N_CTRL)]})
    arms = {"intact": None, "own": masks_from(g, own)}
    for d in range(N_CTRL):
        arms[f"ctrl{d}"] = masks_from(g, ctrl[d])
        arms[f"out{d}"] = masks_from(g, outc[d])
    if role == "N2":  # Q1: the dissection of C3, a partition by the read-out and each neuron's own C3 edges
        internal, _ = m4a.edge_sets(g.spec, c3)
        i, j = g.spec.chem_i.numpy(), g.spec.chem_j.numpy()
        ro = np.zeros(g.spec.n, bool)
        ro[c.READOUT] = True
        arms["C3"] = m4a.common_mask(g, internal)
        arms["C3:read-out among themselves"] = m4a.common_mask(g, internal[ro[i[internal]] & ro[j[internal]]])
        arms["C3:read-out with the rest of C3"] = m4a.common_mask(g, internal[ro[i[internal]] ^ ro[j[internal]]])
        arms["C3:without the read-out"] = m4a.common_mask(g, internal[~ro[i[internal]] & ~ro[j[internal]]])
        for k in c3:
            arms[f"C3:{c.NAMES[k]}"] = m4a.common_mask(g, internal[(i[internal] == k) | (j[internal] == k)])
    out = {"panel": name, "graph": gname, "role": role, "genomes": ids, "info": info, "arms": {}}
    for arm, mask in arms.items():
        out["arms"][arm] = outcomes(g, roots, cur, mask)
    out["arm_edges"] = {a: (None if m is None else int(m.sum(1).max())) for a, m in arms.items()}
    out["intact_not_kept"] = [i_ for i_, o in zip(ids, out["arms"]["intact"]) if o != "both kept"]
    if role == "N2" and MAX_GENOMES >= 10**9:  # Fable: the same genomes, roots and brain as M4a's Part 2
        m4a_p2 = json.load(open(ROOT / "runs" / "memory-m4a" / f"part2__{name}.json"))
        out["matches_m4a_part2"] = (m4a_p2["genomes"] == ids and m4a_p2["arms"]["intact"] == out["arms"]["intact"]
                                    and m4a_p2["arms"]["C3"] == out["arms"]["C3"])
    out["seconds"] = round(time.time() - t0, 1)
    json.dump(out, open(f, "w"))
    print(f"{name}: {len(ids)} genomes, {len(arms)} arms, {out['seconds']} s, intact not kept {out['intact_not_kept']}",
          flush=True)
    m4a.part2_gate({"panel": name, "genomes": ids, "arms": {"intact": out["arms"]["intact"]}})
    if out.get("matches_m4a_part2") is False:
        raise SystemExit(f"{name}: the intact or C3 arm differs from M4a's Part 2: stop for investigation")


def expected_arms(role):
    """The complete arm set of a panel (Astra, round 2: validation checks all of it)."""
    arms = ["intact", "own"] + [f"ctrl{d}" for d in range(N_CTRL)] + [f"out{d}" for d in range(N_CTRL)]
    if role == "N2":
        arms += ["C3", "C3:read-out among themselves", "C3:read-out with the rest of C3", "C3:without the read-out"]
        arms += [f"C3:{c.NAMES[k]}" for k in m4a.core()]
    return arms


def expected():
    """The panels with separate-states genomes, and their genome ids, from the census."""
    out = {}
    for name, gname, seed, role in census.panels():
        ids = [gr["genome"] for gr in json.load(open(CENSUS / f"{name}.json"))["genomes"]
               if gr["class"].startswith("separate states")][:MAX_GENOMES]
        if ids:
            out[name] = (gname, seed, role, ids)
    return out


def validate(p, ids, name=None, role=None, gname=None):
    """A saved panel is usable only if it is the expected panel and role, holds exactly the census's genomes, has every
    expected arm complete and its info aligned, the intact arm kept both roots in every genome, and on N2 its intact
    and C3 outcomes equal M4a's Part 2, compared directly (Astra, rounds 1 and 2)."""
    if name is not None and p.get("panel") != name:
        raise SystemExit(f"{name}: the record is for {p.get('panel')}")
    if gname is not None and p.get("graph") != gname:
        raise SystemExit(f"{p['panel']}: graph {p.get('graph')}, expected {gname} (Astra, round 3)")
    if role is not None and p.get("role") != role:
        raise SystemExit(f"{p['panel']}: role {p.get('role')}, expected {role}")
    if p["genomes"] != ids:
        raise SystemExit(f"{p['panel']}: genome ids differ from the census (a smoke record?)")
    want = expected_arms(p.get("role", role))
    missing = [a for a in want if a not in p["arms"]]
    bad = [a for a in want if a in p["arms"] and len(p["arms"][a]) != len(ids)]
    if missing or bad:
        raise SystemExit(f"{p['panel']}: missing arms {missing}, incomplete arms {bad}")
    if [x.get("genome") for x in p.get("info", [])] != ids:
        raise SystemExit(f"{p['panel']}: info not aligned with the genomes")
    m4a.part2_gate({"panel": p["panel"], "genomes": ids, "arms": {"intact": p["arms"]["intact"]}})
    if p.get("role") == "N2" and MAX_GENOMES >= 10**9:  # a smoke's truncated N2 record cannot equal M4a's
        m2 = json.load(open(ROOT / "runs" / "memory-m4a" / f"part2__{p['panel']}.json"))
        if m2["genomes"] != ids or m2["arms"]["intact"] != p["arms"]["intact"] or m2["arms"]["C3"] != p["arms"]["C3"]:
            raise SystemExit(f"{p['panel']}: the intact or C3 arm differs from M4a's Part 2")


def main():
    for name, (gname, seed, role, ids) in expected().items():
        f = OUT / f"{name}.json"
        if f.exists():
            validate(json.load(open(f)), ids, name, role, gname)
            continue
        run_panel(name, gname, seed, role)


if __name__ == "__main__":
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M4b", script="m4b.py"):
        main()
