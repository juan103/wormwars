# WormWars 03r: pre-registration of the full replication of experiment 03

**Status:** draft for review. It becomes binding at the commit the run's first measurement
follows. No brain on N2's wiring (N2, N2-rev or N2perm4-6) has been run for 03r.

## 0. Why this replication exists

Experiment 03 found N2 *distinctive relative to every ensemble* on one of three primary signals,
P4 (history dependence). The Holm-adjusted p was 0.0465 (`experiments/03-generation0/RESULTS.md`,
D057). The pass condition was discrete: at most one graph at or above N2 in every ensemble. It
was met with exactly one routing-matched graph above N2, and one more would have failed it.

Both reviewers recommended a separately pre-registered replication (D058):
- **Fable 5.1:** before any public claim.
- **Astra 6:** not required before publishing, but with independent genome draws for N2 as well
  as fresh graphs, and with either outcome reported.

The owner chose a full replication before publishing (D059). This file follows both reviewers'
specifications: all five ensembles, 256 routing-matched graphs, and independent genomes for
every graph, N2 included.

## 1. Disclosures

1. **Everything 03 measured is known,** including N2's values on every signal (N2's P4 is 0.931,
   SE 0.006) and every ensemble's distribution. This design, and in particular the choice of P4
   alone as the primary test (§6), was made after seeing them. That choice is justified in §6
   and §7, and 03's full rule is also applied and reported.
2. **Code changes since 03's binding commit (`132acae`)** only add a second instance to the same
   runner (`scripts/exp03.py --instance 03r`, commit `fc42434`):
   - the same measurement code, with different seeds, sizes and paths;
   - a P4-alone verdict function;
   - the variant list passed to the report.
   Instance 03 was checked to be unchanged. Its report regenerates identically, and a re-measured
   03 graph (SH-10000) matches its saved measurement bit for bit.
3. **Measured for 03r before this file:** only the ensembles' structure, from the build and its
   validation (`ensembles.json`, `graphs_manifest.json`). No brain has been run for 03r.
4. **Reviews:** this file goes to Astra 6 (maximum effort) and Fable 5.1 before any run. Their
   changes are listed in §12.

## 2. The question

**Primary:** with fresh graphs from all five null ensembles, and fresh random genomes for every
graph, including N2's, is N2 again *distinctive relative to every ensemble* on P4?

**Secondary:** do 03's verdicts on P1 and P3 (not distinctive) replicate?

**What a replication can and cannot address:**
- **It tests the sampling in 03:** which graphs were drawn, which random genomes, which worlds,
  and which calibration and validation draws.
