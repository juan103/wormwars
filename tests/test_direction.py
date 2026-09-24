"""Chemical synapses must carry signal from the presynaptic to the postsynaptic neuron.

Experiment 01 ran with them reversed (DECISIONS.md D031): `Genome.dense` stores `W[pre, post]` and
`Brain.step` multiplied by its transpose, so drive flowed post -> pre. Nothing caught it because no
test ever sent a signal down a single synapse and looked where it arrived. These tests do.

The reversed behaviour is kept, behind `chem_direction = "post_to_pre"`, only so that experiment 01
reproduces exactly as published. Anything saved before the fix carries no direction field and is
read as reversed; everything new is `pre_to_post`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import torch
import yaml

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import BrainConfig, Config
from wormwars.connectome import load_connectome

ROOT = Path(__file__).resolve().parents[1]
EXP01_RUN = ROOT / "runs" / "m9-calibrated"
EXP01B_RUN = ROOT / "runs" / "exp01b-direction-corrected"


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def spec(con) -> BrainSpec:
    return BrainSpec.from_connectome(con)


def _one_way_edge(con, spec) -> tuple[int, int, int]:
    """A real edge a -> b with no b -> a synapse and no gap junction between them."""
    chem = con.chem > 0
    for k in range(spec.n_chem):
        a, b = int(spec.chem_i[k]), int(spec.chem_j[k])
        if a != b and not chem[b, a] and con.gap[a, b] == 0:
            return k, a, b
    raise AssertionError("no one-way edge found")


def _single_synapse_brain(con, spec, direction: str):
    """Every weight zero except one excitatory synapse a -> b; no gap, no bias."""
    k, a, b = _one_way_edge(con, spec)
    cfg = BrainConfig(chem_direction=direction)
    g = Genome.random(spec, cfg, 1, generator=torch.Generator().manual_seed(0))
    with torch.no_grad():
        g.w.zero_()
        g.w[0, k] = 2.0
        g.g.zero_()
        g.bias.zero_()
        g.tau.fill_(1.0)
    return Brain(g), a, b


def _respond(brain: Brain, driven: int, ticks: int = 20) -> torch.Tensor:
    v = brain.initial_state(1)
    cur = torch.zeros_like(v)
    cur[0, 0, driven] = 3.0
    for _ in range(ticks):
        v = brain.step(v, cur)
    return v[0, 0]


def test_chemical_synapse_carries_signal_from_pre_to_post(con, spec):
    brain, a, b = _single_synapse_brain(con, spec, "pre_to_post")
    assert BrainConfig().chem_direction == "pre_to_post", "the default must be the correct direction"
    assert _respond(brain, a)[b] > 0.5, "driving the presynaptic neuron must drive the postsynaptic one"
    assert _respond(brain, b)[a] == 0.0, "driving the postsynaptic neuron must not reach back"


def test_legacy_direction_runs_post_to_pre(con, spec):
    """What experiment 01 actually ran. Kept only so it reproduces."""
    brain, a, b = _single_synapse_brain(con, spec, "post_to_pre")
    assert _respond(brain, a)[b] == 0.0
    assert _respond(brain, b)[a] > 0.5


def test_legacy_mode_is_exactly_the_original_formula(spec):
    """Legacy mode must be the pre-fix update, operation for operation, not an approximation."""
    cfg = BrainConfig(chem_direction="post_to_pre")
    g = Genome.random(spec, cfg, 3, generator=torch.Generator().manual_seed(5))
    brain = Brain(g)
    gen = torch.Generator().manual_seed(9)
    v0 = torch.randn(3, 6, spec.n, generator=gen) * 0.5
    cur = torch.randn(3, 6, spec.n, generator=gen) * 0.5

    # the update exactly as it was written before the fix
    W, G = g.dense()
    c = (cfg.dt / g.tau).unsqueeze(1)
    den = (1.0 + (cfg.dt / g.tau) * (1.0 + G.sum(dim=2))).unsqueeze(1)
    drive = g.bias.unsqueeze(1) + cur
    Wt = W.transpose(1, 2)
    v = v0.clone()
    for _ in range(cfg.substeps):
        chem = torch.bmm(torch.tanh(v), Wt)
        gap = torch.bmm(v, G)
        v = (v + c * (drive + chem + gap)) / den

    assert torch.equal(brain.step(v0.clone(), cur), v)


def test_an_unknown_direction_is_an_error(spec):
    g = Genome.random(spec, BrainConfig(chem_direction="sideways"), 1,
                      generator=torch.Generator().manual_seed(0))
    with pytest.raises(ValueError, match="chem_direction"):
        Brain(g)


def test_an_ordinary_config_without_the_field_is_the_correct_direction(tmp_path):
    """A partial config must never silently bring the bug back (review finding, D033).

    Only a config recorded by a past run may be read as reversed, and only through
    `Config.from_bundle`. `from_dict` and `from_yaml` treat a missing field as the default.
    """
    assert Config.from_dict({}).brain.chem_direction == "pre_to_post"
    assert Config.from_dict({"world": {"max_ticks": 10}}).brain.chem_direction == "pre_to_post"
    assert Config.from_dict({"brain": {"substeps": 8}}).brain.chem_direction == "pre_to_post"
    partial = tmp_path / "partial.yaml"
    partial.write_text("evo:\n  generations: 3\n", encoding="utf-8")
    assert Config.from_yaml(partial).brain.chem_direction == "pre_to_post"
    assert Config.from_yaml().brain.chem_direction == "pre_to_post"
    # and every shipped simulation config loads correct, brain section or not
    import dataclasses

    sections = {f.name for f in dataclasses.fields(Config)}
    checked = 0
    for path in (ROOT / "configs").glob("*.yaml"):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not set(raw) <= sections:  # e.g. interface.yaml, which is not a simulation config
            continue
        assert Config.from_dict(raw).brain.chem_direction == "pre_to_post", path.name
        checked += 1
    assert checked >= 1


def test_run_bundles_are_read_as_what_they_ran(spec):
    """01's bundle has no direction field and ran reversed; 01b's states the correct one."""
    old = json.loads((EXP01_RUN / "bundle.json").read_text(encoding="utf-8"))
    assert "chem_direction" not in old["config"]["brain"]
    assert Config.from_bundle(old["config"]).brain.chem_direction == "post_to_pre"
    new = json.loads((EXP01B_RUN / "bundle.json").read_text(encoding="utf-8"))
    assert Config.from_bundle(new["config"]).brain.chem_direction == "pre_to_post"

    from wormwars.evo import load_genome

    genome, _ = load_genome(EXP01_RUN / "champion-N2-run00.npz", spec, None)
    assert genome.cfg.chem_direction == "post_to_pre"
    genome, _ = load_genome(EXP01B_RUN / "champion-N2-run00.npz", spec, None)
    assert genome.cfg.chem_direction == "pre_to_post"


@pytest.mark.skipif(not torch.cuda.is_available(), reason="01 was scored on CUDA; bit-exactness needs it")
def test_legacy_mode_reproduces_a_published_experiment_01_score_exactly(con):
    """The reproduction claim in D031, made checkable (review finding, D033).

    Replays 01's N2 run-0 champion, in legacy mode, on its own 32 held-out worlds, and requires the
    held-out score stored in the champion file to the last bit.
    """
    from wormwars.evo import SeedPool, load_genome, rollout
    from wormwars.interface import load_interface

    bundle = json.loads((EXP01_RUN / "bundle.json").read_text(encoding="utf-8"))
    cfg = Config.from_bundle(bundle["config"])
    # 01's champion files predate per-genome gain metadata; the bundle recorded the gains
    gains = bundle["graphs"]["N2"]["calibration"]
    cfg.world.forward_gain, cfg.world.turn_gain = gains["forward_gain"], gains["turn_gain"]
    path = EXP01_RUN / "champion-N2-run00.npz"
    spec = BrainSpec.from_connectome(con, device="cuda")
    genome, meta = load_genome(path, spec, None, device="cuda")
    assert genome.cfg.chem_direction == "post_to_pre"
    seed = int(meta["run_seed"])
    held = rollout(cfg, load_interface(con), genome, SeedPool(cfg, seed).holdout, seed, "cuda")
    assert float(held.per_strain()[0]) == meta["holdout_score"]


def test_a_genome_is_never_replayed_under_the_other_direction(spec, tmp_path):
    from wormwars.evo import load_genome, save_genome

    legacy = Genome.random(spec, BrainConfig(chem_direction="post_to_pre"), 1,
                           generator=torch.Generator().manual_seed(1))
    path = save_genome(tmp_path / "old.npz", legacy)
    with pytest.raises(ValueError, match="chem_direction"):
        load_genome(path, spec, BrainConfig())  # default is pre_to_post
    back, _ = load_genome(path, spec, BrainConfig(chem_direction="post_to_pre"))
    assert back.cfg.chem_direction == "post_to_pre"
