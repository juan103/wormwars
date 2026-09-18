"""Load the cached real connectome.

The cache is produced by `scripts/fetch_connectome.py` from the published spreadsheet. Nothing in
this module invents, approximates or repairs connectome data; if the cache is missing it says so
and stops.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = ROOT / "data" / "cache" / "cook2019_herm.npz"

N_NEURONS = 302
NEURON_CLASSES = ("pharyngeal", "sensory", "inter", "motor", "other")


class ConnectomeError(RuntimeError):
    """Raised when connectome data is missing or does not look like what we expect."""


@dataclass(frozen=True)
class Connectome:
    """A wiring mask plus the anatomical weights it came with.

    `chem[i, j]` is the connection from neuron i (presynaptic) to neuron j (postsynaptic).
    `gap[i, j] == gap[j, i]` and the diagonal is zero.

    `weight_kind` names the physical quantity the weights are, because initialisation scales with
    it. For the Cook 2019 data it is `"em_sections"`: the total number of EM serial sections of
    connectivity, which folds together synapse count and synapse size. It is not a synapse count.
    """

    names: tuple[str, ...]
    classes: tuple[str, ...]
    chem: np.ndarray
    gap: np.ndarray
    weight_kind: str
    meta: dict
    label: str = "N2"

    def __post_init__(self) -> None:
        n = len(self.names)
        if len(self.classes) != n:
            raise ConnectomeError(f"{n} names but {len(self.classes)} classes")
        for mat, what in ((self.chem, "chem"), (self.gap, "gap")):
            if mat.shape != (n, n):
                raise ConnectomeError(f"{what} has shape {mat.shape}, expected {(n, n)}")
        bad = set(self.classes) - set(NEURON_CLASSES)
        if bad:
            raise ConnectomeError(f"unknown neuron classes: {sorted(bad)}")

    @property
    def n(self) -> int:
        return len(self.names)

    @property
    def index_of(self) -> dict[str, int]:
        return {name: i for i, name in enumerate(self.names)}

    def index(self, name: str) -> int:
        """Index of one neuron, by its individual name. Raises if it is not in the dataset."""
        try:
            return self.index_of[name]
        except KeyError:
            raise ConnectomeError(
                f"neuron {name!r} is not in the {self.label} dataset "
                f"({self.n} neurons). Do not substitute another neuron for it."
            ) from None

    def indices(self, names) -> list[int]:
        return [self.index(name) for name in names]

    def of_class(self, cls: str) -> list[str]:
        return [n for n, c in zip(self.names, self.classes) if c == cls]

    def with_masks(self, chem: np.ndarray, gap: np.ndarray, label: str) -> "Connectome":
        """A sibling connectome (a shuffle or a random graph) on the same neurons."""
        return Connectome(self.names, self.classes, chem, gap, self.weight_kind, self.meta, label)

    def summary(self) -> str:
        from collections import Counter

        counts = Counter(self.classes)
        return (
            f"{self.label}: {self.n} neurons "
            f"({', '.join(f'{k}={counts[k]}' for k in NEURON_CLASSES if counts[k])}), "
            f"{int((self.chem > 0).sum())} chemical edges, "
            f"{int((self.gap > 0).sum()) // 2} gap junctions, weight_kind={self.weight_kind}"
        )


@lru_cache(maxsize=4)
def load_connectome(path: str | Path | None = None) -> Connectome:
    """Load the cached Cook 2019 hermaphrodite connectome."""
    path = Path(path) if path is not None else DEFAULT_CACHE
    if not path.exists():
        raise ConnectomeError(
            f"connectome cache not found at {path}.\n"
            "Run:  python scripts/fetch_connectome.py\n"
            "This downloads the published Cook et al. 2019 spreadsheet and verifies its sha256. "
            "There is no fallback and no synthetic substitute."
        )
    # allow_pickle=False: loading a .npz with pickle enabled can execute arbitrary code, and this
    # project publishes .npz files that people will download. Nothing we store needs it -- the
    # arrays are numeric and the metadata is a unicode string array.
    data = np.load(path, allow_pickle=False)
    meta = json.loads(str(data["meta"]))
    con = Connectome(
        names=tuple(str(x) for x in data["names"]),
        classes=tuple(str(x) for x in data["classes"]),
        chem=np.ascontiguousarray(data["chem"], dtype=np.float32),
        gap=np.ascontiguousarray(data["gap"], dtype=np.float32),
        weight_kind=meta["weight_kind"],
        meta=meta,
        label="N2",
    )
    if con.n != N_NEURONS:
        raise ConnectomeError(f"expected {N_NEURONS} neurons, cache has {con.n}")
    asym = float(np.abs(con.gap - con.gap.T).max())
    if asym != 0.0:
        raise ConnectomeError(f"gap matrix is not symmetric (max |G - G^T| = {asym})")
    return con
