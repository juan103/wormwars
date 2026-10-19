"""03h: does the history random brains hold predict how well they forage? (experiments/03h-history-use/DESIGN.md)

The food_fell channel's interface variant and its amplitude; the world modes are `WorldConfig.food_fell`."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np

from ..interface import load_interface
from ..world import FOOD_FELL as MODES  # noqa: F401  (one tuple: the world's)

INTERFACE = Path(__file__).resolve().parents[2] / "configs" / "interface-03h.yaml"
AMPLITUDE = 0.25  # the bit's injected current per ASK neuron (§3), with input_gain 1.0


def interface_03h(con, amplitude: float = AMPLITUDE):
    """The pinned interface plus the food_fell channel on ASKL and ASKR, at `amplitude` (the registered 0.25 by default;
    0.5 only by PILOT.md §5.4's rule). With input_gain 1.0 the channel's gain is its injected current."""
    iface = load_interface(con, INTERFACE)
    if amplitude == AMPLITUDE:
        return iface
    gain = np.asarray(iface.sensor_gain).copy()
    gain[[i for i, n in enumerate(iface.signal_names) if n == "food_fell"]] = amplitude
    return dataclasses.replace(iface, sensor_gain=gain.astype(np.float32))
