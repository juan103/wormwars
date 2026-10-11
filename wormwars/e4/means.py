"""P1-info's source means (docs/E4/E4-DESIGN.md v3 §2): mean(tanh v_i) per strain, unconditional, over every
substep end-state, wey and maze of the intact champion's validation play under shared trails.

Every maze of a strain holds the same number of weys and plays the same ticks, so a plain mean over substeps,
weys and mazes weights mazes and weys equally."""

from __future__ import annotations

import numpy as np
import torch

from ..e3 import maze_runs as MR
from .train import gated_brain


class SourceMeans:
    """A `Brain.substep_hook`: sums tanh(v) [S, B, N] over substeps and weys, in float64."""

    def __init__(self):
        self.total = None
        self.count = 0

    def __call__(self, v: torch.Tensor) -> None:
        s = torch.tanh(v.to(torch.float64)).sum(dim=1)
        self.total = s if self.total is None else self.total + s
        self.count += v.shape[1]

    def mean(self) -> torch.Tensor:
        return (self.total / self.count).cpu()


def source_means(cfg, iface, genome, gate, ids, run_seed, device="cpu", *, ticks=None) -> torch.Tensor:
    """Each strain of `genome`, gated, on every maze of `ids` under shared trails; its means [S, N]."""
    brain = gated_brain(genome, gate, device)
    acc = SourceMeans()
    brain.substep_hook = acc
    MR.play_batch(cfg, iface, brain, np.arange(genome.n_strains), ids, run_seed, device, access="shared", ticks=ticks)
    return acc.mean()
