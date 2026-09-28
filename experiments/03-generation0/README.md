# 03: Generation-0 structure: N2 against five null ensembles

**Status:** published on main (`e856b7d`, D085); replicated by [03r](../03r-replication/README.md) ·
**Run:** 2026-09-26 · **Commit:** `132acae` · **Compute:** 19.75 GPU-hours (cap 24), one GPU,
645 graphs

Every N2-specific signal in the series so far appeared at generation 0, before selection: 01b's
head start, 02's generation-0 mapping interaction, 02's larger input sensitivity, and 02b's larger
history dependence in random N2 brains. The shuffles used until then differed from N2 in generic
ways: mirror symmetry, food-to-motor routing, the class structure of the wiring, and where the
anatomical weights sit. So 03 asks, without evolution: at generation 0, is N2 *distinctive
relative to null ensembles that preserve those generic properties*, and is what distinguishes it
tied to food information? ([`DESIGN.md`](DESIGN.md), "The question".)

## The answer, in brief

- **P4, history dependence: "distinctive relative to every ensemble"** (registered, §6), with a
  Holm-adjusted p of **0.0465**. N2 = 0.931. N2 is above all 128 graphs in four ensembles and
  above 127 of 128 in SH-route: one graph, SH-route-20078, is at 0.934.
- **The result is borderline on the rank gate.** One more SH-route graph at or above N2, or two
  in any other ensemble, would have made it 0.070. The effect margins were never binding.
- **P1, directional selectivity: not distinctive** (Holm-adjusted p 0.93). **P3, food-information
  dependence: the registered criterion was not met** (Holm-adjusted p 0.94). As registered, this
  is not a bound on N2's food-information dependence: the test had little power.
- **Replicated.** The pre-registered full replication gives: *"Replicated under the registered
  single-signal test and under 03's original three-signal rule."* See
  [03r](../03r-replication/README.md).
- **Exploratory (§11):** N2's random brains give a much larger raw food-evoked read-out than any
  shuffle (common mode 5-7 times the ensemble medians, above every one of the 640 ensemble
  graphs). N2's high P4 is not a small denominator: its numerator and denominator are both larger
  than any ensemble graph's. Two readings from experiment 02 do not extend to unselected random
  brains.
- **What it does not show:** the null moves weight placement as well as wiring, so a rejection
  does not isolate wiring. It establishes no memory mechanism and no advantage for the worm, and
  nothing shows the property is food-specific or useful.

Numbers and tables: [`RESULTS.md`](RESULTS.md).

## Design

Binding version: [`PREREGISTRATION.md`](PREREGISTRATION.md), fixed on 2026-09-25 before any N2
measurement. Where it differs from `DESIGN.md` (v3.1), the pre-registration is binding.

