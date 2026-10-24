"""M4d (docs/memory/M4D-PLAN.md): does N2's head core carry the switch into other graphs? Ten fresh hosts from 03's
samplers (two per ensemble); in each, C3's 30x30 chemical block is replaced by N2's (T), by controls of the same edge
count, weight multiset and autapses (D at random positions, R and Rr rewired within the block at fixed degrees, P with
N2's edges and shuffled weights), or by N2's with its gap junctions (T+G), against the intact host (I). One genome
panel per host is drawn on the intact host and every arm's genome is built from it, so the untouched parameters are
the same in every arm. Every drawn genome is classified by M2's frozen classifier, with no eligibility floor. Writes
runs/memory-m4d/; readings by m4d_read.py. CPU only.
Usage: python scripts/memory_m4/m4d.py [stage ...]   (stages: hosts blocks arms companion; all, in that order)"""
from __future__ import annotations

import hashlib
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
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.exp03 import samplers as SM  # noqa: E402

torch.set_grad_enabled(False)
ROOT = Path(__file__).resolve().parents[2]
REAL = ROOT / "runs" / "memory-m4d"
SMOKE = bool(os.environ.get("MEMORY_M4D_SMOKE"))
OUT = Path(os.environ.get("MEMORY_M4D_OUT", REAL))
OUT.mkdir(parents=True, exist_ok=True)
if SMOKE and OUT.resolve() == REAL.resolve():  # a smoke must not land where the real run reads
    raise SystemExit("a smoke run (MEMORY_M4D_SMOKE) needs MEMORY_M4D_OUT set to another folder")
SEED_BASE = {"SH": 2010000, "SH-route": 2020000, "SH-class": 2030000, "SH-mirror": 2040000, "SH-recip": 2050000}
ENSEMBLES = tuple(SEED_BASE)
HOST_OFFSET = 9000 if SMOKE else 1000  # 03mc used offsets 0 to 127
HOSTS_PER = 1 if SMOKE else 2
HOST_ENSEMBLES = ("SH",) if SMOKE else ENSEMBLES
N_PANEL = 256 if SMOKE else 1024
GENOME_SEED = 7999 if SMOKE else 7901  # + host
SEED_BLOCK, SEED_SIGN, SEED_COMP_SIGN = 20261201, 20261211, 20261231
COMP_N2_SEEDS, COMP_HOST_SEED = (7931, 7932), 7941
M4C_SEEDS = list(range(7801, 7809))
ARMS = ("I", "D", "R", "Rr", "P", "T", "T+G")
DRAWN = ("D", "R", "Rr", "P")
SWAPS_PER_EDGE, ATTEMPT_FACTOR = 20, 200
CHUNK = 128
STOP_HOURS = 30.0
CODES = census.CODES
N_EDGES, N_RECIP, N_AUTAPSES = 260, 75, 8  # N2's block, as computed while planning; checked on every build
CAP = reg.CapClock(STOP_HOURS, OUT / "compute.json")  # earlier invocations' recorded seconds count (Astra, Fable)


class Stop(SystemExit):
    pass


# --------------------------------------------------------------------------------------------------------------- hosts
def core_idx():
    return np.array(m4a.core())


def host_list():
    """[(host index, ensemble, first seed)] in a fixed order: two per ensemble, ensembles in 03's order."""
    out = []
    for kind in HOST_ENSEMBLES:
        for i in range(HOSTS_PER):
            out.append((len(out), kind, SEED_BASE[kind] + HOST_OFFSET + i))
    return out


def sha_content(chem, gap):
    """exp03._sha_content of a graph file holding these arrays (name, dtype, shape and bytes, in name order)."""
    h = hashlib.sha256()
    for k, a in sorted({"chem": chem, "gap": gap}.items()):
        a = np.ascontiguousarray(a)
        h.update(k.encode())
        h.update(str(a.dtype).encode())
        h.update(str(a.shape).encode())
        h.update(a.tobytes())
    return h.hexdigest()


def used_graphs():
    """Every earlier graph name in a committed ensembles.json and every content hash in a committed
    graphs_content_manifest.json."""
    names, hashes = set(), set()
    for p in sorted((ROOT / "experiments").glob("*/ensembles.json")):
        names |= {g["name"] for g in json.loads(p.read_text(encoding="utf-8"))["graphs"]}
    for p in sorted((ROOT / "experiments").glob("*/graphs_content_manifest.json")):
        hashes |= set(json.loads(p.read_text(encoding="utf-8"))["graphs"].values())
    return names, hashes


