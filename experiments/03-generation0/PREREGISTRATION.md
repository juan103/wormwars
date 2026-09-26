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

**The null is topology plus weight placement.** N2 keeps its anatomical weights on its own
edges, while every ensemble permutes them; N2perm is descriptive only.

**The tests are approximate reference-ensemble tests** (Astra, D054), not exact permutation tests:
- each control graph is a finite swap chain started from N2 and stopped after a fixed number of
  accepted swaps, at a verified plateau;
- the routing cap is enforced by greedy weight swaps, not a joint redraw.
The rank p-values are exact only under the assumption that N2 is exchangeable with these
ensembles' graphs.

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
- **Validation:** every ensemble passed the rules the build checked (`ensembles.json`):
  - plateau at 20 and 40 passes, within 0.01;
  - acceptance at least 5% (the lowest is 9%, SH-class);
  - no graph over its Jaccard ceiling;
  - no substitutions.

  Median Jaccard to N2 (chemical): 0.050, 0.051, 0.096, 0.063 and 0.050. The median pairwise
  Jaccard *within* each ensemble is the same: 0.048, 0.049, 0.095, 0.063 and 0.049 (40 graphs
  each). So the graphs are as different from one another as from N2.
- **Retired rule:** design v3's hop-distance rule for SH-route was never enforced by the build,
  and is retired here (Astra, D054). SH-route and SH-mirror control direct read-out edges and
  their weight, not path length. For example, SH-route-20000 shortens AWAL's gap-only distance to
  the turn read-out from 3 hops to 2.
- **Identity:** each graph is fixed by its seed (`ensembles.json`) and its file hash
  (`graphs_manifest.json`). The graph files are not committed, because they carry permuted
  anatomical weights.
- **Committed inputs** (sha256 of the committed blob, first 16 hex digits):

| file | sha256 |
|---|---|
| `configs/mirror_pairs.yaml` | `72721ff0cf832e06` |
| `experiments/03-generation0/ensembles.json` | `68cfb8a8eb6d95c6` |
| `experiments/03-generation0/graphs_manifest.json` | `6f75d27e56650fdc` |
| `experiments/03-generation0/pilot.json` | `98d098af28b16a4e` |
| `experiments/02-screening/remaps.json` | `7082f0ef76ab5b11` |

## 4. Procedure for every graph (`scripts/exp03.py`, `measure_graph`)

Every graph, N2 included, goes through the same procedure: same sample sizes, same seed scheme,
same worlds. Symmetric measurement is necessary for the tests of §6. It does not by itself make
N2 exchangeable with an ensemble's graphs; that remains the assumption stated in §2 (Astra,
D055).

- **Calibration:** motor gains calibrated in-world on T0 with 1 024 random genomes (D035's
  method); the achieved drive is saved.
  - **Validation:** N2 and the first 8 graphs of every ensemble are also checked on 2 048
    independent genomes (seed 1). The check is saved, but it never replaces the gains.
  - **Failure:** a graph whose calibration fails to converge is excluded from every signal and
    counted. If N2's fails, every verdict is withheld.
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
  - R1, R2, MS and M0 without gap junctions, on the first 256 of those genomes;
  - M0 with uniform and with permuted magnitudes on 256 fresh genomes (the same seed, a separate
    draw). These are unpaired with the rest (Fable, Astra, D054).
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

**Secondary** (no verdicts). What the report computes: each secondary value for N2 and its
variants, and each ensemble's 5th, 50th and 95th percentiles of it; for P2, each ensemble's mean
against zero with a t-interval; for the variants, their primary-signal ranks. Secondary SEs and
ranks for N2 are not computed and are not claimed (Astra, D055). The secondary values are:
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
finite, is excluded from that signal and counted. The same validity mask is applied in every
computation: the rank test, the SEs, the margin, the bootstrap and the quantiles.

## 6. Verdict (`wormwars/exp03/report.py`, `verdict.py`)

For each primary signal *s* and each ensemble *E*:

1. **Measurement SE of each graph's value:**
   - P1 and P4: a bootstrap over genomes of the ratio of means, 1 000 draws, seed 0;
   - P3: crossed genome × world variance components, after removing the world profile shared by
     the registered ensemble graphs. Shared worlds cancel in rank comparisons. The profile never
     includes N2, its variants, or unregistered files.
2. **The ensemble's latent SD:** τ_E = √(max(var of its valid values − mean SE², 0)). The
   truncation at zero is registered: a margin of 0 leaves the rank test and the interval to
   decide. The margin is 0.5 τ_E, computed at run time from that ensemble's registered graphs,
   with no N2 data.
