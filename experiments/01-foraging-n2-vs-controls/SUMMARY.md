# WormWars 01: *C. elegans* wiring vs. shuffled and random graphs. A foraging null result.

Frozen record of experiment 01. The files beside this one are copies taken at the moment of
freezing: `RESULTS.md`, `DECISIONS.md` and `PROVENANCE.md` as they stood, the exact configuration of
every run in `configs/`, and sha256 hashes in `bundle-hashes.txt`. The repository root keeps living
versions that may move on; these do not.

---

## What was asked

> Given this specific hand-chosen sensor and motor interface and this game, does the real
> *C. elegans* wiring evolve faster, or end up better, than degree-preserving shuffles of it, or than
> random sparse graphs of the same size?

Three conditions on the same 302 neurons with the same neuron indices, so the sensor and motor
mapping lands identically in all of them: **N2** (the real connectome, Cook et al. 2019), **SH**
(five independent degree-preserving shuffles) and **RD** (five independent random sparse graphs with
matched neuron and edge counts). Fifteen independent evolutionary runs per condition. The unit of
analysis is the run.

## What was found

**On the question as asked: no, and slower.**

| | final held-out score | speed of improvement |
|---|---|---|
| N2 | 1.412 [1.366, 1.453] | 1.359 [1.344, 1.373] |
| SH | 1.458 [1.385, 1.552] | 1.459 [1.433, 1.484] |
| RD | 1.452 [1.398, 1.510] | 1.471 [1.439, 1.506] |

- **Final performance: a null.** No contrast separates (N2−SH P = 0.167, N2−RD P = 0.130). N2's mean
  sits inside the spread of the individual control graphs, not at either end.
- **Speed of improvement: N2 is slower**, clearly: N2−SH = −0.100 [−0.129, −0.070] and
  N2−RD = −0.112 [−0.150, −0.077], both P = 0.000.
- **SH and RD are indistinguishable from each other** on everything measured, so preserving the real
  degree sequence bought nothing either.
- **We do not know why N2 is slower.** Graph distance from sensors to the locomotor read-out does not
  explain it (N2 1.17, inside the shuffles' 1.00–1.17), and no condition approaches the parameter
  bounds.

**A confound was found and removed, and the experiment reported both ways.** The raw magnitude of
the motor read-out is a property of the graph, and N2 is the weakest of the seven graphs first
tested. The motor gain had been hand-tuned on N2, so under one fixed gain the controls simply moved
more before evolution started, and foraging rewards moving. With per-graph gain calibration the
final-score deficit disappears; the speed deficit survives almost intact. Both arms are reported.

**The simulator itself works.** Evolved foragers score 1.398 ± 0.013 against random-weight weys'
0.432 ± 0.030 on held-out seeds, beating not just the average random strain but the best of 32, in
3 of 3 independent runs. It still works when eating requires pumping (8.3×).

**Combat produced a second null.** An earlier version of this work claimed coevolved swarms "learned
to flank". That was an artifact of the damage rule's armour weights and is retracted
(`DECISIONS.md` D026, `RESULTS.md` Corrections C1). Re-measured, three of four tactics metrics change
sign between the two runs. Coevolved swarms win by **foraging**, not fighting: they eat 4.4× and
3.7× more than the opponents they beat, while biting supplies 0.1–0.3% of their energy.

## What this does **not** show

- **Nothing about biological wiring in general.** This is one wiring graph, one hand-built interface,
  one task, one search algorithm, one set of parameter bounds. A null here is a null about that
  combination.
- **Nothing about the pharynx.** The three-way comparison ran only on foraging with automatic eating.
  It was never run on combat or on pump-gated eating — the one place N2 is measurably handicapped by
  graph depth (3 hops from sensors to the pump neurons, against 1–2 in all ten controls), because all
  somatic–pharyngeal traffic crosses the two-neuron `RIP↔I1` bridge. Combat and pumping ran on N2
  alone.
- **Nothing about convergence.** Neither N2 nor RD had demonstrably stopped improving when the
  25-generation budget expired (+0.070 and +0.054 over the last ten generations; only SH was flat at
  +0.002). "N2 is slower" is established; "N2 ends up equal" is provisional.
- **Nothing about combat skill.** The frozen opponent suite is six random-weight strains that do not
  approach opponents. Beating it means out-foraging passive strains. There is **no test here of
  combat against a competent opponent**.
- **Nothing that generalises across scale.** Strains coevolved at 40 v 40 barely leave their spawn
  blocks at 2 000 v 2 000.
- **Nothing about worms.** A wey is a worm-shaped neural network in a game body: no neuromodulation,
  no plasticity, no biophysics, no muscles, no body mechanics.

## Corrections made during this experiment

Four, all recorded in `RESULTS.md` → *Corrections*, with the superseded numbers kept:

| | what |
|---|---|
| C1 | "Learned to flank" retracted — the metric was pinned by the armour weights |
| C2 | M7 coevolution figures superseded by a re-run after the food economy was fixed |
| C3 | Tactics figures restated per run and pooled by damage rather than by strain |
| C4 | Sensor-to-motor distance had the pump folded in; separated, N2 is not deeper for locomotion |

## Reproducing it

Run from the repository root, after `scripts/fetch_connectome.py`:

```
python scripts/evolve_forage.py --runs 3 --generations 30 --worlds 8 --out runs/m4
python scripts/experiment.py --k 5 --runs 3 --generations 25 --worlds 8 --calibrate --out runs/m9-calibrated
python scripts/experiment.py --k 5 --runs 3 --generations 25 --worlds 8 --out runs/m9-uncalibrated
python scripts/coevolve.py --runs 2 --generations 20 --population 16 --size 40 --out runs/m7
python scripts/tactics.py --runs runs/m7 --out runs/tactics
```

Exact arguments for every run are in `configs/`. Total cost of the reported experiments was about
2.2 GPU-hours on one RTX 5080. Exact reproduction is claimed only under `replay_mode()`; see
`docs/REPRODUCIBILITY.md`.
