"""The wey brain: a continuous leaky rate network on a fixed connectome mask.

    tau_i dv_i/dt = -v_i + b_i + sum_j W_ij tanh(v_j) + sum_j G_ij (v_j - v_i) + I_i

`W` is nonzero only on the chemical mask; `G` is nonnegative, symmetric and nonzero only on the gap
mask. Integration is semi-implicit in the leak and in the diagonal part of the gap coupling, because
the gap term acts on raw voltage differences and explicit Euler goes unstable as soon as evolution
finds large `G` or small `tau`:

    c_i = dt / tau_i,   g_i = sum_j G_ij
    v_i <- ( v_i + c_i ( b_i + sum_j W_ij tanh(v_j) + sum_j G_ij v_j + I_i ) ) / ( 1 + c_i (1 + g_i) )

Batching. Genomes are per *strain*, and many worlds may run the same strain, so tensors are shaped
`[strains, weys, neurons]` with dense per-strain weights `[strains, neurons, neurons]`. This is the
spec's "group weys by swarm" layout with the redundant world axis folded out: a world/swarm pair is
mapped to a strain index by the caller, so one strain's weights are materialised once no matter how
many worlds use it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import Tensor

from .config import BrainConfig, MutationConfig
from .connectome.loader import Connectome


@dataclass(frozen=True)
class BrainSpec:
    """The fixed part: which edges exist, and their anatomical weights.

    Shared by every strain evolved on one graph, so it is built once per condition (N2, SH3, ...).
    """

    n: int
    chem_i: Tensor  # [E_chem] presynaptic index
    chem_j: Tensor  # [E_chem] postsynaptic index
    chem_anat: Tensor  # [E_chem] anatomical weight (weight_kind units)
    gap_i: Tensor  # [E_gap] one endpoint, i < j
    gap_j: Tensor  # [E_gap] the other
    gap_anat: Tensor  # [E_gap]
    label: str
    weight_kind: str

    @property
    def n_chem(self) -> int:
        return int(self.chem_i.numel())

    @property
    def n_gap(self) -> int:
        return int(self.gap_i.numel())

    @property
    def n_params(self) -> int:
        return self.n_chem + self.n_gap + 2 * self.n

    @property
    def device(self) -> torch.device:
        return self.chem_i.device

    def to(self, device) -> "BrainSpec":
        return BrainSpec(
            n=self.n,
            chem_i=self.chem_i.to(device),
            chem_j=self.chem_j.to(device),
            chem_anat=self.chem_anat.to(device),
            gap_i=self.gap_i.to(device),
            gap_j=self.gap_j.to(device),
            gap_anat=self.gap_anat.to(device),
            label=self.label,
            weight_kind=self.weight_kind,
        )

    @staticmethod
    def from_connectome(con: Connectome, device="cpu") -> "BrainSpec":
        chem = torch.from_numpy(np.ascontiguousarray(con.chem))
        gap = torch.from_numpy(np.ascontiguousarray(con.gap))
        ci, cj = torch.nonzero(chem > 0, as_tuple=True)
        # gap junctions are undirected: keep one entry per pair (i < j), mirrored on materialisation
        upper = torch.triu(gap, diagonal=1)
        gi, gj = torch.nonzero(upper > 0, as_tuple=True)
        return BrainSpec(
            n=con.n,
            chem_i=ci.to(device),
            chem_j=cj.to(device),
            chem_anat=chem[ci, cj].to(device),
            gap_i=gi.to(device),
            gap_j=gj.to(device),
            gap_anat=upper[gi, gj].to(device),
            label=con.label,
            weight_kind=con.weight_kind,
        )


@dataclass
class Genome:
    """Evolvable parameters for `S` strains on one `BrainSpec`.

    Only the values on the mask are stored, so a genome is 5 404 numbers for N2 rather than 182 706.
    Dense matrices are materialised for the forward pass.
    """

    spec: BrainSpec
    cfg: BrainConfig
    w: Tensor  # [S, E_chem]
    g: Tensor  # [S, E_gap], >= 0
    tau: Tensor  # [S, N]
    bias: Tensor  # [S, N]
    dale_sign: Tensor | None = None  # [S, N] fixed sign per presynaptic neuron, if Dale's law

    @property
    def n_strains(self) -> int:
        return int(self.w.shape[0])

    @property
    def device(self) -> torch.device:
        return self.w.device

    @staticmethod
    def random(
        spec: BrainSpec,
        cfg: BrainConfig,
        n_strains: int,
        generator: torch.Generator | None = None,
        device=None,
    ) -> "Genome":
        device = device or spec.device
        spec = spec.to(device)
        gen = generator
        S, N = n_strains, spec.n

        def randn(*shape):
            return torch.randn(*shape, generator=gen, device=device)

        def rand(*shape):
            return torch.rand(*shape, generator=gen, device=device)

        # |W| proportional to the anatomical weight (see Connectome.weight_kind), random sign.
        w_mag = cfg.init_w_scale * spec.chem_anat / spec.chem_anat.mean()
        sign = torch.where(rand(S, spec.n_chem) < 0.5, -1.0, 1.0)
        w = w_mag.unsqueeze(0) * sign

        dale_sign = None
        if cfg.dale:
            dale_sign = torch.where(rand(S, N) < 0.5, -1.0, 1.0)
            w = w.abs() * dale_sign[:, spec.chem_i]

        g = cfg.init_g_scale * (spec.gap_anat / spec.gap_anat.mean()).unsqueeze(0).expand(S, -1)
        g = g.contiguous()

        if cfg.init_tau_log_uniform:
            lo, hi = np.log(cfg.tau_min), np.log(cfg.tau_max)
            tau = torch.exp(rand(S, N) * (hi - lo) + lo)
        else:
            tau = rand(S, N) * (cfg.tau_max - cfg.tau_min) + cfg.tau_min

        bias = randn(S, N) * cfg.init_bias_std
        genome = Genome(spec, cfg, w, g, tau, bias, dale_sign)
        genome.clamp_()
        return genome

    def clamp_(self) -> "Genome":
        """Enforce the hard bounds. Called after every mutation, by contract."""
        cfg = self.cfg
        self.w.clamp_(-cfg.w_max, cfg.w_max)
        self.g.clamp_(0.0, cfg.g_max)
        self.tau.clamp_(cfg.tau_min, cfg.tau_max)
        self.bias.clamp_(-cfg.b_max, cfg.b_max)
        if self.dale_sign is not None:
            self.w.copy_(self.w.abs() * self.dale_sign[:, self.spec.chem_i])
        return self

    def mutate(self, mcfg: MutationConfig, generator: torch.Generator | None = None) -> "Genome":
        """Gaussian mutation in place, then clamp. Returns self for chaining."""
        gen, dev = generator, self.device

        def noise(x, sigma):
            e = torch.randn(x.shape, generator=gen, device=dev) * sigma
            if mcfg.p_mutate < 1.0:
                keep = torch.rand(x.shape, generator=gen, device=dev) < mcfg.p_mutate
                e = e * keep
            return e

        self.w.add_(noise(self.w, mcfg.w_sigma))
        self.g.add_(noise(self.g, mcfg.g_sigma))
        # tau is positive and spans a decade and a half, so it is perturbed multiplicatively
        self.tau.mul_(torch.exp(noise(self.tau, mcfg.tau_sigma)))
        self.bias.add_(noise(self.bias, mcfg.bias_sigma))
        return self.clamp_()

    def clone(self) -> "Genome":
        return Genome(
            self.spec,
            self.cfg,
            self.w.clone(),
            self.g.clone(),
            self.tau.clone(),
            self.bias.clone(),
            None if self.dale_sign is None else self.dale_sign.clone(),
        )

    def select(self, idx) -> "Genome":
        """A new genome holding copies of the strains at `idx` (a LongTensor or list)."""
        idx = torch.as_tensor(idx, dtype=torch.long, device=self.device)
        return Genome(
            self.spec,
            self.cfg,
            self.w[idx].clone(),
            self.g[idx].clone(),
            self.tau[idx].clone(),
            self.bias[idx].clone(),
            None if self.dale_sign is None else self.dale_sign[idx].clone(),
        )

    def flat(self) -> Tensor:
        """[S, n_params] view used for hashing, distance and serialisation."""
        return torch.cat([self.w, self.g, self.tau, self.bias], dim=1)

    def dense(self) -> tuple[Tensor, Tensor]:
        """Materialise `W [S,N,N]` and `G [S,N,N]` (symmetric, zero diagonal)."""
        S, N, spec = self.n_strains, self.spec.n, self.spec
        W = torch.zeros(S, N, N, device=self.device, dtype=self.w.dtype)
        W[:, spec.chem_i, spec.chem_j] = self.w
        G = torch.zeros(S, N, N, device=self.device, dtype=self.g.dtype)
        G[:, spec.gap_i, spec.gap_j] = self.g
        G[:, spec.gap_j, spec.gap_i] = self.g
        return W, G


class Brain:
    """A batch of strains ready to step. Build once per rollout; `Genome` stays the source of truth."""

    def __init__(self, genome: Genome):
        self.genome = genome
        self.cfg = genome.cfg
        self.n = genome.spec.n
        W, G = genome.dense()
        self.W = W
        self.G = G
        self.g_row = G.sum(dim=2)  # [S, N] = sum_j G_ij
        self.tau = genome.tau
        self.bias = genome.bias
        self.c = self.cfg.dt / self.tau  # [S, N]
        self.den = 1.0 + self.c * (1.0 + self.g_row)  # [S, N], constant across ticks

    @property
    def n_strains(self) -> int:
        return self.genome.n_strains

    @property
    def device(self) -> torch.device:
        return self.W.device

    def initial_state(self, n_weys: int) -> Tensor:
        return torch.zeros(self.n_strains, n_weys, self.n, device=self.device, dtype=self.W.dtype)

    def step(self, v: Tensor, current: Tensor, substeps: int | None = None) -> Tensor:
        """Advance `v [S, B, N]` by one world tick under input `current [S, B, N]` (held constant).

        `substeps` overrides the configured count; the input is held fixed across substeps because
        the world only updates once per tick.
        """
        k = self.cfg.substeps if substeps is None else substeps
        if k == self.cfg.substeps:
            c, den = self.c, self.den
        else:
            dt = 1.0 / k
            c = dt / self.tau
            den = 1.0 + c * (1.0 + self.g_row)
        c = c.unsqueeze(1)  # [S, 1, N]
        den = den.unsqueeze(1)
        drive = self.bias.unsqueeze(1) + current  # [S, B, N]
        Wt = self.W.transpose(1, 2)  # so that (tanh v) @ Wt gives sum_j W_ij tanh(v_j)
        for _ in range(k):
            chem = torch.bmm(torch.tanh(v), Wt)
            gap = torch.bmm(v, self.G)  # G symmetric, so no transpose needed
            v = (v + c * (drive + chem + gap)) / den
        return v

    def activity(self, v: Tensor) -> Tensor:
        """The bounded output the motors read."""
        return torch.tanh(v)

    def activity_bound(self) -> float:
        """Analytic bound on |v| at steady state, given the configured parameter bounds.

        From v_i (1 + g_i) = b_i + sum_j W_ij tanh(v_j) + sum_j G_ij v_j + I_i and |tanh| <= 1:
        |v|_max <= b_max + w_max * max_in_degree + input_max.
        """
        in_deg = torch.bincount(self.genome.spec.chem_j, minlength=self.n).max().item()
        cfg = self.cfg
        return cfg.b_max + cfg.w_max * float(in_deg) + cfg.input_max


def inject(current: Tensor, neuron_idx: Tensor, values: Tensor, gain: Tensor) -> Tensor:
    """Scatter sensor channel values into the input current tensor.

    `current [S,B,N]`, `neuron_idx [C]`, `values [S,B,C]`, `gain [C]`. Channels that name the same
    neuron accumulate, which is why this is an index_add rather than an assignment.
    """
    return current.index_add_(2, neuron_idx, values * gain)
