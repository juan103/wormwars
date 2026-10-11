"""E4's organism E-G on the maze (docs/E4/E4-DESIGN.md v3 §1).

E3a's E with ungated comparators and the 32 cross-link slots at 0 (`organism.engineered_gated`), plus E3b-0's W2
wall reflex, on the carrier as E3b-1's seed is built. Its modes come from the output gate on each module's
comparator → motor edges (`Brain.gate_outputs`), attached to the organism so that `maze_organisms.brain`
applies it.
"""

from __future__ import annotations

import dataclasses

from .. import graft as G
from ..e3 import maze_organisms as MO
from ..e3 import organism as O
from ..e4s import comparator as C


def eg(con, l1, bcfg, *, slots: bool = True) -> MO.Organism:
    """E-G + W2 with its gate. `slots=False` builds it without the 32 cross-link slots (a check)."""
    module = O.engineered_gated(l1)
    if not slots:
        cross = set(O.cross_links(module))
        module = G.Module("e4-organism-EG-noslots", module.neurons,
                          tuple(s for s in module.synapses if (s[0], s[1]) not in cross),
                          module.tau, module.bias, module.noses, module.nose_gain, module.neuron_class)
        G.MODULES[module.name] = module
    ext = G.graft_connectome(con, module)
    genome = C.carrier_genome(ext, module, bcfg, forward=MO.CARRIER_FORWARD, turn=MO.REST_TURN["W0"])
    org = MO.maze_organism(con, MO.Seed("E-G" if slots else "E-G-noslots", module, ext, genome), "W2", bcfg)
    return dataclasses.replace(org, gate=O.gate_spec(org.ext, org.module))
