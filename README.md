# WormWars 01: *C. elegans* wiring vs. shuffled and random graphs. A foraging null result.

Many parallel 2D worlds on one GPU. In each world, swarms of small creatures called **weys** forage
and fight. Every wey's brain is a small continuous-time recurrent network whose wiring is the real
*C. elegans* connectome (302 neurons, chemical synapses and gap junctions) used as a fixed sparsity
mask. Weights, time constants and biases are evolved. All weys in a swarm share one genome, and
selection acts on team results.

## Summary of findings

Across 15 independent evolutionary runs per condition, there is **no detectable difference in final
score at generation 25** between the real connectome, degree-preserving shuffles of itself, and
random sparse graphs of the same size — no contrast separates — while the real connectome
**improves measurably more slowly** (N2 − SH = −0.100 [−0.129, −0.070], N2 − RD = −0.112
[−0.150, −0.077], both P < 1/20 000). Shuffled and random graphs **showed no detectable benefit**
over each other on anything measured, so preserving the real degree sequence did not help either.
No equality is claimed: the N2 − SH interval still allows a deficit of about 10%, and by our own
Limitations nothing had converged at generation 25.

A confound was found along the way and removed: the raw magnitude of
the motor read-out is a property of the graph, and the motor gain had been hand-tuned on N2, so
under one fixed gain the controls simply moved more before evolution started; the experiment is
reported **both with and without** per-graph gain calibration, and the final-score deficit turns out
to be mostly that confound while the speed deficit survives it. The **combat section found no
evidence of learned tactics** — an earlier claim that coevolved swarms "learned to flank" was an
artifact of the damage rule and has been retracted; coevolved swarms win by out-foraging their
opponents, not by out-fighting them. We do not know why the real wiring improves more slowly.

Frozen record: [`experiments/01-foraging-n2-vs-controls/`](experiments/01-foraging-n2-vs-controls/).
Every number: [`docs/RESULTS.md`](docs/RESULTS.md). Every modelling choice: `DECISIONS.md`.

## Limitations

Stated here, by us, because they bound what the result means.

**The three-way comparison only ever ran on foraging.** N2 against SH and RD was measured on
single-swarm foraging with automatic eating, and on nothing else. It was never run on combat, and
never on pump-gated eating — which is exactly where `DECISIONS.md` D008 predicts the real wiring is
handicapped, because in N2 every route from a sensor to the pump neurons crosses the two-neuron
`RIP↔I1` bridge: **3 graph hops in N2 against 1–2 in all ten control graphs**. Combat and pumping
were only ever run on N2. The condition where the pharynx should matter has not been tested.

**The evolutionary budget is small, and nothing had clearly converged when it ran out.** 25
generations, population 32, 5 404 parameters per genome. Change in best-of-generation fitness from
generations 10–14 to generations 20–24:

| | gens 10–14 | gens 20–24 | change | runs where it rose |
|---|---|---|---|---|
| N2 | 1.369 | 1.439 | **+0.070** | **13 / 15** (P = 0.004 under a coin flip) |
| SH | 1.497 | 1.500 | +0.002 | 7 / 15 (P = 0.70) |
| RD | 1.496 | 1.550 | +0.054 | 9 / 15 (P = 0.30) |

"Rose" means that run's mean best fitness over generations 20–24 exceeded its mean over generations
10–14. A perfectly flat but noisy curve would be labelled rising in about half of runs, so 7/15 and
9/15 are close to chance and carry little information; only N2's 13/15 stands out.

