# WormWars 03r: pre-registration of the full replication of experiment 03

**Status:** v3, after Astra's and Fable's review (D060) and their confirmation pass (D061). It
becomes binding at the commit recorded in the provenance of the formal run's first saved
measurement. No brain on N2's wiring (N2, N2-rev or N2perm4-6) has been run for 03r.

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
specifications: all five ensembles, 256 routing-matched graphs (Fable's request), and independent
genomes for every graph, N2 included (Astra's).

## 1. Disclosures

1. **Everything 03 measured is known,** including N2's values on every signal (N2's P4 is 0.931,
   SE 0.006) and every ensemble's distribution. This design was made after seeing them, in
   particular the choice of P4 alone as the primary test (§6). The choice is argued in §6, and
   03's full rule is also applied and reported.
2. **Code changes since 03's binding commit (`132acae`)** add a second instance to the same runner
   (`scripts/exp03.py --instance 03r`, commit `fc42434`), plus the review's changes (D060):
   - the same measurement code, with different seeds, sizes and paths;
   - a P4-alone verdict function with per-ensemble gates, written even when withheld;
   - a per-ensemble completeness floor;
   - the registered cap in code;
   - a fresh permutation for one secondary condition (§4);
   - the N2 cache hashed with the inputs;
   - a supplement that counts missing and failed graphs.
   Instance 03 was checked to be unchanged. Its report regenerates identically, a re-measured 03
   graph (SH-10000) matches its saved measurement bit for bit, and its supplement regenerates
   with every value unchanged.
3. **Measured for 03r before this file:**
   - **The ensembles' structure,** from the build and its validation (`ensembles.json`,
     `graphs_manifest.json`).
   - **One preflight measurement of one ensemble graph,** SH-1010000, with the 03r code, to check
     the new code path end to end (D060).
     - It was not saved, and it is excluded from the formal run, which measures that graph again
       from scratch with the same seeds.
     - **What was inspected:** the run time (126 s, including first-use warm-up), the keys of the
       record, its gains (4.12 and 2.95), that its calibration validation ran, and its P4 value
       (0.756).
     - No other value was looked at, and no N2-wiring brain was run.
4. **Reviews:** Astra 6 (maximum effort) and Fable 5.1 reviewed v1 of this file
   (`docs/reviews/*-03r-prereg/`). The changes are listed in §12.

## 2. The question

**Primary:** with fresh graphs from all five null ensembles, and fresh random genomes for every
graph, including N2's, is N2 again *distinctive relative to every ensemble* on P4?

**Secondary:** do 03's verdicts on P1 and P3 (not distinctive) recur? Repeating a "not
distinctive" label reproduces a decision. It is not evidence that the property is absent, least
of all for the low-power P3 (Astra, D060).

**What a replication can and cannot address:**
- **It tests the sampling in 03:** which graphs were drawn, which random genomes, which worlds,
  and which calibration and validation draws.
