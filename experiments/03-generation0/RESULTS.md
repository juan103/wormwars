# WormWars 03: results

**At generation 0, N2's random brains carry more of their recent input than the brains of any of
five null ensembles do.** This is P4, history dependence, one of three pre-registered signals. It
measures how much of the difference between two starting food levels is still in the turn output
after the input has become the same. N2 is:
- above all 128 graphs in four ensembles, and above 127 of 128 in the routing-matched one;
- above the ensembles that match its degree sequence plus, one at a time, its food routing, class
  structure, mirror symmetry or reciprocal wiring.

The verdict is *distinctive relative to every ensemble*, just inside the registered threshold
(Holm-adjusted p = 0.047 against 0.05). On the other two primary signals N2 is not distinctive:
- **P1, directional selectivity:** N2 sits near the middle of every ensemble.
- **P3, food-information dependence:** the registered criterion was not met. N2's estimate is
  slightly negative, and the test had little power.

**How the run was done:**
- Everything was fixed in [`PREREGISTRATION.md`](PREREGISTRATION.md) before any N2 measurement,
  after several rounds of review by Astra 6 and Fable 5.1 (D050-D055).
- N2 and its variants were measured last.
- One deviation occurred (D056): the first run stopped on a faulty hash check, and every graph
  was re-measured from zero. No N2 data existed at that point.

**Run facts:**
- **Scale:** 645 graphs, 19.75 GPU-hours (cap 24), one GPU, binding commit `132acae`.
- **Data:** measurements in `runs/exp03/measures/` (local, git-ignored); the report is
  [`report.json`](report.json), from `scripts/exp03.py report`.
- **Validity:** every signal had all 128 graphs valid in every ensemble, and no calibration
  failed. N2 was valid on all three primaries.

Sections are marked **registered** (the verdicts of §6 and the values §5 lists) or
**exploratory** (§11: anything beyond those values and ranks).

---

## Registered verdicts (§6)

Each per-graph value is a mean over unselected random genomes, measured the same way for every
graph.
- **p:** the one-sided exact rank p, (r + 1)/129.
- **Effect interval:** the 90% joint bootstrap of N2 minus the ensemble mean.
- **Margin:** 0.5 of the ensemble's latent between-graph SD.
- **z:** N2's distance from the ensemble mean in latent SDs.

### P4, history dependence: distinctive relative to every ensemble

N2 = **0.931** (SE 0.006, 90% interval 0.921-0.941). The maximum p over the ensembles is 0.0155;
the Holm-adjusted p is **0.0465**.

| ensemble | mean | central 90% | graphs ≥ N2 | p | N2 − mean [90%] | margin | z | verdict |
|---|---|---|---|---|---|---|---|---|
| SH | 0.747 | 0.604-0.853 | 0 | 0.008 | +0.170 to +0.198 | 0.036 | 2.5 | distinctive |
| SH-route | 0.843 | 0.786-0.904 | 1 | 0.016 | +0.077 to +0.099 | 0.018 | 2.5 | distinctive |
| SH-class | 0.825 | 0.735-0.886 | 0 | 0.008 | +0.094 to +0.118 | 0.024 | 2.2 | distinctive |
| SH-mirror | 0.840 | 0.782-0.897 | 0 | 0.008 | +0.081 to +0.103 | 0.018 | 2.5 | distinctive |
| SH-recip | 0.758 | 0.642-0.867 | 0 | 0.008 | +0.158 to +0.190 | 0.037 | 2.4 | distinctive |

**How fragile this is:**
- **One graph decides the margin.** p = 0.0155 is the second-smallest value the rank test can
  give. It comes from the one SH-route graph at or above N2. Two graphs at or above N2 in any one
  ensemble would have given p = 0.023, and a Holm-adjusted p of 0.070.
- **The design was not expected to detect an effect of this size.** N2 is 2.2-2.5 latent SDs
  above the ensembles. The registered power table (§7) gave 0.00 at z = 2 and 0.33 at z = 2.5,
  assuming every ensemble had SH's pilot parameters.
- **Why it passed anyway:** the observed latent SDs of SH-route, SH-class and SH-mirror (0.036,
  0.049 and 0.036) were smaller than the pilot's 0.074. Their central ranges end below N2 even
  at these z values.
- **What would count against it:** a replication with fresh ensemble draws would have to put N2
  above essentially every graph again.

### P1, directional selectivity: not distinctive

N2 = +0.004 (SE 0.021). Holm-adjusted p = 0.93.

| | SH | SH-route | SH-class | SH-mirror | SH-recip |
|---|---|---|---|---|---|
| graphs ≥ N2 | 59 | 47 | 59 | 50 | 59 |
| verdict | consistent | inconclusive | inconclusive | inconclusive | consistent |

