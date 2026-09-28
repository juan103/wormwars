# 01: foraging, N2 vs shuffled and random graphs (synapses reversed; superseded)

**Status:** superseded by [01b](../01b-direction-corrected/README.md); frozen at tag `exp01-v1.0` ·
**Run:** 2026-09-17 to 2026-09-18 · **Commit:** `cebbefa` for the headline arm (the bundle records
the pre-rewrite hash `d4f4acf`; working tree dirty) · **Compute:** 0.897 GPU-hours for the headline
arm; 2.66 hours for all reported experiments by the committed timing records, before ablations
and benchmarks (the frozen `SUMMARY.md` says about 2.2; corrected in D088), one RTX 5080

> **Read this first.** Every run in this experiment used chemical synapses that carried signal
> from the postsynaptic neuron to the presynaptic one (`DECISIONS.md` D031, correction C5 in
> [`CORRECTIONS.md`](CORRECTIONS.md)). What it tested was the worm's chemical wiring *reversed*,
> with its real gap network, against shuffles and random graphs *of that reversed graph*. That
> comparison is internally valid. It is not a test of the real *C. elegans* wiring. The headline
> arm was rerun with the synapses the right way round as [experiment 01b](../01b-direction-corrected/README.md).
> Cite 01b for any claim about the real wiring.

The question, as the frozen summary put it:

> Given this specific hand-chosen sensor and motor interface and this game, does the real
> *C. elegans* wiring evolve faster, or end up better, than degree-preserving shuffles of it, or than
> random sparse graphs of the same size?

This was the project's first experiment. It built the simulator (milestones M0-M11 in
[`../../PLAN.md`](../../PLAN.md)), checked that evolution works in it, and then ran the three-way
comparison. It also ran pump-gated foraging and two-swarm coevolution (on N2 only), ablations of
the calibrated arm's 45 champions, and a scaling benchmark. This folder is a frozen record: the files pinned in
`bundle-hashes.txt` must not change. This README and `CORRECTIONS.md` are not pinned.

## The answer, in brief

Experiment 01 has no pre-registration document. Everything below describes the **reversed** graph.

- **Speed of improvement: N2 was slower.** The measure is the mean of the best-of-generation
  fitness over all 25 generations. With motor gains calibrated: N2 − SH = −0.100 [−0.129, −0.070]
  and N2 − RD = −0.112 [−0.150, −0.077], both P < 1/20 000. **The sign reverses with the
  direction of the synapses:** 01b gives +0.068 [+0.034, +0.102] and +0.067 [+0.021, +0.105]. In
  the main README's words, "That conclusion does not hold for the real wiring".
- **Final held-out score at generation 25: no separation** with calibrated gains
  (N2 − SH −0.047 [−0.148, +0.039], P = 0.167; N2 − RD −0.041 [−0.113, +0.029], P = 0.130). `RESULTS.md`
  calls this "a failure to detect a difference, not a demonstration of equality".
- **SH vs RD: no separation** on either measure.
- **The motor-drive confound.** N2's raw motor read-out was the weakest of the seven graphs first tested, so
  without calibration the controls moved more before evolution started. Uncalibrated, N2 was lower
  on final score too (N2 − SH −0.110 [−0.185, −0.026], P = 0.005). 01b found that with correct
  synapses N2 is among the strongest drivers, "so that confound was largely a product of the
  reversal".
- **Other results, all on N2 alone and all still describing the reversed graph:** evolved foragers
  beat random-weight strains (1.398 ± 0.013 against 0.432 ± 0.030, 3 of 3 runs above the best of
  32 random strains), also with pump-gated eating (0.810 ± 0.045 against 0.098 ± 0.016).
  Coevolved swarms win by foraging, not fighting: they eat 4.4x and 3.7x more than the frozen
  opponents they beat, and biting supplies 0.1–0.3% of their energy. The claim that they "learned to
  flank" is retracted (C1, D026).
- **Ablations (M10), on the calibrated arm's champions, also reversed:** "no emergent target is
  clearly above its matched random controls".

**What it does not show.**

- Anything about the real wiring. The reversed graph was tested (C5).
- Anything about the pharynx. The three-way comparison ran only on foraging with automatic eating.
  The path argument about the pump (D008, C4) was counted in the true direction, not the one the
  simulation ran.
- Anything about convergence. Neither N2 nor RD had demonstrably stopped improving at generation
  25 (+0.070 and +0.054 over the last ten generations; only SH was flat at +0.002).
- Combat skill against a competent opponent. The frozen suite is six random-weight strains.
- Anything about worms. A wey has no neuromodulation, plasticity, biophysics, muscles or body
  mechanics.

## Design

- **Conditions.** N2 (the real connectome, Cook et al. 2019), SH (five independent
  degree-preserving shuffles, SH1-SH5) and RD (five random sparse graphs with matched neuron and
  edge counts, RD1-RD5). All share the same 302 neurons and indices, so the sensor and motor
  mapping lands identically.
