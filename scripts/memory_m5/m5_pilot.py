"""M5's pilot (docs/memory/M5-PILOT-PLAN.md): design inputs for M5's power calculation, on M4e's ten published hosts.
(a) `rr`: one Rr block per host and draw (M4d's rewiring at N2's labelled degrees and outgoing anatomical magnitudes,
the count of reciprocal pairs kept, N2's diagonal), classified on M4e's genome panel exactly as M4e classified its
arms; (b) `longer`: every genome still unresolved after the 22,000-tick pass in T, K and Rr, replayed and continued to
100,000 ticks; (c) `audit`: 1500 further first-pass-fading genomes per arm, replayed and classified at 22,000 ticks.
Nothing here changes M4e's records or its reading. Writes runs/memory-m5-pilot/; report by m5_pilot_read.py. CPU only.

Usage: python scripts/memory_m5/m5_pilot.py [stage ...]   (stages: rr longer audit; all, in that order)
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m4"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
import m4e  # noqa: E402  (M4e's real settings: its hosts, blocks, panels and classification)
import m4e_stage0 as S0  # noqa: E402

m4d, P, c = m4e.m4d, m4e.P, m4e.c
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402

torch.set_grad_enabled(False)
OUT = Path(os.environ.get("MEMORY_M5P_OUT", ROOT / "runs" / "memory-m5-pilot"))


def check_out_dir(out):
    """Never write where an earlier experiment's records live (Fable, Astra, round 3)."""
    for old in (ROOT / "runs" / "memory-m4d", ROOT / "runs" / "memory-m4e", m4e.OUT):
        if Path(out).resolve() == Path(old).resolve():
            raise SystemExit(f"MEMORY_M5P_OUT points at {out}: an earlier experiment's folder")


check_out_dir(OUT)
# above M4e's families (blocks 20261301-499, signs 20261511-530, reader 20261541-543, audits 20261601-20263508)
SEED_RR, SEED_RR_AUDIT, SEED_BIG_AUDIT = 20264001, 20264101, 20264201  # + hd; + hd; + arm index
LONG = 100_000  # (b)'s horizon
BIG_AUDIT = 1500  # (c)'s genomes per arm
PILOT_ARMS = ("T", "K", "Rr")
N_RECIP = 75
STOP_HOURS = 30.0
CAP = reg.CapClock(STOP_HOURS, OUT / "compute.json")
m4e.CAP, m4e.STOP_HOURS = CAP, STOP_HOURS  # the panels' chunks check the pilot's cap, not M4e's
SEPARATE, UNRESOLVED, FADING, CODES = m4e.SEPARATE, m4e.UNRESOLVED, m4e.FADING, m4e.CODES
CHUNK = m4e.CHUNK
FIRST_FIELDS = ("class", "reason", "a", "root_distance", "readout_difference")  # recorded by the first pass
SECOND_FIELDS = ("class", "reason", "root_distance", "readout_difference")  # recorded by the second pass
# The classifier's batched float64 root search depends on the batch's composition in its last bits; the float32 hold
# does not (the smoke's diagnostic: a genome's end, tail and read-out identical in a batch of 2 and its chunk of 128,
# the chunk reproducing the record bit for bit, the pair differing by 3e-13 in these two fields only). So these two
# are compared within ROOT_TOL relative, the rest exactly, and composition_check replays one genome per arm in its
# original chunk, which must reproduce every field bit for bit.
ROOT_FIELDS, ROOT_TOL = ("root_distance", "readout_difference"), 1e-9


class Stop(SystemExit):
    pass


def cap_check():
    try:
        CAP.check()
    except reg.CapReached:
        raise Stop(f"the pilot's {STOP_HOURS}-hour cap was reached: what finished is reported, the rest incomplete")


# -------------------------------------------------------------------------------------------------------------- Rr
def rr_blocks(hd):
    """Host-draw hd's Rr block (m4d.rewire with keep_recip from N2's block, default_rng(SEED_RR + hd)) and the same
    chain continued with the same generator for as many accepted swaps again (the chain-length check)."""
    Bn = m4d.n2_block()
    rng = np.random.default_rng(SEED_RR + hd)
    B1, ch1 = m4d.rewire(Bn, rng, keep_recip=True)
    B2, ch2 = m4d.rewire(B1, rng, keep_recip=True)
    return B1.astype(np.float32), B2.astype(np.float32), {"first": ch1, "continued": ch2}


