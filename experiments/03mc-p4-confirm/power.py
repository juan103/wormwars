"""03mc: model-based predictive pass probabilities for the registered procedure, from 03m's data (DESIGN.md §6).

    python experiments/03mc-p4-confirm/power.py      # writes power.json beside this file

These are predictions under stated models, not established operating characteristics (Astra, review v2). They use
03m's committed summaries, its local per-genome arrays (`runs/p4m/*.npz`, not committed; hashes recorded), and 03's
and 03r's committed supplements.

**N2's quantities are drawn jointly** (v2, Astra): one paired bootstrap over 03m's 2 048 N2 genomes, which are the
same genomes in 03m's synapses, lesions, decay and weights arrays, gives the covariance at 2 048 genomes of
[Q-A's change with gaps off, Q-D's share at tick 30, RIA's cut, RIA's change in P4, AIY's cut, AIY's change in P4,
N2's response]. N2's true values are drawn from a normal around 03m's estimates with that covariance; the fresh
batch 0 adds one draw of the same covariance; Q-B's 65 536-genome estimates add batch 0's draw and 31 more batches'
mean, (e0 + 31 e')/32.

- **Q-A:** each fresh graph's intact P4 from 03's and 03r's ensemble (pooled per ensemble); its change from a
  regression on intact P4 over 03m's 80 graphs (ensemble intercepts, one slope), with the coefficients and the
  residual SD drawn from their posterior (reference prior) once per simulated study.
- **Q-D:** each fresh graph's log share at tick 30 from a normal per ensemble whose mean and SD are drawn from
  their posterior given 03m's 16 graphs (reference prior p(mu, sigma^2) proportional to 1/sigma^2).
- **Q-B:** the registered normal-theory tests on the drawn estimates, with SEs scaled from 2 048 genomes.
- **Q-C:** each fresh permutation's log response from a normal fitted to 03m's 64 paired permutations (posterior
  draws as Q-D), against N2's drawn response.
- **Tails:** the main model is normal; a sensitivity replaces the graph-level normals (Q-A's residuals, Q-D's log
  shares, Q-C's log responses) by Student t with 5 degrees of freedom at the same SD.
The four questions then go through the whole Holm procedure; a fixed sequence is shown for comparison. Q-D's
endpoint is also compared across ticks 10-50 (DESIGN.md §4)."""

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
SEED = 20261016
SIMS = 20_000
TICK_SIMS = 5_000
GRAPHS = 128
PERMS = 256
TICK = 30
QB_GENOMES = 65_536
MARGIN_P4, MARGIN_CUT = 0.02, 0.40
BOOT = 4_000
T_DF = 5
KEYS = ("dA", "share", "RIA_cut", "RIA_dP4", "AIY_cut", "AIY_dP4", "response")


def ens_of(name):
    for e in ENSEMBLES:
        if name.startswith(e + "-") and name[len(e) + 1:].isdigit():
            return e
    return None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs():
    decay = json.loads((M03 / "decay.json").read_text(encoding="utf-8"))["graphs"]
    weights = json.loads((M03 / "weights.json").read_text(encoding="utf-8"))["permutations"]["paired"]
    sup = {i: json.loads((ROOT / "experiments" / p / "supplement.json").read_text(encoding="utf-8"))["per_graph"]
           for i, p in (("03", "03-generation0"), ("03r", "03r-replication"))}
    arrays = {k: LOCAL / f"{k}-per-genome.npz" for k in ("synapses", "decay", "lesions")}
    npz = {k: np.load(v, allow_pickle=False) for k, v in arrays.items()}
    return decay, weights, sup, arrays, npz


def n2_vector(npz, idx, tick):
    """N2's quantities on the genomes `idx` (all 2 048 for the estimate; a resample for the bootstrap)."""
    syn, dec, les = npz["synapses"], npz["decay"], npz["lesions"]
    a = lambda x: np.abs(x.astype(np.float64))[idx]  # noqa: E731
    fi, si = a(syn["intact|final"]), a(syn["intact|steady"])
    fg, sg = a(syn["gap junctions off|final"]), a(syn["gap junctions off|steady"])
    d = np.abs(dec["N2|diff"].astype(np.float64))[:, idx]
    ticks = [int(t) for t in dec["ticks"]]
    lab = list(les["labels"])
    F, S = np.abs(les["final"].astype(np.float64))[:, idx], np.abs(les["steady"].astype(np.float64))[:, idx]
    i0 = lab.index("intact")
    out = {"dA": fg.mean() / sg.mean() - fi.mean() / si.mean(),
           "share": d[ticks.index(tick)].mean() / d[0].mean(), "response": si.mean()}
    for name, key in (("pair RIA", "RIA"), ("pair AIY", "AIY")):
        j = lab.index(name)
        out[f"{key}_cut"] = 1 - S[j].mean() / S[i0].mean()
        out[f"{key}_dP4"] = F[j].mean() / S[j].mean() - F[i0].mean() / S[i0].mean()
    return np.array([out[k] for k in KEYS])


