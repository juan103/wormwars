# WormWars: *C. elegans* wiring vs. shuffled and random graphs

Many parallel 2D worlds on one GPU. In each world, swarms of small creatures called **weys** forage
and fight. Every wey's brain is a small continuous-time recurrent network whose wiring is the real
*C. elegans* connectome (302 neurons, chemical synapses and gap junctions) used as a fixed sparsity
mask. Weights, time constants and biases are evolved. All weys in a swarm share one genome, and
selection acts on team results.

## Current findings: experiment 01b

**On foraging, the real wiring (N2) does better than random graphs, and better than or level with
shuffles of itself.** This is the pre-registered comparison with chemical synapses running the
right way round. Each condition has 15 independent evolutionary runs, and the controls are five
degree-preserving shuffles (SH) and five random sparse graphs (RD), three runs each. Intervals come
from a hierarchical bootstrap over graphs and runs.

| contrast | final held-out score (generation 25) | mean best-of-generation fitness (generations 0-24) |
|---|---|---|
| N2 − SH | +0.069 [−0.015, +0.169], no separation | **+0.068 [+0.034, +0.102]** |
| N2 − RD | **+0.094 [+0.029, +0.160]** | **+0.067 [+0.021, +0.105]** |
| SH − RD | +0.025 [−0.079, +0.116], no separation | −0.000 [−0.052, +0.045], no separation |

Six contrasts were tested. With Bonferroni-adjusted intervals, all three that separate still do.

- **N2 reaches higher mean best-of-generation fitness than both kinds of control,** and a higher
  final score than the random graphs. Against the shuffles, its final score is not detectably
  different.
- **This does not show that N2 improves faster.** The pre-registered "speed" measure averages every
  generation, generation 0 included, so it mixes where a run starts with how much it gains. Split
  apart (exploratory), N2's edge over the shuffles is, as a point estimate, all head start. Neither
  component separates on its own.
- **Preserving the real degree sequence did not help by itself:** SH and RD do not separate on
  either measure.
- N2 is one graph. By mean best-of-generation fitness it ranks first of the 11 graph means, and
  second on final score, but no rank test is offered: the graphs are not exchangeable.
- The comparison covers the whole pipeline, including recalibration. Motor calibration equalises
  drive only approximately: random populations reach 84-97% of the target drive depending on the
  graph, with the residual slightly favouring N2 over the shuffles.

Everything, including the exploratory analyses and a side-by-side with experiment 01:
[`experiments/01b-direction-corrected/RESULTS.md`](experiments/01b-direction-corrected/RESULTS.md).
It was pre-registered in
[`experiments/01b-direction-corrected/PREREGISTRATION.md`](experiments/01b-direction-corrected/PREREGISTRATION.md)
and reviewed before publication by Astra 6 and Fable 5.1 (`DECISIONS.md` D033).

## Limitations

Stated here, by us, because they bound what the result means.

**One task, one interface.** N2 against SH and RD has been measured only on single-swarm foraging
with automatic eating. Combat, coevolution and pump-gated eating were run only in experiment 01,
with the synapses reversed, and only on N2. The condition where the pharynx should matter is
untested. In N2, every route from a sensor to the pump neurons crosses the two-neuron `RIP↔I1`
gap-junction bridge (`DECISIONS.md` D008).

**A small evolutionary budget.** 25 generations, population 32, 5 404 parameters per genome. In
experiment 01, with the same budget, nothing had demonstrably converged by generation 25. So a
longer run could move the final-score contrasts in either direction.

**Few control graphs, and one real one.** Five shuffles and five random graphs. N2's interval carries
only run-to-run variation, while the controls' also carries graph-to-graph variation. More compute
cannot fix that asymmetry, because there is only one real connectome.

**The interface is our invention, not biology.** Weys get separate left and right food readings, so
foraging can be solved by comparing the two sides. A real worm cannot do that: *C. elegans*
chemotaxis samples concentration over time while moving. The sensor and motor mapping onto named
neurons is chosen by hand.

**Numerics.** 01b ran with 8 integrator substeps. Motor read-out errors above 0.05, against 32
substeps, are rare (0 to 8 of 1440 weys, depending on the inputs used), and their effect on fitness
was not measured.

**A wey is not a worm.** No neuromodulation, no plasticity, no biophysics, no muscles, no body
mechanics. The body is a rigid three-point segment and the motor output is a linear read of named
motor neurons. The only things taken from biology are the wiring graph and a hand-chosen mapping of
game quantities onto individual named neurons.

## Superseded: experiment 01, with the synapses reversed

Experiment 01 ran every brain with **chemical synapses carrying signal backwards**, from the
postsynaptic neuron to the presynaptic one. So it compared the worm's wiring *reversed* against
shuffles of that reversed graph. It reported that N2 **improves measurably more slowly** than both
kinds of control and that final scores do not separate. That conclusion does not hold for the real
wiring:

