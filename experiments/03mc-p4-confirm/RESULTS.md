# 03mc: results of the confirmatory test of 03m's leads on P4

**All four primary questions pass under Holm at a familywise α of 0.05, and P4 replicates a third time.** The
sentences in quotation marks are the ones fixed in advance (PREREGISTRATION §6, §7). This study's statistics come
from [`report.json`](report.json), written by `scripts/p4mc.py report` at `79728d8` from the committed
[`measurements.json`](measurements.json). The other numbers name their sources: the power figure (`power.json`),
03's and 03r's P4 (their reports), and the compute (`compute-record.json`, a copy of the run's accounting aggregate).

| Question | Raw p | Holm-adjusted p | Holm threshold | Outcome |
|---|---|---|---|---|
| Q-C, weight placement | 0.0039 | 0.016 | 0.0125 | pass |
| Q-A, gap junctions | 0.0078 | 0.023 | 0.0167 | pass |
| Q-B, RIA and AIY | 0.0113 | 0.023 | 0.025 | pass |
| Q-D, relaxation | 0.0233 | 0.023 | 0.05 | pass |

Holm's step-down compares each raw p with its threshold, in order; equivalently, each adjusted p with 0.05. So Q-C
passes with an adjusted p (0.016) above its threshold (0.0125).

**What this is and is not:**
- **The tests are confirmatory; the hypotheses are not new.** Every hypothesis, margin and endpoint came from 03m's
  exploratory data. Only the draws are new: fresh genomes for every graph (N2's included), 640 fresh null graphs and
  256 fresh weight permutations, all drawn after the pre-registration and its code were bound and pushed
  (`4dff311`, D294).
- **It is not independent of 03, 03r and 03m:** the same connectome, the same five samplers, the same probe and
  stimulus bank. A probe-specific effect or a systematic code error would recur here (§8).
- **It shows that these changes move these numbers, not a mechanism.** The brains are random and unevolved, the
  read-out is hand-chosen, and deletions locate dependencies, not stores. Nothing here is about behaviour, evolved
  brains or the worm.
- **The model-based chance** of all four passing was 0.63 before the run (`power.json`; D289).
- **Terms (§3):** P4 is the mean |rising − falling| difference in the turn read-out at the ramp's end, over the mean
  |steady contrast|, the read-out's difference after 100 ticks held at the two start levels (0.25 and 1.75 times the
  final food level). **"The response"** is that denominator: how strongly the read-out separates the two levels.

## The run

- **Build** (D295): 640 fresh graphs (128 per ensemble), no substitutions; the freshness audit, the content check and
  03's validation rules all passed.
- **Pre-run check** (D296), on old inputs: the probe repeats bit for bit at the registered composition, and matches
  the one-row references within the declared tolerances, with no label changes (`prerun-repeat.json`,
  `prerun-check.json`).
- **Run** (D297): one attempt at `a5b44e2`, 2026-10-16 05:55-13:09 UTC, no interruption. All 2 336 registered units
  were measured and all are valid, so no question is withheld and every ensemble has 128 valid graphs.
- **Compute:** 7.73 of the 10-hour cap (build 0.26, check 0.24, run 7.22; synchronised wall time). The accounting
  aggregate `runs/p4mc/compute.json` is local; a copy is committed as [`compute-record.json`](compute-record.json). The owner gave the word for the GPU stages: "Start 03mc" (2026-10-16), recorded in the start marker
  and in the run's attempt record.

## Third replication of P4 (secondary, reported first)

**"third replication of P4: distinctive relative to every ensemble"** (03r's single-signal rule; maximum rank p
3/129 = 0.023, against SH-route).

| | N2 | SH | SH-route | SH-class | SH-mirror | SH-recip |
|---|---|---|---|---|---|---|
| P4 (ensemble mean) | **0.926** | 0.766 | 0.839 | 0.832 | 0.849 | 0.772 |
| graphs at or above N2, of 128 | | 0 | 2 | 0 | 0 | 0 |
| N2 minus the ensemble mean, 90% effect interval | | 0.145-0.176 | 0.075-0.100 | 0.080-0.107 | 0.065-0.088 | 0.139-0.169 |

N2's P4 is 0.926 (SE 0.0066, from 03's genome bootstrap; N2 ± 1.645 SE gives 0.915-0.937, a 90% normal interval),
against 0.931 in 03 and 0.924 in 03r. Every rank gate and
every margin gate passes.

## Q-A: gap junctions

**"N2's P4 changed unusually little when gap junctions were switched off, relative to each ensemble: graphs per
ensemble that changed as little or less: SH 0 of 128; SH-route 0 of 128; SH-class 0 of 128; SH-mirror 0 of 128;
SH-recip 0 of 128."**

Since the replication is distinctive relative to every ensemble, the registered second sentence applies: **"N2's P4
lead over each ensemble's median narrows without gap junctions, by: SH -0.083; SH-route -0.055; SH-class -0.050;
SH-mirror -0.057; SH-recip -0.075."**