3. **Rank tests:** one-sided exact p = (r + 1)/(n + 1), in the expected and in the opposite
   direction, where r counts ensemble values at least as extreme as N2's.
4. **Effect interval:** the 90% joint-bootstrap interval of N2 minus E's mean. World indices are
   resampled once and shared by all graphs; genomes are resampled within each graph, and graphs
   within the ensemble. 1 000 resamples, seed 1.
5. **N2's own 90% interval:** its value ± 1.645 SE.

**Across ensembles and signals:** p_s is the maximum of p_sE over the five ensembles
(intersection-union), then Holm across the three primary signals.
- A withheld signal enters Holm with p = 1, so the divisor stays at three.
- The opposite direction is handled the same way, as a separate family. Each direction is held
  at 5%, so the combined error rate across both directions is up to 10% (Astra, D054).
- The effect interval uses 1 000 draws, seed 1.

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

**Completeness:** a signal's verdict needs a valid N2 and at least 120 valid graphs in every
ensemble. Otherwise it is withheld, and the report enforces this before computing any verdict.

## 7. Power and precision (from the rerun pilot, `pilot.json`)

| signal | latent between-graph SD | per-graph SE | reliability |
|---|---|---|---|
| P1 | 0.032 | 0.014 | 0.85 |
| P3 | 0.0071 | 0.0085 | 0.41 |
| P4 | 0.074 | 0.0063 | 0.99 |

**Simulated operating characteristics** (1 000 simulations per cell, D054).

*Assumptions:*
- N2 is measured once and compared with all five ensembles;
- every ensemble has SH's pilot parameters;
- values are Gaussian;
- the margin and effect interval come from the observed ensemble values, with a normal
  approximation to the bootstrap;
- the other two primary signals are at the null.

*Columns:* the probability of "distinctive relative to every ensemble" when N2 sits z latent
SDs above the ensembles; and the probability of "consistent" with every ensemble when N2 is a
true member (z = 0).

| z | member | 2 | 2.5 | 3 | 4 | 5 | 6 | consistent if a member |
|---|---|---|---|---|---|---|---|---|
| P1 | 0.005 | 0.04 | 0.27 | 0.64 | 0.99 | 1.00 | 1.00 | 0.52 |
| P3 | 0.005 | 0.05 | 0.12 | 0.18 | 0.45 | 0.75 | 0.94 | 0.11 |
| P4 | 0.005 | 0.00 | 0.33 | 0.92 | 1.00 | 1.00 | 1.00 | 0.77 |

A "member" is an N2 drawn at random from the ensembles' own distribution, not placed at their
mean. The first version placed it at the mean, which overstated "consistent" for P1 (0.93) and
P4 (1.00) (both reviewers, D055).

**P1:**
- Experiment 02's generation-0 ratio for N2 under M0 was about 0.10, with a different
  aggregation. Against the pilot's mean of about −0.004 and latent SD of 0.032, that is about
  z = 3, so the P1 verdict is roughly a two-to-one chance even if 02's number carries over.

**P3:**
- Its minimum detectable effect at 80% power is about 5.3 latent SDs: about 0.037 score units,
  on a generation-0 T1 score of about 0.89 (4%). Random shuffled brains barely differ on it.
- It will usually be "inconclusive" even if N2 is an ordinary member (consistent only 11% of
  the time).
- If the criterion is not met, the result is reported as exactly that: **the registered
  distinctiveness criterion was not met.** It is not a bound on N2's food-information
  dependence. The v1 wording, "smaller than about 0.04", confused power with an upper bound
  (Astra, D054).
- Reliability 0.9 for P3 would need about 4 460 genomes per cell, roughly 150 GPU-hours. This
  is not bought. v1's "75 GPU-hours" was an arithmetic error (both reviewers).