- **It does not test the probe or the code.** The code, the stimulus bank (03's pilot bank), the
  samplers and the measurement procedure are unchanged. A probe-specific effect, or a systematic
  implementation error, would replicate here. Passing does not validate the probe or identify a
  memory mechanism.
- **The two runs are not independent evidence.** Both compare the same N2 connectome with graphs
  from the same generating procedure. Under an exchangeability model, an unusually high latent
  value for N2 stays high across reruns. Fresh seeds also do not undo 03's selection of P4 from
  three signals.
  - For that reason 03's and 03r's p-values are never multiplied or combined as if they were
    independent tests (Astra).
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
- **Five ensembles,** built with 03's samplers and fresh seeds. All 1 408 ensemble graph arrays
  of 03 and 03r are distinct (checked by Astra).

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
- **Why 256 SH-route graphs:** Fable asked for them, because one SH-route graph decided 03. It is
  not a power decision. Under §7's model it moves the primary pass probability only from about
  0.95 to 0.97; its benefit is precision on the tail that decided 03.
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
- **Manifest:** every graph file is pinned by its raw SHA-256 in `graphs_manifest.json` (Astra
  re-verified all 768) and checked when loaded. N2's connectome cache
  (`data/cache/cook2019_herm.npz`) is hashed raw into every measurement's provenance (Astra,
  D060; the raw hash is Fable's correction, D061).

## 4. Procedure for every graph

Identical to 03 §4. What is redrawn, and what is deliberately kept:

| | 03 | 03r |
|---|---|---|
| genome seeds | SHA-256 of the graph's name | SHA-256 of "03r:" + the graph's name, so N2's genomes are new too |
| worlds | 993 000 000-015 | 994 000 000-015 |
| run seed | 3 | 5 |
| calibration seed (1 024 genomes; it also sets the calibration world's map, so 03r's gains are not comparable with 03's) | 0 | 1003 |
| validation seed (2 048 genomes; N2 and the first 8 graphs of every ensemble) | 1 | 1004 |
| weight permutation of the permuted-magnitude secondary condition | the graph's configured seed (0 except for N2perm, where it reused the graph's own permutation) | fresh per graph, from its salted genome seed (so for N2perm4-6 it is a second, different permutation: descriptive only) |
| **kept:** the stimulus bank for the history test | 03's pilot bank | **the same**: the same probe |
| **kept:** the remapping sets R1, R2 and MS (`02-screening/remaps.json`) | | the same |
| **kept:** the analysis seeds (SE bootstrap 0, effect bootstrap 1) and all configs | | the same |

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
- **Secondary, descriptive, newly registered:**
  - **What:** the quantities 03 reported as exploratory, computed by
    `experiments/03-generation0/supplement.py --instance 03r` into
    `experiments/03r-replication/supplement.json`:
    - P4's numerator and denominator on the raw turn read-out;
    - the same ratio on the raw forward read-out;
    - the mean common-mode turn response;
    - both gains;
    - each validated graph's largest relative deviation from the target drive.
  - **Summaries:** N2's value and each ensemble's 5th, 50th and 95th percentiles, maximum and
    valid n. For the forward-read-out ratio, also the number of each ensemble's graphs at or above
    N2 and each variant.
  - **Masks:** a ratio whose denominator mean is below 10⁻⁴, or not finite, is masked. Missing
    measurements and calibration failures are listed and counted. Every measurement must share
    one provenance.
  - There are no verdicts on these.
- **Secondary, descriptive, newly registered:** 03's and 03r's P4 effect intervals and rank
  counts, side by side for each ensemble, so that "replicated" is not read as "the same
  magnitude" (Fable).

## 6. Verdicts

The per-ensemble quantities are computed exactly as in 03 §6:
- the SEs;
- τ_E and the margin 0.5 τ_E;
- the rank p = (r + 1)/(n + 1), where n is the ensemble's number of **valid** graphs;
- the effect interval;
- N2's 90% interval.

**Primary test: P4 alone** (`report.single_signal`, via `report.replication_primary`):
- p = the maximum over the five ensembles of the rank p (intersection-union), at α = 0.05, with
  no correction across signals, since P4 is the only primary hypothesis.
- The per-ensemble verdict rules are 03's (distinctive, reversed, consistent, inconclusive),
  with the same effect-margin gate.
- **Passes:** *distinctive relative to every ensemble*. With the full planned samples, that means
  at most 5 of 128 graphs at or above N2 in each 128-graph ensemble, and at most 11 of 256 in
  SH-route, with every effect interval beyond its margin.
- **The maximum-p rule gives every ensemble the same p.** So one ensemble's rank failure changes
  every ensemble's label: the labels read "inconclusive" or "consistent", and a margin failure can
  sit beside "distinctive" labels. The labels alone therefore hide which ensemble failed. The
  report also records each ensemble's own gates (Astra):
  - valid n;
  - the count at or above N2;
  - the raw rank p;
  - the rank gate (raw p ≤ 0.05);
  - the margin gate.
  Four passing ensembles cannot rescue the conjunction. The per-ensemble statistics and gates
  are computed whenever N2 is valid on P4, including when the verdict is withheld for
  completeness (Astra, D061).
- **Error rates:**
  - one-sided 5%, under the null that N2 is exchangeable with at least one ensemble;
  - the opposite direction is a separate family, as in 03, so up to 10% across both directions.

**Why P4 alone, and not 03's three-signal Holm rule** (Fable's argument, D060):
- At α/3, the rule's per-ensemble threshold is (r + 1)/(n + 1) ≤ 1.67%. That is close to 03's
  own estimate of SH-route's exceedance rate (1 of 128; posterior mean about 1.2%).
  - Under §7's model, SH-route alone then passes 03's rule with probability about 0.67 at 256
    graphs, rising towards about 0.77 with more (Astra, D061). Its cutoff is 3 versus 4 of 256,
    and 1 versus 2 of 128 in the other ensembles.
  - With all five ensembles, the pass probability is about 0.41.
- At α = 0.05 the threshold is about 4.7%, four times that estimate, and the pass probability is
  about 0.97.
- The single-signal test is also the standard analysis for a single hypothesis stated in
  advance.
- It was chosen after 03 and is disclosed as such.
- 03's rule is also applied, unchanged, and reported alongside.

**Secondary: 03's full rule, applied unchanged** (Holm across P1, P3 and P4 of the maximum p over
ensembles, as in 03 §6), with every per-ensemble verdict. It is reported whatever the primary
result.