def fresh(name, digest, used):
    names, hashes = used
    return name not in names and digest not in hashes


def build_host(kind, seed, passes=20):
    con, info = SM.build(c.S.CON, kind, seed, passes=passes)
    return con, info


def stage_hosts():
    """Each host from its first seed, moving to the next on a used name or content or a sampler failure (recorded)."""
    f = OUT / "hosts.json"
    if f.exists():
        return load_hosts()
    used = used_graphs()
    recs = []
    taken = set()
    for h, kind, seed0 in host_list():
        skipped = []
        seed = seed0
        while True:
            name = f"{kind}-{seed}"
            try:
                con, info = build_host(kind, seed)
            except SM.SamplerFailure as e:
                skipped.append({"seed": seed, "why": f"sampler: {e}"})
                seed += HOSTS_PER
                continue
            digest = sha_content(con.chem, con.gap)
            if not fresh(name, digest, used) or digest in taken:
                skipped.append({"seed": seed, "why": "used name or content"})
                seed += HOSTS_PER
                continue
            break
        taken.add(digest)
        recs.append({"host": h, "ensemble": kind, "seed": seed, "name": name, "content_sha256": digest,
                     "sampler": info, "skipped": skipped, **block_stats(con.chem[np.ix_(core_idx(), core_idx())])})
        print(f"host {h}: {name} ({len(skipped)} skipped), block {recs[-1]['edges']} edges", flush=True)
    json.dump({"hosts": recs}, open(f, "w"), indent=1, default=int)
    return load_hosts()


def check_host_list(recs):
    """The plan's hosts in order, with distinct names, seeds and contents, each seed in its own sequence."""
    plan = host_list()
    if [(r["host"], r["ensemble"]) for r in recs] != [(h, k) for h, k, _ in plan]:
        raise Stop("hosts.json does not hold the plan's hosts")
    for key in ("name", "seed", "content_sha256"):
        if len({r[key] for r in recs}) != len(recs):
            raise Stop(f"hosts.json repeats a host's {key}")
    for r, (_, kind, s0) in zip(recs, plan):
        if r["name"] != f"{kind}-{r['seed']}" or r["seed"] < s0 or (r["seed"] - s0) % HOSTS_PER:
            raise Stop(f"host {r['name']}: not in its seed sequence")


def load_hosts():
    """The recorded hosts, each regenerated from its seed and matched to its recorded content hash."""
    recs = json.load(open(OUT / "hosts.json"))["hosts"]
    check_host_list(recs)
    used = used_graphs()
    out = []
    for r in recs:
        con, _ = build_host(r["ensemble"], r["seed"])
        if sha_content(con.chem, con.gap) != r["content_sha256"] or not fresh(r["name"], r["content_sha256"], used):
            raise Stop(f"host {r['name']} does not regenerate as recorded, or is not fresh")
        out.append((r, con))
    return out


