"""E5-1's hosts (docs/E5/E5-1-DESIGN.md §4, §7.2): 03r's SH-route graphs rebuilt from its record, and L1 grafted on
each host.

- `sh_route(con, name)`: the graph rebuilt by 03's sampler at 03r's settings (the name's seed, 20 passes), its arrays
  checked against 03r's content manifest (`graphs_content_manifest.json`: names, dtypes, shapes and bytes, D106). The
  raw-byte manifest is checked by the E5-1a stage where zlib allows. Graph files are never committed (rule 1).
- `host(con, name)`: N2 itself for "N2", else the SH-route graph; `grafted(...)`: L1 on it, its spec and interface,
  with the checks of §7.2 (L1's 16 output edges onto the 8 turn read-out neurons, its two noses, every interface neuron).
- `calibrated_gains(name)`: 03r's per-graph calibrated motor gains (`supplement.json`), for O0 only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from .. import graft as G
from ..brain import BrainSpec
from ..e4s import arms as A
from ..e4s import comparator as CMP
from ..interface import load_interface

ROOT = Path(__file__).resolve().parents[2]
R03 = ROOT / "experiments" / "03r-replication"
PASSES = 20  # 03r's chains (ensembles.json)


def _read(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def content_sha256(arrays: dict) -> str:
    """03r's `_sha_content` on in-memory arrays: per name, sorted, the name, dtype, shape and bytes."""
    h = hashlib.sha256()
    for k in sorted(arrays):
        a = np.ascontiguousarray(arrays[k])
        h.update(k.encode())
        h.update(str(a.dtype).encode())
        h.update(str(a.shape).encode())
        h.update(a.tobytes())
    return h.hexdigest()


def record(name: str) -> dict:
    """03r's build record for one graph (seed, passes, substitutions)."""
    rows = [r for r in _read(R03 / "ensembles.json")["graphs"] if r["name"] == name]
    if len(rows) != 1:
        raise SystemExit(f"{name} is not in 03r's ensembles.json")
    return rows[0]


def sh_route(con, name: str):
    """(the rebuilt graph, its check): stops unless its arrays match 03r's content manifest."""
    from ..exp03 import samplers as S

    if not name.startswith("SH-route-"):
        raise ValueError(f"{name} is not an SH-route graph")
    rec = record(name)
    seed = int(name.rsplit("-", 1)[1])
    if rec["seed"] != seed or rec["passes"] != PASSES or rec["kind"] != "SH-route":
        raise SystemExit(f"{name}: 03r's record does not match its name (seed, passes, kind)")
    g, _ = S.build(con, "SH-route", seed=seed, passes=PASSES)
    sha = content_sha256({"chem": g.chem, "gap": g.gap})
    want = _read(R03 / "graphs_content_manifest.json")["graphs"].get(name)
    if sha != want:
        raise SystemExit(f"{name}: rebuilt arrays have sha256 {sha}, 03r's content manifest {want}")
    return con.with_masks(g.chem, g.gap, name), {"name": name, "seed": seed, "passes": PASSES,
                                                  "content_sha256": sha, "matches_content_manifest": True}


def host(con, name: str):
    if name == "N2":
        return con, {"name": "N2"}
    return sh_route(con, name)


def grafted(graph, l1: G.Module, probe: str = "real"):
    """(ext, spec, interface): L1 on the graph, checked: its 16 output edges onto the 8 turn read-out neurons at their
    designed weights, its two noses on the food channels, and every interface neuron present."""
    ext = G.graft_connectome(graph, l1)
    spec = BrainSpec.from_connectome(ext)
    n0 = int(ext.meta["worm_neurons"])
    turn = set(CMP.TURN_DORSAL + CMP.TURN_VENTRAL)
    outs = [(a, b) for a, b, _ in l1.synapses if b in turn]
    if len(outs) != 16 or {b for _, b in outs} != turn:
        raise SystemExit("L1 does not have its 16 output edges onto the 8 turn read-out neurons")
    for a, b in outs:
        if not ext.chem[ext.index(a), ext.index(b)] > 0:
            raise SystemExit(f"{graph.label}: L1's edge {a} -> {b} is missing after grafting")
    out_mask = A.output_edge_mask(ext, l1)
    if int(out_mask.sum()) != 16:
        raise SystemExit(f"{graph.label}: {int(out_mask.sum())} module edges onto host neurons, not 16")
    iface = G.graft_interface(ext, l1, probe=probe)
    names = list(iface.signal_names)
    noses = [ext.names[int(iface.sensor_neuron[i])] for i, s in enumerate(names) if int(iface.sensor_neuron[i]) >= n0]
    if sorted(noses) != sorted(l1.noses) or len(noses) != 2:
        raise SystemExit(f"{graph.label}: the noses are {noses}, not L1's")
    worm = load_interface(graph)
    if not all(int(i) < n0 for i in worm.mapped_neurons):
        raise SystemExit(f"{graph.label}: an interface neuron is missing")
    return ext, spec, iface


def calibrated_gains(name: str) -> tuple[float, float]:
    """(forward, turn): 03r's calibrated gains for a graph (N2, N2permK or an SH-route graph)."""
    row = _read(R03 / "supplement.json")["per_graph"].get(name)
    if row is None or "forward_gain" not in row:
        raise SystemExit(f"03r has no calibrated gains for {name}")
    return float(row["forward_gain"]), float(row["turn_gain"])
