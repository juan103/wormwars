"""Experiment 03's measures (design v3). Everything here runs unselected random genomes and keeps
the genome axis, so every value is saved per genome."""

from __future__ import annotations

import hashlib

import numpy as np
import torch

from ..accounting import counted
from ..brain import Brain, Genome
from ..config import Config
from ..world import World


def genome_seed(name: str, salt: str = "") -> int:
    """An independent random-genome seed per graph, from a hash of its whole name. The first
    version kept only the name's first four characters, so graphs shared genomes (Astra,
    pilot review; D053). A salt gives a replication independent genomes for the same graph
    name, N2's included (03r, D059); no salt is 03's seed."""
    return int.from_bytes(hashlib.sha256((salt + name).encode()).digest()[:4], "little") % (2 ** 31)


def task_c_config(base: Config) -> Config:
    """Task C, locomotion coverage: 02's T0 world with no metabolic drain and no hazard damage.
    Food is removed after the map is built (see `coverage`), so the map's random draws are
    unchanged. Weys start with 12 energy and movement costs at most about 1.2 per episode, so
    no wey dies."""
    from ..exp02 import grid
    c = grid.task_config(base, "T0")
    c.world.metabolic_drain = 0.0
    c.world.hazard_damage = 0.0
    return c


@counted("measure")
def coverage(cfg, iface, genome: Genome, world_ids, run_seed, device, chunk_worlds=None) -> dict:
    """Distinct grid cells visited by each strain's swarm (union over its weys) on each world,
    with food and pellets removed from the built map. Returns cells [strains, worlds], the food
    left at the end (must be 0) and the number of weys that died (must be 0)."""
    world_ids = np.asarray(world_ids, dtype=np.int64)
    n_ids, S = len(world_ids), genome.n_strains
    per_chunk = max(1, (chunk_worlds or cfg.evo.chunk_worlds) // max(n_ids, 1))
    cells, food_left, deaths = [], 0.0, 0
    for lo in range(0, S, per_chunk):
        hi = min(lo + per_chunk, S)
        brain = Brain(genome.select(list(range(lo, hi))))
        n_sub = hi - lo
        strain_of = torch.arange(n_sub, device=device).repeat_interleave(n_ids).reshape(-1, 1)
        world = World(cfg, iface, brain, strain_of, run_seed=run_seed, world_ids=np.tile(world_ids, n_sub),
                      device=device)
        world.fields[:, world.ch.FOOD] = 0.0
        world.fields[:, world.ch.PELLET] = 0.0
        visited = torch.zeros(world.n_worlds, world.H, world.W, dtype=torch.bool, device=device)
        wi = torch.arange(world.n_worlds, device=device).view(-1, 1, 1)

        def mark():
            idx = world.pos.long()
            x = idx[..., 0].clamp(0, world.W - 1)
            y = idx[..., 1].clamp(0, world.H - 1)
            alive = world.alive
            visited[wi.expand_as(x)[alive], y[alive], x[alive]] = True

        mark()
        while world.tick_count < cfg.world.max_ticks and not world.done():
            world.tick()
            mark()
        cells.append(visited.sum(dim=(1, 2)).reshape(n_sub, n_ids).cpu().numpy())
        food_left += float(world.fields[:, world.ch.FOOD].sum() + world.fields[:, world.ch.PELLET].sum())
        deaths += int((~world.alive).sum())
    return {"cells": np.concatenate(cells), "food_left": food_left, "deaths": deaths}


def _current(iface, cfg, values: dict, n, s, device):
    cur = torch.zeros(s, 1, n, device=device)
    for name, j, gain in zip(iface.signal_names, iface.sensor_neuron, iface.sensor_gain):
        cur[..., int(j)] += float(values.get(name, 0.0)) * float(gain) * cfg.brain.input_gain
    return cur.clamp(-cfg.brain.input_max, cfg.brain.input_max)


def _readout(iface, cfg, v):
    """[strains, 4]: raw forward, raw turn, motor forward, motor turn."""
    a = torch.tanh(v[:, 0])
    fwd = a[:, list(iface.forward_plus)].mean(-1) - a[:, list(iface.forward_minus)].mean(-1)
    turn = a[:, list(iface.turn_plus)].mean(-1) - a[:, list(iface.turn_minus)].mean(-1)
    return torch.stack([fwd, turn, (fwd * 0.5 * cfg.world.forward_gain).clamp(-1, 1),
                        (turn * 0.5 * cfg.world.turn_gain).clamp(-1, 1)], -1)


@counted("probe")
def history(genome: Genome, cfg, iface, bank: dict, rising_start=0.25, falling_start=1.75,
            warm=100, span=10, after=5) -> dict:
    """02b's matched-input history test on every genome of `genome`, with one stimulus bank
    shared by all genomes and graphs. The final food level is the bank's; the two histories
    start at `rising_start` and `falling_start` times it and ramp to it over `span` ticks, after
    `warm` ticks at the start level. Returns, per read-out (raw_forward, raw_turn, motor_forward,
    motor_turn), arrays over genomes: the rising-minus-falling difference on the final tick
    ("final"), after `after` more ticks of the final input ("after"), and the steady-state
    contrast between holding the two start levels ("steady_contrast")."""
    brain = Brain(genome)
    s, n, dev = genome.n_strains, genome.spec.n, genome.device
    food = (bank["food_left"] + bank["food_right"]) / 2
    at = lambda lvl: _current(iface, cfg, dict(bank, food_left=lvl, food_right=lvl), n, s, dev)  # noqa: E731
    res = {}
    for name, start in (("rising", rising_start * food), ("falling", falling_start * food)):
        v = brain.initial_state(1)
        for _ in range(warm):
            v = brain.step(v, at(start))
        steady = _readout(iface, cfg, v)
        for t in range(span):
            v = brain.step(v, at(start + (food - start) * (t + 1) / span))
        final = _readout(iface, cfg, v)
        for _ in range(after):
            v = brain.step(v, at(food))
        res[name] = (steady, final, _readout(iface, cfg, v))
    keys = ("raw_forward", "raw_turn", "motor_forward", "motor_turn")
    return {k: {"final": (res["rising"][1][:, i] - res["falling"][1][:, i]).cpu().numpy(),
                "after": (res["rising"][2][:, i] - res["falling"][2][:, i]).cpu().numpy(),
                "steady_contrast": (res["falling"][0][:, i] - res["rising"][0][:, i]).cpu().numpy()}
            for i, k in enumerate(keys)}