# -------------------------------------------------------------------------------------------------------------- blocks
def block_stats(B):
    A = B > 0
    off = A.copy()
    np.fill_diagonal(off, False)
    return {"edges": int(off.sum()), "weight": float(B[off].sum()), "autapses": int(np.diag(A).sum()),
            "reciprocal": int((off & off.T).sum() // 2), "in_degree": off.sum(0).tolist(),
            "out_degree": off.sum(1).tolist()}


def n2_block():
    k = core_idx()
    return c.S.CON.chem[np.ix_(k, k)].astype(np.float32)


def recip_delta(A, removed, added):
    """Change in the reciprocal-pair count when the edges `removed` leave A and `added` enter (A is the state before)."""
    before = {frozenset(e) for e in removed + added}
    B = A.copy()
    for a, b in removed:
        B[a, b] = False
    for a, b in added:
        B[a, b] = True
    count = lambda M: sum(1 for p in before for x, y in [tuple(p)] if M[x, y] and M[y, x])  # noqa: E731
    return count(B) - count(A)


def rewire(B, rng, keep_recip=False):
    """N2's off-diagonal block edges rewired by double-edge target swaps (a,b),(c,d) -> (a,d),(c,b): no autapse or
    duplicate created; each weight moves with its source, so in- and out-degrees and out-strengths are kept;
    SWAPS_PER_EDGE accepted swaps per edge. With keep_recip, a swap is accepted only if the reciprocal-pair count is
    unchanged (SH-recip's rule)."""
    n = len(B)
    W = B.copy()
    diag = np.diag(W).copy()
    np.fill_diagonal(W, 0)
    A = W > 0
    edges = [tuple(e) for e in np.argwhere(A)]
    target = SWAPS_PER_EDGE * len(edges)
    acc = att = 0
    while acc < target:
        att += 1
        if att > ATTEMPT_FACTOR * target:
            raise Stop(f"the block's rewiring reached {acc} of {target} swaps")
        e1, e2 = rng.integers(0, len(edges), 2)
        if e1 == e2:
            continue
        (a, b), (cc, d) = edges[e1], edges[e2]
        if a == d or cc == b or A[a, d] or A[cc, b]:
            continue
        if keep_recip and recip_delta(A, [(a, b), (cc, d)], [(a, d), (cc, b)]) != 0:
            continue
        A[a, b] = A[cc, d] = False
        A[a, d] = A[cc, b] = True
        W[a, d], W[cc, b] = W[a, b], W[cc, d]
        W[a, b] = W[cc, d] = 0
        edges[e1], edges[e2] = (a, d), (cc, b)
        acc += 1
    W[np.arange(n), np.arange(n)] = diag
    return W, {"accepted": acc, "attempted": att}


def draw_blocks(h):
    """The host's drawn blocks D, R, Rr, P (default_rng(SEED_BLOCK + 10 host + arm index)) and T, as 30x30 arrays."""
    Bn = n2_block()
    n = len(Bn)
    off = ~np.eye(n, dtype=bool)
    w = Bn[off & (Bn > 0)]
    out, info = {"T": Bn.copy()}, {}
    for ai, arm in enumerate(DRAWN):
        rng = np.random.default_rng(SEED_BLOCK + 10 * h + ai)
        if arm == "D":
            pos = np.argwhere(off)
            take = pos[rng.choice(len(pos), len(w), replace=False)]
            B = np.zeros_like(Bn)
            B[take[:, 0], take[:, 1]] = rng.permutation(w)
            B[np.arange(n), np.arange(n)] = np.diag(Bn)
        elif arm == "P":
            B = Bn.copy()
            m = off & (Bn > 0)
            B[m] = rng.permutation(Bn[m])
        else:
            B, info[arm] = rewire(Bn, rng, keep_recip=arm == "Rr")
        out[arm] = B.astype(np.float32)
    return out, info


def check_blocks(blocks):
    """The plan's rules for every block arm."""
    Bn = n2_block()
    n = len(Bn)
    off = ~np.eye(n, dtype=bool)
    ref = np.sort(Bn[off & (Bn > 0)])
    sn = block_stats(Bn)
    if (sn["edges"], sn["reciprocal"], sn["autapses"]) != (N_EDGES, N_RECIP, N_AUTAPSES):
        raise Stop(f"N2's block is not the plan's: {sn['edges']}, {sn['reciprocal']}, {sn['autapses']}")
    bad = []
    for arm, B in blocks.items():
        s = block_stats(B)
        if s["edges"] != N_EDGES or not np.array_equal(np.sort(B[off & (B > 0)]), ref) \
                or not np.array_equal(np.diag(B), np.diag(Bn)):
            bad.append(f"{arm}: count, weights or autapses differ from N2's")
        if arm in ("R", "Rr", "P", "T") and (s["in_degree"] != sn["in_degree"] or s["out_degree"] != sn["out_degree"]):
            bad.append(f"{arm}: degrees differ from N2's")
        if arm in ("R", "Rr", "T") and not np.allclose((B * off).sum(1), (Bn * off).sum(1)):
            bad.append(f"{arm}: out-strengths differ from N2's")
        if arm in ("Rr", "P", "T") and s["reciprocal"] != N_RECIP:
            bad.append(f"{arm}: {s['reciprocal']} reciprocal pairs")
        if arm in ("P", "T") and not np.array_equal(B > 0, Bn > 0):
            bad.append(f"{arm}: positions differ from N2's")
        if arm == "T" and not np.array_equal(B, Bn):
            bad.append("T: not N2's block")
    if bad:
        raise Stop("blocks violate the plan: " + "; ".join(bad[:10]))


def blocks_record(h):
    blocks, info = draw_blocks(h)
    check_blocks(blocks)
    k = core_idx()
    return {"host": h, "blocks": {a: {"entries": [[int(i), int(j), float(B[i, j])] for i, j in np.argwhere(B > 0)],
                                      **block_stats(B)} for a, B in blocks.items()},
            "chains": info, "core": [int(x) for x in k]}


def stage_blocks():
    want = {"blocks": [blocks_record(h) for h, _, _ in host_list()]}
    f = OUT / "blocks.json"
    if f.exists():
        if json.load(open(f)) != json.loads(json.dumps(want)):
            raise Stop("blocks.json differs from the blocks the code builds: stop for investigation")
        return want
    json.dump(want, open(f, "w"))
    for r in want["blocks"]:
        print(f"host {r['host']}: R {r['chains']['R']}, Rr {r['chains']['Rr']}; reciprocal "
              f"{ {a: b['reciprocal'] for a, b in r['blocks'].items()} }", flush=True)
    return want


def load_blocks():
    f = OUT / "blocks.json"
    if not f.exists():
        raise Stop("blocks.json missing")
    saved = json.load(open(f))
    if saved != json.loads(json.dumps({"blocks": [blocks_record(h) for h, _, _ in host_list()]})):
        raise Stop("blocks.json differs from the blocks the code builds")
    out = {}
    for r in saved["blocks"]:
        bl = {}
        for a, b in r["blocks"].items():
            B = np.zeros((len(r["core"]),) * 2, np.float32)
            for i, j, w in b["entries"]:
                B[i, j] = w
            bl[a] = B
        check_blocks(bl)
        out[r["host"]] = bl
    return out


# ---------------------------------------------------------------------------------------------------------- arm graphs
def arm_graph(host, arm, blocks):
    """The arm's connectome: the host with C3's chemical block replaced (every arm but I), and in T+G its gap junctions
    among C3's neurons replaced by N2's."""
    if arm == "I":
        return host
    k = core_idx()
    chem, gap = host.chem.copy(), host.gap.copy()
    chem[np.ix_(k, k)] = blocks["T" if arm == "T+G" else arm]
    if arm == "T+G":
        gap[np.ix_(k, k)] = c.S.CON.gap[np.ix_(k, k)]
    return c.S.masks(chem, gap, f"{host.label}/{arm}")


def check_outside(host, con):
    """Outside C3's block every arm's chemical matrix equals the host's; the gap layer too outside C3 x C3."""
    k = core_idx()
    inb = np.zeros(host.chem.shape, bool)
    inb[np.ix_(k, k)] = True
    if not (np.array_equal(host.chem[~inb], con.chem[~inb]) and np.array_equal(host.gap[~inb], con.gap[~inb])):
        raise Stop(f"{con.label}: changed outside C3's block")


# ------------------------------------------------------------------------------------------------------------- genomes
def host_genomes(host, n, seed):
    """The panel on the intact host (Genome.random through spikes.genomes) and its configuration."""
    return c.S.genomes(host, n, seed)


def sign_matrix(g_host, n, seed):
    """[S, 30, 30] signs for the block: the intact genome's sign wherever the host has a block edge, a fresh draw
    (default_rng(seed)) elsewhere (Astra, Fable, round 1)."""
    k = core_idx()
    pos = {int(x): a for a, x in enumerate(k)}
    fresh = np.where(np.random.default_rng(seed).random((n, len(k), len(k))) < 0.5, -1.0, 1.0)
    i, j = g_host.spec.chem_i.numpy(), g_host.spec.chem_j.numpy()
    w = g_host.w.numpy()
    for e in np.where(np.isin(i, k) & np.isin(j, k))[0]:
        fresh[:, pos[int(i[e])], pos[int(j[e])]] = np.sign(w[:, e])
    return fresh


def paired_genome(g_host, con, signs):
    """The arm genome on `con` built from the intact genome: outside C3's block every chemical edge keeps its signed
    weight, every neuron its tau and bias, and every gap junction its g; a block edge gets init_w_scale x anatomical
    weight / the intact spec's chem_anat.mean() (Genome.random's arithmetic) with its sign from `signs`; a gap
    junction among C3's neurons that the host lacks, or whose weight changed, gets init_g_scale x weight / the intact
    spec's gap_anat.mean()."""
    hs, cfg = g_host.spec, g_host.cfg
    spec = BrainSpec.from_connectome(con, device="cpu")
    k = core_idx()
    pos = {int(x): a for a, x in enumerate(k)}
    inc = np.zeros(spec.n, bool)
    inc[k] = True
    hidx = {(int(a), int(b)): e for e, (a, b) in enumerate(zip(hs.chem_i.numpy(), hs.chem_j.numpy()))}
    ci, cj = spec.chem_i.numpy(), spec.chem_j.numpy()
    block = inc[ci] & inc[cj]
    outside = np.where(~block)[0]
    w = torch.empty((g_host.n_strains, spec.n_chem), dtype=g_host.w.dtype)
    w[:, torch.as_tensor(outside)] = g_host.w[:, torch.as_tensor([hidx[(int(ci[e]), int(cj[e]))] for e in outside])]
    be = np.where(block)[0]
    mag = cfg.init_w_scale * spec.chem_anat[torch.as_tensor(be)] / hs.chem_anat.mean()
    sg = torch.as_tensor(signs[:, [pos[int(ci[e])] for e in be], [pos[int(cj[e])] for e in be]], dtype=w.dtype)
    w[:, torch.as_tensor(be)] = mag.unsqueeze(0) * sg
    gidx = {(int(a), int(b)): e for e, (a, b) in enumerate(zip(hs.gap_i.numpy(), hs.gap_j.numpy()))}
    g = torch.empty((g_host.n_strains, spec.n_gap), dtype=g_host.g.dtype)
    gi, gj = spec.gap_i.numpy(), spec.gap_j.numpy()
    for e in range(spec.n_gap):
        he = gidx.get((int(gi[e]), int(gj[e])))
        if he is not None and float(hs.gap_anat[he]) == float(spec.gap_anat[e]):
            g[:, e] = g_host.g[:, he]
        else:
            if not (inc[gi[e]] and inc[gj[e]]):
                raise Stop("a gap junction outside C3's block differs from the host's")
            g[:, e] = cfg.init_g_scale * (spec.gap_anat[e] / hs.gap_anat.mean())  # Genome.random's order (Fable)
    out = Genome(spec, cfg, w, g, g_host.tau.clone(), g_host.bias.clone(), None)
    out.clamp_()
    return out


def sham_check(g_host, host, signs):
    """Built with the host's own block, the arm genome must equal Genome.random's bit for bit."""
    k = core_idx()
    sham = paired_genome(g_host, arm_graph(host, "T", {"T": host.chem[np.ix_(k, k)].copy()}), signs)
    for p in Genome.PARAMS:
        a, b = getattr(sham, p), getattr(g_host, p)
        if (a is None) != (b is None) or (a is not None and not torch.equal(a, b)):
            raise Stop(f"the sham genome differs from Genome.random's in {p}")


# -------------------------------------------------------------------------------------------------------------- panels
def write_measures(dense0, k):
    """At the end of the ramp: the squared norm of the two histories' state difference, and its fraction on C3's
    neurons (None when the difference is zero)."""
    d = dense0[:, 0, :].astype(np.float64) - dense0[:, 1, :].astype(np.float64)
    sq = (d ** 2).sum(1)
    on = (d[:, k] ** 2).sum(1)
    return sq, [float(o / s) if s > 0 else None for o, s in zip(on, sq)]


def classify_all(g, cfg):
    """Every genome of g classified by M2's frozen classifier, with no eligibility floor (Astra). Returns per-genome
    columns and the panel's validity (M1's rule)."""
    k = core_idx()
    cols = {x: [] for x in ("class", "reason", "a", "root_distance", "readout_difference", "write_sq", "write_core")}
    steady_all, a_all = [], []
    for lo in range(0, g.n_strains, CHUNK):
        try:
            CAP.check()
        except reg.CapReached:
            raise Stop(f"the run's {STOP_HOURS}-hour cap was reached: what finished is incomplete, not read")
        gs = g.select(list(range(lo, min(lo + CHUNK, g.n_strains))))
        steady_all.append(c.ramp(gs, cfg, with_steady=True)[3])
        run = P.probe_states(gs, cfg)
        sub = {"end": run["end"], "cur": run["cur"], "y": run["y"], "tail": run["tail"]}
        recs, _ = P.full_classify(gs, cfg, sub, compact=True)
        sq, frac = write_measures(run["dense"][:, 0], k)
        for r, s_, f_ in zip(recs, sq, frac):
            cols["class"].append(CODES.index(r["class"]))
            cols["reason"].append(r["reason"])
            cols["a"].append(r["a"])
            cols["root_distance"].append(r["root_distance"])
            cols["readout_difference"].append(r["readout_difference"])
            cols["write_sq"].append(float(s_))
            cols["write_core"].append(f_)
        a_all.append(np.array([r["a"] for r in recs]))
    a, steady = np.concatenate(a_all), np.concatenate(steady_all)
    eligible = int((a >= c.START_FLOOR).sum())
    return cols, {"valid": c.panel_valid(a, steady, eligible), "eligible": eligible}


def panel_file(r, arm):
    return OUT / "arms" / f"{r['name']}__{arm.replace('+', 'p')}.json"


def verify_run():
    """Everything a panel depends on, checked: the hosts (the plan's, regenerated, fresh), the blocks (rebuilt), every
    host's sham, and every arm's graph unchanged outside the block. Returns, per host, the record, the graph, the
    intact genomes and their configuration, the sign matrix, and each arm's graph and content hash. Run before the
    arms and before every reading (Fable, Astra, round 2)."""
    blocks = load_blocks()
    out = []
    for r, host in load_hosts():
        seed = GENOME_SEED + r["host"]
        g_host, cfg = host_genomes(host, N_PANEL, seed)
        signs = sign_matrix(g_host, N_PANEL, SEED_SIGN + r["host"])
        sham_check(g_host, host, signs)
        cons = {}
        for arm in ARMS:
            con = arm_graph(host, arm, blocks[r["host"]])
            check_outside(host, con)
            cons[arm] = (con, sha_content(con.chem, con.gap))
        out.append({"rec": r, "host": host, "g": g_host, "cfg": cfg, "signs": signs, "arms": cons})
    return out


def stage_arms():
    (OUT / "arms").mkdir(parents=True, exist_ok=True)
    for v in verify_run():
        r, g_host, cfg = v["rec"], v["g"], v["cfg"]
        for arm in ARMS:
            con, digest = v["arms"][arm]
            f = panel_file(r, arm)
            if f.exists():
                validate(json.load(open(f)), r, arm, digest)
                continue
            g = g_host if arm == "I" else paired_genome(g_host, con, v["signs"])
            t0 = time.time()
            cols, val = classify_all(g, cfg)
            rec = {"host": r["host"], "name": r["name"], "arm": arm, "genome_seed": GENOME_SEED + r["host"],
                   "n": N_PANEL, "arm_sha256": digest, "genomes": list(range(N_PANEL)), **val, **cols,
                   "seconds": round(time.time() - t0, 1)}
            json.dump(rec, open(f, "w"))
            validate(rec, r, arm, digest)
            n_sep = sum(x in (0, 1) for x in cols["class"])
            print(f"{r['name']} {arm}: {n_sep} separate states, {cols['class'].count(4)} unresolved, "
                  f"{rec['seconds']} s", flush=True)


def validate(rec, r, arm, digest):
    """A saved panel is usable only if it is this host's and arm's, ran on this arm's graph (its content hash binds
    the host and the block), holds genomes 0 to N_PANEL - 1 with every column complete, and was drawn from the host's
    seed."""
    if (rec.get("host"), rec.get("name"), rec.get("arm"), rec.get("genome_seed"), rec.get("n"),
            rec.get("arm_sha256")) != (r["host"], r["name"], arm, GENOME_SEED + r["host"], N_PANEL, digest):
        raise Stop(f"{r['name']} {arm}: the record is not this panel's")
    if rec["genomes"] != list(range(N_PANEL)):
        raise Stop(f"{r['name']} {arm}: genome ids are not 0 to {N_PANEL - 1}")
    for col in ("class", "reason", "a", "root_distance", "readout_difference", "write_sq", "write_core"):
        if len(rec.get(col, [])) != N_PANEL:
            raise Stop(f"{r['name']} {arm}: column {col} incomplete")
    if any(x not in range(len(CODES)) for x in rec["class"]):
        raise Stop(f"{r['name']} {arm}: unknown class codes")


# ----------------------------------------------------------------------------------------------------------- companion
def m4c_switches():
    """M4c's separate-states genomes: (seed, ids) from its committed census records (valid panels only)."""
    out = []
    for s in M4C_SEEDS:
        rec = json.load(open(ROOT / "runs" / "memory-m4c" / "census" / f"N2__{s}.json"))
        if rec.get("seed") != s or rec.get("graph") != "N2" or not rec["valid"]:
            continue
        out.append((s, [gr["genome"] for gr in rec["genomes"] if gr["class"].startswith("separate states")]))
    return out


def m4c_genomes():
    parts = [c.S.genomes(c.S.CON, 1024, s)[0].select(ids) for s, ids in m4c_switches() if ids]
    return Genome.cat(parts)


def with_selected(g_fresh, g_sel):
    """g_fresh with C3's block chemical weights (signs included) and C3's tau and bias taken from g_sel (on N2's
    spec), strain by strain."""
    k = core_idx()
    inc = np.zeros(g_fresh.spec.n, bool)
    inc[k] = True
    ns = {(int(a), int(b)): e for e, (a, b) in enumerate(zip(g_sel.spec.chem_i.numpy(), g_sel.spec.chem_j.numpy()))}
    fi, fj = g_fresh.spec.chem_i.numpy(), g_fresh.spec.chem_j.numpy()
    be = np.where(inc[fi] & inc[fj])[0]
    w = g_fresh.w.clone()
    w[:, torch.as_tensor(be)] = g_sel.w[:, torch.as_tensor([ns[(int(fi[e]), int(fj[e]))] for e in be])]
    tau, bias = g_fresh.tau.clone(), g_fresh.bias.clone()
    tau[:, torch.as_tensor(k)] = g_sel.tau[:, torch.as_tensor(k)]
    bias[:, torch.as_tensor(k)] = g_sel.bias[:, torch.as_tensor(k)]
    return g_fresh.with_params(w=w, tau=tau, bias=bias)


def stage_companion():
    """Fable's circuitry companion (descriptive): M4c's switch genomes' C3 block weights and C3 tau and bias, with fresh
    exteriors in N2 (two each) and in each host's T graph (one each), against the same fresh genomes unchanged."""
    f = OUT / "companion.json"
    if f.exists():
        return
    if not (ROOT / "runs" / "memory-m4c" / "census").exists():
        raise Stop("M4c's census records are missing")
    g_sel = m4c_genomes()
    n = g_sel.n_strains
    rec = {"genomes": n, "m4c": [[s, ids] for s, ids in m4c_switches()], "parts": []}
    for s in COMP_N2_SEEDS:
        g_fresh, cfg = c.S.genomes(c.S.CON, n, s)
        for label, g in (("selected", with_selected(g_fresh, g_sel)), ("control", g_fresh)):
            cols, val = classify_all(g, cfg)
            rec["parts"].append({"where": "N2", "seed": s, "which": label, "class": cols["class"], **val})
            print(f"companion N2 {s} {label}: {sum(x in (0, 1) for x in cols['class'])} of {n}", flush=True)
    blocks = load_blocks()
    for r, host in load_hosts():
        s = COMP_HOST_SEED + r["host"]
        g_h, cfg = host_genomes(host, n, s)
        g_fresh = paired_genome(g_h, arm_graph(host, "T", blocks[r["host"]]), sign_matrix(g_h, n, SEED_COMP_SIGN + r["host"]))
        for label, g in (("selected", with_selected(g_fresh, g_sel)), ("control", g_fresh)):
            cols, val = classify_all(g, cfg)
            rec["parts"].append({"where": r["name"], "seed": s, "which": label, "class": cols["class"], **val})
            print(f"companion {r['name']} {label}: {sum(x in (0, 1) for x in cols['class'])} of {n}", flush=True)
    json.dump(rec, open(f, "w"))


STAGES = {"hosts": stage_hosts, "blocks": stage_blocks, "arms": stage_arms, "companion": stage_companion}


def main(stages):
    for s in stages:
        STAGES[s]()


if __name__ == "__main__":
    todo = sys.argv[1:] or list(STAGES)
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M4d", script="m4d.py"):
        main(todo)