def check_rr(B):
    """The plan's rules for an Rr block: N2's labelled degrees, each source's outgoing anatomical magnitudes, 75
    reciprocal pairs, N2's diagonal and edge count."""
    Bn = m4d.n2_block()
    off = ~np.eye(len(Bn), dtype=bool)
    s, sn = m4d.block_stats(B), m4d.block_stats(Bn)
    bad = []
    if (s["in_degree"], s["out_degree"]) != (sn["in_degree"], sn["out_degree"]):
        bad.append("labelled degrees")
    if not all(np.array_equal(np.sort(B[i][off[i]]), np.sort(Bn[i][off[i]])) for i in range(len(Bn))):
        bad.append("a source's outgoing magnitudes")
    if s["reciprocal"] != N_RECIP:
        bad.append(f"{s['reciprocal']} reciprocal pairs")
    if not np.array_equal(np.diag(B), np.diag(Bn)):
        bad.append("diagonal")
    if s["edges"] != sn["edges"]:
        bad.append("edge count")
    if bad:
        raise Stop("an Rr block violates the plan: " + "; ".join(bad))


def similarity(B, Bn):
    """B's overlap with N2's block, split by whether N2's edge is in a reciprocal pair (Fable, Astra); the weight
    overlap three ways (Astra, round 3)."""
    off = ~np.eye(len(Bn), dtype=bool)
    A, An = off & (B > 0), off & (Bn > 0)
    rec = An & An.T
    shared = A & An
    return {"shared_edges": int(shared.sum()), "shared_reciprocal_edges": int((shared & rec).sum()),
            "n2_reciprocal_edges": int(rec.sum()), "shared_nonreciprocal_edges": int((shared & ~rec).sum()),
            "n2_nonreciprocal_edges": int((An & ~rec).sum()), "same_magnitude_edges": int((shared & (B == Bn)).sum()),
            "min_weight_overlap": float(np.minimum(B, Bn)[off].sum() / Bn[off].sum()),
            "n2_weight_share_on_shared_edges": float(Bn[shared].sum() / Bn[off].sum()),
            "own_weight_share_on_shared_edges": float(B[shared].sum() / B[off].sum())}


def sha(B):
    return hashlib.sha256(np.ascontiguousarray(B, np.float32).tobytes()).hexdigest()


def rr_audit_ids(hd, n=None):
    n = m4e.N_DRAW if n is None else n
    rng = np.random.default_rng(SEED_RR_AUDIT + hd)
    return sorted(int(x) for x in rng.choice(n, min(m4e.AUDIT_PER_PANEL, n), replace=False))


def rr_file(r, d):
    return OUT / "arms" / f"{r['name']}__d{d}__Rr.json"


def validate_rr(rec, r, d, digest):
    """M4e's record rules (m4e.validate) with Rr's own audit ids."""
    n = m4e.N_DRAW
    if (rec.get("host"), rec.get("name"), rec.get("draw"), rec.get("arm"), rec.get("genome_seed"), rec.get("n"),
            rec.get("arm_sha256")) != (r["host"], r["name"], d, "Rr", m4e.GENOME_SEED + 2 * r["host"] + d, n, digest):
        raise Stop(f"{r['name']} d{d} Rr: the record is not this panel's")
    if rec.get("genomes") != list(range(n)):
        raise Stop(f"{r['name']} d{d} Rr: genome ids are not 0 to {n - 1}")
    for col in ("class", "reason", "a", "root_distance", "readout_difference", "write_sq", "write_core"):
        if len(rec.get(col, [])) != n:
            raise Stop(f"{r['name']} d{d} Rr: column {col} incomplete")
    s = rec.get("second", {})
    audit = rr_audit_ids(2 * r["host"] + d)
    want = [i for i, x in enumerate(rec["class"]) if x != FADING or i in audit]
    if rec.get("audit") != audit or s.get("ids") != want:
        raise Stop(f"{r['name']} d{d} Rr: the second pass does not cover the plan's genomes")
    for col in SECOND_FIELDS:
        if len(s.get(col, [])) != len(want):
            raise Stop(f"{r['name']} d{d} Rr: second-pass column {col} incomplete (Astra, round 3)")
    if any(x not in range(len(CODES)) for x in rec["class"] + s["class"]):
        raise Stop(f"{r['name']} d{d} Rr: unknown class codes")


