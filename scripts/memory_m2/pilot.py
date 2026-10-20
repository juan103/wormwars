"""M2 pilot (docs/memory/M2-PILOT-PLAN.md): the sample, the main run, the classifier, the checks R1-R6 and the descriptive
outputs. Each stage writes its own file under runs/memory-m2/ and is skipped when that file exists, so a stopped run
resumes. JSON outputs are committed; trajectories and arrays (.npz) stay local. CPU only.
Usage: python scripts/memory_m2/pilot.py [stage ...]   (stages: sample main classify r3 r4 r4p r5 r6 summary; all by default)"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m1"))
import common as c  # noqa: E402
import classify as K  # noqa: E402
import equilibria as E  # noqa: E402
from wormwars import accounting as acct  # noqa: E402
from wormwars.brain import Brain  # noqa: E402

torch.set_grad_enabled(False)
OUT = Path(os.environ.get("MEMORY_M2_OUT", ROOT / "runs" / "memory-m2"))
OUT.mkdir(parents=True, exist_ok=True)
M1 = ROOT / "runs" / "memory-m1"
GRAPHS = ["N2", "SH-recip-2050039", "SH-class-2030099", "SH-2010013", "SH-mirror-2040045"]
SEED, N_PANEL = 7600, int(os.environ.get("MEMORY_M2_PANEL", 1024))
FOLLOW, DENSE_TO, TAIL_FROM = 2000, 300, 1801
CAP, MIN_T, FORECAST_STOP = 20_000, 200, 1e-3
SUBSTEPS = 32
MAX_CARRIERS, N_GROWERS, N_CONTROLS, N_FADING_REP = 64, 32, 32, 20
STARTS = [0.25 + 0.1875 * i for i in range(9)]
STOP_HOURS = 8.0


def dump(obj, name):
    json.dump(obj, open(OUT / name, "w"), indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))


def load(name):
    return json.load(open(OUT / name))


# ---------------------------------------------------------------------------------------------------------------- probe
def probe_states(g, cfg, starts=(0.25, 1.75), substeps=None, dtype=torch.float32, ticks=FOLLOW, record=True, hook=None):
    """M1's probe with arbitrary ramp starts (fractions of the final food level), one row per start. Returns the read-out
    rows [S, ticks + 1, R], the full states at ticks 0..DENSE_TO, every 10th to TAIL_FROM and every tick from TAIL_FROM
    to `ticks` (settling ranges are computed per history from these), and the final state and input. dtype float64 runs
    the float64 brain."""
    brain = Brain(g) if dtype == torch.float32 else E.brain64(g)
    s, n = g.n_strains, g.spec.n
    food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
    lv0 = [x * food for x in starts]
    cur = lambda levels: c.at(cfg, n, s, levels).to(dtype)  # noqa: E731
    v = brain.initial_state(len(starts)).to(dtype)
    c0 = cur(lv0)
    for t in range(100):
        v = c.finite(brain.step(v, c0, substeps), f"warm-up {t}")
    for t in range(10):
        v = c.finite(brain.step(v, cur([a + (food - a) * (t + 1) / 10 for a in lv0]), substeps), f"ramp {t}")
    cf = cur([food] * len(starts))
    C = c.C.to(dtype)
    rec = {"dense": [v.clone()], "sparse": [], "tail": [], "y": [(torch.tanh(v) @ C).clone()]}
    brain.substep_hook = hook
    for t in range(1, ticks + 1):
        v = c.finite(brain.step(v, cf, substeps), f"follow-up {t}")
        rec["y"].append((torch.tanh(v) @ C).clone())
        if record:
            if t <= DENSE_TO:
                rec["dense"].append(v.clone())
            elif t < TAIL_FROM and t % 10 == 0:
                rec["sparse"].append(v.clone())
            elif t >= TAIL_FROM:
                rec["tail"].append(v.clone())
    brain.substep_hook = None
    out = {"y": torch.stack(rec["y"], 1).double().numpy(), "end": v.double(), "cur": cf.double()}
    if record:
        out["dense"] = torch.stack(rec["dense"], 1).numpy().astype(np.float32)
        out["sparse"] = torch.stack(rec["sparse"], 1).numpy().astype(np.float32) if rec["sparse"] else None
        out["tail"] = torch.stack(rec["tail"], 1).numpy().astype(np.float32) if rec["tail"] else None
    return out


# --------------------------------------------------------------------------------------------------------------- sample
def midpoint_growers(g, cfg):
    """M1's grower diagnostic (growers.py) on every genome of the draw: the one-tick Jacobian at the midpoint of the two
    ramp-end states, its spectral radius, whether the linear state norm grows over 10 ticks, and the tanh-consistent
    forecast of r(30)."""
    out = {"rho": [], "grow10": [], "fore30": []}
    for lo in range(0, g.n_strains, 128):
        idx = list(range(lo, min(lo + 128, g.n_strains)))
        gs = g.select(idx)
        brain, v, food = c.ramp(gs, cfg)
        rec, _, _ = c.follow(brain, cfg, v, food, 1, record=(0,))
        m = v.mean(1, keepdim=True).contiguous()
        n = g.spec.n
        J = torch.zeros(len(idx), n, n, dtype=v.dtype)
        cur = c.at(cfg, n, len(idx), [food])
        with torch.enable_grad():
            x = m.clone().requires_grad_(True)
            y = brain.step(x, cur)[:, 0, :]
            for i in range(n):
                (gi,) = torch.autograd.grad(y[:, i].sum(), x, retain_graph=True)
                J[:, i, :] = gi[:, 0, :]
        J = J.double()
        out["rho"].append(torch.linalg.eigvals(J).abs().max(1).values.numpy())
        a = rec[0]["dy"][:, 0].abs().numpy()
        x0 = rec[0]["dv"][:, 0].clone()
        n0 = x0.norm(dim=1).numpy()
        cm = c.C.unsqueeze(0) * (1 - torch.tanh(m[:, 0].double()) ** 2)
        xx = x0
        for t in range(1, 31):
            xx = torch.einsum("sij,sj->si", J, xx)
            if t == 10:
                out["grow10"].append(xx.norm(dim=1).numpy() / np.maximum(n0, 1e-300) > 1)
        out["fore30"].append((cm * xx).sum(1).abs().numpy() / np.maximum(a, 1e-300))
    return {k: np.concatenate(v) for k, v in out.items()}


def stage_sample():
    """The groups per graph (the plan's sample), from M1's panel arrays for the same 1024-genome draws."""
    res = {}
    rng = np.random.default_rng(20261023)
    for gname in GRAPHS:
        z = np.load(M1 / "panels" / f"{gname}__{SEED}.npz", allow_pickle=False)
        a, d30, ok, cohort = z["a"], z["d30"], z["ok"].astype(bool), z["cohort"].astype(bool)
        g, cfg = c.S.genomes(c.S.graph(gname), N_PANEL, SEED)
        mg = midpoint_growers(g, cfg)
        np.savez_compressed(OUT / f"growers__{gname}.npz", **mg)
        order = np.argsort(-np.where(ok, d30, -1))
        cum = np.cumsum(d30[order]) / d30[ok].sum()
        n_half = int(np.searchsorted(cum, 0.5) + 1)
        carriers = [int(i) for i in order[:min(n_half, MAX_CARRIERS)]]
        coh = [int(i) for i in np.where(cohort)[0]]
        pool = np.where(ok & mg["grow10"] & (mg["rho"] < 1))[0]
        growers = sorted(int(i) for i in rng.choice(pool, min(N_GROWERS, len(pool)), replace=False)) if len(pool) else []
        rest = np.setdiff1d(np.where(ok)[0], carriers + coh + growers)
        controls = sorted(int(i) for i in rng.choice(rest, min(N_CONTROLS, len(rest)), replace=False))
        res[gname] = {"carriers": carriers, "carriers_uncapped": n_half,
                      "carriers_numerator_frac": float(d30[carriers].sum() / d30[ok].sum()),
                      "cohort": coh, "growers": growers, "growers_pool": int(len(pool)), "controls": controls,
                      "all": sorted(set(carriers + coh + growers + controls))}
        print(gname, {k: (len(v) if isinstance(v, list) else v) for k, v in res[gname].items()}, flush=True)
    dump(res, "sample.json")


# ----------------------------------------------------------------------------------------------------------------- main
def stage_main():
    """The main run: the pilot genomes of each graph, M1's probe followed for 2000 ticks, recorded as the plan says."""
    sample = load("sample.json")
    for gname in GRAPHS:
        f = OUT / f"main__{gname}.npz"
        if f.exists():
            continue
        t0 = time.time()
        idx = sample[gname]["all"]
        g, cfg = c.S.genomes(c.S.graph(gname), N_PANEL, SEED)
        r = probe_states(g.select(idx), cfg)
        np.savez_compressed(f, idx=np.array(idx), y=r["y"], end=r["end"].numpy(), dense=r["dense"], sparse=r["sparse"],
                            tail=r["tail"])
        print(gname, len(idx), "genomes", round(time.time() - t0, 1), "s", flush=True)


# ----------------------------------------------------------------------------------------------------------- classifier
def continuation(b64, start, roots, P32, cur, cap=CAP, substeps=None):
    """The float64 continuation of `start` [S, R, N] beside the linear forecast (P32^t x0) of each row's own difference
    x0 from its root (column form; P32 [S, N, N] per strain). Each row runs until its forecast's max norm stays below
    FORECAST_STOP * d0 for 100 consecutive ticks (at least MIN_T, at most cap ticks). Returns d0, T, capped [S, R],
    the last WINDOW distances and forecasts at matching ticks [S, R, WINDOW], and each row's state at its own stopping
    time [S, R, N] (Astra, round 6: not the batch's final state)."""
    S_, R, N = start.shape
    v = start.clone()
    x = (start - roots).clone()
    d0 = x.abs().amax(-1).numpy()
    buf_d, buf_f = np.zeros((K.WINDOW, S_, R)), np.zeros((K.WINDOW, S_, R))
    win_d, win_f = np.zeros((S_, R, K.WINDOW)), np.zeros((S_, R, K.WINDOW))
    T = np.full((S_, R), cap)
    done = np.zeros((S_, R), bool)
    below = np.zeros((S_, R), int)
    v_fin = start.clone()
    for t in range(1, cap + 1):
        v = b64.step(v, cur, substeps)
        x = torch.einsum("sij,srj->sri", P32, x).clamp(-1e30, 1e30)  # clipped: no overflow to inf (Fable, round 5)
        k = (t - 1) % K.WINDOW
        buf_d[k] = (v - roots).abs().amax(-1).numpy()
        buf_f[k] = x.abs().amax(-1).numpy()
        below = np.where(buf_f[k] < FORECAST_STOP * np.maximum(d0, 1e-300), below + 1, 0)
        finish = (~done) & (below >= 100) & (t >= MIN_T)
        if t == cap:
            finish |= ~done
        if finish.any():
            order = [(k + 1 + j) % K.WINDOW for j in range(K.WINDOW)]  # oldest to newest
            win_d[finish] = np.moveaxis(buf_d[order], 0, -1)[finish]
            win_f[finish] = np.moveaxis(buf_f[order], 0, -1)[finish]
            T[finish] = t
            v_fin[torch.from_numpy(finish)] = v[torch.from_numpy(finish)]
            done |= finish
        if done.all():
            break
    return d0, T, T >= cap, win_d, win_f, v_fin


def locate_and_reach(b64, states, cur, substeps=SUBSTEPS, cap=CAP):
    """For each row of states [S, R, N] (float64): damped Newton, the error bound, P's verdict, and whether the row
    reaches its located root (continuation against the forecast at matching ticks). Returns a dict of [S, R] arrays and
    the roots [S, R, N]."""
    S_, R, N = states.shape
    sysm = E.System(b64, cur[:, :1])
    keys = ("located", "error", "sigma", "verdict", "rho", "cont", "near", "reach", "T", "residual", "failed_ls", "singular",
            "dist_end_root", "residual_sub")
    res = {k: np.empty((S_, R), dtype=object) for k in keys}
    roots = torch.zeros_like(states)
    for r in range(R):
        nw = sysm.newton(states[:, r])
        roots[:, r] = nw["v"]
        verdict, rho, cont = sysm.stability(nw["v"], substeps)
        for k, v in (("located", nw["located"]), ("error", sysm.error_bound(nw)), ("sigma", sysm.smallest_singular(nw["v"])),
                     ("verdict", verdict), ("rho", rho), ("cont", cont), ("residual", nw["residual"]),
                     ("failed_ls", nw["failed_line_searches"]), ("singular", nw["singular_solves"]),
                     ("dist_end_root", (nw["v"] - states[:, r]).abs().amax(1).numpy())):
            res[k][:, r] = v
        res["near"][:, r] = res["dist_end_root"][:, r].astype(float) <= K.LOCATE_NEAR
        res["reach"][:, r] = "not located"
        res["T"][:, r] = 0
    for r in range(R):  # one continuation per row index, over the strains whose verdict needs it (Fable, round 5): a
        # root located, near the state, and not unstable; the others' verdict is fixed without it
        accurate = res["error"][:, r].astype(float) <= K.ACCURACY
        need = res["located"][:, r].astype(bool) & res["near"][:, r].astype(bool) & (res["verdict"][:, r] != "unstable") & accurate
        for s_ in np.where(res["located"][:, r].astype(bool) & ~accurate)[0]:
            res["reach"][s_, r] = "not tested (inaccurate root)"
        for s_ in np.where(res["located"][:, r].astype(bool) & ~res["near"][:, r].astype(bool) & accurate)[0]:
            res["reach"][s_, r] = "not approaching"
        for s_ in np.where(res["located"][:, r].astype(bool) & res["near"][:, r].astype(bool) & accurate
                           & (res["verdict"][:, r] == "unstable"))[0]:
            res["reach"][s_, r] = "not tested (unstable root)"
        loc = np.where(need)[0]
        if len(loc) == 0:
            continue
        sub = E.brain64(b64.genome.select(list(loc)))
        sub_sys = E.System(sub, cur[loc, :1])  # H and P from the brain the continuation integrates with (Fable, round 6)
        res_sub = sub_sys.H(roots[loc, r]).abs().amax(1).numpy()
        for j, s_ in enumerate(loc):
            res["residual_sub"][s_, r] = float(res_sub[j])
        P32 = torch.linalg.matrix_power(sub_sys.P(roots[loc, r], substeps), substeps)
        d0, T, capped, wd, wf, _ = continuation(sub, states[loc, r:r + 1], roots[loc, r:r + 1], P32, cur[loc, :1],
                                                cap, substeps)
        for j, s_ in enumerate(loc):
            res["reach"][s_, r] = K.reached(wd[j, 0], wf[j, 0], d0[j, 0], bool(res["near"][s_, r]), bool(capped[j, 0]),
                                            float(res["error"][s_, r]))
            res["T"][s_, r] = int(T[j, 0])
    return res, roots


def history_record(res, s_, r):
    return {"located": bool(res["located"][s_, r]), "error": float(res["error"][s_, r]), "stability": str(res["verdict"][s_, r]),
            "reach": str(res["reach"][s_, r]), "rho_substep": float(res["rho"][s_, r]), "cont_max_re": float(res["cont"][s_, r]),
            "residual": float(res["residual"][s_, r]), "sigma_min": float(res["sigma"][s_, r]),
            "failed_line_searches": int(res["failed_ls"][s_, r]), "singular_solves": int(res["singular"][s_, r]),
            "T": int(res["T"][s_, r]), "dist_end_root": float(res["dist_end_root"][s_, r]),
            "residual_in_continuation_brain": None if res["residual_sub"][s_, r] is None else float(res["residual_sub"][s_, r])}


# ---------------------------------------------------------------------------------------------------------- oscillation
def oscillation_check(g_one, cfg, end_row, tail_row, cur_one, starts, row, cap=CAP, initial=None, eval_substeps=SUBSTEPS,
                      dtype=torch.float32):
    """One candidate history of one genome (strain g_one): a rerun of the integrator being classified, at its precision
    (eval_substeps: 32, or 64 in R3's variant) recorded at every substep over ticks 1801-2000, and a period search there;
    a float64 continuation of `cap` ticks from the main run's tick-2000 state; and Newton from the orbit's final state and
    from its mean over the last period. All three use eval_substeps (Fable, Astra, round 6). Recording at a different
    count would test another integrator: a near-marginal spiral that the 32-substep integrator keeps decays by about 2% a
    period at 64 (found in a smoke test). At 32 substeps a cycle of 2 ticks or more has at least 64 samples a period.
    initial: for planted genomes, the start states instead of the probe. dtype: the precision being classified (float64
    in R3's float64 variant); the recurrence rerun uses it too (Astra, round 8)."""
    substeps = eval_substeps
    rec = []
    count = {"n": 0}
    seen = {"dtype": None}

    def hook(v):
        count["n"] += 1
        if count["n"] > (TAIL_FROM - 1) * substeps:
            rec.append(v[0, row].clone().numpy())
            seen["dtype"] = str(v.dtype).replace("torch.", "")

    if initial is None:
        probe_states(g_one, cfg, starts=starts, substeps=substeps, dtype=dtype, record=False, hook=hook)
    else:
        follow_from(g_one, cfg, initial, substeps=substeps, dtype=dtype, record=False, hook=hook)
    sub = np.array(rec)
    L = K.returns(sub, 50 * substeps)
    b64 = E.brain64(g_one)
    v = end_row.clone().reshape(1, 1, -1)
    last = []
    for t in range(1, cap + 1):
        v = b64.step(v, cur_one, eval_substeps)
        if t > cap - 200:
            last.append(v[0, 0].clone())
    last = torch.stack(last)
    range_late = float((last.max(0).values - last.min(0).values).max())
    range_ref = float((tail_row.max(0) - tail_row.min(0)).max())
    per = max(1, int(round((L or substeps) / substeps)))
    seeds = torch.stack([last[-1], last[-per:].mean(0)])  # [2, N]
    sysm = E.System(b64, cur_one)
    verdicts, dists, rhos, conts = [], [], [], []
    for k in range(2):
        nw = sysm.newton(seeds[k:k + 1])
        if nw["located"][0] and sysm.error_bound(nw)[0] <= K.ACCURACY:
            vd, rho, cont = sysm.stability(nw["v"], eval_substeps)
            verdicts.append(str(vd[0]))
            rhos.append(float(rho[0]))
            conts.append(float(cont[0]))
            dists.append(float((nw["v"][0] - seeds[1]).abs().max()))
    verdict = K.oscillation(True, L, range_late, range_ref, verdicts)
    return {"period_substeps": L, "range_late": range_late, "range_ref": range_ref, "orbit_roots": verdicts,
            "orbit_root_rho_substep": rhos, "orbit_root_cont_max_re": conts, "orbit_root_distance_from_mean": dists,
            "recording_dtype": seen["dtype"], "verdict": verdict}, verdict


# ----------------------------------------------------------------------------------------------------------- classify
def full_classify(g_sel, cfg, run, starts=(0.25, 1.75), substeps=SUBSTEPS, cap=CAP, candidates=True, initial=None,
                  dtype=torch.float32):
    """Classify every genome of g_sel from a probe_states() result: locate and reach both histories' roots, run the
    oscillation procedure on candidates, and apply the classes. Returns the per-genome records and the roots."""
    b64 = E.brain64(g_sel)
    end, cur = run["end"].double(), run["cur"].double()
    y = run["y"]
    a = np.abs(y[:, 0, 0] - y[:, 0, 1])
    res, roots = locate_and_reach(b64, end, cur, substeps, cap)
    ro = ((torch.tanh(roots[:, 0]) - torch.tanh(roots[:, 1])) @ c.C.double()).abs().numpy()
    rd = (roots[:, 0] - roots[:, 1]).abs().amax(1).numpy()
    cand = np.zeros((end.shape[0], 2), bool)
    if run.get("tail") is not None:
        tail = run["tail"]  # [S, 200, 2, N], ticks 1801..2000
        r1 = (tail[:, 90:100].max(1) - tail[:, 90:100].min(1)).max(-1)
        r2 = (tail[:, 190:200].max(1) - tail[:, 190:200].min(1)).max(-1)
        cand = (r1 > K.CANDIDATE_RANGE) & (r2 > K.CANDIDATE_RANGE)
    out = []
    for s_ in range(end.shape[0]):
        hs = [history_record(res, s_, r) for r in range(2)]
        osc, detail = [None, None], [None, None]
        for r in range(2):
            if candidates and cand[s_, r] and not (hs[r]["reach"] == "reached" and hs[r]["stability"] == "stable"):
                detail[r], osc[r] = oscillation_check(g_sel.select([s_]), cfg, end[s_, r], run["tail"][s_, :, r],
                                                      cur[s_:s_ + 1, :1], starts, r, cap=cap, eval_substeps=substeps,
                                                      dtype=dtype,
                                                      initial=None if initial is None else initial[s_:s_ + 1])
        cls, why = K.classify(hs[0], hs[1], float(rd[s_]), float(ro[s_]), float(a[s_]), osc[0], osc[1])
        sens = {str(d): K.classify(hs[0], hs[1], float(rd[s_]), float(ro[s_]), float(a[s_]), osc[0], osc[1], distinct=d)[0]
                for d in (1e-4, 1e-8)}
        out.append({"class": cls, "reason": why, "root_distance": float(rd[s_]), "readout_difference": float(ro[s_]),
                    "a": float(a[s_]), "d30": float(abs(y[s_, 30, 0] - y[s_, 30, 1])),
                    "d300": float(abs(y[s_, 300, 0] - y[s_, 300, 1])), "candidate": [bool(x) for x in cand[s_]],
                    "oscillation": detail, "sensitivity": sens, "histories": hs})
    return out, roots


def follow_from(g, cfg, initial, substeps=None, dtype=torch.float32, ticks=FOLLOW, record=True, hook=None):
    """For planted genomes: the follow-up from constructed start states initial [S, R, N] under the probe's final input,
    recorded as probe_states() records it."""
    brain = Brain(g) if dtype == torch.float32 else E.brain64(g)
    s, n = g.n_strains, g.spec.n
    food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
    cf = c.at(cfg, n, s, [food] * initial.shape[1]).to(dtype)
    v = initial.to(dtype).clone()
    C = c.C.to(dtype)
    rec = {"dense": [v.clone()], "sparse": [], "tail": [], "y": [(torch.tanh(v) @ C).clone()]}
    brain.substep_hook = hook
    for t in range(1, ticks + 1):
        v = c.finite(brain.step(v, cf, substeps), f"follow-up {t}")
        rec["y"].append((torch.tanh(v) @ C).clone())
        if record:
            if t <= DENSE_TO:
                rec["dense"].append(v.clone())
            elif t < TAIL_FROM and t % 10 == 0:
                rec["sparse"].append(v.clone())
            elif t >= TAIL_FROM:
                rec["tail"].append(v.clone())
    brain.substep_hook = None
    out = {"y": torch.stack(rec["y"], 1).double().numpy(), "end": v.double(), "cur": cf.double()}
    if record:
        out["dense"] = torch.stack(rec["dense"], 1).numpy().astype(np.float32)
        out["tail"] = torch.stack(rec["tail"], 1).numpy().astype(np.float32)
    return out


def classify_at_300(g_sel, run, roots2000, records, substeps=SUBSTEPS, cap=CAP):
    """R1 and R2's classification at tick 300 (Astra, rounds 2 and 6): the same rules as at tick 2000 (Newton, the
    accuracy gate, P's verdict and the float64 reaching continuation), applied to the tick-300 states, without the
    oscillation procedure (its windows lie after tick 1800). Returns per genome the class at tick 300, whether each
    history's tick-300 root is the root it reaches by tick 2000, and whether 03mc's criterion called it settled at 300."""
    b64 = E.brain64(g_sel)
    st = torch.from_numpy(run["dense"][:, DENSE_TO]).double()
    cur = run["cur"].double()
    res, roots = locate_and_reach(b64, st, cur, substeps, cap)
    y = run["y"]
    a = np.abs(y[:, 0, 0] - y[:, 0, 1])
    ro = ((torch.tanh(roots[:, 0]) - torch.tanh(roots[:, 1])) @ c.C.double()).abs().numpy()
    rd = (roots[:, 0] - roots[:, 1]).abs().amax(1).numpy()
    same = (roots - roots2000).abs().amax(-1).numpy() <= K.DISTINCT  # [S, 2]
    out = []
    for s_ in range(st.shape[0]):
        hs = [history_record(res, s_, r) for r in range(2)]
        cls, why = K.classify(hs[0], hs[1], float(rd[s_]), float(ro[s_]), float(a[s_]))
        out.append({"class300": cls, "reason300": why, "same_root_as_2000": [bool(x) for x in same[s_]],
                    "histories300": hs})
    settled300 = (run["dense"][:, 291:301].max(1) - run["dense"][:, 291:301].min(1)).max(-1) < c.SETTLE_TOL  # [S, 2]
    return out, settled300


def fading_modes(gs, run, roots, j, floor=1e-12):
    """For a fading genome j: at the common root, P^32's modes (column form: right eigenvectors V are mode shapes, the
    rows of V^-1 give excitation). A mode's part in dy is its read-out visibility, c * sech^2(root) on V's column,
    times its excitation by the tick-300 state difference. The predicted |dy(t)| = |Re sum_k vis_k exc_k mu_k^(t - 300)|
    is set against the observed one over ticks 300-1000, by the slopes of log |dy| fitted where the observed value is
    above `floor`. The observed values come from a float64 continuation of both histories from their tick-300 states:
    the float32 trajectories stall at slightly different float32 points near the common root, and their read-out
    difference freezes (found in a smoke test; the stall level at tick 2000 is recorded). Complex pairs are taken by
    modulus; a cancellation (the predicted value at tick 300 below a tenth of the summed term sizes) is flagged."""
    b64 = E.brain64(gs.select([j]))
    cur = run["cur"].double()[j:j + 1, :1]
    r = roots[j, 0].unsqueeze(0)
    P32 = torch.linalg.matrix_power(E.System(b64, cur).P(r, SUBSTEPS), SUBSTEPS)[0]
    mu, V = torch.linalg.eig(P32)
    W = torch.linalg.inv(V)
    dv = torch.from_numpy(run["dense"][j, DENSE_TO, 0] - run["dense"][j, DENSE_TO, 1]).double().to(V.dtype)
    vis = (c.C.double() * (1 - torch.tanh(r[0]) ** 2)).to(V.dtype) @ V
    exc = W @ dv
    terms = vis * exc
    ts = np.arange(DENSE_TO, 1001, 10)
    pred = np.array([abs(complex((terms * mu ** (t - DENSE_TO)).sum().item()).real) for t in ts])
    v = torch.from_numpy(run["dense"][j:j + 1, DENSE_TO]).double()  # [1, 2, N]
    cur2 = run["cur"].double()[j:j + 1, :1].expand(1, 2, -1).contiguous()
    obs = []
    for t in range(DENSE_TO, ts[-1] + 1):
        if (t - DENSE_TO) % 10 == 0:
            yy = torch.tanh(v[0]) @ c.C.double()
            obs.append(float(abs(yy[0] - yy[1])))
        v = b64.step(v, cur2)
    obs = np.array(obs)
    y = run["y"][j]

    def slope(v):
        m = v > floor
        return float(np.polyfit(ts[m], np.log(v[m]), 1)[0]) if m.sum() >= 3 else None

    k = int(torch.argmax(terms.abs()))
    return {"observed_slope": slope(obs), "predicted_slope": slope(pred), "dominant_mode_rate": float(np.log(abs(mu[k].item()))),
            "slowest_rate": float(np.log(mu.abs().max().item())), "cancellation": bool(pred[0] < 0.1 * float(terms.abs().sum())),
            "points_above_floor": int((obs > floor).sum()), "float32_stall_dy2000": float(abs(y[FOLLOW, 0] - y[FOLLOW, 1])),
            "float32_dy300": float(abs(y[DENSE_TO, 0] - y[DENSE_TO, 1])),
            "stall_stationary": bool(np.ptp(y[TAIL_FROM:FOLLOW + 1, 0] - y[TAIL_FROM:FOLLOW + 1, 1]) == 0)}


def graph_run(gname, idx):
    g, cfg = c.S.genomes(c.S.graph(gname), N_PANEL, SEED)
    return g.select(idx), cfg, g.spec.n


def stage_classify():
    sample = load("sample.json")
    t_first = None
    for gname in GRAPHS:
        f = OUT / f"classes__{gname}.json"
        if f.exists():
            continue
        t0 = time.time()
        z = dict(np.load(OUT / f"main__{gname}.npz", allow_pickle=False))
        idx = [int(i) for i in z["idx"]]
        gs, cfg, n = graph_run(gname, idx)
        food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
        run = {"end": torch.from_numpy(z["end"]), "cur": c.at(cfg, n, len(idx), [food]), "y": z["y"], "tail": z["tail"],
               "dense": z["dense"]}
        recs, roots = full_classify(gs, cfg, run)
        at300, settled300 = classify_at_300(gs, run, roots, recs)
        groups = {k: set(sample[gname][k]) for k in ("carriers", "cohort", "growers", "controls")}
        mg = np.load(OUT / f"growers__{gname}.npz", allow_pickle=False)
        for j, (i, r) in enumerate(zip(idx, recs)):
            r.update({"genome": i, "groups": [k for k in groups if i in groups[k]], **at300[j],
                      "settled300": bool(settled300[j].all()), "midpoint_rho": float(mg["rho"][i]),
                      "grow10": bool(mg["grow10"][i]), "fore30": float(mg["fore30"][i])})
            if r["class"] == "fading":
                r["fading_modes"] = fading_modes(gs, run, roots, j)
        np.savez_compressed(OUT / f"roots__{gname}.npz", idx=np.array(idx), roots=roots.numpy())
        json.dump({"graph": gname, "seconds": round(time.time() - t0, 1), "genomes": recs}, open(f, "w"), indent=1)
        print(gname, round(time.time() - t0, 1), "s",
              {k: sum(r["class"] == k for r in recs) for k in sorted({r["class"] for r in recs})}, flush=True)
        if t_first is None:
            t_first = time.time() - t0
            projected = t_first * len(GRAPHS) * 3 / 3600  # all graphs' classification, then R3-R5 at about twice that
            print(f"projection after the first graph: about {projected:.1f} h", flush=True)
            if projected > STOP_HOURS:
                raise SystemExit(f"projected {projected:.1f} h exceeds {STOP_HOURS} h: the caps are to be revisited (the plan)")


# ------------------------------------------------------------------------------------------------------------------- R3
def representatives(gname, recs):
    rng = np.random.default_rng(20261024 + GRAPHS.index(gname))
    fading = [j for j, r in enumerate(recs) if r["class"] == "fading"]
    other = [j for j, r in enumerate(recs) if r["class"] != "fading"]
    pick = sorted(int(j) for j in rng.choice(fading, min(N_FADING_REP, len(fading)), replace=False)) if fading else []
    return sorted(other + pick)


def stage_r3():
    """R3: the representatives rerun at 64 substeps, in float64 at 32, and at 32 in float32 in batches of 16."""
    for gname in GRAPHS:
        f = OUT / f"r3__{gname}.json"
        if f.exists():
            continue
        t0 = time.time()
        main = json.load(open(OUT / f"classes__{gname}.json"))["genomes"]
        reps = representatives(gname, main)
        idx = [main[j]["genome"] for j in reps]
        gs, cfg, n = graph_run(gname, idx)
        roots_main = torch.from_numpy(np.load(OUT / f"roots__{gname}.npz", allow_pickle=False)["roots"])[reps]
        out = {"representatives": idx, "variants": {}}
        variants = {"substeps64": dict(substeps=64), "float64": dict(dtype=torch.float64), "batch16": dict(batch=16)}
        for name, kw in variants.items():
            recs, roots = [], []
            chunks = [list(range(len(idx)))] if "batch" not in kw else \
                [list(range(i, min(i + kw["batch"], len(idx)))) for i in range(0, len(idx), kw["batch"])]
            for ch in chunks:
                g_ch = gs.select(ch)
                run = probe_states(g_ch, cfg, substeps=kw.get("substeps"), dtype=kw.get("dtype", torch.float32))
                r_, ro_ = full_classify(g_ch, cfg, run, substeps=kw.get("substeps", SUBSTEPS),
                                        dtype=kw.get("dtype", torch.float32))
                recs += r_
                roots.append(ro_)
            roots = torch.cat(roots)
            same_root = (roots - roots_main).abs().amax(-1).numpy() <= K.DISTINCT  # [reps, 2]
            good = np.array([[h["located"] and h["error"] <= K.ACCURACY and h["stability"] == "stable" and h["reach"] == "reached"
                              for h in r_["histories"]] for r_ in recs])
            same_root = same_root & good  # matching root, reached, accurate and stable
            out["variants"][name] = {"classes": [r["class"] for r in recs], "reasons": [r["reason"] for r in recs],
                                     "same_root": same_root.tolist()}
        out["main_classes"] = [main[j]["class"] for j in reps]
        out["seconds"] = round(time.time() - t0, 1)
        dump(out, f.name)
        print("R3", gname, len(idx), "representatives", out["seconds"], "s", flush=True)


# ------------------------------------------------------------------------------------------------------------------- R4
def stage_r4():
    """R4: perturbations of 1e-8, 1e-6 and 1e-4 (max norm) at every reached, P-stable root of the representatives, 8 random
    directions and the eigenvectors of P's two slowest modes, as rows of one strain per root, in float64."""
    rng = np.random.default_rng(20261026)
    for gname in GRAPHS:
        f = OUT / f"r4__{gname}.json"
        if f.exists():
            continue
        t0 = time.time()
        main = json.load(open(OUT / f"classes__{gname}.json"))["genomes"]
        reps = representatives(gname, main)
        roots_all = torch.from_numpy(np.load(OUT / f"roots__{gname}.npz", allow_pickle=False)["roots"])
        targets = []  # (rep index, history)
        for j in reps:
            for h in range(2):
                hh = main[j]["histories"][h]
                if hh["reach"] == "reached" and hh["stability"] == "stable" and hh["error"] <= K.ACCURACY:
                    if h == 1 and main[j]["root_distance"] <= K.DISTINCT:
                        continue  # the same root as history 0
                    targets.append((j, h))
        idx = [main[j]["genome"] for j, _ in targets]
        results = []
        if targets:
            gs, cfg, n = graph_run(gname, idx)
            b64 = E.brain64(gs)
            food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
            cur = c.at(cfg, n, len(idx), [food]).double()
            roots = torch.stack([roots_all[j, h] for j, h in targets])  # [S, N]
            sysm = E.System(b64, cur)
            P = sysm.P(roots, SUBSTEPS)
            P32 = torch.linalg.matrix_power(P, SUBSTEPS)
            ev, V = torch.linalg.eig(P32)
            slow = torch.argsort(ev.abs(), dim=1, descending=True)[:, :2]
            dirs = []
            for s_ in range(len(idx)):
                d = [torch.from_numpy(rng.normal(size=n)) for _ in range(8)]
                d += [V[s_, :, k].real.clone() if V[s_, :, k].real.abs().max() > 0 else V[s_, :, k].imag.clone() for k in slow[s_]]
                dirs.append(torch.stack([x / x.abs().max() for x in d]))
            dirs = torch.stack(dirs).double()  # [S, 10, N]
            sizes = (1e-8, 1e-6, 1e-4)
            starts = torch.cat([roots.unsqueeze(1) + sz * dirs for sz in sizes], 1)  # [S, 30, N]
            other = torch.stack([roots_all[j, 1 - h] for j, h in targets])
            d0, T, capped, wd, wf, v_end = continuation(b64, starts, roots.unsqueeze(1).expand_as(starts).contiguous(),
                                                        P32, cur)
            dest = []  # per row: the root located from its endpoint (at its own stopping time), when accurate
            for q in range(starts.shape[1]):
                nw = sysm.newton(v_end[:, q])
                ok_q = nw["located"] & (sysm.error_bound(nw) <= K.ACCURACY)
                dest.append((nw["v"], ok_q))
            final_d = wd[:, :, -1]
            final_f = wf[:, :, -1]
            for s_, (j, h) in enumerate(targets):
                err = float(main[j]["histories"][h]["error"])
                rows = []
                for q in range(starts.shape[1]):
                    init = float(d0[s_, q])
                    if capped[s_, q] and final_f[s_, q] > K.SLOW_AT_CAP * init:
                        verdict = "inconclusive"
                    else:
                        ok = final_d[s_, q] <= max(K.FLOOR, 10 * err, K.FORECAST_FACTOR * final_f[s_, q]) and final_d[s_, q] <= init / 2
                        verdict = "returns" if ok else "does not return"
                    dv_, okq = dest[q][0][s_], bool(dest[q][1][s_])
                    to_other = bool(main[j]["root_distance"] > K.DISTINCT and okq
                                    and float((dv_ - other[s_]).abs().max()) <= K.DISTINCT
                                    and float((dv_ - roots[s_]).abs().max()) > K.DISTINCT)
                    if to_other:
                        verdict = "small basin"  # counted apart, not a failure to return (the plan; Fable, round 6)
                    rows.append({"size": sizes[q // 10], "direction": "random" if q % 10 < 8 else "slow mode",
                                 "verdict": verdict, "T": int(T[s_, q]), "ended_at_other_root": to_other})
                results.append({"genome": main[j]["genome"], "history": h, "rows": rows})
        dump({"graph": gname, "roots": results, "seconds": round(time.time() - t0, 1)}, f.name)
        print("R4", gname, len(targets), "roots", round(time.time() - t0, 1), "s", flush=True)


# ------------------------------------------------------------------------------------------------------------------ R4'
def stage_r4p():
    """R4': P^32 against the automatic derivative of one float64 tick of Brain.step at 20 reached roots."""
    rng = np.random.default_rng(20261027)
    pool = []
    for gname in GRAPHS:
        main = json.load(open(OUT / f"classes__{gname}.json"))["genomes"]
        for j, r in enumerate(main):
            if r["histories"][0]["reach"] == "reached":
                pool.append((gname, j))
    pick = [pool[i] for i in sorted(rng.choice(len(pool), min(20, len(pool)), replace=False))]
    out = []
    for gname, j in pick:
        main = json.load(open(OUT / f"classes__{gname}.json"))["genomes"]
        root = torch.from_numpy(np.load(OUT / f"roots__{gname}.npz", allow_pickle=False)["roots"])[j, 0].unsqueeze(0)
        gs, cfg, n = graph_run(gname, [main[j]["genome"]])
        b64 = E.brain64(gs)
        food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
        cur = c.at(cfg, n, 1, [food]).double()
        P32 = torch.linalg.matrix_power(E.System(b64, cur).P(root, SUBSTEPS), SUBSTEPS)
        D = E.tick_autograd(b64, root, cur)
        out.append({"graph": gname, "genome": main[j]["genome"], "max_abs_diff": float((P32 - D).abs().max())})
    sign_disagree = []
    for gname in GRAPHS:
        for r in json.load(open(OUT / f"classes__{gname}.json"))["genomes"]:
            for h, hh in enumerate(r["histories"]):
                if hh["located"] and (hh["rho_substep"] < 1) != (hh["cont_max_re"] < 0):
                    sign_disagree.append({"graph": gname, "genome": r["genome"], "history": h,
                                          "rho_substep": hh["rho_substep"], "cont_max_re": hh["cont_max_re"]})
    dump({"checks": out, "passes": all(x["max_abs_diff"] <= 1e-8 for x in out), "P_vs_continuous_disagreements": sign_disagree},
         "r4p.json")
    print("R4'", max(x["max_abs_diff"] for x in out) if out else None, len(sign_disagree), "sign disagreements", flush=True)


# ------------------------------------------------------------------------------------------------------------------- R5
def stage_r5():
    """R5: nine ramp starts for every 'separate states' genome and 20 fading genomes per graph; the distinct stable roots
    reached per genome, a lower bound on the states the histories can reach."""
    for gname in GRAPHS:
        f = OUT / f"r5__{gname}.json"
        if f.exists():
            continue
        t0 = time.time()
        main = json.load(open(OUT / f"classes__{gname}.json"))["genomes"]
        sep = [j for j, r in enumerate(main) if r["class"].startswith("separate states")]
        fading = [j for j, r in enumerate(main) if r["class"] == "fading"]
        rng = np.random.default_rng(20261025 + GRAPHS.index(gname))
        pick = sorted(int(j) for j in rng.choice(fading, min(N_FADING_REP, len(fading)), replace=False)) if fading else []
        chosen = sep + pick
        out = []
        if chosen:
            idx = [main[j]["genome"] for j in chosen]
            gs, cfg, n = graph_run(gname, idx)
            run = probe_states(gs, cfg, starts=STARTS, record=False)
            res, roots = locate_and_reach(E.brain64(gs), run["end"].double(), run["cur"].double())
            for s_, j in enumerate(chosen):
                good = [r for r in range(len(STARTS)) if res["located"][s_, r] and res["reach"][s_, r] == "reached"
                        and res["verdict"][s_, r] == "stable" and float(res["error"][s_, r]) <= K.ACCURACY]
                labels, reps_ = [], []
                for r in range(len(STARTS)):
                    if r not in good:
                        labels.append(None)
                        continue
                    for k, q in enumerate(reps_):
                        if float((roots[s_, r] - q).abs().max()) <= K.DISTINCT:
                            labels.append(k)
                            break
                    else:
                        reps_.append(roots[s_, r])
                        labels.append(len(reps_) - 1)
                y_end = (torch.tanh(roots[s_]) @ c.C.double()).numpy()
                out.append({"genome": main[j]["genome"], "class": main[j]["class"], "distinct_stable_roots": len(reps_),
                            "root_of_start": labels, "unresolved_starts": len(STARTS) - len(good),
                            "end_readout": [float(x) for x in y_end]})
        dump({"graph": gname, "starts": STARTS, "genomes": out, "seconds": round(time.time() - t0, 1)}, f.name)
        print("R5", gname, len(out), "genomes", round(time.time() - t0, 1), "s", flush=True)


# ------------------------------------------------------------------------------------------------------------------- R6
def planted_genomes():
    """The planted genomes on N2's mask (Fable, round 1): every other weight and every gap junction zero. A mutually
    excitatory pair (bistable), the same pair weak (fading), a directed inhibitory three-cycle with high gain
    (oscillating), and the same cycle just below the onset of oscillation (a slowly damped spiral, which must not be
    classed oscillating). Returns {name: (genome, initial states [1, 2, N], expected)}."""
    g, cfg = c.S.genomes(c.S.CON, 1, SEED)
    spec = g.spec
    ci, cj = spec.chem_i.cpu().numpy(), spec.chem_j.cpu().numpy()
    edges = {(int(a), int(b)): k for k, (a, b) in enumerate(zip(ci, cj))}
    avoid = set(c.FOOD_SENSORS) | set(c.READOUT)
    pair = next((a, b) for (a, b) in sorted(edges) if a < b and (b, a) in edges and a not in avoid and b not in avoid)
    sensors = set(c.FOOD_SENSORS)
    ro_pair = next((a, b) for (a, b) in sorted(edges) if (b, a) in edges and a in c.READOUT and b not in c.READOUT
                   and b not in sensors)
    cyc = None
    for (a, b) in sorted(edges):
        if a == b or a in avoid or b in avoid:
            continue
        for k in range(spec.n):
            if k in (a, b) or k in avoid:
                continue
            if (b, k) in edges and (k, a) in edges and not any(e in edges for e in ((a, k), (b, a), (k, b))):
                cyc = (a, b, k)
                break
        if cyc:
            break
    assert cyc is not None, "no directed three-cycle without reverse edges on N2's mask: the plan's fallback applies"

    def build(wdict, taus):
        w = torch.zeros_like(g.w)
        for (a, b), val in wdict.items():
            w[0, edges[(a, b)]] = val
        tau = g.tau.clone()
        for i, t in taus.items():
            tau[0, i] = t
        return g.with_params(w=w, g=torch.zeros_like(g.g), tau=tau, bias=torch.zeros_like(g.bias))

    def init(vals):
        v = torch.zeros(1, 2, spec.n)
        for r, d in enumerate(vals):
            for i, x in d.items():
                v[0, r, i] = x
        return v

    a, b = pair
    x, y, z = cyc
    p0, p1 = ro_pair
    on_ro = init([{p0: 1.0, p1: 1.0}, {p0: -1.0, p1: -1.0}])
    silent_ro = c.READOUT[0]  # a read-out neuron with no weights: its start difference decays, the pair's states stay
    two_silent = init([{a: 1.0, b: 1.0, silent_ro: 1.0}, {a: -1.0, b: -1.0, silent_ro: -1.0}])
    two = init([{a: 1.0, b: 1.0}, {a: -1.0, b: -1.0}])
    ring = init([{x: 1.0, y: -0.5}, {x: -1.0, y: 0.3}])
    taus = {x: 4.0, y: 4.0, z: 4.0}
    ring_of = lambda gain: build({(x, y): -gain, (y, z): -gain, (z, x): -gain}, taus)  # noqa: E731
    food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
    cur = c.at(cfg, spec.n, 1, [food]).double()

    def tick_radius(gain):  # the integrator's radius per tick at the ring's root (the origin), P^32's
        sysm = E.System(E.brain64(ring_of(gain)), cur)
        return float(sysm.stability(torch.zeros(1, spec.n, dtype=torch.float64), SUBSTEPS)[1][0]) ** SUBSTEPS

    lo, hi = 1.5, 1.99999  # the gain at which the integrator damps the spiral by 2e-6 a tick: P-marginal, slow
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if tick_radius(mid) < 1 - 2e-6 else (lo, mid)
    # started small, where tanh saturation adds damping of the same order as the linear rate instead of dominating it
    # (Fable, Astra, rounds 7 and 8: from amplitude 1 it kept only 0.27 of its range, and the range rule alone rejected it)
    ring_small = ring * 0.005
    return {"bistable": (build({(p0, p1): 3.0, (p1, p0): 3.0}, {p0: 2.0, p1: 2.0}), on_ro, "separate states"),
            "bistable, read-out silent": (build({(a, b): 3.0, (b, a): 3.0}, {a: 2.0, b: 2.0}), two_silent,
                                          "separate states, read-out silent"),
            "fading": (build({(a, b): 0.5, (b, a): 0.5}, {a: 2.0, b: 2.0}), two, "fading"),
            "oscillating": (ring_of(3.0), ring, "persistent oscillation"),
            # continuous system stable at its root (rate -1.25e-6 a tick), but the integrator's P is not (radius 1.00009
            # a substep): the explicit chemical term adds about (omega h)^2 / 2 a substep to a weakly damped rotation, and
            # the integrator cycles. The right class for the integrator is a persistent oscillation.
            "integrator cycle": (ring_of(1.99999), ring, "persistent oscillation"),
            "damped spiral": (ring_of(lo), ring_small, "unresolved")}, cfg, {
        "pair": [c.NAMES[i] for i in pair], "readout_pair": [c.NAMES[i] for i in ro_pair],
        "cycle": [c.NAMES[i] for i in cyc], "damped_spiral_gain": lo}


def stage_r6():
    """R6: each planted genome is first confirmed by a long direct float64 simulation, then classified by the pipeline
    from its constructed start states (no ramp)."""
    cases, cfg, where = planted_genomes()
    out = {"neurons": where, "cases": {}}
    for name, (g, init, expected) in cases.items():
        b64 = E.brain64(g)
        food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
        cur = c.at(cfg, g.spec.n, 1, [food, food]).double()
        v = init.double().clone()
        late = []
        for t in range(1, 2 * CAP + 1):  # 40,000 ticks of direct simulation; the range over its last 200 ticks
            v = b64.step(v, cur)
            if t > 2 * CAP - 200:
                late.append(v.clone())
        tail = torch.stack(late)
        rng_end = float((tail.max(0).values - tail.min(0).values).max())
        sep = float((v[0, 0] - v[0, 1]).abs().max())
        confirm = {"bistable": rng_end < 1e-12 and sep > 0.5, "bistable, read-out silent": rng_end < 1e-12 and sep > 0.5,
                   "fading": rng_end < 1e-12 and sep < 1e-9,
                   "oscillating": rng_end > 0.1, "integrator cycle": rng_end > 0.1, "damped spiral": True}[name]
        run = follow_from(g, cfg, init)
        if name == "damped spiral":  # still a candidate at tick 2000, and decaying, which the plan requires of it
            tl = run["tail"]
            r2 = float((tl[:, 190:200].max(1) - tl[:, 190:200].min(1)).max())
            confirm = r2 > K.CANDIDATE_RANGE and rng_end < r2
        if not confirm:
            out["cases"][name] = {"confirmed": False, "note": "the construction does not behave as intended; not used"}
            continue
        recs, _ = full_classify(g, cfg, run, initial=init)
        got = recs[0]["class"]
        ok = got == expected  # exact: "separate states" and its read-out-silent subclass are told apart (Fable, round 6)
        veto_only = None
        if name == "damped spiral":
            # only the root veto may reject it (Fable, Astra, round 7): a period found and 90% of the range kept in every
            # candidate history, the veto's reason given, and the same evidence without the veto would be an oscillation
            det = [d for d in recs[0]["oscillation"] if d]
            veto_only = bool(det and all(d["period_substeps"] is not None and d["range_late"] >= K.PERSIST * d["range_ref"]
                                         and d["verdict"] == "candidate around a stable root"
                                         and K.oscillation(True, d["period_substeps"], d["range_late"], d["range_ref"],
                                                           ["unstable"]) == "persistent oscillation" for d in det))
            ok = ok and veto_only
        out["cases"][name] = {"confirmed": True, "class": got, "reason": recs[0]["reason"], "expected": expected,
                              "correct": bool(ok), "veto_alone_rejects": veto_only, "oscillation": recs[0]["oscillation"]}
        print("R6", name, got, recs[0]["reason"], "correct" if ok else "WRONG", flush=True)
    out["passes"] = all(v.get("correct") for v in out["cases"].values())
    dump(out, "r6.json")


# -------------------------------------------------------------------------------------------------------------- summary
def cheap_rule(allrec):
    """Per history: the cheaper rule (located, accurate, within LOCATE_NEAR of the tick-2000 state) against the full
    verdict (reached)."""
    t = {"both_yes": 0, "cheap_only": 0, "full_only": 0, "both_no": 0}
    for r in allrec.values():
        for h in r["histories"]:
            cheap = h["located"] and h["error"] <= K.ACCURACY and h["dist_end_root"] <= K.LOCATE_NEAR
            full = h["reach"] == "reached"
            t[{(True, True): "both_yes", (True, False): "cheap_only", (False, True): "full_only", (False, False): "both_no"}[(cheap, full)]] += 1
    return t


def stage_summary():
    sample = load("sample.json")
    res = {"graphs": {}, "checks": {}}
    unresolved, flagged = [], {}
    for gname in GRAPHS:
        recs = json.load(open(OUT / f"classes__{gname}.json"))["genomes"]
        num30 = sum(r["d30"] for r in recs)
        num300 = sum(r["d300"] for r in recs)
        by = {}
        for grp in ("carriers", "cohort", "growers", "controls"):
            rr = [r for r in recs if grp in r["groups"]]
            n30, n300 = sum(r["d30"] for r in rr) or 1e-300, sum(r["d300"] for r in rr) or 1e-300
            by[grp] = {k: {"genomes": sum(r["class"] == k for r in rr),
                           "numerator30_frac": sum(r["d30"] for r in rr if r["class"] == k) / n30,
                           "numerator300_frac": sum(r["d300"] for r in rr if r["class"] == k) / n300}
                       for k in sorted({r["class"] for r in rr})}
        un = [r for r in recs if r["class"] == "unresolved"]
        res["graphs"][gname] = {
            "pilot_genomes": len(recs), "carriers_numerator_frac": sample[gname]["carriers_numerator_frac"],
            "by_group": by, "unresolved": len(un), "unresolved_frac": len(un) / len(recs),
            "unresolved_numerator30_frac": sum(r["d30"] for r in un) / max(num30, 1e-300),
            "unresolved_numerator300_frac": sum(r["d300"] for r in un) / max(num300, 1e-300),
            "unresolved_reasons": {k: sum(r["reason"] == k for r in un) for k in sorted({r["reason"] for r in un})},
            "sensitivity": {d: {k: sum(r["sensitivity"][d] == k for r in recs) for k in sorted({r["sensitivity"][d] for r in recs})}
                            for d in ("0.0001", "1e-08")},
            "classes": {k: sum(r["class"] == k for r in recs) for k in sorted({r["class"] for r in recs})}}
        unresolved += un
        settled = [r for r in recs if r["settled300"]]
        good = lambda r: all(h["reach"] == "reached" and h["stability"] == "stable" and h["error"] <= K.ACCURACY  # noqa: E731
                             for h in r["histories"])
        miss = [r for r in settled if not good(r)]
        trans = {}
        for r in recs:
            key = f'{r["class300"]} -> {r["class"]}'
            trans[key] = trans.get(key, 0) + 1
        res["graphs"][gname]["R1"] = {
            "settled300": len(settled), "both_reach_stable": len(settled) - len(miss),
            "flagged_numerator30_frac": sum(r["d30"] for r in miss) / max(num30, 1e-300),
            "flagged_numerator300_frac": sum(r["d300"] for r in miss) / max(num300, 1e-300),
            "same_class_at_300": sum(r["class300"] == r["class"] for r in recs),
            "same_class_and_roots_at_300": sum(r["class300"] == r["class"] and all(r["same_root_as_2000"]) for r in recs),
            "transitions_300_to_2000": trans,
            "cohort_vs_separate": {"cohort_and_separate": sum("cohort" in r["groups"] and r["class"] == "separate states" for r in recs),
                                   "cohort": sum("cohort" in r["groups"] for r in recs),
                                   "separate": sum(r["class"] == "separate states" for r in recs)}}
        flagged[gname] = res["graphs"][gname]
    total = sum(g["pilot_genomes"] for g in flagged.values())
    r1 = [g["R1"] for g in flagged.values()]
    s1 = sum(x["settled300"] for x in r1)
    res["checks"]["R1"] = {"fraction": sum(x["both_reach_stable"] for x in r1) / s1 if s1 else None,
                           "passes": bool(s1 and sum(x["both_reach_stable"] for x in r1) / s1 >= 0.95)}
    res["checks"]["R2"] = {"overall_frac": len(unresolved) / total,
                           "passes": bool(len(unresolved) / total <= 0.05
                                          and all(g["unresolved_frac"] <= 0.05 and g["unresolved_numerator30_frac"] <= 0.10
                                                  for g in flagged.values()))}
    agree = {}
    for gname in GRAPHS:
        r3 = json.load(open(OUT / f"r3__{gname}.json"))
        recs = {r["genome"]: r for r in json.load(open(OUT / f"classes__{gname}.json"))["genomes"]}
        n30 = sum(r["d30"] for r in recs.values())
        n300 = sum(r["d300"] for r in recs.values())
        for v, rec in r3["variants"].items():
            a = agree.setdefault(v, {"same": 0, "n": 0, "basin_changes": [], "num30": 0.0, "num300": 0.0, "tot30": 0.0,
                                     "tot300": 0.0})
            a["tot30"] += n30
            a["tot300"] += n300
            for k, (m, x) in enumerate(zip(r3["main_classes"], rec["classes"])):
                gid = r3["representatives"][k]
                a["same"] += m == x
                a["n"] += 1
                switched = m.startswith("separate states") and not all(rec["same_root"][k])
                if switched:
                    a["basin_changes"].append({"graph": gname, "genome": gid})
                if m != x or switched:  # a basin switch with an unchanged class is flagged too (Astra, round 7)
                    a["num30"] += recs[gid]["d30"]
                    a["num300"] += recs[gid]["d300"]
    res["checks"]["R3"] = {v: {"agreement": a["same"] / a["n"] if a["n"] else None, "basin_changes": a["basin_changes"],
                               "discordant_numerator30_frac": a["num30"] / max(a["tot30"], 1e-300),
                               "discordant_numerator300_frac": a["num300"] / max(a["tot300"], 1e-300)}
                           for v, a in agree.items()}
    res["checks"]["R3"]["passes"] = all(x["agreement"] is not None and x["agreement"] >= 0.95 and not x["basin_changes"]
                                        for k, x in res["checks"]["R3"].items() if k != "passes")
    rows = [row for gname in GRAPHS for rt in json.load(open(OUT / f"r4__{gname}.json"))["roots"] for row in rt["rows"]]
    failed = {(gname, rt["genome"]) for gname in GRAPHS for rt in json.load(open(OUT / f"r4__{gname}.json"))["roots"]
              if any(row["verdict"] == "does not return" for row in rt["rows"])}
    allrec = {(gname, r["genome"]): r for gname in GRAPHS for r in json.load(open(OUT / f"classes__{gname}.json"))["genomes"]}
    tot30 = sum(r["d30"] for r in allrec.values())
    tot300 = sum(r["d300"] for r in allrec.values())
    res["checks"]["R4"] = {"tests": len(rows), "returns": sum(r["verdict"] == "returns" for r in rows),
                           "does_not_return": sum(r["verdict"] == "does not return" for r in rows),
                           "inconclusive": sum(r["verdict"] == "inconclusive" for r in rows),
                           "small_basin": sum(r["verdict"] == "small basin" for r in rows),
                           "small_basin_by_size": {str(z): sum(r["verdict"] == "small basin" and r["size"] == z for r in rows)
                                                   for z in (1e-8, 1e-6, 1e-4)},
                           "flagged_numerator30_frac": sum(allrec[k]["d30"] for k in failed) / max(tot30, 1e-300),
                           "flagged_numerator300_frac": sum(allrec[k]["d300"] for k in failed) / max(tot300, 1e-300),
                           "passes": all(r["verdict"] != "does not return" for r in rows)}
    res["checks"]["R4p"] = {k: v for k, v in load("r4p.json").items() if k != "checks"}
    r5 = [x for gname in GRAPHS for x in json.load(open(OUT / f"r5__{gname}.json"))["genomes"]]
    res["checks"]["R5"] = {"genomes": len(r5), "more_than_two_states": sum(x["distinct_stable_roots"] > 2 for x in r5),
                           "distribution": {k: sum(x["distinct_stable_roots"] == k for x in r5)
                                            for k in sorted({x["distinct_stable_roots"] for x in r5})}}
    res["checks"]["R6"] = load("r6.json")
    # descriptive (the plan): M1's tanh-consistent midpoint forecast of r(30) against the observed r(30), per class; and
    # the fading genomes' predicted against observed late slopes
    from scipy.stats import spearmanr
    desc = {}
    for k in sorted({r["class"] for r in allrec.values()}):
        rr = [r for r in allrec.values() if r["class"] == k and r["a"] > 0]
        if len(rr) >= 5:
            desc[k] = {"genomes": len(rr), "spearman_forecast_r30": float(spearmanr([r["fore30"] for r in rr],
                                                                                    [r["d30"] / r["a"] for r in rr]).correlation)}
    fm = [r["fading_modes"] for r in allrec.values() if r.get("fading_modes")]
    pairs = [(m["observed_slope"], m["predicted_slope"]) for m in fm if None not in (m["observed_slope"], m["predicted_slope"])]
    res["descriptive"] = {"forecast_by_class": desc,
                          "fading_slopes": {"genomes": len(fm), "with_both_slopes": len(pairs),
                                            "median_observed": float(np.median([p[0] for p in pairs])) if pairs else None,
                                            "median_predicted": float(np.median([p[1] for p in pairs])) if pairs else None,
                                            "median_abs_difference": float(np.median([abs(p[0] - p[1]) for p in pairs])) if pairs else None,
                                            "cancellations": sum(m["cancellation"] for m in fm)},
                          # fading genomes whose float32 stall would pass 03mc's "remaining" (|dy(300)| > 0.1 a), and of
                          # those, how many sit in M1's settling cohort without separate states
                          "float32_stall": {
                              "fading_genomes": len(fm),
                              "stationary_stalls": sum(m["stall_stationary"] for m in fm),
                              "stall2000_above_remaining": sum(r["fading_modes"]["float32_stall_dy2000"] > K.REMAIN * r["a"]
                                                               and r["fading_modes"]["stall_stationary"]
                                                               for r in allrec.values() if r.get("fading_modes")),
                              "dy300_above_remaining": sum(r["fading_modes"]["float32_dy300"] > K.REMAIN * r["a"]
                                                           for r in allrec.values() if r.get("fading_modes")),
                              # the contamination of M1's cohort: fading genomes in it whose stationary tick-2000 stall
                              # passes 0.1 a (Fable, Astra, round 8; |dy(300)| >= 0.1 a holds for every cohort member)
                              "stall2000_above_remaining_in_cohort": sum(
                                  r["fading_modes"]["float32_stall_dy2000"] > K.REMAIN * r["a"]
                                  and r["fading_modes"]["stall_stationary"] and "cohort" in r["groups"]
                                  for r in allrec.values() if r.get("fading_modes")),
                              "fading_in_cohort": sum("cohort" in r["groups"] for r in allrec.values() if r.get("fading_modes")),
                              "median_stall_dy2000": float(np.median([m["float32_stall_dy2000"] for m in fm])) if fm else None},
                          # does the cheaper rule (a located, accurate root within 1e-3 of the tick-2000 state) agree with
                          # the float64 continuation's verdict? Per history (Fable, round 7)
                          "cheap_rule": cheap_rule(allrec)}
    dump(res, "summary.json")
    print(json.dumps({k: v.get("passes") if isinstance(v, dict) else v for k, v in res["checks"].items()}))


STAGES = {"sample": stage_sample, "main": stage_main, "classify": stage_classify, "r3": stage_r3, "r4": stage_r4,
          "r4p": stage_r4p, "r5": stage_r5, "r6": stage_r6, "summary": stage_summary}

if __name__ == "__main__":
    todo = sys.argv[1:] or list(STAGES)
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M2-pilot",
                       script="pilot.py", argv=sys.argv[1:]):
        for st in todo:
            t0 = time.time()
            STAGES[st]()
            print("stage", st, round(time.time() - t0, 1), "s", flush=True)
