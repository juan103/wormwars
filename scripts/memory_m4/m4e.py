"""M4e (docs/memory/M4E-PLAN.md): what does a dense block carry? Ten fresh hosts from 03's samplers (two per
ensemble), two block draws per host with 512 paired genomes each. In each, C3's off-diagonal chemical block is
replaced by equal-magnitude random blocks at the host's or N2's edge count and the host's or N2's total weight (U_LL,
U_LH, U_HL, U_HH; U_HX at twice N2's weight, conditional), by U_HH's support with N2's block weights (W), by N2's
edges rewired at N2's labelled degrees with N2's weights shuffled (K), or by N2's block (T), against the intact host
(I); the host's autapses stay in every arm but T. Every genome is classified by M2's frozen classifier with no
eligibility floor, and the genomes the plan names get a second pass at a hold of 22,000 ticks. Writes
runs/memory-m4e/; readings by m4e_read.py. CPU only.

Usage: python scripts/memory_m4/m4e.py [stage ...]   (stages: hosts blocks arms; all, in that order)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
import m4d  # noqa: E402

census, P, c, E = m4d.census, m4d.P, m4d.c, m4d.E
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import Brain  # noqa: E402
from wormwars.exp03 import samplers as SM  # noqa: E402

torch.set_grad_enabled(False)
ROOT = Path(__file__).resolve().parents[2]
REAL = ROOT / "runs" / "memory-m4e"
SMOKE = bool(os.environ.get("MEMORY_M4E_SMOKE"))
OUT = Path(os.environ.get("MEMORY_M4E_OUT", REAL))
if SMOKE and OUT.resolve() == REAL.resolve():  # a smoke must not land where the real run reads
    raise SystemExit("a smoke run (MEMORY_M4E_SMOKE) needs MEMORY_M4E_OUT set to another folder")

SEED_BASE, ENSEMBLES = m4d.SEED_BASE, m4d.ENSEMBLES
HOST_OFFSET = 9100 if SMOKE else 1100  # M4d used 1000 + i, 03mc 0 to 127
HOSTS_PER = 1 if SMOKE else 2
HOST_ENSEMBLES = ("SH",) if SMOKE else ENSEMBLES
DRAWS = 1 if SMOKE else 2
N_DRAW = int(os.environ.get("MEMORY_M4E_SMOKE_N", 128)) if SMOKE else 512
GENOME_SEED = 8199 if SMOKE else 8101  # + 2 host + draw
# block 20261301 + 10 (2h + d) + arm (to 20261499, U_HX's generator included); signs 20261511 + 2h + d;
# audits 20261601 + 100 (2h + d) + arm;
# the reader's 20261541 to 20261543. A smoke shifts all three families by 900,000 (Fable, round 1).
_SHIFT = 900_000 if SMOKE else 0
SEED_BLOCK, SEED_SIGN, SEED_AUDIT = 20261301 + _SHIFT, 20261511 + _SHIFT, 20261601 + _SHIFT
AUDIT_PER_PANEL = 40  # about 800 fading genomes per arm: zero flips bound the rate below 0.4% (Astra, round 1)
EXTRA = 20_000  # the second pass continues the hold from tick 2000 to 22,000
TAIL = 200  # ticks recorded at the end of a follow, as the first pass records ticks 1801 to 2000
INCLUDE_UHX = True if SMOKE else False  # out by the plan's rule after the smoke benchmark (M4E-PLAN, 2026-10-26)
ARMS = ("I", "U_LL", "U_LH", "U_HL", "U_HH", "W", "K", "T")
CHUNK = 128
STOP_HOURS = 48.0
CODES = census.CODES
SEPARATE, OSCILLATION, UNRESOLVED, FADING = (0, 1), 3, 4, 2
N2_E, N2_S = 260, 2347.0  # N2's off-diagonal block, checked on every build
RECIP_TOL, RECIP_ATTEMPTS = 2, 200
CAP = reg.CapClock(STOP_HOURS, OUT / "compute.json")


class Stop(SystemExit):
    pass


def arms():
    if INCLUDE_UHX is None:
        raise Stop("U_HX's inclusion is not yet decided (the plan: after the smoke, before any formal arm)")
    return ARMS + (("U_HX",) if INCLUDE_UHX else ())


# --------------------------------------------------------------------------------------------------------------- hosts
def host_list():
    """[(host index, ensemble, first seed)]: two per ensemble, ensembles in 03's order."""
    out = []
    for kind in HOST_ENSEMBLES:
        for i in range(HOSTS_PER):
            out.append((len(out), kind, SEED_BASE[kind] + HOST_OFFSET + i))
    return out


