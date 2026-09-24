# Experiment 02 Screening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build everything experiment 02's 12-hour screening fraction needs, run it under a
pre-registration, and write it up, stopping before any push.

**Architecture:** Every new behaviour is an opt-in option whose default reproduces every earlier
experiment bit-for-bit: world sensing options, initial-magnitude modes, interface variants, and
evolution checkpoints and snapshots. Experiment-specific logic lives in a new package,
`wormwars/exp02/`: remap selection, scripted controllers, the run grid, probes and analysis. It is
driven by one CLI, `scripts/exp02.py`, whose subcommands produce the frozen inputs (remaps,
calibration, diagnostics, pilot), run the grid in balanced resumable batches, run the probes, and
write the report.

**Tech Stack:** Python 3.13, PyTorch 2.12 (CUDA on an RTX 5080), NumPy, PyYAML, pytest. Run
Python as `py -3.13`.

**Spec:** `experiments/02-screening/DESIGN.md` (v2, commit `1db64e1`).

## Global Constraints

- Defaults must reproduce every earlier experiment exactly.
  `tests/test_direction.py::test_legacy_mode_reproduces_a_published_experiment_01_score_exactly`
  must keep passing. Add no floating-point reordering to default code paths.
- Every new dataclass config field must also be added to `configs/default.yaml` with the same
  value (`tests/test_calibration.py::test_default_yaml_matches_the_dataclass_defaults`).
- `np.load` always takes `allow_pickle=False` (`tests/test_publication_hygiene.py`).
- No connectome-derived arrays are committed: no adjacency, edge lists, degree sequences or
  weight multisets (`test_no_committed_file_contains_graph_structure`). The remap table stores
  per-pair summary features only, never edges.
- N2 never touches tuning. Tuning uses scripted controllers, or discarded pilots on shuffles SH101
  onwards. SH1-SH6 are reserved for the main runs.
- Experiment 02 settings: 32 substeps; 40 generations; population 32; 8 training worlds; 64
  held-out worlds; 400 ticks; target drive |forward| 0.5 and |turn| 0.4; calibration tolerance 2%.
- Budget: 12 GPU-hours in total, stopping only at batch boundaries.
- Never `git push`. Commit locally only.
- Commit messages end with
  `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`, and carry no session
  trailer, by the user's rule.

## Review Focus

1. **Old artefacts after the changes.** A 01b champion file (no manifest fields, no magnitude
   fields) must still load and replay identically. Test in Task 5.
2. **Interrupted runs.** Restarting `run` mid-schedule must skip completed runs, never reuse or
   shift a seed, and never duplicate a record. Test in Task 9.
3. **A remap naming a missing neuron, or one already used by another channel or the read-out,**
   must fail loudly, never silently. Test in Task 3.
4. **Budget stop.** Hitting the time cap must stop only between whole batches, so no cell loses
   runs selectively. Test in Task 9.
5. **A swarm that dies early.** Pellet share, behaviour statistics and normalised scores must not
   crash or produce NaN when all weys are dead, or when a scripted reference scores zero on a
   world. Tests in Tasks 6 and 11.

---

### Task 1: World sensing options and measurement accumulators

**Files:**
- Modify: `wormwars/config.py` (WorldConfig)
- Modify: `configs/default.yaml` (world section)
- Modify: `wormwars/world.py` (`__init__`, `tick`, `_sensor_signals`, `_eat`, new `_probe_food`)
- Test: `tests/test_exp02_world.py`

**Interfaces:**
- Produces: `WorldConfig.food_sensing: str` (`"stereo"` | `"mono"`),
  `WorldConfig.food_probe: str` (`"real"` | `"constant"` | `"mirrored"`); `World.last_forward`,
  `World.last_turn` (`[worlds, swarms, weys]` tensors, set every tick); `World.pellet_eaten`
  (`[worlds]` float64, cumulative); constants `FOOD_SENSING`, `FOOD_PROBES` in `wormwars.world`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_exp02_world.py
"""World options for experiment 02: mono food sensing, food probes, and pure measurements."""

from __future__ import annotations

import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.fields import sample_bilinear
from wormwars.interface import load_interface
from wormwars.world import N_POINTS, P_FRONT_C, P_FRONT_L, P_FRONT_R, World


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def build(parts, cfg=None, n=4, seed=0):
    con, iface, spec = parts
    cfg = cfg or Config()
    genome = Genome.random(spec, cfg.brain, n, generator=torch.Generator().manual_seed(seed))
    return World(cfg, iface, Brain(genome), torch.arange(n).reshape(n, 1), run_seed=3)


def signals_now(w):
    pts = w.sample_points()
    sampled = sample_bilinear(w.fields, pts).reshape(
        w.n_worlds, w.ch.n, w.n_swarms, w.n_weys, N_POINTS
    )
    return sampled, w._sensor_signals(sampled)


def test_defaults_are_stereo_and_real():
    c = Config()
    assert c.world.food_sensing == "stereo" and c.world.food_probe == "real"


def test_mono_copies_the_head_sample_to_both_sides(parts):
    cfg = Config()
    cfg.world.food_sensing = "mono"
    w = build(parts, cfg)
    for _ in range(5):
        w.tick()
    sampled, sig = signals_now(w)
    food = sampled[:, w.ch.FOOD] + sampled[:, w.ch.PELLET]
    expect = food[..., P_FRONT_C] * cfg.world.sense_scale_food
    torch.testing.assert_close(sig["food_left"], expect)
    torch.testing.assert_close(sig["food_right"], expect)


def test_stereo_default_reads_left_and_right(parts):
    w = build(parts)
    for _ in range(5):
        w.tick()
    sampled, sig = signals_now(w)
    food = sampled[:, w.ch.FOOD] + sampled[:, w.ch.PELLET]
    sf = w.cfg.world.sense_scale_food
    torch.testing.assert_close(sig["food_left"], food[..., P_FRONT_L] * sf)
    torch.testing.assert_close(sig["food_right"], food[..., P_FRONT_R] * sf)


def test_constant_probe_carries_no_spatial_information(parts):
    cfg = Config()
    cfg.world.food_probe = "constant"
    w = build(parts, cfg)
    for _ in range(5):
        w.tick()
    _, sig = signals_now(w)
    left = sig["food_left"]
    # one value per world, identical for every wey and both sides
    assert torch.allclose(left, left[:, :1, :1].expand_as(left))
    torch.testing.assert_close(sig["food_left"], sig["food_right"])


def test_mirrored_probe_reads_the_point_reflection(parts):
    cfg = Config()
    cfg.world.food_probe = "mirrored"
    w = build(parts, cfg)
    for _ in range(5):
        w.tick()
    pts = w.sample_points()
    w._food_sample = w._probe_food(pts)
    sampled, sig = signals_now(w)
    x, y = pts[..., 0], pts[..., 1]
    mirrored = torch.stack((w.W - 1 - x, w.H - 1 - y), dim=-1)
    s = sample_bilinear(w.fields[:, w.ch.FOOD : w.ch.PELLET + 1].contiguous(), mirrored)
    food = (s[:, 0] + s[:, 1]).reshape(w.n_worlds, w.n_swarms, w.n_weys, N_POINTS)
    sf = cfg.world.sense_scale_food
    torch.testing.assert_close(sig["food_left"], food[..., P_FRONT_L] * sf)


def test_unknown_options_are_rejected(parts):
    for field, bad in (("food_sensing", "trinocular"), ("food_probe", "psychic")):
        cfg = Config()
        setattr(cfg.world, field, bad)
        with pytest.raises(ValueError, match=field):
            build(parts, cfg)


def test_intake_splits_into_plant_food_and_pellets(parts):
    w = build(parts)
    food0 = w.fields[:, w.ch.FOOD].double().sum(dim=(1, 2))
    for _ in range(300):
        w.tick()
    plant = food0 - w.fields[:, w.ch.FOOD].double().sum(dim=(1, 2))
    total = w.energy_eaten.sum(dim=1)
    assert (w.pellet_eaten >= -1e-6).all()
    torch.testing.assert_close(total, plant + w.pellet_eaten, rtol=1e-4, atol=1e-3)


def test_motor_commands_are_recorded_each_tick(parts):
    w = build(parts)
    w.tick()
    assert w.last_forward.shape == (w.n_worlds, w.n_swarms, w.n_weys)
    assert w.last_turn.shape == w.last_forward.shape
    assert w.last_forward.abs().max() <= 1.0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3.13 -m pytest tests/test_exp02_world.py -q`
Expected: FAIL (`AttributeError` on `food_sensing`, `_probe_food` and `pellet_eaten`).

- [ ] **Step 3: Add the config fields**

In `wormwars/config.py`, at the end of `WorldConfig`, after `crowd_blur`:

```python
    # --- experiment 02 options; the defaults reproduce every earlier experiment ---
    # "stereo": food sampled left and right of the head. "mono": one sample at the head's front
    # centre, copied to both sides, so direction can only come from change over time.
    food_sensing: str = "stereo"
    # Evaluation probes only, never used for selection. "real": the food field. "constant": each
    # world's mean food level at tick 0, identical everywhere. "mirrored": the food field sampled
    # at the point reflection of the true sample point (same distribution, unrelated location).
    food_probe: str = "real"
```

In `configs/default.yaml`, at the end of the `world:` section:

```yaml
  food_sensing: stereo
  food_probe: real
```

- [ ] **Step 4: Implement the world changes**

In `wormwars/world.py`, next to the `P_*` constants:

```python
FOOD_SENSING = ("stereo", "mono")
FOOD_PROBES = ("real", "constant", "mirrored")
```

In `World.__init__`, directly after `wcfg = cfg.world`:

```python
        if wcfg.food_sensing not in FOOD_SENSING:
            raise ValueError(f"world.food_sensing must be one of {FOOD_SENSING}, got {wcfg.food_sensing!r}")
        if wcfg.food_probe not in FOOD_PROBES:
            raise ValueError(f"world.food_probe must be one of {FOOD_PROBES}, got {wcfg.food_probe!r}")
```

In `World.__init__`, directly after `self.energy_from_biting = zs()`:

```python
        # plant food versus corpse pellets, per world: pure measurement
        self.pellet_eaten = torch.zeros(self.n_worlds, dtype=torch.float64, device=self.device)
        self.last_forward: Tensor | None = None
        self.last_turn: Tensor | None = None
        self._food_sample: Tensor | None = None
```

In `World.__init__`, directly after `self._build_maps()`:

```python
        # the "constant" probe's value: each world's mean food level at tick 0
        self._food_constant = self.fields[:, self.ch.FOOD].mean(dim=(1, 2))
```

Add the method `_probe_food`, just before `_sensor_signals`:

```python
    def _probe_food(self, pts: Tensor) -> Tensor:
        """Food + pellet sampled at the point reflection of every sample point. Probe only."""
        x, y = pts[..., 0], pts[..., 1]
        mirrored = torch.stack((self.W - 1 - x, self.H - 1 - y), dim=-1)
        ch = self.ch
        s = sample_bilinear(self.fields[:, ch.FOOD : ch.PELLET + 1].contiguous(), mirrored)
        return (s[:, 0] + s[:, 1]).reshape(self.n_worlds, self.n_swarms, self.n_weys, N_POINTS)
```

In `_sensor_signals`, replace `food = sampled[:, ch.FOOD] + sampled[:, ch.PELLET]` with:

```python
        if wcfg.food_probe == "mirrored":
            food = self._food_sample
        elif wcfg.food_probe == "constant":
            food = self._food_constant.view(-1, 1, 1, 1).expand_as(sampled[:, ch.FOOD])
        else:
            food = sampled[:, ch.FOOD] + sampled[:, ch.PELLET]
        if wcfg.food_sensing == "mono":
            food_l = food_r = food[..., P_FRONT_C]
        else:
            food_l, food_r = food[..., P_FRONT_L], food[..., P_FRONT_R]
```

and in the returned dict, replace the two food entries with:

```python
            "food_left": food_l * sf,
            "food_right": food_r * sf,
```

In `tick`, directly after `signals = self._sensor_signals(sampled)` is computed (and before it),
set the probe sample. The lines become:

```python
        self._food_sample = self._probe_food(pts) if wcfg.food_probe == "mirrored" else None
        signals = self._sensor_signals(sampled)
```

In `tick`, directly after `forward, turn, pump = self._read_motors(v_world)`:

```python
        self.last_forward, self.last_turn = forward, turn
```

In `_eat`, at the end:

```python
        self.pellet_eaten += (taken * (1.0 - share)).sum(dim=(1, 2)).double()
```

- [ ] **Step 5: Run the new tests and the regression guards**

Run: `py -3.13 -m pytest tests/test_exp02_world.py tests/test_world.py tests/test_direction.py tests/test_calibration.py -q`
Expected: all PASS, including the CUDA reproduction test (defaults unchanged).

- [ ] **Step 6: Commit**

```bash
git add wormwars/config.py configs/default.yaml wormwars/world.py tests/test_exp02_world.py
git commit -m "World options for experiment 02: mono food sensing, food probes, intake split"
```

---

### Task 2: Initial-magnitude modes

**Files:**
- Modify: `wormwars/config.py` (BrainConfig)
- Modify: `configs/default.yaml` (brain section)
- Modify: `wormwars/brain.py` (`Genome.random`, new `_apply_magnitude_mode`, `MAGNITUDE_MODES`)
- Test: `tests/test_exp02_magnitudes.py`

**Interfaces:**
- Produces: `BrainConfig.init_chem_magnitude: str`, `BrainConfig.init_gap_magnitude: str`
  (`"anatomical"` | `"uniform"` | `"permuted"`), `BrainConfig.init_permutation_seed: int`;
  `wormwars.brain.MAGNITUDE_MODES`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_exp02_magnitudes.py
"""Initial magnitude modes: anatomical (default, unchanged), uniform, and permuted in-mask."""

from __future__ import annotations

import dataclasses

import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import BrainConfig
from wormwars.connectome import load_connectome


@pytest.fixture(scope="module")
def spec():
    return BrainSpec.from_connectome(load_connectome())


def gen(spec, **kw):
    cfg = dataclasses.replace(BrainConfig(), **kw)
    return Genome.random(spec, cfg, 2, generator=torch.Generator().manual_seed(11))


def test_anatomical_default_is_the_original_formula(spec):
    g = gen(spec)
    cfg = BrainConfig()
    expect = cfg.init_w_scale * spec.chem_anat / spec.chem_anat.mean()
    torch.testing.assert_close(g.w.abs()[0], expect.clamp(max=cfg.w_max), rtol=0, atol=0)


def test_uniform_sets_every_magnitude_to_the_scale(spec):
    g = gen(spec, init_chem_magnitude="uniform", init_gap_magnitude="uniform")
    cfg = BrainConfig()
    assert torch.allclose(g.w.abs(), torch.full_like(g.w, cfg.init_w_scale))
    assert torch.allclose(g.g, torch.full_like(g.g, cfg.init_g_scale))


def test_permuted_keeps_the_multiset_and_the_signs(spec):
    a = gen(spec)
    p = gen(spec, init_chem_magnitude="permuted", init_gap_magnitude="permuted")
    assert torch.equal(torch.sort(a.w.abs()[0]).values, torch.sort(p.w.abs()[0]).values)
    assert torch.equal(torch.sort(a.g[0]).values, torch.sort(p.g[0]).values)
    assert torch.equal(torch.sign(a.w), torch.sign(p.w)), "signs must stay paired"
    assert not torch.equal(a.w.abs(), p.w.abs()), "positions must actually move"


def test_permutation_seed_changes_the_permutation(spec):
    p0 = gen(spec, init_chem_magnitude="permuted", init_permutation_seed=0)
    p1 = gen(spec, init_chem_magnitude="permuted", init_permutation_seed=1)
    assert not torch.equal(p0.w, p1.w)


def test_chem_and_gap_modes_are_independent(spec):
    a = gen(spec)
    c = gen(spec, init_chem_magnitude="uniform")
    assert torch.equal(a.g, c.g) and not torch.equal(a.w.abs(), c.w.abs())


def test_unknown_mode_is_an_error(spec):
    with pytest.raises(ValueError, match="magnitude"):
        gen(spec, init_chem_magnitude="vibes")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3.13 -m pytest tests/test_exp02_magnitudes.py -q`
