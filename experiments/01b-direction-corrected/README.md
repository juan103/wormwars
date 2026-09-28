# 01b: experiment 01's headline comparison, with synapses the right way round

**Status:** published on main (tags `exp01b-v1.0` and `exp01b-v1.1`, same results) · **Run:**
2026-09-24 · **Commit:** `5161e76` (bundle marked dirty only because of untracked review folders) ·
**Compute:** 1.058 h wall time for 45 runs, one RTX 5080

Every run of [experiment 01](../01-foraging-n2-vs-controls/README.md) used chemical synapses that
carried signal from the postsynaptic neuron to the presynaptic one (`DECISIONS.md` D031, found by
Astra 6). So 01 compared the worm's chemical wiring *reversed* against shuffles and random graphs of
that reversed graph. 01b asks 01's question again, with the synapses the right way round:

> Given this specific hand-chosen sensor and motor interface and this game, does the real
> *C. elegans* wiring evolve faster, or end up better, than degree-preserving shuffles of it, or than
> random sparse graphs of the same size?

It reruns only 01's headline arm
(`m9-calibrated`), pre-registered before any run, and changes one thing:
`--chem-direction pre_to_post`.

## The answer, in brief

- **Registered predictions** (from [`PREREGISTRATION.md`](PREREGISTRATION.md)), with outcomes as
  reported in [`RESULTS.md`](RESULTS.md):
  1. "Final held-out score: no contrast separates." **Falsified, in part.** N2 − RD separates, N2
     higher: +0.094 [+0.029, +0.160]. N2 − SH (+0.069 [−0.015, +0.169]) and SH − RD do not.
  2. "SH vs RD: no separation on either measure." **Held**, on both.
  3. "Speed of improvement, N2 against the controls: no prediction." N2 higher than both:
     N2 − SH +0.068 [+0.034, +0.102], N2 − RD +0.067 [+0.021, +0.105].
- **Multiple comparisons.** Six contrasts were tested. With Bonferroni-adjusted intervals
  (99.17%), all three that separate still do.
- **Exploratory: start versus gain.** Split apart, N2's edge over the shuffles is, as a point
  estimate, entirely a higher starting point (+0.074 at generation 0, gain +0.009). Neither
  component separates on its own.
- **Exploratory: the motor-drive confound in 01.** With correct synapses N2's raw random-population
  drive is 0.157, 2nd strongest of 11 (01: 0.082, weakest). "That confound was largely a product
  of the reversal."
- **What this does not show:** that N2 *improves* faster. The "speed" measure averages all 25
  generations, generation 0 included, so it mixes where a run starts with how much it gains. Nor
  does it show that N2 lies outside the distribution of individual control graphs: N2 ranks first
  of 11 graph means on the speed measure and 2nd on final score, but no rank p-value is offered,
  because the graphs are not exchangeable.

## Design

- **Conditions.** N2 (Cook et al. 2019), SH1-SH5 (degree-preserving shuffles), RD1-RD5 (random
  sparse graphs with matched neuron and edge counts). The same ten control graphs as 01, from the
  same seeds.
- **Runs.** 15 per condition (N2 15; each control graph 3), 45 in total, with 01's run seeds.
  **The unit of analysis is the run.**
- **Budget.** 25 generations x 32 strains x 8 worlds x 400 ticks. Held-out score on 32 world ids
  never used for selection. 8 integrator substeps, as in 01.
- **Motor gain calibration.** The same protocol as 01: each graph's random population is matched to
  N2's mean |forward| and |turn|. The gain values differ from 01's because reversing the synapses
  changes what N2's random population does.
- **Measures.** Final held-out score at generation 25, and the "speed" measure: the mean of
  best-of-generation fitness over generations 0 to 24.
- **Test.** Hierarchical bootstrap, runs nested in graphs, 20 000 resamples. Contrasts N2 − SH,
  N2 − RD and SH − RD on both measures. "A contrast 'separates' when its 95% interval excludes
  zero." P is the fraction of bootstrap differences above zero. Intervals are unadjusted; a
  Bonferroni check over the six contrasts is reported alongside.
- **Fixed in advance.** Design, analysis and predictions in
  [`PREREGISTRATION.md`](PREREGISTRATION.md), committed before any 01b run. It was not changed.
  Everything under "Exploratory" in `RESULTS.md` was chosen after seeing the data, much of it at
  the suggestion of the two pre-publication reviewers (D033).
- **One change, checked.** The code run with `--chem-direction post_to_pre` reproduces 01's
  `m9-calibrated` N2 run 0 (seed 40001) and SH1 run 0 (seed 40016) to the last bit.

## Caveats and corrections

- **D033, pre-publication review.** Astra 6 (OpenAI) and Fable 5.1 (Anthropic) both said "do not
  publish as is". The first write-up (`d028a15`) claimed that "the real wiring improves faster",
  that N2 "ends at least level with the shuffles", that every number was pre-registered, and gave
  a rank "p ≈ 0.09". All four were withdrawn in `3d230e5`. The review also fixed a leaking legacy
  default in the code and restored 01's frozen record. The pre-registration was not changed.
- **Calibration is approximate (D033, D035).** At the fitted gains a random population reaches
  84-97% of the target |forward| (N2 95%, SH 84-93%, RD 86-97%) and 92-100% of |turn|. The
  residual favours N2 over the shuffles on average and could contribute to N2's higher starting
  point. The per-graph gains, fitted on 24 genomes, carried about 12% sampling error (D035). The
  comparison is of the whole pre-registered pipeline, recalibration included; it does not isolate
  the synapse direction with the motor gains held fixed.