- **It does not test the probe.** The code, the stimulus bank (03's pilot bank), the samplers
  and the measurement procedure are unchanged. A result that depends on the probe's design would
  replicate here and still be probe-specific.
- **The caveats of 03 §2 apply unchanged:**
  - The null moves weight placement as well as wiring.
  - The rank tests are approximate reference-ensemble tests, exact only under the assumption
    that N2 is exchangeable with the ensembles' graphs.
  - "Distinctive" means relative to these five nulls.

## 3. Graphs

- **N2:** as in 03.
- **Descriptive only**, reported with their values and ranks and no verdict:
  - **N2-rev:** as in 03;
  - **N2perm4-6:** N2's weights permuted over its own edges, with permutation seeds 4-6. These
    are fresh draws; 03 used 1-3.
- **Five ensembles,** built with 03's samplers and fresh seeds:

  | ensemble | graphs | seeds | 03's seeds |
  |---|---|---|---|
  | SH | 128 | 1 010 000 + i | 10 000 + i |
  | SH-route | **256** | 1 020 000 + i | 20 000 + i |
  | SH-class | 128 | 1 030 000 + i | 30 000 + i |
  | SH-mirror | 128 | 1 040 000 + i | 40 000 + i |
  | SH-recip | 128 | 1 050 000 + i | 50 000 + i |

  - A substitution after a sampler failure adds 100 000, as in 03. That stays clear of 03's seeds
    and names.
  - Plateau chains use seeds 1 090 000-1 090 003.
- **Validation,** the same rules as 03 (`ensembles.json`):
  - **The rules all passed.** Every ensemble's plateau at 20 and 40 passes agreed within 0.01.
    The lowest acceptance was 9% (SH-class), against a floor of 5%. No graph was over its
    Jaccard ceiling, and there were no substitutions.
  - **The structure matches 03's ensembles:**

    | ensemble | chemical Jaccard with N2, min / median / max | mirror share, chemical (median) | reciprocal pairs (median) |
    |---|---|---|---|
    | SH | 0.042 / 0.049 / 0.054 (03: 0.044 / 0.050 / 0.058) | 0.147 (03: 0.147) | 124.5 (03: 126) |
    | SH-route | 0.045 / 0.051 / 0.057 (03: 0.044 / 0.051 / 0.059) | 0.149 (03: 0.148) | 124.5 (03: 125.5) |
    | SH-class | 0.089 / 0.096 / 0.103 (03: 0.089 / 0.096 / 0.104) | 0.250 (03: 0.251) | 170 (03: 170) |
    | SH-mirror | 0.054 / 0.062 / 0.069 (03: 0.055 / 0.063 / 0.073) | 0.639 exactly | 150 (03: 150) |
    | SH-recip | 0.045 / 0.050 / 0.058 (03: 0.043 / 0.050 / 0.058) | 0.150 (03: 0.150) | 669 exactly |

  - **Build time:** 0.36 hours on the CPU.
- **Manifest:** every graph file is pinned by its raw SHA-256 in `graphs_manifest.json` and
  checked when loaded.

## 4. Procedure for every graph

Identical to 03 §4, with every random draw fresh:

| | 03 | 03r |
|---|---|---|
| genome seeds | SHA-256 of the graph's name | SHA-256 of "03r:" + the graph's name, so N2's genomes are new too |
| worlds | 993 000 000-015 | 994 000 000-015 |
| run seed | 3 | 5 |
| calibration seed (1 024 genomes) | 0 | 1003 |
| validation seed (2 048 genomes; N2 and the first 8 graphs of every ensemble) | 1 | 1004 |
| stimulus bank for the history test | 03's pilot bank | **the same**: the same probe |

Sample sizes are unchanged:
- 256 genomes × 16 worlds for P3's two cells;
- 64 × 16 for the secondary cells and coverage;
- 2 048 probe genomes for P1 and P4;
- 256 for the secondary response conditions.

The calibration-failure rule is unchanged: such a graph is excluded and counted, and every
verdict is withheld if N2's calibration fails.

## 5. Signals

P1, P3 and P4 are defined exactly as in 03 §5, with the same exclusion rule (a denominator mean
below 10⁻⁴, or a non-finite value).

- **Primary:** P4.
- **Secondary, with verdicts under 03's full rule (§6):** P1 and P3.
- **Secondary, descriptive:** 03's secondary values (03 §5).
- **Secondary, descriptive, newly registered:** the quantities 03 reported as exploratory,
  computed by `experiments/03-generation0/supplement.py --instance 03r` into
  `experiments/03r-replication/supplement.json`:
  - P4's numerator (mean |rising − falling|) and denominator (mean |steady contrast|);
  - the same ratio on the raw forward read-out;
  - the mean common-mode turn response;
  - the gains and the calibration validation.
  For each, the report gives N2's value, each ensemble's 5th, 50th and 95th percentiles and
  maximum, and, for the forward-read-out ratio, the number of each ensemble's graphs at or above
  N2. There are no verdicts on these.

## 6. Verdicts

The per-ensemble quantities are computed exactly as in 03 §6:
- the SEs;
- τ_E and the margin 0.5 τ_E;
- the rank p = (r + 1)/(n + 1), with n = 256 for SH-route;
- the effect interval;
- N2's 90% interval.

**Primary test: P4 alone** (`report.single_signal`):
- p = the maximum over the five ensembles of the rank p (intersection-union), at α = 0.05, with
  no correction across signals, since P4 is the only primary hypothesis.
- The per-ensemble verdict rules are 03's (distinctive, reversed, consistent, inconclusive), with
  the same effect-margin gate.
- **Replicated:** *distinctive relative to every ensemble*. That means at most 5 of 128 graphs at
  or above N2 in each 128-graph ensemble, and at most 11 of 256 in SH-route, with every effect
  interval beyond its margin.
- **Not replicated:** anything else. The per-ensemble verdicts say whether N2 is consistent with
  some ensemble, or inconclusive.

**Why P4 alone and not 03's three-signal Holm rule.**
- 03 had three primary hypotheses; this replication has one, stated in advance: P4.
- Under 03's rule, a replication of an effect exactly as large as 03's would pass only about 41%
  of the time (§7). The outcome would again turn on whether one or two graphs land above N2.
- 03's rule is also applied, unchanged, and reported alongside as a secondary result (below).

**Secondary: 03's full rule, applied unchanged** (Holm across P1, P3 and P4 of the maximum p over
ensembles, as in 03 §6), with every per-ensemble verdict. It is reported whatever the primary
result.

