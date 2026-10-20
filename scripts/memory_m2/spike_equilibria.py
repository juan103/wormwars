"""M2 pilot plan, the spike behind its "facts used" (docs/memory/M2-PILOT-PLAN.md): 64 of N2's seed-7600 genomes, M1's
probe followed for 2000 ticks, then Newton's method in float64 on H(v) = d + tanh(v) M + v G - v (1 + g), whose zeros are
the fixed points of every substep count and every set of time constants. Prints the timing, the residuals, the
distances from the end states, and the genomes ending in distinct equilibria with their stability. Exploratory.
Usage: python scripts/memory_m2/spike_equilibria.py > runs/memory-m2/spike_equilibria.txt"""
import sys, time, numpy as np, torch
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "memory_m1"))
from common import S, ramp, follow, at, START_FLOOR, REMAIN, SETTLE_TOL
from wormwars.brain import Brain
torch.set_grad_enabled(False)
n = 64
g, cfg = S.genomes(S.CON, n, 7600)
brain, v, food = ramp(g, cfg)
cur = at(cfg, S.CON.n, n, [food, food])
x = v.clone(); t0 = time.time()
for t in range(2000):
    x = brain.step(x, cur)
print("2000 ticks", round(time.time() - t0, 1), "s")
# float64 equilibrium: H(v) = drive + tanh(v) M + v G - v (1 + g_row) = 0, independent of tau and dt
M, G = brain.W_drive.double(), brain.G.double(); grow = brain.g_row.double()
drive = (brain.bias.unsqueeze(1) + cur).double()
def H(u): return drive + torch.bmm(torch.tanh(u), M) + torch.bmm(u, G) - u * (1 + grow.unsqueeze(1))
u = x.double().clone()
r0 = H(u).abs().amax((1, 2))
I = torch.eye(S.CON.n, dtype=torch.float64)
for it in range(20):
    h = H(u)
    # dH_j/du_i = sech^2(u_i) M_ij + G_ij - delta_ij (1+g_row_j); row-vector convention: h = u A  => solve du A = -h
    sech2 = 1 - torch.tanh(u) ** 2
    for b in range(2):
        A = sech2[:, b, :, None] * M + G - torch.diag_embed(1 + grow)  # [S, N, N], A[i, j] = dH_j/du_i
        du = torch.linalg.solve(A.transpose(1, 2), -h[:, b, :, None])[..., 0]
        u[:, b] += du
res = H(u).abs().amax(2)
dist = (u - x.double()).abs().amax(2)
sep = (u[:, 0] - u[:, 1]).abs().amax(1)
# stability: tau dv/dt = H(v): J_ct = diag(1/tau) A^T
tau = brain.tau.double()
stab = []
for b in range(2):
    sech2 = 1 - torch.tanh(u[:, b]) ** 2
    A = sech2[:, :, None] * M + G - torch.diag_embed(1 + grow)
    ev = torch.linalg.eigvals(A.transpose(1, 2) / tau[:, :, None])
    stab.append(ev.real.max(1).values.numpy())
print("initial residual median", float(r0.median()), "after newton max", float(res.max()))
print("dist end->eq quantiles", np.quantile(dist.numpy(), [.5, .9, 1]))
print("sep >1e-6:", int((sep > 1e-6).sum()), "of", n, "; max Re", np.round(np.max(stab, 0)[sep.numpy() > 1e-6], 4))
print("any unstable eq among converged:", int(((np.max(stab, 0) > 0) & (dist.max(1).values.numpy() < 1e-3)).sum()))
# H built from the float64 brain's own matrices: its roots must be fixed by one tick of the float64 integrator at any
# substep count; built from the float32 brain's matrices cast to float64 they are not quite (the product with the
# Dale signs and the gap row sums are rounded in float32)
g64 = g.with_params(**{k: (getattr(g, k).double() if getattr(g, k) is not None else None) for k in g.PARAMS})
b64 = Brain(g64)
M6, G6, gr6 = b64.W_drive, b64.G, b64.g_row
d6 = b64.bias.unsqueeze(1) + cur.double()
H6 = lambda q: d6 + torch.bmm(torch.tanh(q), M6) + torch.bmm(q, G6) - q * (1 + gr6.unsqueeze(1))  # noqa: E731
for name, Hf, MM, GG, gg in (("float32 matrices cast", H, M, G, grow), ("float64 brain", H6, M6, G6, gr6)):
    q = x.double().clone()
    for it in range(20):
        h = Hf(q)
        s2 = 1 - torch.tanh(q) ** 2
        for b in range(2):
            A = s2[:, b, :, None] * MM + GG - torch.diag_embed(1 + gg)
            q[:, b] += torch.linalg.solve(A.transpose(1, 2), -h[:, b, :, None])[..., 0]
    ok = Hf(q).abs().amax((1, 2)) < 1e-10
    for k in (8, 32, 64):
        y = b64.step(q, cur.double(), substeps=k)
        print(f"H from {name}: one float64 tick at {k} substeps moves a located root by at most",
              float((y - q)[ok].abs().max()), f"({int(ok.sum())} of {n} genomes located in both histories)")