The three "inconclusive" verdicts come from their small margins: 0.002-0.005, against N2's SE of
0.021. N2 lies within every ensemble's central 90% range.

Before the run, §7 noted that 02's value would have put N2 at about z = 3. The observed z is at
most 0.8.

### P3, food-information dependence: registered criterion not met

N2 = −0.010 (SE 0.014), against ensemble means of +0.001 to +0.003. Holm-adjusted p = 0.94;
inconclusive against every ensemble.
- **The estimate is on the low side:** 114-120 of the 128 graphs in each ensemble are above N2.
- **The opposite direction is not significant either:** the largest one-sided p is 0.116, and the
  Holm-adjusted p is 0.35.
- **As registered (§7), this is not a bound** on N2's food-information dependence. The pilot put
  P3's reliability at 0.41, and even a true member would be "consistent" only about 11% of the
  time.
- **SH-route's margin was 0,** as the pre-registration allows, because its latent SD estimate
  truncated to 0.

---

## Registered secondary values (§5, no verdicts)

Quantiles are each ensemble's 5th, 50th and 95th percentiles; the SH range is its 5th to 95th.

| | N2 | SH median (5th-95th) | other ensembles' medians |
|---|---|---|---|
| P2, mapping preference (M0 minus the mean of R1 and R2) | −0.009 | −0.000 (−0.025 to +0.026) | −0.001 to +0.001 |
| T0 at M0, mean over genomes | 0.90 | 0.89 (0.83-0.96) | 0.88-0.90 |
| T0 at M0, top-decile mean | 1.69 | 1.51 (1.26-1.77) | 1.50-1.53 |
| coverage, task C (cells) | 115 | 115 (101-133) | 113-118 |
| absolute directional response, M0 | 0.0150 | 0.0029 (0.0016-0.0065) | 0.0020-0.0031 |
| common-mode turn response, M0 | 0.0296 | 0.0059 (0.0031-0.0130) | 0.0040-0.0062 |
| P4 decay (share left 5 ticks later) | 0.88 | 0.76 (0.67-0.83) | 0.77-0.82 |

- **P2 is zero in every ensemble.** Each ensemble's mean P2 has a t-interval that contains 0; for
  SH it is −0.0006 [−0.0033, +0.0022].
- **P1 in other conditions (N2):**

  | R1 | R2 | MS | gaps off | uniform magnitudes | permuted magnitudes |
  |---|---|---|---|---|---|
  | −0.057 | −0.016 | +0.013 | −0.089 | −0.072 | −0.060 |

  The ensemble quantiles are in `report.json`.

**The N2 variants**, with their values and the share of each ensemble at or above them:

| | P1 | P3 | P4 | share at or above on P4 (SH, route, class, mirror, recip) |
|---|---|---|---|---|
| N2 | +0.004 | −0.010 | **0.931** | 0.00, 0.01, 0.00, 0.00, 0.00 |
| N2perm1 | +0.017 | −0.008 | 0.797 | 0.25, 0.87, 0.84, 0.87, 0.33 |
| N2perm2 | −0.005 | −0.014 | 0.919 | 0.00, 0.01, 0.00, 0.00, 0.00 |
| N2perm3 | −0.011 | −0.002 | 0.869 | 0.01, 0.22, 0.16, 0.22, 0.05 |
| N2-rev | invalid (denominator below 10⁻⁴) | −0.000 | 0.898 | 0.00, 0.06, 0.02, 0.06, 0.02 |

- **N2perm:** N2's topology with its weights permuted over its edges.
- **N2-rev:** N2 with every chemical synapse's direction reversed.
- **Shares:** the report's `(r + 1)/129` ranks.

---

## Exploratory (§11; chosen after seeing the data)

### What P4's value is made of

P4 is a ratio: the history difference at the final tick, divided by the steady-state contrast
between the two starting levels. So a high P4 could come from a large numerator or a small
denominator. Recomputed from the measurements:

| | numerator: mean \|rising − falling\| | denominator: mean \|steady contrast\| | mean common-mode turn |
|---|---|---|---|
| N2 | 0.120 | 0.129 | 0.030 |
| ensemble medians | 0.015-0.019 | 0.018-0.026 | 0.004-0.006 |
| largest single ensemble graph | 0.063 | 0.073 | 0.020 |

**N2's high P4 is not a small denominator.** Every magnitude of N2's is larger than any of the 640
ensemble graphs': about 6-8 times the medians for the numerator, and 5-7 times for the
denominator. So there are two separate observations:
1. **N2's random brains are much more responsive to food input.** This is what 02 found, and the
   registered common-mode secondary above shows it too.