**Completeness:** as in 03. A valid N2, and at least 120 valid graphs in every ensemble.
Otherwise the verdict is withheld.

## 7. Power

**Method:**
- For each ensemble, the probability that one fresh graph is at or above N2 is given a Jeffreys
  posterior from 03's count, Beta(r + ½, n − r + ½).
- Fresh ensembles of 03r's sizes are drawn from it, 200 000 times (seed 0,
  `experiments/03r-replication/power.py`).
- **Limits:** this assumes the ensembles' tails are as 03 sampled them, and it ignores N2's own
  measurement noise (SE 0.006, small against the ensembles' spreads).

| if N2's true P4 is | P4 alone, α 0.05 (primary) | 03's full rule |
|---|---|---|
| 0.931 (03's estimate) | **0.97** | 0.41 |
| 0.925 (one SE lower) | 0.97 | 0.41 |
| 0.915 | 0.89 | 0.18 |
| 0.905 | 0.35 | 0.00 |

A Gaussian model at 03's observed z values gives 0.98 for the primary test and 0.18 for 03's rule.
03's own ensembles have compressed upper tails, so the Gaussian figure for 03's rule is
pessimistic.

**Reading the power:**
- If 03's effect is real and about as large as measured, the primary test should pass.
- If N2's true P4 is nearer the top of the routing-matched and mirror ensembles (about 0.905),
  it will usually fail.
- A failure is not proof that there is no difference. The report gives every rank count and
  effect interval.

## 8. Budget and run

- **Cost:** 768 ensemble graphs plus 5 N2 graphs, at about 111 s each (03's rate): about 24
  GPU-hours.
- **Cap:** 28 GPU-hours for the ensemble graphs, cumulative across restarts
  (`scripts/exp03.py run --instance 03r --max-hours 28`).
- **Order:** the ensembles are interleaved in proportion to their sizes, so a stop removes graphs
  evenly. N2, N2-rev and N2perm4-6 come **last** and are exempt from the cap.
- **The same rules as 03 §8:** stopping and resuming never depend on a measured value; the run
  refuses uncommitted code; measurements record their commit, input hashes, device and instance;
  the report refuses a mixture; graph files are checked against the manifest; measurements go to
  `runs/exp03r/measures/`.

## 9. Deviations

As in 03 §9. Any deviation is recorded in DECISIONS.md and in the results, and any mid-run code
change means re-measuring every graph.

## 10. What the results decide, and what will be published

- **Replicated:** 03's P4 finding is reported as replicated, with both runs' effect sizes and
  rank counts. The mechanism is the next step (03 §10).
- **Not replicated:** 03's P4 finding is reported as a borderline result that did not replicate.
  There will be no further attempt designed to make it pass. A later experiment on the mechanism
  would need its own case and its own pre-registration.
- **Either way:**
  - 03 and 03r are published together;
  - the README says that a full replication was run before publishing, why (one graph decided
    03's verdict, D058), and who contributed what to that decision (D059): Fable asked for
    replication before any public claim, Astra specified independent genomes and did not require
    it, Claude leaned toward replicating, and the owner decided;
  - P1's and P3's replication results are reported whatever they are.

## 11. Not registered

These are exploratory:
- pooled analyses that combine 03's and 03r's ensembles;
- any analysis of N2-rev or N2perm4-6 beyond their values and ranks;
- any mechanism analysis.

## 12. Changes from the team's review of this file

(To be filled after Astra's and Fable's review.)
