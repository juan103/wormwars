"""E4's training and evaluation brains (docs/E4/E4-DESIGN.md v3 §1): E-G's output gate applied to every brain a
population builds, in `evolve_batch`'s rollouts (`gated_rollout`) and in evaluation (`gated_brain`)."""

from __future__ import annotations

from ..brain import Brain, Genome
from ..e04a.evolve import moved
from ..evo.rollout import rollout


def gated_rollout(gate: dict):
    """A `rollout_fn` for `evolve_batch`: `rollout` with the gate set on each chunk's brain."""
    def fn(cfg, iface, genome, world_ids, run_seed, device="cpu", **kw):
        if "brain_hook" in kw:
            raise ValueError("the gated rollout sets its own brain hook")
        return rollout(cfg, iface, genome, world_ids, run_seed, device,
                       brain_hook=lambda b, lo, hi: b.gate_outputs(gate), **kw)
    return fn


def gated_brain(genome: Genome, gate: dict, device="cpu") -> Brain:
    return Brain(genome if str(device) == "cpu" else moved(genome, device)).gate_outputs(gate)
