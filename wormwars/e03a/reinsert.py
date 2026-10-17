"""Reinserting a deleted neuron X with searchable wiring (experiments/03a-self-consistency/DESIGN.md v7.1 §3, §5, §6).

**The union mask.** For a target X, the union connectome is the graph with every edge touching X removed, plus every
possible edge between X and each other neuron (a candidate): a chemical edge from the candidate onto X ("in"), one
from X onto the candidate ("out") and a gap junction ("gap"), and X's chemical self-connection if the graph has one
(its presence is kept, its weight searched and never scored, §5). The union's edges depend only on the graph with X
deleted, never on X's true partners. A search state chooses which of X's edges are present, with the true number per
type, and their weights; an absent edge has weight exactly 0, which is the network built without that edge (tested,
including gap contributions to neighbours' denominators).

**The background.** Every parameter not belonging to X is copied, by edge identity, from one source brain: an intact
brain (MIP), whose X edges are dropped, which is deletion (D044), or a brain evolved with X deleted (NIP). It is never
re-initialised, and materialising a state never changes it (tested bitwise).

Dale's law is refused: X's weights carry their own signs.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

import numpy as np
import torch
from torch import Tensor

from ..brain import BrainSpec, Genome
from ..connectome.loader import Connectome

TYPES = ("in", "out", "gap")


def candidates(n: int, x: int) -> np.ndarray:
    """Every neuron but X, ascending: the candidate pool of every connection type (§5)."""
    return np.array([i for i in range(n) if i != x], dtype=np.int64)


def truth(con: Connectome, x: int) -> dict:
    """X's true partners per connection type, as boolean arrays over `candidates(con.n, x)`."""
    c = candidates(con.n, x)
    return {"in": con.chem[c, x] > 0, "out": con.chem[x, c] > 0, "gap": con.gap[x, c] > 0}


def true_counts(con: Connectome, x: int) -> dict:
    """What the search is told: X's numbers of partners per type (never which ones)."""
    return {k: int(v.sum()) for k, v in truth(con, x).items()}


def has_self_loop(con: Connectome, x: int) -> bool:
    return bool(con.chem[x, x] > 0)


def union_connectome(con: Connectome, x: int) -> Connectome:
    """The graph with X's edges removed and every candidate edge of X added (anatomical weight 1, which nothing reads:
    X's weights come from the search state and the background from the source brain)."""
    chem = np.array(con.chem, dtype=np.float32, copy=True)
    gap = np.array(con.gap, dtype=np.float32, copy=True)
    loop = has_self_loop(con, x)
    chem[x, :] = chem[:, x] = 0
    gap[x, :] = gap[:, x] = 0
    c = candidates(con.n, x)
    chem[c, x] = chem[x, c] = 1.0
    gap[c, x] = gap[x, c] = 1.0
    if loop:
        chem[x, x] = 1.0
    return con.with_masks(chem, gap, f"{con.label}-union-{con.names[x]}")


def partner_connectome(con: Connectome, x: int, partners: dict, self_loop: bool | None = None) -> Connectome:
    """The graph with X wired to exactly `partners` (boolean arrays over the candidates, per type): the network a
    union-mask state with those partners must equal."""
    chem = np.array(con.chem, dtype=np.float32, copy=True)
    gap = np.array(con.gap, dtype=np.float32, copy=True)
    loop = has_self_loop(con, x) if self_loop is None else self_loop
    chem[x, :] = chem[:, x] = 0
    gap[x, :] = gap[:, x] = 0
    c = candidates(con.n, x)
    chem[c[partners["in"]], x] = 1.0
    chem[x, c[partners["out"]]] = 1.0
    gap[c[partners["gap"]], x] = gap[x, c[partners["gap"]]] = 1.0
    if loop:
        chem[x, x] = 1.0
    return con.with_masks(chem, gap, f"{con.label}-partners-{con.names[x]}")


def edge_positions(spec: BrainSpec, kind: str) -> dict:
    """{(i, j): position} for the chemical edges or the gap junctions (i < j) of a spec."""
    ii, jj = (spec.chem_i, spec.chem_j) if kind == "chem" else (spec.gap_i, spec.gap_j)
    return {(int(a), int(b)): p for p, (a, b) in enumerate(zip(ii.tolist(), jj.tolist()))}


