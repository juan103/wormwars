"""M5's power calculation (docs/memory/M5-POWER-DESIGN.md, draft 4): a simulation of the whole reading procedure,
on counts.

The model (section 2): per arm, host and draw, a multinomial first pass over separate states, unresolved, persistent
oscillation and fading, with logit-normal host propensities (a shared part and an arm part, their correlation rho;
the same logit variance in both arms) and a block-draw term in Rr only; a first-to-final table for the second pass;
the audit's A ids drawn from the panel before classification, with latent fading-to-separate transitions; effects
calibrated so that the expected raw protocol contrast is delta. The reading (section 1) is m5_reading's, vectorised
over runs in the balanced case. Costs (section 6) come from the pilot's panel times, coupled to each panel's
difficulty. Rules A, B and C (section 5) are built on fixed-H power and the two-stage simulation.

Stages: fit (the pilot's inputs and the fits), check (the calibration check), families (A's and B's candidate and
confirmation per allocation, 80% and 90%), nulls, scenarios, c (rule C), report. Each writes its part of
runs/memory-m5-power/power.json, so a stage can be rerun alone.

Usage: python scripts/memory_m5/m5_power.py [stage ...]      (no stage: all, in order)
"""

from __future__ import annotations

import json
import os
import sys
import time
import warnings
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

import numpy as np
from scipy import optimize, special, stats

sys.path.insert(0, str(Path(__file__).parent))
import m5_reading as MR  # noqa: E402

# The reading is D372's (the Welch t in the balanced hull). M5_WELCH_TOO=0 reruns the reading as first written, the
# comparison kept in runs/memory-m5-power/; the default is the adopted reading, kept in runs/memory-m5-power-welch/.
MR.WELCH_TOO = os.environ.get("M5_WELCH_TOO", "1") != "0"

ROOT = Path(__file__).resolve().parents[2]
PILOT = ROOT / "runs" / "memory-m5-pilot"
M4E = ROOT / "runs" / "memory-m4e"


def default_out(env):
    """Each reading's own folder unless M5_POWER_OUT names one (Astra, results round 3: stage C reuses a folder's cached
    allocation search, so the two readings must not share one)."""
    if env.get("M5_POWER_OUT"):
        return Path(env["M5_POWER_OUT"])
    plain = env.get("M5_WELCH_TOO", "1") == "0"
    return ROOT / "runs" / ("memory-m5-power" if plain else "memory-m5-power-welch")


OUT = default_out(os.environ)

SEED = 20264501  # the simulation's family (above the pilot's 2026410x to 2026430x and the reader's 20264401)
TAU = {"T": 0.00131133, "Rr": 0.00130961}  # the per-arm pooled audit bounds (M5-PILOT-RESULTS.md, "(c)")
RATE_RR, RATE_SENS = 0.0058, (0.0031, 0.0090)
TARGETS = {"min": None, "half": 7.6e-6, "core": 1.52e-5, "above": 3.0e-5}
DRAW_TK = 4.5850872993469245e-06  # M4e's T - K draw component, labelled K's (Fable)
DELTAS = (0.0, 0.001, 0.002, 0.003, 0.004)
PLAN_DELTA = 0.002
ENRICH = 0.002  # the latent scenarios' share of latent switches classified unresolved
PM = 0.004  # the nulls' host effects
CONT_SECS = 3.6  # one audited fading genome's continuation to 22,000 ticks (the pilot's (c), 3.3 to 3.7 s)
HOSTS = tuple(range(10, 155, 5))
HOSTS_WIDE = tuple(range(10, 305, 5))
ALLOCS = tuple((d, g, a) for d in (1, 2) for g in (512, 1024) for a in (40, 80, 160))
CAP_MULT = 1.5
PRIOR_AUDIT = {"T": 2283, "Rr": 2286}  # the per-arm audits so far, M4e's and the pilot's, none with a transition
R_COARSE, R_REFINE, R_CONFIRM, R_NULL, R_SCEN, R_TABLE = 400, 4000, 10_000, 40_000, 4000, 2000
N_FIT = 200_000  # hosts sampled for the calibrations' expectations
GH_X, GH_W = np.polynomial.hermite_e.hermegauss(40)
GH_W = GH_W / GH_W.sum()
ARMS = ("T", "Rr")


# =========================================================================================================== inputs
def pilot_inputs():
    """The pilot's first-pass and merged counts per panel (report.json), the first-to-final table from the panel
    records (T: M4e's records; Rr: the pilot's; K's first-pass unresolved for the unresolved-to-separate path)."""
    rep = json.loads((PILOT / "report.json").read_text(encoding="utf-8"))
    out = {"panels": {}}
    for arm in ARMS:
        rows = []
        for key, v in rep["counts"][arm].items():
            name, d = key.rsplit(" d", 1)
            fp = v["first_pass_classes"]
            rows.append({"host": name, "draw": int(d), "S1": fp["separate states"] + fp["separate states, read-out silent"],
                         "U1": fp["unresolved"], "O1": fp["persistent oscillation"], "F1": fp["fading"],
                         "S": v["separate"], "U": v["unresolved"], "seconds": v["panel_seconds"]})
        out["panels"][arm] = rows
    table = {}
    for arm, pat in (("T", M4E / "arms"), ("Rr", PILOT / "arms"), ("K", M4E / "arms")):
        tab = {"F": 0, "O": 0, "U": 0, "S": 0}
        for f in sorted(pat.glob(f"*__{arm}.json")):
            r = json.loads(f.read_text(encoding="utf-8"))
            fin = dict(zip(r["second"]["ids"], r["second"]["class"]))
            for i, c in enumerate(r["class"]):
                if c == 4:
                    tab[{0: "S", 1: "S", 2: "F", 3: "O", 4: "U"}[fin[i]]] += 1
        table[arm] = tab
    n_u = sum(sum(t.values()) for t in table.values())
    out["first_to_final"] = table
    out["u_to_s"] = sum(t["S"] for t in table.values()) / n_u
    v = rep["at_22000"]["T_minus_Rr"]["variance"]
    out["draw_component"] = v["draw"]
    out["pilot"] = {"sd": rep["at_22000"]["T_minus_Rr"]["variance"]["sd_of_host_contrasts"],
                    "interval": rep["at_22000"]["T_minus_Rr"]["interval"]}
    return out


def host_sums(rows, key):
    names = sorted({r["host"] for r in rows})
    return np.array([sum(r[key] for r in rows if r["host"] == h) for h in names], float), names


# ============================================================================================================ fits
def mean_p(mu, sd, sd_v=0.0):
    """E[expit(mu + sd z + sd_v v)], z and v standard normal (Gauss-Hermite)."""
    x = mu + sd * GH_X[:, None] + sd_v * GH_X[None, :]
    return float((special.expit(x) * GH_W[:, None] * GH_W[None, :]).sum())


def solve_mu(rate, sd, sd_v=0.0):
    return optimize.brentq(lambda m: mean_p(m, sd, sd_v) - rate, -20.0, 5.0, xtol=1e-12)


def count_var(rate, sd, n, draws=2, sd_v=0.0):
    """The variance of a host's count over n genomes in `draws` draws, logit-normal host propensity (sd) and a draw
    term (sd_v): n E[p(1-p)] + (n/D)^2 (D E_u Var_v p + D^2 Var_u E_v p)."""
    mu = solve_mu(rate, sd, sd_v)
    x = mu + sd * GH_X[:, None] + sd_v * GH_X[None, :]
    p = special.expit(x)
    w = GH_W[:, None] * GH_W[None, :]
    e_pq = (p * (1 - p) * w).sum()
    ev = (p * GH_W[None, :]).sum(1)
    var_v = ((p - ev[:, None]) ** 2 * GH_W[None, :]).sum(1)
    m = n / draws
    return float(n * e_pq + m * m * (draws * (var_v * GH_W).sum() + draws ** 2 * ((ev - rate) ** 2 * GH_W).sum()))


def fit_sd(counts, n, draws=2, sd_v=0.0):
    """The logit sd whose predicted host-count variance equals the observed one (0 if at or below binomial)."""
    rate, obs = counts.mean() / n, counts.var(ddof=1)
    if rate <= 0 or obs <= count_var(rate, 1e-9, n, draws, sd_v):
        return 0.0
    return float(optimize.brentq(lambda s: count_var(rate, s, n, draws, sd_v) - obs, 1e-9, 5.0, xtol=1e-10))


def fit_draw_sd(component, rate, sd):
    """Rr's block-draw sd: E_u Var_v(expit(mu + u + v)) equals the pilot's draw component (per draw of 512)."""
    def f(sv):
        mu = solve_mu(rate, sd, sv)
        p = special.expit(mu + sd * GH_X[:, None] + sv * GH_X[None, :])
        ev = (p * GH_W[None, :]).sum(1)
        return float((((p - ev[:, None]) ** 2 * GH_W[None, :]).sum(1) * GH_W).sum()) - component
    return float(optimize.brentq(f, 1e-6, 3.0, xtol=1e-10))


def latent_corr(a, b, n):
    """The correlation of two arms' host propensities implied by their host counts, binomial noise removed, clipped
    to [0, 1]."""
    pa, pb = a.mean() / n, b.mean() / n
    va = a.var(ddof=1) - n * pa * (1 - pa)
    vb = b.var(ddof=1) - n * pb * (1 - pb)
    if va <= 0 or vb <= 0:
        return 0.0
    return float(np.clip(np.cov(a, b)[0, 1] / np.sqrt(va * vb), 0.0, 1.0))


