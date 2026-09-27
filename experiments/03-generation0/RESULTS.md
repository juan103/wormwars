# WormWars 03: results

> **Replicated (03r, 2026-09-28).** The pre-registered full replication, with fresh graphs and
> fresh genomes, gives: *"Replicated under the registered single-signal test and under 03's
> original three-signal rule."* In 03r, P1 recurs as "not distinctive", and P3 comes out
> *reversed* (N2 below every ensemble), a new, unpredicted secondary label. See
> [03r's results](../03r-replication/RESULTS.md).

**N2 stands out on one of three pre-registered signals: history dependence (P4).** The test brings
two food histories to the same input, then asks how much of the difference set by the earlier
food level is still in the turn read-out. On that probe, N2's random, unselected brains keep more
of it than every one of five reference ensembles of shuffled wirings.
- In four ensembles N2 is above all 128 graphs.
- In the routing-matched ensemble it is above 127 of 128: one graph, SH-route-20078, is at
  0.934 against N2's 0.931.

**The verdict is "distinctive relative to every ensemble", with an adjusted p of 0.047.** That is
borderline: one more SH-route graph at or above N2, or two in any other ensemble, would have
made it 0.070.

**The other two signals show nothing distinctive:**
- **P1, directional selectivity:** N2 sits near the middle of every ensemble.
- **P3, food-information dependence:** the registered criterion was not met. N2's estimate is
  slightly negative, and the test had little power.

**How the run was done:**
- Everything was fixed in [`PREREGISTRATION.md`](PREREGISTRATION.md) before any N2 measurement,
  after several rounds of review by Astra 6 and Fable 5.1 (D050-D055).
  - **What that rests on:** local commit records and the run's provenance. The pre-registration
    was first pushed to GitHub on 2026-09-27, after the run (D062, D063).
- N2 and its variants were measured last.
- One deviation occurred (D056): the first run stopped on a faulty hash check, and every graph
  was re-measured from zero. No N2 data existed at that point.
- Both reviewers then reviewed these results (D058). Their corrections are included.

**Run facts:**
- **Scale:** 645 graphs, 19.75 GPU-hours (cap 24), one GPU, binding commit `132acae`.
- **Data:**
  - the measurements are in `runs/exp03/measures/` (local, git-ignored, about 640 MB);
  - the registered report is [`report.json`](report.json), from `scripts/exp03.py report`;
  - the exploratory per-graph quantities are in [`supplement.json`](supplement.json), from
    [`supplement.py`](supplement.py).
- **Validity:** every signal had all 128 graphs valid in every ensemble, and no calibration
  failed. N2 was valid on all three primaries.

Sections are marked **registered** (the verdicts of §6 and the values §5 lists) or
**exploratory** (§11: anything beyond those values and ranks).

---

## Registered verdicts (§6)

**What was measured.** Each per-graph value is a mean over unselected random genomes, measured
the same way for every graph.

**How the verdict is computed:**
- **Per ensemble:** a one-sided rank p, (r + 1)/129, where r is the number of the ensemble's 128
  graphs at or above N2.
  - It would be exact if N2 were exchangeable with the ensemble's graphs.
  - The finite swap chains and greedy weight repair approximate that exchangeability but do not
    establish it (§2), so these are approximate reference-ensemble tests.
- **Per signal:** the maximum p over the five ensembles. Claiming "distinctive relative to every
  ensemble" requires every ensemble to reject (an intersection-union test), so no fivefold
  correction is needed.
- **Across signals:** Holm across the three signals.
- **The opposite direction** is a separate family of three tests. Together the two directions
  allow up to 10% combined error.
- **Effect interval:** the 90% joint bootstrap of N2 minus the ensemble mean. "Distinctive" also
  requires it to lie beyond a margin of 0.5 of the ensemble's latent between-graph SD.
- **Consistent:** N2's whole 90% interval lies inside the ensemble's central 90%.
- **Inconclusive:** anything else.

**What the ensembles control for.** All five keep N2's degree sequence and move both wiring and
weight placement:
- **SH:** adds nothing else;
- **SH-route:** caps direct food read-out edges;
- **SH-class:** keeps class profiles;
- **SH-mirror:** keeps the mirror-symmetric share plus the routing cap;
- **SH-recip:** keeps reciprocal pairs.

A rejection therefore says N2 differs from these rewirings-with-moved-weights. It does not isolate
wiring from weights. Combinations not tested include class structure together with reciprocity.

### P4, history dependence: distinctive relative to every ensemble

N2 = **0.931** (SE 0.006, 90% interval 0.921-0.941). The maximum p over the ensembles is 0.0155;
the Holm-adjusted p is **0.0465**.

| ensemble | mean | central 90% | graphs ≥ N2 | p | N2 − mean [90%] | margin | z | verdict |
|---|---|---|---|---|---|---|---|---|
| SH | 0.747 | 0.604-0.853 | 0 | 0.008 | +0.170 to +0.198 | 0.036 | 2.6 | distinctive |
| SH-route | 0.843 | 0.786-0.904 | 1 | 0.016 | +0.077 to +0.099 | 0.018 | 2.5 | distinctive |
| SH-class | 0.825 | 0.735-0.886 | 0 | 0.008 | +0.094 to +0.118 | 0.024 | 2.2 | distinctive |
| SH-mirror | 0.840 | 0.782-0.897 | 0 | 0.008 | +0.081 to +0.103 | 0.018 | 2.5 | distinctive |
| SH-recip | 0.758 | 0.642-0.867 | 0 | 0.008 | +0.158 to +0.190 | 0.037 | 2.4 | distinctive |

(z is N2's distance from the ensemble mean in latent SDs.)

**What is and is not borderline:**
- **The margins were never binding.** Every effect interval's lower end (0.077-0.170) is far above
  its margin (0.018-0.037), and would be above the pilot's margin (0.037) too. The latent SD
  estimates set the margins and the quoted z values, but they could not have changed a verdict.
- **The rank gate is borderline.**
  - The attainable Holm-adjusted p values here are 3 × 1/129 = 0.023, 3 × 2/129 = 0.047 and
    3 × 3/129 = 0.070.
  - The result is on the middle one, because of the one SH-route graph above N2.
  - One more SH-route graph at or above N2, or two in any other ensemble, would have given
    0.070.
  - Equally, a replication that missed 0.05 by one graph would not by itself refute the
    difference.
- **Modest registered power:** at N2's z of 2.2-2.6, the registered power was 0.002 at z = 2 and
  0.33 at z = 2.5 (§7).

**Why the result passed at that power is not established.** That table simulated Gaussian
ensembles with SH's pilot parameters. The observed P4 distributions are not Gaussian: they are
left-skewed, with compressed upper tails.
- The ensembles' maxima lie only 1.7-2.5 latent SDs above their means.
- SH-class has skew −1.75, and its lowest graph is 4.7 SDs below its mean.
- Tails like these make an N2 at this z more likely to top all 128 graphs than the Gaussian table
  implies. The rank test itself stays valid whatever the shape, under the exchangeability
  assumption.
- Sampling variation is also a possible reason.

### P1, directional selectivity: not distinctive

N2 = +0.004 (SE 0.0205, 90% interval −0.030 to +0.038). Holm-adjusted p = 0.93.

| | SH | SH-route | SH-class | SH-mirror | SH-recip |
|---|---|---|---|---|---|
| graphs ≥ N2 | 59 | 47 | 59 | 50 | 59 |
| central 90% | −0.051 to +0.078 | −0.025 to +0.028 | −0.021 to +0.026 | −0.025 to +0.023 | −0.056 to +0.061 |
| verdict | consistent | inconclusive | inconclusive | inconclusive | consistent |

- **Consistent** needs N2's whole interval inside the ensemble's central 90%. That holds for SH
  and SH-recip.
- **Inconclusive:** in the three narrower ensembles, N2's point estimate is inside their range but
  its interval is not.
- **Against the prediction from 02:** before the run, §7 noted that 02's value would have put N2
  at about z = 3. The observed z is at most 0.8.

### P3, food-information dependence: registered criterion not met

N2 = −0.010 (SE 0.014), against ensemble means of +0.0006 to +0.0026. Holm-adjusted p = 0.94;
inconclusive against every ensemble.
- **The estimate is on the low side:** 114-120 of the 128 graphs in each ensemble are at or above
  N2.
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
| T0 at M0, top-decile mean | 1.69 | 1.51 (1.26-1.77) | 1.49-1.53 |
| coverage, task C (cells) | 115 | 115 (101-133) | 113-118 |
| absolute directional response, M0 | 0.0150 | 0.0029 (0.0016-0.0065) | 0.0020-0.0031 |
| common-mode turn response, M0 | 0.0296 | 0.0059 (0.0031-0.0130) | 0.0040-0.0062 |
| P4 decay: median per-genome share left 5 ticks later | 0.88 | 0.76 (0.67-0.83) | 0.77-0.82 |

- **P2:** every ensemble's mean-P2 95% t-interval includes zero. For SH it is −0.0006
  [−0.0033, +0.0022].
- **P1 in other conditions (N2):**

  | R1 | R2 | MS | gaps off | uniform magnitudes | permuted magnitudes |
  |---|---|---|---|---|---|
  | −0.057 | −0.016 | +0.013 | −0.089 | −0.072 | −0.060 |

  The ensemble quantiles are in `report.json`.

**The N2 variants** (descriptive only):
- **N2perm1-3:** N2's topology, with its weights permuted over its edges.
- **N2-rev:** N2 with every chemical synapse's direction reversed.

| | P1 | P3 | P4 |
|---|---|---|---|
| N2 | +0.004 | −0.010 | **0.931** |
| N2perm1 | +0.017 | −0.008 | 0.797 |
| N2perm2 | −0.005 | −0.014 | 0.919 |
| N2perm3 | −0.011 | −0.002 | 0.869 |
| N2-rev | invalid (common-mode denominator below 10⁻⁴) | −0.000 | 0.898 |

Graphs at or above each variant on P4 (r, of 128):

| | SH | SH-route | SH-class | SH-mirror | SH-recip |
|---|---|---|---|---|---|
| N2 | 0 | 1 | 0 | 0 | 0 |
| N2perm1 | 32 | 112 | 107 | 112 | 42 |
| N2perm2 | 0 | 1 | 0 | 0 | 0 |
| N2perm3 | 1 | 28 | 20 | 28 | 6 |
| N2-rev | 0 | 8 | 2 | 7 | 2 |

`report.json` gives these as (r + 1)/129. It stores N2-rev's invalid P1 as `NaN`, which strict
JSON readers reject; the validity flags mark it.

---

## Exploratory (§11; chosen after seeing the data)

Every per-graph number below is in [`supplement.json`](supplement.json).

### What P4's value is made of

P4 is a ratio: the history difference at the final tick, divided by the steady-state contrast
between the two starting levels (each held for 100 ticks). So a high P4 could come from a large
numerator or a small denominator.

| | numerator: mean \|rising − falling\| | denominator: mean \|steady contrast\| | mean common-mode turn (M0 response probe) |
|---|---|---|---|
| N2 | 0.120 | 0.129 | 0.030 |
| ensemble medians | 0.015-0.019 | 0.018-0.026 | 0.004-0.006 |
| largest single ensemble graph | 0.063 | 0.073 | 0.020 |
| N2-rev | 0.00036 | 0.00040 | 0.00009 |

- **N2's high P4 is not a small denominator.** Every magnitude of N2's is larger than any of the
  640 ensemble graphs': about 6-8 times the medians for the numerator, and 5-7 times for the
  denominator.
- **Two observations, under these probes:**
  1. N2's random brains give a much larger raw food-evoked read-out. 02 found this, and the
     registered common-mode secondary shows it.
  2. Normalised by that, more of the earlier level's difference remains.

**P4 has no ceiling at 1.** Nothing in the definition bounds the final difference by the starting
contrast. Within N2, the quarter of genomes with the smallest contrast has a ratio of means of
1.37. §7's statement that "P4 is a bounded ratio" is wrong (annotated there, D058).

**Calibration cannot enter P4 or these magnitudes.** The calibrated gains act only on the motor
outputs, after the raw read-out, and every quantity here is raw.
- **Gain-scaled:** scaled by each graph's own turn gain, N2's common mode is still larger. It is
  0.061, against ensemble medians of 0.012-0.018 and a largest single graph of 0.056. This is
  in the probe, not the world's drive, with motor clipping ignored.
- **Validation:** the independent calibration check on N2 and 8 graphs per ensemble was within
  7.4% of the target drive everywhere, and within 3% for N2. No tolerance was registered.

**Two checks on artefact readings:**
- **Saturation.** Saturation of the read-out under N2's stronger drive could inflate the ratio.
  Within N2, though, the per-genome ratio does not rise with the size of the steady contrast
  (correlation −0.04). The ratio of means in the upper three quarters of contrast is 0.92, 0.87
  and 0.94. This does not rule saturation out.
- **Another read-out.** On the raw *forward* read-out, the same ratio is 0.899 for N2. At most 2
  of 128 graphs in any ensemble are at or above that. So the pattern is not specific to the turn
  read-out.

**Responsiveness and normalised history partly separate among the variants:**
- N2perm1 is nearly as responsive as N2 (common mode 0.023) but has an ordinary P4.
- N2perm2 is about as responsive as a typical shuffle (0.006) but has a P4 above essentially every
  ensemble graph.
- N2-rev is left out of this argument. Its P4 is a ratio of two numbers near 4 × 10⁻⁴, which may
  be numerically fragile.

So a larger raw response does not by itself give a high P4, but three draws do not settle it.

**On wiring versus weights:**
- Two of the three weight permutations keep P4 high relative to SH. That suggests N2's wiring
  contributes.
- One drops to an ordinary value, so where the weights sit matters too.
- These are single draws, and the reversal changes the directed wiring. No causal feature is
  isolated.

**Readings the design cannot yet tell apart:**
- slow relaxation;
- hysteresis or multistability;
- nonlinear saturation;
- a steady-state contrast measured after a finite 100-tick warm-up rather than at verified
  equilibrium.

### Compared with 02b's evolved champions

02b found that selection made the champions' turn history-dependent. At generation 39 the
difference was a median 0.90-0.95 of the steady contrast, with 0.83-0.87 left five ticks later.
N2's unselected random brains here give a ratio of means of 0.93, and a median per-genome decay of
0.88.

This does not show that N2 is born where selection took the champions:
- the aggregations differ;
- 02b used each run's own stimulus bank, while 03 uses one common bank;
- the unselected shuffles here already sit at 0.75-0.84;
- 02b gave no normalised generation-0 figure. Its generation-0 gap (N2 0.095 against SH 0.030)
  is an absolute difference, which could reflect responsiveness.

### Readings from experiment 02 that do not extend to unselected random brains

1. **"On average N2's response points toward the stronger side"** (02 RESULTS, generation-0
   input response).
   - 02: a signed raw response of +0.0029, from 256 random genomes, with no uncertainty saved.
   - 03: +0.0001, from 2 048 genomes on an independent seed. N2's P1 is in the middle of every
     ensemble.
   - The absolute directional response agrees (0.0146 in 02, 0.0150 here). Sampling variation in
     02 is a plausible explanation.
2. **"The shuffles start worse under the biological mapping"** (02, D042) was about best-of-32
   generation-0 *champions*.
   - 03 measures unselected population means. There, every ensemble's mean mapping preference is
     indistinguishable from zero.
   - This blocks generalising 02's champion result to average random brains. It does not overturn
     that result.

What 02 and 03 agree on at generation 0: **N2's random brains give a much larger raw food-evoked
read-out than shuffles do.** Here the common mode is 5-7 times the ensemble medians, and above
every ensemble graph.

---

## What this decides (§10)

**P4, distinctive relative to every ensemble.** Under this probe, N2 has unusually high
normalised history dependence at generation 0, relative to all five reference ensembles. One
SH-route graph, SH-route-20078, is above N2. The
verdict is borderline on the rank gate, and the null moves weights as well as wiring. It does not
establish a memory mechanism, or any advantage for the worm.

§10 names the mechanism as the next step. Before that, both reviewers recommend a replication
(D058):
- fresh ensemble draws, with 256 SH-route graphs because one graph decided this result;
- independent genome draws for N2 and the controls;
- separately pre-registered, with either outcome reported.

The reviewers differ on whether it must come before publishing:
- **Fable:** replicate before any public claim.
- **Astra:** an honestly qualified report of this completed experiment can be published first.

**What happened next.** The owner chose a full replication before merging into main (D059). 03r is
pre-registered in `experiments/03r-replication/` and running. These first-run results became
public on the `roadmap` branch while it ran (D063).

Further questions, not registered:
- Where does the persistence live? Silencing or deletion of candidate loops can test that.
- Does it survive with gap junctions removed?
- Does it hold for inputs other than food?

**P1 and P3: no N2-specific generation-0 signal was found.**
- For P1 the wider ensembles bracket N2.
- For P3 the test had little power, and N2's estimate is on the low side.
- Neither supports "N2 is specialised at birth for stereo steering or for food information".

**For the owner's question** (is the connectome shaped for worm-like tasks?):
- The one distinctive property is a general dynamical one, holding on to an earlier input level.
  It was measured with food input, but nothing shows it is food-specific or useful.
- The food-specific and stereo-specific signals show nothing distinctive.

**The five ensembles** are built, validated and hashed, and are now available to 03a and 04 as
controls.

## Deviations

- **D056:** the first run (commit `0ef9a3d`) stopped after 52 ensemble graphs on a faulty
  graph-hash check. The check was fixed, the 52 measurements were set aside
  (`runs/exp03/measures-aborted-0ef9a3d/`), and every graph was re-measured from zero, as §9
  requires.
- No other deviation. The report ran as registered, and no parameter was chosen after seeing the
  data.
- **Pre-registration annotation (D058):** §7's "P4 is a bounded ratio" was wrong. It affected
  only the discussion of the power table, not any rule.