def posterior_normal(rng, v):
    """mu, sd drawn from the reference-prior posterior of a normal sample `v`."""
    m = len(v)
    sd = np.sqrt((m - 1) * np.var(v, ddof=1) / rng.chisquare(m - 1))
    return rng.normal(np.mean(v), sd / np.sqrt(m)), sd


def draw(rng, mu, sd, size, tails):
    if tails == "normal":
        return rng.normal(mu, sd, size)
    return mu + sd * rng.standard_t(T_DF, size) / np.sqrt(T_DF / (T_DF - 2))


def holm(P):
    """P [sims, 4] -> passed [sims, 4], Holm at 0.05 in p order, stopping at the first failure."""
    order = np.argsort(P, 1, kind="stable")
    passed = np.zeros_like(P, bool)
    going = np.ones(P.shape[0], bool)
    for rank in range(P.shape[1]):
        q = order[:, rank]
        p = P[np.arange(P.shape[0]), q]
        ok = going & (p <= 0.05 / (P.shape[1] - rank))
        passed[np.arange(P.shape[0]), q] = ok
        going = ok
    return passed


def main():
    rng = np.random.default_rng(SEED)
    decay, weights, sup, arrays, npz = load_inputs()
    n_gen = npz["synapses"]["intact|final"].shape[0]

    def joint(tick):
        est = n2_vector(npz, np.arange(n_gen), tick)
        boots = np.array([n2_vector(npz, rng.integers(0, n_gen, n_gen), tick) for _ in range(BOOT)])
        return est, np.cov(boots.T)

    est, cov = joint(TICK)

    # Q-A's regression and its posterior
    rows = [(ens_of(k), v["numerator"] / v["denominator"], v["gaps_off"]["P4"] - v["numerator"] / v["denominator"])
            for k, v in decay.items() if ens_of(k)]
    X = np.array([[1.0 * (e == f) for f in ENSEMBLES] + [p4] for e, p4, _ in rows])
    y = np.array([d for _, _, d in rows])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    dof = X.shape[0] - X.shape[1]
    s2 = float(np.sum((y - X @ beta) ** 2) / dof)
    xtx_inv = np.linalg.inv(X.T @ X)
    intact_pool = {e: np.array([v["P4_turn"] for i in sup for k, v in sup[i].items() if ens_of(k) == e
                                and v.get("P4_turn") is not None]) for e in ENSEMBLES}
    # Q-D's per-ensemble samples, Q-C's permutations
    def logs_at(tick):
        ticks = [int(t) for t in npz["decay"]["ticks"]]
        t = ticks.index(tick)
        return {e: np.log([v["mean_abs_difference"][t] / v["mean_abs_difference"][0] for k, v in decay.items()
                           if ens_of(k) == e]) for e in ENSEMBLES}
    logs = logs_at(TICK)
    perm_log = np.log([v["denominator"] for v in weights.values() if v["valid"]])

    def simulate(sims, tails, est, cov, logs, qb_genomes=QB_GENOMES):
        k = qb_genomes / 2048
        P = np.ones((sims, 4))
        for s in range(sims):
            truth = rng.multivariate_normal(est, cov)
            e0 = rng.multivariate_normal(np.zeros(len(KEYS)), cov)
            batch0 = truth + e0
            rest = rng.multivariate_normal(np.zeros(len(KEYS)), cov / max(k - 1, 1e-9)) if k > 1 else 0 * e0
            pooled = truth + (e0 + (k - 1) * rest) / k
            v = dict(zip(KEYS, batch0))
            # Q-A
            sig2 = dof * s2 / rng.chisquare(dof)
            b = rng.multivariate_normal(beta, sig2 * xtx_inv)
            pa = []
            for i, e in enumerate(ENSEMBLES):
                x = rng.choice(intact_pool[e], GRAPHS)
                d = b[i] + b[-1] * x + draw(rng, 0.0, np.sqrt(sig2), GRAPHS, tails)
                pa.append(((d <= v["dA"]).sum() + 1) / (GRAPHS + 1))
            P[s, 0] = max(pa)
            # Q-B
            w = dict(zip(KEYS, pooled))
            comps = []
            for key in ("RIA", "AIY"):
                cse = np.sqrt(cov[KEYS.index(f"{key}_cut"), KEYS.index(f"{key}_cut")] / k)
                dse = np.sqrt(cov[KEYS.index(f"{key}_dP4"), KEYS.index(f"{key}_dP4")] / k)
                comps.append(norm.sf((w[f"{key}_cut"] - MARGIN_CUT) / cse))
                comps.append(max(norm.sf((w[f"{key}_dP4"] + MARGIN_P4) / dse), norm.sf((MARGIN_P4 - w[f"{key}_dP4"]) / dse)))
            P[s, 1] = max(comps)
            # Q-C
            mu, sd = posterior_normal(rng, perm_log)
            g = draw(rng, mu, sd, PERMS, tails)
            P[s, 2] = ((g >= np.log(max(v["response"], 1e-12))).sum() + 1) / (PERMS + 1)
            # Q-D
            n2s = np.log(max(v["share"], 1e-12))
            pd = []
            for e in ENSEMBLES:
                mu, sd = posterior_normal(rng, logs[e])
                g = draw(rng, mu, sd, GRAPHS, tails)
                pd.append(((g >= n2s).sum() + 1) / (GRAPHS + 1))
            P[s, 3] = max(pd)
        return P

    def summarise(P):
        h = holm(P)
        seq, ok = {}, np.ones(P.shape[0], bool)
        for q in "CADB":
            ok = ok & (P[:, "ABCD".index(q)] <= 0.05)
            seq[q] = float(ok.mean())
        return {"each alone at 0.05": {q: float((P[:, i] <= 0.05).mean()) for i, q in enumerate("ABCD")},
                "Holm": {q: float(h[:, i].mean()) for i, q in enumerate("ABCD")},
                "Holm, all four": float(h.all(1).mean()), "fixed sequence C, A, D, B": seq}

    results = {}
    for tails in ("normal", "t5"):
        results[tails] = summarise(simulate(SIMS, tails, est, cov, logs))
    results["normal, Q-B at 16 384 genomes"] = summarise(simulate(SIMS // 4, "normal", est, cov, logs, 16_384))
    ticks = {}
    for t in (10, 20, 30, 40, 50):
        e_t, c_t = joint(t)
        P = simulate(TICK_SIMS, "normal", e_t, c_t, logs_at(t))
        ticks[t] = {"Q-D alone at 0.05": float((P[:, 3] <= 0.05).mean()), "Q-D under Holm": float(holm(P)[:, 3].mean())}
    doc = {"what": "03mc design: model-based predictive pass probabilities from 03m's data (see the docstring)",
           "seed": SEED, "simulations": SIMS, "tick_simulations": TICK_SIMS, "graphs_per_ensemble": GRAPHS,
           "permutations": PERMS, "tick": TICK, "qb_genomes": QB_GENOMES, "bootstrap": BOOT,
           "inputs": {"N2_estimates": dict(zip(KEYS, map(float, est))),
                      "N2_se_2048": dict(zip(KEYS, map(float, np.sqrt(np.diag(cov))))),
                      "N2_correlations": {f"{KEYS[i]}~{KEYS[j]}": float(cov[i, j] / np.sqrt(cov[i, i] * cov[j, j]))
                                          for i in range(len(KEYS)) for j in range(i + 1, len(KEYS))},
                      "Q-A": {"slope_on_intact_P4": float(beta[-1]), "slope_se": float(np.sqrt(s2 * xtx_inv[-1, -1])),
                              "residual_sd": float(np.sqrt(s2)), "intercepts": dict(zip(ENSEMBLES, map(float, beta[:-1]))),
                              "intact_pool_sizes": {e: int(len(v)) for e, v in intact_pool.items()}},
                      "Q-C": {"permutations": int(len(perm_log)), "log_response_mean_sd": [float(perm_log.mean()),
                                                                                         float(perm_log.std(ddof=1))]},
                      "Q-D": {"log_share_mean_sd": {e: [float(v.mean()), float(v.std(ddof=1))] for e, v in logs.items()}},
                      "local_arrays_sha256": {k: sha(v) for k, v in arrays.items()}},
           "results": results, "Q-D by tick": ticks}
    (HERE / "power.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"results": results, "Q-D by tick": ticks}, indent=1))


if __name__ == "__main__":
    main()