def fit(inp=None):
    inp = inp or pilot_inputs()
    n = 1024
    f = {}
    for cls in ("S1", "U1", "O1"):
        sums = {a: host_sums(inp["panels"][a], cls)[0] for a in ARMS}
        f[cls] = {"rate": {a: float(sums[a].sum() / (len(sums[a]) * n)) for a in ARMS},
                  "sd": {a: fit_sd(sums[a], n) for a in ARMS},
                  "rho": latent_corr(sums["T"], sums["Rr"], n),
                  "count_var": {a: float(sums[a].var(ddof=1)) for a in ARMS},
                  "count_corr": float(np.corrcoef(sums["T"], sums["Rr"])[0, 1])}
    s = f["S1"]
    # Rr's host sd and its block-draw sd, fitted jointly (Astra, results round 1: Rr's host sd fitted without the
    # draw term counted the draw variation twice once the draw term was added): alternate until both hold.
    sums_r = host_sums(inp["panels"]["Rr"], "S1")[0]
    s["sd_Rr_without_draw"] = sd_r = s["sd"]["Rr"]
    sd_v = 0.0
    for _ in range(100):
        sd_v_new = fit_draw_sd(inp["draw_component"], s["rate"]["Rr"], sd_r)
        sd_r_new = fit_sd(sums_r, n, sd_v=sd_v_new)
        done = abs(sd_r_new - sd_r) < 1e-12 and abs(sd_v_new - sd_v) < 1e-12
        sd_r, sd_v = sd_r_new, sd_v_new
        if done:
            break
    s["sd"]["Rr"] = sd_r
    s["sd_pooled"] = float(np.sqrt((s["sd"]["T"] ** 2 + s["sd"]["Rr"] ** 2) / 2))
    sd_v_tk = fit_draw_sd(DRAW_TK, RATE_RR, s["sd_pooled"])
    tab = inp["first_to_final"]
    second = {}
    for a in ARMS:
        t = tab[a]
        tot = sum(t.values())
        second[a] = {"S": inp["u_to_s"], "F": t["F"] / tot, "O": t["O"] / tot}
        second[a]["U"] = 1.0 - second[a]["S"] - second[a]["F"] - second[a]["O"]
    times = fit_times(inp)
    return {"classes": f, "sd_v": sd_v, "sd_v_tk": sd_v_tk, "second": second, "u_to_s": inp["u_to_s"],
            "first_to_final": tab, "times": times, "pilot": inp["pilot"]}


def fit_times(inp):
    """Per arm: panel seconds = a + b U1 + c (S1 + U1 + O1) (least squares on the pilot's 20 panels), the residuals
    kept by pilot host and draw (whole-host resampling), and the audit's share of the intercept."""
    out = {}
    hosts = sorted({r["host"] for r in inp["panels"]["T"]})
    for a in ARMS:
        rows = sorted(inp["panels"][a], key=lambda r: (hosts.index(r["host"]), r["draw"]))
        X = np.array([[1.0, r["U1"], r["S1"] + r["U1"] + r["O1"]] for r in rows])
        y = np.array([r["seconds"] for r in rows])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        res = (y - X @ coef).reshape(len(hosts), 2)
        audited = 40 * np.mean([r["F1"] / 512 for r in rows])  # the pilot's audit: 40 ids, the fading ones continued
        out[a] = {"coef": coef.tolist(), "residuals": res.tolist(), "raw": y.reshape(len(hosts), 2).tolist(),
                  "audit_seconds": float(audited * CONT_SECS), "corr_seconds_U1": float(np.corrcoef(y, X[:, 1])[0, 1])}
    return out


# ========================================================================================================= the model
@dataclass(frozen=True)
class Scenario:
    """Everything a simulated M5 run depends on except the allocation."""
    target: str = "min"  # the host-variance scenario (TARGETS), solved for rho / scale at RATE_RR
    rate_rr: float = RATE_RR
    rho: float | None = None  # set by solve(); None until then
    scale: float = 1.0  # the logit variance's multiplier (above the ceiling)
    extra_w: float = 0.0  # draft 1's parametrisation: an added independent arm sd
    draw: str = "pilot"  # "pilot", "zero" or "tk"
    tau: str = "symmetric"  # "symmetric", "zero", "Rr", "T", "host", "host_T", "host_Rr", "panel"
    spread: str = "constant"  # "constant", "proportional", "uniform", "sparse", "ensemble", "pm", "ens_null"
    delta: float = PLAN_DELTA
    latent: str = "none"  # "none", "Rr", "T": latent switches classified unresolved
    su_corr: float = 0.0  # the correlation of the unresolved and separate-states shared propensities
    invalid: float = 0.0  # the per-panel invalidity
    times: str = "coupled"  # "coupled" or "whole_host"
    ens_sd: str = "equal"  # "equal" or "unequal": the five ensembles' host spreads scaled 0.5 to 1.5
    overhead: bool = False  # the pilot's unattributed 12.6% added

    def label(self):
        return ",".join(f"{k}={v}" for k, v in asdict(self).items() if k != "rho")


@dataclass
class Model:
    fitted: dict
    sc: Scenario
    alloc: tuple  # (D, G, A)
    mu: dict = field(default_factory=dict)
    inc: float = 0.0  # the effect term (an increment, or a logit shift for "proportional")

    @property
    def sd(self):
        return self.fitted["classes"]["S1"]["sd_pooled"] * np.sqrt(self.sc.scale)

    @property
    def sd_v(self):
        return {"pilot": self.fitted["sd_v"], "zero": 0.0, "tk": self.fitted["sd_v_tk"]}[self.sc.draw]


def make_model(fitted, sc, alloc):
    m = Model(fitted, sc, alloc)
    c = fitted["classes"]
    sd_tot = np.sqrt(m.sd ** 2 + sc.extra_w ** 2)
    m.mu = {"S": {"T": solve_mu(sc.rate_rr, sd_tot), "Rr": solve_mu(sc.rate_rr, sd_tot, m.sd_v)}}
    for cls, key in (("U", "U1"), ("O", "O1")):
        m.mu[cls] = {a: solve_mu(c[key]["rate"][a], c[key]["sd"][a]) for a in ARMS}
    m.inc = calibrate(m)
    return m


def tau_of(m, arm):
    return {"zero": 0.0, "T": TAU["T"] if arm == "T" else 0.0, "Rr": TAU["Rr"] if arm == "Rr" else 0.0,
            "host_T": TAU["T"] if arm == "T" else 0.0, "host_Rr": TAU["Rr"] if arm == "Rr" else 0.0}.get(
        m.sc.tau, TAU[arm])


# ---------------------------------------------------------------------------------------------- one batch of runs
def draw_hosts(m, rng, R, H):
    """The host effects: z (shared) and e (per arm) for separate states, and the unresolved and oscillation
    propensities; ensembles host % 5."""
    sc = m.sc
    rho = 1.0 if sc.rho is None else sc.rho
    z = rng.standard_normal((R, H))
    eT, eR = rng.standard_normal((R, H)), rng.standard_normal((R, H))
    logit_s = {"T": m.sd * (np.sqrt(rho) * z + np.sqrt(1 - rho) * eT),
               "Rr": m.sd * (np.sqrt(rho) * z + np.sqrt(1 - rho) * eR)}
    if sc.extra_w:
        logit_s = {a: v + sc.extra_w * rng.standard_normal((R, H)) for a, v in logit_s.items()}
    if sc.ens_sd == "unequal":  # the ensembles' host spreads differ (the unbalanced reading's coverage check)
        mult = np.array([0.5, 0.75, 1.0, 1.25, 1.5])[np.arange(H) % 5]
        logit_s = {a: v * mult for a, v in logit_s.items()}
    c = m.fitted["classes"]
    zu = sc.su_corr * z + np.sqrt(1 - sc.su_corr ** 2) * rng.standard_normal((R, H))
    out = {"S": logit_s}
    for cls, key, zs in (("U", "U1", zu), ("O", "O1", rng.standard_normal((R, H)))):
        r_ = c[key]["rho"]
        out[cls] = {a: c[key]["sd"][a] * (np.sqrt(r_) * zs + np.sqrt(1 - r_) * rng.standard_normal((R, H)))
                    for a in ARMS}
    return out


def effect_weights(m, rng, R, H):
    """Each host's effect: (to T, to Rr) multipliers of the increment, or the null's fixed effects."""
    sp = m.sc.spread
    ens = np.arange(H) % 5
    gT, gR = np.ones((R, H)), np.zeros((R, H))
    if m.sc.delta < 0:  # a negative effect raises Rr, so no probability is clipped
        gT, gR = gR, gT
    fixed_T, fixed_R = np.zeros((R, H)), np.zeros((R, H))
    if sp == "uniform":
        gT = rng.uniform(0, 2, (R, H))
    elif sp == "sparse":
        gT = 5.0 * (rng.random((R, H)) < 0.2)
    elif sp == "ensemble":
        gT = np.broadcast_to(5.0 * (ens == 0), (R, H)).copy()
    elif sp == "pm":
        up = rng.random((R, H)) < 0.5
        fixed_T, fixed_R = PM * up, PM * ~up
    elif sp == "ens_null":
        fixed_T = np.broadcast_to(PM * (ens <= 1), (R, H)).copy()
        fixed_R = np.broadcast_to(PM * ((ens == 2) | (ens == 3)), (R, H)).copy()
    return gT, gR, fixed_T, fixed_R


def first_pass_probs(m, he, eff, rng, R, H, D):
    """(R, H, D) first-pass probabilities per arm and class."""
    gT, gR, fT, fR = eff
    v = m.sd_v * rng.standard_normal((R, H, D))
    p = {}
    for a in ARMS:
        x = m.mu["S"][a] + he["S"][a][..., None] + (v if a == "Rr" else 0.0)
        if m.sc.spread == "proportional" and a == "T":
            x = x + m.inc
        pS = special.expit(x)
        if m.sc.spread != "proportional":
            pS = pS + (m.inc * (gT if a == "T" else gR))[..., None]
        pS = np.broadcast_to(pS + (fT if a == "T" else fR)[..., None], (R, H, D))
        pU = np.broadcast_to(special.expit(m.mu["U"][a] + he["U"][a])[..., None], (R, H, D))
        pO = np.broadcast_to(special.expit(m.mu["O"][a] + he["O"][a])[..., None], (R, H, D))
        pL = np.full((R, H, D), ENRICH if m.sc.latent == a else 0.0)
        p[a] = {"S": np.clip(pS, 0.0, 1.0), "U": pU, "O": pO, "L": pL}
    return p