**Completeness:** a valid N2, and at least **120** valid graphs in each 128-graph ensemble and
**240** in SH-route. That keeps 03's retained fraction (Astra). Otherwise the verdict is
**withheld**, and the report says so explicitly, with the per-ensemble statistics and gates if
N2 is valid. The report gives, separately:
- planned counts;
- measured counts;
- calibration failures;
- signal-invalid counts;
- valid counts.

## 7. Probability of passing the rank gates (posterior predictive)

**What this is.** Not the power of the whole registered procedure. It is the probability, under
a model built from 03's counts, that the rank gates pass.
- **Not simulated:** the margin gate (never binding in 03), exclusions and completeness.
- **03's-rule column:** it uses α/3, which is P4's Holm threshold only when P4 has the smallest p
  of the three signals, as it did in 03.

**Method** (`experiments/03r-replication/power.py`, seed 0, 200 000 draws):
- For each ensemble, the probability that one fresh graph is at or above N2's value gets a
  posterior from 03's count, Beta(r + a, n − r + a).
- Fresh ensembles of 03r's sizes are drawn from it.
- The table's rows fix N2's measured value. The noise column instead draws N2's fresh measurement
  around the row's value with 03's SE (0.006).
- The five tail rates are treated as independent given their posteriors.

| N2's P4 | primary, Jeffreys (a = ½) | 03's rule, Jeffreys | primary, uniform prior (a = 1) | 03's rule, uniform | primary with N2 noise | 03's rule with N2 noise |
|---|---|---|---|---|---|---|
| 0.931 (03's estimate) | **0.97** | 0.41 | 0.91 | 0.17 | 0.97 | 0.46 |
| 0.925 | 0.97 | 0.41 | 0.91 | 0.18 | 0.95 | 0.40 |
| 0.915 | 0.89 | 0.18 | 0.81 | 0.07 | 0.80 | 0.22 |
| 0.905 | 0.35 | 0.00 | 0.27 | 0.00 | 0.39 | 0.03 |

- **The 0.925 row equals the 0.931 row** because no 03 graph lies between them.
- **The figures depend on the assumptions.** With four ensembles at zero exceedances, the prior
  matters (Astra). A Gaussian model at 03's observed z values gives 0.98 for the primary test and
  0.18 for 03's rule, which is lower under that alternative model.
- **The most likely split:** by this table the primary test passes and 03's rule fails with
  probability roughly 0.5. §10 fixes the wording for that case in advance.

**Reading it:**
- If 03's effect is real and about as large as measured, the primary test should pass.
- If N2's P4 is nearer the top of the routing-matched and mirror ensembles (about 0.905), it will
  usually fail.
- A failure is not proof that there is no difference. The report gives every count and interval.

## 8. Budget and run

- **Cost:** 768 ensemble graphs plus 5 N2 graphs, at about 111 s each (03's rate): about 24
  GPU-hours.
- **Cap:** 32 GPU-hours for the ensemble graphs, cumulative across restarts. v2 set 28 hours.
  Fable noted that at the preflight's 126 s per graph, 768 graphs need about 27 hours, so the cap
  was raised before binding (D061).
  - 03 averaged about 110 s per graph.
  - 32 hours covers up to about 150 s per graph.
  - A resume after N2 is measured also counts N2's seconds, which only makes the cap stricter.
  - It is registered in code (`INSTANCES["03r"]["max_hours"]`). The runner refuses any other value
    on the command line (`scripts/exp03.py run --instance 03r`).
  - **The cap is never extended.** If it bites, the remaining ensemble graphs are skipped. The
    skips are proportional across ensembles because of the interleaving. N2 and its variants are
    then measured, and the report is run on what exists, with the completeness rule of §6
    (Fable).
- **Order:** the ensembles are interleaved in proportion to their sizes. N2, N2-rev and N2perm4-6
  come **last** and are exempt from the cap.
- **The same rules as 03 §8:**
  - stopping and resuming never depend on a measured value;
  - the run refuses uncommitted code;
  - measurements record their commit, input hashes (including the N2 cache), device and instance;
  - the report refuses a mixture;
  - graph files are checked against the manifest;
  - measurements go to `runs/exp03r/measures/`.

## 9. Deviations

As in 03 §9. Any deviation is recorded in DECISIONS.md and in the results, and any mid-run code
change means re-measuring every graph.

## 10. Outcomes, their fixed wording, and what will be published

The wording for each outcome is fixed now, and it is used in RESULTS.md and the README (Fable,
Astra, D060).

| outcome | fixed wording |
|---|---|
| **The primary test passes, and so does 03's full rule for P4** | "Replicated under the registered single-signal test and under 03's original three-signal rule." |
| **The primary test passes; 03's full rule fails** | "Replicated under the registered single-signal test (maximum p = x). Under 03's three-signal rule the Holm-adjusted p would have been y (counts …). 03's full significance criterion was not reproduced." |
| **The primary test fails, and N2 is not consistent with any ensemble** | "Not replicated under the registered rule. N2 remained above the central 90% of k of 5 ensembles (counts …). The failing gates were …." |
| **The primary test fails, and N2 is consistent with some ensemble** | "Not replicated; N2 is consistent with ensemble(s) X." |
| **Withheld** (N2 invalid, or completeness not met) | "No verdict: the replication was incomplete or unevaluable (reason …). No rerun without a new pre-registration." |

**Every outcome:**
- **The gate table.** The per-ensemble gate table (§6) is published for every outcome in which
  N2 is valid on P4, withheld included. A split is described from it, never from the labels
  alone. If N2 is invalid, the accounting counts of §6 are published instead.
- **How 03 and 03r are presented:**
  - side by side, each with both decision rules, and never replaced by a pooled result;
  - pooled analyses are exploratory (§11) and can never stand in for a failed or withheld
    registered verdict;
  - p-values from the two runs are never combined.
- **The README's sentence:**
  - it carries the probe caveat: "with the same probe, stimulus bank and code; the replication
    tests sampling, not the probe";
  - it says that a full replication was run before publishing, and why: one graph decided 03's
    verdict (D058);
  - it says who contributed what to that decision (D059): Fable asked for replication before any
    public claim; Astra specified independent genomes and did not require replication first;
    Claude leaned toward replicating first; the owner decided.
- **P1 and P3:** their results are reported whatever they are, as recurring or not recurring
  decision labels, not as evidence of absence.
- **No further attempt designed to make P4 pass.** A later experiment on the mechanism needs its
  own case and its own pre-registration.
- **Replicated:** the mechanism is the next step (03 §10). A pass supports sampling stability
  under this probe. It is not an independent confirmation, and not a mechanism (§2).

## 11. Not registered

These are exploratory:
- pooled analyses that combine 03's and 03r's ensembles;
- any analysis of N2-rev or N2perm4-6 beyond their values and ranks;
- any mechanism analysis.

## 12. Changes from the team's review

### v3, from the confirmation pass (D061)

**Astra: "not ready to bind" until two items were fixed.**
- **A withheld verdict lost the per-ensemble statistics** (reproduced by Astra). They are now
  computed whenever N2 is valid, with gates, and tested.
- **The preflight measurement is disclosed** (§1), and the binding boundary is clarified.
- **Also fixed:**
  - the supplement drops non-finite values and requires provenance;
  - the threshold argument for P4 alone is softened, using Astra's figures;
  - the claim that one failing ensemble makes every label "inconclusive" is corrected.

**Fable: "ready to bind" once a §10 sentence was corrected and the cache hashed raw.** Both are
done, and:
- the cap is raised to 32 hours for headroom;
- §4 notes that N2perm4-6's permuted-magnitude condition is a second permutation;
- §8 notes that a resume counts N2's seconds.

### v2, from the review of v1 (D060)

Both reviewers judged the design a faithful replication, and runnable once the outcome rules
were completed. Astra checked the code, the 768 manifest hashes, graph distinctness and seed
streams; it ran `power.py` and 14 report tests. Fable checked the code by reading and recomputed
the power figures.

**Must fix (both):** outcome rules and wording for every case (§10):
- the split between the two rules;
- a per-ensemble split, shown by the new gate table;
- a withheld result, which is now written explicitly by the code;
- how the two runs are presented together.

**Astra:**
- **The permutation was not fresh.** The permuted-magnitude secondary condition reused 03's
  weight permutation for N2 and N2-rev. It is now fresh per graph, and the retained elements are
  listed (§4).
- **§7 is a posterior-predictive probability of the rank gates,** not the power of the whole
  procedure. It is relabelled, with its omissions, its prior sensitivity and N2's own noise now
  shown.
- **The supplement** crashed on a missing or calibration-failed graph and did not summarise
  everything promised. It is fixed, with registered masks and counts, and there are tests.
- **The two runs are not independent evidence,** so p-values are never combined (§2).
- **Completeness:** SH-route's floor is now 240, and counts are reported separately.
- **The cutoffs** use n = valid graphs; SH-route's cutoff under 03's rule is 3 versus 4 of 256.
- **The N2 cache** is now hashed into provenance.
- **P1 and P3 wording:** a recurring label is not evidence of absence.

**Fable:**
- **The threshold argument for P4 alone** (§6), and the error rates.
- **256 SH-route graphs** are stated as Fable's request, not a power decision.
- **The cap** is registered in code, refused on the command line if different, and never
  extended.
- **The withheld primary** is written, not omitted.
- **The probe caveat** goes into the README sentence.
- **Effect intervals** for 03 and 03r are compared side by side.
- **The calibration seed** also sets the calibration map, so the gains are not comparable across
  runs.
- **`power.py`'s** α/3 and margin assumptions are stated.
