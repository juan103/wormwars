"""E5-0's reused hunters (docs/E5/E5-0-PLAN.md §5), each loaded from its local genome file and checked against the
sha256 its committed record gives.

- `e4s1_champions`: E4s-1's 16 M-arm runs' validation champions (N2 + L1, 306 neurons), whole brains;
- `l1_carrier`: E4s-0's frozen L1 on its carrier (forward 1.0, turn 0.2), the neural positive control;
- `e2d_champions`: E2d's champions of E2 and 04a (N2, 302 neurons), duplicates by sha256 dropped;
- `generation0`: random N2 genomes, 02's initialisation.

The genome files are local (rule 1 keeps the connectome-derived weights out of the repository); a missing file stops
the caller rather than shrinking a set silently.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import torch

from .. import graft as G
from ..brain import BrainSpec, Genome
from ..e4s import arms as A
from ..e4s import comparator as CMP
from ..evo.genomes import genome_hash, load_population

ROOT = Path(__file__).resolve().parents[2]
E4S1_EXP, E4S1_OUT = ROOT / "experiments" / "E4s-stereo-module" / "E4s-1", ROOT / "runs" / "e4s1"
E2_EXP, E2_OUT = ROOT / "experiments" / "E2-optimizer-screen", ROOT / "runs" / "e2"
E04A_EXP, E04A_OUT = ROOT / "experiments" / "04a-navigation-primitive", ROOT / "runs" / "e04a"
M_STAGES = ("train-1", "train-4")  # E4s-1's M arm: runs 0-7 and 8-15
L1_CARRIER = {"forward": 1.0, "turn": 0.2}  # E4s-0's qualified carrier (ladder.json)


def _read(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _pick(path: Path, index: int, sha: str, spec: BrainSpec, bcfg) -> Genome:
    if not Path(path).exists():
        raise SystemExit(f"{path} is missing: the hunter set would shrink silently")
    g, _ = load_population(path, spec, bcfg)
    if dataclasses.asdict(g.cfg) != dataclasses.asdict(bcfg):
        raise SystemExit(f"{Path(path).name} loads with another brain configuration")
    g = g.select([index])
    if genome_hash(g, 0) != sha:
        raise SystemExit(f"{Path(path).name} checkpoint {index} does not match its committed sha256")
    return g


def grafted(con):
    """(the L1 module, N2 + L1, its spec): E4s's graft, checked against its bound sha256."""
    l1 = A.load_l1()
    ext = G.graft_connectome(con, l1)
    return l1, ext, BrainSpec.from_connectome(ext)


def e4s1_champions(con, bcfg) -> dict[str, tuple[Genome, str]]:
    _, ext, spec = grafted(con)
    out = {}
    for stage in M_STAGES:
        rec = _read(E4S1_EXP / f"{stage}.json")
        if rec["arm"] != "M":
            raise SystemExit(f"E4s-1's {stage} is arm {rec['arm']}, not M")
        for r in rec["records"]:
            run, c = r["spec"]["run"], r["champion"]
            out[f"e4s1 M run{run:02d}"] = (_pick(E4S1_OUT / "genomes" / f"M-run{run:02d}-candidates.npz",
                                                 c["checkpoint"], c["sha256"], spec, bcfg), c["sha256"])
    if len(out) != 16:
        raise SystemExit(f"{len(out)} M-arm champions, not 16")
    return out


def l1_carrier(con, bcfg) -> Genome:
    l1, ext, _ = grafted(con)
    return CMP.carrier_genome(ext, l1, bcfg, **L1_CARRIER)


def e2d_champions(con, bcfg) -> dict[str, tuple[Genome, str]]:
    """E2's GA, ES and random-sampling champions, the extension's, and 04a's, as E2d loaded them; the first label is
    kept for a sha256 met twice."""
    spec = BrainSpec.from_connectome(con)
    out, seen = {}, set()

    def add(label, path, c):
        if c["sha256"] in seen:
            return
        seen.add(c["sha256"])
        out[label] = (_pick(path, c["checkpoint"], c["sha256"], spec, bcfg), c["sha256"])

    for m in ("ga", "es", "random"):
        for r in _read(E2_EXP / f"train-{m}.json")["records"]:
            run = r["spec"]["run"]
            add(f"e2 {m} run{run:02d}", E2_OUT / "genomes" / f"{m}-run{run:02d}-candidates.npz", r["champion"])
    for c in _read(E2_EXP / "extension.json")["champions_over_both"]:
        prefix = "es" if c["source"] == "formal" else "extension"
        add(f"e2 extension run{c['run']:02d}", E2_OUT / "genomes" / f"{prefix}-run{c['run']:02d}-candidates.npz", c)
    for b in ("A", "B"):
        for r in _read(E04A_EXP / f"train-{b}.json")["records"]:
            run = r["spec"]["run"]
            add(f"04a run{run:02d}", E04A_OUT / "genomes" / f"run{run:02d}-candidates.npz", r["champion"])
    return out


def generation0(con, bcfg, n: int, seed: int) -> Genome:
    spec = BrainSpec.from_connectome(con)
    return Genome.random(spec, bcfg, n, generator=torch.Generator().manual_seed(int(seed)))
