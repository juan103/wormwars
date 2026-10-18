"""03h: does the history random brains hold predict how well they forage? (experiments/03h-history-use/DESIGN.md)

The food_fell channel's interface variant and its amplitude; the world modes are `WorldConfig.food_fell`."""

from __future__ import annotations

from pathlib import Path

from ..interface import load_interface
from ..world import FOOD_FELL as MODES  # noqa: F401  (one tuple: the world's)

INTERFACE = Path(__file__).resolve().parents[2] / "configs" / "interface-03h.yaml"
AMPLITUDE = 0.25  # the bit's injected current per ASK neuron (§3), with input_gain 1.0


def interface_03h(con):
    """The pinned interface plus the food_fell channel on ASKL and ASKR."""
    return load_interface(con, INTERFACE)