def used_graphs():
    """M4d's used set (every committed ensembles.json and content manifest) and M4d's ten hosts."""
    names, hashes = m4d.used_graphs()
    f = ROOT / "runs" / "memory-m4d" / "hosts.json"
    for r in json.loads(f.read_text(encoding="utf-8"))["hosts"]:
        names.add(r["name"])
        hashes.add(r["content_sha256"])
    return names, hashes


def stage_hosts():
    f = OUT / "hosts.json"
    if f.exists():
        return load_hosts()
    used = used_graphs()
    recs, taken = [], set()
    for h, kind, seed0 in host_list():
        skipped, seed = [], seed0
        while True:
            name = f"{kind}-{seed}"
            try:
                con, info = m4d.build_host(kind, seed)
            except SM.SamplerFailure as e:
                skipped.append({"seed": seed, "why": f"sampler: {e}"})
                seed += HOSTS_PER
                continue
            digest = m4d.sha_content(con.chem, con.gap)
            if not m4d.fresh(name, digest, used) or digest in taken:
                skipped.append({"seed": seed, "why": "used name or content"})
                seed += HOSTS_PER
                continue
            break
        taken.add(digest)
        k = m4d.core_idx()
        recs.append({"host": h, "ensemble": kind, "seed": seed, "name": name, "content_sha256": digest,
                     "sampler": info, "skipped": skipped, **m4d.block_stats(con.chem[np.ix_(k, k)])})
        print(f"host {h}: {name} ({len(skipped)} skipped), block {recs[-1]['edges']} edges", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump({"hosts": recs}, open(f, "w"), indent=1, default=int)
    return load_hosts()


def check_host_list(recs):
    plan = host_list()
    if [(r["host"], r["ensemble"]) for r in recs] != [(h, k) for h, k, _ in plan]:
        raise Stop("hosts.json does not hold the plan's hosts")
    for key in ("name", "seed", "content_sha256"):
        if len({r[key] for r in recs}) != len(recs):
            raise Stop(f"hosts.json repeats a host's {key}")
    for r, (_, kind, s0) in zip(recs, plan):
        if r["name"] != f"{kind}-{r['seed']}" or r["seed"] < s0 or (r["seed"] - s0) % HOSTS_PER:
            raise Stop(f"host {r['name']}: not in its seed sequence")
        if [s["seed"] for s in r["skipped"]] != list(range(s0, r["seed"], HOSTS_PER)):
            raise Stop(f"host {r['name']}: the seeds before it are not all recorded as skipped (Astra, round 1)")


def check_skips(recs, used):
    """Each recorded skip regenerated: a sampler failure, or a used or earlier-taken name or content."""
    taken = set()
    for r in recs:
        for s in r["skipped"]:
            name = f"{r['ensemble']}-{s['seed']}"
            try:
                con, _ = m4d.build_host(r["ensemble"], s["seed"])
            except SM.SamplerFailure:
                continue
            digest = m4d.sha_content(con.chem, con.gap)
            if m4d.fresh(name, digest, used) and digest not in taken:
                raise Stop(f"host {r['name']}: skipped seed {s['seed']} is fresh, so it should have been used")
        taken.add(r["content_sha256"])


def load_hosts():
    recs = json.load(open(OUT / "hosts.json"))["hosts"]
    check_host_list(recs)
    used = used_graphs()
    check_skips(recs, used)
    out = []
    for r in recs:
        con, _ = m4d.build_host(r["ensemble"], r["seed"])
        if m4d.sha_content(con.chem, con.gap) != r["content_sha256"] or not m4d.fresh(r["name"], r["content_sha256"],
                                                                                        used):
            raise Stop(f"host {r['name']} does not regenerate as recorded, or is not fresh")
        out.append((r, con))
    return out


# -------------------------------------------------------------------------------------------------------------- blocks
def arm_index(arm):
    return (ARMS + ("U_HX",)).index(arm)


def match_recip(W, target, rng):
    """Further degree-preserving swaps of W's off-diagonal edges, each accepted only if it moves the reciprocal-pair
    count toward `target`, until within RECIP_TOL or RECIP_ATTEMPTS x edges attempts (the plan's fallback: the
    achieved count is recorded and used). Weights move with their sources, as in m4d.rewire."""
    n = len(W)
    W = W.copy()
    diag = np.diag(W).copy()
    np.fill_diagonal(W, 0)
    A = W > 0
    edges = [tuple(e) for e in np.argwhere(A)]
    recip = lambda M: int((M & M.T).sum() // 2)  # noqa: E731
    cur, att = recip(A), 0
    while abs(cur - target) > RECIP_TOL and att < RECIP_ATTEMPTS * len(edges):
        att += 1
        e1, e2 = rng.integers(0, len(edges), 2)
        if e1 == e2:
            continue
        (a, b), (cc, d) = edges[e1], edges[e2]
        if a == d or cc == b or A[a, d] or A[cc, b]:
            continue
        delta = m4d.recip_delta(A, [(a, b), (cc, d)], [(a, d), (cc, b)])
        if abs(cur + delta - target) >= abs(cur - target):
            continue
        A[a, b] = A[cc, d] = False
        A[a, d] = A[cc, b] = True
        W[a, d], W[cc, b] = W[a, b], W[cc, d]
        W[a, b] = W[cc, d] = 0
        edges[e1], edges[e2] = (a, d), (cc, b)
        cur += delta
    W[np.arange(n), np.arange(n)] = diag
    return W, {"target": int(target), "achieved": cur, "attempted": att, "matched": abs(cur - target) <= RECIP_TOL}


def draw_blocks(h, d, host_block):
    """The blocks of host h, draw d, as 30x30 float32 arrays (the plan's table). The diagonal is the host's in every
    arm but T. Generators: default_rng(SEED_BLOCK + 10 (2h + d) + arm index)."""
    Bn = m4d.n2_block()
    n = len(Bn)
    off = ~np.eye(n, dtype=bool)
    Hd = np.diag(host_block).astype(np.float32)
    E_h = int((host_block[off] > 0).sum())
    S_h = float(host_block[off].sum())
    w_n2 = Bn[off & (Bn > 0)]
    if len(w_n2) != N2_E or not np.isclose(w_n2.sum(), N2_S):
        raise Stop("N2's block is not the plan's")
    rng = {a: np.random.default_rng(SEED_BLOCK + 10 * (2 * h + d) + arm_index(a)) for a in ARMS + ("U_HX",)}
    pos = np.argwhere(off)
    hi = pos[rng["U_HL"].choice(len(pos), N2_E, replace=False)]
    lo = hi[rng["U_LL"].choice(N2_E, E_h, replace=False)]

    def eq(support, total):
        B = np.zeros((n, n), np.float32)
        B[support[:, 0], support[:, 1]] = np.float32(total / len(support))
        return B

    out = {"U_LL": eq(lo, S_h), "U_LH": eq(lo, N2_S), "U_HL": eq(hi, S_h), "U_HH": eq(hi, N2_S),
           "U_HX": eq(hi, 2 * N2_S)}
    Wb = np.zeros((n, n), np.float32)
    Wb[hi[:, 0], hi[:, 1]] = rng["W"].permutation(w_n2)
    out["W"] = Wb
    Kb, chain = m4d.rewire(Bn, rng["K"])
    m = off & (Kb > 0)
    Kb[m] = rng["K"].permutation(Kb[m])
    Kb, recip = match_recip(Kb, m4d.block_stats(Wb)["reciprocal"], rng["K"])
    out["K"] = Kb.astype(np.float32)
    for a in out:
        out[a][np.arange(n), np.arange(n)] = Hd
    out["T"] = Bn.copy()
    return out, {"E_h": E_h, "S_h": S_h, "K_chain": chain, "K_recip": recip,
                 "low_support": lo.tolist(), "high_support": hi.tolist()}


def check_blocks(blocks, info, host_block):
    """The plan's rules for every block of one host and draw."""
    Bn = m4d.n2_block()
    n = len(Bn)
    off = ~np.eye(n, dtype=bool)
    bad = []
    lo = {tuple(x) for x in info["low_support"]}
    hi = {tuple(x) for x in info["high_support"]}
    if not lo <= hi or len(lo) != info["E_h"] or len(hi) != N2_E:
        bad.append("supports not nested, or of the wrong size")
    for a, (sup, total) in {"U_LL": (lo, info["S_h"]), "U_LH": (lo, N2_S), "U_HL": (hi, info["S_h"]),
                            "U_HH": (hi, N2_S), "U_HX": (hi, 2 * N2_S)}.items():
        B = blocks[a]
        got = {tuple(x) for x in np.argwhere(off & (B > 0))}
        vals = B[off & (B > 0)]
        if got != sup or not np.allclose(vals, total / len(sup), rtol=1e-6) or not np.isclose(vals.sum(), total,
                                                                                             rtol=1e-5):
            bad.append(f"{a}: support, equal magnitudes or total")
    if {tuple(x) for x in np.argwhere(off & (blocks["W"] > 0))} != hi or not np.array_equal(
            np.sort(blocks["W"][off & (blocks["W"] > 0)]), np.sort(Bn[off & (Bn > 0)])):
        bad.append("W: support or N2's weights")
    sk, sn = m4d.block_stats(blocks["K"]), m4d.block_stats(Bn)
    if sk["in_degree"] != sn["in_degree"] or sk["out_degree"] != sn["out_degree"] or not np.array_equal(
            np.sort(blocks["K"][off & (blocks["K"] > 0)]), np.sort(Bn[off & (Bn > 0)])):
        bad.append("K: N2's degrees or weights")
    if sk["reciprocal"] != info["K_recip"]["achieved"] or info["K_recip"]["target"] != m4d.block_stats(blocks["W"])[
            "reciprocal"]:
        bad.append("K: reciprocal pairs differ from the record, or its target from W's count")
    for a, B in blocks.items():
        want = np.diag(Bn) if a == "T" else np.diag(host_block)
        if not np.array_equal(np.diag(B), want.astype(B.dtype)):
            bad.append(f"{a}: diagonal")
    if not np.array_equal(blocks["T"], Bn):
        bad.append("T: not N2's block")
    if bad:
        raise Stop("blocks violate the plan: " + "; ".join(bad[:10]))


def blocks_record(h, d, host_block):
    blocks, info = draw_blocks(h, d, host_block)
    check_blocks(blocks, info, host_block)
    return {"host": h, "draw": d, "info": info,
            "blocks": {a: {"entries": [[int(i), int(j), float(B[i, j])] for i, j in np.argwhere(B > 0)],
                           **m4d.block_stats(B)} for a, B in blocks.items()}}


def host_block(con):
    k = m4d.core_idx()
    return con.chem[np.ix_(k, k)].astype(np.float32)


def stage_blocks():
    want = {"blocks": [blocks_record(r["host"], d, host_block(con)) for r, con in load_hosts() for d in range(DRAWS)]}
    f = OUT / "blocks.json"
    if f.exists():
        if json.load(open(f)) != json.loads(json.dumps(want)):
            raise Stop("blocks.json differs from the blocks the code builds: stop for investigation")
        return want
    json.dump(want, open(f, "w"))
    for r in want["blocks"]:
        print(f"host {r['host']} draw {r['draw']}: E_h {r['info']['E_h']}, K recip {r['info']['K_recip']}", flush=True)
    return want


def load_blocks(hosts):
    f = OUT / "blocks.json"
    if not f.exists():
        raise Stop("blocks.json missing")
    saved = json.load(open(f))
    want = {"blocks": [blocks_record(r["host"], d, host_block(con)) for r, con in hosts for d in range(DRAWS)]}
    if saved != json.loads(json.dumps(want)):
        raise Stop("blocks.json differs from the blocks the code builds")
    out = {}
    for r in saved["blocks"]:
        bl = {}
        for a, b in r["blocks"].items():
            B = np.zeros((30, 30), np.float32)
            for i, j, w in b["entries"]:
                B[i, j] = w
            bl[a] = B
        out[(r["host"], r["draw"])] = bl
    return out


def arm_graph(host, arm, blocks):
    if arm == "I":
        return host
    k = m4d.core_idx()
    chem = host.chem.copy()
    chem[np.ix_(k, k)] = blocks[arm]
    return c.S.masks(chem, host.gap.copy(), f"{host.label}/{arm}")


def check_clamp(g_host, con):
    """No block magnitude reaches w_max (the plan: a clamped entry stops the run)."""
    spec = m4d.BrainSpec.from_connectome(con, device="cpu")
    mag = g_host.cfg.init_w_scale * spec.chem_anat / g_host.spec.chem_anat.mean()
    if float(mag.max()) >= g_host.cfg.w_max:
        raise Stop(f"{con.label}: a block magnitude reaches w_max")


# --------------------------------------------------------------------------------------------------------- the passes
def audit_ids(h, d, arm, n=None):
    n = N_DRAW if n is None else n
    rng = np.random.default_rng(SEED_AUDIT + 100 * (2 * h + d) + arm_index(arm))
    return sorted(int(x) for x in rng.choice(n, min(AUDIT_PER_PANEL, n), replace=False))


def continue_hold(gs, cfg, end, ticks, tail=TAIL):
    """The float32 hold continued for `ticks` from the tick-2000 states `end` [S, 2, N] (float64 copies of the float32
    states, so exact), recording the last `tail` ticks as probe_states records its tail. Returns the run dict that
    full_classify reads, without y (the caller keeps the first pass's), and the state `tail` ticks before the end
    ("pre_tail"), from which the oscillation check's rerun records the same ticks without repeating the rest."""
    brain = Brain(gs)
    s, n = gs.n_strains, gs.spec.n
    food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
    cf = c.at(cfg, n, s, [food, food]).to(torch.float32)
    v = end.to(torch.float32).clone()
    rec, pre = [], v.clone()
    for t in range(1, ticks + 1):
        v = c.finite(brain.step(v, cf, None), f"second pass {t}")
        if t == ticks - tail:
            pre = v.clone()
        if t > ticks - tail:
            rec.append(v.clone())
    return {"end": v.double(), "cur": cf.double(), "tail": torch.stack(rec, 1).numpy().astype(np.float32),
            "pre_tail": pre}


def second_pass(g, cfg, idx, ends, ys):
    """The plan's second pass for genomes idx of g: the hold continued to 22,000 ticks and classified by the same rules,
    with the first pass's write amplitude and tick-30 and tick-300 read-out differences (ys) kept."""
    if not idx:
        return []
    gs = g.select(list(idx))
    run = continue_hold(gs, cfg, ends, EXTRA)
    run["y"] = ys
    # the oscillation check's rerun records ticks 21,801 to 22,000: from the tick-21,800 state, the same substeps as a
    # rerun from tick 2000, since the float32 hold is deterministic (a test)
    recs, _ = P.full_classify(gs, cfg, run, compact=True, initial=run["pre_tail"], follow_ticks=TAIL, tail_from=1)
    return recs


def classify_panel(g, cfg, audit):
    """Every genome of g classified (no floor), then the second pass on the plan's genomes. Returns the columns, the
    second pass's records and the panel's validity (M1's rule)."""
    k = m4d.core_idx()
    cols = {x: [] for x in ("class", "reason", "a", "root_distance", "readout_difference", "write_sq", "write_core")}
    steady_all, a_all, ends, ys = [], [], [], []
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
        sq, frac = m4d.write_measures(run["dense"][:, 0], k)
        for r, s_, f_ in zip(recs, sq, frac):
            cols["class"].append(CODES.index(r["class"]))
            cols["reason"].append(r["reason"])
            cols["a"].append(r["a"])
            cols["root_distance"].append(r["root_distance"])
            cols["readout_difference"].append(r["readout_difference"])
            cols["write_sq"].append(float(s_))
            cols["write_core"].append(f_)
        a_all.append(np.array([r["a"] for r in recs]))
        ends.append(run["end"])
        ys.append(run["y"][:, :301])
    a, steady = np.concatenate(a_all), np.concatenate(steady_all)
    eligible = int((a >= c.START_FLOOR).sum())
    end, y = torch.cat(ends), np.concatenate(ys)
    who = [i for i, x in enumerate(cols["class"]) if x != FADING or i in audit]
    t0 = time.time()
    recs2 = []
    for lo in range(0, len(who), CHUNK):
        try:
            CAP.check()
        except reg.CapReached:
            raise Stop(f"the run's {STOP_HOURS}-hour cap was reached during a second pass: incomplete, not read")
        part = who[lo:lo + CHUNK]
        recs2 += second_pass(g, cfg, part, end[part], y[part])
    second = {"ids": who, "class": [CODES.index(r["class"]) for r in recs2], "reason": [r["reason"] for r in recs2],
              "root_distance": [r["root_distance"] for r in recs2],
              "readout_difference": [r["readout_difference"] for r in recs2], "seconds": round(time.time() - t0, 1)}
    return cols, second, {"valid": c.panel_valid(a, steady, eligible), "eligible": eligible}


# ----------------------------------------------------------------------------------------------------------- the run
def panel_file(r, d, arm):
    return OUT / "arms" / f"{r['name']}__d{d}__{arm}.json"


def verify_run():
    """Everything a panel depends on, checked: the hosts, the blocks (rebuilt), every host and draw's sham, every
    arm's graph unchanged outside the block and unclamped. Run before the arms and before every reading."""
    hosts = load_hosts()
    blocks = load_blocks(hosts)
    out = []
    for r, host in hosts:
        for d in range(DRAWS):
            hd = 2 * r["host"] + d
            g_host, cfg = m4d.host_genomes(host, N_DRAW, GENOME_SEED + hd)
            signs = m4d.sign_matrix(g_host, N_DRAW, SEED_SIGN + hd)
            m4d.sham_check(g_host, host, signs)
            cons = {}
            for arm in arms():
                con = arm_graph(host, arm, blocks[(r["host"], d)])
                m4d.check_outside(host, con)
                check_clamp(g_host, con)
                cons[arm] = (con, m4d.sha_content(con.chem, con.gap))
            out.append({"rec": r, "draw": d, "host": host, "g": g_host, "cfg": cfg, "signs": signs, "arms": cons})
    return out


def validate(rec, r, d, arm, digest):
    if (rec.get("host"), rec.get("name"), rec.get("draw"), rec.get("arm"), rec.get("genome_seed"), rec.get("n"),
            rec.get("arm_sha256")) != (r["host"], r["name"], d, arm, GENOME_SEED + 2 * r["host"] + d, N_DRAW, digest):
        raise Stop(f"{r['name']} d{d} {arm}: the record is not this panel's")
    if rec["genomes"] != list(range(N_DRAW)):
        raise Stop(f"{r['name']} d{d} {arm}: genome ids are not 0 to {N_DRAW - 1}")
    for col in ("class", "reason", "a", "root_distance", "readout_difference", "write_sq", "write_core"):
        if len(rec.get(col, [])) != N_DRAW:
            raise Stop(f"{r['name']} d{d} {arm}: column {col} incomplete")
    if any(x not in range(len(CODES)) for x in rec["class"]):
        raise Stop(f"{r['name']} d{d} {arm}: unknown class codes")
    s = rec.get("second", {})
    audit = audit_ids(r["host"], d, arm)
    want = [i for i, x in enumerate(rec["class"]) if x != FADING or i in audit]
    if rec.get("audit") != audit or s.get("ids") != want:
        raise Stop(f"{r['name']} d{d} {arm}: the second pass does not cover the plan's genomes")
    for col in ("class", "reason", "root_distance", "readout_difference"):
        if len(s.get(col, [])) != len(want):
            raise Stop(f"{r['name']} d{d} {arm}: second-pass column {col} incomplete")
    if any(x not in range(len(CODES)) for x in s["class"]):
        raise Stop(f"{r['name']} d{d} {arm}: unknown second-pass class codes (Astra, round 1)")


def stage_arms():
    (OUT / "arms").mkdir(parents=True, exist_ok=True)
    for v in verify_run():
        r, d, g_host, cfg = v["rec"], v["draw"], v["g"], v["cfg"]
        for arm in arms():
            con, digest = v["arms"][arm]
            f = panel_file(r, d, arm)
            if f.exists():
                validate(json.load(open(f)), r, d, arm, digest)
                continue
            g = g_host if arm == "I" else m4d.paired_genome(g_host, con, v["signs"])
            audit = audit_ids(r["host"], d, arm)
            t0 = time.time()
            cols, second, val = classify_panel(g, cfg, audit)
            rec = {"host": r["host"], "name": r["name"], "draw": d, "arm": arm,
                   "genome_seed": GENOME_SEED + 2 * r["host"] + d, "n": N_DRAW, "arm_sha256": digest,
                   "genomes": list(range(N_DRAW)), **val, **cols, "audit": audit, "second": second,
                   "seconds": round(time.time() - t0, 1)}
            json.dump(rec, open(f, "w"))
            validate(rec, r, d, arm, digest)
            n1 = sum(x in SEPARATE for x in cols["class"])
            n2 = sum(x in SEPARATE for x in merged_classes(rec))
            print(f"{r['name']} d{d} {arm}: separate {n1} (first pass), {n2} (merged); unresolved "
                  f"{cols['class'].count(UNRESOLVED)}; second pass {len(second['ids'])} genomes in {second['seconds']} s;"
                  f" {rec['seconds']} s", flush=True)


def merged_classes(rec):
    """The reading's classes: the second pass's where it ran, the first pass's elsewhere."""
    out = list(rec["class"])
    for i, x in zip(rec["second"]["ids"], rec["second"]["class"]):
        out[i] = x
    return out


def audit_failed(rec):
    """True if an audited genome classified fading by the first pass is separate states after the second."""
    second = dict(zip(rec["second"]["ids"], rec["second"]["class"]))
    return any(rec["class"][i] == FADING and second.get(i) in SEPARATE for i in rec["audit"])


STAGES = {"hosts": stage_hosts, "blocks": stage_blocks, "arms": stage_arms}


def main(stages):
    for s in stages:
        STAGES[s]()


if __name__ == "__main__":
    todo = sys.argv[1:] or list(STAGES)
    OUT.mkdir(parents=True, exist_ok=True)
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M4e", script="m4e.py"):
        main(todo)
