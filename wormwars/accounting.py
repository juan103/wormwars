"""Compute accounting (roadmap v3, T0; docs/foundations/T0.md section 1; D068, D069).

Three counts, taken at the only places the work happens, so no call site can be missed:
- **worlds built:** `World.__init__`;
- **world-ticks:** `World.tick`, one per world in the batch per tick actually simulated;
- **neural updates:** `Brain.step`, S x B x substeps network updates (strains x batch x substeps).
  The unit ignores network size N, so a brain with neurons deleted counts the same per update.

Known gaps, by design:
- scripted controllers do not use `Brain.step` and count zero neural updates;
- `scripts/bench_brain.py`'s `SparseBrain` bypasses `Brain.step`: a benchmark, uncounted;
- geometry's `duel` builds worlds and calls `_combat` without `tick`, so it has worlds and zero
  world-ticks. Its time is recorded under "probe".

Each count goes to the innermost active category. Work outside any category goes to "other",
whose time is not measured: it is written as null, and the file flags it as uncategorised.
Experiment scripts run inside `attempt(...)` with a default category, so they leave nothing in
"other".

**Time:** synchronised wall-clock seconds per category. `torch.cuda.synchronize()` runs on every
visible device at category boundaries only, never in the hot loop. Time in a nested category is
not also counted in its parent. Category seconds exclude breeding, logging and I/O outside
categories, so they do not sum to `RunResult.gpu_seconds`.

**Pure measurement:** the hooks read tensor shapes, touch no tensor, draw no random numbers and
change no result (tested).
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

import torch

CATEGORIES = ("selection", "holdout", "snapshot", "final", "calibration", "probe", "measure",
              "tuning", "other")
COUNT_FIELDS = ("worlds_built", "world_ticks", "neural_updates")
TIME_UNIT = "synchronised wall-clock seconds per category (not GPU kernel time)"
NEURAL_UNIT = "strains x batch x substeps network updates (network size not included)"


@dataclass
class Counts:
    worlds_built: int = 0
    world_ticks: int = 0
    neural_updates: int = 0
    seconds: float = 0.0


def _sync() -> None:
    if torch.cuda.is_available() and torch.cuda.is_initialized():
        for d in range(torch.cuda.device_count()):
            torch.cuda.synchronize(d)


class Ledger:
    def __init__(self) -> None:
        self.enabled = True
        self.reset()

    def reset(self) -> None:
        self.counts: dict[str, Counts] = {}
        self._stack: list[list] = []  # [name, start of its current segment]
        self._timed: set[str] = set()

    def current(self) -> str:
        return self._stack[-1][0] if self._stack else "other"

    def _bucket(self) -> Counts:
        return self.counts.setdefault(self.current(), Counts())

    # ---- the three hooks
    def worlds(self, n: int) -> None:
        if self.enabled:
            self._bucket().worlds_built += int(n)

    def ticks(self, n_worlds: int) -> None:
        if self.enabled:
            self._bucket().world_ticks += int(n_worlds)

    def neural(self, n: int) -> None:
        if self.enabled:
            self._bucket().neural_updates += int(n)

    # ---- categories
    def _close_segment(self, now: float) -> None:
        if self._stack:
            name, start = self._stack[-1]
            self.counts.setdefault(name, Counts()).seconds += now - start

    def push(self, name: str) -> None:
        if name not in CATEGORIES:
            raise ValueError(f"unknown compute category {name!r}; one of {CATEGORIES}")
        if self.enabled:
            _sync()
        now = time.perf_counter()
        self._close_segment(now)
        self._stack.append([name, now])
        self._timed.add(name)
        self.counts.setdefault(name, Counts())

    def pop(self) -> None:
        """Always restores the parent, even if synchronising raises (a CUDA error surfaces
        there); the original exception still propagates."""
        try:
            if self.enabled:
                _sync()
        finally:
            now = time.perf_counter()
            if self._stack:  # a reset() inside a category empties the stack
                self._close_segment(now)
                self._stack.pop()
                if self._stack:
                    self._stack[-1][1] = now  # the parent resumes: its time excludes the child's

    # ---- reading
    def snapshot(self) -> dict:
        """Counts so far, including the time of the currently open segment."""
        out = {k: asdict(v) for k, v in self.counts.items()}
        if self._stack:
            name, start = self._stack[-1]
            out.setdefault(name, asdict(Counts()))["seconds"] += time.perf_counter() - start
        for k in out:
            if k not in self._timed:
                out[k]["seconds"] = None
        return out

    def since(self, before: dict) -> dict:
        """What was added since `before` (a `snapshot()`), including time-only changes."""
        out = {}
        for k, v in self.snapshot().items():
            b = before.get(k) or asdict(Counts())
            d = {f: v[f] - (b[f] or 0) for f in COUNT_FIELDS}
            d["seconds"] = None if v["seconds"] is None else v["seconds"] - (b["seconds"] or 0.0)
            if any(d[f] for f in COUNT_FIELDS) or d["seconds"]:
                out[k] = d
        return out


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


def totals(categories: dict) -> dict:
    out = {f: sum(c[f] for c in categories.values()) for f in COUNT_FIELDS}
    secs = [c["seconds"] for c in categories.values() if c["seconds"] is not None]
    out["seconds_timed"] = float(sum(secs))
    return out


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parents[1],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


@contextmanager
def attempt(directory, default: str | None = None, **extra):
    """Run a script's work as one recorded attempt. A uniquely named file is written to
    `directory` when the block ends, **whether it succeeds or raises**, so failed attempts and
    retries keep their accounting. `default` is a category for work the block does not
    categorise more specifically (innermost wins), so nothing lands in untimed "other"."""
    directory = Path(directory)
    before = LEDGER.snapshot()
    t0 = datetime.now(timezone.utc)
    status, error = "completed", None
    try:
        if default is not None:
            with category(default):
                yield
        else:
            yield
    except BaseException as e:  # noqa: BLE001  (recorded, then re-raised)
        status, error = "failed", f"{type(e).__name__}: {e}"
        raise
    finally:
        cats = LEDGER.since(before)
        doc = {**extra, "status": status, "error": error,
               "started_utc": t0.isoformat(timespec="seconds"),
               "ended_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "pid": os.getpid(), "git_commit": _git_commit(),
               "cuda_devices": [torch.cuda.get_device_name(d) for d in range(torch.cuda.device_count())]
               if torch.cuda.is_available() else [],
               "time_unit": TIME_UNIT, "neural_update_unit": NEURAL_UNIT,
               "uncategorised": "other" in cats, "categories": cats, "totals": totals(cats)}
        directory.mkdir(parents=True, exist_ok=True)
        name = f"{t0.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}.json"
        (directory / name).write_text(json.dumps(doc, indent=1), encoding="utf-8")
        if doc["uncategorised"]:
            print(f"[accounting] warning: uncategorised work in {directory / name}")


def aggregate(directory) -> dict:
    """Sum every attempt file in `directory` (one per process and invocation), failed ones
    included, into one experiment-level record."""
    cats: dict[str, dict] = {}
    attempts = []
    for path in sorted(Path(directory).glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        attempts.append({"file": path.name, "status": d.get("status"), "command": d.get("command"),
                         "git_commit": d.get("git_commit")})
        for k, v in d.get("categories", {}).items():
            c = cats.setdefault(k, {**{f: 0 for f in COUNT_FIELDS}, "seconds": 0.0})
            for f in COUNT_FIELDS:
                c[f] += v[f]
            c["seconds"] = None if (c["seconds"] is None or v["seconds"] is None) else c["seconds"] + v["seconds"]
    return {"time_unit": TIME_UNIT, "neural_update_unit": NEURAL_UNIT, "attempts": attempts,
            "failed_attempts": sum(a["status"] == "failed" for a in attempts),
            "uncategorised": "other" in cats, "categories": cats, "totals": totals(cats)}


def write_aggregate(directory, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(aggregate(directory), indent=1), encoding="utf-8")
    return path
