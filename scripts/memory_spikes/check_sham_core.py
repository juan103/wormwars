"""Which N2 edges survive batch 5's sham (triangles held) vs free rewiring? Kept fraction overall, inside the 30-neuron
head core (batch 6's top30_start list), between core and rest, and in triangle-rich edges."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
exec(open(Path(__file__).parent / "batch5.py").read().split("fr = []")[0])
names = list(S.CON.names)
core = [names.index(x) for x in json.load(open(S.ROOT / "runs/memory-spikes/batch6.json"))["lists"]["top30_start"]]
A0 = (S.CON.chem > 0); np.fill_diagonal(A0, False)
inc = np.zeros(S.CON.n, bool); inc[core] = True
Ai = A0.astype(np.int64)
tri = (Ai @ Ai).T * Ai + (Ai @ Ai) * Ai  # edge in a 3-cycle (first term) or as the shortcut of a ff triangle
rich = (tri > 0) & A0
print("N2 recip pairs", int((A0 & A0.T).sum() // 2), "core-internal edges", int(A0[np.ix_(inc, inc)].sum()))
out = {}
for kind, seeds, hold in (("sham", (300, 301, 302), True), ("free", (400, 401, 402), False)):
    for s in seeds:
        c, _ = swaps(S.CON.chem, 0.727, s, hold=hold)
        B = c > 0; np.fill_diagonal(B, False)
        keep = A0 & B
        r = {"kept_all": keep.sum() / A0.sum(),
             "kept_core_internal": keep[np.ix_(inc, inc)].sum() / A0[np.ix_(inc, inc)].sum(),
             "kept_core_boundary": (keep[np.ix_(inc, ~inc)].sum() + keep[np.ix_(~inc, inc)].sum()) / (A0[np.ix_(inc, ~inc)].sum() + A0[np.ix_(~inc, inc)].sum()),
             "kept_rest": keep[np.ix_(~inc, ~inc)].sum() / A0[np.ix_(~inc, ~inc)].sum(),
             "kept_triangle_edges": (keep & rich).sum() / rich.sum(), "kept_other_edges": (keep & ~rich).sum() / (A0 & ~rich).sum(),
             "core_internal_edges_after": int(B[np.ix_(inc, inc)].sum())}
        out[f"{kind}{s}"] = r
        print(kind, s, {k: round(float(v), 3) for k, v in r.items()})
json.dump(out, open(S.ROOT / "runs/memory-spikes/sham_core.json", "w"), indent=1, default=float)
