# WormWars 03: pre-registration

**Fixed on 2026-09-25, before any N2 measurement.** No N2 brain, and no brain on N2's wiring (N2-rev,
N2perm), has been run for 03. The binding version of this file and of the code is the commit the
run's first measurement follows. The design argument is in `DESIGN.md` (v3.1) and `DECISIONS.md`
D050-D053. Where they differ, this file is binding.

## 1. Disclosures

1. **Structural facts about N2 were computed before this file,** from its published wiring; no
   brain was run:
   - mirror symmetry: 0.639 of chemical and 0.620 of gap edges keep their mirror image;
   - 669 reciprocal chemical pairs;
   - 38 autapses;
   - the food pairs' routing to the motor read-out.
   Every ensemble is built to be compared with these.
2. **Everything else measured so far is on pilot shuffles** (SH101-SH116, never used in the
   ensembles) or on the ensembles' structure:
   - a throughput benchmark (`timing.json`);
   - the ensemble build and validation (`ensembles.json`);
   - the pilot (`pilot.json`).
3. **The first pilot was discarded.** A seed bug made graphs share random genomes (D053); its
   file is kept locally as `runs/exp03-pilot-v1-shared-seeds.json`, and nothing below uses it.
4. **Reviews.** Astra 6 (maximum effort) and Fable 5.1 reviewed the design three times and the
   pilot's precision failure once (`docs/reviews/`, D050-D053). This file goes to both before any
   run, and the changes are listed in §12.

## 2. The question

At generation 0, before any selection:
- is N2 *distinctive relative to null ensembles that share its generic properties*, on three
  signals;
- and is its food-information dependence distinctive?

A verdict of "distinctive" means distinctive relative to these five nulls, not N2-specific in any
unrestricted sense. "Consistent" means inside an ensemble's distribution. It does not mean that
ensemble's constraint is the cause.

## 3. Graphs

- **N2**, the real wiring.
- **N2-rev** (the chemical mask transposed) and **N2perm1-3** (N2's weights permuted over its own
  edges): descriptive only, reported with their ranks, with no verdict.
- **Five ensembles of 128 graphs each**, built and validated before this file:
  - **SH:** ordinary shuffles, identical to 01b's and 02's sampler.
  - **SH-route:** direct read-out edges and weight capped at N2's, for the food pairs of M0, R1
    and R2.
  - **SH-class:** each neuron keeps its in- and out-degree per partner class (the dataset's five
    types).
  - **SH-mirror:** N2's exact mirror-symmetric share, plus the routing cap.
  - **SH-recip:** N2's 669 reciprocal pairs.
- **Validation:** every ensemble passed every rule fixed in design v3 (`ensembles.json`):
  - plateau at 20 and 40 passes, within 0.01;
  - acceptance at least 5% (the lowest is 9%, SH-class);
  - no graph over its Jaccard ceiling;
  - no substitutions.
  Median Jaccard to N2 (chemical): 0.050, 0.051, 0.096, 0.063 and 0.050.
- **Identity:** each graph is fixed by its seed (`ensembles.json`) and its file hash
  (`graphs_manifest.json`). The graph files are not committed, because they carry permuted
  anatomical weights.
- **Committed inputs** (sha256 of the committed blob, first 16 hex digits):

| file | sha256 |
|---|---|
| `configs/mirror_pairs.yaml` | `72721ff0cf832e06` |
| `experiments/03-generation0/ensembles.json` | `83b43aefc1d13315` |
| `experiments/03-generation0/graphs_manifest.json` | `6f75d27e56650fdc` |
| `experiments/03-generation0/pilot.json` | `5f82f7c2eb1c8f6c` |
| `experiments/02-screening/remaps.json` | `7082f0ef76ab5b11` |

## 4. Procedure for every graph (`scripts/exp03.py`, `measure_graph`)

Every graph, N2 included, goes through the same procedure: same sample sizes, same seed scheme,
same worlds. That is what makes N2 exchangeable with an ensemble's graphs under the null.

