# 02: a screening of N2 against shuffles, across tasks and food mappings

**Status:** published on main (`5706c7e`; Corrections entry added in `76c613a`, 2026-09-27) ·
**Run:** 2026-09-25 · **Commit:** `225e8f8` (evolution), `971bbb3` (probes and report) ·
**Compute:** 5.64 GPU-hours of evolution and 7.44 GPU-hours in total with the probes, of a
12-hour cap; one RTX 5080

Experiment 01b found that the real *C. elegans* wiring (N2) did better than random graphs on
foraging, and better than or level with shuffles of itself. Experiment 02 asks whether that edge
generalises across tasks and interfaces, and whether it is concentrated where conditions are
worm-like ([`DESIGN.md`](DESIGN.md)). The full grid would cost 40-150+ GPU-hours, so 02 is a
screening fraction of it, capped at 12 GPU-hours, meant to find failure modes and size the full
experiment. The pilot's feasibility gate failed: a pilot champion beat the tuned memoryless
controller without being hurt by the validated history ablation (D038). So 02 measures whether
champions *use* a capability instead of assuming it. Only one outcome carries a verdict: whether
N2's evolved champions depend on the left-right food difference more, and meaningfully, than
the shuffles' champions.

## The answer in brief

- **Registered primary (§4): "challenged: no meaningful N2 use".** The registered prediction:
  *"under this 40-generation procedure, N2 champions show greater, meaningful dependence on
  bilateral food information than champions from the sampled shuffle distribution."* In stereo
  foraging with food entering AWA, AWC and ASE (cell T0-M0), feeding both sides the bilateral
  mean costs N2's generation-39 champions +0.027 [+0.000, +0.060] and the shuffles' +0.023
  [+0.003, +0.047]. The registered threshold for meaningful use is 0.10. The contrast N2 − SH is
  +0.004 [−0.032, +0.044]. In the results' words: "Under the registered reading, 40 generations
  of this search found stereo use in neither group. The registered prediction was tested and
  challenged under this search procedure. Whether N2's wiring could support stereo foraging under
  a different search remains open." ([`RESULTS.md`](RESULTS.md))
- **Exploratory: random N2 brains respond more to food input, not more selectively.** Under the
  biological mapping, their turn read-out responds 3.5-11 times more strongly than the shuffles'
  to a left-right food difference, but more strongly to total food too. Relative to that, N2's
  response is ordinary: 0.49, against 0.45-0.54 for the shuffles. No across-brain uncertainty
  was saved.
- **Exploratory, post hoc: under the biological mapping, the shuffles catch up.** At generation 0
  the mapping interaction favours N2 in both tasks (T0 +0.068 [+0.019, +0.117], T1 +0.069
  [+0.026, +0.111]). The shuffles' best random brains start worse under the biological mapping
  (T0 −0.042 [−0.069, −0.018]) and evolution removes that deficit (+0.019 [−0.001, +0.037]).
  N2's own preference has roughly the same point estimate at both times (+0.026), with intervals
  that include zero.
- **Tripwire fired: shortcuts differ.** With food entering FLP, PHB and PVD (MS), N2 does worse
  than the shuffles; MS advantage minus matched −0.082 [−0.129, −0.020]. The registered
  consequence: routing must stay matched in the full design.
- **What it does not show.** It does not show that shuffles *cannot* use stereo (never claimed
  under any result; in T0-M0, 0 of 8 SH graphs showed detected meaningful use). The jitter probes "neither
  show nor exclude history use". The strength control detected no effect "under this procedure",
  with no equivalence margin, so it does not show that magnitudes do not matter. Only §4 carries a
  verdict; a screening cannot establish specialisation or equivalence.

## Design

All binding details are in [`PREREGISTRATION.md`](PREREGISTRATION.md), fixed on 2026-09-25
before any N2 run. The binding code is the commit the run's `bundle.json` records (`225e8f8`).
Where [`DESIGN.md`](DESIGN.md) (v3) differs, the pre-registration is binding.