def simulate(m, rng, R, H):
    """R runs of H hosts: per host (summed over its D draws) the raw confirmed counts, the final unresolved counts,
    the unaudited first-pass fading counts, the audited fading counts and transitions, the hidden transitions and
    latent switches, the first-pass unresolved and non-fading counts (for the cost), and the panel seconds."""
    D, G, A = m.alloc
    he = draw_hosts(m, rng, R, H)
    eff = effect_weights(m, rng, R, H)
    p = first_pass_probs(m, he, eff, rng, R, H, D)
    sec = m.fitted["second"]
    out = {"rejected": 0}
    host_k = rng.integers(0, 10, (R, H))  # the pilot host whose residuals a simulated host takes
    for a in ARMS:
        pa = p[a]
        probs = np.stack([pa["S"], pa["U"], pa["L"], pa["O"]], -1)
        bad = probs.sum(-1) > 0.2
        out["rejected"] += int(bad.sum())
        probs = np.where(bad[..., None], probs * (0.2 / probs.sum(-1, keepdims=True)), probs)
        probs = np.concatenate([probs, 1.0 - probs.sum(-1, keepdims=True)], -1)
        S1, U1, L, O1, F1 = first_pass_counts(rng, G, probs)
        aud = audit_draw(rng, F1, G, A)
        tau = tau_panel(m, a, rng, R, H, D)
        trans = rng.binomial(aud, tau)
        hidden = rng.binomial(F1 - aud, tau)
        fin = rng.multinomial(U1, [sec[a]["S"], sec[a]["F"], sec[a]["O"], sec[a]["U"]])
        uS, uF, uO, uU = (fin[..., i] for i in range(4))
        S = S1 + uS + trans
        Ufin = uU + L
        out[a] = {"S": S.sum(-1), "U": Ufin.sum(-1), "Fun": (F1 - aud).sum(-1), "aud": aud.sum(-1),
                  "trans": trans.sum(-1), "hidden": hidden.sum(-1), "L": L.sum(-1), "U1": U1.sum(-1),
                  "uF": uF.sum(-1),
                  "seconds": panel_seconds(m, a, U1 + L, S1 + U1 + L + O1, aud, host_k, rng).sum(-1)}
    if m.sc.invalid:
        out["invalid"] = (rng.random((R, H, 2 * D)) < m.sc.invalid).any(-1)
    return out


def audit_draw(rng, F1, G, A):
    """The first-pass fading genomes among a panel's A audit ids, drawn from all G before classification (M4e's)."""
    return rng.hypergeometric(F1, G - F1, A)


def first_pass_counts(rng, G, probs):
    """One multinomial per panel (Astra: coherent counts): S1, U1, L (latent switches, classified unresolved), O1, F1."""
    cnt = rng.multinomial(G, probs)
    return tuple(cnt[..., i] for i in range(5))


def tau_panel(m, arm, rng, R, H, D):
    t = tau_of(m, arm)
    if m.sc.tau in ("host", "host_T", "host_Rr"):
        return np.broadcast_to(((rng.random((R, H)) < 0.2) * 5 * t)[..., None], (R, H, D))
    if m.sc.tau == "panel":
        return (rng.random((R, H, D)) < 0.2) * 5 * t
    return np.full((R, H, D), t)


def panel_seconds(m, arm, U1, NF1, aud, host_k, rng):
    """A panel's seconds: the pilot's regression on its difficulty (first-pass unresolved and non-fading counts), the
    first pass and the fixed part scaled by G/512, the audit at the allocation's size, plus a residual from the pilot
    host the simulated host resamples (both arms and draws together). "whole_host": the pilot's raw panel times."""
    D, G, A = m.alloc
    t = m.fitted["times"][arm]
    if m.sc.times == "whole_host":
        return (np.asarray(t["raw"])[host_k][..., :D] - t["audit_seconds"]) * G / 512 + aud * CONT_SECS
    r = np.asarray(t["residuals"])[host_k][..., :D]  # (10 pilot hosts, 2 draws)
    a0, b, c = t["coef"]
    return (a0 - t["audit_seconds"] + r) * G / 512 + b * U1 + c * NF1 + aud * CONT_SECS


# ------------------------------------------------------------------------------------------- calibrating the effect
def expected_raw(m, inc, arm):
    """E[raw confirmed share] of one arm at effect term inc, by quadrature, exactly: each class's mean propensity is
    its solved rate, an increment's host weights average 1 (H a multiple of 5), and the fixed null effects average
    their probabilities. (A sample of hosts, as draft code had it, left a bias of about 1e-5 at delta = 0, enough to
    move the false "raises" rate by a tenth.)"""
    D, G, A = m.alloc
    c = m.fitted["classes"]
    sp = m.sc.spread
    if sp == "proportional" and arm == "T":
        sd_tot = np.sqrt(m.sd ** 2 + m.sc.extra_w ** 2)
        pS = mean_p(m.mu["S"]["T"] + inc, sd_tot)
    else:
        pS = m.sc.rate_rr
        to_T = m.sc.delta >= 0
        if sp != "proportional" and (arm == "T") == to_T:
            pS += inc
    if sp == "pm":
        pS += PM / 2
    elif sp == "ens_null":
        pS += PM * 2 / 5
    pU, pO = c["U1"]["rate"][arm], c["O1"]["rate"][arm]
    pL = ENRICH if m.sc.latent == arm else 0.0
    pF = 1.0 - pS - pU - pO - pL
    return float(pS + pU * m.fitted["second"][arm]["S"] + tau_of(m, arm) * pF * A / G)


def calibrate(m):
    """The effect term giving an expected raw protocol contrast of delta (Astra: on the whole protocol), exactly. For
    the nulls ("pm", "ens_null") delta is 0 and the term only removes the base contrast."""
    delta = 0.0 if m.sc.spread in ("pm", "ens_null") else m.sc.delta

    def gap(inc):
        return expected_raw(m, inc, "T") - expected_raw(m, inc, "Rr") - delta
    if m.sc.spread == "proportional":
        return float(optimize.brentq(gap, -3.0, 3.0, xtol=1e-14))
    g0, g1 = gap(0.0), gap(1e-3)
    return float(-g0 * 1e-3 / (g1 - g0))  # gap is linear in an increment


# ---------------------------------------------------------------------------------------- the host-variance scenarios
def host_component(fitted, rate, sd, rho, sd_v, n=None, seed=None, extra_w=0.0):
    """Var_h(pbar_T,h - pbar_Rr,h) at zero effect on draw-averaged probabilities, by Gauss-Hermite quadrature over the
    shared part, each arm's own part and Rr's draw (Astra, results round 1: a sample of 200,000 hosts gave 1.5200e-5
    where quadrature gives 1.5102e-5). n and seed are ignored (kept for callers)."""
    sd_tot = np.sqrt(sd ** 2 + extra_w ** 2)
    muT, muR = solve_mu(rate, sd_tot), solve_mu(rate, sd_tot, sd_v)
    s_sh, s_in = sd * np.sqrt(rho), np.sqrt((1 - rho) * sd ** 2 + extra_w ** 2)
    x = s_sh * GH_X[:, None] + s_in * GH_X[None, :]  # (shared node, own node)
    pT = special.expit(muT + x)
    pR = (special.expit(muR + x[..., None] + sd_v * GH_X[None, None, :]) * GH_W).sum(-1)
    eT, eR = (pT * GH_W[None, :]).sum(1), (pR * GH_W[None, :]).sum(1)
    eT2, eR2 = (pT ** 2 * GH_W[None, :]).sum(1), (pR ** 2 * GH_W[None, :]).sum(1)
    mean = ((eT - eR) * GH_W).sum()
    second = ((eT2 - 2 * eT * eR + eR2) * GH_W).sum()
    return float(second - mean ** 2)


def solve_scenario(fitted, sc):
    """rho (and the scale above the ceiling) for the scenario's target at its rate; None if unreachable."""
    sd0 = fitted["classes"]["S1"]["sd_pooled"]
    sd_v = {"pilot": fitted["sd_v"], "zero": 0.0, "tk": fitted["sd_v_tk"]}[sc.draw]
    target = TARGETS[sc.target]
    if sc.extra_w:
        return sc
    if target is None:
        return replace(sc, rho=1.0, scale=1.0)
    hc = lambda rho, k=1.0: host_component(fitted, sc.rate_rr, sd0 * np.sqrt(k), rho, sd_v)  # noqa: E731
    lo, hi = hc(1.0), hc(0.0)
    if lo <= target <= hi:
        return replace(sc, rho=float(optimize.brentq(lambda r: hc(r) - target, 0.0, 1.0, xtol=1e-6)), scale=1.0)
    if target > hi:
        try:
            k = optimize.brentq(lambda k: hc(0.0, k) - target, 1.0, 6.0, xtol=1e-6)
        except ValueError:
            return None
        return replace(sc, rho=0.0, scale=float(k))
    return None


def solve_extra_w(fitted, sc, target=TARGETS["core"]):
    sd0 = fitted["classes"]["S1"]["sd_pooled"]
    w = optimize.brentq(lambda w: host_component(fitted, sc.rate_rr, sd0, 1.0, fitted["sd_v"], extra_w=w) - target,
                        1e-4, 3.0, xtol=1e-6)
    return replace(sc, rho=1.0, extra_w=float(w))


# ========================================================================================================= the reading
_W = {}


def weights(ens_key, b=MR.B):
    """The bootstrap's resampling matrix for a composition (ensemble labels), cached; fixed seed (MR.SEED_BOOT)."""
    if ens_key not in _W:
        _W[ens_key] = MR.resample_weights(np.array(ens_key), b, seed=MR.SEED_BOOT, stratified=True)
    return _W[ens_key]


def hull_parts(d, W, level=MR.LEVEL):
    """The balanced reading's parts for each row of d (R, H): the stratified bootstrap's ends, the estimate, the
    plain-s^2 t's half-width and the Welch t's."""
    H = d.shape[1]
    bm = d @ W.T
    q = 100 * (1 - level) / 2
    blo, bhi = np.percentile(bm, [q, 100 - q], axis=1)
    m = d.mean(1)
    half = stats.t.ppf(0.5 + level / 2, H - 1) * d.std(1, ddof=1) / np.sqrt(H)
    return blo, bhi, m, half, welch_half(d, np.arange(H) % 5, level)


def hull_batch(d, W, level=MR.LEVEL):
    """The balanced reading's hull for each row of d (R, H): the stratified bootstrap and the plain-s^2 t (and the
    Welch t under the proposal, MR.WELCH_TOO)."""
    blo, bhi, m, half, whalf = hull_parts(d, W, level)
    if MR.WELCH_TOO:
        half = np.maximum(half, whalf)
    return np.minimum(blo, m - half), np.maximum(bhi, m + half)


def welch_half(d, ens, level=MR.LEVEL):
    groups = [np.flatnonzero(ens == e) for e in range(MR.N_ENS)]
    a = np.stack([d[:, g].var(1, ddof=1) / (MR.N_ENS ** 2 * len(g)) for g in groups], 1)
    k = np.array([len(g) for g in groups])
    with np.errstate(divide="ignore", invalid="ignore"):
        df = np.where(a.sum(1) > 0, a.sum(1) ** 2 / (a ** 2 / (k - 1)).sum(1), k.min() - 1)
    return stats.t.ppf(0.5 + level / 2, df) * np.sqrt(a.sum(1))


