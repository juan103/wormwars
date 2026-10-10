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


def anatomical_references() -> dict:
    """label -> (chemical, gap) anatomical weights, in each graph's edge order: N2 and its controls.
    The graphs are the loaded connectome's (kept on it, so a grafted label can be rebuilt)."""
    from wormwars.connectome import load_connectome
    from wormwars.connectome.graphs import random_graph, shuffled

    con = load_connectome()
    graphs = {"N2": con}
    for k in range(1, 6):
        graphs[f"SH{k}"] = shuffled(con, k, f"SH{k}")
        graphs[f"RD{k}"] = random_graph(con, k, f"RD{k}")
    return {lab: (g.chem[g.chem > 0].astype(np.float64), g.gap[np.triu(g.gap, 1) > 0].astype(np.float64), g)
            for lab, g in graphs.items()}


def proportional_fraction(values, reference):
    """Worst of two scale estimates: the mean, and the median of the per-entry ratio."""
    v = np.abs(np.asarray(values, dtype=np.float64))
    if v.shape != reference.shape:
        return 0.0
    best = 0.0
    if v.mean() > 0:
        best = float(np.isclose(v / v.mean(), reference / reference.mean(), rtol=1e-3).mean())
    ok = reference > 0
    if ok.any():
        scale = float(np.median(v[ok] / reference[ok]))
        if np.isfinite(scale) and scale > 0:
            best = max(best, float(np.isclose(v, scale * reference, rtol=1e-3).mean()))
    return best


PROPORTIONAL_LIMIT = 0.01  # 1%: the worst committed genome measures 0.46% under either normalisation


def genome_offences(label, w, g, anat) -> list[str]:
    """Why a genome's weights would leak the anatomy. A grafted genome ("<graph>+<module>") is checked
    on its worm block, rebuilt from the registered module; an unregistered module is itself an offence.
    Labels of no known graph are not checked (an unknown graph carries no N2 weights)."""
    w, g = np.atleast_2d(w), np.atleast_2d(g)
    if label and "+" in label:
        base, name = label.split("+", 1)
        if base not in anat:
            return []
        from wormwars import graft as G

        if name not in G.MODULES:
            return [f"{label}: the module {name!r} is not registered in wormwars.graft.MODULES, so its worm "
                    "block cannot be checked"]
        ext = G.graft_connectome(anat[base][2], G.MODULES[name])
        w, g = G.worm_parameters(ext, w, g)
        label = base
    if label not in anat:
        return []
    out = []
    for key, arr, reference in (("w", w, anat[label][0]), ("g", g, anat[label][1])):
        worst = max(proportional_fraction(arr[i], reference) for i in range(arr.shape[0]))
        if worst > PROPORTIONAL_LIMIT:
            out.append(f"{key} is {worst:.1%} proportional to {label} weights")
    return out


def large_square_offence(a) -> bool:
    """A square matrix wider than the worm's 302 neurons: a grafted connectome, or a genome's dense
    weights, whose leading block would be the worm's (E4s). Up to 302 + 256 neurons."""
    from wormwars.connectome.loader import N_NEURONS

    a = np.asarray(a)
    return a.ndim >= 2 and a.shape[-1] == a.shape[-2] and N_NEURONS < a.shape[-1] <= N_NEURONS + 256


MAZE_SIDE_MAX = 8  # the largest maze any experiment plays is 6 × 6 (E3d); 8 leaves a margin


def is_maze_spawn_list(key: str, arr) -> bool:
    """D230: E3d's maze records list each maze's spawn cells, at most 4 [row, column] pairs of a c × c maze, under
    a key named "spawns". Such a list is a pair list of tiny whole numbers, not a 302-neuron edge list; only it
    is exempt from the edge-list offence."""
    a = np.asarray(arr, dtype=np.float64)
    return (key.endswith(".spawns") and a.ndim == 2 and a.shape[1] == 2 and 1 <= a.shape[0] <= 4
            and float(a.min()) >= 0 and float(a.max()) < MAZE_SIDE_MAX)


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

    anat = anatomical_references()
    offenders = []
    for rel in [f for f in tracked_files() if f.endswith(".npz")]:
        d = np.load(ROOT / rel, allow_pickle=False)
        if "meta" not in d.files:
            continue
        label = json.loads(str(d["meta"])).get("graph")
        offenders += [f"{rel}: {o}" for o in genome_offences(label, d["w"], d["g"], anat)]
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
        if large_square_offence(a):
            out.append(f"is a square matrix wider than {N} (shape {a.shape}): a grafted connectome?")
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
                if "edge list" in bad and is_maze_spawn_list(key, arr):
                    continue  # a maze's spawn cells (D230)
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