Expected: FAIL (`TypeError`: unexpected keyword `init_chem_magnitude`).

- [ ] **Step 3: Add the config fields**

In `wormwars/config.py`, in `BrainConfig`, directly after `init_tau_log_uniform`:

```python
    # Initial |W| and G magnitudes: "anatomical" (default: proportional to the anatomical weight),
    # "uniform" (every edge at the scale), or "permuted" (the anatomical magnitudes shuffled within
    # the graph's own mask, seeded by init_permutation_seed). Experiment 02 uses the last two to
    # ask whether N2's edge comes from its topology or from its synapse strengths.
    init_chem_magnitude: str = "anatomical"
    init_gap_magnitude: str = "anatomical"
    init_permutation_seed: int = 0
```

In `configs/default.yaml`, in the `brain:` section after `init_tau_log_uniform: true`:

```yaml
  init_chem_magnitude: anatomical
  init_gap_magnitude: anatomical
  init_permutation_seed: 0
```

- [ ] **Step 4: Implement the modes in `wormwars/brain.py`**

Add at module level, after the imports:

```python
MAGNITUDE_MODES = ("anatomical", "uniform", "permuted")


def _apply_magnitude_mode(mag: Tensor, mode: str, scale: float, seed: int, salt: int) -> Tensor:
    """Transform anatomical initial magnitudes. "anatomical" returns `mag` itself, untouched, so
    the default path performs exactly the arithmetic it always did."""
    if mode == "anatomical":
        return mag
    if mode == "uniform":
        return torch.full_like(mag, scale)
    if mode == "permuted":
        # a private CPU generator: must not consume the genome's generator, so signs, biases and
        # time constants stay paired with the anatomical draw
        gen = torch.Generator().manual_seed(int(seed) * 2 + salt)
        perm = torch.randperm(mag.numel(), generator=gen).to(mag.device)
        return mag[perm]
    raise ValueError(f"init magnitude mode must be one of {MAGNITUDE_MODES}, got {mode!r}")
```

In `Genome.random`, replace

```python
        w_mag = cfg.init_w_scale * spec.chem_anat / spec.chem_anat.mean()
```

with

```python
        w_mag = cfg.init_w_scale * spec.chem_anat / spec.chem_anat.mean()
        w_mag = _apply_magnitude_mode(
            w_mag, cfg.init_chem_magnitude, cfg.init_w_scale, cfg.init_permutation_seed, 0
        )
```

and replace

```python
        g = cfg.init_g_scale * (spec.gap_anat / spec.gap_anat.mean()).unsqueeze(0).expand(S, -1)
```

with

```python
        g_mag = cfg.init_g_scale * (spec.gap_anat / spec.gap_anat.mean())
        g_mag = _apply_magnitude_mode(
            g_mag, cfg.init_gap_magnitude, cfg.init_g_scale, cfg.init_permutation_seed, 1
        )
        g = g_mag.unsqueeze(0).expand(S, -1)
```

- [ ] **Step 5: Run the tests and the regression guards**

Run: `py -3.13 -m pytest tests/test_exp02_magnitudes.py tests/test_brain.py tests/test_direction.py tests/test_calibration.py -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add wormwars/config.py configs/default.yaml wormwars/brain.py tests/test_exp02_magnitudes.py
git commit -m "Initial-magnitude modes: anatomical (unchanged), uniform, permuted within the mask"
```

---

### Task 3: Interface variants, plus two documentation fixes

**Files:**
- Modify: `wormwars/interface.py` (split out `interface_from_spec`; add `remapped_spec`, `negated_spec`, `interface_hash`)
- Modify: `configs/interface.yaml` (header comment only)
- Modify: `wormwars/connectome/graphs.py` (module docstring only)
- Test: `tests/test_exp02_interface.py`

**Interfaces:**
- Produces: `interface_from_spec(con, spec: dict) -> Interface`;
  `remapped_spec(spec: dict, prefix: str, pairs: list[tuple[str, str]]) -> dict`;
  `negated_spec(spec: dict, prefix: str) -> dict`; `interface_hash(iface: Interface) -> str`;
  `load_interface_spec(path=None) -> dict`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_exp02_interface.py
"""Interface variants: remapping one signal's neurons, negating it, and hashing the result."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.connectome import load_connectome
from wormwars.connectome.loader import ConnectomeError
from wormwars.interface import (
    interface_from_spec,
    interface_hash,
    load_interface,
    load_interface_spec,
    negated_spec,
    remapped_spec,
)


@pytest.fixture(scope="module")
def con():
    return load_connectome()


def test_from_spec_matches_load_interface(con):
    a = load_interface(con)
    b = interface_from_spec(con, load_interface_spec())
    assert interface_hash(a) == interface_hash(b)


def test_remap_moves_only_the_food_neurons(con):
    spec = load_interface_spec()
    new = remapped_spec(spec, "food", [("ASIL", "ASIR"), ("ASJL", "ASJR"), ("ASGL", "ASGR")])
    a, b = load_interface(con), interface_from_spec(con, new)
    names = con.names
    fl = [names[i] for s, i in zip(b.signal_names, b.sensor_neuron) if s == "food_left"]
    fr = [names[i] for s, i in zip(b.signal_names, b.sensor_neuron) if s == "food_right"]
    assert fl == ["ASIL", "ASJL", "ASGL"] and fr == ["ASIR", "ASJR", "ASGR"]
    keep = [k for k, s in enumerate(a.signal_names) if not s.startswith("food_")]
    assert np.array_equal(a.sensor_neuron[keep], b.sensor_neuron[keep])
    assert np.array_equal(a.sensor_gain, b.sensor_gain)
    for part in ("forward_plus", "forward_minus", "turn_plus", "turn_minus", "pump_neurons"):
        assert np.array_equal(getattr(a, part), getattr(b, part))
    assert interface_hash(a) != interface_hash(b)
    assert spec["sensors"][0]["neurons"] == ["AWAL"], "the input spec must not be mutated"


def test_remap_refuses_neurons_already_in_use(con):
    spec = load_interface_spec()
    for pairs in ([("ASKL", "ASKR"), ("ASIL", "ASIR"), ("ASJL", "ASJR")],   # pheromone sensor
                  [("AVAL", "AVAR"), ("ASIL", "ASIR"), ("ASJL", "ASJR")]):  # motor read-out
        with pytest.raises(ValueError, match="already"):
            remapped_spec(spec, "food", pairs)


def test_remap_refuses_the_wrong_number_of_pairs():
    with pytest.raises(ValueError, match="pairs"):
        remapped_spec(load_interface_spec(), "food", [("ASIL", "ASIR")])


def test_remap_to_a_missing_neuron_fails_loudly(con):
    new = remapped_spec(load_interface_spec(), "food",
                        [("NOPEL", "NOPER"), ("ASIL", "ASIR"), ("ASJL", "ASJR")])
    with pytest.raises(ConnectomeError, match="NOPE"):
        interface_from_spec(con, new)


def test_negation_flips_only_that_signal(con):
    a = load_interface(con)
    b = interface_from_spec(con, negated_spec(load_interface_spec(), "food"))
    food = np.array([s.startswith("food_") for s in a.signal_names])
    assert np.array_equal(b.sensor_gain[food], -a.sensor_gain[food])
    assert np.array_equal(b.sensor_gain[~food], a.sensor_gain[~food])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3.13 -m pytest tests/test_exp02_interface.py -q`
Expected: FAIL (`ImportError`).

- [ ] **Step 3: Implement in `wormwars/interface.py`**

Add the imports `import copy`, `import hashlib` and `import json`. Then replace the whole
`load_interface` function with:

```python
def load_interface_spec(path: str | Path | None = None) -> dict:
    """The raw interface specification, as written in the YAML file."""
    path = Path(path) if path is not None else DEFAULT_INTERFACE
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_interface(con: Connectome, path: str | Path | None = None) -> Interface:
    return interface_from_spec(con, load_interface_spec(path))


def interface_from_spec(con: Connectome, spec: dict) -> Interface:
    """Resolve a raw specification (as loaded from YAML, or built by `remapped_spec`)."""
    signal_names: list[str] = []
    sensor_neuron: list[int] = []
    sensor_gain: list[float] = []
    for i, ch in enumerate(spec["sensors"]):
        signal = ch["signal"]
        if signal not in KNOWN_SIGNALS:
            raise ConnectomeError(
                f"sensors[{i}]: unknown signal {signal!r}. Known signals: {list(KNOWN_SIGNALS)}"
            )
        idx = _resolve(con, ch["neurons"], f"sensors[{i}] ({signal})")
        for j in idx:
            signal_names.append(signal)
            sensor_neuron.append(int(j))
            sensor_gain.append(float(ch.get("gain", 1.0)))

    motors = spec["motors"]
    pump = motors["pump"]
    if pump.get("squash", "sigmoid") != "sigmoid":
        raise ConnectomeError("only squash: sigmoid is implemented for the pump read-out")
    sampling = spec["sampling"]

    return Interface(
        signal_names=tuple(signal_names),
        sensor_neuron=np.array(sensor_neuron, dtype=np.int64),
        sensor_gain=np.array(sensor_gain, dtype=np.float32),
        forward_plus=_resolve(con, motors["forward"]["plus"], "motors.forward.plus"),
        forward_minus=_resolve(con, motors["forward"]["minus"], "motors.forward.minus"),
        turn_plus=_resolve(con, motors["turn"]["plus"], "motors.turn.plus"),
        turn_minus=_resolve(con, motors["turn"]["minus"], "motors.turn.minus"),
        pump_neurons=_resolve(con, pump["neurons"], "motors.pump.neurons"),
        pump_gain=float(pump.get("gain", 4.0)),
        forward_offset=float(sampling["forward_offset"]),
        lateral_offset=float(sampling["lateral_offset"]),
        raw=spec,
    )


def _motor_names(spec: dict) -> set[str]:
    m = spec["motors"]
    return set(m["forward"]["plus"] + m["forward"]["minus"] + m["turn"]["plus"]
               + m["turn"]["minus"] + m["pump"]["neurons"])


def remapped_spec(spec: dict, prefix: str, pairs: list[tuple[str, str]]) -> dict:
    """A copy of `spec` in which the k-th `<prefix>_left`/`_right` entries receive pairs[k].

    Gains, order, every other channel and the motor read-out are untouched. A neuron already used
    by another channel or by the read-out is refused, as is the wrong number of pairs.
    """
    out = copy.deepcopy(spec)
    lefts = [s for s in out["sensors"] if s["signal"] == f"{prefix}_left"]
    rights = [s for s in out["sensors"] if s["signal"] == f"{prefix}_right"]
    if len(lefts) != len(pairs) or len(rights) != len(pairs):
        raise ValueError(
            f"{prefix!r} has {len(lefts)} left and {len(rights)} right entries; got {len(pairs)} pairs"
        )
    new = [n for p in pairs for n in p]
    if len(set(new)) != len(new):
        raise ValueError(f"remap pairs repeat a neuron: {new}")
    elsewhere = {n for s in out["sensors"] if not s["signal"].startswith(prefix + "_")
                 for n in s["neurons"]}
    clash = set(new) & (elsewhere | _motor_names(out))
    if clash:
        raise ValueError(f"remap neurons {sorted(clash)} are already used by the interface")
    for entry, (left, _) in zip(lefts, pairs):
        entry["neurons"] = [left]
    for entry, (_, right) in zip(rights, pairs):
        entry["neurons"] = [right]
    return out


def negated_spec(spec: dict, prefix: str) -> dict:
    """A copy of `spec` with every `<prefix>_*` channel's gain multiplied by -1."""
    out = copy.deepcopy(spec)
    for s in out["sensors"]:
        if s["signal"].startswith(prefix + "_"):
            s["gain"] = -float(s.get("gain", 1.0))
    return out


