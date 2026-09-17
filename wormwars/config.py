"""All tunable numbers live here or in `configs/*.yaml`. No magic numbers in the simulation code.

Every dataclass is plain data: no behaviour, no defaults that depend on other sections. YAML files
override fields by name; an unknown field is an error, not a silently ignored typo.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "default.yaml"


@dataclass
class BrainConfig:
    """The leaky rate model and the bounds evolution must respect.

    Time is measured in world ticks: `tau = 1.0` means a neuron relaxes with a one-tick time
    constant. `substeps` brain updates are taken per tick, each of size `dt = 1 / substeps`.
    """

    substeps: int = 8
    # hard bounds, enforced by clamping after every mutation
    tau_min: float = 0.5
    tau_max: float = 20.0
    w_max: float = 3.0
    g_max: float = 2.0
    b_max: float = 2.0
    # initialisation
    init_w_scale: float = 0.2  # |W| = init_w_scale * anat / mean(anat), random sign
    init_g_scale: float = 0.05  # G = init_g_scale * anat / mean(anat), >= 0
    init_bias_std: float = 0.1
    init_tau_log_uniform: bool = True
    dale: bool = False  # one sign per presynaptic neuron
    # input
    input_gain: float = 1.0
    input_max: float = 5.0  # |I| bound, so the analytic activity bound is finite

    @property
    def dt(self) -> float:
        return 1.0 / self.substeps


@dataclass
class MutationConfig:
    w_sigma: float = 0.08
    g_sigma: float = 0.04
    tau_sigma: float = 0.15  # multiplicative, in log space
    bias_sigma: float = 0.05
    p_mutate: float = 1.0  # fraction of parameters perturbed per offspring


@dataclass
class Config:
    brain: BrainConfig = field(default_factory=BrainConfig)
    mutation: MutationConfig = field(default_factory=MutationConfig)

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> "Config":
        path = Path(path) if path is not None else DEFAULT_CONFIG
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Config":
        kwargs: dict[str, Any] = {}
        sections = {f.name: f for f in dataclasses.fields(cls)}
        unknown = set(raw) - set(sections)
        if unknown:
            raise ValueError(f"unknown config section(s): {sorted(unknown)}")
        for name, f in sections.items():
            sub = raw.get(name) or {}
            section_cls = f.type if isinstance(f.type, type) else _resolve(f)
            known = {g.name for g in dataclasses.fields(section_cls)}
            bad = set(sub) - known
            if bad:
                raise ValueError(f"unknown field(s) in config section {name!r}: {sorted(bad)}")
            kwargs[name] = section_cls(**sub)
        return cls(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _resolve(f: dataclasses.Field) -> type:
    # dataclass field types are strings under `from __future__ import annotations`
    return globals()[f.type]
