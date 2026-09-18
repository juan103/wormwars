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
two-swarm coevolution improves against a frozen opponent suite (**+0.128 → +0.343**, 2/2 runs).

**Coevolution did not produce any measurable combat tactic.** An earlier version of this README
claimed it learned to flank; that was an artifact of the damage rule's armour weights and has been
retracted — see *Corrections* in [`docs/RESULTS.md`](docs/RESULTS.md) and `DECISIONS.md` D026.
Re-measured against the frozen suite inside the same matches, coevolved swarms land bites no further
back than their unevolved opponents do (placement share difference -0.011 [-0.036, +0.019]), turn
toward the bite at chance, and their damage is *more* answered than their opponents', not less
(-0.153 [-0.227, -0.081]).

**On the claim under test, the answer is: no, and slower.** The full experiment is K=5, R=3 --
five independent SH graphs and five RD graphs with three runs each, and fifteen runs of N2, so every
condition has **15 runs**. It was run twice, with and without per-graph motor gain calibration
(see below). Held-out foraging score, hierarchical bootstrap over graphs and runs:

| condition | final score (calibrated) | speed of improvement |
|---|---|---|
| N2 | 1.412 [1.366, 1.453] | 1.359 [1.344, 1.373] |
| SH | 1.458 [1.385, 1.552] | 1.459 [1.433, 1.484] |
| RD | 1.452 [1.398, 1.510] | 1.471 [1.439, 1.506] |

- **Final performance: a null.** No contrast separates (N2 - SH P = 0.167, N2 - RD P = 0.130).
  N2's mean sits inside the spread of the individual control graphs, not at either end.
- **Speed of improvement: N2 is slower**, and clearly so: N2 - SH = -0.100 [-0.129, -0.070] and
  N2 - RD = -0.112 [-0.150, -0.077], both P = 0.000.
- **SH and RD are indistinguishable from each other** on everything measured, so preserving the
  real degree sequence bought nothing either.

The real wiring, on this task with this interface, **reaches the same ceiling as its own shuffles
and as random graphs of the same size, and takes longer to get there.**

### The confound, and why the experiment was run twice

A first pass (K=3, R=2) found N2 significantly *worse* on final score too. Two checks followed. It
is **not** an artifact of the parameter bounds: champions of all three conditions sit nowhere near
them and use the parameter space identically. But there **is** a confound: the raw magnitude of the
motor read-out is a property of the graph, and N2 is the weakest of the seven graphs tested. The
motor gain was hand-tuned on N2, so under one fixed gain the controls simply move more before
evolution starts, and foraging rewards moving.

Running it both ways separates the two:

| contrast | one fixed gain | gains calibrated |
|---|---|---|
| N2 - SH, final score | **-0.110 [-0.185, -0.026]** | -0.047 [-0.148, +0.039] |
| N2 - SH, speed | **-0.118 [-0.160, -0.080]** | **-0.100 [-0.129, -0.070]** |

The final-score deficit was mostly the confound. The speed deficit is not: it survives calibration
almost intact, and is the more robust of the two findings. N2 scores identically in both arms
(1.4115), because N2 is the calibration reference and only the controls moved -- which doubles as a
check that the pipeline is deterministic.

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