@dataclass
class XState:
    """S states of X's wiring. Masks are boolean [S, K] over the candidates; weights are [S, K] and are read only where
    the mask is set; tau, bias and the self-connection weight are [S] (w_self is unused without a self-connection)."""

    m_in: Tensor
    m_out: Tensor
    m_gap: Tensor
    w_in: Tensor
    w_out: Tensor
    g: Tensor
    tau: Tensor
    bias: Tensor
    w_self: Tensor

    @property
    def n(self) -> int:
        return int(self.m_in.shape[0])

    @property
    def device(self) -> torch.device:
        return self.m_in.device

    def masks(self) -> dict:
        return {"in": self.m_in, "out": self.m_out, "gap": self.m_gap}

    def weights(self) -> dict:
        return {"in": self.w_in, "out": self.w_out, "gap": self.g}

    def counts(self) -> dict:
        """[S] partner counts per type."""
        return {k: v.sum(dim=1) for k, v in self.masks().items()}

    def _map(self, f) -> "XState":
        return XState(**{fd.name: f(getattr(self, fd.name)) for fd in fields(self)})

    def clone(self) -> "XState":
        return self._map(lambda t: t.clone())

    def to(self, device) -> "XState":
        return self._map(lambda t: t.to(device))

    def select(self, idx) -> "XState":
        idx = torch.as_tensor(idx, dtype=torch.long, device=self.device).reshape(-1)
        return self._map(lambda t: t[idx].clone())

    @staticmethod
    def cat(parts: list) -> "XState":
        return XState(**{fd.name: torch.cat([getattr(p, fd.name) for p in parts]) for fd in fields(XState)})

    def equal(self, other: "XState") -> bool:
        return all(torch.equal(getattr(self, fd.name), getattr(other, fd.name)) for fd in fields(self))