- **Switching gap junctions off raises P4 in N2 and in the typical null graph, but less in N2:** N2's ΔP4 is +0.020 (95% interval
  0.005-0.035). Each ensemble's median ΔP4: SH +0.095, SH-route +0.072, SH-class +0.072, SH-mirror +0.073, SH-recip
  +0.088.
- **N2's lead over each ensemble's median P4** (N2 minus the median, not the mean), intact → gaps-off:

  | | SH | SH-route | SH-class | SH-mirror | SH-recip |
  |---|---|---|---|---|---|
  | intact | 0.155 | 0.087 | 0.083 | 0.075 | 0.142 |
  | gaps off | 0.072 | 0.032 | 0.033 | 0.018 | 0.068 |

- **With gap junctions off, N2's P4 (0.946) is "not distinctive"** (secondary, single-signal rule): the rank gate
  fails against SH-route (14 of 128 graphs at or above N2), SH-class (8) and SH-mirror (23), and the margin gate
  against SH-mirror. Against SH and SH-recip, 1 and 3 graphs are at or above it.

## Q-B: the RIA and AIY pairs

**"Deleting the RIA pair, or the AIY pair, cuts N2's response by more than 40% while P4 stays within 0.02: the history
signal falls approximately in proportion."**

Pooled over 32 batches (65 536 genomes per condition); SEs from the paired bootstrap; intervals are 90% percentile
intervals, reported as a check.

| Deletion | Response cut | Numerator cut | ΔP4 | p, cut > 0.40 | p, \|ΔP4\| < 0.02 |
|---|---|---|---|---|---|
| RIA | 0.608 (SE 0.003; 0.603-0.613) | 0.608 | +0.0002 (SE 0.0014; −0.0021 to 0.0026) | < 10⁻¹⁰⁰ | 1.2 × 10⁻⁴⁴ |
| AIY | 0.504 (SE 0.005; 0.496-0.513) | 0.512 | −0.0151 (SE 0.0021; −0.0187 to −0.0116) | 1.7 × 10⁻⁹¹ | **0.0113** |
| both (descriptive) | 0.748 (SE 0.002; 0.744-0.751) | 0.762 | −0.052 (SE 0.0016; −0.054 to −0.049) | | |

- Q-B's p is the largest of its four parts: AIY's equivalence test, 0.0113. No bootstrap resample was dropped. ("< 10⁻¹⁰⁰" stands for RIA's cut test,
  whose p is 0.0 in floating point.)
- **Descriptive readings, not tests:** AIY's deletion does lower P4 a little: its 90% interval for ΔP4 excludes zero,
  though it lies inside the ±0.02 margin. Deleting both pairs lowers P4 by 0.052, beyond the margin; the double
  deletion was registered as descriptive.
- **The degree-matched controls** (secondary, intersection-union at 0.05): **passed for both targets.** On batch 0,
  RIA's response cut exceeds each of its four controls' (AIB, AVJ, RIM, AVH) by 0.56 to 0.60, and AIY's exceeds each
  of its (AWB, RIF, RIP, RIV) by 0.49 to 0.52. The intersection-union p is 6 × 10⁻⁷¹ for RIA and 5 × 10⁻⁴⁵ for
  AIY.
- **The null-graph deletions** (descriptive; the first 32 graphs of each ensemble, on their own genomes): no null
  graph in any ensemble reaches N2's batch-0 cut, for any of the three deletions (0 of 32 in all 15 comparisons).
  The ensembles' median cuts are 0.009 to 0.017 for RIA, −0.002 to −0.0005 for AIY (intervals spanning zero) and 0.007
  to 0.015 for both, against N2's 0.578, 0.478 and 0.736. Single null graphs reach cuts up to 0.28.
- **The 95-pair screen** (descriptive, batch 0): RIA's deletion has the largest response cut of the 95 bilateral
  pairs (0.578) and AIY's the second (0.478). The next are ASE (0.217) and AIZ (0.086; its ΔP4 is −0.035, 95%
  interval −0.055 to −0.017).

## Q-C: weight placement

**"N2's response is unusually high relative to permutations of its weight magnitudes: 0 of 256 permutations reached
it."**

- N2's response (P4's denominator) is 0.114 (95% interval 0.106-0.123); the permutations' median is 0.024.
- **N2's P4 rank among the permutations** (secondary, at 0.05): **not significant.** 15 of 256 permutations reach
  N2's P4 (p = 16/257 = 0.062). Its low power was stated in advance.
- **The share of N2's excess P4 that the permutations keep** (descriptive): the pooled fresh null median P4 is
  0.826, N2's is 0.100 above it, and the permutations' median (0.878) keeps 52% of that excess (95% interval
  47%-59%).
- **The factorial** (descriptive, the first 32 permutations): N2's response cut minus the permutations' mean cut is
  0.44 for RIA (95% interval 0.39-0.48), 0.42 for AIY (0.39-0.45) and 0.55 for both (0.49-0.60). Under permutation,
  the mean cuts are 0.14, 0.06 and 0.19.

## Q-D: relaxation