- **Calibration:** motor gains calibrated in-world on T0 with 1 024 random genomes (D035's
  method). N2's calibration is also validated on 2 048 independent genomes. The validation is
  reported, but it never replaces the 1 024-genome gains.
- **Genomes:** random, unselected. The seed is a SHA-256 hash of the graph's name. 256 fitness
  genomes; the first 64 are shared by every fitness cell and by coverage. 2 048 probe genomes;
  the first 256 are used for the secondary response conditions.
- **Worlds:** 16 fixed world ids (993 000 000 to 993 000 015), shared by every graph and task,
  run seed 3.
- **Fitness cells:**
  - T1 at M0 and T1-const at M0, 256 genomes × 16 worlds (P3);
  - T1 at R1 and at R2, and T0 at M0, 64 × 16 (secondary).
  T1-const is T1 with the food signal replaced by each world's tick-0 mean.
- **Task C (coverage):** 64 × 16, the T0 world with no food, no drain and no hazard damage.
  Score: the union of cells the swarm visits. Descriptive.
- **Input response:** 02's corrected probe (b = 0.1, d = 0.05, 40 ticks from rest, raw
  read-out), saved per genome:
  - M0 with 2 048 genomes;
  - R1, R2, MS, M0 without gap junctions, and M0 with uniform and with permuted magnitudes, 256
    each.
- **History:** 02b's matched-input test on the 2 048 probe genomes at M0, with the pilot's
  stimulus bank:
  - food 0.2234 per side, and every other signal at its pilot median (`pilot.json`);
  - rising from 0.25 and falling from 1.75 times the final level, over 10 ticks, after 100 ticks
    at the start level;
  - the steady-state contrast and the decay after 5 ticks are saved.

## 5. Signals

**Primary**, with the direction 02 and 02b predict:

| | signal | per-graph value | expected |
|---|---|---|---|
| P1 | directional selectivity | mean over genomes and ticks of the signed directional turn (raw), divided by the same mean of the absolute common-mode turn, at M0 | N2 above |
| P3 | food-information dependence | mean over genomes × worlds of the T1 score at M0 minus the T1-const score at M0 | N2 above |
| P4 | history dependence | mean over genomes of \|rising − falling\| (raw turn, final tick), divided by the mean of \|steady-state contrast\| | N2 above |

**Secondary** (reported with values, SEs and ranks, no verdicts):
- P2, the own mapping preference: T1 at M0 on the shared 64 genomes, minus the mean of T1 at R1
  and at R2;
