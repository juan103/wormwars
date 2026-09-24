"""The wey brain: a continuous leaky rate network on a fixed connectome mask.

    tau_j dv_j/dt = -v_j + b_j + sum_i W[i, j] tanh(v_i) + sum_i G[i, j] (v_i - v_j) + I_j

`W[i, j]` is the chemical synapse from presynaptic neuron i to postsynaptic neuron j, the same
orientation as `Connectome.chem[i, j]`, so neuron j is driven by the neurons that synapse onto it.
`W` is nonzero only on the chemical mask; `G` is nonnegative, symmetric and nonzero only on the gap
mask. Integration is semi-implicit in the leak and in the diagonal part of the gap coupling, because
the gap term acts on raw voltage differences and explicit Euler goes unstable as soon as evolution
finds large `G` or small `tau`:

    c_j = dt / tau_j,   g_j = sum_i G[i, j]
    v_j <- ( v_j + c_j ( b_j + sum_i W[i, j] tanh(v_i) + sum_i G[i, j] v_i + I_j ) ) / ( 1 + c_j (1 + g_j) )

Direction. Experiment 01 ran with the chemical term reversed -- `sum_i W[j, i] tanh(v_i)`, so a
neuron was driven by the neurons it synapses onto -- because the update multiplied by `W^T` while
`W` was stored pre-by-post (DECISIONS.md D031). That update survives as
`BrainConfig.chem_direction = "post_to_pre"`, only so experiment 01 reproduces exactly.

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

from .config import CHEM_DIRECTIONS, BrainConfig, MutationConfig
from .connectome.loader import Connectome

MAGNITUDE_MODES = ("anatomical", "uniform", "permuted")


def _apply_magnitude_mode(mag: Tensor, mode: str, scale: float, seed: int, salt: int) -> Tensor:
    """Transform anatomical initial magnitudes. "anatomical" returns `mag` itself, untouched, so
    the default path performs exactly the arithmetic it always did."""
    if mode == "anatomical":
        return mag
    if mode == "uniform":
        return torch.full_like(mag, scale)
    if mode == "permuted":
        # a private CPU generator: must not consume the genome's generator, so signs, biases and
        # time constants stay paired with the anatomical draw
        gen = torch.Generator().manual_seed(int(seed) * 2 + salt)
        perm = torch.randperm(mag.numel(), generator=gen).to(mag.device)
        return mag[perm]
    raise ValueError(f"init magnitude mode must be one of {MAGNITUDE_MODES}, got {mode!r}")


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
        w_mag = _apply_magnitude_mode(
            w_mag, cfg.init_chem_magnitude, cfg.init_w_scale, cfg.init_permutation_seed, 0
        )
        sign = torch.where(rand(S, spec.n_chem) < 0.5, -1.0, 1.0)
        w = w_mag.unsqueeze(0) * sign

        dale_sign = None
        if cfg.dale:
            dale_sign = torch.where(rand(S, N) < 0.5, -1.0, 1.0)
            # one sign per PRESYNAPTIC neuron. Under the legacy post_to_pre update (D031) the
            # presynaptic index is the receiving end, so Dale's law must not be combined with it.
            w = w.abs() * dale_sign[:, spec.chem_i]

        g_mag = cfg.init_g_scale * (spec.gap_anat / spec.gap_anat.mean())
        g_mag = _apply_magnitude_mode(
            g_mag, cfg.init_gap_magnitude, cfg.init_g_scale, cfg.init_permutation_seed, 1
        )
        g = g_mag.unsqueeze(0).expand(S, -1)
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
        if self.cfg.chem_direction not in CHEM_DIRECTIONS:
            raise ValueError(
                f"chem_direction must be one of {CHEM_DIRECTIONS}, got {self.cfg.chem_direction!r}"
            )
        W, G = genome.dense()
        self.W = W
        # `(tanh v) @ M` gives each neuron its chemical drive. W is stored pre-by-post, so M = W
        # sends signal pre -> post. The legacy M = W^T sends it post -> pre (experiment 01, D031).
        self.W_drive = W if self.cfg.chem_direction == "pre_to_post" else W.transpose(1, 2)
        self.G = G
        self.g_row = G.sum(dim=2)  # [S, N] = sum_j G_ij
        self.tau = genome.tau
        self.bias = genome.bias
        self.c = self.cfg.dt / self.tau  # [S, N]
        self.den = 1.0 + self.c * (1.0 + self.g_row)  # [S, N], constant across ticks
        # Optional per-strain silencing mask, [S, 1, N] of 1.0 (alive) / 0.0 (silenced). Kept per
        # strain so that dozens of different ablations of the same champion run in one batch.
        self.silence_mask: Tensor | None = None

    def silence(self, per_strain: list[list[int]] | None) -> "Brain":
        """Clamp the named neurons to zero after every substep, one neuron list per strain.

        A silenced neuron emits tanh(0) = 0 and contributes nothing to the gap coupling, which is
        the cleanest definition of "this cell is not participating" in a rate model.
        """
        if per_strain is None:
            self.silence_mask = None
            return self
        if len(per_strain) != self.n_strains:
            raise ValueError(f"{len(per_strain)} ablations for {self.n_strains} strains")
        mask = torch.ones(self.n_strains, 1, self.n, device=self.device, dtype=self.W.dtype)
        for s, idx in enumerate(per_strain):
            if idx:
                mask[s, 0, torch.as_tensor(list(idx), device=self.device)] = 0.0
        self.silence_mask = mask
        return self

    def cut_gap(self, pairs: list[list[tuple[int, int]]]) -> "Brain":
        """Zero specific gap junctions per strain, e.g. the RIP-I1 bridge. Symmetric, in place."""
        for s, plist in enumerate(pairs):
            for i, j in plist:
                self.G[s, i, j] = 0.0
                self.G[s, j, i] = 0.0
        self.g_row = self.G.sum(dim=2)
        self.den = 1.0 + self.c * (1.0 + self.g_row)
        return self

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
        M = self.W_drive  # see __init__: the chemical term, oriented by cfg.chem_direction
        mask = self.silence_mask
        for _ in range(k):
            chem = torch.bmm(torch.tanh(v), M)
            gap = torch.bmm(v, self.G)  # G symmetric, so no transpose needed
            v = (v + c * (drive + chem + gap)) / den
            if mask is not None:
                v = v * mask
        return v

    def activity(self, v: Tensor) -> Tensor:
        """The bounded output the motors read."""
        return torch.tanh(v)

    def activity_bound(self) -> float:
        """Analytic bound on |v| at steady state, given the configured parameter bounds.

        From v_i (1 + g_i) = b_i + sum_j W_ij tanh(v_j) + sum_j G_ij v_j + I_i and |tanh| <= 1:
        |v|_max <= b_max + w_max * max_in_degree + input_max.
        """
        # The receiving end of each synapse is the postsynaptic neuron, except under the legacy
        # reversed update, where drive arrives at the presynaptic one.
        spec = self.genome.spec
        receivers = spec.chem_j if self.cfg.chem_direction == "pre_to_post" else spec.chem_i
        in_deg = torch.bincount(receivers, minlength=self.n).max().item()
        cfg = self.cfg
        return cfg.b_max + cfg.w_max * float(in_deg) + cfg.input_max
