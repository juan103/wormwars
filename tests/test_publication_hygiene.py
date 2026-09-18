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

    Measured two ways, because normalising by the mean is defeatable. `clamp_(0, g_max)` clips the
    4 gap junctions of 1091 that start above g_max, which moves mean(g) by ~8% and makes a
    mean-normalised comparison fail on every entry at once -- reading 0% for a vector that is still
    99.6% anatomical. Fixing the scale by the median ratio cannot be moved by four entries. Both
    are checked and the worse answer is the one that counts (DECISIONS.md D028).

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
        """Worst of two scale estimates: the mean, and the median of the per-entry ratio."""
        v = np.abs(np.asarray(values, dtype=np.float64))
        if v.shape != reference.shape:
            return 0.0
        best = 0.0
        if v.mean() > 0:
            best = float(
                np.isclose(v / v.mean(), reference / reference.mean(), rtol=1e-3).mean()
            )
        ok = reference > 0
        if ok.any():
            scale = float(np.median(v[ok] / reference[ok]))
            if np.isfinite(scale) and scale > 0:
                best = max(best, float(np.isclose(v, scale * reference, rtol=1e-3).mean()))
        return best

    LIMIT = 0.01  # 1%: the worst committed genome measures 0.46% under either normalisation
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


def test_no_committed_file_contains_graph_structure():
    """Not the genomes -- the GRAPHS: N2's wiring, and the SH and RD controls.

    The proportionality guard above cannot see a control graph. SH carries the real anatomical
    weights in permuted positions and the real degree sequence, so nothing about it is proportional
    to anything. This looks for the structures directly, in every tracked file whatever its format:

      * any 302x302 matrix, or any array with 302*302 entries
      * any integer array of index pairs (an edge list)
      * any array equal to one of N2's degree sequences, sorted or not
      * any array whose sorted values are the anatomical weight multiset, up to one scale factor

    The control graphs are built in memory from the fetched connectome plus an integer seed
    (`wormwars/connectome/graphs.py`, which has no write path). They must never reach a file.
    """
    import io
    import re
    from collections import Counter

    from wormwars.connectome.loader import DEFAULT_CACHE, N_NEURONS

    N = N_NEURONS
    refs = {}
    if DEFAULT_CACHE.exists():  # the anatomy-dependent half of the check
        from wormwars.connectome import load_connectome

        con = load_connectome()
        refs["weights"] = {
            "chemical": np.sort(con.chem[con.chem > 0].astype(np.float64)),
            "gap": np.sort(con.gap[np.triu(con.gap, 1) > 0].astype(np.float64)),
        }
        refs["degrees"] = {
            "chemical out-degree": (con.chem > 0).sum(1),
            "chemical in-degree": (con.chem > 0).sum(0),
            "gap degree": (con.gap > 0).sum(1),
        }
        n_chem = int((con.chem > 0).sum())
        n_gap = int((np.triu(con.gap, 1) > 0).sum())
        refs["edge_counts"] = {n_chem, n_gap, 2 * n_chem, 2 * n_gap}

    def numeric_arrays(rel, raw):
        """Every numeric array in one file, whatever the format."""
        if raw[:4] == b"PK\x03\x04":
            with np.load(io.BytesIO(raw), allow_pickle=False) as d:
                return [(k, np.asarray(d[k])) for k in d.files if d[k].dtype.kind in "fiub"]
        if raw[:6] == b"\x93NUMPY":
            a = np.load(io.BytesIO(raw), allow_pickle=False)
            return [("<npy>", a)] if a.dtype.kind in "fiub" else []
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return []
        found = []
        if rel.endswith((".json", ".cff", ".ipynb")):
            try:
                obj = json.loads(text)
            except ValueError:
                obj = None
            if obj is not None:

                def numeric(x):
                    return isinstance(x, (int, float)) and not isinstance(x, bool)

                def rectangular(o):
                    """A numeric list, or a list of equal-length numeric lists: one array.

                    `[[i, j], [i, j], ...]` is an edge list and `[[...302...], ...]` is a matrix.
                    Without this they decompose into thousands of length-2 rows and nothing fires.
                    """
                    if not isinstance(o, list) or not o:
                        return None
                    if all(numeric(x) for x in o):
                        return np.asarray(o, dtype=np.float64)
                    rows = [rectangular(x) for x in o]
                    if any(r is None for r in rows):
                        return None
                    shapes = {r.shape for r in rows}
                    return np.stack(rows) if len(shapes) == 1 else None

                def walk(o, path):
                    if isinstance(o, dict):
                        for k, v in o.items():
                            walk(v, f"{path}.{k}")
                    elif isinstance(o, list):
                        block = rectangular(o)
                        if block is not None:
                            found.append((path, block))
                        else:
                            for i, v in enumerate(o):
                                walk(v, f"{path}[{i}]")

                walk(obj, "")
                return found
        tokens = re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", text)
        if len(tokens) >= 200:
            try:
                found.append(("<numbers in text>", np.asarray([float(t) for t in tokens])))
            except ValueError:
                pass
        return found

    def offences(arr):
        out = []
        a = np.asarray(arr)
        if a.ndim >= 2 and a.shape[-2:] == (N, N):
            out.append(f"is a {N}x{N} matrix (shape {a.shape})")
        if a.size == N * N:
            out.append(f"has {N * N} entries, the size of a full adjacency matrix")
        flat = a.reshape(-1).astype(np.float64)
        integral = bool(flat.size) and np.all(flat == np.floor(flat)) and np.all(flat >= 0)
        in_range = integral and float(flat.max()) < N
        if a.ndim == 2 and a.shape[-1] == 2 and in_range:
            out.append(f"looks like an edge list (shape {a.shape}, whole-number pairs below {N})")
        # index vectors split across separate arrays: {"i": [...], "j": [...]}
        if a.ndim == 1 and in_range and flat.size in refs.get("edge_counts", set()):
            if np.unique(flat).size > N // 4:
                out.append(
                    f"is {flat.size} whole numbers below {N} -- the length of an edge list, so "
                    f"this looks like one column of neuron indices"
                )
        for what, deg in refs.get("degrees", {}).items():
            d = deg.astype(np.float64)
            if flat.size == d.size and (
                np.array_equal(flat, d) or np.array_equal(np.sort(flat), np.sort(d))
            ):
                out.append(f"is N2's {what} sequence")
        for what, w in refs.get("weights", {}).items():
            if flat.size == w.size:
                sorted_abs = np.sort(np.abs(flat))
                if np.allclose(sorted_abs, w, rtol=1e-6, atol=0):
                    out.append(f"is the anatomical {what} weight multiset")
                elif sorted_abs.max() > 0 and Counter(
                    np.round(sorted_abs / sorted_abs.max(), 9).tolist()
                ) == Counter(np.round(w / w.max(), 9).tolist()):
                    out.append(f"is the anatomical {what} weight multiset, up to one scale factor")
        return out

    offenders = []
    for rel in tracked_files():
        raw = (ROOT / rel).read_bytes()
        for key, arr in numeric_arrays(rel, raw):
            for bad in offences(arr):
                offenders.append(f"{rel} [{key}] {bad}")
    assert not offenders, (
        "committed files contain connectome or control-graph structure:\n  " + "\n  ".join(offenders)
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