def rr_con(v):
    B1, B2, chain = rr_blocks(2 * v["rec"]["host"] + v["draw"])
    check_rr(B1)
    check_rr(B2)
    con = m4e.arm_graph(v["host"], "Rr", {"Rr": B1})
    m4d.check_outside(v["host"], con)
    m4e.check_clamp(v["g"], con)
    return con, B1, B2, chain


def write_json(f, obj):
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(f)


def stage_rr(verified):
    (OUT / "arms").mkdir(parents=True, exist_ok=True)
    Bn = m4d.n2_block()
    rows = []
    for v in verified:
        r, d, g_host, cfg = v["rec"], v["draw"], v["g"], v["cfg"]
        con, B1, B2, chain = rr_con(v)
        digest = m4d.sha_content(con.chem, con.gap)
        scale = g_host.cfg.init_w_scale / float(g_host.spec.chem_anat.mean())
        rows.append({"host": r["name"], "draw": d, "chain": chain, "sha256": [sha(B1), sha(B2)],
                     "first": {**similarity(B1, Bn), **S0.summaries(np.minimum(B1 * scale, g_host.cfg.w_max))},
                     "continued": {**similarity(B2, Bn), **S0.summaries(np.minimum(B2 * scale, g_host.cfg.w_max))}})
        # written as it grows, so a cap stop keeps the blocks already described (Astra, round 3)
        (OUT / "rr-summary.json").write_text(json.dumps({"blocks": rows}, indent=1) + "\n", encoding="utf-8",
                                             newline="\n")
        f = rr_file(r, d)
        if f.exists():
            validate_rr(json.load(open(f)), r, d, digest)
            continue
        g = m4d.paired_genome(g_host, con, v["signs"])
        audit = rr_audit_ids(2 * r["host"] + d)
        t0 = time.time()
        cols, second, val = m4e.classify_panel(g, cfg, audit)
        rec = {"host": r["host"], "name": r["name"], "draw": d, "arm": "Rr",
               "genome_seed": m4e.GENOME_SEED + 2 * r["host"] + d, "n": m4e.N_DRAW, "arm_sha256": digest,
               "genomes": list(range(m4e.N_DRAW)), **val, **cols, "audit": audit, "second": second,
               "seconds": round(time.time() - t0, 1)}
        validate_rr(rec, r, d, digest)
        write_json(f, rec)
        merged = m4e.merged_classes(rec)
        print(f"{r['name']} d{d} Rr: separate {sum(x in SEPARATE for x in cols['class'])} (first pass), "
              f"{sum(x in SEPARATE for x in merged)} (merged); unresolved {merged.count(UNRESOLVED)}; second pass "
              f"{len(second['ids'])} genomes in {second['seconds']} s; {rec['seconds']} s", flush=True)


# ------------------------------------------------------------------------------------------------- replay and extend
def fields(recs, names):
    """The classifier's outputs as the records store them (a JSON round trip, so floats compare exactly)."""
    out = []
    for x in recs:
        x = {**x, "class": CODES.index(x["class"]) if isinstance(x["class"], str) else x["class"]}
        out.append(json.loads(json.dumps({k: x[k] for k in names})))
    return out


def recorded(rec, ids, which):
    """Genome ids' recorded outputs: the first pass's (which="first") or the second pass's ("second")."""
    if which == "first":
        return [json.loads(json.dumps({k: rec[k][i] for k in FIRST_FIELDS})) for i in ids]
    pos = {i: p for p, i in enumerate(rec["second"]["ids"])}
    return [json.loads(json.dumps({k: rec["second"][k][pos[i]] for k in SECOND_FIELDS})) for i in ids]


def companion(ids, n):
    """A genome added to a batch of one and discarded: a one-strain batch is a different path on the CPU (T1; Fable,
    round 3)."""
    return next(i for i in range(n) if i not in ids)


def replay(g, cfg, ids):
    """The first pass for genomes `ids` of g, regenerated in one batch (never of one: a one-strain batch takes another
    path on the CPU, T1) and classified by the frozen rules. Returns the batch, the run (the float32 hold's states),
    the classifier's records for `ids` and the batch's ids. The hold is tested identical in batches of 2 and 3 and in
    the production chunk of 128, and state_check compares it with the original chunk on every (b) genome; the
    classifier's outputs are compared with the record by the registered rule (check_replay)."""
    run_ids = list(ids) + ([companion(ids, g.n_strains)] if len(ids) == 1 else [])
    gs = g.select(run_ids)
    run = P.probe_states(gs, cfg)
    sub = {"end": run["end"], "cur": run["cur"], "y": run["y"], "tail": run["tail"]}
    recs, _ = P.full_classify(gs, cfg, sub, compact=True)
    return gs, run, recs[:len(ids)], run_ids