def interface_hash(iface: Interface) -> str:
    """sha256 of everything that decides what reaches which neuron and what is read out."""
    payload = {
        "signals": list(iface.signal_names),
        "sensor_neuron": [int(i) for i in iface.sensor_neuron],
        "sensor_gain": [float(g) for g in iface.sensor_gain],
        "forward_plus": [int(i) for i in iface.forward_plus],
        "forward_minus": [int(i) for i in iface.forward_minus],
        "turn_plus": [int(i) for i in iface.turn_plus],
        "turn_minus": [int(i) for i in iface.turn_minus],
        "pump_neurons": [int(i) for i in iface.pump_neurons],
        "pump_gain": float(iface.pump_gain),
        "offsets": [float(iface.forward_offset), float(iface.lateral_offset)],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
```

- [ ] **Step 4: Fix the two documentation errors**

In `configs/interface.yaml`, replace the line

```yaml
# Read-out and injection both use the neuron's bounded output tanh(v), not the raw voltage.
```

with

```yaml
# Injection adds each signal, times its gain, as an external current (clipped to +-input_max).
# The motor read-out uses the neuron's bounded output tanh(v), not the raw voltage.
```

In `wormwars/connectome/graphs.py`'s module docstring, replace

```
  symmetric. Anatomical weights are carried along with the edges, so the weight *distribution* is
  identical to N2 and only the topology moves.
```

with

```
  symmetric. The anatomical weights are permuted onto the shuffled edges: the overall weight
  distribution is identical to N2's, but no edge or neuron keeps its own anatomical strength.
```

- [ ] **Step 5: Run the tests**

Run: `py -3.13 -m pytest tests/test_exp02_interface.py tests/test_world.py tests/test_calibration.py -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add wormwars/interface.py configs/interface.yaml wormwars/connectome/graphs.py tests/test_exp02_interface.py
git commit -m "Interface variants (remap, negate, hash); fix two documentation errors"
```

---

### Task 4: Remap selection by a fixed rule

**Files:**
- Create: `wormwars/exp02/__init__.py` (empty docstring module)
- Create: `wormwars/exp02/remaps.py`
- Test: `tests/test_exp02_remaps.py`

**Interfaces:**
- Consumes: `load_interface` (Task 3).
- Produces: `FEATURES: tuple[str, ...]`; `hops_to(adj, source, targets, limit=99) -> int`;
  `candidate_pairs(con, iface) -> list[str]`; `motivated_pairs(con, iface, prefix="food") -> list[str]`;
  `pair_features(con, iface, base) -> dict[str, float]`;
  `choose_matched(con, iface, n_sets=2, prefix="food") -> list[list[str]]`;
  `choose_shortcut(con, iface, exclude, k=3) -> list[str]`;
  `remap_record(con, iface) -> dict` (JSON-ready: sets as neuron-name pairs, plus per-pair feature
  table and triple distances; no edges).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_exp02_remaps.py
"""Remap selection: matched to the food neurons on degree and routing, by a fixed rule."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.connectome import load_connectome
from wormwars.exp02 import remaps
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con)


def test_hops_follow_the_direction_of_the_synapse():
    adj = np.zeros((3, 3), dtype=bool)
    adj[0, 1] = adj[1, 2] = True  # 0 -> 1 -> 2
    assert remaps.hops_to(adj, 0, {2}) == 2
    assert remaps.hops_to(adj, 2, {0}) == 99


def test_candidates_are_bilateral_sensory_pairs_outside_the_interface(parts):
    con, iface = parts
    cands = remaps.candidate_pairs(con, iface)
    mapped = {con.names[i] for i in iface.mapped_neurons}
    assert cands == sorted(cands) and len(cands) >= 9
    for base in cands:
        for side in "LR":
            n = base + side
            assert n in con.index_of and n not in mapped
            assert con.classes[con.index(n)] == "sensory"


def test_motivated_pairs_are_the_food_neurons(parts):
    assert remaps.motivated_pairs(*parts) == ["AWA", "AWC", "ASE"]


def test_matched_sets_are_disjoint_triples_and_deterministic(parts):
    con, iface = parts
    a = remaps.choose_matched(con, iface)
    b = remaps.choose_matched(con, iface)
    assert a == b and len(a) == 2
    assert all(len(s) == 3 for s in a)
    assert not set(a[0]) & set(a[1])


def test_shortcut_pairs_have_more_direct_read_out_weight(parts):
    con, iface = parts
    matched = remaps.choose_matched(con, iface)
    short = remaps.choose_shortcut(con, iface, exclude={p for s in matched for p in s})
    dw = lambda b: remaps.pair_features(con, iface, b)["direct_weight"]  # noqa: E731
    assert min(dw(b) for b in short) > max(dw(b) for s in matched for b in s)


def test_record_is_json_ready_and_carries_no_edges(parts):
    import json

    rec = remaps.remap_record(*parts)
    text = json.dumps(rec)
    assert set(rec["sets"]) == {"M0", "R1", "R2", "MS"}
    assert rec["sets"]["M0"] == [["AWAL", "AWAR"], ["AWCL", "AWCR"], ["ASEL", "ASER"]]
    assert "chem" not in text.lower().replace("chem_in", "").replace("chem_out", "")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3.13 -m pytest tests/test_exp02_remaps.py -q`
Expected: FAIL (`ModuleNotFoundError: wormwars.exp02`).

- [ ] **Step 3: Implement `wormwars/exp02/__init__.py` and `wormwars/exp02/remaps.py`**

```python
# wormwars/exp02/__init__.py
"""Experiment 02: the screening fraction. See experiments/02-screening/DESIGN.md."""
```

```python
# wormwars/exp02/remaps.py
"""Choosing the wrong food mappings by a fixed rule, before any fitness is measured.

A remap moves the food signal from AWA/AWC/ASE to three other bilateral sensory pairs outside the
interface. Matched remaps minimise the distance to the food neurons on six features: chemical out-
and in-degree, gap degree, hop distance to the forward and to the turn read-out (in the direction
signal flows: chemical pre -> post, gap both ways), and summed anatomical weight of direct edges
into the read-out. Each feature is scaled by its standard deviation over the candidate pool. The
two best disjoint triples are R1 and R2. The shortcut remap MS is the three pairs with the most
direct read-out weight. Only per-pair summaries leave this module, never edges.
"""

from __future__ import annotations

import itertools

import numpy as np

FEATURES = ("chem_out", "chem_in", "gap", "hops_forward", "hops_turn", "direct_weight")


def hops_to(adj: np.ndarray, source: int, targets: set[int], limit: int = 99) -> int:
    """Shortest path length from `source` to any of `targets` along `adj[u, v]` (u -> v)."""
    if source in targets:
        return 0
    seen, frontier, d = {source}, [source], 0
    while frontier:
        d += 1
        nxt = []
        for u in frontier:
            for v in np.flatnonzero(adj[u]):
                v = int(v)
                if v in targets:
                    return d
                if v not in seen:
                    seen.add(v)
                    nxt.append(v)
        frontier = nxt
    return limit


def _pair(con, base: str) -> tuple[int, int]:
    return con.index(base + "L"), con.index(base + "R")


def candidate_pairs(con, iface) -> list[str]:
    mapped = set(iface.mapped_neurons)
    out = set()
    for i, n in enumerate(con.names):
        if con.classes[i] != "sensory" or not n.endswith("L"):
            continue
        r = n[:-1] + "R"
        if r not in con.index_of:
            continue
        if i in mapped or con.index(r) in mapped:
            continue
        out.add(n[:-1])
    return sorted(out)


def motivated_pairs(con, iface, prefix: str = "food") -> list[str]:
    left = [con.names[i] for s, i in zip(iface.signal_names, iface.sensor_neuron)
            if s == f"{prefix}_left"]
    return [n[:-1] for n in left]


def _readout(iface) -> tuple[set[int], set[int]]:
    fwd = {int(i) for i in np.concatenate([iface.forward_plus, iface.forward_minus])}
    turn = {int(i) for i in np.concatenate([iface.turn_plus, iface.turn_minus])}
    return fwd, turn


def pair_features(con, iface, base: str) -> dict[str, float]:
    chem, gap = con.chem > 0, con.gap > 0
    adj = chem | gap
    fwd, turn = _readout(iface)
    read = sorted(fwd | turn)
    rows = []
    for i in _pair(con, base):
        rows.append({
            "chem_out": float(chem[i].sum()),
            "chem_in": float(chem[:, i].sum()),
            "gap": float(gap[i].sum()),
            "hops_forward": float(hops_to(adj, i, fwd)),
            "hops_turn": float(hops_to(adj, i, turn)),
            "direct_weight": float(con.chem[i, read].sum() + con.gap[i, read].sum()),
        })
    return {f: float(np.mean([r[f] for r in rows])) for f in FEATURES}


def _table(con, iface, bases):
    return {b: pair_features(con, iface, b) for b in bases}


def _vec(feats: dict[str, dict], triple) -> np.ndarray:
    return np.array([[feats[b][f] for f in FEATURES] for b in triple]).mean(axis=0)


def _scales(feats: dict[str, dict], bases) -> np.ndarray:
    m = np.array([[feats[b][f] for f in FEATURES] for b in bases])
    s = m.std(axis=0)
    return np.where(s > 0, s, 1.0)


def _ranked_triples(con, iface, prefix="food"):
    cands = candidate_pairs(con, iface)
    target = motivated_pairs(con, iface, prefix)
    feats = _table(con, iface, cands + target)
    scale = _scales(feats, cands)
    t = _vec(feats, target)
    scored = [(float(np.abs((_vec(feats, tr) - t) / scale).sum()), tr)
              for tr in itertools.combinations(cands, 3)]
    scored.sort()
    return scored, feats


def choose_matched(con, iface, n_sets: int = 2, prefix: str = "food") -> list[list[str]]:
    scored, _ = _ranked_triples(con, iface, prefix)
    chosen: list[list[str]] = []
    for _, tr in scored:
        if all(not set(tr) & set(c) for c in chosen):
            chosen.append(list(tr))
            if len(chosen) == n_sets:
                break
    return chosen


def choose_shortcut(con, iface, exclude: set[str], k: int = 3) -> list[str]:
    cands = [b for b in candidate_pairs(con, iface) if b not in exclude]
    ranked = sorted(cands, key=lambda b: (-pair_features(con, iface, b)["direct_weight"], b))
    return ranked[:k]


def remap_record(con, iface, prefix: str = "food") -> dict:
    scored, feats = _ranked_triples(con, iface, prefix)
    dist = {tuple(tr): d for d, tr in scored}
    r1, r2 = choose_matched(con, iface, 2, prefix)
    ms = choose_shortcut(con, iface, exclude=set(r1) | set(r2))
    m0 = motivated_pairs(con, iface, prefix)
    as_pairs = lambda bases: [[b + "L", b + "R"] for b in bases]  # noqa: E731
    return {
        "rule": __doc__.strip().splitlines()[0],
        "features": list(FEATURES),
        "sets": {"M0": as_pairs(m0), "R1": as_pairs(r1), "R2": as_pairs(r2), "MS": as_pairs(ms)},
        "distance_to_M0": {"R1": dist[tuple(r1)], "R2": dist[tuple(r2)]},
        "pair_features": {b: feats.get(b) or pair_features(con, iface, b)
                          for b in m0 + r1 + r2 + ms},
    }
```

- [ ] **Step 4: Run the tests**

Run: `py -3.13 -m pytest tests/test_exp02_remaps.py -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add wormwars/exp02/__init__.py wormwars/exp02/remaps.py tests/test_exp02_remaps.py
git commit -m "Experiment 02: remap selection by a fixed rule on degree and routing"
```

---

### Task 5: Genome manifests and a relabelling-invariance test

**Files:**
- Modify: `wormwars/evo/genomes.py` (`edge_hash`; meta in `save_genome`/`save_population`; check in `load_genome`)
- Create: `wormwars/exp02/manifest.py`
- Test: `tests/test_exp02_manifest.py`, `tests/test_relabel_invariance.py`

**Interfaces:**
- Consumes: `interface_hash` (Task 3).
- Produces: `edge_hash(spec) -> str` in `wormwars.evo.genomes`;
  `run_manifest(cfg, iface, spec) -> dict`, `check_manifest(meta, cfg, iface, spec) -> None` in
  `wormwars.exp02.manifest`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_exp02_manifest.py
"""A saved genome must refuse to be replayed on another graph, interface or sensing mode."""

from __future__ import annotations

import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import shuffled
from wormwars.evo import load_genome, save_genome
from wormwars.evo.genomes import edge_hash
from wormwars.exp02.manifest import check_manifest, run_manifest
from wormwars.interface import interface_from_spec, load_interface, load_interface_spec, remapped_spec

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def con():
    return load_connectome()


def test_same_label_different_shuffle_is_refused(con, tmp_path):
    a = BrainSpec.from_connectome(shuffled(con, 1, "SH1"))
    b = BrainSpec.from_connectome(shuffled(con, 2, "SH1"))  # same label, different graph
    assert edge_hash(a) != edge_hash(b)
    g = Genome.random(a, Config().brain, 1, generator=torch.Generator().manual_seed(0))
    path = save_genome(tmp_path / "g.npz", g)
    load_genome(path, a, None)
    with pytest.raises(ValueError, match="edge set"):
        load_genome(path, b, None)


def test_manifest_refuses_another_interface_or_sensing(con, tmp_path):
    spec = BrainSpec.from_connectome(con)
    cfg = Config()
    iface = load_interface(con)
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(0))
    path = save_genome(tmp_path / "g.npz", g, cfg=cfg, **run_manifest(cfg, iface, spec))
    _, meta = load_genome(path, spec, None)
    check_manifest(meta, cfg, iface, spec)
    other = interface_from_spec(con, remapped_spec(
        load_interface_spec(), "food", [("ASIL", "ASIR"), ("ASJL", "ASJR"), ("ASGL", "ASGR")]))
    with pytest.raises(ValueError, match="interface_hash"):
        check_manifest(meta, cfg, other, spec)
    mono = cfg.copy()
    mono.world.food_sensing = "mono"
    with pytest.raises(ValueError, match="food_sensing"):
        check_manifest(meta, mono, iface, spec)


def test_old_files_without_a_manifest_still_load(con):
    spec = BrainSpec.from_connectome(con)
    g, meta = load_genome(ROOT / "runs" / "exp01b-direction-corrected" / "champion-N2-run00.npz", spec, None)
    assert "edge_hash" not in meta and g.cfg.init_chem_magnitude == "anatomical"
```

```python
# tests/test_relabel_invariance.py
"""Renumbering the neurons consistently everywhere must change nothing the world can see.

A cheap defence against indexing and direction errors of the kind that reversed experiment 01's
synapses: any code that confuses an index with a name, or rows with columns, fails this.
"""

from __future__ import annotations

import numpy as np
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.loader import Connectome
from wormwars.evo.rollout import rollout
from wormwars.interface import load_interface


def _relabel(con, perm):
    """New index perm[i] holds old neuron i."""
    n = con.n
    names = [None] * n
    classes = [None] * n
    for i in range(n):
        names[perm[i]] = con.names[i]
        classes[perm[i]] = con.classes[i]
    chem = np.zeros_like(con.chem)
    gap = np.zeros_like(con.gap)
    chem[np.ix_(perm, perm)] = con.chem
    gap[np.ix_(perm, perm)] = con.gap
    return Connectome(tuple(names), tuple(classes), chem, gap, con.weight_kind, con.meta, con.label)


def _transport(g, spec_a, spec_b, perm):
    p = torch.as_tensor(perm)
    idx_b = {(int(i), int(j)): k for k, (i, j) in enumerate(zip(spec_b.chem_i, spec_b.chem_j))}
    gidx_b = {(int(i), int(j)): k for k, (i, j) in enumerate(zip(spec_b.gap_i, spec_b.gap_j))}
    w = torch.zeros_like(g.w)
    for k, (i, j) in enumerate(zip(spec_a.chem_i, spec_a.chem_j)):
        w[:, idx_b[(int(p[i]), int(p[j]))]] = g.w[:, k]
    gg = torch.zeros_like(g.g)
    for k, (i, j) in enumerate(zip(spec_a.gap_i, spec_a.gap_j)):
        a, b = sorted((int(p[i]), int(p[j])))
        gg[:, gidx_b[(a, b)]] = g.g[:, k]
    tau = torch.zeros_like(g.tau)
    bias = torch.zeros_like(g.bias)
    tau[:, p] = g.tau
    bias[:, p] = g.bias
    return Genome(spec_b, g.cfg, w, gg, tau, bias)


def test_relabelling_changes_neither_brain_nor_world():
    con = load_connectome()
    perm = np.random.default_rng(0).permutation(con.n)
    con_b = _relabel(con, perm)
    spec_a, spec_b = BrainSpec.from_connectome(con), BrainSpec.from_connectome(con_b)
    cfg = Config()
    cfg.world.max_ticks = 30
    g_a = Genome.random(spec_a, cfg.brain, 2, generator=torch.Generator().manual_seed(4))
    g_b = _transport(g_a, spec_a, spec_b, perm)

    v = torch.randn(2, 3, con.n, generator=torch.Generator().manual_seed(5)) * 0.5
    cur = torch.randn(2, 3, con.n, generator=torch.Generator().manual_seed(6)) * 0.5
    p = torch.as_tensor(perm)
    vb, cb = torch.zeros_like(v), torch.zeros_like(cur)
    vb[..., p], cb[..., p] = v, cur
    out_a = Brain(g_a).step(v, cur)
    out_b = Brain(g_b).step(vb, cb)
    torch.testing.assert_close(out_b[..., p], out_a, rtol=1e-5, atol=1e-5)

    ids = np.arange(4)
    s_a = rollout(cfg, load_interface(con), g_a, ids, 9).score
    s_b = rollout(cfg, load_interface(con_b), g_b, ids, 9).score
    np.testing.assert_allclose(s_a, s_b, rtol=0, atol=1e-3)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3.13 -m pytest tests/test_exp02_manifest.py tests/test_relabel_invariance.py -q`
Expected: the manifest tests FAIL (`ImportError: edge_hash`). The relabelling test may already
PASS; that is the point of it, and it stays as a guard.

- [ ] **Step 3: Implement `edge_hash` and the check in `wormwars/evo/genomes.py`**

Add after `genome_hash`:

```python
def edge_hash(spec: BrainSpec) -> str:
    """sha256 of the edge lists in mask order. Two graphs with one label but different edges differ."""
    h = hashlib.sha256()
    for t in (spec.chem_i, spec.chem_j, spec.gap_i, spec.gap_j):
        h.update(t.detach().to("cpu", torch.int64).numpy().tobytes())
    return h.hexdigest()
```

In both `save_genome` and `save_population`, add `"edge_hash": edge_hash(spec),` to the `meta`
dict, directly after `"n_neurons": spec.n,`.

In `load_genome`, directly after the graph-label check:

```python
    stored_edges = meta.get("edge_hash")
    if stored_edges is not None and stored_edges != edge_hash(spec):
        raise ValueError(
            f"{Path(path).name} was evolved on a different edge set than this {spec.label!r} spec: "
            "same label, different graph. Genomes are mask-specific."
        )
