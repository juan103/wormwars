"""M2 pilot (docs/memory/M2-PILOT-PLAN.md): the equilibrium tools. Under constant input a state is fixed by one substep of
`Brain.step` if and only if H(v) = d + tanh(v) M + v G - v * (1 + g) = 0 (no tau, no substep length). Newton's method
on H in float64 locates roots; P, one substep linearised at a root, gives the integrator's own stability. H is always
built from the float64 brain that the trajectories are checked with (a root of H from float32 matrices cast to float64
moves by about 1e-7 under one float64 tick; `spike_equilibria.py`). Exploratory; CPU."""
from __future__ import annotations

import numpy as np
import torch

from wormwars.brain import Brain

NEWTON_TOL, NEWTON_ITERS = 1e-12, 100


def brain64(genome):
    """The float64 brain of a genome. M1's probe uses no silence mask, clamp or output gate; any of them changes H."""
    g = genome.with_params(**{k: (getattr(genome, k).double() if getattr(genome, k) is not None else None)
                              for k in genome.PARAMS})
    b = Brain(g)
    assert b.silence_mask is None and b.clamp_mask is None and b.output_gate is None
    return b


class System:
    """H and its Jacobian for strains s of a float64 brain under a constant input current [S, 1, N] (float64)."""

    def __init__(self, b64: Brain, current: torch.Tensor):
        self.b = b64
        self.M, self.G, self.g = b64.W_drive, b64.G, b64.g_row  # [S, N, N], [S, N, N], [S, N]
        self.d = b64.bias + current[:, 0, :].double()  # [S, N]
        self.tau = b64.tau

    def H(self, v, idx=None):
        """v [S', N] -> [S', N]; idx selects the strains v belongs to (all if None; Astra, round 3: the matrices must be
        sliced with the state)."""
        M, G, g, d = (self.M, self.G, self.g, self.d) if idx is None else (self.M[idx], self.G[idx], self.g[idx], self.d[idx])
        return d + torch.bmm(torch.tanh(v).unsqueeze(1), M)[:, 0] + torch.bmm(v.unsqueeze(1), G)[:, 0] - v * (1 + g)

    def J(self, v, idx=None):
        """J[s, i, j] = dH_j / dv_i (row-vector convention: dH = dv J), A in the plan."""
        M, G, g = (self.M, self.G, self.g) if idx is None else (self.M[idx], self.G[idx], self.g[idx])
        return (1 - torch.tanh(v) ** 2).unsqueeze(2) * M + G - torch.diag_embed(1 + g)

    def newton(self, v0, iters=NEWTON_ITERS, tol=NEWTON_TOL):
        """Damped Newton (backtracking on max |H|) from v0 [S, N]. Returns a dict: the iterate, per strain whether max |H|
        fell below tol, the final residual, the last accepted step's size, the iterations used, and how many line searches
        failed to reduce the residual (Fable, round 3: such a step is recorded, not counted as progress) or met a
        singular A (solved by least squares instead of aborting the batch)."""
        v = v0.double().clone()
        n = len(v)
        res = self.H(v).abs().amax(1)
        done = res < tol
        last = torch.zeros(n, dtype=v.dtype)
        used = torch.zeros(n, dtype=torch.long)
        failed_ls = torch.zeros(n, dtype=torch.long)
        singular = torch.zeros(n, dtype=torch.long)
        gave_up = torch.zeros(n, dtype=torch.bool)  # persistent (Fable, Astra, round 4)
        for _ in range(iters):
            act = torch.where(~done & ~gave_up)[0]
            if len(act) == 0:
                break
            h = self.H(v[act], act)
            A = self.J(v[act], act).transpose(1, 2)
            sol, info = torch.linalg.solve_ex(A, -h.unsqueeze(2))
            bad = info != 0
            if bool(bad.any()):
                sol[bad] = torch.linalg.lstsq(A[bad], -h[bad].unsqueeze(2)).solution
                singular[act[bad]] += 1
            step = sol[..., 0]
            r0 = h.abs().amax(1)
            lam = torch.ones(len(act), dtype=v.dtype)
            trial = v[act] + step
            r1 = self.H(trial, act).abs().amax(1)
            for _ in range(30):  # halve the step where the residual did not fall
                worse = ~(r1 < r0)
                if not bool(worse.any()):
                    break
                lam = torch.where(worse, lam / 2, lam)
                trial = v[act] + lam.unsqueeze(1) * step
                r1 = self.H(trial, act).abs().amax(1)
            ok = r1 < r0
            failed_ls[act[~ok]] += 1
            v[act[ok]] = trial[ok]  # a failed line search leaves the iterate where it was
            last[act[ok]] = (lam[ok].unsqueeze(1) * step[ok]).abs().amax(1)
            used[act] += 1
            res[act[ok]] = r1[ok]
            done = res < tol
            gave_up |= failed_ls >= 3  # three failed searches: that strain is given up for good (not located)
        located = (res < tol).numpy()
        return {"v": v, "located": located, "residual": res.numpy(), "last_step": last.numpy(), "iterations": used.numpy(),
                "failed_line_searches": failed_ls.numpy(), "singular_solves": singular.numpy()}

    def error_bound(self, out):
        """e = max(the size of one further Newton step at the final iterate, residual / sigma_min(A)) per strain. The last
        accepted step measures the previous iterate's error, not the final one's, so the further step is used. The
        residual is a max norm and sigma_min a 2-norm quantity, so the second term understates the 2-norm bound by up
        to sqrt(N) (about 17); the plan's 1000x margin between the accuracy gate (1e-9) and the distinct-root threshold
        (1e-6) covers that (Fable, round 3)."""
        v = out["v"]
        sol, info = torch.linalg.solve_ex(self.J(v).transpose(1, 2), -self.H(v).unsqueeze(2))
        nxt = sol[..., 0].abs().amax(1).numpy()
        nxt = np.where(info.numpy() == 0, nxt, np.inf)
        return np.maximum(nxt, out["residual"] / np.maximum(self.smallest_singular(v), 1e-300))

    def smallest_singular(self, v):
        return torch.linalg.svdvals(self.J(v)).amin(1).numpy()

    def P(self, v, substeps):
        """One substep linearised at v, in column form x' = P x: P = I + diag(h / (tau + h (1 + g))) J^T."""
        h = 1.0 / substeps
        scale = h / (self.tau + h * (1 + self.g))  # [S, N]
        n = v.shape[1]
        return torch.eye(n, dtype=v.dtype) + scale.unsqueeze(2) * self.J(v).transpose(1, 2)

    def stability(self, v, substeps, margin=1e-6):
        """P's spectral radius per substep; 'stable' below 1 - margin, 'unstable' above 1 + margin, else 'marginal'; and
        the largest real part of diag(1/tau) J^T, the continuous sign, beside it."""
        rho = torch.linalg.eigvals(self.P(v, substeps)).abs().amax(1).numpy()
        cont = torch.linalg.eigvals(self.J(v).transpose(1, 2) / self.tau.unsqueeze(2)).real.amax(1).numpy()
        verdict = np.where(rho < 1 - margin, "stable", np.where(rho > 1 + margin, "unstable", "marginal"))
        return verdict, rho, cont


def tick_autograd(b64: Brain, v, current):
    """The derivative of one tick of `Brain.step` itself (all its substeps) at v [S, N], by automatic differentiation,
    in column form x' = D x. At a root of H every substep has the same linearisation P, so D must equal P^k (R4'):
    a check of P against the integrator, not against a reimplementation of it."""
    s, n = v.shape
    D = torch.zeros(s, n, n, dtype=v.dtype)
    with torch.enable_grad():
        x = v.clone().unsqueeze(1).requires_grad_(True)
        y = b64.step(x, current.double())[:, 0, :]
        for i in range(n):
            (gi,) = torch.autograd.grad(y[:, i].sum(), x, retain_graph=True)
            D[:, i, :] = gi[:, 0, :]
    return D
