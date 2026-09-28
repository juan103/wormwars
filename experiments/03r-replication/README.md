# 03r: Full replication of experiment 03

**Status:** published on main together with 03 (`e856b7d`, D085) · **Run:** started 2026-09-26
23:45 +02:00 (first saved measurement), finished 2026-09-28 · **Commit:** `7c146fc` (every
measurement records it, with `code_dirty: false`) · **Compute:** 23.95 GPU-hours, one GPU, one
uninterrupted invocation, 773 graphs

Experiment 03 found N2 *distinctive relative to every ensemble* on one of three primary signals,
P4 (history dependence), with a Holm-adjusted p of 0.0465. The pass condition was discrete, and it
was met with exactly one routing-matched graph above N2: one more would have failed it. So both
reviewers recommended a separately pre-registered replication (D058), and the owner chose a full
one (D059). 03r asks: with fresh graphs from all five null ensembles, and fresh random genomes for
every graph, N2's included, is N2 again distinctive relative to every ensemble on P4?
([`PREREGISTRATION.md`](PREREGISTRATION.md) §0, §2.)

## The answer, in brief

- **The registered outcome, in the wording fixed in advance (§10):** *"Replicated under the
  registered single-signal test and under 03's original three-signal rule."*
- **Primary test, P4 alone:** maximum rank p **0.0155**, *distinctive relative to every
  ensemble*. N2 = 0.924 (03: 0.931). Graphs at or above N2: 0 in SH, 0 of 256 in SH-route, 1 in
  SH-class, 0 in SH-mirror and 0 in SH-recip.
- **03's three-signal rule:** Holm-adjusted p **0.0465**, also distinctive. The margin under that
  rule is still one graph: one additional SH-class graph at or above N2 would give 0.070. The
  single-signal primary would still pass (p = 3/129 = 0.023).
- **Secondary, P1:** *not distinctive*, recurring (Holm-adjusted p 1.0). A recurring label is not
  evidence that N2 has no directional selectivity.
- **Secondary, P3:** *reversed against every ensemble*, a **new, unpredicted** label
  (opposite-direction Holm-adjusted p 0.0465; N2 = −0.024, SE 0.012; 0, 0 of 256, 0, 0 and 1
  graphs at or below N2). N2's random brains score slightly worse with the real food signal than
  with a constant one.
  - **The caveat:** N2's P3 measurement is much noisier than the ensemble graphs' (SE 0.012,
    against an ensemble median of 0.0065; only 3 of 768 graphs have an SE as large). Unequal
    measurement noise undermines the exchangeability the rank test assumes, and can make it
    anti-conservative. An **exploratory** noise-aware check gives a one-sided p of about 0.024, or
    about **0.072 after Holm** across three signals.
  - It is also fragile: one additional SH-recip graph at or below N2 would give 0.070. It is
    controlled only within 03's opposite-direction family, and both directions together allow up
    to 10% error (§6). It is reported as found, with no claim about its cause; a claim would need
    its own pre-registered test.
- **What it does not show:**
  - it tests the sampling in 03 (graphs, genomes, worlds, seeds), **not the probe or the code**:
    the replication used the same probe, stimulus bank and code, so a probe-specific effect, or a
    systematic implementation error, would replicate too (pre-registration §2);
  - the two runs are **not independent evidence**: both compare the same N2 connectome with graphs
    from the same generating procedure, and their p-values are never combined;
  - it establishes neither a mechanism nor any advantage for the worm.

Numbers and tables: [`RESULTS.md`](RESULTS.md).

