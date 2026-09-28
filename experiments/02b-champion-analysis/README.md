# 02b: what experiment 02's champions compute

**Status:** published on main (`e856b7d`, 2026-09-28, D085); exploratory, not pre-registered ·
**Run:** 2026-09-25 (v1 and v2); reconciled with 02's registered result on 2026-09-27 (D063) ·
**Commit:** `7b26c87` (script v2 and its outputs) · **Compute:** about 1.5 GPU-hours

Experiment 02's evolved champions foraged well without detected stereo use, and their strategy
was unknown ([`../02-screening/RESULTS.md`](../02-screening/RESULTS.md)). 02 recommended, before
redesigning the task, replaying matched current input after different histories and measuring the
champions' steering responses directly. 02b is that re-analysis: roadmap item 1, run on 02's
saved genomes, with no evolution. It asks how the champions move and steer, whether their turning
depends on food history, which neurons they cannot lose, how much of the anatomy's synapse
strengths survives evolution, and what that means for the self-consistency experiment 03a.

## The answer in brief

There is no registered outcome. **"Exploratory and descriptive. This analysis was not
pre-registered, and nothing here is a confirmatory claim."** ([`RESULTS.md`](RESULTS.md))

- **It does not revise 02's registered result.** In stereo foraging (T0, biological mapping), the
  champions' turn command is *associated* with which side the food is on, equally for N2 and
  shuffles: the within-wey standardised coefficient is 0.27 for N2 and 0.22 for SH. "This is a
  replay correlation, not evidence that the left-right difference drives the turning." 02's
  registered result is about fitness: feeding both noses the mean costs only +0.027 (N2) and
  +0.023 (SH), below 02's threshold of 0.10. "A turn can covary with the side difference and
  still be worth little score." In 02b's words: "02's primary reading is unchanged." (D063)
- **Champions circle, and slow down on food and near obstacles.** Turn-sign persistence is
  0.997-0.999 in every group.
- **Selection, not parameter drift, made the turning history-dependent.** After identical current
  input, the raw turn read-out differs by food history far more at generation 39 than at
  generation 0 or after 39 generations of mutation without selection, in every group (T0 N2:
  0.095 / 0.452 [0.196, 0.707] / 0.106 [0.052, 0.160]). The difference is a median 0.90-0.95 of
  the steady-state contrast between the two starting levels, and 0.83-0.87 of it survives five
  more ticks: "a slow or persistent memory of level, not a transient derivative."
- **Deletion criticality has a mapping-independent core in N2.** AIZ and RIA are critical in most
  runs under all three food mappings, including R2, whose food neurons are not amphid. Beyond that
  core the critical set shifts: the ranking by mean deletion cost correlates 0.84 (M0 against R1)
  and 0.80 (M0 against R2), and the 20 most critical neurons overlap only 10 and 9 times. N2
  champions have 54.5 [40.9, 68.1] critical neurons, SH champions 88.1 [77.0, 99.2].
- **For 03a:** 94 of the 96 most critical N2 targets connect directly to interface neurons.
  Deleting only those edges costs a median 35% of what full deletion costs, and 03a keeps those
  edges fixed.
- **Anatomical magnitudes are largely eroded by generation 39:** the rank correlation of |w| with
  anatomy falls from 1.0 to 0.35 (N2) and 0.36 (SH).
- **What it does not show:** whether the turn *uses* the side difference in a way that matters for
  score (02 says it mostly does not); whether the history effect helps foraging (not tested);
  whether the criticality differences come from the mapping or from evolutionary history (the
  mappings used separately evolved champions).

## Design

- **Champions:** unless stated, generation 39 of 02's cells T0-M0 and T1-M0: 8 N2 runs and 16 SH
  runs (8 graphs × 2). Generation-0 champions are the comparison where stated. N2's T1-R1 and
  T1-R2 champions (8 each) are the criticality controls.
