"""Motor gain calibration: the nuisance variable it removes, and the ones it must not touch."""

from __future__ import annotations

import pytest

from wormwars import calibration as calib
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import random_graph, shuffled
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con)


@pytest.fixture(scope="module")
def cal_setup(parts):
    con, iface = parts
    cfg = Config()
    ref = calib.reference_from(con, cfg, iface, n_strains=8, ticks=40)
    return con, iface, cfg, ref


def test_graphs_differ_in_raw_motor_scale(parts):
    """If they did not, calibration would be pointless -- and the M5 result would need no caveat."""
    con, iface = parts
    cfg = Config()
    raws = {}
    for g in (con, shuffled(con, 1), random_graph(con, 1)):
        raws[g.label] = calib.raw_motor_magnitude(g, cfg, iface, n_strains=8, ticks=40)[0]
    spread = max(raws.values()) / min(raws.values())
    assert spread > 1.2, f"graphs barely differ in raw motor scale: {raws}"


def test_calibration_equalises_the_scaled_output(cal_setup):
    con, iface, cfg, ref = cal_setup
    for g in (con, shuffled(con, 1), shuffled(con, 2), random_graph(con, 1)):
        c = calib.calibrate(g, cfg, iface, reference=ref, n_strains=8, ticks=40)
        assert c.raw_forward * c.forward_gain == pytest.approx(ref[0], rel=1e-6)
        assert c.raw_turn * c.turn_gain == pytest.approx(ref[1], rel=1e-6)


def test_n2_is_the_reference_so_its_gains_do_not_move(cal_setup):
    con, iface, cfg, ref = cal_setup
    c = calib.calibrate(con, cfg, iface, reference=ref, n_strains=8, ticks=40)
    assert c.forward_gain == pytest.approx(cfg.world.forward_gain, rel=1e-6)
    assert c.turn_gain == pytest.approx(cfg.world.turn_gain, rel=1e-6)


def test_calibration_is_deterministic(cal_setup):
    con, iface, cfg, ref = cal_setup
    g = shuffled(con, 3)
    a = calib.calibrate(g, cfg, iface, reference=ref, n_strains=8, ticks=40)
    b = calib.calibrate(g, cfg, iface, reference=ref, n_strains=8, ticks=40)
    assert a.forward_gain == b.forward_gain and a.turn_gain == b.turn_gain


def test_calibration_changes_only_the_gains(cal_setup):
    """Everything the experimental design requires to be identical must stay identical."""
    con, iface, cfg, ref = cal_setup
    c = calib.calibrate(shuffled(con, 1), cfg, iface, reference=ref, n_strains=8, ticks=40)
    out = calib.apply(cfg, c)
    a, b = cfg.to_dict(), out.to_dict()
    for section in a:
        for key in a[section]:
            if (section, key) in (("world", "forward_gain"), ("world", "turn_gain")):
                continue
            assert a[section][key] == b[section][key], f"calibration changed {section}.{key}"
    assert cfg.world.forward_gain == 4.0, "the original config was mutated"


def test_gain_is_capped(cal_setup):
    con, iface, cfg, ref = cal_setup
    c = calib.calibrate(
        shuffled(con, 1), cfg, iface, reference=(1e9, 1e9), n_strains=8, ticks=40, max_gain=7.5
    )
    assert c.forward_gain == 7.5 and c.turn_gain == 7.5


def test_config_copy_is_deep():
    cfg = Config()
    other = cfg.copy()
    other.world.forward_gain = 99.0
    other.evo.population = 7
    assert cfg.world.forward_gain == 4.0 and cfg.evo.population == 32


def test_default_yaml_matches_the_dataclass_defaults():
    """configs/default.yaml is the documented surface of every knob; it must not drift."""
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "configs" / "default.yaml"
    assert path.exists(), "configs/default.yaml is missing"
    assert Config.from_yaml(path).to_dict() == Config().to_dict()


def test_unknown_config_keys_are_errors(tmp_path):
    bad = tmp_path / "c.yaml"
    bad.write_text("world: {not_a_field: 1}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not_a_field"):
        Config.from_yaml(bad)
    bad.write_text("nonsense: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="nonsense"):
        Config.from_yaml(bad)


def test_yaml_ranges_load_as_tuples():
    """YAML has no tuples; a range must still arrive as one so configs are interchangeable."""
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "configs" / "default.yaml"
    cfg = Config.from_yaml(path)
    assert isinstance(cfg.map.food_patches, tuple)
    assert isinstance(cfg.evo.coevo_sizes, tuple)