- **Runs.** 15 per condition: N2 15 runs, each control graph 3. 45 runs per arm. **The unit of
  analysis is the run.**
- **Budget.** 25 generations, population 32, 8 worlds per strain, 400 ticks. Held-out score on 32
  world ids never used for selection. Genome: 5 404 parameters (3 709 W + 1 091 G + 302 tau +
  302 bias); the wiring mask is fixed. 8 integrator substeps.
- **Measures.** Final held-out score (surviving swarm energy divided by starting swarm energy) at
  generation 25, and speed of improvement (the mean of best-of-generation fitness over all 25
  generations, "area under the fitness curve").
- **Statistics.** Hierarchical bootstrap over graphs and runs, 20 000 resamples, 95% intervals.
  P is a bootstrap tail probability; "P < 1/20 000" means no resample favoured the first condition.
- **Two arms.** `m9-calibrated` matched each graph's motor gain so every condition's random
  population starts with the same mean |forward| and |turn| as N2 (`wormwars/calibration.py`).
  `m9-uncalibrated` used one fixed gain. Calibration was added after the M5 pilot (K=3, R=2) found
  N2's raw read-out weakest (0.0815 against 0.102-0.159). Both arms are reported.
- **What was fixed in advance.** No pre-registration document. The milestone-9 design in
  `PLAN.md` ("K=5, R=3 per graph, K·R runs for N2, hierarchical bootstrap, per-evaluation and
  per-GPU-hour") and the docstring of `scripts/experiment.py`.

## Caveats and corrections

- **C5, synapses reversed (D031, D033).** `Genome.dense` stored weights pre-by-post and
  `Brain.step` multiplied by their transpose. The bug was present from M2, before any run, and was
  found by Astra 6 (OpenAI) reviewing the roadmap. Gap junctions were unaffected. The uncalibrated
  arm, pump-gated foraging, coevolution and the combat tactics were **not** rerun and still
  describe the reversed graph. The correction lives in the unfrozen `CORRECTIONS.md`, and the
  frozen files were restored byte for byte to `exp01-v1.0` (D033).
- **C1, "learned to flank" retracted (D026).** The metric was pinned at 2 / 2.25 = 0.8889 by the
  armour weights.
- **C2, M7 figures superseded (D023).** Re-run after food was made to scale with headcount.
- **C3, tactics restated per run.** n = 2 runs, so no interval over runs; pooled ratios.
- **C4, sensor-to-motor distance.** The first figure folded in the pump. Separated, N2's
  locomotor distance (1.17) is inside the shuffle range (1.00–1.17); the pump is 3 hops in N2 and
  1–2 in every control. C5 adds that these hops were counted in the true direction.
- **D024, ablation gains.** The first ablation report replayed champions at the wrong motor gains.
  The reported M10 numbers replay each champion at the gains it was evolved under.
- **D030, gap initialisation.** 4 of 1091 junctions start clipped at `g_max`. SH and RD preserve
  the weight multiset, so the same four clip in every condition.
- **D032, integrator.** On 01's 45 champions, 0 of 1440 weys have a motor read-out error above
  0.05 between 8 and 32 substeps.
- **D027, D028, rewritten history.** The git history was rewritten twice before publication, so
  the commit hashes inside the run bundles no longer exist. `commit-hash-map.txt` maps them.
- **Frozen hashes pin CRLF.** `bundle-hashes.txt` was written on Windows. On Linux or macOS, use
  `pytest tests/test_frozen_records.py` or convert to CRLF before hashing (see `CORRECTIONS.md`).
- **Convergence and power.** Nothing had converged by generation 25, and the calibrated N2 − SH
  final-score interval still admits a deficit of about 10%.

## Files

| File | What it is |
|---|---|
| [`SUMMARY.md`](SUMMARY.md) | The frozen one-page summary (frozen) |
| [`RESULTS.md`](RESULTS.md) | Every measured number, M0-M11, with corrections C1-C4 (frozen) |
| [`CORRECTIONS.md`](CORRECTIONS.md) | C5, found after freezing: the reversed synapses, with the 01 vs 01b table (not frozen) |
| [`DECISIONS.md`](DECISIONS.md), [`PROVENANCE.md`](PROVENANCE.md) | D001-D030 and the connectome provenance as they stood at freezing (frozen) |
| [`configs/`](configs/) | Exact arguments and config of every run: `m4`, `m5`, `m7`, `m7-varied`, `m8`, `m9-calibrated`, `m9-uncalibrated` (frozen) |
| [`runs-index.json`](runs-index.json) | Run directory, script and recorded git commit of each run (frozen) |
| [`commit-hash-map.txt`](commit-hash-map.txt) | Maps the pre-rewrite hashes in the bundles to this history (frozen) |
| [`bundle-hashes.txt`](bundle-hashes.txt) | sha256 of every frozen file and of the run bundles |
| `../../scripts/experiment.py` | The N2/SH/RD comparison (M5, M9); writes `bundle.json`, `records.json`, `REPORT.md` |
| `../../scripts/evolve_forage.py` | Foragers vs random weys (M4; M8 with `--stage 2`) |
| `../../scripts/coevolve.py`, `../../scripts/tactics.py` | Two-swarm coevolution (M7) and the tactics metrics (M10) |
| `../../scripts/ablate.py`, `../../scripts/bench_scaling.py`, `../../scripts/showcase.py` | Ablations (M10), scaling (M11), the 2000 v 2000 showcase |
| `../../wormwars/calibration.py` | Per-graph motor gain calibration |
| `../../runs/m9-calibrated/`, `../../runs/m9-uncalibrated/` | Committed: bundle, `records.json`, `REPORT.md`, per-run logs and the 45 champions of each arm |
| `../../runs/m4/`, `m5/`, `m7/`, `m7-varied/`, `m8/`, `ablation/`, `tactics/`, `scaling.*` | Committed run data of the other milestones. The frozen opponent suite is not committed; it is regenerated from its seed (D028) |

## Reproduce it

Set up the environment as in [`../../README.md#how-to-reproduce`](../../README.md#how-to-reproduce),
then fetch the connectome (it is not redistributed):

```
python scripts/fetch_connectome.py
```

**The headline arm, in legacy (reversed) mode.** Only `scripts/experiment.py` has the direction
switch. Its current defaults are `--chem-direction pre_to_post` and `--base-seed 20000`, so both
must be given. The other arguments are those recorded in `configs/m9-calibrated.json`:

```
python scripts/experiment.py --k 5 --runs 3 --generations 25 --population 32 --worlds 8 --ticks 400 --holdout 32 --base-seed 40000 --conditions N2,SH,RD --calibrate --chem-direction post_to_pre --device cuda --out runs/m9-calibrated-repro
```

Drop `--calibrate` for the uncalibrated arm. Compare `records.json` and `REPORT.md` with
`runs/m9-calibrated/`. The original arms took 0.897 h and 0.892 h of wall time on an RTX 5080
(`REPORT.md`). 01b's pre-registration records that two reproduction runs at the fix took 126 s and
356 s, against 01's 71 s per run. The short commands in the frozen `SUMMARY.md` omit
`--base-seed` and `--chem-direction`, so under current code they run a different experiment.

`evolve_forage.py` and `coevolve.py` have no direction switch. Under current code they run with the
synapses the right way round, so they cannot reproduce M4, M7 or M8. Their exact arguments are in
`configs/`.

**What has been checked.** At the fix, rerunning N2 run 0 (seed 40001) and SH1 run 0 (seed 40016)
end to end in legacy mode reproduced the held-out score, survival, training score, AUC and SH1's
calibrated gains to the last bit (D031; one-off, not kept). The check anyone can repeat, on CUDA:

```
python -m pytest tests/test_direction.py -k legacy_mode_reproduces
python -m pytest tests/test_frozen_records.py
```

The first replays 01's N2 run-0 champion on its 32 held-out worlds and requires the published score
to the last bit. Exact CUDA reproduction is claimed only under `replay_mode()`, for the same GPU,
pinned environment and batch composition; a single-strain chunk is its own composition. See
[`../../docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md).

## Extend it

- **Use 01b, not this.** The headline comparison with correct synapses is
  [01b](../01b-direction-corrected/README.md).
- **The arms never rerun.** The uncalibrated arm, pump-gated foraging and coevolution with its
  tactics still describe the reversed graph. 01b's pre-registration says each "can be rerun later
  under their own pre-registration".
- **The pharynx.** N2 against SH and RD was never run on pump-gated eating, the one place where
  N2's two-neuron `RIP↔I1` bridge should matter (D008; README Limitations).

## Record

- Frozen record: tag `exp01-v1.0`; [`SUMMARY.md`](SUMMARY.md), [`RESULTS.md`](RESULTS.md),
  [`bundle-hashes.txt`](bundle-hashes.txt).
- Correction: [`CORRECTIONS.md`](CORRECTIONS.md) (C5), also C5 in
  [`../../docs/RESULTS.md`](../../docs/RESULTS.md).
- Decisions: D001-D030 in the frozen [`DECISIONS.md`](DECISIONS.md); D031, D032 and D033 in
  [`../../DECISIONS.md`](../../DECISIONS.md).
- Review trail: [`../../docs/REVIEW_TRAIL.md`](../../docs/REVIEW_TRAIL.md), episodes 1-6 (the flank
  retraction, the path length, the data leak, pickle loading and the reversed synapses).
- The rerun: [`../01b-direction-corrected/`](../01b-direction-corrected/).
