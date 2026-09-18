# WormWars 01: *C. elegans* wiring vs. shuffled and random graphs. A foraging null result.

Many parallel 2D worlds on one GPU. In each world, swarms of small creatures called **weys** forage
and fight. Every wey's brain is a small continuous-time recurrent network whose wiring is the real
*C. elegans* connectome (302 neurons, chemical synapses and gap junctions) used as a fixed sparsity
mask. Weights, time constants and biases are evolved. All weys in a swarm share one genome, and
selection acts on team results.

## Summary of findings

Across 15 independent evolutionary runs per condition, the real connectome **reaches the same final
foraging performance** as degree-preserving shuffles of itself and as random sparse graphs of the
same size — no contrast separates — but it **improves measurably more slowly** (N2 − SH = −0.100
[−0.129, −0.070], N2 − RD = −0.112 [−0.150, −0.077], both P = 0.000). **Shuffled and random graphs
are indistinguishable from each other** on everything measured, so preserving the real degree
sequence bought nothing either. A confound was found along the way and removed: the raw magnitude of
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
three had demonstrably converged**, so **"N2 is slower" is established while "N2 ends up equal" is
provisional**: a longer run could separate them in either direction.

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
Re-measured per run against the frozen suite inside the same matches, three of four tactics metrics
change sign between the two runs, which is what no effect looks like. **Coevolved swarms appear to
win by foraging, not by fighting:** they take in 4.4x and 3.7x more energy by eating than the
opponents they beat, while biting supplies 0.1–0.3% of their energy. With only two coevolution runs,
all of this is reported per run and no interval over runs is claimed.

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

## How this was made

The specification was developed in conversation with Claude (Anthropic), reviewed by a second AI
model (Astra), and implemented by Claude Code. Juan H. González Estefan directed the work and made
the decisions, including the calls recorded in `DECISIONS.md`. The retraction in D026 came from
external review of the published results, not from the author of the code.