```

- [ ] **Step 4: Implement `wormwars/exp02/manifest.py`**

```python
"""What a saved experiment-02 genome must match to be replayed: graph, interface, sensing, gains."""

from __future__ import annotations

from ..evo.genomes import edge_hash
from ..interface import interface_hash


def run_manifest(cfg, iface, spec) -> dict:
    return {
        "edge_hash": edge_hash(spec),
        "interface_hash": interface_hash(iface),
        "food_sensing": cfg.world.food_sensing,
        "sense_scale_pheromone": float(cfg.world.sense_scale_pheromone),
        "substeps": int(cfg.brain.substeps),
        "init_chem_magnitude": cfg.brain.init_chem_magnitude,
        "init_gap_magnitude": cfg.brain.init_gap_magnitude,
        "forward_gain": float(cfg.world.forward_gain),
        "turn_gain": float(cfg.world.turn_gain),
    }


def check_manifest(meta: dict, cfg, iface, spec) -> None:
    expected = run_manifest(cfg, iface, spec)
    bad = {k: (meta.get(k), v) for k, v in expected.items() if meta.get(k) != v}
    if bad:
        detail = "; ".join(f"{k}: saved {a!r}, now {b!r}" for k, (a, b) in bad.items())
        raise ValueError(f"genome does not match this condition: {detail}")
```

- [ ] **Step 5: Run the tests and the regression guards**

Run: `py -3.13 -m pytest tests/test_exp02_manifest.py tests/test_relabel_invariance.py tests/test_direction.py tests/test_coevolve.py -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add wormwars/evo/genomes.py wormwars/exp02/manifest.py tests/test_exp02_manifest.py tests/test_relabel_invariance.py
git commit -m "Genome manifests (edge hash, interface, sensing, gains) and a relabelling-invariance test"
```

---

### Task 6: Rollout for any brain, pellet accounting, and scripted controllers

**Files:**
- Modify: `wormwars/evo/rollout.py` (`_play`, `rollout_brain`, `RolloutResult.pellet_eaten`)
- Create: `wormwars/exp02/scripted.py`
- Test: `tests/test_exp02_scripted.py`

**Interfaces:**
- Consumes: `World.pellet_eaten` (Task 1).
- Produces: `rollout_brain(cfg, iface, brain, world_ids, run_seed, device="cpu", ticks=None) -> RolloutResult`;
  `RolloutResult.pellet_eaten: np.ndarray | None`;
  `ScriptedBrain(iface, n, policy, forward_gain, turn_gain, n_strains=1)`; policies `Stationary`,
  `Straight`, `StereoProportional(k, speed)`, `LevelKinesis(slow, fast, threshold, turn)`,
  `OneStepMemory(speed, turn, threshold)`; `score_policy(cfg, iface, policy, world_ids, run_seed, device) -> np.ndarray`;
  `tune(make_policy, grid, cfg, iface, world_ids, run_seed, device) -> tuple[dict, float]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_exp02_scripted.py
"""Scripted controllers drive the motors directly, through the same world as evolved brains."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo.rollout import rollout, rollout_brain
from wormwars.exp02 import scripted
from wormwars.interface import load_interface
from wormwars.world import World


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con)


def world_for(cfg, iface, policy, n_worlds=2):
    b = scripted.ScriptedBrain(iface, 302, policy, cfg.world.forward_gain, cfg.world.turn_gain)
    return World(cfg, iface, b, torch.zeros(n_worlds, 1, dtype=torch.long), run_seed=1)


def test_commands_arrive_at_the_motors_exactly(parts):
    _, iface = parts
    cfg = Config()

    class Fixed:
        def init(self, s, b):
            return None

        def __call__(self, left, right, state):
            return torch.full_like(left, 0.5), torch.full_like(left, -0.25), state

    w = world_for(cfg, iface, Fixed())
    w.tick()
    alive = w.alive
    torch.testing.assert_close(w.last_forward[alive], torch.full_like(w.last_forward[alive], 0.5))
    torch.testing.assert_close(w.last_turn[alive], torch.full_like(w.last_turn[alive], -0.25))


def test_stationary_does_not_move_and_straight_does(parts):
    _, iface = parts
    cfg = Config()
    w = world_for(cfg, iface, scripted.Stationary())
    p0 = w.pos.clone()
    for _ in range(20):
        w.tick()
    moved = (w.pos - p0).norm(dim=-1)[w.alive]
    assert moved.max() < 0.2  # only crowd pushes
    w = world_for(cfg, iface, scripted.Straight())
    p0 = w.pos.clone()
    for _ in range(20):
        w.tick()
    assert (w.pos - p0).norm(dim=-1)[w.alive].mean() > 2.0


def test_one_step_memory_turns_only_when_concentration_falls():
    pol = scripted.OneStepMemory(speed=0.8, turn=0.9, threshold=0.0)
    s = pol.init(1, 2)
    x = torch.tensor([[1.0, 1.0]])
    f, t, s = pol(x, x, s)                       # first step: no history
    assert torch.all(t == 0)
    f, t, s = pol(torch.tensor([[1.2, 0.5]]), torch.tensor([[1.2, 0.5]]), s)
    assert t[0, 0] == 0 and t[0, 1] == pytest.approx(0.9)


def test_rollout_brain_matches_rollout_for_a_real_brain(parts):
    con, iface = parts
    cfg = Config()
    cfg.world.max_ticks = 60
    spec = BrainSpec.from_connectome(con)
    g = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(1))
    ids = np.arange(3)
    from wormwars.brain import Brain

    a = rollout(cfg, iface, g, ids, 4)
    b = rollout_brain(cfg, iface, Brain(g), ids, 4)
    np.testing.assert_array_equal(a.score, b.score)
    assert a.pellet_eaten is not None and a.pellet_eaten.shape == a.score.shape


def test_scores_are_finite_when_everyone_starves(parts):
    _, iface = parts
    cfg = Config()
    cfg.world.max_ticks = 500
    s = scripted.score_policy(cfg, iface, scripted.Stationary(), np.arange(2), 1, "cpu")
    assert np.isfinite(s).all() and (s >= 0).all()


def test_tune_returns_the_best_grid_point(parts):
    _, iface = parts
    cfg = Config()
    cfg.world.max_ticks = 80
    best, score = scripted.tune(
        lambda speed: scripted.StereoProportional(k=2.0, speed=speed),
        {"speed": [0.0, 0.8]}, cfg, iface, np.arange(2), 1, "cpu",
    )
    assert best == {"speed": 0.8} and np.isfinite(score)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3.13 -m pytest tests/test_exp02_scripted.py -q`
Expected: FAIL (`ImportError: rollout_brain`).

- [ ] **Step 3: Refactor `wormwars/evo/rollout.py`**

Add a field at the end of `RolloutResult`:

```python
    pellet_eaten: np.ndarray | None = None  # corpse pellets eaten, [strains, worlds]
```

Add `_play` and `rollout_brain` before `rollout`, and replace the body of `rollout`'s chunk loop
with a call to `_play`:

```python
def _play(cfg, iface, brain, world_ids, run_seed, device, combat_stage=0, ticks=None, recorder=None):
    """Every strain of `brain` on every world id. `brain` is a Brain or anything World accepts."""
    n_sub, n_ids = brain.n_strains, len(world_ids)
    strain_of = torch.arange(n_sub, device=device).repeat_interleave(n_ids).reshape(-1, 1)
    ids = np.tile(world_ids, n_sub)
    world = World(
        cfg, iface, brain, strain_of, run_seed=run_seed, world_ids=ids,
        device=device, combat_stage=combat_stage,
    )
    if recorder is not None:
        recorder.attach(world)
    food0 = world.fields[:, world.ch.FOOD].sum(dim=(1, 2)).clone()
    world.run(ticks)
    food1 = world.fields[:, world.ch.FOOD].sum(dim=(1, 2))
    shape = (n_sub, n_ids)
    return {
        "score": foraging_score(world).reshape(shape).cpu().numpy(),
        "energy": world.swarm_energy()[:, 0].reshape(shape).cpu().numpy(),
        "alive": world.n_alive()[:, 0].reshape(shape).cpu().numpy(),
        "eaten": (food0 - food1).reshape(shape).cpu().numpy(),
        "pellet": world.pellet_eaten.reshape(shape).cpu().numpy(),
        "err": world.energy_ledger_error().abs().max().item(),
        "ticks": world.tick_count,
    }


def rollout_brain(cfg, iface, brain, world_ids, run_seed, device="cpu", ticks=None) -> RolloutResult:
    """Like `rollout`, for an already-built brain (for example a scripted controller)."""
    world_ids = np.asarray(world_ids, dtype=np.int64)
    r = _play(cfg, iface, brain, world_ids, run_seed, device, ticks=ticks)
    return RolloutResult(r["score"], r["energy"], r["alive"], r["eaten"], r["ticks"], r["err"],
                         pellet_eaten=r["pellet"])
```

In `rollout`, the list setup becomes `scores, energies, alives, eatens, pellets = [], [], [], [], []`,
and the loop body after `brain_hook` becomes:

```python
        r = _play(cfg, iface, brain, world_ids, run_seed, device, combat_stage, ticks,
                  recorder if lo == 0 else None)
        scores.append(r["score"])
        energies.append(r["energy"])
        alives.append(r["alive"])
        eatens.append(r["eaten"])
        pellets.append(r["pellet"])
        worst_err = max(worst_err, r["err"])
        used_ticks = r["ticks"]
```

(Remove the now-unused `n_sub`, `strain_of`, `ids`, `world` and `food*` lines from the loop.) The
return adds `pellet_eaten=np.concatenate(pellets)`.

- [ ] **Step 4: Implement `wormwars/exp02/scripted.py`**

```python
"""Scripted controllers: reference levels for each task, played through the real world.

