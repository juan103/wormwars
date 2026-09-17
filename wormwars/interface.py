"""The sensor and motor interface: which world quantity reaches which named neuron.

The mapping itself lives in `configs/interface.yaml`. This module only resolves names to indices
and fails loudly when a named neuron is absent. It never substitutes a sibling neuron.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from .connectome.loader import Connectome, ConnectomeError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INTERFACE = ROOT / "configs" / "interface.yaml"

# Signals the world must be able to produce. Kept explicit so a typo in the YAML is caught here
# rather than silently producing a dead sensor.
KNOWN_SIGNALS = (
    "food_left",
    "food_right",
    "ally_pheromone_left",
    "ally_pheromone_right",
    "enemy_pheromone_left",
    "enemy_pheromone_right",
    "hazard_left",
    "hazard_right",
    "damage_left",
    "damage_right",
    "collision_front",
    "collision_front_left",
    "collision_front_right",
    "collision_rear_left",
    "collision_rear_right",
)


@dataclass(frozen=True)
class Interface:
    """Resolved interface: index arrays ready for the brain."""

    signal_names: tuple[str, ...]  # one entry per input channel, in order
    sensor_neuron: np.ndarray  # [n_channels] neuron index receiving that channel
    sensor_gain: np.ndarray  # [n_channels]
    forward_plus: np.ndarray
    forward_minus: np.ndarray
    turn_plus: np.ndarray
    turn_minus: np.ndarray
    pump_neurons: np.ndarray
    pump_gain: float
    forward_offset: float
    lateral_offset: float
    raw: dict = field(repr=False, default_factory=dict)

    @property
    def n_channels(self) -> int:
        return len(self.signal_names)

    @property
    def mapped_neurons(self) -> tuple[int, ...]:
        """Every neuron index the interface touches, sensor or motor."""
        parts = [
            self.sensor_neuron,
            self.forward_plus,
            self.forward_minus,
            self.turn_plus,
            self.turn_minus,
            self.pump_neurons,
        ]
        return tuple(sorted(set(int(i) for part in parts for i in part)))


def _resolve(con: Connectome, names, where: str) -> np.ndarray:
    if not names:
        raise ConnectomeError(f"{where}: empty neuron list in the interface config")
    missing = [n for n in names if n not in con.index_of]
    if missing:
        raise ConnectomeError(
            f"{where}: neuron(s) {missing} are not in the {con.label} dataset. "
            "The interface names individual neurons on purpose; do not guess at alternatives."
        )
    return np.array([con.index(n) for n in names], dtype=np.int64)


def load_interface(con: Connectome, path: str | Path | None = None) -> Interface:
    path = Path(path) if path is not None else DEFAULT_INTERFACE
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))

    signal_names: list[str] = []
    sensor_neuron: list[int] = []
    sensor_gain: list[float] = []
    for i, ch in enumerate(spec["sensors"]):
        signal = ch["signal"]
        if signal not in KNOWN_SIGNALS:
            raise ConnectomeError(
                f"sensors[{i}]: unknown signal {signal!r}. Known signals: {list(KNOWN_SIGNALS)}"
            )
        idx = _resolve(con, ch["neurons"], f"sensors[{i}] ({signal})")
        for j in idx:
            signal_names.append(signal)
            sensor_neuron.append(int(j))
            sensor_gain.append(float(ch.get("gain", 1.0)))

    motors = spec["motors"]
    pump = motors["pump"]
    if pump.get("squash", "sigmoid") != "sigmoid":
        raise ConnectomeError("only squash: sigmoid is implemented for the pump read-out")
    sampling = spec["sampling"]

    return Interface(
        signal_names=tuple(signal_names),
        sensor_neuron=np.array(sensor_neuron, dtype=np.int64),
        sensor_gain=np.array(sensor_gain, dtype=np.float32),
        forward_plus=_resolve(con, motors["forward"]["plus"], "motors.forward.plus"),
        forward_minus=_resolve(con, motors["forward"]["minus"], "motors.forward.minus"),
        turn_plus=_resolve(con, motors["turn"]["plus"], "motors.turn.plus"),
        turn_minus=_resolve(con, motors["turn"]["minus"], "motors.turn.minus"),
        pump_neurons=_resolve(con, pump["neurons"], "motors.pump.neurons"),
        pump_gain=float(pump.get("gain", 4.0)),
        forward_offset=float(sampling["forward_offset"]),
        lateral_offset=float(sampling["lateral_offset"]),
        raw=spec,
    )
