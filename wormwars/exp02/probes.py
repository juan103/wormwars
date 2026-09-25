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
    """Per-world scores of one champion with the real food signal and under each intervention:
    food replaced by each world's tick-0 mean level ("constant"), by the mirrored signal,
    collision (and pheromone) sensing off, and the history-sensitivity jitters. Stereo tasks
    add the stereo ablations: the bilateral mean (the primary one, removing only the left-right
    difference), the left-right swap, and single-nose substitution ("mono", which also moves the
    sample point). Jitter draws come from a generator seeded by `seed`, recorded as probe_seed."""
    variants = {
        "real": cfg,
        "food_constant": _variant(cfg, food_probe="constant"),
        "food_mirrored": _variant(cfg, food_probe="mirrored"),
        "collision_off": _variant(cfg, sense_scale_collision=0.0),
    }
    if with_pheromone:
        variants["pheromone_off"] = _variant(cfg, sense_scale_pheromone=0.0)
    # history sensitivity (D037, D038): 1 cell is the scripted-validated ablation; 3 cells also
    # costs a memoryless controller, so it is a sensitivity outcome only
    variants["jitter1"] = _variant(cfg, food_probe="jitter", food_probe_radius=1.0)
    variants["jitter3"] = _variant(cfg, food_probe="jitter", food_probe_radius=3.0)
    if cfg.world.food_sensing == "stereo":
        variants["mono"] = _variant(cfg, food_sensing="mono")
        variants["food_mean"] = _variant(cfg, food_probe="mean")
        variants["food_swapped"] = _variant(cfg, food_probe="swapped")
    return {"world_ids": [int(i) for i in ids], "probe_seed": int(seed),
            "scores": {k: rollout(c, iface, champion, ids, seed, device).score[0].tolist()
                       for k, c in variants.items()}}


def gen0_scores(spec, cfg, iface, n_strains, ids, seed, device) -> float:
    gen = torch.Generator(device=device).manual_seed(seed)
    g = Genome.random(spec, cfg.brain, n_strains, generator=gen, device=device)
    return float(rollout(cfg, iface, g, ids, seed, device).score.mean())


def input_response(spec, cfg, iface, n_strains, device, ticks=40, base=0.1, diff=0.05) -> dict:
    """Motor response of random brains to food input, outside the world, per tick.

    Levels are sensed-signal units (after sense_scale_food), injected through the interface's
    sensor gains, input_gain and input clamp as in the world. Common mode: (b, b) against (0, 0).
    Directional (Astra's decision review, point 3): (b+d, b-d) against (b-d, b+d), half the
    difference, so the total food level is identical in both. Positive signed turn means turning
    toward the stronger side, the scripted stereo controller's convention. Each is reported for
    the raw read-out and for the motor command after the world's gains and clip."""
    gen = torch.Generator(device=device).manual_seed(0)
    g = Genome.random(spec, cfg.brain, n_strains, generator=gen, device=device)
    brain = Brain(g)
    names = list(iface.signal_names)
    gains = np.asarray(iface.sensor_gain) * cfg.brain.input_gain
    left = [(int(i), float(k)) for s, i, k in zip(names, iface.sensor_neuron, gains) if s == "food_left"]
    right = [(int(i), float(k)) for s, i, k in zip(names, iface.sensor_neuron, gains) if s == "food_right"]
    fp, fm = list(iface.forward_plus), list(iface.forward_minus)
    tp, tm = list(iface.turn_plus), list(iface.turn_minus)
    motor_scale = torch.tensor([cfg.world.forward_gain, cfg.world.turn_gain], device=device) * 0.5

    def trace(lvl_l, lvl_r):
        v = brain.initial_state(1)
        cur = torch.zeros_like(v)
        for j, k in left:
            cur[..., j] += lvl_l * k
        for j, k in right:
            cur[..., j] += lvl_r * k
        cur = cur.clamp(-cfg.brain.input_max, cfg.brain.input_max)
        out = []
        for _ in range(ticks):
            v = brain.step(v, cur)
            a = torch.tanh(v)
            out.append(torch.stack([a[..., fp].mean(-1) - a[..., fm].mean(-1),
                                    a[..., tp].mean(-1) - a[..., tm].mean(-1)], -1))
        raw = torch.stack(out).reshape(ticks, -1, 2)  # [ticks, strains, (forward, turn)]
        return {"raw": raw, "motor": (raw * motor_scale).clamp(-1, 1)}

    zero, both = trace(0.0, 0.0), trace(base, base)
    toward_l, toward_r = trace(base + diff, base - diff), trace(base - diff, base + diff)
    out = {}
    for kind in ("raw", "motor"):
        common = (both[kind] - zero[kind]).abs().mean(1)
        direc = (toward_l[kind] - toward_r[kind]) / 2
        out[f"common_forward_{kind}"] = common[:, 0].tolist()
        out[f"common_turn_{kind}"] = common[:, 1].tolist()
        out[f"directional_forward_{kind}"] = direc[..., 0].abs().mean(1).tolist()
        out[f"directional_turn_{kind}"] = direc[..., 1].abs().mean(1).tolist()
        out[f"directional_turn_signed_{kind}"] = direc[..., 1].mean(1).tolist()
    return out


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