- each ensemble's mean P2 against zero (02's "shuffles start worse under M0");
- T0 at M0: the mean and the top-decile mean over genomes (01b's head start);
- coverage;
- absolute directional and common-mode responses;
- P1 under R1, R2, MS, without gaps, and with uniform and permuted magnitudes;
- P4's decay;
- every primary signal for N2-rev and N2perm.

**Exclusions:** a graph whose P1 or P4 denominator mean is below 10⁻⁴, or whose value is not
finite, is excluded from that signal and counted.

## 6. Verdict (`wormwars/exp03/report.py`, `verdict.py`)

For each primary signal *s* and each ensemble *E*:

1. **Measurement SE of each graph's value:**
   - P1 and P4: a bootstrap over genomes of the ratio of means;
   - P3: crossed genome × world variance components, after removing the world profile shared by
     all graphs, since shared worlds cancel in rank comparisons.
2. **The ensemble's latent SD:** τ_E = √(var of its 128 values − mean SE²). Its margin is
   0.5 τ_E, computed at run time from that ensemble's graphs. It uses no N2 data.
3. **Rank tests:** one-sided exact p = (r + 1)/(n + 1), in the expected and in the opposite
   direction, where r counts ensemble values at least as extreme as N2's.
4. **Effect interval:** the 90% joint-bootstrap interval of N2 minus E's mean. World indices are
   resampled once and shared by all graphs; genomes are resampled within each graph, and graphs
   within the ensemble. 1 000 resamples, seed 1.
5. **N2's own 90% interval:** its value ± 1.645 SE.

**Across ensembles and signals:** p_s is the maximum of p_sE over the five ensembles
(intersection-union), then Holm across the three primary signals. The opposite direction is
handled the same way, separately.

**Verdict per signal and ensemble,** mutually exclusive:
- **distinctive:** Holm-adjusted p_s ≤ 0.05, and the effect interval lies entirely beyond +0.5 τ_E
  in the expected direction;
- **reversed:** the opposite-direction Holm-adjusted p ≤ 0.05, and the interval lies entirely
  beyond the margin the other way;
- **consistent:** N2's own 90% interval lies inside E's central 90% (its 5th to 95th percentile);
- **inconclusive:** otherwise.

**Per signal overall:** *distinctive relative to every ensemble* only if distinctive against all
five; *reversed against every ensemble* only if reversed against all five; otherwise *not
distinctive*. Per-ensemble verdicts are always reported.

**Completeness:** a verdict needs N2 and at least 120 valid graphs per ensemble. Otherwise the
signal's verdict is withheld.

## 7. Power and precision (from the rerun pilot, `pilot.json`)

| signal | latent between-graph SD | per-graph SE | reliability |
|---|---|---|---|
| P1 | 0.032 | 0.014 | 0.85 |
| P3 | 0.0071 | 0.0085 | 0.41 |
| P4 | 0.074 | 0.0063 | 0.99 |

**Simulated probability of "distinctive relative to every ensemble"** (1 000 simulations per
cell). N2 is placed z latent SDs above every ensemble's mean; the other two signals are at the
null; the full rule of §6 is applied:

| z | 2.5 | 3 | 4 | 5 | 6 | 8 |
|---|---|---|---|---|---|---|
| P1 | 0.07 | 0.44 | 0.99 | 1.00 | 1.00 | 1.00 |
| P3 | 0.00 | 0.01 | 0.12 | 0.51 | 0.86 | 1.00 |
| P4 | 0.30 | 0.90 | 1.00 | 1.00 | 1.00 | 1.00 |

- **P3 has little power per latent SD.** Random shuffled brains barely differ in food-information
  dependence, and genome sampling dominates each graph's measurement.
- **In absolute units,** P3 detects an N2 effect of about 0.043 score units (6 latent SDs) with
  86% power. It detects effects below about 0.03 rarely.
- **A null P3 result means "smaller than about 0.04",** not "no food-information dependence".
- A reliability of 0.41 means P3's between-graph spread is mostly measurement noise. The rank
  test stays valid, since every graph is measured the same way, but it loses power.
- Reaching reliability 0.9 for P3 would take about 75 GPU-hours, and is not bought here.

## 8. Budget and run

- **Cost:** about 111 seconds per graph in the pilot; 645 graphs is about 19.9 GPU-hours.
- **Cap:** 24 GPU-hours (`exp03.py run --max-hours 24`), stopping between graphs.
- **Order:** N2, N2-rev and N2perm1-3 first, then the five ensembles interleaved graph by graph.
  A stop removes graphs evenly across ensembles.
- **Resumable:** one file per graph under `runs/exp03/measures/`.

## 9. Deviations

Any deviation is recorded in DECISIONS.md and in the results. A crash or bug found mid-run is
fixed and recorded. The affected graphs are re-measured, since measurements are deterministic
given the seeds. Completed graphs are kept only if the bug provably did not touch them.

## 10. What the results decide

- **A signal distinctive relative to every ensemble:** N2 has a generation-0 property that none of
  these generic structures reproduces. The next step is the mechanism.
- **Consistent with an ensemble:** the signal is within the range that ensemble's structure
  produces. The claim narrows, and the series continues (D045).
- **Every ensemble** (SH, SH-route, SH-class, SH-mirror and SH-recip) becomes a control available
  to 03a and 04, whatever the result.

## 11. Not registered

The following are exploratory and chosen as needed:
- any comparison among the ensembles themselves;
- any analysis of N2-rev or N2perm beyond their reported values and ranks;
- any analysis of the secondary signals beyond their reported values.

## 12. Changes from the team's review of this file

(Filled in before the run.)