A ScriptedBrain stands in for Brain. It reads the injected current at the food neurons of the
interface it is given (the same observation an evolved brain gets) and writes motor commands by
setting the read-out neurons so that the world's own read-out reproduces the command exactly:
forward = mean(tanh v+) - mean(tanh v-), scaled by 0.5 x gain. With tanh v+ = c / gain and
tanh v- = -c / gain, the final command is c.
"""

from __future__ import annotations

import itertools

import numpy as np
import torch

from ..evo.rollout import rollout_brain


class ScriptedBrain:
    def __init__(self, iface, n, policy, forward_gain, turn_gain, n_strains=1):
        self.n, self.n_strains, self.policy = n, n_strains, policy
        self.forward_gain, self.turn_gain = float(forward_gain), float(turn_gain)
        names = list(iface.signal_names)
        self.left = int(iface.sensor_neuron[names.index("food_left")])
        self.right = int(iface.sensor_neuron[names.index("food_right")])
        t = lambda a: torch.as_tensor(np.asarray(a), dtype=torch.long)  # noqa: E731
        self.fp, self.fm = t(iface.forward_plus), t(iface.forward_minus)
        self.tp, self.tm = t(iface.turn_plus), t(iface.turn_minus)
        self.state = None

    def initial_state(self, n_weys: int) -> torch.Tensor:
        self.state = self.policy.init(self.n_strains, n_weys)
        return torch.zeros(self.n_strains, n_weys, self.n)

    def step(self, v: torch.Tensor, current: torch.Tensor) -> torch.Tensor:
        left, right = current[..., self.left], current[..., self.right]
        fwd, turn, self.state = self.policy(left, right, self.state)
        out = torch.zeros_like(current)
        dev = current.device
        a_f = torch.atanh((fwd / self.forward_gain).clamp(-0.999999, 0.999999))
        a_t = torch.atanh((turn / self.turn_gain).clamp(-0.999999, 0.999999))
        out[..., self.fp.to(dev)] = a_f.unsqueeze(-1)
        out[..., self.fm.to(dev)] = -a_f.unsqueeze(-1)
        out[..., self.tp.to(dev)] = a_t.unsqueeze(-1)
        out[..., self.tm.to(dev)] = -a_t.unsqueeze(-1)
        return out


class Stationary:
    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        z = torch.zeros_like(left)
        return z, z, state


class Straight:
    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        return torch.ones_like(left), torch.zeros_like(left), state


class StereoProportional:
    """Memoryless, stereo: steer toward the stronger side at a constant speed."""

    def __init__(self, k: float, speed: float):
        self.k, self.speed = k, speed

    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        turn = (self.k * (left - right)).clamp(-1, 1)
        return torch.full_like(left, self.speed), turn, state


class LevelKinesis:
    """Memoryless, mono: slow down where food is strong, speed up where it is weak, keep turning."""

    def __init__(self, slow: float, fast: float, threshold: float, turn: float):
        self.slow, self.fast, self.threshold, self.turn = slow, fast, threshold, turn

    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        level = (left + right) / 2
        fwd = torch.where(level > self.threshold, torch.full_like(level, self.slow),
                          torch.full_like(level, self.fast))
        return fwd, torch.full_like(level, self.turn), state


class OneStepMemory:
    """Mono, one tick of memory: go straight while concentration holds, turn when it falls."""

    def __init__(self, speed: float, turn: float, threshold: float):
        self.speed, self.turn, self.threshold = speed, turn, threshold

    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        level = (left + right) / 2
        if state is None:
            falling = torch.zeros_like(level, dtype=torch.bool)
        else:
            falling = level < state - self.threshold
        turn = torch.where(falling, torch.full_like(level, self.turn), torch.zeros_like(level))
        return torch.full_like(level, self.speed), turn, level.clone()


def score_policy(cfg, iface, policy, world_ids, run_seed, device) -> np.ndarray:
    """Per-world foraging score of one scripted policy, shape [worlds]."""
    brain = ScriptedBrain(iface, 302, policy, cfg.world.forward_gain, cfg.world.turn_gain)
    return rollout_brain(cfg, iface, brain, world_ids, run_seed, device).score[0]


def tune(make_policy, grid: dict, cfg, iface, world_ids, run_seed, device) -> tuple[dict, float]:
    """Exhaustive grid search on tuning worlds; returns (best parameters, their mean score)."""
    keys = sorted(grid)
    best, best_score = None, -np.inf
    for values in itertools.product(*(grid[k] for k in keys)):
        params = dict(zip(keys, values))
        s = float(score_policy(cfg, iface, make_policy(**params), world_ids, run_seed, device).mean())
        if s > best_score:
            best, best_score = params, s
    return best, best_score
```

- [ ] **Step 5: Run the tests and the regression guards**

Run: `py -3.13 -m pytest tests/test_exp02_scripted.py tests/test_evolve.py tests/test_world.py tests/test_direction.py -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add wormwars/evo/rollout.py wormwars/exp02/scripted.py tests/test_exp02_scripted.py
git commit -m "Rollout for any brain, pellet accounting, and scripted controllers"
```

---

### Task 7: In-world, iterated calibration to a fixed target

**Files:**
- Modify: `wormwars/calibration.py` (add `DriveReport`, `achieved_drive`, `InWorldCalibration`, `calibrate_in_world`)
- Test: `tests/test_exp02_calibration.py`

**Interfaces:**
- Consumes: `World.last_forward/last_turn` (Task 1).
- Produces: `achieved_drive(graph, cfg, iface, n_strains=24, ticks=80, seed=0, device="cpu") -> DriveReport`
  (fields `forward, turn, clip_forward, clip_turn, displacement`);
  `calibrate_in_world(graph, cfg, iface, target: tuple[float, float], *, n_strains=24, ticks=80, seed=0, device="cpu", tol=0.02, max_iter=8, max_gain=40.0) -> InWorldCalibration`
  (fields `graph, forward_gain, turn_gain, target, achieved: DriveReport, iterations, history`; method `as_dict()`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_exp02_calibration.py
"""Calibration in the world the brains actually run in, to a fixed target, iterated."""

from __future__ import annotations

import pytest

from wormwars import calibration as calib
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import shuffled
from wormwars.interface import load_interface

TARGET = (0.5, 0.4)


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con)


def test_achieved_drive_reports_in_range_values(parts):
    con, iface = parts
    d = calib.achieved_drive(con, Config(), iface, n_strains=6, ticks=30)
    assert 0 < d.forward <= 1 and 0 < d.turn <= 1
    assert 0 <= d.clip_forward <= 1 and 0 <= d.clip_turn <= 1 and d.displacement >= 0


@pytest.mark.parametrize("which", ["N2", "SH1"])
def test_calibration_reaches_the_target_within_tolerance(parts, which):
    con, iface = parts
    graph = con if which == "N2" else shuffled(con, 1, "SH1")
    cal = calib.calibrate_in_world(graph, Config(), iface, TARGET, n_strains=6, ticks=30, tol=0.02)
    assert abs(cal.achieved.forward / TARGET[0] - 1) <= 0.02
    assert abs(cal.achieved.turn / TARGET[1] - 1) <= 0.02
    assert cal.as_dict()["graph"] == graph.label


def test_calibration_that_cannot_converge_says_so(parts):
    con, iface = parts
    with pytest.raises(RuntimeError, match="did not converge"):
        calib.calibrate_in_world(con, Config(), iface, (1.5, 0.4), n_strains=4, ticks=20, max_iter=3)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3.13 -m pytest tests/test_exp02_calibration.py -q`
Expected: FAIL (`AttributeError: achieved_drive`).

- [ ] **Step 3: Implement in `wormwars/calibration.py`**

Add at the end of the module:

```python
@dataclass
class DriveReport:
    """What a random population actually does at the configured gains, in the real world."""

    forward: float  # mean |forward command| over ticks and living weys
    turn: float
    clip_forward: float  # share of commands at the +-1 clip
    clip_turn: float
    displacement: float  # mean distance moved per tick

    def as_dict(self) -> dict:
        return dict(vars(self))


def achieved_drive(graph, cfg, iface, n_strains=24, ticks=80, seed=0, device="cpu") -> DriveReport:
    from .world import World

    probe = cfg.copy()
    probe.world.n_swarms = 1
    spec = BrainSpec.from_connectome(graph, device=device)
    gen = torch.Generator(device=device).manual_seed(seed)
    genome = Genome.random(spec, probe.brain, n_strains, generator=gen, device=device)
    world = World(probe, iface, Brain(genome), torch.arange(n_strains).reshape(n_strains, 1),
                  run_seed=seed, device=device)
    acc = np.zeros(5)
    n = 0
    for _ in range(ticks):
        pos0 = world.pos.clone()
        world.tick()
        alive = world.alive
        if not bool(alive.any()):
            break
        f, t = world.last_forward[alive].abs(), world.last_turn[alive].abs()
        acc += [float(f.mean()), float(t.mean()), float((f >= 1 - 1e-6).float().mean()),
                float((t >= 1 - 1e-6).float().mean()),
                float((world.pos - pos0).norm(dim=-1)[alive].mean())]
        n += 1
    acc /= max(n, 1)
    return DriveReport(*[float(x) for x in acc])


@dataclass
class InWorldCalibration:
    graph: str
    forward_gain: float
    turn_gain: float
    target: tuple[float, float]
    achieved: DriveReport
    iterations: int
    history: list

    def as_dict(self) -> dict:
        d = dict(vars(self))
        d["achieved"] = self.achieved.as_dict()
        d["target"] = list(self.target)
        return d


def calibrate_in_world(graph, cfg, iface, target, *, n_strains=24, ticks=80, seed=0,
                       device="cpu", tol=0.02, max_iter=8, max_gain=40.0) -> InWorldCalibration:
    """Multiplicative fixed-point iteration on the gains until the achieved drive is within `tol`
    of `target` on both axes. Clipping and sensory feedback make the response non-linear, which is
    why one linear fit (the old `calibrate`) lands at 84-97% of target and this iterates."""
    c = cfg.copy()
    history = []
    for it in range(1, max_iter + 1):
        d = achieved_drive(graph, c, iface, n_strains, ticks, seed, device)
        history.append({"forward_gain": c.world.forward_gain, "turn_gain": c.world.turn_gain,
                        **d.as_dict()})
        if abs(d.forward / target[0] - 1) <= tol and abs(d.turn / target[1] - 1) <= tol:
            return InWorldCalibration(graph.label, float(c.world.forward_gain),
                                      float(c.world.turn_gain), tuple(target), d, it, history)
        c.world.forward_gain = min(c.world.forward_gain * target[0] / max(d.forward, 1e-9), max_gain)
        c.world.turn_gain = min(c.world.turn_gain * target[1] / max(d.turn, 1e-9), max_gain)
    raise RuntimeError(
        f"calibration of {graph.label} did not converge within {max_iter} iterations: {history[-1]}"
    )
```

Check that `np`, `torch`, `Brain`, `BrainSpec`, `Genome` and `dataclass` are already imported at
the top of `calibration.py`; `np`, `torch`, `dataclass` and the brain classes are, per its header.

- [ ] **Step 4: Run the tests**

Run: `py -3.13 -m pytest tests/test_exp02_calibration.py tests/test_calibration.py -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add wormwars/calibration.py tests/test_exp02_calibration.py
git commit -m "In-world calibration to a fixed target, iterated until within tolerance"
```

---

### Task 8: Evolution checkpoints on a separate suite, and champion snapshots

**Files:**
- Modify: `wormwars/evo/evolve.py` (`evolve` parameters `checkpoint_ids`, `snapshots`; `RunResult.snapshots`)
- Test: `tests/test_exp02_evolve.py`

**Interfaces:**
- Produces: `evolve(..., checkpoint_ids: np.ndarray | None = None, snapshots: tuple[int, ...] = ())`;
  `RunResult.snapshots: dict[int, Genome]` (the best-of-generation strain at each listed
  generation).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_exp02_evolve.py
"""Checkpoints on their own suite, and snapshots that let an 80-generation run stand in for a
40-generation one."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo import evolve as evolve_mod
from wormwars.evo.evolve import evolve
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def small():
    con = load_connectome()
    cfg = Config()
    cfg.world.max_ticks = 40
    cfg.evo.population = 6
    cfg.evo.elites = 1
    cfg.evo.truncation = 3
    cfg.evo.worlds_per_strain = 2
    cfg.evo.holdout_worlds = 2
    return cfg, load_interface(con), BrainSpec.from_connectome(con)


def test_checkpoints_use_the_given_suite(small, monkeypatch):
    cfg, iface, spec = small
    cfg = cfg.copy()
    cfg.evo.generations = 3
    seen = []
    orig = evolve_mod.evaluate_on

    def spy(cfg_, iface_, genome, ids, *a, **k):
        seen.append(tuple(np.asarray(ids)))
        return orig(cfg_, iface_, genome, ids, *a, **k)

    monkeypatch.setattr(evolve_mod, "evaluate_on", spy)
    suite = np.array([123456789, 123456790])
    evolve(cfg, iface, spec, 0, 7, holdout_every=1, checkpoint_ids=suite, verbose=False)
    assert tuple(suite) in seen


def test_snapshot_of_the_last_generation_is_the_champion(small):
    cfg, iface, spec = small
    cfg = cfg.copy()
    cfg.evo.generations = 3
    r = evolve(cfg, iface, spec, 0, 7, snapshots=(0, 2), verbose=False)
    assert set(r.snapshots) == {0, 2}
    assert torch.equal(r.snapshots[2].w, r.champion.w)


def test_a_longer_run_reproduces_the_shorter_one_up_to_its_length(small):
    cfg, iface, spec = small
    short, long_ = cfg.copy(), cfg.copy()
    short.evo.generations, long_.evo.generations = 2, 4
    a = evolve(short, iface, spec, 0, 9, verbose=False)
    b = evolve(long_, iface, spec, 0, 9, snapshots=(1,), verbose=False)
    assert torch.equal(a.champion.w, b.snapshots[1].w)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3.13 -m pytest tests/test_exp02_evolve.py -q`
Expected: FAIL (`TypeError`: unexpected keyword `checkpoint_ids`).

- [ ] **Step 3: Implement in `wormwars/evo/evolve.py`**

In `RunResult`, add `snapshots: dict = field(default_factory=dict)`.

Add to `evolve`'s signature, after `verbose: bool = True,`:

```python
    checkpoint_ids: np.ndarray | None = None,
    snapshots: tuple[int, ...] = (),
```

In the periodic evaluation, replace `pool.holdout` with
`pool.holdout if checkpoint_ids is None else np.asarray(checkpoint_ids)`.

Directly after `result.evaluations += fit.size * len(ids)`:

```python
        if g in snapshots:
            result.snapshots[g] = genome.select([int(np.argmax(fit))])
```

(The final champion is `argmax` of the same population on the same ids at the last generation,
so the last-generation snapshot equals it, and the third test pins that.)

- [ ] **Step 4: Run the tests and the regression guards**

Run: `py -3.13 -m pytest tests/test_exp02_evolve.py tests/test_evolve.py -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add wormwars/evo/evolve.py tests/test_exp02_evolve.py
git commit -m "Evolution checkpoints on a separate suite, and champion snapshots"
```

---

### Task 9: The grid, the schedule, and the resumable runner

**Files:**
- Create: `wormwars/exp02/grid.py`
- Create: `scripts/exp02.py` (subcommands `remaps`, `calibrate`, `diagnostics`, `pilot`, `run`)
- Test: `tests/test_exp02_grid.py`

**Interfaces:**
- Consumes: Tasks 1-8.
- Produces (`wormwars.exp02.grid`): `EXP02_DIR = ROOT / "experiments" / "02-screening"`;
  `TARGET_DRIVE = (0.5, 0.4)`; `CHECKPOINT_IDS`; `TUNING_IDS`; `task_config(base, task) -> Config`;
  `Cell(task, mapping)`; `RunSpec(cell, graph, run, run_seed, generations, snapshots)`;
  `run_schedule() -> list[list[RunSpec]]` (batches); `graph_for(con, name) -> Connectome`;
  `brain_config_for_graph(cfg, name) -> Config`; `interface_for(con, mapping, remap_sets) -> Interface`;
  `pending(schedule, done_keys) -> list[list[RunSpec]]`; `RunSpec.key -> str`;
  `select_batches(batches, elapsed_s, per_batch_s, budget_s) -> int`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_exp02_grid.py
"""The schedule is balanced, crossed, resumable, and stops only between whole batches."""

from __future__ import annotations

from collections import Counter

import pytest

from wormwars.config import Config
from wormwars.exp02 import grid


def test_task_configs():
    base = Config()
    t0, t1, a = (grid.task_config(base, t) for t in ("T0", "T1", "A"))
    assert (t0.world.food_sensing, t0.world.sense_scale_pheromone) == ("stereo", 0.0)
    assert (t1.world.food_sensing, t1.world.sense_scale_pheromone) == ("mono", 0.0)
    assert (a.world.food_sensing, a.world.sense_scale_pheromone) == ("stereo", 0.35)
    for c in (t0, t1, a):
        assert c.brain.substeps == 32 and c.evo.generations == 40 and c.evo.holdout_worlds == 64
    assert base.brain.substeps == 8, "the base config must not be mutated"
    with pytest.raises(ValueError):
        grid.task_config(base, "T9")


def test_schedule_counts_match_the_design():
    runs = [r for b in grid.run_schedule() for r in b]
    by = Counter((r.cell.task, r.cell.mapping, r.graph[:2]) for r in runs)
    for task, mapping in [("T0", m) for m in ("M0", "R1", "R2")] + [("T1", m) for m in ("M0", "R1", "R2", "MS")]:
        assert by[(task, mapping, "N2")] == 4 + (6 if (task, mapping) == ("T1", "M0") else 0)
        assert by[(task, mapping, "SH")] == 12
    assert by[("A", "M0", "N2")] == 4 and by[("A", "M0", "SH")] == 6
    assert sum(r.generations == 80 for r in runs) == 8
    assert len(runs) == 128
    assert len({r.key for r in runs}) == len(runs)


def test_seeds_are_crossed_across_cells():
    runs = [r for b in grid.run_schedule() for r in b]
    seeds = {}
    for r in runs:
        seeds.setdefault((r.graph, r.run), set()).add(r.run_seed)
    assert all(len(s) == 1 for s in seeds.values()), "one seed per (graph, run) in every cell"


def test_every_batch_is_one_replicate_across_all_its_cells():
    for batch in grid.run_schedule():
        units = {(r.graph, r.run) for r in batch}
        assert len(units) == 1


def test_resume_skips_done_runs_without_shifting_seeds():
    sched = grid.run_schedule()
    done = {r.key for r in sched[0]} | {sched[1][0].key}
    rest = grid.pending(sched, done)
    left = [r for b in rest for r in b]
    assert all(r.key not in done for r in left)
    original = {r.key: r.run_seed for b in sched for r in b}
    assert all(original[r.key] == r.run_seed for r in left)


def test_budget_stops_between_batches():
    assert grid.select_batches(10, elapsed_s=0, per_batch_s=100, budget_s=350) == 3
    assert grid.select_batches(10, elapsed_s=300, per_batch_s=100, budget_s=350) == 0
    assert grid.select_batches(2, elapsed_s=0, per_batch_s=100, budget_s=1e9) == 2
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3.13 -m pytest tests/test_exp02_grid.py -q`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement `wormwars/exp02/grid.py`**