def extend(gs, cfg, end, y, ticks):
    """The hold continued `ticks` from `end` and classified as M4e's second pass classifies (m4e.second_pass)."""
    run = m4e.continue_hold(gs, cfg, end, ticks)
    run["y"] = y
    recs, _ = P.full_classify(gs, cfg, run, compact=True, initial=run["pre_tail"], follow_ticks=m4e.TAIL, tail_from=1)
    return run["end"], recs


def check_replay(label, got, want, exact=False):
    """The registered rule (the plan): class, reason and write amplitude exactly; the float64 root search's two fields
    within ROOT_TOL relative, |d| / max(1, |recorded|) (exactly too with exact=True). Returns the largest relative
    deviation in those two."""
    bad, dev = [], 0.0
    for i, (a, b) in enumerate(zip(got, want)):
        for k in b:
            if k in ROOT_FIELDS and not exact and a.get(k) is not None and b[k] is not None:
                d = abs(a[k] - b[k]) / max(1.0, abs(b[k]))
                dev = max(dev, d)
                if not d <= ROOT_TOL:
                    bad.append((i, k, a.get(k), b[k]))
            elif json.dumps(a.get(k)) != json.dumps(b[k]):
                bad.append((i, k, a.get(k), b[k]))
        if set(a) != set(b):
            bad.append((i, "fields", sorted(a), sorted(b)))
    if bad or len(got) != len(want):
        raise Stop(f"{label}: the replay's outputs differ from the record's {bad[:3]}: stop for investigation")
    return dev