- **Graphs:**
  - **N2**, the real wiring (Cook et al. 2019 hermaphrodite).
  - **Five ensembles of 128 graphs each.** All keep N2's degree sequence and move both wiring and
    weight placement:
    - **SH:** ordinary shuffles, the sampler of 01b and 02;
    - **SH-route:** direct read-out edges and weight capped at N2's, for the food pairs of M0, R1
      and R2;
    - **SH-class:** each neuron keeps its in- and out-degree per partner class (the dataset's five
      types);
    - **SH-mirror:** N2's exact mirror-symmetric share, plus the routing cap;
    - **SH-recip:** N2's 669 reciprocal chemical pairs.
  - **Descriptive only:** N2-rev (every chemical synapse's direction reversed) and N2perm1-3
    (N2's weights permuted over its own edges).
  - Every ensemble passed its structural rules before the pre-registration (plateau, acceptance,
    Jaccard ceiling, no substitutions; `ensembles.json`).
- **Unit of analysis:** the graph. Each graph's value is a mean over unselected random genomes,
  measured the same way for every graph (16 shared worlds, 993 000 000 to 993 000 015, run
  seed 3; genome seeds are a SHA-256 hash of the graph's name).
- **Primary signals, with the direction 02 and 02b predict (N2 above):**
  - **P1, directional selectivity:** signed directional turn over absolute common-mode turn, at
    M0, on 2 048 probe genomes;
  - **P3, food-information dependence:** T1 score minus T1-const score (food signal replaced by
    each world's tick-0 mean), 256 genomes × 16 worlds;
  - **P4, history dependence:** \|rising − falling\| turn read-out over the steady-state contrast,
    with one stimulus bank shared by all graphs, on 2 048 probe genomes.
  - P2 (own mapping preference) was a primary in the design and became a secondary before the
    pre-registration (D053).
- **Test:**
  - per ensemble, a one-sided rank p = (r + 1)/129;
  - per signal, the maximum p over the five ensembles (intersection-union);
  - Holm across the three signals;
  - "distinctive" also needs the 90% joint-bootstrap interval of N2 minus the ensemble mean to lie
    beyond 0.5 of the ensemble's latent between-graph SD;
  - the opposite direction is a separate family; together the two directions allow up to 10%
    combined error.
- **These are approximate reference-ensemble tests.** The rank p is exact only if N2 is
  exchangeable with the ensemble's graphs, which finite swap chains and greedy weight repair
  approximate but do not establish (§2).
- **Run rules:** a cumulative 24 GPU-hour cap; ensembles interleaved graph by graph; N2 and its
  variants measured last and exempt from the cap; the run refuses uncommitted code, and the
  report refuses a mixture of commits or inputs (§8).

## Caveats and corrections

- **D056, deviation:** the first run (commit `0ef9a3d`) stopped after 52 ensemble graphs on a
  faulty graph-hash check. The check was fixed, the 52 measurements were set aside
  (`runs/exp03/measures-aborted-0ef9a3d/`), and every graph was re-measured from zero, as §9
  requires. No N2 data existed at that point.
- **D058, results review:** Astra 6 and Fable 5.1 reproduced the verdicts; their corrections to
  the write-up are included. In particular:
  - why P4 passed at modest registered power is **not established** (the first write-up's
    explanation was wrong; the ensembles' P4 tails are left-skewed and compressed);
  - §7's "P4 is a bounded ratio" was wrong. The pre-registration is annotated, with its text
    kept; it affected only the discussion of the power table, not any rule;
  - N2-rev's P4 is a ratio of two numbers near 4 × 10⁻⁴ and supports no argument.
- **Timing of the pre-registration:** everything was fixed in the pre-registration before any N2
  measurement. That rests on local commit records and the run's provenance: the
  pre-registration was first pushed to GitHub on 2026-09-27, after the run (D062, D063).
- **Before the pre-registration:** the first pilot was discarded because of a seed bug that made
  graphs share random genomes (D053). Design v3's hop-distance rule for SH-route was never
  enforced by the build and was retired (D054).
- **D050, a correction that started here:** the turn read-out is dorsal minus ventral, so mirror
  symmetry forbids, rather than gives, a left-right comparison at this read-out. This reversed the
  rationale of D041 and 02's registered reading. SH-mirror has no predicted direction (D051).
- **`report.json` stores N2-rev's invalid P1 as `NaN`,** which strict JSON readers reject; the
  validity flags mark it (D058).
- **Replication:** because one graph decided the verdict, both reviewers recommended a separately
  pre-registered replication (D058), and the owner chose a full one (D059). That is
  [03r](../03r-replication/README.md). 03's first-run results were public on the `roadmap` branch
  from 2026-09-27 while 03r ran (D063).

## Files

| File | What it is |
|---|---|
| [`DESIGN.md`](DESIGN.md) | Design v3.1, with the changes from each review round |
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | The binding pre-registration (with the D058 annotation and the D056 deviation note) |
| [`RESULTS.md`](RESULTS.md) | Registered verdicts, registered secondary values, and the exploratory analysis, labelled |
| [`report.json`](report.json) | The registered report, from `scripts/exp03.py report`, with every per-graph value |
| [`supplement.json`](supplement.json) | Exploratory per-graph quantities (P4 numerator and denominator, forward-read-out ratio, common mode, gains, calibration validation) |
| [`supplement.py`](supplement.py) | Writes `supplement.json` from the local measurements (added after the run, D058) |
| [`ensembles.json`](ensembles.json) | Ensemble build and validation: seeds, plateau checks, per-graph structure |
| [`graphs_manifest.json`](graphs_manifest.json) | Raw SHA-256 of every ensemble graph file |
| [`pilot.json`](pilot.json) | The shuffle-only pilot (SH101-SH116): stimulus bank, margins, precision, timing |
| [`timing.json`](timing.json), [`timing.py`](timing.py) | Throughput benchmark on pilot shuffle SH101 (about 168 genome-world evaluations per second) |
| [`../../scripts/exp03.py`](../../scripts/exp03.py) | The runner: `build`, `pilot`, `variance`, `power`, `run`, `report` |
| [`../../wormwars/exp03/`](../../wormwars/exp03/) | `samplers.py` (the five ensembles), `measures.py`, `verdict.py`, `report.py` |
| `../../configs/mirror_pairs.yaml`, `../02-screening/remaps.json` | Registered inputs (hashes in the pre-registration, §3) |
| `../../tests/test_exp03_*.py` | Tests of the samplers, measures, verdict, report rules and runner |
| `runs/exp03/measures/` | One measurement file per graph. Local, git-ignored, about 640 MB |
| `runs/exp03/graphs/` | The ensemble graph files. Not committed, because they carry permuted anatomical weights |

## Reproduce it

**Setup:** follow [the main README](../../README.md#how-to-reproduce) (pinned environment,
`check_env.py`, `fetch_connectome.py`). The tested platform is one NVIDIA RTX 5080 with Python
3.13.

**What you can check without a GPU:** every verdict and table is computed from the committed
[`report.json`](report.json) and [`supplement.json`](supplement.json). The per-graph measurements
themselves (about 640 MB) are not committed, so `report` cannot be rerun from a fresh clone
without re-measuring.

**Re-running the experiment as registered** uses the binding commit. At `132acae`, `exp03.py` has
no `--instance` flag (added later, at `fc42434`, for 03r):

```
# 1. the graph files (not committed), from a current checkout: regenerated from the committed
#    record and checked byte for byte against graphs_manifest.json
python scripts/fetch_connectome.py
python scripts/exp03.py rebuild-graphs --into ../wormWars-03/runs/exp03/graphs

# 2. the run itself, at the binding commit
git worktree add ../wormWars-03 132acae
cd ../wormWars-03
python scripts/fetch_connectome.py
python scripts/exp03.py run --max-hours 24
python scripts/exp03.py report          # writes experiments/03-generation0/report.json
```

Then `python experiments/03-generation0/supplement.py` writes `supplement.json` from
`runs/exp03/measures/`. The script was added after the run (D058), so it is not in `132acae`; it
reads the measurements under the checkout it sits in, so place a current copy in the worktree.

- **The graph files.** They are not committed. `rebuild-graphs` (added after the run, D087)
  regenerates each from the kind, seed and passes recorded in the committed `ensembles.json`, and
  checks it against the committed manifest's raw hash. It never touches the record, unlike `build`.
  **Checked on 2026-09-28: all 640 rebuilt files matched the manifest byte for byte.** numpy writes a
  fixed timestamp into the `.npz`, so the bytes are reproducible in the pinned environment. The
  runner checks every file against the manifest again when it loads it.
- **Wall time:** 19.75 GPU-hours on one GPU; the pilot measured about 111 s per graph.
- **Compare against:** `report.json` (verdicts, ranks, per-graph values) and `supplement.json`.
- **Exactness:** see [`docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md). CUDA results are
  exact only on the same GPU, in the pinned environment, with the same batch composition (D082);
  03 evaluates each graph's genomes in one chunk. When 03r's code was added, a re-measured 03
  graph (SH-10000) matched its saved measurement bit for bit, and 03's report regenerated
  identically (03r pre-registration §1). The stages `pilot`, `variance` and `power` produced
  `pilot.json` and §7's tables; they are not needed to recompute the verdicts.

## Extend it

- **The mechanism follow-up** (roadmap Track B, [`ROADMAP.md`](../../ROADMAP.md#03-and-03r)):
  where the history effect lives (deletions), gap junctions or chemical synapses, inputs other
  than food, and what gives N2's random brains their stronger response. It needs its own
  pre-registration.
- **Wiring versus weights:** two of three weight permutations kept P4 high and one did not. These
  are single draws, and no causal feature is isolated (RESULTS, exploratory).
- **Readings the design cannot yet tell apart:** slow relaxation, hysteresis or multistability,
  nonlinear saturation, and a steady-state contrast measured after a finite 100-tick warm-up.
- **Reuse the controls:** the five validated ensembles are available to later experiments,
  including [03a](../03a-self-consistency/README.md).

## Record

- Pre-registration: [`PREREGISTRATION.md`](PREREGISTRATION.md); design: [`DESIGN.md`](DESIGN.md);
  results: [`RESULTS.md`](RESULTS.md).
- Replication: [`../03r-replication/`](../03r-replication/README.md).
- Decisions ([`DECISIONS.md`](../../DECISIONS.md)): D050-D053 (design and pilot), D054-D055
  (pre-registration review), D056 (deviation), D057 (results), D058 (results review), D059
  (replication chosen), D062-D063 (publication and timing), D085 (published on main).
- Reviews (`docs/reviews/`): `20260925-210723-03-design`, `20260925-212556-03-design-v2`,
  `20260925-222802-03-precision`, `20260925-232702-03-prereg`,
  `20260925-234635-03-prereg-recheck`, `20260926-220511-03-results`.
- Review trail: [`docs/REVIEW_TRAIL.md`](../../docs/REVIEW_TRAIL.md), episode 11.