| contrast | 01, synapses reversed | 01b, synapses correct |
|---|---|---|
| N2 − SH, mean best-of-generation fitness | −0.100 [−0.129, −0.070] | +0.068 [+0.034, +0.102] |
| N2 − RD, mean best-of-generation fitness | −0.112 [−0.150, −0.077] | +0.067 [+0.021, +0.105] |
| N2 − SH, final score | −0.047 [−0.148, +0.039] | +0.069 [−0.015, +0.169] |
| N2 − RD, final score | −0.041 [−0.113, +0.029] | +0.094 [+0.029, +0.160] |

The bug was introduced by Claude Code and found a week later by Astra 6 (OpenAI) reading the
source. It was then confirmed, fixed and rerun as 01b (`DECISIONS.md` D031). Experiment 01 also
found N2 driving the motors more weakly than every control, and removed that confound by
calibrating each graph's motor gain. With the synapses the right way round, N2 is among the
strongest drivers, so that confound was largely a product of the reversal. Calibration is kept.

Experiment 01's other results also describe the reversed graph:
- foraging with pump-gated eating;
- two-swarm coevolution, where swarms win by out-foraging rather than out-fighting their
  opponents;
- the retracted claim that swarms "learned to flank", an artifact of the damage rule (C1).

Frozen record: [`experiments/01-foraging-n2-vs-controls/`](experiments/01-foraging-n2-vs-controls/).
Every number, and the correction, is C5 in [`docs/RESULTS.md`](docs/RESULTS.md).

## How to reproduce

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

## Data, and how to cite it

The connectome is real published data, never synthesised. **It is not redistributed here.**

> Cook SJ, Jarrell TA, Brittin CA, Wang Y, Bloniarz AE, Yakovlev MA, Nguyen KCQ, Tang LT-H,
> Bayer EA, Duerr JS, Bülow HE, Hobert O, Hall DH, Emmons SW (2019).
> **Whole-animal connectomes of both Caenorhabditis elegans sexes.** *Nature* **571**, 63–71.
> doi:[10.1038/s41586-019-1352-7](https://doi.org/10.1038/s41586-019-1352-7)

This project uses the hermaphrodite adjacency matrices (SI 5, corrected July 2020), distributed by
[wormwiring.org](https://wormwiring.org/pages/adjacency.html), which carries the notice
"Emmons Lab Copyright (c) 2020" and **states no licence granting redistribution**. No connectome
file is therefore committed to this repository. `python scripts/fetch_connectome.py` downloads it
from the original source and verifies its sha256 against the value recorded in `PROVENANCE.md`; the
loader fails with a clear message, and no fallback or synthetic substitute, if it is missing.

`PROVENANCE.md` records source URLs, hashes, the exact quantity used (`em_sections`, not synapse
counts) and every transformation applied.

If you use this repository, please cite both it (see `CITATION.cff`) and Cook et al. 2019.
The data terms are also stated in `NOTICE`; `LICENSE` (MIT) covers the code and documentation only.

## Status

See `PLAN.md` for milestones and what has actually been measured. `DECISIONS.md` records modelling
choices the spec left open, and `docs/REPRODUCIBILITY.md` says exactly what is and is not
reproducible.

## How this was made

This project was designed and built almost entirely by AI models, directed by a human.

- Juan H. González Estefan: the original ideas (connectome-tuned agents, swarm battles, parallel
  worlds, side bites, publishing the null result as a numbered series, and the hypotheses behind
  experiment 02), direction, and final approval at each checkpoint. He publishes and answers for
  this repository, but has not independently verified the code line by line.
- Claude Fable 5.1 (Anthropic), in conversation: turned those ideas into the experimental design and
  specification, reviewed the results, and drafted the experiment 02 pre-registration (to be
  committed next). Later, consulted read-only, it reviewed experiment 01b before publication (D033).
- Astra 6 (a GPT model from OpenAI): adversarial review of the specification, which produced the
  statistical design, the resource accounting rules and the numerical stability requirements.
  Reviewing the roadmap, it found that the chemical synapses of experiment 01 ran backwards (D031),
  and it reviewed experiment 01b before publication (D033).
- Claude Code running Claude Opus 5 and, from 2026-09-24, Claude Opus 5.5 (Anthropic): every line
  of code, every measurement, and all implementation decisions recorded in DECISIONS.md. Opus 5
  built experiment 01 and found the motor-gain confound on its own. Opus 5.5 confirmed and fixed
  the reversed synapses, ran experiment 01b, and acted on its review.

Errors and who caught them: the "learned to flank" claim was made by Claude Code and caught by
Claude Fable 5.1 in review (D026). The "N2 is deeper" explanation was made by Claude Fable 5.1,
built on a path length mis-measured by Claude Code, and caught by Claude Code when it re-measured
instead of writing the claim as dictated (C4). No single participant, human or AI, would have caught
both. The largest error, chemical synapses running backwards in every run of experiment 01, was
made by Claude Code and caught by Astra 6 (D031). Claude Code's first write-up of the corrected
rerun then overclaimed, and Astra 6 and Fable 5.1 each caught that independently (D033). The full
list, with commits: [`docs/REVIEW_TRAIL.md`](docs/REVIEW_TRAIL.md).

The design and implementation came from Anthropic models and the specification review from an OpenAI
model. Reviewers from different model families are less likely to share the same blind spots.

Because the work is AI-generated and has had limited human verification, treat every result as
provisional until someone replicates it.
