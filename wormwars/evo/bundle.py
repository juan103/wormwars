"""Run bundles: everything needed to understand, and mostly to reproduce, a run.

Exact re-simulation is only claimed under `replay_mode()`; see `docs/REPRODUCIBILITY.md`. The
bundle records enough to tell whether two results are comparable at all: configs, dataset hashes,
package versions, git commit, and the documented seed derivation.
"""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

from ..config import Config
from ..connectome.loader import DEFAULT_CACHE, Connectome

SEED_SCHEME = (
    "A run has one integer run_seed. World w of that run uses "
    "world_seed(run_seed, world_id) = splitmix64(run_seed * 2**32 + world_id), which seeds a "
    "numpy default_rng used for that world's map, hazards and spawn. Training world ids for "
    "generation g are drawn from numpy.random.default_rng([run_seed, g, 0xC0FFEE]) within "
    "[train_seed_base, train_seed_base + train_seed_span); held-out ids are the fixed range "
    "[holdout_seed_base, holdout_seed_base + holdout_worlds) and are never used for selection. "
    "Torch RNG for genome initialisation and mutation is a single generator seeded with run_seed."
)


def _git_commit() -> str | None:
    with contextlib.suppress(Exception):
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
            ).strip()
        )
    return None


def _git_dirty() -> bool | None:
    with contextlib.suppress(Exception):
        out = subprocess.check_output(
            ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, text=True
        )
        return bool(out.strip())
    return None


def _package_versions() -> dict[str, str]:
    import importlib.metadata as md

    out = {}
    for name in ("torch", "numpy", "scipy", "matplotlib", "pyyaml", "pandas", "openpyxl"):
        with contextlib.suppress(Exception):
            out[name] = md.version(name)
    return out


def file_sha256(path: str | Path) -> str | None:
    path = Path(path)
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def environment() -> dict:
    info = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "packages": _package_versions(),
        "git_commit": _git_commit(),
        "git_dirty": _git_dirty(),
    }
    if torch.cuda.is_available():
        info["gpu"] = torch.cuda.get_device_name(0)
        info["gpu_capability"] = list(torch.cuda.get_device_capability(0))
        info["gpu_arch_list"] = torch.cuda.get_arch_list()
    return info


def write_bundle(
    out_dir: str | Path,
    cfg: Config,
    con: Connectome,
    *,
    graphs: dict[str, dict] | None = None,
    extra: dict | None = None,
) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    bundle = {
        "config": cfg.to_dict(),
        "connectome": {
            "label": con.label,
            "weight_kind": con.weight_kind,
            "n_neurons": con.n,
            "source_sha256": con.meta.get("sha256"),
            "cache_path": str(DEFAULT_CACHE),
            "cache_sha256": file_sha256(DEFAULT_CACHE),
            "citation": con.meta.get("citation"),
        },
        "graphs": graphs or {},
        "seed_scheme": SEED_SCHEME,
        "environment": environment(),
        "extra": extra or {},
    }
    path = out / "bundle.json"
    path.write_text(json.dumps(bundle, indent=2, default=str), encoding="utf-8")
    return path


@contextlib.contextmanager
def replay_mode(warn: bool = True):
    """Deterministic CUDA kernels, for the one mode where exact reproduction is claimed.

    Grid splatting uses index_add_/scatter, which is nondeterministic on CUDA by default. Inside
    this context torch is asked for deterministic algorithms; outside it, expect trajectories that
    agree approximately and diverge in chaotic regimes.
    """
    import os

    prev = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    torch.use_deterministic_algorithms(True, warn_only=warn)
    try:
        yield
    finally:
        torch.use_deterministic_algorithms(False)
        if prev is None:
            os.environ.pop("CUBLAS_WORKSPACE_CONFIG", None)
        else:
            os.environ["CUBLAS_WORKSPACE_CONFIG"] = prev
