"""Ablation, convergence and tactics analysis.

**Two kinds of ablation, and the difference matters.**

*Implementation checks* silence neurons that the sensor/motor map names. If silencing AVA changes
the forward read-out, that is arithmetic: AVA is a term in the read-out. These checks verify that
the interface is wired the way the config says. **They say nothing about biology** and are labelled
`implementation` wherever they appear.

*Emergent tests* silence interneurons the map does not name -- AIY, AIZ, AIB, RIA, RIM, and the
RIP-I1 gap junction bridge between the somatic and pharyngeal systems. Any effect there had to come
through the evolved dynamics. Each is compared against **matched random ablations**: the same number
of neurons, the same class, and similar degree, so "removing any five interneurons hurts" is not
mistaken for "removing these five hurts".

Even then, a resemblance to a real worm result is a resemblance and nothing more. These weys have no
neuromodulation, no plasticity and no biophysics, and the task is a game.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch

from ..brain import Brain, BrainSpec, Genome
from ..config import Config
from ..connectome.loader import Connectome
from ..interface import Interface, load_interface

# Interneurons deliberately left out of the sensor/motor map, so that any effect of removing them is
# something evolution built rather than something the interface guarantees.
EMERGENT_TARGETS: dict[str, list[str]] = {
    "AIY": ["AIYL", "AIYR"],
    "AIZ": ["AIZL", "AIZR"],
    "AIB": ["AIBL", "AIBR"],
    "RIA": ["RIAL", "RIAR"],
    "RIM": ["RIML", "RIMR"],
}
# The only wiring between the somatic and pharyngeal nervous systems (measured; see PROVENANCE.md).
RIP_I1_BRIDGE = [("RIPL", "I1L"), ("RIPR", "I1R")]


@dataclass
class AblationSpec:
    name: str
    neurons: list[str] = field(default_factory=list)
    gap_cuts: list[tuple[str, str]] = field(default_factory=list)
    kind: str = "emergent"  # "emergent", "implementation", "matched_random", "none"

    def indices(self, con: Connectome) -> list[int]:
        return [con.index(n) for n in self.neurons]

    def gap_pairs(self, con: Connectome) -> list[tuple[int, int]]:
        return [(con.index(a), con.index(b)) for a, b in self.gap_cuts]


def implementation_checks(con: Connectome, iface: Interface) -> list[AblationSpec]:
    """Ablations whose effect follows by construction from the interface config."""
    return [
        AblationSpec("impl:AVA (forward read-out)", ["AVAL", "AVAR"], kind="implementation"),
        AblationSpec("impl:AVB (forward read-out)", ["AVBL", "AVBR"], kind="implementation"),
        AblationSpec(
            "impl:anterior touch (ALM/AVM sensors)", ["ALML", "ALMR", "AVM"], kind="implementation"
        ),
        AblationSpec("impl:food sensors AWC", ["AWCL", "AWCR"], kind="implementation"),
        AblationSpec("impl:turn read-out SMDD", ["SMDDL", "SMDDR"], kind="implementation"),
        AblationSpec("impl:pump read-out MC", ["MCL", "MCR"], kind="implementation"),
    ]


def emergent_checks() -> list[AblationSpec]:
    out = [AblationSpec(f"emergent:{k}", v) for k, v in EMERGENT_TARGETS.items()]
    out.append(AblationSpec("emergent:RIP-I1 bridge", [], RIP_I1_BRIDGE))
    return out


def degree_of(con: Connectome) -> np.ndarray:
    """Total degree: chemical in + chemical out + gap."""
    return (
        (con.chem > 0).sum(axis=0) + (con.chem > 0).sum(axis=1) + (con.gap > 0).sum(axis=1)
    ).astype(float)


def matched_random(
    con: Connectome,
    target: AblationSpec,
    n: int,
    rng: np.random.Generator,
    exclude: set[str] | None = None,
    degree_tolerance: float = 0.5,
) -> list[AblationSpec]:
    """`n` random ablations matched to `target` on size, neuron class and degree.

    Each target neuron is replaced by a random neuron of the same class whose total degree is within
    `degree_tolerance` (relative) of it. Without this, "ablating any two interneurons hurts" would
    look like evidence about the specific pair.
    """
    exclude = (exclude or set()) | set(target.neurons)
    deg = degree_of(con)
    idx_of = con.index_of
    out: list[AblationSpec] = []
    for k in range(n):
        picked: list[str] = []
        for name in target.neurons:
            i = idx_of[name]
            cls, d = con.classes[i], deg[i]
            pool = [
                m
                for j, m in enumerate(con.names)
                if con.classes[j] == cls
                and m not in exclude
                and m not in picked
                and abs(deg[j] - d) <= degree_tolerance * max(d, 1.0)
            ]
            if not pool:  # fall back to class-only matching rather than silently skipping
                pool = [
                    m
                    for j, m in enumerate(con.names)
                    if con.classes[j] == cls and m not in exclude and m not in picked
                ]
            picked.append(str(rng.choice(pool)))
        out.append(AblationSpec(f"{target.name}/random{k}", picked, kind="matched_random"))
    return out


def evaluate_ablations(
    cfg: Config,
    iface: Interface,
    con: Connectome,
    genome: Genome,
    specs: list[AblationSpec],
    world_ids: np.ndarray,
    run_seed: int,
    device="cpu",
    combat_stage: int = 0,
) -> np.ndarray:
    """Foraging score of one champion under each ablation. Returns [len(specs)] scores.

    Every ablation is run as its own strain slot in one batch, on the same world ids, so the
    comparison between ablations is paired.
    """
    from ..evo.rollout import rollout

    if genome.n_strains != 1:
        raise ValueError("ablations are run against a single champion")
    replicated = genome.select([0] * len(specs))
    result = rollout(
        cfg, iface, replicated, world_ids, run_seed=run_seed, device=device,
        combat_stage=combat_stage,
        brain_hook=lambda brain, lo, hi: _apply(brain, con, specs[lo:hi]),
    )
    return result.per_strain()


def _apply(brain: Brain, con: Connectome, specs: list[AblationSpec]) -> None:
    brain.silence([s.indices(con) for s in specs])
    if any(s.gap_cuts for s in specs):
        brain.cut_gap([s.gap_pairs(con) for s in specs])


def sensitivity(scores: np.ndarray, baseline: float) -> np.ndarray:
    """Fractional loss caused by each ablation. 0 = no effect, 1 = total collapse."""
    if baseline <= 0:
        return np.zeros_like(scores)
    return 1.0 - scores / baseline


def profile_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Correlation between two ablation-sensitivity profiles: do two champions rely on the same
    neurons? This is the convergence measure."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.std() < 1e-12 or b.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


@dataclass
class TacticsReport:
    flank_share: float  # damage landed on mid/tail as a fraction of all damage
    head_share: float
    turn_toward_rate: float  # how often a wey turned toward the side it was bitten from
    turn_events: int

    def __str__(self) -> str:
        return (
            f"damage to mid/tail {self.flank_share:.3f}, to head {self.head_share:.3f}; "
            f"turned toward the bite {self.turn_toward_rate:.3f} of {self.turn_events} events"
        )


def tactics_from_world(world) -> TacticsReport:
    total = float(world.damage_by_point.sum())
    toward, events = (float(x) for x in world.turn_toward_damage)
    return TacticsReport(
        flank_share=world.flank_damage / max(total, 1e-12),
        head_share=world.head_damage / max(total, 1e-12),
        turn_toward_rate=toward / max(events, 1.0),
        turn_events=int(events),
    )