**What the signals measure, in plain words** (the history test's two food histories, what the
ratio means, and what it does not show): [03's README](../03-generation0/README.md#what-the-three-signals-measure-in-plain-words).

## Design

The design is the pre-registration itself: [`PREREGISTRATION.md`](PREREGISTRATION.md) (v3, bound
at `7c146fc`). The procedure for every graph is identical to 03's (03 pre-registration §4).

- **Graphs:** N2; five ensembles built with 03's samplers and fresh seeds: SH, SH-class, SH-mirror
  and SH-recip with 128 graphs each, and **SH-route with 256** (Fable's request, because one
  SH-route graph decided 03; not a power decision). All 1 408 ensemble graph arrays of 03 and 03r
  are distinct. Descriptive only: N2-rev and fresh weight permutations N2perm4-6.
- **What is redrawn:**

  | | 03 | 03r |
  |---|---|---|
  | genome seeds | SHA-256 of the graph's name | SHA-256 of "03r:" + the graph's name, so N2's genomes are new too |
  | worlds | 993 000 000-015 | 994 000 000-015 |
  | run seed | 3 | 5 |
  | calibration seed | 0 | 1003 |
  | validation seed | 1 | 1004 |
  | ensemble seeds | 10 000 + i, … 50 000 + i | 1 010 000 + i, … 1 050 000 + i |

- **What is kept:** the stimulus bank for the history test (03's pilot bank, so the same probe),
  the remapping sets R1, R2 and MS, the analysis seeds, all configs, and the sample sizes.
- **Primary test: P4 alone.** The maximum rank p over the five ensembles, at α = 0.05, with the
  effect-margin gate of 03. It passes as *distinctive relative to every ensemble*. The report also
  records each ensemble's own gates (valid n, count at or above N2, raw rank p, rank gate, margin
  gate).
  - **This choice was made after seeing 03's data** and is disclosed as such. It followed Fable's
    argument that 03's three-signal threshold (α/3) sits close to the routing ensemble's own
    estimated tail rate (D060, §6).
- **Secondary:** 03's full rule (Holm across P1, P3 and P4 of the maximum p over ensembles),
  reported whatever the primary result. Newly registered descriptive secondaries: the P4
  decomposition (via `supplement.py --instance 03r`) and 03's and 03r's P4 effect intervals side
  by side.
- **Completeness:** a valid N2, at least 120 valid graphs in each 128-graph ensemble and 240 in
  SH-route; otherwise the verdict is withheld.
- **Fixed wording for every outcome** (§10), including a split between the two rules and a
  withheld result. Before the run, the posterior-predictive probability of passing the rank gates
  was about 0.97 for the primary test and 0.41 for 03's rule, at 03's N2 value (§7, Jeffreys
  prior, [`power.py`](power.py)).
- **Run rules:** a 32 GPU-hour cap for the ensemble graphs, registered in code and never extended;
  ensembles interleaved in proportion to their sizes; N2, N2-rev and N2perm4-6 last, exempt from
  the cap (§8).

**Why a replication, and who contributed what** (D059):
- **Fable 5.1** asked for replication before any public claim, and argued for testing P4 alone.
- **Astra 6** specified independent genomes for N2 as well as fresh graphs, and did not require
  replication first.
- **Claude Opus 5.5**, the experimenter, leaned toward replicating first.
- **The owner decided** on the full replication.

## Caveats and corrections

- **Public disclosure came after measurement began** ([`DISCLOSURE.md`](DISCLOSURE.md)):
  - the run started from `7c146fc`, committed 2026-09-26 23:43 +02:00; its first measurement was
    saved at 23:45;
  - the branch with the pre-registration was first pushed to GitHub on 2026-09-27 (`ff17f00`,
    17:28 +02:00), while the run was in progress. GitHub's receipt time shows only when the text
    became public. It is not proof of registration before the run;
  - shortly before disclosure (checked 16:16 +02:00), 528 of 773 graphs were measured, and N2 and
    its variants were not (D063 gives 565 of 773 at the moment of the push);
  - what had been inspected was operational information only. The one 03r signal value seen is the
    preflight's P4 (0.756) for SH-1010000, before binding, disclosed in §1;
  - the dated addendum (2026-09-28) lists the checks after the run, and says they support, but
    cannot on their own prove, that nothing was inspected in between.
- **The README sentence bound in §10 was amended** (D063): it said "a full replication was run
  before publishing", but 03's first-run results were public on the `roadmap` branch from
  2026-09-27 17:28 +02:00 while 03r ran. The owner chose this knowingly, to get a public timestamp
  for 03r's pre-registration. The amended wording: the replication was run before 03 was merged
  into main and presented as a result.
- **§9 and code committed during the run:** T0 work (D064-D076, including `scripts/exp03.py`,
  D069) was committed in the working directory while 03r ran, but the running process never
  reloaded (one invocation, no resume). N2 and the last ensemble graph measured
  (SH-route-1020255) were re-measured with the binding commit's code and are **bit-for-bit
  identical** to their saved measurements ([`remeasure.json`](remeasure.json); D082, D083). Two
  graphs are evidence, not proof, for all 773.
- **The report** was produced by the binding commit's code and again by the current code, and the
  two are identical (D080).
- **Results review** (D081-D083): both reviewers first answered "not yet", on presentation; the
  verdicts were confirmed. The P3 noise caveat, the both-rules table, the fragility statements and
  the scoped provenance claim came from that review. Both then answered "ready to publish" (D083).
- **The caveats of 03 apply unchanged:** approximate reference-ensemble tests, exact only if N2 is
  exchangeable with the ensembles' graphs; the nulls move weights as well as wiring; "distinctive"
  means relative to these five nulls.
- **03r's motor gains are not comparable with 03's:** the calibration seed also sets the
  calibration world's map.
- **N2-rev:** its descriptive P1 is invalid (common-mode denominator about 9 × 10⁻⁵, below the
  10⁻⁴ floor) and stored as `NaN` in `report.json`; its P4 is a ratio of numbers near 4 × 10⁻⁴ and
  is not interpreted.

## Files

| File | What it is |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | The binding pre-registration (v3), with the review changes in §12 |
| [`DISCLOSURE.md`](DISCLOSURE.md) | The public disclosure notice (2026-09-27) and its dated addendum (2026-09-28) |
| [`RESULTS.md`](RESULTS.md) | Primary and secondary results, descriptive secondaries, deviations and disclosures |
| [`report.json`](report.json) | The registered report, from `scripts/exp03.py report --instance 03r`: verdicts, per-ensemble gates (`replication_primary`), accounting, `P4_beside_03`, per-graph values |
| [`supplement.json`](supplement.json) | Registered descriptive secondaries (P4 decomposition, forward-read-out ratio, gains, calibration validation), produced by `experiments/03-generation0/supplement.py --instance 03r` at `eca542d` |
| [`ensembles.json`](ensembles.json) | Ensemble build and validation (768 graphs; 0.36 hours on the CPU) |
| [`graphs_manifest.json`](graphs_manifest.json) | Raw SHA-256 of every ensemble graph file |
| [`power.py`](power.py) | §7's posterior-predictive probabilities of passing the rank gates (seed 0, 200 000 draws) |
| [`remeasure.py`](remeasure.py), [`remeasure.json`](remeasure.json) | The bit-for-bit re-measurement of N2 and SH-route-1020255 with the binding code, and its record |
| [`../../scripts/exp03.py`](../../scripts/exp03.py) | The runner, shared with 03; `--instance 03r` selects this experiment's seeds, sizes, paths and cap |
| [`../../wormwars/exp03/`](../../wormwars/exp03/) | Samplers, measures, verdict and report (including `single_signal` and `replication_primary`) |
| `../03-generation0/pilot.json` | 03's pilot, whose stimulus bank 03r reuses |
| `../../tests/test_exp03r_replication.py` | Tests of the replication instance |
| `runs/exp03r/measures/` | One measurement file per graph (773). Local, git-ignored |
| `runs/exp03r/graphs/` | The ensemble graph files. Not committed, because they carry permuted anatomical weights |

## Reproduce it

**Setup:** follow [the main README](../../README.md#how-to-reproduce). The tested platform is one
NVIDIA RTX 5080 with Python 3.13; `remeasure.json` records that device.

**What you can check without a GPU:** the committed [`report.json`](report.json) holds every
graph's signal values, so the rank counts and p-values can be recomputed from it, and
[`supplement.json`](supplement.json) holds the decomposition. The margin gate, the standard errors
and the effect intervals need the per-genome measurements, which are not committed. `python experiments/03r-replication/power.py` reprints §7's table from 03's
committed `report.json` (CPU only).

**Re-running the experiment as registered** uses the binding commit:

```
# from a current checkout
python scripts/fetch_connectome.py
git worktree add ../wormWars-03r 7c146fc
# the graph files (not committed): regenerated from the committed record, each checked byte for
# byte against graphs_manifest.json
python scripts/exp03.py rebuild-graphs --instance 03r --into ../wormWars-03r/runs/exp03r/graphs

# the run itself, at the binding commit
cd ../wormWars-03r
python scripts/fetch_connectome.py
python scripts/exp03.py run --instance 03r        # the 32 GPU-hour cap is registered in code
python scripts/exp03.py report --instance 03r     # writes experiments/03r-replication/report.json
python experiments/03-generation0/supplement.py --instance 03r
```

- **The graph files.** They are not committed. `rebuild-graphs` (added after the run,
  D087) regenerates each from the kind, seed and passes recorded in the committed `ensembles.json`,
  and checks it against the committed manifest's raw hash, without touching the record.
  **Checked on 2026-09-28: all 768 rebuilt files matched the manifest byte for byte.** The runner
  checks every file against the manifest again when it loads it. The files carry permuted
  anatomical weights derived from the connectome, so do not commit or share them.
- **`--max-hours`:** any value other than the registered 32 is refused. The `pilot`, `variance`
  and `power` subcommands belong to 03 only; 03r reuses 03's pilot.
- **From the current checkout,** a resumed 03r run would be refused, because HEAD is past
  `7c146fc` and a resume refuses measurements from other code (D063).
- **`remeasure.py`** hard-codes two local Windows paths (the main checkout and a binding worktree
  at `7c146fc`); edit them before running it. It needs the saved measurements.
- **Wall time:** about 24 GPU-hours on one GPU (23.95 in the run; 03 averaged about 110 s per
  graph).
- **Compare against:** `report.json` (`replication_primary`, `signals`, `accounting`,
  `P4_beside_03`) and `supplement.json`.
- **Exactness:** see [`docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md). On CUDA, exact
  reproduction is guaranteed only inside `replay_mode()`, on the same GPU, in the pinned
  environment, with the same batch composition (D082). Outside it, equality was observed in the
  tested configurations but is not guaranteed. 03 and 03r evaluate each graph's genomes in one
  chunk. The re-measurement of two graphs with the
  binding code was bit-for-bit identical (`remeasure.json`).

## Extend it

- **The mechanism follow-up** is next in Track B ([`ROADMAP.md`](../../ROADMAP.md#03-and-03r)):
  where the history effect lives (deletions), gap junctions or chemical synapses, inputs other than
  food, and what gives N2's random brains their stronger response. It needs its own
  pre-registration.
- **Bridge 2** (the A/B shuttle on N2 and matched nulls) gains priority, per the roadmap: it tests
  whether N2's memory head start matters for behaviour.
- **P3's reversal** is an unpredicted secondary. Any claim about its cause needs its own
  pre-registered test.
- **Not an option:** §10 rules out any further attempt designed to make P4 pass, and pooled
  analyses of 03 and 03r are exploratory only (§11).

## Record

- Pre-registration: [`PREREGISTRATION.md`](PREREGISTRATION.md); disclosure:
  [`DISCLOSURE.md`](DISCLOSURE.md); results: [`RESULTS.md`](RESULTS.md).
- The experiment it replicates: [`../03-generation0/`](../03-generation0/README.md).
- Decisions ([`DECISIONS.md`](../../DECISIONS.md)): D058-D059 (why, and who decided), D060-D061
  (pre-registration reviews), D062-D063 (publication plan and timing), D080 (results), D081-D083
  (results review, re-measurement, ready to publish), D085 (published on main).
- Reviews (`docs/reviews/`): `20260926-225906-03r-prereg`, `20260926-225909-03r-prereg`,
  `20260926-232016-03r-prereg-recheck`, `20260926-232018-03r-prereg-recheck`,
  `20260926-233226-03r-prereg-final`, `20260926-234038-03r-prereg-final2`,
  `20260927-160621-pushes`, `20260927-160623-pushes`, `20260928-002527-03r-results`,
  `20260928-002529-03r-results`, `20260928-005135-03r-T0-combo`, `20260928-005137-03r-T0-combo`,
  `20260928-014201-03r-T0-re`, `20260928-014203-03r-T0-re`.
- Review trail: [`docs/REVIEW_TRAIL.md`](../../docs/REVIEW_TRAIL.md).
