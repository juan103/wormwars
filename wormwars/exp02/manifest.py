"""What a saved experiment-02 genome must match to be replayed: graph, interface, sensing, gains."""

from __future__ import annotations

from ..evo.genomes import edge_hash
from ..interface import interface_hash


def run_manifest(cfg, iface, spec) -> dict:
    return {
        "edge_hash": edge_hash(spec),
        "interface_hash": interface_hash(iface),
        "food_sensing": cfg.world.food_sensing,
        "sense_scale_pheromone": float(cfg.world.sense_scale_pheromone),
        "substeps": int(cfg.brain.substeps),
        "init_chem_magnitude": cfg.brain.init_chem_magnitude,
        "init_gap_magnitude": cfg.brain.init_gap_magnitude,
        "forward_gain": float(cfg.world.forward_gain),
        "turn_gain": float(cfg.world.turn_gain),
    }


def check_manifest(meta: dict, cfg, iface, spec) -> None:
    expected = run_manifest(cfg, iface, spec)
    bad = {k: (meta.get(k), v) for k, v in expected.items() if meta.get(k) != v}
    if bad:
        detail = "; ".join(f"{k}: saved {a!r}, now {b!r}" for k, (a, b) in bad.items())
        raise ValueError(f"genome does not match this condition: {detail}")