class Reinsertion:
    """One source brain with target X deleted, ready to take states of X's wiring.

    `source` is a one-strain genome on `con` (MIP: the intact graph) or on `con` with X's edges removed (NIP,
    `deletion.without_neuron`). Its edges other than X's must be exactly the union's; anything else is refused."""

    def __init__(self, con: Connectome, x: int, source: Genome, device="cpu"):
        if source.n_strains != 1:
            raise ValueError("a reinsertion takes one source brain")
        if source.cfg.dale or source.dale_sign is not None:
            raise ValueError("03a's reinsertion assumes Dale's law is off")
        if source.spec.n != con.n:
            raise ValueError("the source brain is not on this graph's neurons")
        self.con, self.x, self.device = con, int(x), torch.device(device)
        self.cand = candidates(con.n, self.x)
        self.K = len(self.cand)
        self.self_loop = has_self_loop(con, self.x)
        self.spec = BrainSpec.from_connectome(union_connectome(con, self.x)).to(self.device)
        pc, pg = edge_positions(self.spec, "chem"), edge_positions(self.spec, "gap")
        x_ = self.x
        t = lambda a: torch.as_tensor(a, dtype=torch.long, device=self.device)  # noqa: E731
        self.pos_in = t([pc[(int(c), x_)] for c in self.cand])
        self.pos_out = t([pc[(x_, int(c))] for c in self.cand])
        self.pos_gap = t([pg[(min(int(c), x_), max(int(c), x_))] for c in self.cand])
        self.pos_self = pc[(x_, x_)] if self.self_loop else None

        src = source.select([0])
        sc = list(zip(src.spec.chem_i.tolist(), src.spec.chem_j.tolist()))
        sg = list(zip(src.spec.gap_i.tolist(), src.spec.gap_j.tolist()))
        keep_c = [p for p, (a, b) in enumerate(sc) if a != x_ and b != x_]
        keep_g = [p for p, (a, b) in enumerate(sg) if a != x_ and b != x_]
        union_bg_c = {e for e in pc if x_ not in e}
        union_bg_g = {e for e in pg if x_ not in e}
        if {sc[p] for p in keep_c} != union_bg_c or {sg[p] for p in keep_g} != union_bg_g:
            raise ValueError("the source brain's edges, X's aside, are not this graph's")
        w = torch.zeros(self.spec.n_chem, dtype=src.w.dtype)
        g = torch.zeros(self.spec.n_gap, dtype=src.g.dtype)
        w[[pc[sc[p]] for p in keep_c]] = src.w[0, keep_c].cpu()
        g[[pg[sg[p]] for p in keep_g]] = src.g[0, keep_g].cpu()
        self.w_bg, self.g_bg = w.to(self.device), g.to(self.device)
        self.tau_bg, self.bias_bg = src.tau[0].to(self.device).clone(), src.bias[0].to(self.device).clone()
        self.cfg = src.cfg
        self._template = src
        # the background's X-free positions, for the bitwise checks
        x_c = torch.zeros(self.spec.n_chem, dtype=torch.bool)
        x_c[self.pos_in.cpu()] = True
        x_c[self.pos_out.cpu()] = True
        if self.pos_self is not None:
            x_c[self.pos_self] = True
        x_g = torch.zeros(self.spec.n_gap, dtype=torch.bool)
        x_g[self.pos_gap.cpu()] = True
        self.x_chem, self.x_gap = x_c.to(self.device), x_g.to(self.device)

    def genome(self, st: XState) -> Genome:
        """The S-strain genome on the union spec: the background, with X wired as `st` says."""
        S = st.n
        st = st.to(self.device)
        zero = torch.zeros((), dtype=self.w_bg.dtype, device=self.device)
        w = self.w_bg.unsqueeze(0).repeat(S, 1)
        w[:, self.pos_in] = torch.where(st.m_in, st.w_in, zero)
        w[:, self.pos_out] = torch.where(st.m_out, st.w_out, zero)
        if self.pos_self is not None:
            w[:, self.pos_self] = st.w_self
        g = self.g_bg.unsqueeze(0).repeat(S, 1)
        g[:, self.pos_gap] = torch.where(st.m_gap, st.g, zero)
        tau = self.tau_bg.unsqueeze(0).repeat(S, 1)
        bias = self.bias_bg.unsqueeze(0).repeat(S, 1)
        tau[:, self.x] = st.tau
        bias[:, self.x] = st.bias
        return self._template.with_params(spec=self.spec, w=w, g=g, tau=tau, bias=bias, dale_sign=None)

    def empty_state(self, S: int = 1) -> XState:
        """X with no connection at all, its self-connection off: the deleted brain (X isolated, affecting nothing)."""
        K, dev = self.K, self.device
        zb = torch.zeros(S, K, dtype=torch.bool, device=dev)
        zf = torch.zeros(S, K, dtype=self.w_bg.dtype, device=dev)
        one = torch.ones(S, dtype=self.w_bg.dtype, device=dev)
        return XState(zb, zb.clone(), zb.clone(), zf, zf.clone(), zf.clone(), one, 0 * one, 0 * one)

    def saved_state(self, intact: Genome) -> XState:
        """X's evolved parameters in an intact brain (one strain, on the intact graph): MIP's exact restoration."""
        if intact.n_strains != 1:
            raise ValueError("one intact brain")
        tr = truth(self.con, self.x)
        pc, pg = edge_positions(intact.spec, "chem"), edge_positions(intact.spec, "gap")
        w, gg = intact.w[0].cpu(), intact.g[0].cpu()
        K, x_ = self.K, self.x

        def take(kind, key, pos):
            out = torch.zeros(K, dtype=w.dtype)
            for k, c in enumerate(self.cand):
                if tr[kind][k]:
                    out[k] = (w if key == "chem" else gg)[pos[k_edge(kind, int(c), x_)]]
            return out

        def k_edge(kind, c, x):
            return (c, x) if kind == "in" else (x, c) if kind == "out" else (min(c, x), max(c, x))

        st = XState(
            torch.as_tensor(tr["in"]).unsqueeze(0), torch.as_tensor(tr["out"]).unsqueeze(0),
            torch.as_tensor(tr["gap"]).unsqueeze(0),
            take("in", "chem", pc).unsqueeze(0), take("out", "chem", pc).unsqueeze(0),
            take("gap", "gap", pg).unsqueeze(0),
            intact.tau[0, x_].cpu().reshape(1).clone(), intact.bias[0, x_].cpu().reshape(1).clone(),
            (w[pc[(x_, x_)]] if self.self_loop else torch.zeros(())).reshape(1).clone())
        return st.to(self.device)


def x_edges_zero(genome: Genome, x: int) -> bool:
    """True if no strain of `genome` has a nonzero weight on any edge touching X (NIP's pinning, checked on the dense
    matrices the brain uses, so a spec that kept X's edges would be caught)."""
    W, G = genome.dense()
    return bool((W[:, x, :] == 0).all() and (W[:, :, x] == 0).all() and (G[:, x, :] == 0).all()
                and (G[:, :, x] == 0).all())