def welch_batch(d, ens, W, level=MR.LEVEL):
    """The unbalanced reading's hull for each row of d: the stratified bootstrap and the Welch t."""
    groups = [np.flatnonzero(ens == e) for e in range(MR.N_ENS)]
    bm = d @ W.T
    q = 100 * (1 - level) / 2
    blo, bhi = np.percentile(bm, [q, 100 - q], axis=1)
    m = sum(d[:, g].mean(1) for g in groups) / MR.N_ENS
    a = np.stack([d[:, g].var(1, ddof=1) / (MR.N_ENS ** 2 * len(g)) for g in groups], 1)
    k = np.array([len(g) for g in groups])
    se = np.sqrt(a.sum(1))
    with np.errstate(divide="ignore", invalid="ignore"):
        df = np.where(a.sum(1) > 0, a.sum(1) ** 2 / (a ** 2 / (k - 1)).sum(1), k.min() - 1)
    half = stats.t.ppf(0.5 + level / 2, df) * se
    return np.minimum(blo, m - half), np.maximum(bhi, m + half)


def fixed_per_host(fitted, D):
    """A host's fixed CPU seconds: its build, D Rr blocks with their continued chains, and a tenth of M4e's
    verification of ten hosts (Astra, results round 1: draft code charged two blocks at D = 1 and no verification)."""
    f = fitted.get("fixed", {"host": 0.0, "block": 0.0, "verify_per_host": 0.0})
    return f["host"] + D * f["block"] + f["verify_per_host"]


def valid_hosts(sim):
    R, H = sim["T"]["S"].shape
    return ~sim["invalid"] if "invalid" in sim else np.ones((R, H), bool)


def contrasts(sim):
    """Per run and host, the numerator (in genomes) of each of MR.READINGS. The raw counts already hold the audited
    transitions; the audit adjustment adds each arm's pooled rate (transitions over audited first-pass fading
    genomes, every valid panel: an invalid host's audit is unusable, Astra, results round 2) times the host's
    unaudited first-pass fading genomes only, so nothing is counted twice; the unresolved sensitivities add
    MR.R_BOUND times the arm's unresolved genomes."""
    T, Rr = sim["T"], sim["Rr"]
    valid = valid_hosts(sim)
    tau_hat = {}
    for a in ARMS:
        aud = (sim[a]["aud"] * valid).sum(1)
        tau_hat[a] = np.where(aud > 0, (sim[a]["trans"] * valid).sum(1) / np.maximum(aud, 1), 0.0)
    adjT = T["S"] + tau_hat["T"][:, None] * T["Fun"]
    adjR = Rr["S"] + tau_hat["Rr"][:, None] * Rr["Fun"]
    uT, uR = MR.R_BOUND * T["U"], MR.R_BOUND * Rr["U"]
    return {"raw": T["S"] - Rr["S"], "audit": adjT - adjR, "unres_T": T["S"] + uT - Rr["S"],
            "unres_Rr": T["S"] - Rr["S"] - uR, "audit_unres_T": adjT + uT - adjR, "audit_unres_Rr": adjT - adjR - uR}


def readings(sim, m, H, cap=None, exclusion=True):
    """Per run: every reading's direction, the qualification, success, the envelope, the unresolved flag, the
    exclusion and the incomplete flag, with the latent and protocol contrasts and the cost."""
    D, G, A = m.alloc
    n = D * G
    T, Rr = sim["T"], sim["Rr"]
    R = T["S"].shape[0]
    num = contrasts(sim)
    seconds = T["seconds"].sum(1) + Rr["seconds"].sum(1) + H * fixed_per_host(m.fitted, D)
    if m.sc.overhead:
        seconds = seconds * 1.126
    out = {"seconds": seconds}
    valid = valid_hosts(sim)
    ens = np.arange(H) % 5
    counts_ok = np.stack([(valid & (ens == e)).sum(1) for e in range(5)], 1)
    complete = counts_ok.min(1) >= 2
    if cap is not None:
        complete &= seconds <= cap
    out["complete"] = complete
    if cap is not None:
        out["over_125"] = seconds > cap * 1.25 / CAP_MULT
    lo, hi = {}, {}
    all_valid = valid.all(1)
    W = weights(tuple(ens))
    for k, x in num.items():
        lo[k], hi[k] = np.full(R, np.nan), np.full(R, np.nan)
        if all_valid.any():
            lo[k][all_valid], hi[k][all_valid] = hull_batch(x[all_valid] / n, W)
    parts = {k: np.zeros(R, bool) for k in ("raw_boot_raises", "raw_t_raises", "raw_welch_raises", "raw_t_lowers")}
    if all_valid.any():  # the raw reading's parts, alone (balanced runs), for the null diagnosis (results round 1)
        blo, _, mm, half, whalf = hull_parts(num["raw"][all_valid] / n, W)
        parts["raw_boot_raises"][all_valid] = blo > 0
        parts["raw_t_raises"][all_valid] = mm - half > 0
        parts["raw_welch_raises"][all_valid] = mm - whalf > 0
        parts["raw_t_lowers"][all_valid] = mm + half < 0
    for k, v in parts.items():
        out[k] = v & complete
    for r in np.flatnonzero(~all_valid & (counts_ok.min(1) >= 2)):  # an invalid panel: the unbalanced reading
        keep = valid[r]
        e_r = ens[keep]
        Wr = weights(tuple(e_r))
        for k, x in num.items():
            iv = MR.interval(x[r, keep] / n, e_r, Wr)
            lo[k][r], hi[k][r] = iv
    raises = {k: lo[k] > 0 for k in num}
    out["raw_raises"] = raises["raw"] & complete
    out["raw_lowers"] = (hi["raw"] < 0) & complete
    single = raises["audit"] & raises["unres_T"] & raises["unres_Rr"]
    comb = raises["audit_unres_T"] & raises["audit_unres_Rr"]
    out["success"] = raises["raw"] & single & comb & complete
    out["q_audit"] = raises["raw"] & ~raises["audit"] & complete
    out["q_unres"] = raises["raw"] & ~(raises["unres_T"] & raises["unres_Rr"]) & complete
    out["q_comb_only"] = raises["raw"] & single & ~comb & complete
    out["lo_raw"], out["hi_raw"] = lo["raw"], hi["raw"]
    out["unbalanced"] = ~all_valid
    # the envelope (balanced runs), its crossing zero
    elo, ehi = np.full(R, np.nan), np.full(R, np.nan)
    if all_valid.any():
        dlo = (T["S"] - Rr["S"] - Rr["U"])[all_valid] / n
        dhi = (T["S"] + T["U"] - Rr["S"])[all_valid] / n
        elo[all_valid], ehi[all_valid] = envelope_batch(dlo, dhi, W)
    flag = np.zeros(R, bool)
    if all_valid.any():  # the unresolved-share flag: the hull of Rr's minus T's unresolved share above zero
        ulo, _ = hull_batch((Rr["U"] - T["U"])[all_valid] / n, W)
        flag[all_valid] = ulo > 0
    for r in np.flatnonzero(~all_valid & (counts_ok.min(1) >= 2)):  # an invalid panel: the unbalanced versions
        keep = valid[r]
        e_r = ens[keep]
        Wr = weights(tuple(e_r))
        elo[r], ehi[r] = MR.envelope((T["S"] - Rr["S"] - Rr["U"])[r, keep] / n,
                                     (T["S"] + T["U"] - Rr["S"])[r, keep] / n, e_r, Wr)
        flag[r] = MR.interval((Rr["U"] - T["U"])[r, keep] / n, e_r, Wr)[0] > 0
    out["envelope_crosses"] = (elo <= 0) & (ehi >= 0)
    out["unres_flag"] = flag
    # the exclusion at 0.002 with the leave-one-out guard
    out["exclusion"] = np.zeros(R, bool)
    if exclusion and H // 5 >= 3:
        inside = all_valid & (lo["raw"] > -PLAN_DELTA) & (hi["raw"] < PLAN_DELTA) & complete
        idx = np.flatnonzero(inside)
        ok = np.ones(len(idx), bool)
        d = num["raw"][idx] / n
        for j in range(H):
            keep = np.arange(H) != j
            e_j = ens[keep]
            l_, h_ = welch_batch(d[:, keep], e_j, weights(tuple(e_j)))
            ok &= (l_ > -PLAN_DELTA) & (h_ < PLAN_DELTA)
        out["exclusion"][idx] = ok
    if exclusion:  # after an invalid host: every leave-one-out reading must stay valid, so 3 valid per ensemble
        for r in np.flatnonzero(~all_valid & (counts_ok.min(1) >= 3) & complete & (lo["raw"] > -PLAN_DELTA)
                                & (hi["raw"] < PLAN_DELTA)):
            keepv = np.flatnonzero(valid[r])
            d = num["raw"][r] / n
            ok = True
            for j in keepv:
                kk = keepv[keepv != j]
                l_, h_ = MR.interval(d[kk], ens[kk], weights(tuple(ens[kk])))
                if not (l_ > -PLAN_DELTA and h_ < PLAN_DELTA):
                    ok = False
                    break
            out["exclusion"][r] = ok
    # the audit's bound and its coverage (per arm, the common rate), valid hosts only
    for a in ARMS:
        aud, tr = (sim[a]["aud"] * valid).sum(1), (sim[a]["trans"] * valid).sum(1)
        ub = np.where(aud > 0, stats.beta.ppf(0.95, tr + 1, np.maximum(aud - tr, 1)), 1.0)
        ub = np.where(tr >= aud, 1.0, ub)
        single_tau = m.sc.tau in ("zero", "symmetric", "T", "Rr")
        out[f"cover_tau_{a}"] = ub >= tau_of(m, a) if single_tau else None
        hidden_ub = ub * (sim[a]["Fun"] * valid).sum(1)
        out[f"cover_hidden_{a}"] = hidden_ub >= (sim[a]["hidden"] * valid).sum(1)
        pooled = stats.beta.ppf(0.95, tr + 1, aud + PRIOR_AUDIT[a] - tr)  # with the pilot's and M4e's audits (0 of n)
        out[f"cover_tau_pooled_{a}"] = pooled >= tau_of(m, a) if single_tau else None
    out["protocol"] = (T["S"] - Rr["S"]).mean(1) / n
    out["latent"] = ((T["S"] + T["hidden"] + T["L"]) - (Rr["S"] + Rr["hidden"] + Rr["L"])).mean(1) / n
    return out


