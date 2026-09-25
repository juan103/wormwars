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
    or a food neuron's self-loop, keeps its sign. Exact without gap junctions; a gap junction
    between a food neuron and any other neuron couples raw voltages and breaks it."""
    spec = genome.spec
    s = torch.ones(spec.n, device=genome.device)
    s[torch.as_tensor(sorted(food_neurons), device=genome.device)] = -1.0
    w = genome.w * (s[spec.chem_i] * s[spec.chem_j]).unsqueeze(0)
    return Genome(spec, genome.cfg, w, genome.g.clone(), genome.tau.clone(), genome.bias * s,
                  genome.dale_sign)


def valence_check(spec, cfg, con, iface, n_strains, ids, seed, device, gaps: bool) -> dict:
    gen = torch.Generator(device=device).manual_seed(seed)
    g = Genome.random(spec, cfg.brain, n_strains, generator=gen, device=device)
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
    """Mean score with the real food signal, with it replaced by a constant, with it replaced by
    the distribution-matched mirrored signal, and with collision (and pheromone) sensing off."""
    variants = {
        "real": cfg,
        "food_constant": _variant(cfg, food_probe="constant"),
        "food_mirrored": _variant(cfg, food_probe="mirrored"),
        "collision_off": _variant(cfg, sense_scale_collision=0.0),
    }
    if with_pheromone:
        variants["pheromone_off"] = _variant(cfg, sense_scale_pheromone=0.0)
    # capability use: history (jitter, D037: 1 cell is the scripted-validated ablation; 3 cells
    # reaches brains that integrate over many ticks) and, for stereo tasks, the second nose
    variants["jitter1"] = _variant(cfg, food_probe="jitter", food_probe_radius=1.0)
    variants["jitter3"] = _variant(cfg, food_probe="jitter", food_probe_radius=3.0)
    if cfg.world.food_sensing == "stereo":
        variants["mono"] = _variant(cfg, food_sensing="mono")
    return {k: float(rollout(c, iface, champion, ids, seed, device).score.mean())
            for k, c in variants.items()}


def gen0_scores(spec, cfg, iface, n_strains, ids, seed, device) -> float:
    gen = torch.Generator(device=device).manual_seed(seed)
    g = Genome.random(spec, cfg.brain, n_strains, generator=gen, device=device)
    return float(rollout(cfg, iface, g, ids, seed, device).score.mean())


def input_response(spec, cfg, iface, n_strains, device, ticks=40) -> dict:
    """Motor read-out response of random brains to food input, outside the world: common-mode
    (both sides) and differential (left only), as mean |change from no input| per tick."""
    gen = torch.Generator(device=device).manual_seed(0)
    g = Genome.random(spec, cfg.brain, n_strains, generator=gen, device=device)
    brain = Brain(g)
    names = list(iface.signal_names)
    left = [int(i) for s, i in zip(names, iface.sensor_neuron) if s == "food_left"]
    right = [int(i) for s, i in zip(names, iface.sensor_neuron) if s == "food_right"]
    fp, fm = list(iface.forward_plus), list(iface.forward_minus)
    tp, tm = list(iface.turn_plus), list(iface.turn_minus)

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
    """Per-world scores at 32 and 128 substeps, and at 32 with every bias moved by 1e-6. The last
    is the chaos floor: a persistent parameter perturbation, not a perturbation of the initial
    state, standing for any difference too small to matter that chaotic dynamics amplify."""
    out = {}
    for name, sub, eps in (("s32", 32, 0.0), ("s128", 128, 0.0), ("s32_bias_perturbed", 32, 1e-6)):
        c = cfg.copy()
        c.brain.substeps = sub
        g = Genome(champion.spec, c.brain, champion.w, champion.g, champion.tau,
                   champion.bias + eps, champion.dale_sign)
        out[name] = rollout(c, iface, g, ids, seed, device).score[0].tolist()
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
        far = torch.tensor([world.W - 1.0, world.H - 1.0], device=p.device)
        edge = torch.minimum(p, far - p).min(dim=-1).values
        wall.append(float((edge < 2.0).float().mean()))
        fx = world.fields[:, world.ch.FOOD]
        idx = world.pos.long().clamp(0, world.W - 1)
        wi = torch.arange(world.n_worlds, device=fx.device).view(-1, 1, 1).expand_as(idx[..., 0])
        on = fx[wi, idx[..., 1], idx[..., 0]] > 0.05
        food.append(float(on[alive].float().mean()))
    m = lambda xs: float(np.mean(xs)) if xs else 0.0  # noqa: E731
    return {"speed": m(speed), "turn_abs": m(turn_abs), "turn_persistence": m(persist),
            "near_wall": m(wall), "on_food": m(food)}