- **Brains:** N2, 8 runs per cell (seeds 20000-20007). SH: 8 degree-preserving shuffles, SH1-SH8,
  2 runs each. N2perm1-3 (N2 with anatomical magnitudes permuted within its mask, the strength
  control): T1-M0 only, 2 runs each. Each unit's seed is shared across its cells.
- **Tasks** (single swarm of 20): T0, stereo foraging (odour sigma 1, 200 ticks, food x2, food
  sensing scale halved, pheromone off); T1, single-nose foraging (T0 with one food sample at the
  head, copied to both sides); A, the 01b anchor (01b's world exactly, M0 only).
- **Food mappings** (`remaps.json`, D036): M0 = AWA, AWC, ASE; R1 = ASJ, ASI, ASG; R2 = PLN,
  IL2D, IL2V; MS = FLP, PHB, PVD (T1 only, exploratory shortcut).
- **Cells:** T0 x {M0, R1, R2}, T1 x {M0, R1, R2, MS}, A-M0 and the strength control: 190 runs
  (N2 64, SH 120, N2perm 6). Eight runs continue to 80 generations.
- **Held fixed:** 40 generations, population 32, 8 training worlds per strain, 64 held-out worlds
  per run, 32 integrator substeps, anatomical-magnitude initialisation with random signs, and each
  graph's motor gains calibrated in-world on 2048 genomes (`calibration.json`).
- **Primary estimand:** for a champion and probe p, U_p is the mean over the 64 probe worlds of
  the real score minus the score under p. N2's use is the mean over its runs; SH's is the mean of
  the 8 graph means. Delta = N2 − SH, for the bilateral-mean probe (both sides fed (L+R)/2) in
  cell T0-M0, generation-39 champions. The unit of analysis is the run.
- **Test:** hierarchical bootstrap, 20 000 resamples, seed 0, 95% percentile intervals; a Student
  t-interval for N2's use and a Welch interval for Delta beside them. The verdict uses the
  bootstrap and the threshold USE = 0.10: supported, challenged ("no meaningful N2 use" or
  "contrast reversed"), inconclusive, or withheld if the primary data are incomplete.
- **Secondary outcomes** (registered as exploratory, intervals and no claims): capability use
  under the other probes (swap, single nose, jitter 1 and 3, constant food, collision off), each
  champion's own class, the fitness interactions I(t), the strength control, generation-0
  structure, integrator, convergence, graph covariates and behaviour. "With this many intervals,
  some will exclude zero by chance."
- **Probes** were validated on scripted controllers before use (`probe_validation.json`, D039).
- **Ten tripwires** (§6) are reported whether they fire or not. None can change the §4 verdict
  rule.
- **Disclosed before the run** (§2): the design changed after the failed feasibility gate, and one
  generation-0 N2 measurement was seen (turn response 0.12 to a left-right difference, 0.16 to
  common-mode food, under M0), which motivated the prediction.

## Caveats and corrections

- **Correction, D050 (found 2026-09-25, published 2026-09-27).** The mirror-symmetry reading
  registered in §4 was wrong. The turn read-out is dorsal minus ventral, so symmetric wiring gives
  no left-right comparison for free. D051 adds that symmetric wiring with independently drawn
  random parameters is not equivariant, so a mirror-symmetric control has no predicted direction.
  **No result changes:** the reading applied only to a supported primary. The registered text is
  left unchanged, with a pointer beside it and beside D041. The reasoning came from Fable 5.1's
  review of the pre-registration, Claude Opus 5.5 adopted it, and Astra 6 found the error while
  reviewing experiment 03's design. Full entry: [RESULTS.md, Corrections](RESULTS.md#corrections).
- **Deviation (D041).** Fable 5.1's review of the pre-registration arrived after the evolution had
  started (06:25, from `225e8f8`) and before any probe. All ten points changed probes, analysis or
  wording only, and were committed before any probe ran (`971bbb3`). The run: 190 of 190 runs, no
  crash, no rerun, no dropped probe step.
- **Results revised before publication (D042, D043).** Reviewers found the first write-up
  (`6dc7d71`) too strong. Withdrawn: "evolution erodes N2's advantage" (the shuffles catch up),
  "not on its history", "stereo steering is real but worth little", "N2 reads food more strongly"
  (an intervention effect), and "topology, not strengths".
- **Limitations the results state:**
  - jitter measures history *sensitivity*, not history use (D039); on T0 it measures spatial-noise
    sensitivity, since it moves both noses independently;
  - the strength control is weak: mutation over 40 generations erodes the initial magnitudes;
  - the between-graph variance component is truncated at zero, so graph-to-graph variance is not
    shown to be negligible;
  - the R1 − R2 tripwire was computed on T1 only; on T0 at generation 39 the remaps would have
    disagreed, +0.063 [+0.011, +0.116] (post hoc);
  - D036's no-shortcut rule applied to N2's remaps only: shuffles give the food neurons direct
    read-out weight of 1.5 to 43 per pair, against N2's 0-1;
  - several analyses are post hoc and labelled so in `RESULTS.md`.
- **Later code changes (D065-D067).** The jitter generator was later keyed by world identity. The
  earlier batching defect "does not establish bias in 02's jitter means" (D067 wording), but
  `probe_validation.json`, the `history_probe` block of `diagnostics.json` and the champions'
  jitter scores can no longer be regenerated by current code. They remain reproducible from 02's
  commits. Other changes since then (for example, which strain is saved as champion, D066) also
  mean current code is not the code that ran.

## Files

| File | What it is |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | The binding pre-registration, with disclosures (§2) and review changes (§11) |
| [`DESIGN.md`](DESIGN.md) | The design argument, v3 |
| [`RESULTS.md`](RESULTS.md) | Every result, the Corrections entry, deviations and the review changes |
| `remaps.json`, `calibration.json`, `diagnostics.json`, `probe_validation.json`, `pilot.json` | Frozen inputs, hashed in the pre-registration (§3): wrong food mappings, per-graph motor gains, scripted reference controllers, probe validation, the timed pilot and failed feasibility gate |
| [`exploration/`](exploration/README.md) | Runs on pilot shuffles SH101-SH108 after the gate failed, with their scripts |
| [`reviews/`](reviews/README.md) | Every consultation of Astra 6 and Fable 5.1, verbatim |
| [`../../scripts/exp02.py`](../../scripts/exp02.py) | The driver: subcommands `remaps`, `calibrate`, `diagnostics`, `extend`, `validate-probes`, `pilot`, `run`, `probes`, `report` |
| [`../../wormwars/exp02/`](../../wormwars/exp02/) | `grid` (tasks, cells, seeds, batches), `remaps`, `scripted` (scripted controllers), `probes`, `analysis`, `report`, `structure` (graph covariates), `manifest` (genome replay check) |
| `../../tests/test_exp02_*.py` | The experiment's tests |
| `../../runs/exp02-screening/` | Raw run data. Committed: `records.jsonl` (one record per run), `bundle.json` (config, connectome hashes, environment, commit), `probes.json`, `analysis.json` (the report). Local-only: the champion genomes (`*-g00.npz`, `*-g39.npz`, and `*-g79.npz` for continuation runs) |

## Reproduce it

**Environment and connectome** ([../../README.md#how-to-reproduce](../../README.md#how-to-reproduce)):

```
pip install -r requirements.txt
python scripts/check_env.py
python scripts/fetch_connectome.py
```

The commands below use `py -3.13`, the form in `scripts/exp02.py`'s docstring (the run used
Python 3.13.3).

**Rebuild the report from committed files.** `report` reads `records.jsonl` and `probes.json`,
the frozen inputs, and `runs/exp01b-direction-corrected/records.json`, all committed. It needs no
genomes:

```
py -3.13 scripts/exp02.py report          # -> runs/exp02-screening/analysis.json
```

It overwrites `analysis.json`; compare with the committed version (`git diff`). The primary
block should read `"verdict": "challenged: no meaningful N2 use"`.

**Rerun the whole experiment.** Evolution ran at `225e8f8`, the probes and report at `971bbb3`.
At `225e8f8` the output folder `runs/exp02-screening/` is empty; at the current commit it holds
the committed `records.jsonl` and `probes.json`, and `run` and `probes` resume from them (they
skip completed work). So run from the historical commits:

```
git checkout 225e8f8
py -3.13 scripts/exp02.py run             # 190 runs; default --max-hours 8.0 (evolution budget)
git checkout 971bbb3
py -3.13 scripts/exp02.py probes          # default --max-hours 12.0 (total, evolution included)
py -3.13 scripts/exp02.py report
```

`--device` defaults to `cuda` when available. The frozen inputs are committed; `remaps`,
`calibrate`, `diagnostics`, `extend`, `validate-probes` and `pilot` regenerate them. Expected cost
on one RTX 5080: 5.64 GPU-hours of evolution, 7.44 in total. Compare against the committed
`records.jsonl`, `probes.json` and `analysis.json`.

**What is exactly reproducible** ([../../docs/REPRODUCIBILITY.md](../../docs/REPRODUCIBILITY.md)):
- World maps and seeds are reproducible from the run seeds.
- On CUDA, exact reproduction holds only for the same GPU, the pinned environment and the same
  batch composition, inside `replay_mode()`. The bundle records the environment (Python 3.13.3,
  torch 2.12.0+cu130, RTX 5080) and the commit, but not whether deterministic mode was on (D067).
- A single-strain chunk takes a different GPU kernel path. In the T0 checks, 2-8 of 128 worlds of
  02's champions differed by more than 1e-4 at 200 ticks, with a maximum of 0.027 (D082).
- Current code cannot regenerate 02's jitter draws (D066, D067).

## Extend it

- **A generation-0 study** of structural questions, with many random genomes and shuffles, was
  02's first recommendation. It became experiment 03 and its replication 03r
  ([`../03-generation0/`](../03-generation0/), [`../03r-replication/`](../03r-replication/)).
  One review suggestion stays untested in 02: run the input-response probe with gap junctions off.
- **What the champions do instead of stereo.** 02 recommended richer memoryless baselines, replays
  of matched current input after different histories, and direct measures of steering. 02b took up
  the last two ([`../02b-champion-analysis/`](../02b-champion-analysis/RESULTS.md)).
- **Control graphs:** the no-shortcut rule applied to shuffles, a mirror-symmetric shuffle variant,
  and more than two remaps. Under D036's rule, further remaps (R3, R4) are impossible (D050).
- **A task that forces stereo** would need the memoryless kinesis controller close to
  straight-running; kinesis carries most of the scripted gain here. See also "Sensing over time
  versus stereo sensing" in [`../../ROADMAP.md`](../../ROADMAP.md#later-biology-questions-unscheduled).

## Record

- [Pre-registration](PREREGISTRATION.md), [design](DESIGN.md), [results](RESULTS.md),
  [exploration](exploration/README.md).
- Reviews, verbatim: [`reviews/`](reviews/README.md) (design v1 and v2, plan, T1 memory gate,
  feasibility, go/no-go, pre-registration and its recheck, Fable's pre-registration review,
  results, next step).
- Decisions in [`../../DECISIONS.md`](../../DECISIONS.md): D034-D043 (design to results), D050 and
  D051 (the correction), D063 (the correction's pre-push review), D065-D067 (jitter generator).
- Errors caught in review: episodes 8, 9 and 10 in
  [`../../docs/REVIEW_TRAIL.md`](../../docs/REVIEW_TRAIL.md).
- Who did what: Claude Opus 5.5 designed, pre-registered, ran and wrote up 02, delegated end to end
  by the owner, with Astra 6 (OpenAI) and Fable 5.1 (Anthropic) reviewing at each stage
  ([`../../README.md`](../../README.md#experiment-02-a-screening)).
