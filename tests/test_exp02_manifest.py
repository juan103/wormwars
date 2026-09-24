"""A saved genome must refuse to be replayed on another graph, interface or sensing mode."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import shuffled
from wormwars.evo import load_genome, save_genome
from wormwars.evo.genomes import edge_hash
from wormwars.exp02.manifest import check_manifest, run_manifest
from wormwars.interface import interface_from_spec, load_interface, load_interface_spec, remapped_spec

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def con():
    return load_connectome()


def test_same_label_different_shuffle_is_refused(con, tmp_path):
    a = BrainSpec.from_connectome(shuffled(con, 1, "SH1"))
    b = BrainSpec.from_connectome(shuffled(con, 2, "SH1"))  # same label, different graph
    assert edge_hash(a) != edge_hash(b)
    g = Genome.random(a, Config().brain, 1, generator=torch.Generator().manual_seed(0))
    path = save_genome(tmp_path / "g.npz", g)
    load_genome(path, a, None)
    with pytest.raises(ValueError, match="edge set"):
        load_genome(path, b, None)


def test_manifest_refuses_another_interface_or_sensing(con, tmp_path):
    spec = BrainSpec.from_connectome(con)
    cfg = Config()
    iface = load_interface(con)
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(0))
    path = save_genome(tmp_path / "g.npz", g, cfg=cfg, **run_manifest(cfg, iface, spec))
    _, meta = load_genome(path, spec, None)
    check_manifest(meta, cfg, iface, spec)
    other = interface_from_spec(con, remapped_spec(
        load_interface_spec(), "food", [("ASIL", "ASIR"), ("ASJL", "ASJR"), ("ASGL", "ASGR")]))
    with pytest.raises(ValueError, match="interface_hash"):
        check_manifest(meta, cfg, other, spec)
    mono = cfg.copy()
    mono.world.food_sensing = "mono"
    with pytest.raises(ValueError, match="food_sensing"):
        check_manifest(meta, mono, iface, spec)


def test_old_files_without_a_manifest_still_load(con):
    spec = BrainSpec.from_connectome(con)
    g, meta = load_genome(ROOT / "runs" / "exp01b-direction-corrected" / "champion-N2-run00.npz", spec, None)
    assert "edge_hash" not in meta and g.cfg.init_chem_magnitude == "anatomical"