- **Intervals:** Student t over runs. SH graph clustering is not modelled.
- **Stages** (`analyse.py`; each writes `<stage>.json` in this folder):
  - `behaviour`: replays on 8 probe worlds, per tick, weys tracked individually. Standardised
    regression of the motor commands on five sensed quantities (food level, food change, food
    left minus right, collision left minus right, collision total), pooled and within wey (each
    wey's own mean removed); turn-sign persistence of the same wey across ticks.
  - `response`: the input-response probe on the evolved T0-M0 genomes (fixed artificial input from
    rest), next to their stereo-use scores from 02's `probes.json`.
  - `history`: one stimulus bank per run (the mean sensed signals, ticks 20-60, of the
    generation-39 champion's replay). After 100 ticks at a starting level, food reaches the same
    final value over 10 ticks, rising from a quarter of it or falling from 1.75 times it. The raw
    read-out, before gain and clip, is measured on the final tick, with the steady-state contrast
    and the decay over 5 more ticks. Tested on generation 0, generation 39, and a mutation-only
    drift control (the generation-0 champion mutated 39 times without selection, 4 replicates).
  - `criticality`, `criticality_R1`, `criticality_R2`: each of the 245 eligible neurons (not
    mapped, not pharyngeal) deleted in turn from each T1 champion with a true deletion operator
    (`wormwars/deletion.py`), scored on 32 probe worlds with the run's seed. Every batch carries a
    null strain. "Critical" means a drop above 5% of the intact score, 03a's performance margin.
  - `kept_edges`: for each N2 T1-M0 champion's 12 most critical neurons, deleting only their edges
    to interface neurons, against full deletion.
  - `magnitudes`: Spearman correlation (average ranks for ties) of |w| with the anatomical
    magnitude over each champion's chemical edges.
  - `summarise`: every number `RESULTS.md` reports, from the files above plus the connectome
    (`summary.json`).
- **Fixed in advance:** nothing. The analysis is exploratory and was not pre-registered.

## Caveats and corrections

- **v1 was corrected after review (D048 → D049).** Astra 6 and Fable 5.1 reviewed v1 and
  confirmed its numbers and the deletion operator. Bugs fixed in v2: turn persistence compared
  neighbouring weys, not the same wey over time; the history table's forward values were
  censored by the motor clip; rank correlations mishandled ties; `delete_neurons` accepted index
  −1. Readings withdrawn or corrected: "N2 circles a little less"; "evolved N2 champions steer
  toward food; shuffles do not" (it rested on two champions); "AWC and ASE become critical" (they
  were not eligible under M0); "hubs" (replaced by degree percentiles: RIA 98-99th, AIZ 78-89th,
  AIY 58-65th). Controls added: the drift control, a shared stimulus bank per run, the R2
  criticality control, the kept-edge check and a null strain per deletion batch.
- **Reconciled with 02 before publication (D062, D063).** The owner's publishing plan required
  02b to be reconciled with 02's registered result before reaching main. In the pre-push review
  (Astra 6), "steer by which side the food is on" became a replay association with the turn
  command. A table in `RESULTS.md` (section
  1) sets the task, measure and output against 02's registered primary, and 02b says it does not
  revise 02's primary reading.
- **Correlations, not causes.** The behaviour regressions are replay correlations. Removing each
  wey's mean does not remove time-varying confounds from the trajectory (Astra). The food-change
  coefficient is not evidence of temporal sensing.
- **The input-response probe shows no group-level change:** N2's signed turn toward food is +0.009
  [−0.007, +0.026] at generation 39 (5 of 8 positive), and two champions carry the mean.
- **Criticality under three mappings** used separately evolved champions, so mapping and
  evolutionary history are not separated.
- **Noted for the owner, not changed (D063):** 02b names four connections and gives degree
  percentiles and per-neuron interface-edge counts. These are not reconstructable graph data.

## Files

| File | What it is |
|---|---|
| [`RESULTS.md`](RESULTS.md) | The results (v2), the reconciliation with 02, and the changes from v1 |
| [`analyse.py`](analyse.py) | The analysis script; one stage per command-line argument |
| `behaviour.json` | Per-champion replay regressions and turn persistence (48 champions, T0 and T1) |
| `response.json` | Input-response probe on the evolved T0-M0 genomes, with 02's stereo-use scores |
| `history.json` | Matched-input history test: generation 0, generation 39, drift replicates |
| `criticality.json` | Deletion drops per eligible neuron, T1-M0 champions (8 N2, 16 SH) |
| `criticality_R1.json`, `criticality_R2.json` | The same for N2's T1-R1 and T1-R2 champions |
| `kept_edges.json` | Interface-edge-only deletion against full deletion, N2 T1-M0 |
| `magnitudes.json` | Rank correlation of \|w\| with anatomy, generations 0 and 39 |
| `summary.json` | Every reported number, written by `summarise` |
| [`../../wormwars/deletion.py`](../../wormwars/deletion.py) | The deletion operator added for 02b (tested in `../../tests/test_deletion.py`) |
| [`../../wormwars/exp02/probes.py`](../../wormwars/exp02/probes.py) | 02's probes; 02b uses its input-response probe with a `genome` option |
| `../../runs/exp02-screening/` | 02's run data. Committed: `records.jsonl`, `probes.json`. Local-only: the champion genomes (`*.npz`) that every stage except `summarise` loads |

## Reproduce it

**Environment and connectome:** see [../../README.md#how-to-reproduce](../../README.md#how-to-reproduce)
(`pip install -r requirements.txt`, `python scripts/check_env.py`,
`python scripts/fetch_connectome.py`).

**Recompute every reported number from committed files.** `summarise` reads the stage JSON files
in this folder, `runs/exp02-screening/records.jsonl`, 02's `remaps.json` and `calibration.json`,
and the connectome. It needs no genomes:

```
py -3.13 experiments/02b-champion-analysis/analyse.py summarise    # -> summary.json
```

**Rerun the stages.** Every other stage loads 02's champion genomes, which are local-only. To
regenerate them, rerun experiment 02's evolution ([`../02-screening/README.md`](../02-screening/README.md#reproduce-it)).
Then, in this order (`kept_edges` reads `criticality.json`):

```
py -3.13 experiments/02b-champion-analysis/analyse.py magnitudes
py -3.13 experiments/02b-champion-analysis/analyse.py response
py -3.13 experiments/02b-champion-analysis/analyse.py behaviour
py -3.13 experiments/02b-champion-analysis/analyse.py history
py -3.13 experiments/02b-champion-analysis/analyse.py criticality
py -3.13 experiments/02b-champion-analysis/analyse.py criticality_R1
py -3.13 experiments/02b-champion-analysis/analyse.py criticality_R2
py -3.13 experiments/02b-champion-analysis/analyse.py kept_edges
py -3.13 experiments/02b-champion-analysis/analyse.py summarise
```

Each stage overwrites its JSON file here; compare with the committed versions. The whole analysis
took about 1.5 GPU-hours. The script uses CUDA when available.

**What is exactly reproducible** ([../../docs/REPRODUCIBILITY.md](../../docs/REPRODUCIBILITY.md)):
- The committed outputs came from `7b26c87`. Later commits wrapped the script in compute
  accounting, which writes git-ignored `compute/` and `compute.json` here (D069-D072), and changed
  how `wormwars/deletion.py` and the exp02 probes build genomes (D066). For a like-for-like rerun,
  check out `7b26c87`.
- CUDA reproduction is exact only for the same GPU, pinned environment and batch composition.
  Regenerated genomes match 02's only under the same conditions.

## Extend it

- **Separate mapping from evolutionary history** in the criticality map with a cross-mapping test
  on frozen genomes (`RESULTS.md`, section 3).
- **Does the level memory help foraging?** Not tested. N2's random champions carry more history
  than the shuffles' at generation 0 (0.095 against 0.030); experiments 03 and 03r measured
  history dependence in unevolved random brains ([`../03-generation0/`](../03-generation0/),
  [`../03r-replication/`](../03r-replication/)). Where the history effect lives is part of the
  mechanism follow-up ([`../../ROADMAP.md`](../../ROADMAP.md#03-and-03r)).
- **03a's kept-edge risk.** Either search the targets' interface connections, or pick targets
  whose criticality does not come only from interface adjacency
  ([`../../ROADMAP.md`](../../ROADMAP.md#03a-redesign-after-03r-before-any-confirmatory-run)).
  Whether hubs such as RIA are easier or harder to recover is open.

## Record

- Results: [`RESULTS.md`](RESULTS.md). No pre-registration or design document: the analysis is
  exploratory. It builds on 02's [results](../02-screening/RESULTS.md) and
  [pre-registration](../02-screening/PREREGISTRATION.md).
- Reviews, verbatim: v1 by Astra 6 and Fable 5.1, `../../docs/reviews/20260925-184331-02b/`; the
  pre-push review that reconciled 02b with 02, `../../docs/reviews/20260927-160621-pushes/` (Astra)
  and `../../docs/reviews/20260927-160623-pushes/` (Fable).
- Decisions in [`../../DECISIONS.md`](../../DECISIONS.md): D045 (02b first in roadmap v2), D048
  (v1), D049 (v2 after review), D062 (the publishing plan), D063 (the reconciliation), D085
  (published on main).
- Who did what: 02b was run and written up by Claude Code running Claude Opus 5.5 (Anthropic), and
  reviewed by Astra 6 (OpenAI) and Fable 5.1 (Anthropic) ([`../../ROADMAP.md`](../../ROADMAP.md#credits)).
