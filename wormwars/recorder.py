"""Trajectory recording.

"Replay" in this project means **playback of recorded trajectories**, not re-simulation. The
recorder is switched on for chosen worlds and stores what happened; the viewer draws it back.
Re-simulating from a run bundle is a separate, best-effort thing (see docs/REPRODUCIBILITY.md).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch


@dataclass
class Recorder:
    """Records chosen worlds. Attach to a `World` as `world.recorder`.

    Wey state is recorded every tick; fields every `field_every` ticks, because a 600-tick match of
    a 24x24 world is about 10 MB of fields and only about 0.3 MB of bodies.
    """

    worlds: tuple[int, ...] = (0,)
    field_every: int = 4
    record_neurons: bool = False
    neuron_subset: tuple[int, ...] | None = None

    pos: list = field(default_factory=list)
    heading: list = field(default_factory=list)
    energy: list = field(default_factory=list)
    alive: list = field(default_factory=list)
    pump: list = field(default_factory=list)
    neurons: list = field(default_factory=list)
    fields: list = field(default_factory=list)
    field_ticks: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def attach(self, world) -> "Recorder":
        self.meta = {
            "side": world.side,
            "n_swarms": world.n_swarms,
            "n_weys": world.n_weys,
            "worlds": list(self.worlds),
            "channels": {
                k: getattr(world.ch, k)
                for k in ("FOOD", "PELLET", "HAZARD", "WALL", "BODY", "PHEROMONE", "ATTACK")
            },
            "body_length": world.cfg.world.body_length,
            "max_energy": world.cfg.world.max_energy,
            "run_seed": world.run_seed,
            "world_ids": [int(world.world_ids[w]) for w in self.worlds],
        }
        world.recorder = self
        self.record(world)  # tick 0, before anything happens
        return self

    def record(self, world) -> None:
        sel = list(self.worlds)
        cpu = lambda t: t[sel].detach().to("cpu").numpy().copy()  # noqa: E731
        self.pos.append(cpu(world.pos))
        self.heading.append(cpu(world.heading))
        self.energy.append(cpu(world.energy))
        self.alive.append(cpu(world.alive))
        self.pump.append(cpu(world.pump))
        if self.record_neurons:
            v = world.neuron_state()
            if self.neuron_subset is not None:
                v = v[..., list(self.neuron_subset)]
            self.neurons.append(cpu(v))
        if world.tick_count % self.field_every == 0:
            self.fields.append(cpu(world.fields))
            self.field_ticks.append(world.tick_count)

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        arrays = {
            "pos": np.stack(self.pos),
            "heading": np.stack(self.heading),
            "energy": np.stack(self.energy),
            "alive": np.stack(self.alive),
            "pump": np.stack(self.pump),
            "fields": np.stack(self.fields),
            "field_ticks": np.array(self.field_ticks),
            "meta": np.array(json.dumps(self.meta)),
        }
        if self.neurons:
            arrays["neurons"] = np.stack(self.neurons)
        np.savez_compressed(path, **arrays)
        return path


@dataclass
class Replay:
    """A loaded recording. Axis order is [tick, world, swarm, wey, ...]."""

    pos: np.ndarray
    heading: np.ndarray
    energy: np.ndarray
    alive: np.ndarray
    pump: np.ndarray
    fields: np.ndarray
    field_ticks: np.ndarray
    meta: dict
    neurons: np.ndarray | None = None

    @property
    def n_ticks(self) -> int:
        return self.pos.shape[0]

    def field_at(self, tick: int) -> np.ndarray:
        """Fields of the most recent recorded frame at or before `tick`."""
        i = int(np.searchsorted(self.field_ticks, tick, side="right") - 1)
        return self.fields[max(i, 0)]

    @staticmethod
    def load(path: str | Path) -> "Replay":
        d = np.load(path, allow_pickle=False)  # never enable pickle on downloaded files
        return Replay(
            pos=d["pos"],
            heading=d["heading"],
            energy=d["energy"],
            alive=d["alive"],
            pump=d["pump"],
            fields=d["fields"],
            field_ticks=d["field_ticks"],
            meta=json.loads(str(d["meta"])),
            neurons=d["neurons"] if "neurons" in d.files else None,
        )
