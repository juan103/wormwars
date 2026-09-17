"""Saving, loading and naming genomes.

A saved genome carries enough to rebuild the exact brain: the mask values, the graph label, the
brain config, and the dataset hash the mask came from. Loading against a different graph is refused
rather than silently reshaped.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from ..brain import BrainSpec, Genome
from ..config import BrainConfig

# Deterministic nicknames for hall-of-fame champions. Two short word lists: 64 x 64 = 4096 names,
# which is plenty for one run's champions and short enough to say out loud.
ADJECTIVES = (
    "brave amber ancient bitter bright calm clever coral crimson dapper deep dusty eager early "
    "fierce flint frosty gentle gilded glossy grave hollow humble idle ivory jagged keen lucid "
    "lunar marble mellow mild misty noble olive patient placid quiet rapid restless rough rusty "
    "sable salty scarlet silent slender solemn sombre steady stern stormy sudden sunken swift "
    "tawny tidy umber velvet violet wary wild winter"
).split()
ANIMALS = (
    "heron adder auk badger bison bittern boar bream cicada civet cod coot crane crow curlew dace "
    "dipper dormouse dunlin egret eider elver ermine ferret finch gannet gecko godwit grebe hare "
    "hoopoe ibex jackdaw kestrel lapwing lemur linnet lynx marten merlin mole newt osprey otter "
    "petrel pika pipit plover puffin quail raven roach shrew siskin skua smelt stoat swift tern "
    "vole weasel wigeon wren"
).split()


def genome_hash(genome: Genome, index: int = 0) -> str:
    flat = genome.flat()[index].detach().to("cpu").numpy().astype(np.float32)
    return hashlib.sha256(flat.tobytes()).hexdigest()


def nickname(genome: Genome, index: int = 0) -> str:
    """Deterministic adjective-animal name derived from the genome itself."""
    h = int(genome_hash(genome, index)[:16], 16)
    return f"{ADJECTIVES[h % len(ADJECTIVES)]}-{ANIMALS[(h >> 6) % len(ANIMALS)]}"


def strain_id(graph: str, run: int, generation: int, rank: int) -> str:
    """`<graph>-run<run>-g<generation>-r<rank>`, e.g. N2-run04-g0412-r1."""
    return f"{graph}-run{run:02d}-g{generation:04d}-r{rank}"


def save_genome(path, genome: Genome, index: int = 0, **meta) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    spec = genome.spec
    meta = {
        "graph": spec.label,
        "weight_kind": spec.weight_kind,
        "n_chem": spec.n_chem,
        "n_gap": spec.n_gap,
        "n_neurons": spec.n,
        "brain_config": dataclasses.asdict(genome.cfg),
        "genome_sha256": genome_hash(genome, index),
        "nickname": nickname(genome, index),
        **meta,
    }
    np.savez_compressed(
        path,
        w=genome.w[index].detach().cpu().numpy(),
        g=genome.g[index].detach().cpu().numpy(),
        tau=genome.tau[index].detach().cpu().numpy(),
        bias=genome.bias[index].detach().cpu().numpy(),
        dale=(
            np.zeros(0)
            if genome.dale_sign is None
            else genome.dale_sign[index].detach().cpu().numpy()
        ),
        meta=np.array(json.dumps(meta)),
    )
    return path


def save_population(path, genome: Genome, **meta) -> Path:
    """All strains of a population in one file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    spec = genome.spec
    meta = {
        "graph": spec.label,
        "weight_kind": spec.weight_kind,
        "n_chem": spec.n_chem,
        "n_gap": spec.n_gap,
        "n_neurons": spec.n,
        "n_strains": genome.n_strains,
        "brain_config": dataclasses.asdict(genome.cfg),
        "nicknames": [nickname(genome, i) for i in range(genome.n_strains)],
        **meta,
    }
    np.savez_compressed(
        path,
        w=genome.w.detach().cpu().numpy(),
        g=genome.g.detach().cpu().numpy(),
        tau=genome.tau.detach().cpu().numpy(),
        bias=genome.bias.detach().cpu().numpy(),
        dale=(np.zeros(0) if genome.dale_sign is None else genome.dale_sign.detach().cpu().numpy()),
        meta=np.array(json.dumps(meta)),
    )
    return path


def load_genome(
    path, spec: BrainSpec, cfg: BrainConfig | None = None, device="cpu", strain: int | None = None
) -> tuple[Genome, dict]:
    """Load one genome, or a whole saved population.

    `strain` selects a single strain from a population file. The mask is validated against the
    *stored array shapes*, not against metadata, so a file saved by an older writer still fails
    loudly if it does not fit the spec.
    """
    d = np.load(Path(path), allow_pickle=True)
    meta = json.loads(str(d["meta"]))
    if meta["graph"] != spec.label:
        raise ValueError(
            f"genome was evolved on graph {meta['graph']!r} but the spec is {spec.label!r}. "
            "Genomes are mask-specific and are not transferable between graphs."
        )
    t = lambda k: torch.from_numpy(np.atleast_2d(d[k])).to(device)  # noqa: E731
    w, g, tau, bias = t("w"), t("g"), t("tau"), t("bias")
    if w.shape[1] != spec.n_chem or g.shape[1] != spec.n_gap or tau.shape[1] != spec.n:
        raise ValueError(
            f"genome does not fit the mask: stored {w.shape[1]} W / {g.shape[1]} G / "
            f"{tau.shape[1]} neurons, spec wants {spec.n_chem} / {spec.n_gap} / {spec.n}"
        )
    cfg = cfg or BrainConfig(**meta["brain_config"])
    dale = d["dale"]
    genome = Genome(
        spec.to(device),
        cfg,
        w=w,
        g=g,
        tau=tau,
        bias=bias,
        dale_sign=None if dale.size == 0 else torch.from_numpy(np.atleast_2d(dale)).to(device),
    )
    if strain is not None:
        genome = genome.select([strain])
    return genome, meta


def load_population(path, spec: BrainSpec, cfg: BrainConfig | None = None, device="cpu"):
    return load_genome(path, spec, cfg, device)
