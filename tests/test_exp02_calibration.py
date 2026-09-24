"""Calibration in the world the brains actually run in, to a fixed target, iterated."""

from __future__ import annotations

import pytest

from wormwars import calibration as calib
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import shuffled
from wormwars.interface import load_interface

TARGET = (0.5, 0.4)


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con)


def test_achieved_drive_reports_in_range_values(parts):
    con, iface = parts
    d = calib.achieved_drive(con, Config(), iface, n_strains=6, ticks=30)
    assert 0 < d.forward <= 1 and 0 < d.turn <= 1
    assert 0 <= d.clip_forward <= 1 and 0 <= d.clip_turn <= 1 and d.displacement >= 0
    # signed statistics, so a graph that "moves" by reversing is visible
    assert -1 <= d.forward_signed <= 1 and 0 <= d.reversing <= 1
    assert abs(d.forward_signed) <= d.forward + 1e-9


@pytest.mark.parametrize("which", ["N2", "SH1"])
def test_calibration_reaches_the_target_within_tolerance(parts, which):
    con, iface = parts
    graph = con if which == "N2" else shuffled(con, 1, "SH1")
    cal = calib.calibrate_in_world(graph, Config(), iface, TARGET, n_strains=6, ticks=30, tol=0.02)
    assert abs(cal.achieved.forward / TARGET[0] - 1) <= 0.02
    assert abs(cal.achieved.turn / TARGET[1] - 1) <= 0.02
    assert cal.as_dict()["graph"] == graph.label


def test_calibration_that_cannot_converge_says_so(parts):
    con, iface = parts
    with pytest.raises(RuntimeError, match="did not converge"):
        calib.calibrate_in_world(con, Config(), iface, (1.5, 0.4), n_strains=4, ticks=20, max_iter=3)