```python
"""Experiment 02's grid: tasks, cells, crossed seeds, balanced resumable batches."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config import Config
from ..connectome.graphs import shuffled
from ..interface import interface_from_spec, load_interface_spec, remapped_spec

ROOT = Path(__file__).resolve().parents[2]
EXP02_DIR = ROOT / "experiments" / "02-screening"
TARGET_DRIVE = (0.5, 0.4)
CHECKPOINT_IDS = np.arange(950_000_000, 950_000_016)
TUNING_IDS = np.arange(960_000_000, 960_000_032)
TUNING_SEED = 99_999
N2_RUNS, SH_GRAPHS, SH_RUNS, PERM_RUNS = 4, 6, 2, 6
MAIN = [("T0", m) for m in ("M0", "R1", "R2")] + [("T1", m) for m in ("M0", "R1", "R2", "MS")]
# Pre-registered continuation runs (80 generations; their generation-39 snapshot is the 40-generation result)
CONTINUATION = {("T1", "M0", "N2", 0), ("T1", "M0", "N2", 1), ("T1", "M0", "SH1", 0),
                ("T1", "M0", "SH2", 0), ("T0", "M0", "N2", 0), ("T0", "M0", "N2", 1),
                ("T0", "M0", "SH1", 0), ("T0", "M0", "SH2", 0)}


def task_config(base: Config, task: str) -> Config:
    if task not in ("T0", "T1", "A"):
        raise ValueError(f"unknown task {task!r}")
    c = base.copy()
    c.brain.substeps = 32
    c.world.max_ticks = 400
    c.evo.generations, c.evo.population = 40, 32
    c.evo.worlds_per_strain, c.evo.holdout_worlds = 8, 64
    c.world.food_sensing = "mono" if task == "T1" else "stereo"
    c.world.sense_scale_pheromone = 0.35 if task == "A" else 0.0
    return c


@dataclass(frozen=True)
class Cell:
    task: str
    mapping: str


@dataclass(frozen=True)
class RunSpec:
    cell: Cell
    graph: str  # "N2", "N2perm", "SH1".."SH6"
    run: int
    run_seed: int
    generations: int
    snapshots: tuple

    @property
    def key(self) -> str:
        return f"{self.cell.task}-{self.cell.mapping}-{self.graph}-run{self.run:02d}"


def _seed(graph: str, run: int) -> int:
    if graph == "N2":
        return 20_000 + run
    if graph == "N2perm":
        return 22_000 + run
    return 21_000 + 10 * int(graph[2:]) + run


def _spec(task, mapping, graph, run) -> RunSpec:
    cont = (task, mapping, graph, run) in CONTINUATION
    return RunSpec(Cell(task, mapping), graph, run, _seed(graph, run),
                   80 if cont else 40, (0, 39) if cont else (0,))


def run_schedule() -> list[list[RunSpec]]:
    """One batch per replicate unit (graph, run), holding that unit's runs in every cell it has."""
    units = []
    for r in range(max(N2_RUNS, SH_RUNS, PERM_RUNS)):
        if r < N2_RUNS:
            units.append(("N2", r))
        for k in range(1, SH_GRAPHS + 1):
            if r < SH_RUNS:
                units.append((f"SH{k}", r))
        if r < PERM_RUNS:
            units.append(("N2perm", r))
    batches = []
    for graph, r in units:
        b = []
        if graph == "N2perm":
            b.append(_spec("T1", "M0", graph, r))
        else:
            b += [_spec(t, m, graph, r) for t, m in MAIN]
            if graph == "N2" or r == 0:
                b.append(_spec("A", "M0", graph, r))
        batches.append(b)
    return batches


def pending(schedule, done_keys: set[str]) -> list[list[RunSpec]]:
    out = []
    for b in schedule:
        left = [r for r in b if r.key not in done_keys]
        if left:
            out.append(left)
    return out


def select_batches(n_batches: int, elapsed_s: float, per_batch_s: float, budget_s: float) -> int:
    """How many whole batches still fit in the budget."""
    room = budget_s - elapsed_s
    return max(0, min(n_batches, int(room // per_batch_s))) if per_batch_s > 0 else n_batches


def graph_for(con, name: str):
    if name in ("N2", "N2perm"):
        return con
    return shuffled(con, int(name[2:]), name)


def brain_config_for_graph(cfg: Config, name: str) -> Config:
    c = cfg.copy()
    if name == "N2perm":
        c.brain.init_chem_magnitude = c.brain.init_gap_magnitude = "permuted"
        c.brain.init_permutation_seed = 1
    return c


def interface_for(con, mapping: str, remap_sets: dict):
    spec = load_interface_spec()
    if mapping == "M0":
        return interface_from_spec(con, spec)
    pairs = [tuple(p) for p in remap_sets[mapping]]
    return interface_from_spec(con, remapped_spec(spec, "food", pairs))
```

Note: the SH "run r" units come after the N2 unit of the same r, so batches alternate
N2 and SH replicates. `run_schedule()` returns 4 N2 + 12 SH + 6 N2perm = 22 batches holding
7 x 4 + 7 x 12 + 4 + 6 + 6 = 128 runs.

- [ ] **Step 4: Implement `scripts/exp02.py`**

```python
"""Experiment 02, the screening fraction. See experiments/02-screening/DESIGN.md.

    py -3.13 scripts/exp02.py remaps        # choose R1, R2, MS by the fixed rule -> remaps.json
    py -3.13 scripts/exp02.py calibrate     # in-world gains per graph variant   -> calibration.json
    py -3.13 scripts/exp02.py diagnostics   # tune and score scripted controllers -> diagnostics.json
    py -3.13 scripts/exp02.py pilot         # one timed end-to-end run per task on SH101 -> pilot.json
    py -3.13 scripts/exp02.py run           # the grid, in balanced resumable batches
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wormwars import calibration as calib
from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import shuffled
from wormwars.evo import SeedPool, rollout, save_genome
from wormwars.evo.bundle import write_bundle
from wormwars.evo.evolve import evolve
from wormwars.exp02 import grid, remaps, scripted
from wormwars.exp02.manifest import run_manifest
from wormwars.interface import load_interface

OUT = Path("runs/exp02-screening")
GRAPH_VARIANTS = ["N2", "N2perm"] + [f"SH{k}" for k in range(1, grid.SH_GRAPHS + 1)]


def _json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_remaps(args, con, iface):
    rec = remaps.remap_record(con, iface)
    _json(grid.EXP02_DIR / "remaps.json", rec)
    print(json.dumps(rec["sets"], indent=1))


def cmd_calibrate(args, con, iface):
    base = grid.task_config(Config(), "T0")
    out = {}
    for name in GRAPH_VARIANTS:
        cfg = grid.brain_config_for_graph(base, name)
        cal = calib.calibrate_in_world(grid.graph_for(con, name), cfg, iface, grid.TARGET_DRIVE,
                                       device=args.device)
        check = cfg.copy()
        check.world.forward_gain, check.world.turn_gain = cal.forward_gain, cal.turn_gain
        val = calib.achieved_drive(grid.graph_for(con, name), check, iface, seed=1, device=args.device)
        out[name] = {**cal.as_dict(), "validation_seed1": val.as_dict()}
        print(f"{name:7} gains {cal.forward_gain:.3f}/{cal.turn_gain:.3f} in {cal.iterations} it; "
              f"validation |fwd| {val.forward:.3f} |turn| {val.turn:.3f}")
    _json(grid.EXP02_DIR / "calibration.json", out)


POLICIES = {
    "T0": {"stereo_proportional": (lambda k, speed: scripted.StereoProportional(k, speed),
                                   {"k": [0.5, 1, 2, 4, 8], "speed": [0.4, 0.6, 0.8, 1.0]})},
    "T1": {"level_kinesis": (lambda slow, fast, threshold, turn: scripted.LevelKinesis(slow, fast, threshold, turn),
                             {"slow": [0.0, 0.2], "fast": [0.6, 1.0], "threshold": [0.02, 0.05, 0.1],
                              "turn": [0.0, 0.3, 0.6]}),
           "one_step_memory": (lambda speed, turn, threshold: scripted.OneStepMemory(speed, turn, threshold),
                               {"speed": [0.6, 0.8, 1.0], "turn": [0.5, 0.9], "threshold": [0.0, 0.005, 0.02]})},
}


def cmd_diagnostics(args, con, iface):
    cal = _load(grid.EXP02_DIR / "calibration.json")["N2"]
    seeds = sorted({r.run_seed for b in grid.run_schedule() for r in b})
    out = {}
    for task in ("T0", "T1", "A"):
        cfg = grid.task_config(Config(), task)
        cfg.world.forward_gain, cfg.world.turn_gain = cal["forward_gain"], cal["turn_gain"]
        fixed = {"stationary": scripted.Stationary(), "straight": scripted.Straight()}
        tuned = {}
        for name, (make, space) in POLICIES["T1" if task == "T1" else "T0"].items():
            best, s = scripted.tune(make, space, cfg, iface, grid.TUNING_IDS, grid.TUNING_SEED, args.device)
            tuned[name] = {"params": best, "tuning_score": s}
            fixed[name] = make(**best)
        per_seed = {}
        for seed in seeds:
            ids = SeedPool(cfg, seed).holdout
            per_seed[str(seed)] = {n: scripted.score_policy(cfg, iface, p, ids, seed, args.device).tolist()
                                   for n, p in fixed.items()}
        out[task] = {"tuned": tuned, "per_seed_holdout": per_seed}
        print(task, {n: v["params"] for n, v in tuned.items()})
    _json(grid.EXP02_DIR / "diagnostics.json", out)


def _gains(name):
    c = _load(grid.EXP02_DIR / "calibration.json")[name]
    return c["forward_gain"], c["turn_gain"]


def _execute(spec: grid.RunSpec, con, remap_sets, device, out: Path, gains_for=None) -> dict:
    cfg = grid.brain_config_for_graph(grid.task_config(Config(), spec.cell.task), spec.graph)
    cfg.evo.generations = spec.generations
    cfg.world.forward_gain, cfg.world.turn_gain = (gains_for or _gains)(spec.graph)
    graph = grid.graph_for(con, spec.graph)
    iface = grid.interface_for(con, spec.cell.mapping, remap_sets)
    bspec = BrainSpec.from_connectome(graph, device=device)
    t0 = time.perf_counter()
    res = evolve(cfg, iface, bspec, spec.run, spec.run_seed, device=device, holdout_every=10,
                 checkpoint_ids=grid.CHECKPOINT_IDS, snapshots=spec.snapshots, verbose=False)
    pool = SeedPool(cfg, spec.run_seed)
    manifest = run_manifest(cfg, iface, bspec)
    rec = {"key": spec.key, "task": spec.cell.task, "mapping": spec.cell.mapping, "graph": spec.graph,
           "run": spec.run, "run_seed": spec.run_seed, "generations": spec.generations,
           "checkpoints": [(x.generation, x.holdout_best) for x in res.log if x.holdout_best is not None]}
    for g in spec.snapshots:
        champ = res.snapshots[g]
        held = rollout(cfg, iface, champ, pool.holdout, spec.run_seed, device)
        tag = "g00" if g == 0 else "g39"
        rec[f"holdout_{tag}"] = held.score[0].tolist()
        rec[f"pellet_share_{tag}"] = float(held.pellet_eaten.sum() / max(held.pellet_eaten.sum() + held.eaten.sum(), 1e-9))
        save_genome(out / f"{spec.key}-{tag}.npz", champ, 0, cfg=cfg, run_seed=spec.run_seed,
                    snapshot_generation=g, **manifest)
    if spec.generations > 40:
        held = rollout(cfg, iface, res.champion, pool.holdout, spec.run_seed, device)
        rec["holdout_g79"] = held.score[0].tolist()
        save_genome(out / f"{spec.key}-g79.npz", res.champion, 0, cfg=cfg, run_seed=spec.run_seed, **manifest)
    rec["wall_seconds"] = time.perf_counter() - t0
    return rec


def cmd_pilot(args, con, iface):
    remap_sets = _load(grid.EXP02_DIR / "remaps.json")["sets"]
    out = OUT / "pilot"
    pilot_gains = {}

    def gains_for(name):
        if name not in pilot_gains:
            cfg = grid.task_config(Config(), "T0")
            c = calib.calibrate_in_world(shuffled(con, 101, "SH101"), cfg, iface, grid.TARGET_DRIVE,
                                         device=args.device)
            pilot_gains[name] = (c.forward_gain, c.turn_gain)
        return pilot_gains[name]

    times = {}
    for task, mapping in (("T0", "M0"), ("T1", "M0")):
        spec = grid.RunSpec(grid.Cell(task, mapping), "SH101", 0, 31_000, 40, (0,))
        spec = grid.RunSpec(spec.cell, "SH101", 0, 31_000, 40, (0,))
        rec = _execute_pilot(spec, con, remap_sets, args.device, out, gains_for)
        times[task] = rec["wall_seconds"]
        print(task, f"{rec['wall_seconds']:.0f}s end to end")
    per_run = float(np.mean(list(times.values())))
    runs = sum(len(b) for b in grid.run_schedule()) + 8  # continuation adds 40 generations each
    _json(grid.EXP02_DIR / "pilot.json", {"seconds_per_run": times, "projected_hours": per_run * runs / 3600})
    print(f"projected main-grid time: {per_run * runs / 3600:.1f} h")


def _execute_pilot(spec, con, remap_sets, device, out, gains_for):
    # SH101 is a pilot-only shuffle; graph_for does not know it, so build the run directly
    cfg = grid.task_config(Config(), spec.cell.task)
    cfg.world.forward_gain, cfg.world.turn_gain = gains_for("SH101")
    graph = shuffled(con, 101, "SH101")
    iface = grid.interface_for(con, spec.cell.mapping, remap_sets)
    bspec = BrainSpec.from_connectome(graph, device=device)
    t0 = time.perf_counter()
    res = evolve(cfg, iface, bspec, 0, spec.run_seed, device=device, holdout_every=10,
                 checkpoint_ids=grid.CHECKPOINT_IDS, snapshots=(0,), verbose=False)
    rollout(cfg, iface, res.snapshots[0], SeedPool(cfg, spec.run_seed).holdout, spec.run_seed, device)
    rollout(cfg, iface, res.champion, SeedPool(cfg, spec.run_seed).holdout, spec.run_seed, device)
    return {"wall_seconds": time.perf_counter() - t0}


def cmd_run(args, con, iface):
    remap_sets = _load(grid.EXP02_DIR / "remaps.json")["sets"]
    OUT.mkdir(parents=True, exist_ok=True)
    records_path = OUT / "records.jsonl"
    done = set()
    if records_path.exists():
        done = {json.loads(line)["key"] for line in records_path.read_text(encoding="utf-8").splitlines() if line}
    if not (OUT / "bundle.json").exists():
        write_bundle(OUT, grid.task_config(Config(), "T0"), con,
                     extra={"script": "exp02.py run", "remaps": remap_sets,
                            "calibration": _load(grid.EXP02_DIR / "calibration.json")})
    batches = grid.pending(grid.run_schedule(), done)
    budget = args.max_hours * 3600
    t_start = time.perf_counter()
    elapsed_before = sum(json.loads(l)["wall_seconds"] for l in records_path.read_text(encoding="utf-8").splitlines() if l) if records_path.exists() else 0.0
    per_batch = None
    for i, batch in enumerate(batches):
        elapsed = elapsed_before + (time.perf_counter() - t_start)
        if per_batch is not None and grid.select_batches(1, elapsed, per_batch, budget) == 0:
            print(f"stopping at a batch boundary: {elapsed / 3600:.2f} h used of {args.max_hours} h")
            break
        tb = time.perf_counter()
        for spec in batch:
            rec = _execute(spec, con, remap_sets, args.device, OUT)
            with records_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
            print(f"  {spec.key:28} holdout {np.mean(rec.get('holdout_g39', [np.nan])):.3f} "
                  f"{rec['wall_seconds']:.0f}s")
        per_batch = time.perf_counter() - tb if per_batch is None else max(per_batch, time.perf_counter() - tb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["remaps", "calibrate", "diagnostics", "pilot", "run"])
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--max-hours", type=float, default=10.5)
    args = ap.parse_args()
    con = load_connectome()
    iface = load_interface(con)
    {"remaps": cmd_remaps, "calibrate": cmd_calibrate, "diagnostics": cmd_diagnostics,
     "pilot": cmd_pilot, "run": cmd_run}[args.command](args, con, iface)


if __name__ == "__main__":
    main()
```

The runner's record fields `holdout_g00`, `holdout_g39` and (for continuation runs) `holdout_g79`
are per-world lists over the run's 64 held-out worlds. For a 40-generation run the generation-39
snapshot is its final champion (Task 8), so every run has `holdout_g39`.

- [ ] **Step 5: Run the tests and a CLI smoke check**

Run: `py -3.13 -m pytest tests/test_exp02_grid.py -q`
Expected: all PASS.
Run: `py -3.13 scripts/exp02.py remaps`
Expected: prints the four sets and writes `experiments/02-screening/remaps.json`.

- [ ] **Step 6: Commit**

```bash
git add wormwars/exp02/grid.py scripts/exp02.py tests/test_exp02_grid.py
git commit -m "Experiment 02 grid, schedule and resumable runner"
```

---

### Task 10: Probes

**Files:**
- Create: `wormwars/exp02/probes.py`
- Modify: `scripts/exp02.py` (add subcommand `probes`)
- Test: `tests/test_exp02_probes.py`

**Interfaces:**
- Consumes: Tasks 1-9.
- Produces: `flip_food_signs(genome, food_neurons) -> Genome`;
  `valence_check(spec, cfg, con, iface, n_strains, ids, seed, device, gaps: bool) -> dict`;
  `channel_dependence(cfg, iface, champion, ids, seed, device, with_pheromone: bool) -> dict[str, float]`;
  `input_response(spec, cfg, iface, n_strains, device, ticks=40) -> dict`;
  `integrator_rescore(cfg, iface, champion, ids, seed, device) -> dict[str, float]`;
  `behaviour(cfg, iface, champion, ids, seed, device) -> dict[str, float]`;
  `gen0_scores(spec, cfg, iface, n_strains, ids, seed, device) -> float`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_exp02_probes.py
