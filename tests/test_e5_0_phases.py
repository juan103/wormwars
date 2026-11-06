"""E5-0's exploratory phases (scripts/e5_0_phases.py): a captured life without a logged first contact is counted apart
and kept out of the phase medians (the results review, Astra 1 and Fable 3: its -1 sentinel gave negative
approaches)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location("e5_0_phases_test", ROOT / "scripts" / "e5_0_phases.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    return M


def test_a_capture_without_contact_is_counted_apart():
    M = _module()
    lab = "h"
    z = {f"{lab}|ev activation_tick": np.array([[0, 40, 90, -1]]),
         f"{lab}|ev capture_tick": np.array([[30, 70, -1, -1]]),
         f"{lab}|ev first_contact_tick": np.array([[10, -1, 95, -1]]),
         f"{lab}|ev contact_ticks": np.array([[12, 0, 3, 0]]),
         f"{lab}|captures": np.array([2])}
    p = M.phases(z, lab)
    assert p["captured_lives"] == 2 and p["captured_without_contact"] == 1
    assert p["approach_median"] == 10.0 and p["kill_median"] == 20.0 and p["contact_ticks_median"] == 12.0
