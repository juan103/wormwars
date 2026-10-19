"""03h's pilot probe of the bit (experiments/03h-history-use/PILOT.md §4): does the food_fell input reach the turn
read-out of a random brain? A diagnostic of the manipulation, not a rule (DESIGN.md v3.3 §13)."""

from __future__ import annotations

from ..accounting import counted
from ..brain import Brain, Genome
from ..exp03.measures import _current, _readout


@counted("probe")
def bit_turn_response(genome: Genome, cfg, iface, bank: dict, warm: int = 100):
    """Per genome: `warm` ticks at the bank's inputs with the bit at 0, then one tick with the bit on against one with
    it off, from the same state; the difference in the motor turn read-out at that tick, [genomes]."""
    brain = Brain(genome)
    s, n, dev = genome.n_strains, genome.spec.n, genome.device
    off = _current(iface, cfg, dict(bank, food_fell=0.0), n, s, dev)
    on = _current(iface, cfg, dict(bank, food_fell=1.0), n, s, dev)
    v = brain.initial_state(1)
    for _ in range(warm):
        v = brain.step(v, off)
    t_off = _readout(iface, cfg, brain.step(v.clone(), off))
    t_on = _readout(iface, cfg, brain.step(v.clone(), on))
    return (t_on[:, 3] - t_off[:, 3]).cpu().numpy()