"""Probes: the valence symmetry is exact without gap junctions; the others return sane numbers."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.exp02 import probes
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def small_cfg():
    c = Config()
    c.world.max_ticks = 60
    return c


def test_valence_symmetry_is_exact_without_gap_junctions(parts):
    con, iface, spec = parts
    r = probes.valence_check(spec, small_cfg(), con, iface, 4, np.arange(2), 3, "cpu", gaps=False)
    assert r["max_abs_score_diff"] <= 1e-5


def test_valence_with_gap_junctions_reports_a_discrepancy(parts):
    con, iface, spec = parts
    r = probes.valence_check(spec, small_cfg(), con, iface, 4, np.arange(2), 3, "cpu", gaps=True)
    assert np.isfinite(r["mean_abs_score_diff"])


def test_channel_dependence_returns_every_variant(parts):
    con, iface, spec = parts
    g = Genome.random(spec, Config().brain, 1, generator=torch.Generator().manual_seed(0))
    d = probes.channel_dependence(small_cfg(), iface, g, np.arange(2), 3, "cpu", with_pheromone=True)
    assert set(d) == {"real", "food_constant", "food_mirrored", "collision_off", "pheromone_off"}
    assert all(np.isfinite(v) for v in d.values())


def test_behaviour_is_finite_even_if_all_die(parts):
    con, iface, spec = parts
    cfg = small_cfg()
    cfg.world.metabolic_drain = 5.0  # everyone dies on the first tick
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(0))
    b = probes.behaviour(cfg, iface, g, np.arange(2), 3, "cpu")
    assert all(np.isfinite(v) for v in b.values())
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3.13 -m pytest tests/test_exp02_probes.py -q`
Expected: FAIL (`ImportError`).

- [ ] **Step 3: Implement `wormwars/exp02/probes.py`**

```python
"""Evaluation-only probes for experiment 02. None of these feeds back into selection."""

from __future__ import annotations

import numpy as np
import torch

from ..brain import Brain, Genome
from ..evo.rollout import rollout
from ..interface import interface_from_spec, negated_spec


def flip_food_signs(genome: Genome, food_neurons) -> Genome:
    """The sign-flip symmetry: negate the food neurons' voltages. With s = -1 on the food neurons
    and +1 elsewhere, w_ij -> s_i s_j w_ij and b_i -> s_i b_i, so an edge between two food neurons,
    or a food neuron's self-loop, keeps its sign."""
    spec = genome.spec
    s = torch.ones(spec.n, device=genome.device)
    s[torch.as_tensor(list(food_neurons), device=genome.device)] = -1.0
    w = genome.w * (s[spec.chem_i] * s[spec.chem_j]).unsqueeze(0)
    return Genome(spec, genome.cfg, w, genome.g.clone(), genome.tau.clone(), genome.bias * s,
                  genome.dale_sign)


def valence_check(spec, cfg, con, iface, n_strains, ids, seed, device, gaps: bool) -> dict:
    g = Genome.random(spec, cfg.brain, n_strains, generator=torch.Generator(device=device).manual_seed(seed), device=device)
    if not gaps:
        g = Genome(g.spec, g.cfg, g.w, torch.zeros_like(g.g), g.tau, g.bias, g.dale_sign)
    food = {int(i) for s, i in zip(iface.signal_names, iface.sensor_neuron) if s.startswith("food_")}
    neg = interface_from_spec(con, negated_spec(iface.raw, "food"))
    a = rollout(cfg, iface, g, ids, seed, device).score
    b = rollout(cfg, neg, flip_food_signs(g, food), ids, seed, device).score
    d = np.abs(a - b)
    return {"gaps": gaps, "max_abs_score_diff": float(d.max()), "mean_abs_score_diff": float(d.mean()),
            "mean_score": float(a.mean())}


def _variant(cfg, **world):
    c = cfg.copy()
    for k, v in world.items():
        setattr(c.world, k, v)
    return c


def channel_dependence(cfg, iface, champion, ids, seed, device, with_pheromone: bool) -> dict:
    variants = {
        "real": cfg,
        "food_constant": _variant(cfg, food_probe="constant"),
        "food_mirrored": _variant(cfg, food_probe="mirrored"),
        "collision_off": _variant(cfg, sense_scale_collision=0.0),
    }
    if with_pheromone:
        variants["pheromone_off"] = _variant(cfg, sense_scale_pheromone=0.0)
    return {k: float(rollout(c, iface, champion, ids, seed, device).score.mean()) for k, c in variants.items()}


def gen0_scores(spec, cfg, iface, n_strains, ids, seed, device) -> float:
    g = Genome.random(spec, cfg.brain, n_strains, generator=torch.Generator(device=device).manual_seed(seed), device=device)
    return float(rollout(cfg, iface, g, ids, seed, device).score.mean())


def input_response(spec, cfg, iface, n_strains, device, ticks=40) -> dict:
    """Motor read-out response of random brains to food input, outside the world: common-mode
    (both sides) and differential (left only), as |change from no input| over time."""
    g = Genome.random(spec, cfg.brain, n_strains, generator=torch.Generator(device=device).manual_seed(0), device=device)
    brain = Brain(g)
    names = list(iface.signal_names)
    left = [int(i) for s, i in zip(names, iface.sensor_neuron) if s == "food_left"]
    right = [int(i) for s, i in zip(names, iface.sensor_neuron) if s == "food_right"]
    fp, fm = iface.forward_plus, iface.forward_minus
    tp, tm = iface.turn_plus, iface.turn_minus

    def trace(lvl_l, lvl_r):
        v = brain.initial_state(1)
        cur = torch.zeros_like(v)
        cur[..., left] = lvl_l
        cur[..., right] = lvl_r
        out = []
        for _ in range(ticks):
            v = brain.step(v, cur)
            a = torch.tanh(v)
            out.append(torch.stack([a[..., fp].mean(-1) - a[..., fm].mean(-1),
                                    a[..., tp].mean(-1) - a[..., tm].mean(-1)], -1))
        return torch.stack(out)  # [ticks, S, 1, 2]

    base = trace(0.0, 0.0)
    cm = (trace(0.5, 0.5) - base).abs().mean(dim=(1, 2))
    df = (trace(0.5, 0.0) - base).abs().mean(dim=(1, 2))
    return {"common_forward": cm[:, 0].tolist(), "common_turn": cm[:, 1].tolist(),
            "diff_forward": df[:, 0].tolist(), "diff_turn": df[:, 1].tolist()}


def integrator_rescore(cfg, iface, champion, ids, seed, device) -> dict:
    out = {}
    for name, sub, eps in (("s32", 32, 0.0), ("s128", 128, 0.0), ("s32_perturbed", 32, 1e-6)):
        c = cfg.copy()
        c.brain.substeps = sub
        g = Genome(champion.spec, c.brain, champion.w, champion.g, champion.tau,
                   champion.bias + eps, champion.dale_sign)
        out[name] = float(rollout(c, iface, g, ids, seed, device).score.mean())
    return out


def behaviour(cfg, iface, champion, ids, seed, device) -> dict:
    from ..world import World

    n = len(ids)
    world = World(cfg, iface, Brain(champion), torch.zeros(n, 1, dtype=torch.long, device=device),
                  run_seed=seed, world_ids=np.asarray(ids), device=device)
    speed, turn_abs, wall, food, persist = [], [], [], [], []
    prev_turn = None
    while not world.done():
        pos0 = world.pos.clone()
        world.tick()
        alive = world.alive
        if not bool(alive.any()):
            break
        speed.append(float((world.pos - pos0).norm(dim=-1)[alive].mean()))
        t = world.last_turn
        turn_abs.append(float(t[alive].abs().mean()))
        if prev_turn is not None:
            persist.append(float((torch.sign(t) == torch.sign(prev_turn))[alive].float().mean()))
        prev_turn = t.clone()
        p = world.pos[alive]
        edge = torch.minimum(p, torch.tensor([world.W - 1.0, world.H - 1.0], device=p.device) - p).min(dim=-1).values
        wall.append(float((edge < 2.0).float().mean()))
        fx = world.fields[:, world.ch.FOOD]
        idx = world.pos.long().clamp(0, world.W - 1)
        wi = torch.arange(world.n_worlds, device=fx.device).view(-1, 1, 1).expand_as(idx[..., 0])
        on = fx[wi, idx[..., 1], idx[..., 0]] > 0.05
        food.append(float(on[alive].float().mean()))
    m = lambda xs: float(np.mean(xs)) if xs else 0.0  # noqa: E731
    return {"speed": m(speed), "turn_abs": m(turn_abs), "turn_persistence": m(persist),
            "near_wall": m(wall), "on_food": m(food)}
```

- [ ] **Step 4: Add the `probes` subcommand to `scripts/exp02.py`**

Add `"probes"` to the `choices`, the dispatch dict entry `"probes": cmd_probes`, and add
`from wormwars.exp02 import probes as P` and
`from wormwars.evo import load_genome` to the imports. Then:

```python
def cmd_probes(args, con, iface):
    remap_sets = _load(grid.EXP02_DIR / "remaps.json")["sets"]
    recs = [json.loads(l) for l in (OUT / "records.jsonl").read_text(encoding="utf-8").splitlines() if l]
    diag_ids = grid.CHECKPOINT_IDS
    out = {"valence": [], "gen0_strength": [], "input_response": {}, "champions": {}}
    # valence and generation-0 strength: T1 config, M0, N2 and SH1
    cfg1 = grid.task_config(Config(), "T1")
    for name in ("N2", "SH1"):
        cfg = grid.brain_config_for_graph(cfg1, name)
        cfg.world.forward_gain, cfg.world.turn_gain = _gains(name)
        spec = BrainSpec.from_connectome(grid.graph_for(con, name), device=args.device)
        for gaps in (False, True):
            out["valence"].append({"graph": name, **P.valence_check(spec, cfg, con, iface, 256, diag_ids, 7, args.device, gaps)})
    for name in ("N2", "SH1", "SH2", "SH3"):
        for mapping in ("M0", "R1", "R2", "MS"):
            fam = grid.interface_for(con, mapping, remap_sets)
            spec = BrainSpec.from_connectome(grid.graph_for(con, name), device=args.device)
            for mode in ("anatomical", "uniform", "permuted"):
                cfg = cfg1.copy()
                cfg.brain.init_chem_magnitude = cfg.brain.init_gap_magnitude = mode
                cfg.world.forward_gain, cfg.world.turn_gain = _gains(name)
                out["gen0_strength"].append({"graph": name, "mapping": mapping, "mode": mode,
                                             "score": P.gen0_scores(spec, cfg, fam, 128, diag_ids, 7, args.device)})
            out["input_response"][f"{name}-{mapping}"] = P.input_response(spec, cfg1, fam, 64, args.device)
    # per-champion probes
    for r in recs:
        cfg = grid.brain_config_for_graph(grid.task_config(Config(), r["task"]), r["graph"])
        cfg.world.forward_gain, cfg.world.turn_gain = _gains(r["graph"])
        fam = grid.interface_for(con, r["mapping"], remap_sets)
        spec = BrainSpec.from_connectome(grid.graph_for(con, r["graph"]), device=args.device)
        champ, meta = load_genome(OUT / f"{r['key']}-g39.npz", spec, None, device=args.device)
        from wormwars.exp02.manifest import check_manifest
        check_manifest(meta, cfg, fam, spec)
        out["champions"][r["key"]] = {
            "channels": P.channel_dependence(cfg, fam, champ, diag_ids, r["run_seed"], args.device, r["task"] == "A"),
            "integrator": P.integrator_rescore(cfg, fam, champ, diag_ids, r["run_seed"], args.device),
            "behaviour": P.behaviour(cfg, fam, champ, diag_ids[:4], r["run_seed"], args.device),
        }
    _json(OUT / "probes.json", out)
```

- [ ] **Step 5: Run the tests**

Run: `py -3.13 -m pytest tests/test_exp02_probes.py -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add wormwars/exp02/probes.py scripts/exp02.py tests/test_exp02_probes.py
git commit -m "Experiment 02 probes: valence symmetry, channels, strength, input response, integrator, behaviour"
```

---

### Task 11: Analysis, tripwires and report

**Files:**
- Create: `wormwars/exp02/analysis.py`
- Modify: `scripts/exp02.py` (add subcommand `report`)
- Test: `tests/test_exp02_analysis.py`

**Interfaces:**
- Consumes: runner records (Task 9), `diagnostics.json`, `probes.json`.
- Produces: `normalise(records, diagnostics) -> list[dict]` (adds `norm_g00`, `norm_g39` per record:
  mean over worlds of score / best scripted score on that world, with worlds where the best
  scripted score is 0 dropped); `units(records, measure) -> tuple[dict, dict]`
  (N2 units `{run: {cell: value}}`, SH `{graph: {run: {cell: value}}}`);
  `advantage(n2, sh, cell) -> float`; `interaction(n2, sh, task) -> float`;
  `task_contrast(n2, sh) -> float`;
  `paired_bootstrap(n2, sh, stat, n_boot=20000, seed=0) -> dict` (`mean, lo, hi`);
  `variance_components(sh, task) -> dict`; `leave_one_graph_out(n2, sh, task) -> dict`;
  `tripwires(summary) -> list[dict]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_exp02_analysis.py
"""Interaction estimates and the paired bootstrap, on synthetic data with known answers."""

from __future__ import annotations

import numpy as np

from wormwars.exp02 import analysis as A

CELLS = [("T0", "M0"), ("T0", "R1"), ("T0", "R2"), ("T1", "M0"), ("T1", "R1"), ("T1", "R2")]


