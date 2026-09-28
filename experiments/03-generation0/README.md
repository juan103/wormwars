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

## What the three signals measure, in plain words

All three are measured on **random, unevolved brains**: 2 048 random genomes per graph for the
probes, and 256 for the task scores. Nothing has been selected, so each signal describes what a
wiring does "out of the box", with random weights. Exact definitions:
[`PREREGISTRATION.md`](PREREGISTRATION.md) §4-§5.

### P4, history dependence: does the brain remember where the input came from?

The question: **once the input has become identical, does the brain's output still carry a trace
of the recent past?**

**The test.** It is a scripted stimulus played into each brain, not a game:

| | Ticks 1-100 | Ticks 101-110 |
|---|---|---|
| **Rising** | food held at ¼ of the final level | ramps up, reaching the final level on tick 110 |
| **Falling** | food held at 1.75 × the final level | ramps down, reaching the same final level on tick 110 |

On tick 110, the last step of the ramp, the input is exactly the same in both runs. Every other sense is held at the same
fixed value throughout. A memoryless brain would give the same turning output at that tick, so any
difference can only come from the past: the brain "remembers" whether food was recently low or
high.

**The number.** P4 = (the mean over genomes of |rising − falling| in the raw turn read-out on the
final tick) ÷ (the mean of |steady-state contrast|).
- **The numerator** is the leftover difference: the memory.
- **The denominator** is a yardstick: how differently the brain turns while it is actually held at
  the low level and at the high level. Dividing by it makes graphs comparable. Some wirings respond
  more strongly to food overall, and N2 does, so a raw difference would partly measure that.

**How to read the values:**
- **0** means no difference in this read-out, for these two histories, on that tick. It does not
  rule out history held elsewhere in the network, or shown by other histories.
- **N2's 0.931 (03; 0.924 in 03r)** means: averaged over genomes, the absolute difference in the
  final turn output is about 93% of the average absolute contrast after holding the two starting
  levels for 100 ticks. It is a ratio of averages. It does not say that each brain keeps 93% of
  its state, and the 100 ticks are not shown to reach equilibrium (Astra, Fable, D092).
- The ratio is not capped at 1 (D058).
- N2's high value is not a small denominator: its numerator and its denominator are both larger
  than any ensemble graph's (exploratory, §11).

**What was found:**
- **03:** N2 is above every graph in four of the five ensembles, and above all but one of 128 in
  the routing-matched one (SH-route).
- **03r:** with 768 fresh graphs and fresh random brains for N2 too, N2 is above every graph in four
  ensembles, all 256 routing-matched graphs included. It is above all but one of 128 in SH-class.
- So the real wiring's random brains hold on to recent food history more than wirings matched to
  it on the generic properties each ensemble keeps: degrees, and then food-to-motor routing,
  neuron classes, mirror symmetry, or two-way connections.

### P1, directional selectivity: does the brain turn toward the side with more food?

**The test.** Food is fed to the left and right sensors unequally: (b + d, b − d), then mirrored,
(b − d, b + d). The total is identical, and only the side differs. The brain runs 40 ticks from
rest. The signed turn toward the stronger side is compared with a yardstick: how much the turn
changes when both sides go from no food to the same food, (0, 0) to (b, b), the "common-mode"
response.

**The number.** The signed directional response is half the difference in turn between the two
mirrored conditions. P1 = that response, averaged over genomes and all 40 ticks, ÷ the mean
absolute common-mode turn, averaged the same way. A high P1 means the brain steers by the
left-right difference strongly, relative to how much it simply reacts to food being there.

**What was found:** *not distinctive* in either 03 or 03r. N2's random brains react to food much
more strongly overall, but their steering by side, relative to that, is not unusual.

### P3, food-information dependence: does using the real food signal help?