- **Absolute scores are not comparable with 01.** N2 is the calibration reference, and its
  stronger drive doubled the calibration target (reference |forward| 0.326 in 01, 0.626 in 01b).
  Only the contrasts are comparable.
- **Integrator (D032, D033).** On 01b's champions, 0 of 1440 weys have a motor read-out error above
  0.05 between 8 and 32 substeps (input seed 300, max 0.049). A reviewer with other inputs (seed
  200) found 8 of 1440 (max 0.26). Their effect on fitness was not measured, and the exposure is
  not symmetric across conditions.
- **Food ceiling (D034).** While experiment 02's task world was being chosen, the best scripted
  controllers ate essentially all the food in 400 ticks (a median of 98-100%). D034: "This probably also compressed 01b's comparison: its champions scored
  close to the scripted ceilings."
- **Score per GPU-hour is not a result.** `REPORT.md` reports it; wall time per run rose from 74-77 s
  to 87-97 s partway through, with the machine shared.
- **Scope.** One hand-chosen interface, one foraging task, 25 generations, five shuffles and five
  random graphs against one real graph. 01's uncalibrated arm, pump-gated foraging, coevolution and
  combat tactics were not rerun and still describe the reversed graph.

## Files

| File | What it is |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | Design, analysis, predictions and outcome readings, committed before any run |
| [`RESULTS.md`](RESULTS.md) | Pre-registered results, then the exploratory analyses, then the side-by-side with 01 |
| `../../scripts/experiment.py` | Runs the comparison and writes the pre-registered report (`REPORT.md`) |
| `../../wormwars/calibration.py` | Per-graph motor gain calibration |
| `../../runs/exp01b-direction-corrected/` | Committed: `bundle.json`, `records.json`, `REPORT.md`, 45 per-run logs and 45 champions (`champion-<graph>-run<r>.npz`) |
| `../../tests/test_direction.py` | Direction tests, including the legacy-mode reproduction of a published 01 score |

`RESULTS.md` does not name a script for its exploratory analyses.

## Reproduce it

Set up the environment as in [`../../README.md#how-to-reproduce`](../../README.md#how-to-reproduce),
then fetch the connectome (it is not redistributed):

```
python scripts/fetch_connectome.py
```

The run, as pre-registered. Use a new `--out` to keep the committed run intact:

```
python scripts/experiment.py --k 5 --runs 3 --generations 25 --population 32 --worlds 8 \
    --ticks 400 --holdout 32 --base-seed 40000 --conditions N2,SH,RD --calibrate \
    --chem-direction pre_to_post --device cuda --out runs/exp01b-repro
```

`experiment.py` writes the report itself. Compare `records.json` and `REPORT.md` with
`runs/exp01b-direction-corrected/`. The original took 1.058 h of wall time on an RTX 5080; the
pre-registration budgeted up to 4.5 h.

**What has been checked since (D081).** On the same RTX 5080, at later code, all 9 01b champions
of N2, SH1 and RD1 reproduce their stored `holdout_score` to 6 decimals, in default and replay mode,
and generations 0-2 of N2-run00, rerun from its bundle configuration and seed, reproduce the
logged best, mean and best nickname. These checks are in `scripts/t0_gpu_checks.py`, which also
runs T0's other GPU checks and by default writes `docs/foundations/T0_gpu.json`.

**What is exact and what is not.** Exact CUDA reproduction is claimed only under `replay_mode()`,
for the same GPU, pinned environment and batch composition. A single-strain chunk is its own
composition and can differ slightly from the same genome inside a population batch (D082). 01b's
bundle records `git_dirty: true`, so the executed source cannot be checked out exactly. See
[`../../docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md).

## Extend it

- **Rerun the arms 01b left out.** The uncalibrated arm, pump-gated foraging and coevolution with
  its tactics "can each be rerun later under their own pre-registration".
- **More control graphs.** Showing that N2 lies outside the distribution of individual graphs needs
  more of them (`RESULTS.md`). Experiment 03's five validated null ensembles are to become the
  standard controls ([`../../ROADMAP.md`](../../ROADMAP.md), Track B).
- **The pharynx.** N2 against SH and RD has never been run on pump-gated eating, where every route
  from a sensor to the pump neurons crosses the `RIP↔I1` bridge (D008, README Limitations).
- **Longer or harder runs.** A longer budget needs more integrator substeps or a semi-implicit
  chemical term (D032), and a world without the food ceiling (D034). Experiment 02
  ([`../02-screening/`](../02-screening/)) changed the task world for that reason (D034).

## Record

- Pre-registration: [`PREREGISTRATION.md`](PREREGISTRATION.md) (committed in `5161e76`, with the fix).
- Results: [`RESULTS.md`](RESULTS.md); first write-up `d028a15`, revised after review in `3d230e5`.
- Decisions in [`../../DECISIONS.md`](../../DECISIONS.md): D031 (the bug and the fix), D032
  (integrator), D033 (the pre-publication review), D034 (food ceiling), D035 (calibration sample
  size), D081 and D082 (later replay checks and the CUDA contract).
- Reviews: the prompt and both answers of the D033 review are kept outside the repository. The
  review trail is [`../../docs/REVIEW_TRAIL.md`](../../docs/REVIEW_TRAIL.md), episodes 6 and 7.
- The superseded experiment and its correction:
  [`../01-foraging-n2-vs-controls/CORRECTIONS.md`](../01-foraging-n2-vs-controls/CORRECTIONS.md) (C5).