**RD was still improving too** (+0.054, nearly as much as N2's +0.070); only SH was flat. So this is
not a case of N2 climbing while the controls sat still. What it does mean is that **none of the
three had demonstrably converged**, so **"N2 is slower" is established while "no detectable
difference in final score" is provisional**: a longer run could separate them in either direction.

**Five control graphs, and they disagree with each other.** SH graph means span 1.384–1.607 and RD
1.406–1.530, against N2's single value of 1.412. N2 is one draw sitting inside that spread. There is
only one real connectome, so its interval carries run-to-run variation only while the controls also
carry graph-to-graph variation; that asymmetry cannot be fixed by more compute.

**The interface probably favours shallow graphs — though by less than we first reported.** Weys are
given separate left and right food readings, so foraging can be solved by wiring a sensor difference
almost straight to the turn read-out, and a task solvable in one hop rewards graphs that offer one
hop. But measured across the ten control graphs actually used, N2 is **not** meaningfully deeper for
locomotion: mean distance from the mapped sensors to the locomotor read-out is **1.17 in N2**,
**1.00–1.17 across the five shuffles**, and **1.06–1.39 across the five random graphs** — N2 sits
inside the shuffle range and below one of the random graphs. The clear depth penalty is to the pump
(3 hops versus 1–2), and the foraging experiment never used the pump. Separately, a real worm cannot
make that left/right comparison at all: *C. elegans* chemotaxis works by sampling concentration over
time while moving, not by comparing two sides at once. The interface is our invention, not biology.

**We do not know why N2 improves more slowly.** Graph distance from sensors to the locomotor
read-out does not explain it, as the numbers above show. Nor do the parameter bounds, which no
condition comes close to. The cause is simply unidentified, and nothing here should be read as
having found it.

**The frozen opponent suite cannot measure combat skill.** It is six **random-weight** strains,
never evolved for anything, and they do not approach opponents: the same six strains dealt 94 and 2
damage against random opponents but 38 063 and 13 244 against coevolved ones, because contact only
happens when someone comes to it. Beating the suite therefore means out-foraging passive random
strains — the coevolved populations ate **4.4× and 3.7×** more than the suite did, while biting
supplied **0.1–0.3%** of their energy. **Experiment 01 contains no test of combat skill against a
competent opponent.** The coevolution score going up says the swarms got better at the game; it does
not say they got better at fighting.

**Combat rests on two runs of one graph.** All coevolution was N2 only: 2 runs, population 16, 20
generations. No shuffled or random graph was ever coevolved. And the showcase shows the design does
not generalise across a 50× change in headcount — strains coevolved at 40 v 40 barely leave their
spawn blocks at 2 000 v 2 000, because arena side grows as √headcount while wey speed does not.

**A wey is not a worm.** No neuromodulation, no plasticity, no biophysics, no muscles, no body
mechanics. The body is a rigid three-point segment and the motor output is a linear read of named
motor neurons. The only things taken from biology are the wiring graph and a hand-chosen mapping of
game quantities onto individual named neurons.

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

## What has been found so far

Full numbers in [`docs/RESULTS.md`](docs/RESULTS.md); every one of them was measured by a script in
`scripts/`.

**The simulator works.** Evolved foragers score **1.398 ± 0.013** against random-weight weys'
**0.432 ± 0.030** on held-out seeds across 3 independent runs, and every run beat the *best of 32*
random strains. They keep 16-18 of 20 weys alive against 6-7, and eat 3.7x more food, so this is
foraging and not an accounting exploit. It still works when eating requires pumping (**8.3x**), and
two-swarm coevolution improves against a frozen opponent suite at a fixed 40 v 40 (run 0
+0.071 → +0.377, run 1 +0.185 → +0.310; 2 of 2 runs improved). With headcounts varying between 50
and 200 the same setup improves in only **1 of 2 runs** (run 0 +0.168 → +0.165, run 1
+0.096 → +0.211): a non-stationary objective is harder.

**Coevolution did not produce any measurable combat tactic.** An earlier version of this README
claimed it learned to flank; that was an artifact of the damage rule's armour weights and has been
retracted — see *Corrections* in [`docs/RESULTS.md`](docs/RESULTS.md) and `DECISIONS.md` D026.
Re-measured per run against the frozen suite inside the same matches, three of four tactics metrics
change sign between the two runs, which is what no effect looks like. **Coevolved swarms appear to
win by foraging, not by fighting:** they take in 4.4x and 3.7x more energy by eating than the
opponents they beat, while biting supplies 0.1–0.3% of their energy. With only two coevolution runs,
all of this is reported per run and no interval over runs is claimed.

**On the claim under test, the answer is: no, and slower.** The full experiment is K=5, R=3 --
five independent SH graphs and five RD graphs with three runs each, and fifteen runs of N2, so every
condition has **15 runs**. It was run twice, with and without per-graph motor gain calibration
(see below). Held-out foraging score, hierarchical bootstrap over graphs and runs:

**Speed of improvement** is the mean of the best-of-generation fitness over all 25 generations of
a run — same units as the foraging score (surviving swarm energy divided by starting swarm energy,
dimensionless). A run that climbs earlier has a higher mean, so **lower means slower**.

| condition | final score at generation 25 (calibrated) | speed of improvement (higher = faster) |
|---|---|---|
| N2 | 1.412 [1.366, 1.453] | 1.359 [1.344, 1.373] |
| SH | 1.458 [1.385, 1.552] | 1.459 [1.433, 1.484] |
| RD | 1.452 [1.398, 1.510] | 1.471 [1.439, 1.506] |

- **Final score at generation 25: no detectable difference.** No contrast separates
  (N2 - SH P = 0.167, N2 - RD P = 0.130). N2's mean sits inside the spread of the individual
  control graphs, not at either end. This is a failure to detect a difference, not a demonstration
  of equality: the N2 - SH interval [-0.148, +0.039] still allows a deficit of roughly 10%.
- **Speed of improvement: N2 is slower**, and clearly so: N2 - SH = -0.100 [-0.129, -0.070] and
  N2 - RD = -0.112 [-0.150, -0.077], both **P < 1/20 000** (zero of 20 000 bootstrap resamples
  favoured N2).
- **SH and RD showed no detectable benefit over each other** on anything measured, so preserving
  the real degree sequence did not help either.

On this task with this interface, the real wiring **improves measurably more slowly, and by
generation 25 no difference in final score is detectable.** Nothing had converged by then (see
Limitations), so this says nothing about a ceiling.

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
almost intact, and is the more robust of the two findings. N2 is the calibration reference, so only
the controls moved; N2 was nevertheless **re-run from scratch in both arms** (15 runs each, about 18
minutes per arm) and all 15 of its held-out scores and speed values came out identical. That is an
observation from one pair of arms on this machine, not a guarantee:
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) explains that CUDA `index_add_` makes GPU runs
**not** guaranteed bit-exact, and nothing here should be taken as promising they will be.

Also measured, and predicted in `DECISIONS.md` D008 before the experiment was run: in N2 the pump
neurons sit **three graph hops** from any sensor, because all somatic-pharyngeal traffic goes
through the two-neuron `RIP<->I1` gap-junction bridge. In every shuffled or random control they are
one or two hops away.

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
  committed next).
- Astra 6 (a GPT model from OpenAI): adversarial review of the specification, which produced the
  statistical design, the resource accounting rules and the numerical stability requirements.
- Claude Code running Claude Opus 5 (Anthropic): every line of code, every measurement, and all
  implementation decisions recorded in DECISIONS.md. It found the motor-gain confound on its own.

Errors and who caught them: the "learned to flank" claim was made by Claude Code and caught by
Claude Fable 5.1 in review (D026). The "N2 is deeper" explanation was made by Claude Fable 5.1,
built on a path length mis-measured by Claude Code, and caught by Claude Code when it re-measured
instead of writing the claim as dictated (C4). No single participant, human or AI, would have caught
both.

The design and implementation came from Anthropic models and the specification review from an OpenAI
model. Reviewers from different model families are less likely to share the same blind spots.

Because the work is AI-generated and has had limited human verification, treat every result as
provisional until someone replicates it.