# ----------------------------------------------------------------------------- grafted genomes (E4s)
# A grafted genome (`wormwars/graft.py`) is labelled "<graph>+<module>" and its worm edges are
# interleaved with the module's, so the guards above would skip it (Fable, E4s design review, D141).
# These tests run on genomes built in memory, never on a committed fixture: a fixture with an
# anatomical block would itself break rule 1.


def _toy_module():
    from wormwars.graft import Module

    return Module(name="hygiene-toy", neurons=("E4S_HA", "E4S_HB"),
                  synapses=(("E4S_HA", "SMDDL", 1.0), ("SMDVL", "E4S_HB", 0.5), ("E4S_HA", "E4S_HB", -1.0)))


def test_the_genome_guard_sees_a_grafted_unevolved_genome(monkeypatch):
    import torch

    from wormwars import graft as G
    from wormwars.brain import BrainSpec, Genome
    from wormwars.config import Config
    from wormwars.connectome.loader import DEFAULT_CACHE

    if not DEFAULT_CACHE.exists():
        pytest.skip("connectome not fetched; run scripts/fetch_connectome.py")
    from wormwars.connectome import load_connectome

    con, m = load_connectome(), _toy_module()
    monkeypatch.setitem(G.MODULES, m.name, m)
    ext = G.graft_connectome(con, m)
    base = Genome.random(BrainSpec.from_connectome(con), Config().brain, 1, generator=torch.Generator().manual_seed(1))
    unevolved = G.seeded_genome(ext, m, Config().brain, base=base)
    anat = anatomical_references()
    found = genome_offences(ext.label, unevolved.w.numpy(), unevolved.g.numpy(), anat)
    assert any(f.startswith("w is") for f in found), found  # the chemical weights interleave with the module's
    rng = np.random.default_rng(2)  # an evolved-looking genome: no anatomical scale left
    w = rng.normal(size=unevolved.w.shape).astype(np.float32)
    g = np.abs(rng.normal(size=unevolved.g.shape)).astype(np.float32)
    assert genome_offences(ext.label, w, g, anat) == []


def test_an_unregistered_grafted_label_is_an_offence():
    found = genome_offences("N2+never-registered", np.zeros((1, 3)), np.zeros((1, 3)), {"N2": None})
    assert found and "not registered" in found[0]


def test_a_square_matrix_larger_than_the_worm_is_structure():
    assert large_square_offence(np.zeros((332, 332)))
    assert large_square_offence(np.zeros((4, 310, 310)))
    assert not large_square_offence(np.zeros((10, 10)))
    assert not large_square_offence(np.zeros((332, 8)))


def test_the_maze_spawn_exemption_is_narrow():
    """D230: only a list of at most 4 [row, column] pairs below 8 under a key named "spawns" is exempt from the
    edge-list offence; a neuron edge list stays an offence whatever its key."""
    assert is_maze_spawn_list(".blocks.0.mazes[3].spawns", [[0, 4], [5, 2], [3, 0], [1, 5]])
    assert not is_maze_spawn_list(".blocks.0.mazes[3].spawns", [[0, 4], [5, 2], [3, 0], [1, 5], [2, 2]])  # 5 rows
    assert not is_maze_spawn_list(".spawns", [[0, 40], [5, 2]])  # an index past any maze
    assert not is_maze_spawn_list(".edges", [[0, 4], [5, 2]])  # another key
    edges = np.stack([np.arange(300), np.arange(1, 301)], axis=1)
    assert not is_maze_spawn_list(".spawns", edges)
