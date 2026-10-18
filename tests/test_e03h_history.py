"""03h's per-history read-outs (wormwars/exp03/measures.py history(per_history=True); DESIGN.md §5): the default output is
unchanged, and each difference is the two histories' own values subtracted."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.exp02 import grid
from wormwars.exp03.measures import history
from wormwars.interface import load_interface

ROOT = Path(__file__).resolve().parents[1]


def test_per_history_values_reproduce_the_differences_and_leave_the_default_unchanged():
    con = load_connectome()
    iface = load_interface(con)
    cfg = grid.task_config(Config(), "T1")
    bank = json.loads((ROOT / "experiments" / "03-generation0" / "pilot.json").read_text(encoding="utf-8"))["bank"]
    g = Genome.random(BrainSpec.from_connectome(con), cfg.brain, 6, generator=torch.Generator().manual_seed(4))
    plain = history(g, cfg, iface, bank)
    full = history(g, cfg, iface, bank, per_history=True)
    for k, v in plain.items():
        for part, arr in v.items():
            assert np.array_equal(arr, full[k][part])
        r, f = full[k]["rising"], full[k]["falling"]
        assert np.array_equal(full[k]["final"], r["final"] - f["final"])
        assert np.array_equal(full[k]["after"], r["after"] - f["after"])
        assert np.array_equal(full[k]["steady_contrast"], f["steady"] - r["steady"])
    assert set(plain["raw_turn"]) == {"final", "after", "steady_contrast"}
