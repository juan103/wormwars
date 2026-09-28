"""Guards for pre-registered runs, shared by runners after E1 (D103).

They are the ones E1's five review rounds produced (D095-D099), as reusable functions. E1's own
runner (`scripts/e1.py`) keeps its copies unchanged, because it is the published record of that run.

- `provenance` records the code, the environment and the connectome's hashes at a stage's start.
- `require_formal` refuses anything but CUDA on the registered GPU, the pinned environment, a clean
  tree (code and the pre-registration) and a pushed HEAD.
- `start_marker` is exclusive: a started stage is never silently rerun.
- `write_json` writes LF on every platform; `file_sha256` hashes text normalised to LF.
- `CapClock` checks a registered compute cap against the accounting's records.
- `lower_bound` is the paired percentile bootstrap over worlds, one-sided 95%.
- `require_same_code` and `require_same_env` compare a later stage with an earlier one.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache" / "cook2019_herm.npz"
SOURCE = ROOT / "data" / "raw" / "SI5_Connectome_adjacency_matrices_corrected_July_2020.xlsx"
ENV_KEYS = ("python", "numpy", "torch", "cuda", "gpu", "connectome_cache_sha256", "connectome_source_sha256")


class CapReached(Exception):
    pass


def git(*a, root: Path | None = None) -> str:
    return subprocess.check_output(["git", *a], cwd=root or ROOT, text=True).strip()


def _sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def provenance(guarded: list[str], root: Path | None = None) -> dict:
    return {"git_commit": git("rev-parse", "HEAD", root=root), "branch": git("rev-parse", "--abbrev-ref", "HEAD", root=root),
            "dirty": bool(git("status", "--porcelain", "--", *guarded, root=root)),
            "python": platform.python_version(), "numpy": np.__version__,
            "torch": torch.__version__, "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "connectome_cache_sha256": _sha(CACHE), "connectome_source_sha256": _sha(SOURCE)}


def pinned(root: Path | None = None) -> dict:
    """The registered environment: Python 3.13, and the torch and numpy pins in requirements.txt."""
    pins = {"python": "3.13"}
    for line in ((root or ROOT) / "requirements.txt").read_text(encoding="utf-8").splitlines():
        name, _, rest = line.partition("==")
        if name.strip() in ("torch", "numpy") and rest:
            pins[name.strip()] = rest.split()[0]
    return pins


def require_pins(prov: dict) -> None:
    pins = pinned()
    bad = {}
    if not str(prov.get("python", "")).startswith(pins["python"] + "."):
        bad["python"] = (pins["python"], prov.get("python"))
    for k in ("torch", "numpy"):
        if prov.get(k) != pins.get(k):
            bad[k] = (pins.get(k), prov.get(k))
    if bad:
        raise SystemExit(f"not the pinned environment (registered, found): {bad}")


def require_formal(device: str, prov: dict, gpu: str = "RTX 5080") -> None:
    """A formal stage: CUDA on the registered GPU, the pinned environment, a clean tree, HEAD pushed."""
    if not (str(device).startswith("cuda") and torch.cuda.is_available()):
        raise SystemExit("formal stages run on CUDA only")
    if gpu not in str(prov.get("gpu")):
        raise SystemExit(f"formal stages run on the registered GPU ({gpu}), not {prov.get('gpu')}")
    require_pins(prov)
    if prov["dirty"]:
        raise SystemExit("uncommitted changes in the guarded files: commit first")
    subprocess.run(["git", "fetch", "-q", "origin"], cwd=ROOT, check=True)
    pushed = subprocess.run(["git", "merge-base", "--is-ancestor", "HEAD", f"origin/{prov['branch']}"],
                            cwd=ROOT).returncode == 0
    if not pushed:
        raise SystemExit("HEAD is not pushed: the registration and its inputs are public before the run")


def start_marker(directory: Path, stage: str, prov: dict) -> Path:
    """Exclusive: created before the stage touches its worlds; if it exists, the stage is not rerun."""
    path = Path(directory) / f"{stage}-started.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as f:
            json.dump({"stage": stage, "provenance": prov,
                       "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, f, indent=1)
    except FileExistsError:
        raise SystemExit(f"{path.name} exists: {stage} has started before and is not rerun") from None
    return path


def write_json(path: Path, doc, atomic: bool = False) -> None:
    """LF line endings on every platform; optionally written to a temporary file and moved into place."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    target = path.with_name(path.stem + ".tmp" + path.suffix) if atomic else path
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=1))
        f.write("\n")
    if atomic:
        os.replace(target, path)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class CapClock:
    """Earlier attempts' recorded seconds (the accounting's aggregate) plus this process's time since
    the clock was made."""

    def __init__(self, cap_hours: float, compute_json: Path):
        self.cap_hours, self.compute_json, self.t_start = float(cap_hours), Path(compute_json), time.perf_counter()

    def spent_hours(self) -> float:
        if not self.compute_json.exists():
            return 0.0
        return float(json.loads(self.compute_json.read_text(encoding="utf-8"))["totals"]["seconds_timed"]) / 3600

    def check(self) -> None:
        if self.spent_hours() + (time.perf_counter() - self.t_start) / 3600 > self.cap_hours:
            raise CapReached(f"the registered cap of {self.cap_hours} GPU-hours is reached")


def lower_bound(values: np.ndarray, resamples: int = 10_000, seed: int = 0) -> float:
    """One-sided 95% lower bound of the mean of per-world values: the 5th percentile of the bootstrap
    distribution over worlds."""
    values = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, values.size, size=(resamples, values.size))
    return float(np.quantile(values[idx].mean(axis=1), 0.05))


def require_same_code(commit: str, guarded: list[str], root: Path | None = None) -> None:
    """Only outputs may change after `commit`: none of the guarded paths."""
    diff = git("diff", "--name-only", commit, "HEAD", "--", *guarded, root=root)
    if diff:
        raise SystemExit(f"code or the pre-registration changed since {commit[:7]}: {diff.splitlines()[:5]}")


def require_same_env(was: dict, now: dict, keys=ENV_KEYS) -> None:
    diff = {k: (was.get(k), now.get(k)) for k in keys if was.get(k) != now.get(k)}
    if diff:
        raise SystemExit(f"the environment differs from the earlier stage's: {diff}")
