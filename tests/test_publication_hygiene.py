"""Guards on what this repository is allowed to contain.

The connectome is published under a copyright notice with no redistribution licence, so neither the
data nor anything that reconstructs it may be committed. These tests exist because that rule was
broken once: an unevolved genome's |W| is proportional to the anatomical weights by construction,
and the frozen opponent suite is unevolved (DECISIONS.md D028).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def tracked_files() -> list[str]:
    return subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
    ).splitlines()


def test_no_np_load_enables_pickle():
    """Pickle in np.load is arbitrary code execution on any file a user downloads.

    Parsed with ast rather than matched with a regex: `np.load(Path(p), allow_pickle=False)`
    defeats a naive paren match, and a guard that cries wolf gets switched off.
    """
    import ast

    offenders = []
    for path in ROOT.rglob("*.py"):
        if any(part in (".venv", "__pycache__") for part in path.parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "load"):
                continue
            if not (isinstance(func.value, ast.Name) and func.value.id in ("np", "numpy")):
                continue
            kw = {k.arg: k.value for k in node.keywords}
            ok = (
                "allow_pickle" in kw
                and isinstance(kw["allow_pickle"], ast.Constant)
                and kw["allow_pickle"].value is False
            )
            if not ok:
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert not offenders, "np.load must pass allow_pickle=False:\n  " + "\n  ".join(offenders)


def test_every_committed_npz_loads_without_pickle():
    files = [f for f in tracked_files() if f.endswith(".npz")]
    assert files, "no .npz files are tracked; this test would be vacuous"
    for rel in files:
        d = np.load(ROOT / rel, allow_pickle=False)
        for key in d.files:
            _ = d[key]


def test_no_committed_genome_reproduces_the_anatomical_weights():
    """An unevolved genome leaks the connectome's weights; an evolved one does not.

    Skips cleanly when the connectome has not been fetched, because it needs the real weights to
    compare against and this repository deliberately does not ship them.
    """
    from wormwars.connectome.loader import DEFAULT_CACHE

    if not DEFAULT_CACHE.exists():
        pytest.skip("connectome not fetched; run scripts/fetch_connectome.py")

    from wormwars.connectome import load_connectome
    from wormwars.connectome.graphs import random_graph, shuffled

    con = load_connectome()
    graphs = {"N2": con}
    for k in range(1, 6):
        graphs[f"SH{k}"] = shuffled(con, k, f"SH{k}")
        graphs[f"RD{k}"] = random_graph(con, k, f"RD{k}")
    anat = {
        lab: (
            g.chem[g.chem > 0].astype(np.float64),
            g.gap[np.triu(g.gap, 1) > 0].astype(np.float64),
        )
        for lab, g in graphs.items()
    }

    def proportional_fraction(values, reference):
        v = np.abs(np.asarray(values, dtype=np.float64))
        if v.shape != reference.shape or v.mean() <= 0:
            return 0.0
        return float(np.isclose(v / v.mean(), reference / reference.mean(), rtol=1e-3).mean())

    LIMIT = 0.01  # 1%: chance agreement measures 0.0-0.2% across all committed genomes
    offenders = []
    for rel in [f for f in tracked_files() if f.endswith(".npz")]:
        d = np.load(ROOT / rel, allow_pickle=False)
        if "meta" not in d.files:
            continue
        label = json.loads(str(d["meta"])).get("graph")
        if label not in anat:
            continue
        chem_anat, gap_anat = anat[label]
        for key, reference in (("w", chem_anat), ("g", gap_anat)):
            arr = np.atleast_2d(d[key])
            worst = max(proportional_fraction(arr[i], reference) for i in range(arr.shape[0]))
            if worst > LIMIT:
                offenders.append(f"{rel}: {key} is {worst:.1%} proportional to {label} weights")
    assert not offenders, (
        "committed genomes reproduce the connectome's anatomical weights:\n  "
        + "\n  ".join(offenders)
    )


def test_the_frozen_suite_is_never_committed():
    """It is unevolved, so it is the connectome's weights in disguise. Regenerate it from its seed."""
    bad = [f for f in tracked_files() if "frozen-suite" in f]
    assert not bad, f"the frozen suite must not be committed: {bad}"


def test_the_frozen_suite_regenerates_deterministically():
    from wormwars.connectome.loader import DEFAULT_CACHE

    if not DEFAULT_CACHE.exists():
        pytest.skip("connectome not fetched; run scripts/fetch_connectome.py")

    import torch

    from wormwars.brain import BrainSpec
    from wormwars.config import Config
    from wormwars.connectome import load_connectome
    from wormwars.evo.coevolve import make_frozen_suite

    spec = BrainSpec.from_connectome(load_connectome())
    cfg = Config()
    a, meta_a = make_frozen_suite(spec, cfg, n=6)
    b, meta_b = make_frozen_suite(spec, cfg, n=6)
    assert torch.equal(a.flat(), b.flat()), "the suite must regenerate bit-identically"
    assert meta_a["suite_version"] == meta_b["suite_version"]