def envelope_batch(dlo, dhi, W, level=MR.LEVEL):
    """The balanced envelope per row (MR.envelope, vectorised)."""
    H = dlo.shape[1]
    q = 100 * (1 - level) / 2
    blo = np.percentile(dlo @ W.T, q, axis=1)
    bhi = np.percentile(dhi @ W.T, 100 - q, axis=1)
    mlo, mhi = dlo.mean(1), dhi.mean(1)
    c = (mlo + mhi) / 2
    bound = np.maximum((dlo - c[:, None]) ** 2, (dhi - c[:, None]) ** 2).sum(1) / (H - 1)
    half = stats.t.ppf(0.5 + level / 2, H - 1) * np.sqrt(bound / H)
    if MR.WELCH_TOO:  # the per-ensemble bound at t(min n_e - 1), which holds every corner's Welch t
        ens = np.arange(H) % 5
        var = 0.0
        for e in range(MR.N_ENS):
            g = np.flatnonzero(ens == e)
            ce = (dlo[:, g].mean(1) + dhi[:, g].mean(1)) / 2
            var = var + np.maximum((dlo[:, g] - ce[:, None]) ** 2, (dhi[:, g] - ce[:, None]) ** 2).sum(1) / (
                (len(g) - 1) * MR.N_ENS ** 2 * len(g))
        half = np.maximum(half, stats.t.ppf(0.5 + level / 2, H // 5 - 1) * np.sqrt(var))
    return np.minimum(blo, mlo - half), np.maximum(bhi, mhi + half)


# ======================================================================================================== evaluation
def cell_seed(*parts):
    return np.random.default_rng([SEED] + [int(abs(hash_str(str(p)))) % (2 ** 31) for p in parts])


def hash_str(s):
    import hashlib
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)


def run_cell(m, H, R, *seed_parts, cap=None, batch=2000, exclusion=False):
    """R runs at H hosts, in batches; returns the summed readings."""
    rng = cell_seed(m.sc.label(), m.alloc, H, R, *seed_parts)
    acc = {}
    done = 0
    capped = 0
    while done < R:
        r = min(batch, R - done)
        sim = simulate(m, rng, r, H)
        capped += sim["rejected"]
        out = readings(sim, m, H, cap=cap, exclusion=exclusion)
        for k, v in out.items():
            if v is None:
                continue
            acc.setdefault(k, []).append(v)
        done += r
    res = {k: np.concatenate(v) for k, v in acc.items()}
    res["capped"] = np.array([capped])
    return res


COVERS = tuple(f"cover_{k}_{a}" for k in ("tau", "hidden", "tau_pooled", "tau_stage1", "hidden_stage1")
               for a in ARMS)


def summary(res):
    n = len(res["success"])
    s = {"runs": n}
    for k in ("success", "raw_raises", "raw_lowers", "q_audit", "q_unres", "q_comb_only", "envelope_crosses",
              "unres_flag", "exclusion", "complete", "over_125", "raw_boot_raises", "raw_t_raises",
              "raw_welch_raises", "raw_t_lowers") + COVERS:
        if k in res:
            s[k] = float(np.mean(res[k]))
    s["capped_draws"] = int(res["capped"].sum()) if "capped" in res else None
    s["successes"] = int(res["success"].sum())
    s["raw_raises_count"] = int(res["raw_raises"].sum())
    s["protocol_contrast"] = float(np.mean(res["protocol"]))
    s["latent_contrast"] = float(np.mean(res["latent"]))
    sec = res["seconds"] / 3600
    s["cpu_hours"] = {"mean": float(sec.mean()), "median": float(np.median(sec)), "p95": float(np.percentile(sec, 95))}
    return s


def cp_lower(x, n, level):
    return 0.0 if x == 0 else float(stats.beta.ppf(1 - level, x, n - x + 1))


def cp_upper(x, n, level=0.95):
    return 1.0 if x >= n else float(stats.beta.ppf(level, x + 1, n - x))


# ============================================================================================================ stages
def load():
    f = OUT / "power.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def save(rec):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "power.json.tmp"
    tmp.write_text(json.dumps(rec, indent=1, default=float), encoding="utf-8")
    tmp.replace(OUT / "power.json")


def fitted_from(rec):
    return rec["fit"]["fitted"]


def scenario(rec, **kw):
    """A solved scenario: rho and scale from the fit stage's table (Rr's rate, the draw scenario)."""
    sc = Scenario(**kw)
    sol = rec["fit"]["scenarios"].get(f"{sc.target}|{sc.draw}|{sc.rate_rr}")
    if sol is None:
        return None
    return replace(sc, rho=sol["rho"], scale=sol["scale"])


def stage_fit(rec):
    fitted = fit()
    fc = OUT / "fixed-costs.json"
    if fc.exists():
        x = json.loads(fc.read_text(encoding="utf-8"))
        fitted["fixed"] = {"host": float(np.mean([h["cpu_seconds"] for h in x["hosts"]])),
                           "block": float(np.mean([b["cpu_seconds"] for b in x["rr_blocks"]])),
                           "verify_per_host": x["m4e_verify_run_cpu_seconds"] / 10}
    else:
        fitted["fixed"] = {"host": 0.0, "block": 0.0, "verify_per_host": 0.0}
    table = {}
    sd0 = fitted["classes"]["S1"]["sd_pooled"]
    for draw in ("pilot", "zero", "tk"):
        sd_v = {"pilot": fitted["sd_v"], "zero": 0.0, "tk": fitted["sd_v_tk"]}[draw]
        for tg in TARGETS:
            sc = solve_scenario(fitted, Scenario(target=tg, draw=draw))
            key = f"{tg}|{draw}|{RATE_RR}"
            if sc is None:
                table[key] = None
                continue
            table[key] = {"rho": sc.rho, "scale": sc.scale, "realised": host_component(
                fitted, RATE_RR, sd0 * np.sqrt(sc.scale), sc.rho, sd_v), **implied_counts(fitted, sc)}
    core = table[f"core|pilot|{RATE_RR}"]
    for rate in RATE_SENS:  # the base-rate sensitivities at the central rho and at the core's rho (Astra)
        for tg, rho in (("min", 1.0), ("core", core["rho"])):
            sc = Scenario(target=tg, rate_rr=rate, rho=rho)
            table[f"{tg}|pilot|{rate}"] = {"rho": rho, "scale": 1.0, "realised": host_component(
                fitted, rate, sd0, rho, fitted["sd_v"]), **implied_counts(fitted, sc)}
        hi = host_component(fitted, rate, sd0, 0.0, fitted["sd_v"])
        for tg in ("half", "core", "above"):
            table[f"reach|{tg}|{rate}"] = {"ceiling_at_rho_0": hi, "reachable_by_rho": TARGETS[tg] <= hi}
    ew = solve_extra_w(fitted, Scenario(target="core"))
    table["extra_w|core"] = {"extra_w": ew.extra_w, "rho": 1.0, "scale": 1.0}
    rec["fit"] = {"fitted": fitted, "scenarios": table, "note": "rho and scale solve the contrast's host component "
                  "(draw-averaged, zero effect) at Rr's 0.0058 in both arms; the reach rows say whether a target is "
                  "reachable at the sensitivity rates by lowering rho alone"}
    save(rec)
    print("fit:", json.dumps(table, default=float)[:3000], flush=True)


def implied_counts(fitted, sc, n_hosts=40_000):
    """The implied per-arm host-count variance over 1024 genomes (2 draws of 512) and the counts' correlation, by
    simulating the first pass's separate states, beside the pilot's 22.5, 15.4 and 0.70."""
    m = Model(fitted, sc, (2, 512, 40))
    sd_tot = np.sqrt(m.sd ** 2 + sc.extra_w ** 2)
    muT, muR = solve_mu(sc.rate_rr, sd_tot), solve_mu(sc.rate_rr, sd_tot, m.sd_v)
    rng = np.random.default_rng([SEED, 3])
    rho = 1.0 if sc.rho is None else sc.rho
    z, eT, eR = rng.standard_normal((3, n_hosts))
    v = rng.standard_normal((n_hosts, 2))
    pT = special.expit(muT + m.sd * (np.sqrt(rho) * z + np.sqrt(1 - rho) * eT))[:, None].repeat(2, 1)
    pR = special.expit(muR + (m.sd * (np.sqrt(rho) * z + np.sqrt(1 - rho) * eR))[:, None] + m.sd_v * v)
    cT, cR = rng.binomial(512, pT).sum(1), rng.binomial(512, pR).sum(1)
    return {"count_var_T": float(cT.var()), "count_var_Rr": float(cR.var()),
            "count_corr": float(np.corrcoef(cT, cR)[0, 1])}


# ---------------------------------------------------------------------------------------------- the calibration check
def stage_check(rec):
    """The model at the central scenario and the pilot's design (10 hosts, D = 2, G = 512, A = 40), at the pilot's
    fitted rates (T 0.0073, Rr 0.0058: a constant increment of 0.0015), against the pilot's observed values."""
    fitted = fitted_from(rec)
    sc = replace(scenario(rec, target="min"), delta=0.0015)
    m = make_model(fitted, sc, (2, 512, 40))
    rng = cell_seed("check")
    R, H, n = 4000, 10, 1024
    sim = simulate(m, rng, R, H)
    d = (sim["T"]["S"] - sim["Rr"]["S"]) / n
    lo, hi = hull_batch(d, weights(tuple(np.arange(H) % 5)))
    inp = pilot_inputs()
    iv = inp["pilot"]["interval"]
    obs = {"sd": inp["pilot"]["sd"], "half_width": (iv[1] - iv[0]) / 2}
    sims = {"sd": d.std(1, ddof=1), "half_width": (hi - lo) / 2}
    c = fitted["classes"]
    for a in ARMS:
        obs[f"count_var_{a}"] = c["S1"]["count_var"][a]
        sims[f"count_var_{a}"] = sim[a]["S"].var(1, ddof=1)
        obs[f"unresolved_{a}"] = sum(r["U"] for r in inp["panels"][a]) / (10 * n)
        sims[f"unresolved_{a}"] = sim[a]["U"].sum(1) / (H * n)
    obs["count_corr"] = c["S1"]["count_corr"]
    for a in ARMS:  # the first-to-final counts: first-pass unresolved, and how many became fading
        tab = fitted["first_to_final"][a]
        obs[f"first_pass_unresolved_{a}"] = sum(tab.values())
        sims[f"first_pass_unresolved_{a}"] = sim[a]["U1"].sum(1)
        obs[f"unresolved_to_fading_{a}"] = tab["F"]
        sims[f"unresolved_to_fading_{a}"] = sim[a]["uF"].sum(1)
    ok = (sim["T"]["S"].std(1) > 0) & (sim["Rr"]["S"].std(1) > 0)
    cc = np.full(R, np.nan)
    for r in np.flatnonzero(ok):
        cc[r] = np.corrcoef(sim["T"]["S"][r], sim["Rr"]["S"][r])[0, 1]
    sims["count_corr"] = cc
    out = {}
    for k, v in obs.items():
        s = sims[k][np.isfinite(sims[k])]
        q = float((s < v).mean() + 0.5 * (s == v).mean())
        out[k] = {"observed": v, "simulated_median": float(np.median(s)),
                  "central_95": [float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))],
                  "quantile_of_observed": q, "inside_central_95": bool(0.025 <= q <= 0.975)}
    rec["check"] = {"design": "10 hosts, D 2, G 512, A 40, T 0.0073, Rr 0.0058, central scenario, 4000 runs",
                    "note": "weak at ten hosts: a sample variance's central 95% spans about 0.30 to 2.1 times its "
                            "truth (Fable)",
                    "values": out, "all_inside": all(v["inside_central_95"] for v in out.values())}
    save(rec)
    print("check:", json.dumps(rec["check"], default=float), flush=True)