**"N2 retained an unusually large share of its history difference 30 ticks after the ramp, relative to each
ensemble: graphs per ensemble that retained as much or more: SH 0 of 128; SH-route 0 of 128; SH-class 2 of 128;
SH-mirror 1 of 128; SH-recip 2 of 128."**

- N2 keeps 0.436 of its difference at tick 30 (95% interval 0.401-0.472); the ensembles' medians are 0.255 to 0.291.
- **The other ticks** (secondary, each at 0.05): all four pass.

  | Tick | N2's share | Ensembles' medians | Largest count at or above N2, of 128 | p |
  |---|---|---|---|---|
  | 10 | 0.768 | 0.618-0.666 | 1 | 0.016 |
  | 50 | 0.269 | 0.110-0.133 | 3 (SH-recip) | 0.031 |
  | 100 | 0.127 | 0.018-0.034 | 5 (SH-mirror, SH-recip) | 0.047 |
  | 300 | 0.090 | 0.001-0.009 | 5 (SH-class, SH-recip) | 0.047 |

  At tick 300 a failure was expected in advance; the test passed, narrowly.
- **Long-lived differences** (descriptive): of N2's 1 977 genomes whose difference starts at 10⁻³ or more (§7 says "above"; the
  code uses ≥), 43 (2.2%) keep more than 10% of their difference at tick 300; the ensembles' medians are 0.08% to 0.36%. 26 of N2's genomes are settled with
  separation left; across the null graphs the median is 0 or 1 per graph, but single null graphs reach 28 to 126.
  No stable states are claimed (§7).

## Q-E: P4 before the tanh (secondary)

**"P4's distinctiveness persists on the pre-tanh read-out"** (maximum rank p 3/129 = 0.023, against SH-route). N2's
pre-tanh P4 is 0.917; the ensembles' means are 0.769 to 0.849. The tanh stays in the recurrent dynamics, so this is
robustness to the read-out map only.

**The read-out's tanh slope** (descriptive): N2's turn read-out neurons have a mean tanh slope of 0.438 at the holds'
end and at the ramp's end; the ensembles' medians are 0.73 to 0.74, and no null graph is below N2.

## What follows

- **03m's four leads hold on fresh draws,** under tests fixed in advance:
  - switching gap junctions off raises the null graphs' P4 more than N2's, and narrows N2's lead;
  - deleting RIA or AIY cuts N2's response by 61% or 50% while P4 moves by less than 0.02;
  - N2's response is far above that of permutations of its own weight magnitudes;
  - N2 keeps a larger share of its history difference 30 ticks after the ramp.
- **What stays open** (§7, "not claimed"):
  - whether any deletion removes the elevated P4. The double deletion lowers it by 0.05, to 0.875. That is above each
    ensemble's mean intact P4 (0.766 to 0.849) but inside their spread: 4, 24, 18, 30 and 6 of 128 graphs (SH,
    SH-route, SH-class, SH-mirror, SH-recip) are at or above it, so it would not be distinctive by the rank rule. A
    descriptive comparison, not a test;
  - stable states;
  - whether weight placement acts through RIA and AIY.
- **Next on the roadmap:** 03a's six-neuron proof of concept (D094).

## Components, counts and the full records

**Counts:** every question is complete. Q-A, Q-D and the ensemble secondaries: 128 planned, measured and valid
graphs per ensemble, and a valid N2. Q-C: 256 permutations planned, measured and valid. Q-B: 32 batches planned,
measured, valid and paired for each condition.

**Per-ensemble rank p** (SH, SH-route, SH-class, SH-mirror, SH-recip; a question's p is the largest):

| | SH | SH-route | SH-class | SH-mirror | SH-recip |
|---|---|---|---|---|---|
| Q-A | 1/129 | 1/129 | 1/129 | 1/129 | 1/129 |
| Q-D | 1/129 | 1/129 | 3/129 | 2/129 | 3/129 |
| replication | 1/129 | 3/129 | 1/129 | 1/129 | 1/129 |
| Q-E | 1/129 | 3/129 | 2/129 | 2/129 | 1/129 |
| gaps-off P4 | 2/129 | 15/129 | 9/129 | 24/129 | 4/129 |

**Not reproduced above, in [`report.json`](report.json):** the full 95-pair screen with numerator cuts and paired
intervals (`descriptive."pair screen, batch 0"`); every null graph's deletion cuts with each ensemble's median
interval (`descriptive."null-graph deletions"`); the full retention curves at 32 ticks (`descriptive.curves`); the
factorial's per-permutation cuts (`descriptive.factorial`); each graph's P4 for the replication, Q-E and gaps-off
(`replication`, `Q-E`, `gaps_off_levels`, `per_ensemble.*.values`); and the double deletion's 95% intervals
(`Q-B.per_deletion.both.bootstrap`).

## Reproduce it

See the [README](README.md#reproduce-it). The per-genome arrays are local (`runs/p4mc/arrays`); `measurements.json`
holds their sha256, and `p4mc.py report` checks them before any statistic.
