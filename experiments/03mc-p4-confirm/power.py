"""03mc: the probability of passing the registered procedure, simulated from 03m's data (DESIGN.md §6).

    python experiments/03mc-p4-confirm/power.py      # writes power.json beside this file

A model, not a measurement. It uses 03m's committed summaries and its local per-genome arrays (`runs/p4m/*.npz`,
not committed; their hashes are recorded), and 03's and 03r's committed supplements. Each simulated study draws:
- Q-A: every fresh graph's intact P4 from 03's and 03r's ensemble (pooled per ensemble); its change with gap
  junctions off from a regression of change on intact P4 over 03m's 80-graph panel (ensemble intercepts, one
  slope), with the fit's residual; N2's change from its 03m estimate, with the uncertainty of that estimate and
  the sampling of a fresh 2 048-genome draw (Fable, review of v1: the risk sits in graphs near N2's intact P4).
- Q-D: every fresh graph's log retained share at tick 30 from a normal per ensemble, its mean and SD drawn
  from their posterior given 03m's 16 graphs (the fit's uncertainty); N2's share from its 03m estimate, with
  that estimate's uncertainty and a fresh draw's.
- Q-B: the true response cut and change in P4 for RIA and AIY from their 03m estimates and SEs (a paired
  bootstrap over 03m's 2 048 genomes), then the estimate a sample of `qb_genomes` would give; the p-values as
  the registered normal-theory tests would compute them.
- Q-C: N2's response against 256 permutations. In 03m no permutation came within 0.07 of N2's response, which
  is 5 SEs of either; the model takes r = 0.
The four questions are drawn independently (shared N2 draws ignored), and the whole Holm procedure is applied,
and a fixed sequence for comparison. Rank-gate probabilities are reported apart from whole-procedure power."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
M03 = ROOT / "experiments" / "03m-p4-mechanism"
LOCAL = ROOT / "runs" / "p4m"
ENSEMBLES = ("SH", "SH-route", "SH-class", "SH-mirror", "SH-recip")
SEED = 20261015
SIMS = 20_000
GRAPHS = 128
PERMS = 256
TICK = 30
MARGIN_P4, MARGIN_CUT = 0.02, 0.40
BOOT = 2_000


def ens_of(name):
    for e in ENSEMBLES:
        if name.startswith(e + "-") and name[len(e) + 1:].isdigit():
            return e
    return None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def boot_ratio(rng, num_a, den_a, num_b=None, den_b=None, n=None):
    """SE of P4 (or of a paired change in P4, or of a response cut) by resampling genomes."""
    n = n or len(num_a)
    out = []
    for _ in range(BOOT):
        i = rng.integers(0, len(num_a), n)
        a = num_a[i].mean() / den_a[i].mean()
        out.append(a if num_b is None else num_b[i].mean() / den_b[i].mean() - a)
    return float(np.std(out))


def main():
    rng = np.random.default_rng(SEED)
    decay = json.loads((M03 / "decay.json").read_text(encoding="utf-8"))["graphs"]
    sup = {i: json.loads((ROOT / "experiments" / p / "supplement.json").read_text(encoding="utf-8"))["per_graph"]
           for i, p in (("03", "03-generation0"), ("03r", "03r-replication"))}
    arrays = {k: LOCAL / f"{k}-per-genome.npz" for k in ("synapses", "decay", "lesions")}
    syn, dec, les = (np.load(arrays[k], allow_pickle=False) for k in ("synapses", "decay", "lesions"))

    # ---------------------------------------------------------------- Q-A
    rows = [(ens_of(k), v["numerator"] / v["denominator"], v["gaps_off"]["P4"] - v["numerator"] / v["denominator"])
            for k, v in decay.items() if ens_of(k)]
    X = np.array([[1.0 * (e == f) for f in ENSEMBLES] + [p4] for e, p4, _ in rows])
    y = np.array([d for _, _, d in rows])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid_sd = float(np.std(y - X @ beta, ddof=X.shape[1]))
    intact_pool = {e: np.array([v["P4_turn"] for i in sup for k, v in sup[i].items() if ens_of(k) == e
                                and v.get("P4_turn") is not None]) for e in ENSEMBLES}
    fi, si = np.abs(syn["intact|final"].astype(float)), np.abs(syn["intact|steady"].astype(float))
    fg, sg = np.abs(syn["gap junctions off|final"].astype(float)), np.abs(syn["gap junctions off|steady"].astype(float))
    n2_dA = fg.mean() / sg.mean() - fi.mean() / si.mean()
    n2_dA_se = boot_ratio(rng, fi, si, fg, sg)

    # ---------------------------------------------------------------- Q-D
    ticks = list(dec["ticks"])
    t = ticks.index(TICK)
    logs = {e: np.log([v["mean_abs_difference"][t] / v["mean_abs_difference"][0] for k, v in decay.items()
                       if ens_of(k) == e]) for e in ENSEMBLES}
    dn2 = np.abs(dec["N2|diff"].astype(float))
    n2_share = dn2[t].mean() / dn2[0].mean()
    sh = []
    for _ in range(BOOT):
        i = rng.integers(0, dn2.shape[1], dn2.shape[1])
        sh.append(dn2[t, i].mean() / dn2[0, i].mean())
    n2_share_se = float(np.std(sh))

    # ---------------------------------------------------------------- Q-B
    lab = list(les["labels"])
    F, S = np.abs(les["final"].astype(float)), np.abs(les["steady"].astype(float))
    i0 = lab.index("intact")
    qb = {}
    for name in ("pair RIA", "pair AIY"):
        j = lab.index(name)
        cut = 1 - S[j].mean() / S[i0].mean()
        dp = F[j].mean() / S[j].mean() - F[i0].mean() / S[i0].mean()
        cs, ds = [], []
        for _ in range(BOOT):
            i = rng.integers(0, F.shape[1], F.shape[1])
            cs.append(1 - S[j, i].mean() / S[i0, i].mean())
            ds.append(F[j, i].mean() / S[j, i].mean() - F[i0, i].mean() / S[i0, i].mean())
        qb[name] = {"cut": float(cut), "cut_se_2048": float(np.std(cs)), "dP4": float(dp), "dP4_se_2048": float(np.std(ds))}

    def simulate(qb_genomes: int, order=None):
        k = qb_genomes / 2048
        p = {q: np.ones(SIMS) for q in "ABCD"}
        gate = {q: np.zeros(SIMS, bool) for q in "AD"}
        for s in range(SIMS):
            # Q-A
            n2 = rng.normal(n2_dA, n2_dA_se * np.sqrt(2))
            pa = []
            for e in ENSEMBLES:
                x = rng.choice(intact_pool[e], GRAPHS)
                d = beta[ENSEMBLES.index(e)] + beta[-1] * x + rng.normal(0, resid_sd, GRAPHS)
                pa.append(((d <= n2).sum() + 1) / (GRAPHS + 1))
            p["A"][s] = max(pa)
            # Q-D: normal with unknown mean and SD (posterior predictive by drawing both)
            n2s = np.log(max(rng.normal(n2_share, n2_share_se * np.sqrt(2)), 1e-9))
            pd = []
            for e in ENSEMBLES:
                v = logs[e]
                m = len(v)
                sd = np.sqrt((m - 1) * v.var(ddof=1) / rng.chisquare(m - 1))
                mu = rng.normal(v.mean(), sd / np.sqrt(m))
                g = rng.normal(mu, sd, GRAPHS)
                pd.append(((g >= n2s).sum() + 1) / (GRAPHS + 1))
            p["D"][s] = max(pd)
            # Q-B: true values from 03m's estimates, then a fresh estimate at qb_genomes
            comps = []
            for v in qb.values():
                cut_true = rng.normal(v["cut"], v["cut_se_2048"])
                dp_true = rng.normal(v["dP4"], v["dP4_se_2048"])
                cut_se, dp_se = v["cut_se_2048"] / np.sqrt(k), v["dP4_se_2048"] / np.sqrt(k)
                c_hat, d_hat = rng.normal(cut_true, cut_se), rng.normal(dp_true, dp_se)
                comps.append(norm.sf((c_hat - MARGIN_CUT) / cut_se))
                comps.append(max(norm.sf((d_hat + MARGIN_P4) / dp_se), norm.sf((MARGIN_P4 - d_hat) / dp_se)))
            p["B"][s] = max(comps)
            p["C"][s] = 1 / (PERMS + 1)
        return p

    def holm(p):
        P = np.stack([p[q] for q in "ABCD"], 1)
        order = np.argsort(P, 1)
        passed = np.zeros_like(P, bool)
        for s in range(P.shape[0]):
            for rank, q in enumerate(order[s]):
                if P[s, q] <= 0.05 / (4 - rank):
                    passed[s, q] = True
                else:
                    break
        return passed

    def sequence(p, seq):
        P = {q: p[q] for q in seq}
        ok = np.ones(SIMS, bool)
        out = {}
        for q in seq:
            ok = ok & (P[q] <= 0.05)
            out[q] = ok.copy()
        return out

    result = {}
    for qn in (2048, 16384, 65536):
        p = simulate(qn)
        h = holm(p)
        fs = sequence(p, "CADB")
        result[f"Q-B at {qn} genomes"] = {
            "each alone at 0.05": {q: float((p[q] <= 0.05).mean()) for q in "ABCD"},
            "Holm": {q: float(h[:, "ABCD".index(q)].mean()) for q in "ABCD"},
            "Holm, all four": float(h.all(1).mean()),
            "fixed sequence C, A, D, B": {q: float(fs[q].mean()) for q in "CADB"}}
    doc = {"what": "03mc design: probability of passing, simulated from 03m's data (a model; see the docstring)",
           "seed": SEED, "simulations": SIMS, "graphs_per_ensemble": GRAPHS, "permutations": PERMS, "tick": TICK,
           "inputs": {"Q-A": {"N2_change": n2_dA, "N2_change_se_2048": n2_dA_se, "slope_on_intact_P4": float(beta[-1]),
                              "residual_sd": resid_sd, "intercepts": dict(zip(ENSEMBLES, map(float, beta[:-1]))),
                              "intact_pool_sizes": {e: int(len(v)) for e, v in intact_pool.items()}},
                      "Q-D": {"N2_share": float(n2_share), "N2_share_se_2048": n2_share_se,
                              "log_share_mean_sd": {e: [float(v.mean()), float(v.std(ddof=1))] for e, v in logs.items()}},
                      "Q-B": qb,
                      "local_arrays_sha256": {k: sha(v) for k, v in arrays.items()}},
           "results": result}
    (HERE / "power.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
