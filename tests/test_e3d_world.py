"""E3d's maze-family switch in the maze world (docs/E3/E3d-DESIGN.md v2.2 §2, §7).

"tree" (the default, left unset in the configuration so tree configurations and their hashes are unchanged)
plays E3b-1's generator; "islands" plays `islands.maze_for` at `maze_extra_openings` k_r. Scramble mode needs
equal open-cell counts and is refused for the island family.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.connectome import load_connectome
from wormwars.e1 import controllers as C
from wormwars.e3 import islands as I
from wormwars.e3 import maze as M
from wormwars.e3 import maze_world as MW
from wormwars.interface import load_interface

C6 = dict(c=6, horizon=20, colony=2, mu=0.01, lam=0.02, delta=0.05, d0=1.142)


@pytest.fixture(scope="module")
def iface():
    return load_interface(load_connectome())


def _world(iface, ids, cfg, run_seed=1_190_000, **kw):
    brain = C.scripted(iface, C.ConstantMotion(0.0, 0.0), cfg)
    strain_of = torch.zeros(len(ids), 1, dtype=torch.long)
    return MW.MazeWorld(cfg, iface, brain, strain_of, run_seed=run_seed, world_ids=np.asarray(ids), **kw)


def test_the_tree_family_leaves_the_configuration_unchanged():
    cfg = MW.maze_config(**C6)
    assert cfg.world.maze_family is None and cfg.world.maze_extra_openings is None
    assert "maze_family" not in cfg.to_dict()["world"] and "maze_extra_openings" not in cfg.to_dict()["world"]
    assert MW.maze_config(**C6, family="tree").to_dict() == cfg.to_dict()


def test_the_island_family_is_recorded_in_the_configuration():
    w = MW.maze_config(**C6, family="islands", k_r=2).world
    assert (w.maze_family, w.maze_extra_openings) == ("islands", 2)
    assert MW.maze_config(**C6, family="islands", k_r=2).to_dict()["world"]["maze_family"] == "islands"


def test_unknown_family_or_k_r_on_a_tree_is_refused():
    with pytest.raises(ValueError, match="family"):
        MW.maze_config(**C6, family="loops")
    with pytest.raises(ValueError, match="k_r"):
        MW.maze_config(**C6, family="tree", k_r=2)


def test_the_world_builds_island_mazes(iface):
    ids = [30_000, 30_001, 30_002]
    w = _world(iface, ids, MW.maze_config(**C6, family="islands", k_r=2))
    for k, mid in enumerate(ids):
        mz, pl, _ = I.maze_for(run_seed=1_190_000, maze_id=mid, episode=0, c=6, k_r=2, n_spawns=4)
        assert np.array_equal(w.mazes[k].wall, mz.wall) and w.placements[k] == pl
        assert np.array_equal(w.fields[k, w.ch.WALL].numpy() > 0, mz.wall)


def test_the_tree_family_still_builds_tree_mazes(iface):
    w = _world(iface, [30_000], MW.maze_config(**C6))
    mz, pl = M.maze_for(run_seed=1_190_000, maze_id=30_000, episode=0, c=6, n_spawns=4)
    assert np.array_equal(w.mazes[0].wall, mz.wall) and w.placements[0] == pl


def test_scramble_is_refused_for_islands(iface):
    with pytest.raises(ValueError, match="scramble"):
        _world(iface, [30_000, 30_001], MW.maze_config(**C6, family="islands", k_r=0), access="scramble")


def test_a_tree_config_built_on_an_island_base_is_a_tree_config():
    """Astra: `maze_config(base=island_cfg, family="tree")` must clear the island fields."""
    isl = MW.maze_config(**C6, family="islands", k_r=2)
    tree = MW.maze_config(isl, **C6, family="tree")
    assert tree.world.maze_family is None and tree.world.maze_extra_openings is None
    assert tree.to_dict() == MW.maze_config(**C6).to_dict()
