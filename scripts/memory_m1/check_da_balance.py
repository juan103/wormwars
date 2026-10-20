"""M1 amendment 1, a check written after its result (docs/memory/M1-RESULTS.md, "Amendment 1's result"): on the
||da(0)|| basis, (1) the replaced balance rule applied to M1's own four arms, without the new ones, and (2) N2's mean
||da(0)|| per used stratum against the reference median's, with the new arms, so that the ratio of mean a is read as a
ratio of starting alignments only where the norms match. Reads runs/memory-m1/{summary,panel}.json, panels/*.npz and
d1_small_k/*.npz (local); writes runs/memory-m1/check_da_balance.json."""
import numpy as np

import d1_small_k as d
from common import dump


def mean_norm(Z, k, extra, edges):
    elig, obs = d.observations(Z[k], "da0", extra.get(k))
    K = len(edges) + 1
    num, cnt = np.zeros(K), np.zeros(K)
    for var, _, _, m in obs:
        st = np.digitize(var, edges)
        np.add.at(num, st[m], var[m])
        np.add.at(cnt, st[m], 1)
    return np.where(cnt > 0, num / np.maximum(cnt, 1), np.nan)


def main():
    s, Z, keys, n2keys, refs = d.inputs()
    W, by_e, gpick = d.weights(np.random.default_rng(0), keys, n2keys, refs, len(Z[keys[0]]["a"]), nres=4)
    rec, edges, used, pi = d.basis(s, "da0")
    old = d.read("da0", Z, {}, edges, used, pi, W, by_e, gpick, keys, n2keys)  # point values only; W unused for them
    extra = {}
    for k in n2keys:
        z = np.load(d.DIR / f"N2__{k[1]}.npz", allow_pickle=False)
        extra[k] = {x: {q: z[f"{q}_{x}"] for q in ("a", "d30", "da0")} for x in d.NEW}
    ref = np.nanmedian([mean_norm(Z, k, {}, edges) for k in refs], 0)
    out = {}
    for k in n2keys:
        tag = f"seed{k[1]}"
        out[tag] = {"old_arms_balance_worst": old[tag]["balance_worst"],
                    "old_arms_mean_a_ratio_per_used_stratum": {i: v["mean_a_ratio"] for i, v in old[tag]["balance_per_used_stratum"].items()},
                    "with_new_arms_mean_norm_ratio_per_used_stratum": {int(i): float(r) for i, r in
                                                                       zip(np.where(used)[0], mean_norm(Z, k, extra, edges)[used] / ref[used])}}
    dump(out, "check_da_balance.json")
    print({t: (round(v["old_arms_balance_worst"], 3), [round(x, 3) for x in v["with_new_arms_mean_norm_ratio_per_used_stratum"].values()])
           for t, v in out.items()})


if __name__ == "__main__":
    main()