# ------------------------------------------------------------------------------------------- fixed-H families (A, B)
FAMILIES = {"A": "core", "B": "min"}


def caps_for(rec, alloc, H):
    """The frozen cap for a fixed-H run at H: 1.5 times its mean cost under the central scenario and base case."""
    key = f"{alloc}|{H}"
    caps = rec.setdefault("caps", {})
    if key not in caps:
        m = make_model(fitted_from(rec), scenario(rec, target="min"), alloc)
        rng = cell_seed("cap", alloc, H)
        sec = []
        for _ in range(2):
            sim = simulate(m, rng, R_COARSE // 2, H)
            sec.append(sim["T"]["seconds"].sum(1) + sim["Rr"]["seconds"].sum(1) + H * fixed_per_host(
                fitted_from(rec), alloc[0]))
        caps[key] = float(CAP_MULT * np.concatenate(sec).mean())
    return caps[key]


def power_at(rec, m, H, R, *tag, exclusion=False):
    return summary(run_cell(m, H, R, *tag, cap=caps_for(rec, m.alloc, H), exclusion=exclusion))


def family_level(K):
    return 1 - 0.05 / K


def summarise_short(s):
    return {k: s[k] for k in ("runs", "success", "successes", "raw_raises", "q_audit", "q_unres", "q_comb_only",
                              "complete", "over_125", "over_125_own_mean", "capped_draws", "cpu_hours",
                              "cap_seconds", "protocol_contrast", "latent_contrast") + COVERS if k in s}


def search(rec, m, goal, level, tag, coarse):
    """The candidate H (R_REFINE, the family's level) from the coarse powers, upward if needed; then its one
    confirmation at H and H + 5 (R_CONFIRM)."""
    near = sorted(H for H, r in coarse.items() if abs(r["success"] - goal) <= 0.1)
    refined, cand = {}, None
    for H in near or [max(coarse)]:
        s = power_at(rec, m, H, R_REFINE, tag, "refine")
        refined[H] = s
        if cp_lower(s["successes"], s["runs"], level) >= goal:
            cand = H
            break
    H = max(refined)
    while cand is None and H + 5 <= HOSTS_WIDE[-1]:
        H += 5
        s = power_at(rec, m, H, R_REFINE, tag, "refine")
        refined[H] = s
        if cp_lower(s["successes"], s["runs"], level) >= goal:
            cand = H
    a = {"candidate": cand, "refined": {str(h): summarise_short(s) for h, s in refined.items()}}
    if cand is None:
        a["selected"], a["status"] = None, "no candidate in the grid"
        return a
    conf = {}
    for h in (cand, cand + 5):
        s = power_at(rec, m, h, R_CONFIRM, tag, "confirm")
        low = cp_lower(s["successes"], s["runs"], level)
        conf[str(h)] = {**summarise_short(s), "lower": low, "passes": low >= goal}
    passing = [int(h) for h, c in conf.items() if c["passes"]]
    a["confirmation"] = conf
    a["selected"] = min(passing) if passing else None
    a["status"] = "confirmed" if passing else "not confirmed"
    if a["selected"] is not None:
        a["cap_seconds"] = caps_for(rec, m.alloc, a["selected"])
    return a


def coarse_pass(rec, m, tag, hosts=HOSTS, stop=0.98):
    rows = {}
    for H in hosts:
        s = power_at(rec, m, H, R_COARSE, tag, "coarse")
        rows[H] = {"success": s["success"], "raw_raises": s["raw_raises"], "cpu_hours": s["cpu_hours"]["mean"]}
        if s["success"] > stop:
            break
    return rows


def stage_families(rec):
    """A's and B's families: each allocation's coarse pass, candidate and confirmation, at 80% and at 90%; plus,
    descriptive, each allocation's raw-only H and its H at tau = 0 (Fable)."""
    fitted = fitted_from(rec)
    fam = rec.setdefault("families", {})
    for name, target in FAMILIES.items():
        sc = scenario(rec, target=target)
        coarse = {}
        for alloc in ALLOCS:
            coarse[alloc] = coarse_pass(rec, make_model(fitted, sc, alloc), name)
            print(name, alloc, {h: round(r["success"], 3) for h, r in coarse[alloc].items()}, flush=True)
        fam[f"{name}|coarse"] = {str(a): {str(h): r for h, r in v.items()} for a, v in coarse.items()}
        for goal in (0.80, 0.90):
            K = 2 * len(ALLOCS)
            level = family_level(K)
            out = {"K": K, "level": level, "goal": goal, "scenario": target, "allocations": {}}
            for alloc in ALLOCS:
                m = make_model(fitted, sc, alloc)
                a = search(rec, m, goal, level, f"{name}|{goal}", coarse[alloc])
                out["allocations"][str(alloc)] = a
                print(name, goal, alloc, a["status"], a.get("selected"), flush=True)
                fam[f"{name}|{goal}"] = out
                save(rec)
        if name == "A":  # what the audit's noise and the qualifiers cost: the raw-only H and the H at tau = 0
            desc = {}
            sc0 = replace(sc, tau="zero")
            for alloc in ALLOCS:
                raw_h = next((h for h, r in coarse[alloc].items() if r["raw_raises"] >= 0.80), None)
                rows0 = coarse_pass(rec, make_model(fitted, sc0, alloc), "A|tau0")
                tau0_h = next((h for h, r in rows0.items() if r["success"] >= 0.80), None)
                desc[str(alloc)] = {"raw_only_H": raw_h, "tau_zero_H": tau0_h,
                                    "note": "coarse point estimates (R = 400), descriptive"}
            fam["A|descriptive"] = desc
        save(rec)


def selected_allocs(rec, name, goal=0.80):
    """The fewest-host and the cheapest confirmed allocations of a family (by the selected H's mean cost)."""
    al = rec["families"][f"{name}|{goal}"]["allocations"]
    ok = {k: v for k, v in al.items() if v.get("selected")}
    if not ok:
        return {}
    cost = {k: v["confirmation"][str(v["selected"])]["cpu_hours"]["mean"] for k, v in ok.items()}
    fewest = min(ok, key=lambda k: (ok[k]["selected"], cost[k]))
    cheapest = min(ok, key=lambda k: (cost[k], ok[k]["selected"]))
    return {"fewest_hosts": [fewest, ok[fewest]["selected"]], "cheapest": [cheapest, ok[cheapest]["selected"]]}


def parse_alloc(s):
    return tuple(int(x) for x in s.strip("()").split(","))


# ------------------------------------------------------------------------------------------------------------ nulls
NULL_VARIANTS = (("min", "constant"), ("half", "constant"), ("core", "constant"), ("above", "constant"),
                 ("min", "pm"), ("min", "ens_null"), ("core", "pm"), ("core", "ens_null"))  # Fable: both nulls at
# the core as well as the central scenario


def null_rates(s):
    """The gate's two rates with their upper bounds, and, for the diagnosis (results round 1), the raw "lowers" rate
    and the raw reading's parts alone: the bootstrap, the plain-s^2 t (raises and lowers) and the Welch t."""
    out = {}
    for key, cnt in (("raw", "raw_raises_count"), ("unqualified", "successes")):
        x = s[cnt]
        out[key] = {"rate": x / s["runs"], "upper_95": cp_upper(x, s["runs"])}
    out["parts"] = {k: s[k] for k in ("raw_lowers", "raw_boot_raises", "raw_t_raises", "raw_t_lowers",
                                      "raw_welch_raises") if k in s}
    return out


def stage_nulls(rec):
    """The false "raises" rate at delta = 0 (R = 40,000) for each family's fewest-host and cheapest confirmed
    allocations, under every host-variance scenario and both nulls; tolerance 0.0275 (A and B)."""
    fitted = fitted_from(rec)
    out = rec.setdefault("nulls", {})
    for name in FAMILIES:
        for role, (alloc_s, H) in selected_allocs(rec, name).items():
            alloc = parse_alloc(alloc_s)
            rows = {}
            for target, spread in NULL_VARIANTS:
                sc = scenario(rec, target=target, spread=spread, delta=0.0)
                s = power_at(rec, make_model(fitted, sc, alloc), H, R_NULL, "null", name, role)
                r = null_rates(s)
                r["passes"] = all(r[k]["upper_95"] <= 0.0275 for k in ("raw", "unqualified"))
                rows[f"{target}|{spread}"] = r
                print("null", name, role, alloc, H, target, spread, json.dumps(r), flush=True)
            out[f"{name}|{role}"] = {"allocation": alloc_s, "H": H, "tolerance": 0.0275, "rows": rows,
                                     "passes": all(r["passes"] for r in rows.values())}
            save(rec)


# --------------------------------------------------------------------------------------------------------- scenarios
def scenario_variants(rec):
    """(label, Scenario) for every sensitivity of section 2, at delta = 0.002 unless stated."""
    v = [("base, core", scenario(rec, target="core")), ("base, central", scenario(rec, target="min"))]
    for tg in ("half", "above"):
        v.append((f"host component {tg}", scenario(rec, target=tg)))
    for d in DELTAS + (-0.002,):
        v.append((f"delta {d}, core", scenario(rec, target="core", delta=d)))
        v.append((f"delta {d}, central", scenario(rec, target="min", delta=d)))
    for sp in ("proportional", "uniform", "sparse", "ensemble"):
        v.append((f"spread {sp}, core", scenario(rec, target="core", spread=sp)))
    for tau in ("zero", "Rr", "T", "host", "host_T", "host_Rr", "panel"):
        v.append((f"tau {tau}, core", scenario(rec, target="core", tau=tau)))
    for draw in ("zero", "tk"):
        v.append((f"draw {draw}, core", scenario(rec, target="core", draw=draw)))
    for rate in RATE_SENS:
        for tg in ("min", "core"):
            v.append((f"Rr rate {rate}, rho of {tg}", scenario(rec, target=tg, rate_rr=rate)))
    for lat in ("Rr", "T"):
        v.append((f"latent {lat}, core", scenario(rec, target="core", latent=lat)))
        v.append((f"latent {lat}, central", scenario(rec, target="min", latent=lat)))
    v.append(("unresolved with separate 0.5, core", scenario(rec, target="core", su_corr=0.5)))
    v.append(("whole-host times, core", scenario(rec, target="core", times="whole_host")))
    v.append(("overhead 12.6%, core", scenario(rec, target="core", overhead=True)))
    ew = rec["fit"]["scenarios"]["extra_w|core"]["extra_w"]
    v.append(("draft 1 parametrisation, core", replace(Scenario(target="core"), rho=1.0, extra_w=ew)))
    v.append(("invalid 1% per panel, core", scenario(rec, target="core", invalid=0.01)))
    v.append(("unequal ensemble spreads, 5% invalid, core", scenario(rec, target="core", ens_sd="unequal",
                                                                     invalid=0.05)))
    return [(k, s) for k, s in v if s is not None]


def realised_host_component(m, n=200_000):
    """The contrast's host component under the model's effect spread (Fable, Astra: reported per spread): the
    variance over hosts of pbar_T - pbar_Rr, Rr's draw averaged by quadrature, on n sampled hosts."""
    rng = np.random.default_rng([SEED, 4])
    he = draw_hosts(m, rng, 1, n)
    gT, gR, fT, fR = (x[0] for x in effect_weights(m, rng, 1, n))
    xT = m.mu["S"]["T"] + he["S"]["T"][0] + (m.inc if m.sc.spread == "proportional" else 0.0)
    pT = special.expit(xT)
    pR = (special.expit(m.mu["S"]["Rr"] + he["S"]["Rr"][0][:, None] + m.sd_v * GH_X[None, :]) * GH_W).sum(1)
    if m.sc.spread != "proportional":
        pT, pR = pT + m.inc * gT, pR + m.inc * gR
    return float(np.var(pT + fT - pR - fR))


def stage_scenarios(rec):
    """Every sensitivity at each family's fewest-host and cheapest confirmed allocations and H (R = 4000; the
    invalid-panel one R = 1000, its unbalanced reading being per run), pointwise and descriptive; the exclusion at
    delta 0 and +-0.002."""
    fitted = fitted_from(rec)
    out = rec.setdefault("scenarios", {})
    for name in FAMILIES:
        for role, (alloc_s, H) in selected_allocs(rec, name).items():
            alloc = parse_alloc(alloc_s)
            rows = {}
            for label, sc in scenario_variants(rec):
                R = 1000 if sc.invalid else R_SCEN
                excl = abs(sc.delta) in (0.0, 0.002) and label.startswith("delta")
                m = make_model(fitted, sc, alloc)
                if sc.ens_sd == "unequal":  # the unbalanced reading's coverage of the true protocol contrast
                    res = run_cell(m, H, R, "scen", name, role, cap=caps_for(rec, alloc, H))
                    s = summary(res)
                    truth = float(np.mean(res["protocol"]))
                    cov = (res["lo_raw"] <= truth) & (truth <= res["hi_raw"])
                    ok = np.isfinite(res["lo_raw"]) & res["complete"]
                    s["coverage_of_protocol_contrast"] = {
                        "truth": truth, "unbalanced_runs": int((ok & res["unbalanced"]).sum()),
                        "unbalanced": float(cov[ok & res["unbalanced"]].mean()),
                        "balanced_runs": int((ok & ~res["unbalanced"]).sum()),
                        "balanced": float(cov[ok & ~res["unbalanced"]].mean()) if (ok & ~res["unbalanced"]).any()
                        else None}
                else:
                    s = power_at(rec, m, H, R, "scen", name, role, exclusion=excl)
                if label.startswith("spread") or label.startswith("base") or label.startswith("host component"):
                    s["realised_host_component"] = realised_host_component(m)
                rows[label] = s
                print("scen", name, role, alloc, H, label, round(s["success"], 3), round(s["raw_raises"], 3),
                      flush=True)
            out[f"{name}|{role}"] = {"allocation": alloc_s, "H": H, "rows": rows}
            save(rec)


# ------------------------------------------------------------------------------------------------------------ rule C
C_FAMILY_K = 2
C_TOLERANCE = 0.030
CORE_SCENARIOS = ("min", "half", "core")


def slice_sim(sim, h):
    out = {"rejected": sim["rejected"]}
    for a in ARMS:
        out[a] = {k: v[:, :h] for k, v in sim[a].items()}
    if "invalid" in sim:
        out["invalid"] = sim["invalid"][:, :h]
    return out


def stage1_contrasts(sim, h1, n):
    """What the interim reads: stage 1's (the first h1 hosts') per-host raw contrasts, nothing of stage 2."""
    return (sim["T"]["S"] - sim["Rr"]["S"])[:, :h1] / n


def interim(d1, table, h1, hmax):
    """The registered interim: from stage 1's per-host raw contrasts, s^2 and the final H only (never a mean, an
    interval or a per-host value). s^2 is inflated by the normal-reference 75% upper limit, mapped through the
    table (expected total per-host variance -> required H, linear in s^2), rounded up to a multiple of 5 and
    clipped to [h1, hmax]."""
    d1 = np.asarray(d1, float)
    n = np.isfinite(d1).sum(-1)  # an invalid host enters as NaN and is left out (Astra, results round 1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # a run short of hosts is stopped by the caller
        s2 = np.nanvar(d1, -1, ddof=1)
    s75 = s2 * (n - 1) / stats.chi2.ppf(0.25, n - 1)
    v = np.asarray(table["variance"])
    h = np.asarray(table["H"], float)
    req = np.interp(s75, v, h)
    req = np.where(s75 > v[-1], hmax, req)
    H = np.clip(np.ceil(req / 5) * 5, h1, hmax).astype(int)
    return {"s2": s2, "H": H}


def lookup_table(rec, alloc):
    """Rule C's table for an allocation: along the rho path (then the scale beyond its ceiling) to a host component
    of 4.5e-5, each row's expected total per-host raw contrast variance at delta = 0.002 and its required H (the
    smallest H in HOSTS_WIDE whose point power is at least 0.80 at R_TABLE, by bisection), under the base case."""
    fitted = fitted_from(rec)
    sd0 = fitted["classes"]["S1"]["sd_pooled"]
    path = [(r, 1.0) for r in (1.0, 0.8, 0.6, 0.4, 0.2, 0.0)] + [(0.0, k) for k in (1.25, 1.5, 2.0, 2.5, 3.0)]
    rows = []
    for rho, k in path:
        hc = host_component(fitted, RATE_RR, sd0 * np.sqrt(k), rho, fitted["sd_v"])
        sc = Scenario(target="table", rho=rho, scale=k)
        m = make_model(fitted, sc, alloc)
        sim = simulate(m, cell_seed("table-var", alloc, rho, k), R_TABLE, 20)
        var = float(((sim["T"]["S"] - sim["Rr"]["S"]) / (alloc[0] * alloc[1])).var(1, ddof=1).mean())
        lo, hi = 0, len(HOSTS_WIDE) - 1
        if power_at(rec, m, HOSTS_WIDE[hi], R_TABLE, "table", rho, k)["success"] < 0.80:
            req = None
        else:
            while lo < hi:
                mid = (lo + hi) // 2
                if power_at(rec, m, HOSTS_WIDE[mid], R_TABLE, "table", rho, k)["success"] >= 0.80:
                    hi = mid
                else:
                    lo = mid + 1
            req = HOSTS_WIDE[lo]
        rows.append({"rho": rho, "scale": k, "host_component": hc, "variance": var, "H": req})
        print("table", alloc, rho, k, hc, var, req, flush=True)
        if hc >= 4.5e-5 or req is None:
            break
    good = [r for r in rows if r["H"] is not None]
    good.sort(key=lambda r: r["variance"])
    return {"rows": rows, "variance": [r["variance"] for r in good], "H": [r["H"] for r in good]}


def stage1_bound(aud, trans, valid, h1):
    """Stage 1's own audit bound per run (its size fixed before the interim): the one-sided 95% Clopper-Pearson upper
    bound on tau from the first h1 hosts' valid audits only."""
    v = valid[:, :h1]
    a1, t1 = (aud[:, :h1] * v).sum(1), (trans[:, :h1] * v).sum(1)
    return np.where(t1 >= a1, 1.0, stats.beta.ppf(0.95, t1 + 1, np.maximum(a1 - t1, 1)))


def run_c(rec, m, h1, hmax, table, R, *tag, batch=2000, cap=None):
    """R runs of rule C: H_max hosts simulated, stage 1 the first h1 (balanced, ensembles host % 5), the interim on
    stage 1's valid hosts (a run with fewer than 2 valid stage-1 hosts in an ensemble stops, incomplete), then the
    reading on the first H hosts, invalid ones left out; the cap 1.5 times the mean fixed-H cost at H_max (central,
    base case). Also stage 1's own audit bound (fixed in size) and its coverage, beside the final pooled one."""
    cap = caps_for(rec, m.alloc, hmax) if cap is None else cap
    rng = cell_seed("C", m.sc.label(), m.alloc, h1, hmax, R, *tag)
    n = m.alloc[0] * m.alloc[1]
    acc, Hs, done, capped = {}, [], 0, 0
    while done < R:
        r = min(batch, R - done)
        sim = simulate(m, rng, r, hmax)
        capped += sim["rejected"]
        inv1 = sim["invalid"][:, :h1] if "invalid" in sim else np.zeros((r, h1), bool)
        d1 = np.where(inv1, np.nan, stage1_contrasts(sim, h1, n))
        ens1 = np.arange(h1) % 5
        short = np.stack([((~inv1) & (ens1 == e)).sum(1) for e in range(5)], 1).min(1) < 2
        with np.errstate(invalid="ignore", divide="ignore"):
            H = interim(d1, table, h1, hmax)["H"]
        H = np.where(short, h1, H)
        Hs.append(H)
        res = {}
        for h in np.unique(H):
            sel = H == h
            sub = {"rejected": 0, **{a: {k: v[sel] for k, v in sim[a].items()} for a in ARMS}}
            if "invalid" in sim:
                sub["invalid"] = sim["invalid"][sel]
            sl = slice_sim(sub, int(h))
            out = readings(sl, m, int(h), cap=cap, exclusion=False)
            vf = valid_hosts(sl)
            for a in ARMS:  # stage 1's audit bound (its size fixed), applied to the final valid hosts' unaudited fading
                ub1 = stage1_bound(sl[a]["aud"], sl[a]["trans"], vf, h1)
                if m.sc.tau in ("zero", "symmetric", "T", "Rr"):
                    out[f"cover_tau_stage1_{a}"] = ub1 >= tau_of(m, a)
                out[f"cover_hidden_stage1_{a}"] = ub1 * (sl[a]["Fun"] * vf).sum(1) >= (sl[a]["hidden"] * vf).sum(1)
            for k, v in out.items():
                if v is None:
                    continue
                res.setdefault(k, np.empty(r, dtype=v.dtype))[sel] = v
        for k in ("success", "raw_raises", "raw_lowers", "q_audit", "q_unres", "q_comb_only", "complete"):
            res[k][short] = False
        for k, v in res.items():
            acc.setdefault(k, []).append(v)
        done += r
    res = {k: np.concatenate(v) for k, v in acc.items()}
    res["capped"] = np.array([capped])
    s = summary(res)
    # over_125 is against 1.25 times the fixed-H reference mean at H_max; this one against C's own mean (Astra)
    s["over_125_own_mean"] = float((res["seconds"] > 1.25 * res["seconds"].mean()).mean())
    Hs = np.concatenate(Hs)
    s["H"] = {"mean": float(Hs.mean()), "p10": float(np.percentile(Hs, 10)), "median": float(np.median(Hs)),
              "p90": float(np.percentile(Hs, 90)), "at_hmax": float((Hs == hmax).mean()),
              "at_h1": float((Hs == h1).mean())}
    s["cap_seconds"] = cap
    return s


def stage_c(rec):
    """Rule C (section 5): per allocation, its table, H1 (B's selected H), H_max explored from A's H upward (at most
    four steps of 5, the core scenario, C's family level); the nominated allocation (the lowest expected central cost
    among those reaching the bound); its one confirmation at H_max and H_max + 5 under all three core scenarios
    (a conjunction); its nulls (tolerance 0.030) and its power above the core range."""
    fitted = fitted_from(rec)
    out = rec.setdefault("c", {"explore": {}})
    level = family_level(C_FAMILY_K)
    fa = rec["families"]["A|0.8"]["allocations"]
    fb = rec["families"]["B|0.8"]["allocations"]
    for alloc in ALLOCS:
        key = str(alloc)
        if key in out["explore"]:
            continue
        a_h = fa[key].get("selected") or fa[key].get("candidate")
        h1 = fb[key].get("selected") or fb[key].get("candidate")
        if a_h is None or h1 is None:
            out["explore"][key] = {"status": "no A or B host count"}
            continue
        table = lookup_table(rec, alloc)
        m_core = make_model(fitted, scenario(rec, target="core"), alloc)
        m_min = make_model(fitted, scenario(rec, target="min"), alloc)
        tried, hmax = {}, None
        for step in range(5):
            h = max(a_h, h1) + 5 * step
            s = run_c(rec, m_core, h1, h, table, R_REFINE, "explore")
            low = cp_lower(s["successes"], s["runs"], level)
            tried[str(h)] = {**summarise_short(s), "H": s["H"], "lower": low}
            print("C explore", alloc, h1, h, round(s["success"], 3), round(low, 3), flush=True)
            if low >= 0.80:
                hmax = h
                break
        entry = {"h1": h1, "a_h": a_h, "table": table, "tried": tried, "hmax": hmax}
        if hmax is not None:
            sc = run_c(rec, m_min, h1, hmax, table, R_REFINE, "explore-central")
            entry["central"] = {**summarise_short(sc), "H": sc["H"]}
        out["explore"][key] = entry
        save(rec)
    cands = {k: v for k, v in out["explore"].items() if v.get("hmax") is not None}
    if not cands:
        out["status"] = "C not confirmed: no allocation reached the bound"
        save(rec)
        return
    nom = min(cands, key=lambda k: cands[k]["central"]["cpu_hours"]["mean"])
    e = cands[nom]
    alloc, h1, table = parse_alloc(nom), e["h1"], e["table"]
    conf = {}
    for h in (e["hmax"], e["hmax"] + 5):
        rows = {}
        for tg in CORE_SCENARIOS:
            s = run_c(rec, make_model(fitted, scenario(rec, target=tg), alloc), h1, h, table, R_CONFIRM, "confirm")
            low = cp_lower(s["successes"], s["runs"], level)
            rows[tg] = {**summarise_short(s), "H": s["H"], "lower": low, "passes": low >= 0.80}
        conf[str(h)] = {"rows": rows, "passes": all(r["passes"] for r in rows.values())}
        print("C confirm", nom, h, conf[str(h)]["passes"], flush=True)
    passing = [int(h) for h, c in conf.items() if c["passes"]]
    out.update({"nominated": nom, "h1": h1, "confirmation": conf, "level": level, "K": C_FAMILY_K})
    if not passing:
        out["status"] = "C not confirmed"
        save(rec)
        return
    hmax = min(passing)
    out["hmax"], out["status"] = hmax, "confirmed"
    nulls = {}
    for target, spread in NULL_VARIANTS:
        sc = scenario(rec, target=target, spread=spread, delta=0.0)
        s = run_c(rec, make_model(fitted, sc, alloc), h1, hmax, table, R_NULL, "null")
        r = null_rates(s)
        r["passes"] = all(r[k]["upper_95"] <= C_TOLERANCE for k in ("raw", "unqualified"))
        nulls[f"{target}|{spread}"] = r
        print("C null", target, spread, json.dumps(r), flush=True)
    out["nulls"] = {"tolerance": C_TOLERANCE, "rows": nulls, "passes": all(r["passes"] for r in nulls.values())}
    s = run_c(rec, make_model(fitted, scenario(rec, target="above"), alloc), h1, hmax, table, R_CONFIRM, "above")
    out["above"] = {**summarise_short(s), "H": s["H"]}
    out["passes"] = out["nulls"]["passes"]
    save(rec)


def stage_c_sens(rec, R=1000):
    """Rule C's own invalid-panel sensitivities (Astra, results round 1), descriptive, at the nominated policy and
    H_max (R = 1000): 1% invalid per panel at the core; unequal ensemble spreads with 5% invalid per panel."""
    c = rec.get("c", {})
    if c.get("status") != "confirmed":
        return
    fitted = fitted_from(rec)
    alloc, table = parse_alloc(c["nominated"]), c["explore"][c["nominated"]]["table"]
    rows = {}
    for label, sc in (("invalid 1% per panel, core", scenario(rec, target="core", invalid=0.01)),
                      ("unequal ensemble spreads, 5% invalid, core",
                       scenario(rec, target="core", ens_sd="unequal", invalid=0.05))):
        s = run_c(rec, make_model(fitted, sc, alloc), c["h1"], c["hmax"], table, R, "sens")
        rows[label] = {**summarise_short(s), "H": s["H"]}
        print("C sens", label, round(s["success"], 3), round(s["complete"], 3), flush=True)
    c["sensitivity"] = rows
    save(rec)


# ------------------------------------------------------------------------------------------------------------ report
def stage_report(rec):
    """The answer: each rule's allocation, host count, cost and powers, and the choice rule's outcome."""
    ans = {}
    for name in FAMILIES:
        sel = selected_allocs(rec, name)
        ans[name] = {}
        for role, (alloc_s, H) in sel.items():
            a = rec["families"][f"{name}|0.8"]["allocations"][alloc_s]
            c = a["confirmation"][str(H)]
            row = {"allocation": alloc_s, "H": H, "power": c["success"], "lower": c["lower"],
                   "cpu_hours": c["cpu_hours"], "cap_hours": a["cap_seconds"] / 3600}
            n = rec.get("nulls", {}).get(f"{name}|{role}")
            if n:
                row["nulls_pass"] = n["passes"]
            sc = rec.get("scenarios", {}).get(f"{name}|{role}", {}).get("rows", {})
            for lab in ("base, central", "base, core", "host component above"):
                if lab in sc:
                    row[f"power, {lab}"] = sc[lab]["success"]
                    row[f"cpu_hours, {lab}"] = sc[lab]["cpu_hours"]["mean"]
            ans[name][role] = row
    desc = rec["families"].get("A|descriptive", {})
    third = {}
    for alloc_s, a in rec["families"]["A|0.8"]["allocations"].items():
        raw_h = desc.get(alloc_s, {}).get("raw_only_H")
        if a.get("selected") and raw_h:
            third[alloc_s] = {"selected": a["selected"], "raw_only_H": raw_h,
                              "tau_zero_H": desc[alloc_s].get("tau_zero_H"),
                              "exceeds_by_a_third": a["selected"] > raw_h * 4 / 3}
    ans["A_qualifier_cost"] = third
    c = rec.get("c", {})
    if c.get("status") == "confirmed":
        cen = c["confirmation"][str(c["hmax"])]["rows"]["min"]
        a_cheap = ans["A"].get("cheapest")
        ans["C"] = {"allocation": c["nominated"], "h1": c["h1"], "hmax": c["hmax"], "central": cen,
                    "core": c["confirmation"][str(c["hmax"])]["rows"]["core"], "above": c["above"],
                    "nulls_pass": c["nulls"]["passes"]}
        if a_cheap:
            a_central = a_cheap.get("cpu_hours, base, central", a_cheap["cpu_hours"]["mean"])
            saving = 1 - cen["cpu_hours"]["mean"] / a_central
            ans["choice"] = {"C_central_cpu_hours": cen["cpu_hours"]["mean"], "A_central_cpu_hours": a_central,
                             "saving": saving, "recommend": "C" if saving >= 0.20 and c["nulls"]["passes"] else "A"}
    else:
        ans["C"] = {"status": c.get("status")}
        ans["choice"] = {"recommend": "A"}
    rec["answer"] = ans
    save(rec)
    print(json.dumps(ans, indent=1, default=float))


STAGES = {"fit": stage_fit, "check": stage_check, "families": stage_families, "nulls": stage_nulls,
          "scenarios": stage_scenarios, "c": stage_c, "c_sens": stage_c_sens, "report": stage_report}


def main(argv):
    stages = argv or list(STAGES)
    rec = load()
    for st in stages:
        t0 = time.time()
        STAGES[st](rec)
        rec.setdefault("seconds", {})[st] = round(time.time() - t0, 1)
        save(rec)
        print(f"stage {st}: {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
