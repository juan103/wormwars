"""E4's arms and acute interventions (docs/E4/E4-DESIGN.md v3 §1-§2).

- `context`: E-G + W2 with its gate, and its spec, built once.
- `scales`: E3b-1's T-F mask at 0.25, minus the frozen selector (Q's τ, bias and self-weight, RA → Q, RB → Q, the
  relays' τ and biases, the four Q → comparator edges). X0 freezes the 32 cross-link slots (scale 0); X+ makes them
  mutable at `cross_factor`, chosen by the registered scale rule and never defaulted.
- `assert_frozen`: E4's own end-of-run check, every frozen parameter bitwise equal to the start's.
- `cut`: the listed links at weight 0. `mean_substitute`: the links cut and each target's bias raised by
  Σ_{i→j} w_ij · mean(tanh v_i), without `Genome.clamp_` (the brain reads `bias` unclamped).
"""

from __future__ import annotations

import torch

from ..brain import Genome
from ..e3 import organism as O
from ..e3 import tuning as T
from . import organism as E4O

ARMS = ("x0", "x_plus")
FACTOR = T.FACTOR  # the inherited parameters' mutation factor, as T-F
CROSS_FACTORS = (0.25, 0.5, 1.0)  # the scale rule's candidates
SELECTOR_EDGES = ((O.Q, O.Q), ("E3_RA", O.Q), ("E3_RB", O.Q)) + tuple((O.Q, c) for c in O.COMPARATORS)
SELECTOR_NODES = (O.Q, "E3_RA", "E3_RB")


def context(con, l1, bcfg) -> dict:
    org = E4O.eg(con, l1, bcfg)
    return {"org": org, "spec": org.genome.spec}


def _edge_indices(cx, pairs) -> torch.Tensor:
    spec, ext = cx["spec"], cx["org"].ext
    pos = {(int(a), int(b)): k for k, (a, b) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist()))}
    return torch.tensor([pos[(ext.index(a), ext.index(b))] for a, b in pairs], dtype=torch.long)


def slot_indices(cx) -> torch.Tensor:
    """The 32 cross-link slots' positions in the chemical edge list, in `organism.cross_links` order."""
    return _edge_indices(cx, O.cross_links(cx["org"].module))


def scales(cx, arm: str, *, cross_factor: float | None = None) -> dict:
    if arm not in ARMS:
        raise ValueError(f"the arms are {ARMS}")
    if arm == "x_plus" and cross_factor is None:
        raise ValueError("X+ needs the cross-link factor chosen by the scale rule")
    ext = cx["org"].ext
    sc = {k: v.clone() for k, v in T.scales(ext, FACTOR).items()}
    sc["w"][_edge_indices(cx, SELECTOR_EDGES)] = 0.0
    for n in SELECTOR_NODES:
        sc["tau"][ext.index(n)] = 0.0
        sc["bias"][ext.index(n)] = 0.0
    sc["w"][slot_indices(cx)] = 0.0 if arm == "x0" else float(cross_factor)
    return sc


def mutable_count(cx, arm: str, *, cross_factor: float | None = None) -> int:
    return int(sum(int((v != 0).sum()) for v in scales(cx, arm, cross_factor=cross_factor).values()))


def assert_frozen(start: Genome, final: Genome, sc: dict) -> None:
    """Every frozen parameter of every strain of `final` equals strain 0 of `start`, bitwise."""
    for name in ("w", "tau", "bias", "g"):
        frozen = sc[name] == 0
        a = getattr(start, name)[0].cpu()[frozen]
        b = getattr(final, name).cpu()[:, frozen]
        if not torch.equal(b, a.unsqueeze(0).expand_as(b)):
            raise AssertionError(f"a frozen parameter changed ({name})")


def cut(genome: Genome, links: torch.Tensor) -> Genome:
    w = genome.w.clone()
    w[:, links] = 0.0
    return genome.with_params(w=w)


def mean_substitute(genome: Genome, links: torch.Tensor, means: torch.Tensor) -> Genome:
    """`links` cut; each target's bias plus Σ w_ij · means_i. `means` is [N] or [S, N] (mean tanh activation per
    source neuron). Not clamped."""
    if genome.cfg.chem_direction != "pre_to_post":
        raise ValueError("mean substitution reads chem_i as the source, which holds only under pre_to_post")
    spec = genome.spec
    links = links.to(spec.chem_i.device)
    m = means.to(genome.bias.device, genome.bias.dtype)
    if m.dim() == 1:
        m = m.unsqueeze(0).expand(genome.n_strains, -1)
    drive = genome.w[:, links] * m[:, spec.chem_i[links]]  # [S, L]
    bias = genome.bias.clone()
    bias.index_add_(1, spec.chem_j[links], drive)
    return cut(genome, links).with_params(bias=bias)
