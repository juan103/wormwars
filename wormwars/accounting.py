"""Compute accounting (roadmap v3, T0; docs/foundations/T0.md section 1; D068).

Three counts, taken at the only places the work happens, so no call site can be missed:
- **worlds built:** `World.__init__`;
- **world-ticks:** `World.tick`, one per world in the batch per tick actually simulated;
- **neural updates:** `Brain.step`, S x B x substeps network updates (strains x batch x
  substeps). Scripted controllers do not use `Brain.step` and count zero.

Each count goes to the innermost active category; outside any category it goes to "other". Time
is **synchronised wall time** per category: `torch.cuda.synchronize()` runs at category boundaries
only (never in the hot loop), and time spent in a nested category is not also counted in its
parent. Counting is pure measurement: it reads tensor shapes, draws no random numbers and changes
no result (tested).
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from functools import wraps
from pathlib import Path

import torch

CATEGORIES = ("selection", "holdout", "snapshot", "final", "calibration", "probe", "measure",
              "tuning", "other")
TIME_UNIT = "synchronised wall-clock seconds per category (not GPU kernel time)"


@dataclass
class Counts:
    worlds_built: int = 0
    world_ticks: int = 0
    neural_updates: int = 0
    seconds: float = 0.0


def _sync() -> None:
    if torch.cuda.is_available() and torch.cuda.is_initialized():
        torch.cuda.synchronize()


class Ledger:
    def __init__(self) -> None:
        self.enabled = True
        self.reset()

    def reset(self) -> None:
        self.counts: dict[str, Counts] = {}
        self._stack: list[list] = []  # [name, start of the current segment]

    def current(self) -> str:
        return self._stack[-1][0] if self._stack else "other"

    def _bucket(self) -> Counts:
        return self.counts.setdefault(self.current(), Counts())

    # the three hooks
    def worlds(self, n: int) -> None:
        if self.enabled:
            self._bucket().worlds_built += int(n)

    def ticks(self, n_worlds: int) -> None:
        if self.enabled:
            self._bucket().world_ticks += int(n_worlds)

    def neural(self, n: int) -> None:
        if self.enabled:
            self._bucket().neural_updates += int(n)

    # categories
    def _close_segment(self, now: float) -> None:
        if self._stack:
            name, start = self._stack[-1]
            self.counts.setdefault(name, Counts()).seconds += now - start

    def push(self, name: str) -> None:
        if name not in CATEGORIES:
            raise ValueError(f"unknown compute category {name!r}; one of {CATEGORIES}")
        if not self.enabled:
            self._stack.append([name, 0.0])
            return
        _sync()
        now = time.perf_counter()
        self._close_segment(now)
        self._stack.append([name, now])
        self.counts.setdefault(name, Counts())

    def pop(self) -> None:
        if not self.enabled:
            self._stack.pop()
            return
        _sync()
        now = time.perf_counter()
        self._close_segment(now)
        self._stack.pop()
        if self._stack:
            self._stack[-1][1] = now  # the parent resumes: its time excludes the child's

    def snapshot(self) -> dict:
        return {k: asdict(v) for k, v in self.counts.items()}

    def since(self, before: dict) -> dict:
        """Counts added since `before` (a `snapshot()`), dropping categories with nothing new."""
        out = {}
        for k, v in self.snapshot().items():
            b = before.get(k, asdict(Counts()))
            d = {f: v[f] - b[f] for f in v}
            if any(d[f] for f in ("worlds_built", "world_ticks", "neural_updates")):
                out[k] = d
        return out

    def write(self, path, extra: dict | None = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = {**(extra or {}), "time_unit": TIME_UNIT, "categories": self.snapshot(),
               "neural_update_unit": "strains x batch x substeps network updates"}
        path.write_text(json.dumps(doc, indent=1), encoding="utf-8")
        return path


LEDGER = Ledger()


@contextmanager
def category(name: str):
    LEDGER.push(name)
    try:
        yield
    finally:
        LEDGER.pop()


def counted(name: str):
    """Decorator: run the function under a compute category."""
    def wrap(fn):
        @wraps(fn)
        def inner(*a, **k):
            with category(name):
                return fn(*a, **k)
        return inner
    return wrap
