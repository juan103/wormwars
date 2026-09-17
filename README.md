# WormWars

Many parallel 2D worlds on one GPU. In each world, swarms of small creatures called **weys** forage
and fight. Every wey's brain is a small continuous-time recurrent network whose wiring is the real
*C. elegans* connectome (302 neurons, chemical synapses and gap junctions) used as a fixed sparsity
mask. Weights, time constants and biases are evolved. All weys in a swarm share one genome, and
selection acts on team results.

## What a wey is, and is not

**A wey is a worm-shaped neural network in a game body. It is not a simulation of a worm.**
It has no neuromodulation, no plasticity, no biophysics, no muscles and no body mechanics: the body
is a rigid three-point segment, and the motor output is a linear read-out of named motor neurons.
The only thing borrowed from biology is the *wiring graph* and a hand-chosen mapping of game
quantities onto individual named neurons.

## The claim under test, stated precisely

> Given this specific hand-chosen sensor and motor interface and this game, does the real wiring
> evolve faster, or end up better, than degree-preserving shuffles of it, or than random sparse
> graphs of the same size?

That is a test of **wiring plus interface on one task**. It is not a test of whether biological
wiring is better in general. A positive result would say that this graph suits this interface on
this game; a negative result would say it does not. Neither generalises on its own.

## Conditions

| Name | Meaning |
|---|---|
| `N2` | the real connectome (named after the standard wild-type strain) |
| `SH` | degree-preserving shuffles of it — several independently generated graphs |
| `RD` | random sparse graphs with the same neuron and edge counts |

## Vocabulary

- **Connectome** — the wiring mask (`N2` / `SH` / `RD`; individual shuffles are `SH3`, `RD1`, …).
- **Strain** — one genome, i.e. one evolved tuning of a connectome.
  ID: `<graph>-run<run>-g<generation>-r<rank>`, e.g. `N2-run04-g0412-r1`.
  Hall-of-fame champions also get a deterministic adjective-animal nickname from a hash of the
  genome, e.g. `N2 brave-heron`.
- **Wey** (plural weys) — one creature running a strain. Weys are clones, identified only by swarm
  and index.
- **Swarm** — all the weys of one strain in one world.
- **Run** — one independent evolutionary run. **This is the unit of statistical analysis.**

## Data

The connectome is real published data, never synthesised: Cook et al. 2019, hermaphrodite,
corrected July 2020, including the 20 pharyngeal neurons. See `PROVENANCE.md` for source URLs,
citation, file hashes, the exact quantity used and every transformation applied.

## What has been found so far

Full numbers in [`docs/RESULTS.md`](docs/RESULTS.md); every one of them was measured by a script in
`scripts/`.

**The simulator works.** Evolved foragers score **1.398 ± 0.013** against random-weight weys'
**0.432 ± 0.030** on held-out seeds across 3 independent runs, and every run beat the *best of 32*
random strains. They keep 16-18 of 20 weys alive against 6-7, and eat 3.7x more food, so this is
foraging and not an accounting exploit. It still works when eating requires pumping (**8.3x**), and
coevolved swarms learn to flank: **88% of the damage they deal lands on an enemy's flank or tail**
rather than its head, which is exactly what the measured combat geometry rewards.

**On the claim under test, the first answer is negative.** In the reduced pipeline check (K=3,
R=2, 18 runs) the real wiring did *worse* than both controls:

| condition | held-out foraging score |
|---|---|
| N2 | 1.369 [1.266, 1.470] |
| SH | 1.550 [1.427, 1.657] |
| RD | 1.501 [1.433, 1.577] |

N2 - SH = -0.181 [-0.329, -0.030]; N2 - RD = -0.132 [-0.260, -0.006]; SH and RD indistinguishable.

Two things were then checked. It is **not** an artifact of the parameter bounds: champions of all
three conditions sit nowhere near them and use the parameter space identically. But there **is** a
confound: the raw magnitude of the motor read-out is a property of the graph, and N2 is the weakest
of the seven graphs tested. The motor gain was hand-tuned on N2, so under one fixed gain the
controls simply move more before evolution starts, and foraging rewards moving. The full experiment
is therefore run **both ways** -- one fixed gain, and per-graph gains calibrated so every condition
starts from the same motor output magnitude (`wormwars/calibration.py`). Reporting only the
friendlier number would not be a result.

Also measured, and predicted in `DECISIONS.md` D008 before the experiment was run: in N2 the pump
neurons sit **three graph hops** from any sensor, because all somatic-pharyngeal traffic goes
through the two-neuron `RIP<->I1` gap-junction bridge. In every shuffled or random control they are
one or two hops away.

## Status

See `PLAN.md` for milestones and what has actually been measured. `DECISIONS.md` records modelling
choices the spec left open, and `docs/REPRODUCIBILITY.md` says exactly what is and is not
reproducible.

## Setup

```
pip install -r requirements.txt          # torch from the cu130 index
python scripts/check_env.py              # runs a real CUDA kernel, not just is_available()
python scripts/fetch_connectome.py       # downloads + hashes + caches the connectome
python -m pytest
```

## Things to run

```
python scripts/watch.py --out runs/look              # one foraging world, rendered to PNG
python scripts/evolve_forage.py --runs 3             # evolve foragers, compare to random weys
python scripts/evolve_forage.py --runs 3 --stage 2   # ... with eating gated on pumping
python scripts/coevolve.py --runs 2                  # two-swarm coevolution
python scripts/experiment.py --k 5 --runs 3 --calibrate   # the N2/SH/RD experiment
python scripts/ablate.py --champions 'runs/m4/champion-*.npz'
python scripts/bench_scaling.py --showcase           # wey-ticks/s and peak VRAM
python scripts/showcase.py --a A.npz --b B.npz --size 2000
```

Every script writes a run bundle (config, dataset hashes, package versions, git commit, seed
scheme) next to its output.