**The test.** Each random brain plays the single-nose foraging task (02's T1) twice on the same 16
worlds:
- with the real food signal;
- with the food signal replaced by each world's constant tick-0 average, so the brain feels food
  but cannot follow it.

**The number.** P3 = the mean score with the real signal minus the mean score with the constant
one. The score is the energy the swarm keeps, as a fraction of what it started with. Above 0 means
the food information helps even without evolution.

**What was found:**
- **03:** the registered criterion was not met, with little power.
- **03r:** the registered secondary label is *reversed*: N2's random brains scored slightly worse with the
  real signal than with the constant one. It is small and unpredicted. N2's measurement is much
  noisier than the ensembles', and an exploratory noise-aware check gives about p = 0.072 after
  correction. No claim is made about its cause ([03r's README](../03r-replication/README.md)).

### What none of this means (yet)

- **These are properties of wiring plus random weights, before any selection.** They are not
  behaviours the worm, or an evolved wey, is shown to use.
- **P1 and P4 are read from the raw turn output under scripted inputs,** not from movement in a
  world. Nothing shows the memory is useful.
- **What produces P4 is not known.** The readings 03 cannot yet tell apart ([`RESULTS.md`](RESULTS.md)):
  slow relaxation; hysteresis or multistability; nonlinear saturation; and a steady-state contrast
  measured after a finite 100-tick warm-up rather than at a verified equilibrium. Finding out is
  the next Track B experiment: delete neurons and connections, compare gap junctions with chemical
  synapses, and try inputs other than food ([`ROADMAP.md`](../../ROADMAP.md#03-and-03r)).
- **The null ensembles move weights as well as wiring,** so the result is not a pure wiring
  effect.
- **02b is related, but not the same measurement.** Selection made 02's champions' turning
  history-dependent ([02b](../02b-champion-analysis/README.md)). That does not show that N2's random
  brains start where selection took the champions: the aggregations and stimulus banks differ, and
  the unselected shuffles here already sit at 0.75-0.84 ([`RESULTS.md`](RESULTS.md), "Compared
  with 02b's evolved champions").

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
- **D050, a correction that started here:** the turn read-out is dorsal minus ventral, so a *fully*
  mirror-equivariant network (mirror-symmetric wiring and parameters) cannot make a left-right
  comparison at this read-out. Symmetric wiring alone does not forbid one, because each synapse's
  parameters are drawn independently, but it does not give the comparison for free either. This
  reversed the rationale of D041 and 02's registered reading. SH-mirror has no predicted direction
  (D050, D051; [02's Corrections entry](../02-screening/RESULTS.md)).
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

**What you can check without a GPU:** the committed [`report.json`](report.json) holds every
graph's signal values, so the rank counts and p-values can be recomputed from it, and
[`supplement.json`](supplement.json) holds the decomposition. The margin gate, the standard errors
and the effect intervals need the per-genome measurements (about 640 MB), which are not committed.
So `report` itself cannot be rerun from a fresh clone without re-measuring.

**Re-running the experiment as registered** uses the binding commit. At `132acae`, `exp03.py` has
no `--instance` flag (added later, at `fc42434`, for 03r):

```
# from a current checkout
python scripts/fetch_connectome.py
git worktree add ../wormWars-03 132acae
# the graph files (not committed): regenerated from the committed record, each checked byte for
# byte against graphs_manifest.json
python scripts/exp03.py rebuild-graphs --into ../wormWars-03/runs/exp03/graphs

# the run itself, at the binding commit
cd ../wormWars-03
python scripts/fetch_connectome.py
python scripts/exp03.py run --max-hours 24
python scripts/exp03.py report          # writes experiments/03-generation0/report.json
```

Then `python experiments/03-generation0/supplement.py` writes `supplement.json` from
`runs/exp03/measures/`. The script was added after the run (D058), so it is not in `132acae`; it
reads the measurements under the checkout it sits in, so copy the current version into the
worktree **after** `run`: before it, the untracked file would make `run` refuse the tree as dirty.

- **The graph files.** They are not committed. `rebuild-graphs` (added after the run, D087)
  regenerates each from the kind, seed and passes recorded in the committed `ensembles.json`, and
  checks it against the committed manifest's raw hash. It never touches the record, unlike `build`.
  **Checked on 2026-09-28: all 640 rebuilt files matched the manifest byte for byte.** numpy writes a
  fixed timestamp into the `.npz`, so the bytes are reproducible in the pinned environment. The
  runner checks every file against the manifest again when it loads it. The files carry permuted
  anatomical weights derived from the connectome, so do not commit or share them.
  - *Added 2026-09-28 (D106): "byte for byte" holds on Windows, where the files were written. The
    first CI run, on Linux, rebuilt two files whose bytes differed: numpy's zip headers record the
    writing operating system, and zlib builds can compress differently. `rebuild-graphs` now also
    checks each file's arrays against `graphs_content_manifest.json`, which must match on any
    system. `--windows-bytes` rewrites the one OS byte, so the raw hashes the runner checks at load
    time also match wherever zlib compressed identically; the command reports how many do.*
- **Wall time:** 19.75 GPU-hours on one GPU; the pilot measured about 111 s per graph.
- **Compare against:** `report.json` (verdicts, ranks, per-graph values) and `supplement.json`.
- **Exactness:** see [`docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md). On CUDA, exact
  reproduction is guaranteed only inside `replay_mode()`, on the same GPU, in the pinned
  environment, with the same batch composition (D082). Outside it, equality was observed in the
  tested configurations but is not guaranteed. 03 evaluates each graph's genomes in one chunk. When 03r's code was added, a re-measured 03
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