2. **Given that responsiveness, they hold more of it.** The ratio is higher, and more of the
   difference is left five ticks later (decay 0.88 against the ensemble medians of 0.76-0.82).

**Responsiveness and persistence separate among the N2 variants:**
- N2perm1 is nearly as responsive as N2 (common mode 0.023) but has an ordinary P4.
- N2perm2 is only as responsive as a typical shuffle (0.006) but has a P4 above essentially every
  ensemble graph.
- N2-rev barely responds at all (common mode 0.0001, about 300 times below N2), yet its P4 is also
  high.

So high P4 does not simply follow from a strong drive.

**On topology versus weights:**
- Two of the three weight permutations, and the reversal, keep P4 high relative to SH. This
  suggests N2's topology contributes.
- One permutation drops to an ordinary value, so where the weights sit matters too.
- These are single draws, and the pre-registration does not attribute cause.

**Compared with 02b's evolved champions:** 02b found that selection made the champions' turn
history-dependent. At generation 39 the difference was a median 0.90-0.95 of the steady
contrast, and 0.83-0.87 of it was left five ticks later. N2's *unselected* random brains already
average 0.93 and 0.88 here.
- **Why this is not a like-for-like comparison:** 02b's figures are medians of per-champion
  ratios over a few selected champions; 03's are ratios of means over 2 048 random genomes.
- **What it raises:** whether selection in 02b amplified a property N2 already has at birth,
  which is what 02b's generation-0 gap (N2 0.095 against SH 0.030) pointed to.

**On the scale of P4:** a value near 1 means the final tick still shows almost the whole
difference between the starting levels. N2 (0.93) and N2perm2 (0.92) are close to that. The
probe's window may therefore compress differences among the slowest graphs. That would tend to
understate, not create, a difference at the top.

**The mechanism is not tested here.** Candidates:
- saturation or slow nonlinear dynamics under N2's stronger drive, though N2-rev argues against a
  pure drive explanation;
- slow modes in the wiring, for example loops, or the gap-junction network.

### Readings from experiment 02 that do not hold at generation 0

1. **"On average N2's response points toward the stronger side"** (02 RESULTS, generation-0
   input response) does not replicate.
   - 02: a signed raw response of +0.0029, from 256 random genomes, with no uncertainty saved.
   - 03: +0.0001, from 2 048 genomes on an independent seed. N2's P1 is in the middle of every
     ensemble.
   - The absolute directional response agrees (0.0146 in 02, 0.0150 here), so the probe measures
     the same thing. 02's signed value was most likely sampling noise.
2. **"The shuffles start worse under the biological mapping"** (02, D042) came from best-of-32
   generation-0 *champions*. Among *unselected* random brains, no ensemble's mean mapping
   preference differs from zero, and N2's own is −0.009.

What stands from 02 at generation 0: **N2's random brains respond much more strongly to food
input than shuffles do**. Here the common mode is 5-7 times the ensemble medians, and above every
ensemble graph.

---

## What this decides (§10)

- **P4, distinctive relative to every ensemble:** N2 has a generation-0 property, holding on to its
  recent input, that none of the five null ensembles reproduces.
  - Each ensemble adds one constraint at a time to the degree sequence. A structure combining two
    of them, for example mirror symmetry together with routing, is not excluded.
  - The verdict is borderline (see "How fragile this is").
  - §10 names the mechanism as the next step. The questions below are not registered:
    - Where does the persistence live? Silencing or deleting candidate loops is now possible with
      the deletion operator.
    - Does it survive with gap junctions removed?
    - Is it the same slow level-memory that 02b found in evolved champions (see the exploratory
      comparison above)?
    - Does it replicate on fresh ensemble draws?
- **P1 and P3:** no N2-specific generation-0 signal was found.
  - For P1 the ensembles bracket N2 comfortably.
  - For P3 the test had little power, and N2's estimate is on the low side.
  - Neither supports "N2 is specialised at birth for stereo steering or for food information".
- **For the owner's question** (is the connectome shaped for worm-like tasks?):
  - The one distinctive property is holding recent input. It is measured with food input, but
    nothing in the design shows it is food-specific.
  - The food-specific and stereo-specific signals show nothing distinctive.
- **Every ensemble** is built, validated and hashed, and is now available to 03a and 04 as a
  control.

## Deviations

- **D056:** the first run (commit `0ef9a3d`) stopped after 52 ensemble graphs on a faulty
  graph-hash check. The check was fixed, the 52 measurements were set aside
  (`runs/exp03/measures-aborted-0ef9a3d/`), and every graph was re-measured from zero, as §9
  requires.
- No other deviation. The report ran as registered, and no parameter was chosen after seeing the
  data.
