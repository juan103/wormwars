"""Minimal local viewer: fields as heatmaps, weys as oriented segments.

Deliberately headless (Agg backend). It writes PNG contact sheets and GIFs rather than opening a
window, so the same call works over ssh, in a test, and when a human wants to stare at a match.

The point of this module is to make behaviour *visible* before any score is trusted: whether weys
find food, whether they grind along walls, whether a swarm collapses into one cell, whether a
"successful" forager is just parked on a patch.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .recorder import Replay  # noqa: E402

SWARM_COLORS = ["#ff5d3b", "#3ba7ff", "#ffd23b", "#57d97a"]


def _draw(ax, replay: Replay, tick: int, world: int, show: str = "food") -> None:
    ch = replay.meta["channels"]
    n_swarms = replay.meta["n_swarms"]
    side = replay.meta["side"]
    f = replay.field_at(tick)[world]

    if show == "food":
        base = f[ch["FOOD"]] + f[ch["PELLET"]]
        cmap, label = "YlGn", "food + pellets"
    elif show == "hazard":
        base, cmap, label = f[ch["HAZARD"]], "inferno", "hazard"
    elif show == "pheromone":
        base = f[ch["PHEROMONE"] : ch["PHEROMONE"] + n_swarms].sum(0)
        cmap, label = "PuBu", "pheromone"
    elif show == "body":
        base, cmap, label = f[ch["BODY"]], "magma", "body density"
    elif show == "attack":
        base = f[ch["ATTACK"] : ch["ATTACK"] + n_swarms].sum(0)
        cmap, label = "Reds", "attack"
    else:
        raise ValueError(f"unknown field {show!r}")

    ax.imshow(
        base, origin="lower", cmap=cmap, extent=(0, side, 0, side), interpolation="nearest",
        vmin=0.0,
    )
    wall = f[ch["WALL"]]
    ax.imshow(
        np.ma.masked_where(wall <= 0, wall), origin="lower", cmap="Greys", vmin=0, vmax=1.4,
        extent=(0, side, 0, side), interpolation="nearest",
    )
    haz = f[ch["HAZARD"]]
    if show != "hazard" and haz.max() > 0:
        ax.contour(
            np.linspace(0, side, haz.shape[1]), np.linspace(0, side, haz.shape[0]), haz,
            levels=[0.3], colors="#d62728", linewidths=0.8, alpha=0.7,
        )

    body_len = replay.meta["body_length"]
    max_e = replay.meta["max_energy"]
    for s in range(n_swarms):
        alive = replay.alive[tick, world, s]
        if not alive.any():
            continue
        p = replay.pos[tick, world, s][alive]
        th = replay.heading[tick, world, s][alive]
        e = replay.energy[tick, world, s][alive]
        tailx = p[:, 0] - np.cos(th) * body_len
        taily = p[:, 1] - np.sin(th) * body_len
        segs = np.stack([np.stack([tailx, p[:, 0]], -1), np.stack([taily, p[:, 1]], -1)], -1)
        from matplotlib.collections import LineCollection

        widths = 0.8 + 2.2 * np.clip(e / max_e, 0, 1)
        ax.add_collection(
            LineCollection(segs, colors=SWARM_COLORS[s % len(SWARM_COLORS)], linewidths=widths)
        )
        ax.scatter(p[:, 0], p[:, 1], s=6, c="white", edgecolors="black", linewidths=0.3, zorder=3)

    ax.set_xlim(0, side)
    ax.set_ylim(0, side)
    ax.set_xticks([])
    ax.set_yticks([])
    alive_txt = " / ".join(str(int(replay.alive[tick, world, s].sum())) for s in range(n_swarms))
    e_txt = " / ".join(
        f"{replay.energy[tick, world, s][replay.alive[tick, world, s]].sum():.0f}"
        for s in range(n_swarms)
    )
    ax.set_title(f"t={tick}  alive {alive_txt}  E {e_txt}  [{label}]", fontsize=8)


def contact_sheet(
    replay: Replay,
    path: str | Path,
    world: int = 0,
    n_frames: int = 12,
    show: str = "food",
    cols: int = 4,
) -> Path:
    """A grid of frames across the whole match, saved as one PNG. The fastest way to see a match."""
    ticks = np.linspace(0, replay.n_ticks - 1, n_frames).astype(int)
    rows = int(np.ceil(n_frames / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(3.0 * cols, 3.2 * rows))
    for ax, t in zip(np.atleast_1d(axes).ravel(), ticks):
        _draw(ax, replay, int(t), world, show)
    for ax in np.atleast_1d(axes).ravel()[len(ticks) :]:
        ax.axis("off")
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def panel(replay: Replay, path: str | Path, tick: int = -1, world: int = 0) -> Path:
    """One tick, every field side by side. For checking what the sensors can actually see."""
    tick = replay.n_ticks - 1 if tick < 0 else tick
    shows = ["food", "pheromone", "hazard", "body"]
    if replay.meta["n_swarms"] > 1:
        shows.append("attack")
    fig, axes = plt.subplots(1, len(shows), figsize=(3.2 * len(shows), 3.4))
    for ax, s in zip(np.atleast_1d(axes).ravel(), shows):
        _draw(ax, replay, tick, world, s)
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def gif(
    replay: Replay,
    path: str | Path,
    world: int = 0,
    show: str = "food",
    stride: int = 4,
    fps: int = 15,
) -> Path:
    """Animated playback. Uses pillow, which matplotlib already depends on."""
    from matplotlib.animation import FuncAnimation, PillowWriter

    fig, ax = plt.subplots(figsize=(5, 5.3))
    ticks = range(0, replay.n_ticks, stride)

    def frame(t):
        ax.clear()
        _draw(ax, replay, int(t), world, show)

    anim = FuncAnimation(fig, frame, frames=list(ticks), interval=1000 / fps)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    anim.save(path, writer=PillowWriter(fps=fps))
    plt.close(fig)
    return path


def energy_plot(replay: Replay, path: str | Path, world: int = 0) -> Path:
    """Swarm energy and headcount over the match: the score, but visible."""
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6, 5), sharex=True)
    for s in range(replay.meta["n_swarms"]):
        e = (replay.energy[:, world, s] * replay.alive[:, world, s]).sum(-1)
        n = replay.alive[:, world, s].sum(-1)
        c = SWARM_COLORS[s % len(SWARM_COLORS)]
        a1.plot(e, color=c, label=f"swarm {s}")
        a2.plot(n, color=c)
    a1.set_ylabel("surviving energy")
    a1.legend(fontsize=8)
    a2.set_ylabel("weys alive")
    a2.set_xlabel("tick")
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