**P4:**
- P4 is a bounded ratio. The pilot shuffles reach at most 0.86, and z = 3 corresponds to about
  1.0 (z = 4, about 1.07), so the table's upper rows are near the signal's ceiling.
  - *Post-run annotation (D058, text above kept as registered):* P4 is not bounded by 1.
    Nothing in its definition bounds the final history difference by the starting contrast
    (Astra's results review). This sentence affected only the discussion of the power table, not
    any rule.
- 02b's history numbers used a different stimulus, so no expected z for N2 is available.
- Real ensembles differ, so N2's effective z is its smallest across the five.

## 8. Budget and run

- **Cost:** about 111 seconds per graph in the pilot; 645 graphs is about 19.9 GPU-hours.
- **Cap:** 24 GPU-hours (`exp03.py run --max-hours 24`), stopping between graphs.
- **Order:** the five ensembles interleaved graph by graph, so a stop removes graphs evenly.
  Then N2, N2-rev and N2perm1-3 **last**, exempt from the cap. No mid-run decision is taken with
  N2's numbers on disk (Fable, D054).
- **The cap is cumulative:** the saved measurements' wall time is summed, so a restart does not
  reset it.
- **Stopping or resuming may not depend on any measured value.**
- **Provenance:** every measurement records the code commit, the hashes of the registered inputs
  and the device. The run refuses to start with uncommitted code. The report refuses a mixture
  of commits or inputs, and reads only registered graph names.
- **Graph files:** each is checked against `graphs_manifest.json` when loaded, and a mismatch
  stops the run.
- **Resumable:** one file per graph under `runs/exp03/measures/`.

## 9. Deviations

Any deviation is recorded in DECISIONS.md and in the results. The provenance rule of §8 makes any
mid-run code change mean re-measuring **every** graph: the run refuses to resume over
measurements from other code, inputs or a different device, and the report refuses a mixture
(D055). A calibration that does not converge is not a crash. That graph is saved as excluded
and counted (§4).

## 10. What the results decide

- **A signal distinctive relative to every ensemble:** N2 has a generation-0 property that none of
  these generic structures reproduces. The next step is the mechanism.
- **Consistent with an ensemble:** the signal is within the range that ensemble's structure
  produces. The claim narrows, and the series continues (D045).
- **Every ensemble** (SH, SH-route, SH-class, SH-mirror and SH-recip) becomes a control available
  to 03a and 04, whatever the result.

## 10b. Deviations during the run

- **D056.** The first run (commit 0ef9a3d) stopped after 52 ensemble graphs, on a faulty graph-hash
  check: text normalisation applied to binary files. The check was fixed, the 52 measurements
  were set aside, and every graph was re-measured from zero, as §9 requires. No N2 data existed
  when it stopped.

## 11. Not registered

The following are exploratory and chosen as needed:
- any comparison among the ensembles themselves;
- any analysis of N2-rev or N2perm beyond their reported values and ranks;
- any analysis of the secondary signals beyond their reported values.

## 12. Changes from the team's review of this file

Astra 6 and Fable 5.1, both at maximum effort, reviewed the first version
(`docs/reviews/20260925-232702-03-prereg/`). Both said not to start. Astra reproduced verdict-changing
failures on synthetic data. Every point was checked and fixed, with tests where it is code
(D054):

1. **Exclusions and completeness** are enforced in every path. An invalid N2 or an incomplete
   ensemble withholds the verdict, and a withheld signal enters Holm with p = 1 (both).
2. **The P3 world profile and the margins** use registered ensemble graphs only (Astra).
3. **"Exact exchangeability" is reworded** as approximate reference-ensemble tests, and the
   greedy weight repair is disclosed (Astra).
4. **The power table** now uses one N2 draw, observed margins and observed intervals, and adds
   the probability of "consistent" (both). P4 is given in ratio units (Fable).
5. **"Smaller than about 0.04" is removed** (Astra), and the reliability cost is corrected to
   about 150 GPU-hours (both).
6. **The run:**
   - N2 last and exempt from the cap (Fable);
   - a cumulative cap;
   - provenance checks;
   - graph hashes verified at load;
   - only registered names read;
   - stopping may not depend on results (Astra).
7. **Calibration:** validation is implemented, with a rule for a graph whose calibration fails
   (both).
8. **Magnitude variants** are unpaired draws; the text is corrected (both).
9. **The hop-distance rule** is retired and disclosed (Astra).
10. **The error rate across both directions** is stated (both).
11. **The bootstrap sizes and seeds** are fixed (Fable).
12. **The secondary signals** are implemented in the report before any N2 run (both).

A confirmation pass (`docs/reviews/20260925-234635-03-prereg-recheck/`) found the verdict path fixed, and
asked for one more commit before launch (D055):
- the report command's crash on an undefined name is fixed;
- a calibration failure is saved as an excluded, counted graph, and withholds every verdict if it
  is N2's;
- an empty P3 reference set withholds instead of crashing;
- a resumed run refuses measurements from other code, inputs or devices;
- hashes normalise line endings, so they match the committed blobs;
- the dirty-check covers the registered inputs;
- the power simulation draws a true member at random, and §7's table is updated;
- one sentence claiming exchangeability, the §9 rule and the secondary outputs are corrected.