def synth(effect_t1=0.2, unit_offset_sd=1.0, noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    n2, sh = {}, {}
    for r in range(4):
        off = rng.normal(0, unit_offset_sd)
        n2[r] = {c: off + (effect_t1 if c == ("T1", "M0") else 0.0) + rng.normal(0, noise) for c in CELLS}
    for k in range(6):
        sh[f"SH{k + 1}"] = {}
        for r in range(2):
            off = rng.normal(0, unit_offset_sd)
            sh[f"SH{k + 1}"][r] = {c: off + rng.normal(0, noise) for c in CELLS}
    return n2, sh


def test_interaction_recovers_the_planted_effect():
    n2, sh = synth(effect_t1=0.2, noise=0.0)
    assert abs(A.interaction(n2, sh, "T1") - 0.2) < 1e-9
    assert abs(A.interaction(n2, sh, "T0")) < 1e-9
    assert abs(A.task_contrast(n2, sh) - 0.2) < 1e-9


def test_unit_offsets_cancel_inside_the_bootstrap():
    # huge per-unit offsets, no noise: resampling whole unit vectors must leave the interaction exact
    n2, sh = synth(effect_t1=0.2, unit_offset_sd=10.0, noise=0.0)
    b = A.paired_bootstrap(n2, sh, lambda a, s: A.interaction(a, s, "T1"), n_boot=500)
    assert abs(b["lo"] - 0.2) < 1e-9 and abs(b["hi"] - 0.2) < 1e-9


def test_bootstrap_interval_covers_the_truth_under_noise():
    n2, sh = synth(effect_t1=0.2, unit_offset_sd=1.0, noise=0.05, seed=3)
    b = A.paired_bootstrap(n2, sh, lambda a, s: A.interaction(a, s, "T1"), n_boot=2000)
    assert b["lo"] < 0.2 < b["hi"]


def test_normalise_drops_worlds_where_the_reference_is_zero():
    recs = [{"task": "T0", "run_seed": 1, "holdout_g00": [0.5, 0.4], "holdout_g39": [1.0, 0.8]}]
    diag = {"T0": {"per_seed_holdout": {"1": {"a": [1.0, 0.0], "b": [0.5, 0.0]}}}}
    out = A.normalise(recs, diag)
    assert out[0]["norm_g39"] == 1.0 and out[0]["norm_g00"] == 0.5
    diag0 = {"T0": {"per_seed_holdout": {"1": {"a": [0.0, 0.0]}}}}
    assert np.isnan(A.normalise(recs, diag0)[0]["norm_g39"])


def test_variance_components_are_non_negative_and_named():
    _, sh = synth(noise=0.1)
    v = A.variance_components(sh, "T1")
    assert set(v) == {"between_graph", "within_graph"} and min(v.values()) >= 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3.13 -m pytest tests/test_exp02_analysis.py -q`
Expected: FAIL (`ImportError`).

- [ ] **Step 3: Implement `wormwars/exp02/analysis.py`**

```python
"""Experiment 02 analysis: interaction, task contrast, paired bootstrap, variance components.

Resampling units are whole replicate vectors. An N2 run, or an SH graph's run, carries its value
in every cell together, because every cell uses the same seed for that unit. SH graphs are
resampled first, then runs within each graph. Remaps are crossed with graphs, never nested.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

MATCHED = ("R1", "R2")


def normalise(records, diagnostics) -> list[dict]:
    out = []
    for r in records:
        per = diagnostics[r["task"]]["per_seed_holdout"][str(r["run_seed"])]
        best = np.max(np.array(list(per.values())), axis=0)
        keep = best > 0
        r = dict(r)
        for tag in ("g00", "g39", "g79"):
            key = f"holdout_{tag}"
            if key in r:
                x = np.asarray(r[key])
                r[f"norm_{tag}"] = float(np.mean(x[keep] / best[keep])) if keep.any() else float("nan")
        out.append(r)
    return out


def units(records, measure: str):
    n2: dict = defaultdict(dict)
    sh: dict = defaultdict(lambda: defaultdict(dict))
    for r in records:
        cell = (r["task"], r["mapping"])
        if r["graph"] == "N2":
            n2[r["run"]][cell] = r[measure]
        elif r["graph"].startswith("SH"):
            sh[r["graph"]][r["run"]][cell] = r[measure]
    return dict(n2), {g: dict(v) for g, v in sh.items()}


def _n2_mean(n2, cell):
    v = [u[cell] for u in n2.values() if cell in u]
    return float(np.mean(v))


def _sh_mean(sh, cell):
    per_graph = [np.mean([u[cell] for u in runs.values() if cell in u]) for runs in sh.values()]
    return float(np.mean(per_graph))


def advantage(n2, sh, cell) -> float:
    return _n2_mean(n2, cell) - _sh_mean(sh, cell)


def interaction(n2, sh, task: str) -> float:
    a0 = advantage(n2, sh, (task, "M0"))
    return a0 - float(np.mean([advantage(n2, sh, (task, m)) for m in MATCHED]))


def task_contrast(n2, sh) -> float:
    return interaction(n2, sh, "T1") - interaction(n2, sh, "T0")


def paired_bootstrap(n2, sh, stat, n_boot: int = 20000, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    n2_keys = list(n2)
    graphs = list(sh)
    samples = np.empty(n_boot)
    for b in range(n_boot):
        rn2 = {i: n2[k] for i, k in enumerate(rng.choice(n2_keys, len(n2_keys)))}
        rsh = {}
        for j, gk in enumerate(rng.choice(graphs, len(graphs))):
            runs = list(sh[gk])
            rsh[f"g{j}"] = {i: sh[gk][r] for i, r in enumerate(rng.choice(runs, len(runs)))}
        samples[b] = stat(rn2, rsh)
    return {"estimate": float(stat(n2, sh)), "lo": float(np.quantile(samples, 0.025)),
            "hi": float(np.quantile(samples, 0.975))}


def _unit_contrast(u, task):
    return u[(task, "M0")] - np.mean([u[(task, m)] for m in MATCHED])


def variance_components(sh, task: str) -> dict:
    """One-way random-effects ANOVA on SH's per-unit mapping contrast: graphs x runs."""
    groups = [[_unit_contrast(u, task) for u in runs.values()] for runs in sh.values()]
    k, n = len(groups), len(groups[0])
    means = [np.mean(g) for g in groups]
    msb = n * np.var(means, ddof=1) if k > 1 else 0.0
    msw = np.mean([np.var(g, ddof=1) for g in groups]) if n > 1 else 0.0
    return {"between_graph": float(max((msb - msw) / n, 0.0)), "within_graph": float(max(msw, 0.0))}


def leave_one_graph_out(n2, sh, task: str) -> dict:
    return {g: interaction(n2, {k: v for k, v in sh.items() if k != g}, task) for g in sh}


def tripwires(summary: dict) -> list[dict]:
    """Each entry: name, fired (bool), detail. `summary` is assembled by the report command."""
    t = []
    ch = summary["t1_channel_drop"]  # interval of (real - food_constant) on T1 champions
    t.append({"name": "T1 depends on food history", "fired": ch["lo"] <= 0, "detail": ch})
    mem = summary["t1_memory_vs_memoryless"]  # interval of (one_step_memory - level_kinesis)
    t.append({"name": "memory controller beats memoryless on T1", "fired": mem["lo"] <= 0, "detail": mem})
    t.append({"name": "anchor sign replicates 01b", "fired": summary["anchor_advantage"]["estimate"] <= 0,
              "detail": summary["anchor_advantage"]})
    t.append({"name": "drive within calibration tolerance", "fired": summary["max_drive_error"] > 0.02,
              "detail": summary["max_drive_error"]})
    integ = summary["integrator"]
    t.append({"name": "integrator shift within chaos floor",
              "fired": integ["interaction_shift"] > integ["chaos_floor"], "detail": integ})
    t.append({"name": "90% of asymptote by generation 40", "fired": summary["late_cells"] > 7 / 3,
              "detail": summary["late_cells"]})
    t.append({"name": "shortcut remap moves N2 more than matched remaps",
              "fired": summary["ms_vs_matched"]["lo"] > 0 or summary["ms_vs_matched"]["hi"] < 0,
              "detail": summary["ms_vs_matched"]})
    t.append({"name": "R1 and R2 agree", "fired": summary["r1_minus_r2"]["lo"] > 0 or summary["r1_minus_r2"]["hi"] < 0,
              "detail": summary["r1_minus_r2"]})
    t.append({"name": "SH indifferent to mapping", "fired": summary["sh_mapping"]["lo"] > 0 or summary["sh_mapping"]["hi"] < 0,
              "detail": summary["sh_mapping"]})
    t.append({"name": "valence symmetry exact without gaps", "fired": summary["valence_no_gap_max"] > 1e-5,
              "detail": summary["valence_no_gap_max"]})
    return t
```

- [ ] **Step 4: Add the `report` subcommand to `scripts/exp02.py`**

Add `"report"` to `choices` and the dispatch dict (`"report": cmd_report`), and
`from wormwars.exp02 import analysis as An` to the imports. Then:

```python
def cmd_report(args, con, iface):
    recs = [json.loads(l) for l in (OUT / "records.jsonl").read_text(encoding="utf-8").splitlines() if l]
    diag = _load(grid.EXP02_DIR / "diagnostics.json")
    prb = _load(OUT / "probes.json")
    cal = _load(grid.EXP02_DIR / "calibration.json")
    recs = An.normalise(recs, diag)
    out = {}
    for tag in ("norm_g00", "norm_g39"):
        n2, sh = An.units([r for r in recs if r["task"] != "A"], tag)
        out[tag] = {
            "I_T0": An.paired_bootstrap(n2, sh, lambda a, s: An.interaction(a, s, "T0")),
            "I_T1": An.paired_bootstrap(n2, sh, lambda a, s: An.interaction(a, s, "T1")),
            "I_T1_minus_I_T0": An.paired_bootstrap(n2, sh, An.task_contrast),
            "variance_T0": An.variance_components(sh, "T0"),
            "variance_T1": An.variance_components(sh, "T1"),
            "loo_T1": An.leave_one_graph_out(n2, sh, "T1"),
        }
    n2, sh = An.units(recs, "norm_g39")
    ms = lambda a, s: An.advantage(a, s, ("T1", "MS")) - np.mean([An.advantage(a, s, ("T1", m)) for m in An.MATCHED])  # noqa: E731
    r12 = lambda a, s: An.advantage(a, s, ("T1", "R1")) - An.advantage(a, s, ("T1", "R2"))  # noqa: E731
    shmap = lambda a, s: An._sh_mean(s, ("T1", "M0")) - np.mean([An._sh_mean(s, ("T1", m)) for m in An.MATCHED])  # noqa: E731
    anchor = lambda a, s: An.advantage(a, s, ("A", "M0"))  # noqa: E731
    champs = prb["champions"]
    t1 = [k for k in champs if k.startswith("T1-")]
    drops = np.array([champs[k]["channels"]["real"] - champs[k]["channels"]["food_constant"] for k in t1])
    boot = np.random.default_rng(0).choice(drops, (20000, len(drops))).mean(axis=1)
    integ_shift = []
    floor = []
    for k, v in champs.items():
        integ_shift.append(abs(v["integrator"]["s128"] - v["integrator"]["s32"]))
        floor.append(abs(v["integrator"]["s32_perturbed"] - v["integrator"]["s32"]))
    t1_memory = diag["T1"]["tuned"]
    summary = {
        "t1_channel_drop": {"estimate": float(drops.mean()), "lo": float(np.quantile(boot, 0.025)), "hi": float(np.quantile(boot, 0.975))},
        "t1_memory_vs_memoryless": {"estimate": t1_memory["one_step_memory"]["tuning_score"] - t1_memory["level_kinesis"]["tuning_score"],
                                    "lo": t1_memory["one_step_memory"]["tuning_score"] - t1_memory["level_kinesis"]["tuning_score"],
                                    "hi": t1_memory["one_step_memory"]["tuning_score"] - t1_memory["level_kinesis"]["tuning_score"]},
        "anchor_advantage": An.paired_bootstrap(n2, sh, anchor),
        "max_drive_error": max(max(abs(c["achieved"]["forward"] / c["target"][0] - 1), abs(c["achieved"]["turn"] / c["target"][1] - 1)) for c in cal.values()),
        "integrator": {"interaction_shift": float(np.mean(integ_shift)), "chaos_floor": float(np.mean(floor))},
        "late_cells": 0,
        "ms_vs_matched": An.paired_bootstrap(n2, sh, ms),
        "r1_minus_r2": An.paired_bootstrap(n2, sh, r12),
        "sh_mapping": An.paired_bootstrap(n2, sh, shmap),
        "valence_no_gap_max": max(v["max_abs_score_diff"] for v in prb["valence"] if not v["gaps"]),
    }
    out["summary"] = summary
    out["tripwires"] = An.tripwires(summary)
    _json(OUT / "analysis.json", out)
    for t in out["tripwires"]:
        print(f"{'FIRED' if t['fired'] else 'ok   '}  {t['name']}")
```

The `late_cells` entry is computed in the report from the checkpoint curves: fit
`y = a - b * exp(-g / c)` to each cell's mean checkpoint curve (`scipy.optimize.curve_fit`),
and count cells whose 90%-of-asymptote generation exceeds 40. Implement it as
`An.late_cells(recs)` with its own test before replacing the `0`:

```python
def late_cells(records, threshold_gen: int = 40) -> int:
    from scipy.optimize import curve_fit

    curves = defaultdict(list)
    for r in records:
        if r["checkpoints"]:
            curves[(r["task"], r["mapping"])].append(dict(r["checkpoints"]))
    late = 0
    for cell, cs in curves.items():
        gens = sorted(set.intersection(*(set(c) for c in cs)))
        y = np.array([np.mean([c[g] for c in cs]) for g in gens], dtype=float)
        x = np.array(gens, dtype=float)
        try:
            (a, b, c), _ = curve_fit(lambda g, a, b, c: a - b * np.exp(-g / c), x, y,
                                     p0=(y[-1], y[-1] - y[0], 10.0), maxfev=20000)
            g90 = -c * np.log(0.1) if b > 0 and c > 0 else 0.0
        except RuntimeError:
            g90 = float("inf")
        late += int(g90 > threshold_gen)
    return late
```

with the test

```python
def test_late_cells_counts_slow_curves():
    fast = {"task": "T0", "mapping": "M0", "checkpoints": [(g, 1 - np.exp(-g / 3)) for g in (0, 10, 20, 30, 39)]}
    slow = {"task": "T1", "mapping": "M0", "checkpoints": [(g, 1 - np.exp(-g / 40)) for g in (0, 10, 20, 30, 39)]}
    assert A.late_cells([fast, slow]) == 1
```

Then set `"late_cells": An.late_cells(recs)` in the summary.

- [ ] **Step 5: Run the tests**

Run: `py -3.13 -m pytest tests/test_exp02_analysis.py -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add wormwars/exp02/analysis.py scripts/exp02.py tests/test_exp02_analysis.py
git commit -m "Experiment 02 analysis: paired bootstrap, interaction, variance components, tripwires"
```

---

### Task 12: Frozen inputs, pilot, and the pre-registration

- [ ] **Step 1:** Run `py -3.13 -m pytest -q`. Expected: all PASS.
- [ ] **Step 2:** Run `py -3.13 scripts/exp02.py remaps`. Record R1, R2 and MS in the
  pre-registration with their feature table and distances.
- [ ] **Step 3:** Run `py -3.13 scripts/exp02.py calibrate`. Check that every graph converged
  within 2% and that the seed-1 validation is within 5%. If not, stop and treat it as a failure
  mode (DECISIONS entry).
- [ ] **Step 4:** Run `py -3.13 scripts/exp02.py diagnostics`. Check the T1 tripwire on scripted
  controllers now, before any N2 run: if the tuned memoryless controller matches the memory
  controller, redesign T1 before pre-registering.
- [ ] **Step 5:** Run `py -3.13 scripts/exp02.py pilot` (SH101 only, discarded). Set
  `--max-hours` for the run so that the projected total plus probes fits in 12 hours; apply the
  design's cut order if it does not.
- [ ] **Step 6:** Write `experiments/02-screening/PREREGISTRATION.md`: design as run (the chosen
  remap sets, gains, controller parameters and budget), the estimates, the tripwires with their
  consequences, what the screening can and cannot conclude, and the stop rule. Commit it.
- [ ] **Step 7:** Consult Astra 6 and Fable 5.1 on the pre-registration (read-only, via
  `~/.claude/skills/consult/consult.py`). Verify each point, revise, and record the review in
  DECISIONS. Commit before any N2 run.

### Task 13: Run, probe, report

- [ ] **Step 1:** `py -3.13 scripts/exp02.py run --max-hours <from pilot>` in the background.
  It resumes safely if interrupted.
- [ ] **Step 2:** `py -3.13 scripts/exp02.py probes`.
- [ ] **Step 3:** `py -3.13 scripts/exp02.py report`. Check the ledger errors in the logs and the
  manifest checks (probes load every champion through `check_manifest`).
- [ ] **Step 4:** Commit `runs/exp02-screening` records, champions, bundle, probes and analysis.
  Add `.gitignore` exceptions for its `*.npz` champions. Run the hygiene tests before committing.

### Task 14: Write-up and review

- [ ] **Step 1:** Write `experiments/02-screening/RESULTS.md`: pre-registered estimates first,
  exploratory analyses separately, every tripwire whether it fired or not, and what each result
  changes for the full design.
- [ ] **Step 2:** Consult Astra 6 and Fable 5.1 on the results. Verify, fix, and record the
  review (DECISIONS, `docs/REVIEW_TRAIL.md`).
- [ ] **Step 3:** Update the README and memory. Commit locally. **Do not push.** Report to the user.