def chunk_of(i, n):
    lo = (i // CHUNK) * CHUNK
    return list(range(lo, min(lo + CHUNK, n)))


def state_check(g, cfg, part, run):
    """The replay batch's float32 hold equals the original chunks' (M4e's composition) for every genome of `part`:
    end state, tail and read-out (Fable, round 4). Hold only, no classifier. Returns the chunks checked."""
    los = sorted({chunk_of(i, g.n_strains)[0] for i in part})
    for lo in los:
        ids = chunk_of(lo, g.n_strains)
        ch = P.probe_states(g.select(ids), cfg)
        for j, i in enumerate(part):
            if i in ids:
                k = i - lo
                if not (torch.equal(run["end"][j], ch["end"][k]) and np.array_equal(run["tail"][j], ch["tail"][k])
                        and np.array_equal(run["y"][j], ch["y"][k])):
                    raise Stop(f"genome {i}: the float32 hold differs between its replay batch and its chunk")
    return [[lo, chunk_of(lo, g.n_strains)[-1]] for lo in los]


def composition_check(g, cfg, rec, i):
    """Genome i's first pass replayed in its original chunk (m4e.classify_panel's composition): every recorded output
    bit for bit; and its stage-style replay's float32 hold equal to the chunk's (Fable, round 4)."""
    ids = chunk_of(i, g.n_strains)
    gs = g.select(ids)
    run = P.probe_states(gs, cfg)
    sub = {"end": run["end"], "cur": run["cur"], "y": run["y"], "tail": run["tail"]}
    recs, _ = P.full_classify(gs, cfg, sub, compact=True)
    check_replay(f"genome {i} in its chunk", fields([recs[i - ids[0]]], FIRST_FIELDS), recorded(rec, [i], "first"),
                 exact=True)
    _, rrun, _, run_ids = replay(g, cfg, [i])
    k = i - ids[0]
    same = (torch.equal(rrun["end"][0], run["end"][k]) and np.array_equal(rrun["tail"][0], run["tail"][k])
            and np.array_equal(rrun["y"][0], run["y"][k]))
    if not same:
        raise Stop(f"genome {i}: the float32 hold differs between the stage's replay and its chunk")
    return {"genome": i, "chunk": [ids[0], ids[-1]], "exact": True, "states_equal": True, "replay_batch": run_ids}


def panel_record(v, arm):
    """A panel's saved record, validated before it is used (M4e's rules for T and K; Astra, round 3)."""
    r, d = v["rec"], v["draw"]
    if arm == "Rr":
        rec = json.load(open(rr_file(r, d)))
        con = rr_con(v)[0]
        validate_rr(rec, r, d, m4d.sha_content(con.chem, con.gap))
    else:
        rec = json.load(open(m4e.panel_file(r, d, arm)))
        m4e.validate(rec, r, d, arm, v["arms"][arm][1])
    return rec


def panel_genome(v, arm):
    con = rr_con(v)[0] if arm == "Rr" else v["arms"][arm][0]
    return m4d.paired_genome(v["g"], con, v["signs"])


def composition_plan(verified, recs):
    """{arm: (panel index, genome)}: the first target of the first panel with targets, per arm."""
    out = {}
    for arm in PILOT_ARMS:
        for p, v in enumerate(verified):
            ids = longer_targets(recs[arm][p])
            if ids:
                out[arm] = (p, ids[0])
                break
    return out


def check_composition_file(obj, verified, recs):
    """The saved composition checks are the plan's, each passed (Astra, round 4): validated on resume and read."""
    want = composition_plan(verified, recs)
    if set(obj) != set(want):
        raise Stop(f"composition-check.json covers {sorted(obj)}, not {sorted(want)}")
    for arm, (p, i) in want.items():
        v = verified[p]
        o = obj[arm]
        if (o.get("panel"), o.get("genome"), o.get("chunk"), o.get("exact"), o.get("states_equal")) != (
                f"{v['rec']['name']} d{v['draw']}", i, [chunk_of(i, m4e.N_DRAW)[0], chunk_of(i, m4e.N_DRAW)[-1]],
                True, True):
            raise Stop(f"composition-check.json: {arm} is not the plan's passed check")


def fallback_holds(rerun, want):
    """The pre-registered remedy (Fable, round 4): a genome failing the registered rule continues only if M4e's own
    code and composition (m4e.classify_panel on its panel) reproduce its record bit for bit."""
    try:
        check_replay("panel rerun", rerun, want, exact=True)
    except Stop:
        return False
    return True


def panel_rerun(v, arm, cache):
    """M4e's classify_panel on the panel, in M4e's composition, cached: {genome: (first fields, second fields)}."""
    key = (v["rec"]["host"], v["draw"], arm)
    if key not in cache:
        r, d = v["rec"], v["draw"]
        audit = rr_audit_ids(2 * r["host"] + d) if arm == "Rr" else m4e.audit_ids(r["host"], d, arm)
        cols, second, _ = m4e.classify_panel(panel_genome(v, arm), v["cfg"], audit)
        rec = {**cols, "second": second}
        cache[key] = rec
    return cache[key]


def checked(label, got, want, v, arm, part, which, cache, fallbacks):
    """check_replay, with the pre-registered remedy on a failure: rerun the panel as M4e ran it; continue if that
    reproduces each failing genome's record bit for bit (both values recorded), stop otherwise."""
    try:
        return check_replay(label, got, want)
    except Stop:
        rec = panel_rerun(v, arm, cache)
        dev = 0.0
        for i, a, b in zip(part, got, want):
            try:
                dev = max(dev, check_replay(label, [a], [b]))
            except Stop:
                rerun = recorded(rec, [i], which)
                if not fallback_holds(rerun, [b]):
                    raise Stop(f"{label}: genome {i} differs from its record, and M4e's own composition does not "
                               "reproduce the record either: stop for investigation")
                fallbacks.append({"genome": i, "pass": which, "recorded": b, "replayed": a, "panel_rerun_exact": True})
        return dev


def longer_targets(rec):
    """Genomes still unresolved after the 22,000-tick pass (M4e's merged classes)."""
    return [i for i, x in enumerate(m4e.merged_classes(rec)) if x == UNRESOLVED]


LONGER_COLS = ("recorded_2000", "recorded_22000", "replayed_2000", "replayed_22000", "class_100000", "reason_100000")
AUDIT_COLS = ("recorded_2000", "replayed_2000", "class_22000", "reason_22000")


def check_out(out, ids, cols, label, expect=None, rec=None):
    """A stage file's identity, completeness and agreement with its source record, before it is skipped on a resume
    or read (Astra, rounds 3 and 4): host, draw and arm; ids and column lengths; class codes; the stored recorded
    outputs equal to the validated record's exactly; the replayed ones within the registered rule, or covered by a
    recorded fallback whose panel rerun was exact."""
    if expect is not None and (out.get("host"), out.get("draw"), out.get("arm")) != expect:
        raise Stop(f"{label}: not this panel's file")
    if out.get("ids") != ids:
        raise Stop(f"{label}: not this panel's genomes")
    for col in cols:
        if len(out.get(col, [])) != len(ids):
            raise Stop(f"{label}: column {col} incomplete")
    for col in ("class_100000", "class_22000"):
        if col in cols and any(x not in range(len(CODES)) for x in out[col]):
            raise Stop(f"{label}: unknown class codes")
    if rec is None:
        return
    fb = {(x["genome"], x["pass"]) for x in out.get("fallbacks", []) if x.get("panel_rerun_exact") is True}
    for which, rc, pc in (("first", "recorded_2000", "replayed_2000"), ("second", "recorded_22000", "replayed_22000")):
        if rc not in cols:
            continue
        want = recorded(rec, ids, which)
        if json.dumps(out[rc]) != json.dumps(want):
            raise Stop(f"{label}: its copy of the record differs from the record")
        for i, a, b in zip(ids, out[pc], want):
            if (i, which) not in fb:
                check_replay(f"{label} genome {i}", [a], [b])


def stage_longer(verified):
    (OUT / "longer").mkdir(parents=True, exist_ok=True)
    recs = {a: [panel_record(v, a) for v in verified] for a in PILOT_ARMS}
    f = OUT / "composition-check.json"
    if f.exists():
        check_composition_file(json.load(open(f)), verified, recs)
    else:  # one target per arm, in its original chunk, bit for bit, before any continuation
        done = {}
        for arm, (p, i) in composition_plan(verified, recs).items():
            cap_check()
            v = verified[p]
            done[arm] = {"panel": f"{v['rec']['name']} d{v['draw']}",
                         **composition_check(panel_genome(v, arm), v["cfg"], recs[arm][p], i)}
            print(f"composition check {arm}: {done[arm]}", flush=True)
        check_composition_file(done, verified, recs)
        write_json(f, done)
    cache = {}
    for p, v in enumerate(verified):
        r, d, cfg = v["rec"], v["draw"], v["cfg"]
        for arm in PILOT_ARMS:
            f = OUT / "longer" / f"{r['name']}__d{d}__{arm}.json"
            rec = recs[arm][p]
            ids = longer_targets(rec)
            if f.exists():
                check_out(json.load(open(f)), ids, LONGER_COLS, f.name, (r["name"], d, arm), rec)
                continue
            out = {"host": r["name"], "draw": d, "arm": arm, "ids": ids, **{k: [] for k in LONGER_COLS},
                   "batches": [], "state_chunks": [], "fallbacks": [], "max_root_deviation": 0.0,
                   "seconds": {"replay_2000": 0.0, "state_check": 0.0, "to_22000": 0.0, "to_100000": 0.0}}
            if ids:
                g = panel_genome(v, arm)
                for lo in range(0, len(ids), CHUNK):
                    cap_check()
                    part = ids[lo:lo + CHUNK]
                    k = len(part)
                    t0 = time.time()
                    gs, run, r1, run_ids = replay(g, cfg, part)
                    t1 = time.time()
                    out["state_chunks"] += state_check(g, cfg, part, run)
                    t2 = time.time()
                    y = run["y"][:, :301]
                    end22, r22 = extend(gs, cfg, run["end"], y, m4e.EXTRA)
                    t3 = time.time()
                    _, r100 = extend(gs, cfg, end22, y, LONG - 2000 - m4e.EXTRA)
                    t4 = time.time()
                    got1, got22 = fields(r1, FIRST_FIELDS), fields(r22[:k], SECOND_FIELDS)
                    want1, want22 = recorded(rec, part, "first"), recorded(rec, part, "second")
                    dev = max(checked(f"{r['name']} d{d} {arm} at 2000", got1, want1, v, arm, part, "first", cache,
                                      out["fallbacks"]),
                              checked(f"{r['name']} d{d} {arm} at 22,000", got22, want22, v, arm, part, "second",
                                      cache, out["fallbacks"]))
                    out["max_root_deviation"] = max(out["max_root_deviation"], dev)
                    out["recorded_2000"] += want1
                    out["recorded_22000"] += want22
                    out["replayed_2000"] += got1
                    out["replayed_22000"] += got22
                    out["class_100000"] += [CODES.index(x["class"]) for x in r100[:k]]
                    out["reason_100000"] += [x["reason"] for x in r100[:k]]
                    out["batches"].append(run_ids)
                    for key, dt in (("replay_2000", t1 - t0), ("state_check", t2 - t1), ("to_22000", t3 - t2),
                                    ("to_100000", t4 - t3)):
                        out["seconds"][key] = round(out["seconds"][key] + dt, 1)
            check_out(out, ids, LONGER_COLS, f.name, (r["name"], d, arm), rec)
            write_json(f, out)
            print(f"longer {r['name']} d{d} {arm}: {len(ids)} genomes; at 100,000: "
                  f"{[CODES[x] for x in out['class_100000']]}; fallbacks {len(out['fallbacks'])}; {out['seconds']}",
                  flush=True)


# ------------------------------------------------------------------------------------------------------- the audit
def audit_pool(recs):
    """[(panel index, genome id)] of first-pass-fading genomes no audit touched, in panel order."""
    pool = []
    for p, rec in enumerate(recs):
        seen = set(rec["audit"]) | set(rec["second"]["ids"])
        pool += [(p, i) for i, x in enumerate(rec["class"]) if x == FADING and i not in seen]
    return pool


def audit_sample(recs, arm, n=BIG_AUDIT):
    pool = audit_pool(recs)
    rng = np.random.default_rng(SEED_BIG_AUDIT + PILOT_ARMS.index(arm))
    pick = sorted(rng.choice(len(pool), min(n, len(pool)), replace=False).tolist())
    return [pool[k] for k in pick]


def stage_audit(verified):
    (OUT / "audit").mkdir(parents=True, exist_ok=True)
    cache = {}
    for arm in PILOT_ARMS:
        recs = [panel_record(v, arm) for v in verified]
        sample = audit_sample(recs, arm)
        for p, v in enumerate(verified):
            r, d, cfg = v["rec"], v["draw"], v["cfg"]
            f = OUT / "audit" / f"{r['name']}__d{d}__{arm}.json"
            ids = [i for q, i in sample if q == p]
            if f.exists():
                check_out(json.load(open(f)), ids, AUDIT_COLS, f.name, (r["name"], d, arm), recs[p])
                continue
            out = {"host": r["name"], "draw": d, "arm": arm, "ids": ids, **{k: [] for k in AUDIT_COLS},
                   "batches": [], "fallbacks": [], "max_root_deviation": 0.0,
                   "seconds": {"replay_2000": 0.0, "to_22000": 0.0}}
            g = panel_genome(v, arm) if ids else None
            for lo in range(0, len(ids), CHUNK):
                cap_check()
                part = ids[lo:lo + CHUNK]
                k = len(part)
                t0 = time.time()
                gs, run, r1, run_ids = replay(g, cfg, part)
                t1 = time.time()
                _, r22 = extend(gs, cfg, run["end"], run["y"][:, :301], m4e.EXTRA)
                t2 = time.time()
                got1, want1 = fields(r1, FIRST_FIELDS), recorded(recs[p], part, "first")
                out["max_root_deviation"] = max(out["max_root_deviation"], checked(
                    f"{r['name']} d{d} {arm} audit at 2000", got1, want1, v, arm, part, "first", cache, out["fallbacks"]))
                out["recorded_2000"] += want1
                out["replayed_2000"] += got1
                out["class_22000"] += [CODES.index(x["class"]) for x in r22[:k]]
                out["reason_22000"] += [x["reason"] for x in r22[:k]]
                out["batches"].append(run_ids)
                out["seconds"]["replay_2000"] = round(out["seconds"]["replay_2000"] + t1 - t0, 1)
                out["seconds"]["to_22000"] = round(out["seconds"]["to_22000"] + t2 - t1, 1)
            check_out(out, ids, AUDIT_COLS, f.name, (r["name"], d, arm), recs[p])
            write_json(f, out)
            moved = sum(x != FADING for x in out["class_22000"])
            print(f"audit {r['name']} d{d} {arm}: {len(ids)} genomes, {moved} changed class; fallbacks "
                  f"{len(out['fallbacks'])}; {out['seconds']}", flush=True)


STAGES = {"rr": stage_rr, "longer": stage_longer, "audit": stage_audit}


def main(stages):
    verified = m4e.verify_run()
    for s in stages:
        STAGES[s](verified)


if __name__ == "__main__":
    todo = sys.argv[1:] or list(STAGES)
    OUT.mkdir(parents=True, exist_ok=True)
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M5-pilot",
                       script="m5_pilot.py"):
        main(todo)
