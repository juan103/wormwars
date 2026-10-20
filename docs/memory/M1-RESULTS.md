# M1: accounting, amplitude and the cheap kills — results

*Draft 3, 2026-10-20, after three rounds of review (Astra 6 and Fable 5.1: round 1 both "revise", round 2 both
"revise" on wording, round 3 Fable one record fixed and Astra "agree"; no reading changed; drafts 1 and 2 and the reviews are archived in [`docs/reviews/20261020-m1-results/`](../reviews/20261020-m1-results/)). Exploratory: the plan
([`M1-PLAN.md`](M1-PLAN.md), draft 8, agreed by both after eight rounds) fixed the definitions, panels and decision
rules before anything ran; nothing here is a pre-registration. Numbers come from `runs/memory-m1/` (`summary.json`,
`accounting.json`, `anatomy.json`, `tau.json`, `growers.json`, `panels/*.json`). Anything below that was not fixed in
the plan is marked **descriptive** or **after the data**.*

## The run

- Run on 2026-10-20, 07:24 to 11:15 UTC, on the CPU of the tested machine, in the order accounting, anatomy, panels,
  tau, growers, summarise (`runs/memory-m1/run_steps.txt`, a copy of the local
  `run.log`; every step exited 0). The panels ran at commit 954d220; tau and
  growers at f1a9df8, which changed no script (`git diff --stat 954d220 f1a9df8 -- scripts/` is empty). Compute is in
  `runs/memory-m1/compute-record.json`, a copy of the local `compute.json` (2.16 × 10⁹ neural updates, category probe).
- **Validity.** All 42 fresh panels are valid (`invalid_panels: []`): N2 on seeds 7600 and 7700, the 30 random graphs
  and the 10 selected ones. The batch-composition check: the largest per-genome gap between the batched and the lone
  intact runs is 6.3 × 10⁻⁷ (`batch_gap_max`), and no genome exceeds 10⁻³.
- **The reference** for every rule is the 30 random graphs (6 per ensemble). On the fresh panels N2's eligible share
  at tick 30 is 0.444 (seed 7600) and 0.443 (seed 7700), against a reference median of 0.275 (range 0.181 to 0.405;
  none at or above N2). So the lead replicates on fresh CPU genomes.

## The readings

| Rule | Reading | In one line |
|---|---|---|
| **D1, amplitude** | **inconclusive (conditions)** | B3's coverage condition fails (34% and 41% of N2's numerator covered, against 75%). Descriptively, every amplitude-matched comparison keeps most of the lead. *Updated 2026-10-20: the targeted replication (amendment 1) reads **does not fire**; see the end of this file.* |
| **D2, alignment** | **does not fire** | The alignment part of the excess is *negative* on both panels: persistence of the activity difference carries all of it. |
| Kill: gap dissipation | support (narrow; seed 7600) | N2 is below the null median under both ratios at tick 30, by small margins. On seed 7700 the same rule reads partial. |
| Kill: left-right antisymmetry | not rejected | The antisymmetric share is 0.47, far above 10%; but it is not distinctive of N2. |
| Kill: equal tau | **survives** | The equal-tau lead is 92% of the intact lead. |
| Kill: growers | **not rejected** | Under the frozen ramp-end Jacobian, 4.8% of N2's eligible genomes grow transiently with radius below 1, carrying 30% of the numerator. |
| For M2 | cohort fraction | The settling cohort carries 30–38% of the mean tick-30 lead and 66–68% of the tick-300 lead. |

### D1, amplitude

- **The rule's conditions are not met.** On the a-basis (D1's variable), B3's common support uses strata 0 to 9 (a up
  to 0.087). N2's genomes are large: even at k = 0.25 its largest genomes stay above that, so the covered genomes hold
  only 34% (seed 7600) and 41% (seed 7700) of N2's intact-arm numerator and 45% and 54% of its denominator. The other
  two conditions hold: the baseline lead ratio is 1.56 and 1.74 (at least 1.1 needed). **The balance condition was
  vacuous:** no used stratum held 10% of N2's pooled numerator (the largest held 4.3% and 5.2%; a check written
  after the data, `scripts/memory_m1/check_b3_balance.py`, output `runs/memory-m1/check_b3_balance.json`), so
  `balance_worst` is the default 0.
- **f itself,** reported though the rule cannot read it: 1.08 [0.96, 1.24] on seed 7600 and 1.23 [1.13, 1.34] on seed
  7700, with no bad resamples. Both intervals lie wholly above 0.25, and both point estimates above 0.75.
- **On ‖δa(0)‖ instead of a** (descriptive, as planned): the conditions are met (coverage 76% and 78% of the numerator,
  84% and 88% of the denominator; balance again vacuous, largest used stratum 6.2%), and f = 0.85 [0.70, 0.98] and
  0.92 [0.82, 1.02]. The first interval lies wholly below 1, so on this basis a small part of the lead is
  attributable to amplitude. *Annotated 2026-10-20 (amendment 1, D352): this comparison was not balanced. Its
  balance condition read 0 only because it was vacuous; under amendment 1's rule (every used stratum within 25%),
  N2's mean a on M1's own arms is 1.4 to 2.4 times the reference median's in every used ‖δa(0)‖ stratum (seed 7600;
  1.5 to 2.4 at seed 7700; `runs/memory-m1/check_da_balance.json`, from `scripts/memory_m1/check_da_balance.py`, a
  check written after the data). So the "small part attributable to amplitude" reading does not stand (Fable).*
- **A2, the check on 03mc's arrays:** every ensemble is "unsupported", as the plan expected (the used strata drop 90–92%
  of N2's numerator and 92–94% of its denominator). f = 1.09 to 1.13. Descriptively, N2's share is above the median graph's in
  every used stratum, by factors of 1.5 to 3.3 (`accounting.json`, `A2.*.N2_strata.stratum_share` against
  `ensembles.*.stratum_share_median`). In the dropped strata the ratio falls: 1.5 to 1.7 at
  the 90th to 95th percentile, 1.0 to 1.4 at the 95th to 99th, and 0.81 to 1.12 above the 99th, where N2 is *below* the median graph in four of five ensembles. That top
  stratum holds 79 to 83% of N2's numerator (by ensemble); but N2's genomes in it have a mean a of 0.30 against the median graph's 0.12
  to 0.16, so it is not matched, and it cuts both ways.
- **Within a genome, retention barely depends on the scale of the difference.** The median within-genome ratio
  r(k = 2)/r(k = 0.5) is 1.006 and 1.010 for N2 and 1.000 for the reference median. N2's share against each arm's own
  start is 0.48, 0.49, 0.44 and 0.43 at k = 0.25, 0.5, 1 and 2 (seed 7600), against 0.26, 0.26, 0.26 and 0.25 for the
  reference medians. So N2 at a quarter of its amplitude, where its mean a (0.039) is close to the nulls' intact
  0.021, keeps nearly twice the nulls' share.
- **Reading.** The rule is inconclusive, and by the plan an inconclusive rule changes nothing until a targeted
  replication. The plan's matched comparison cannot cover N2's largest genomes with k ≥ 0.25; a replication would need
  smaller k on N2 (Fable: a smaller k on every graph would push most null genomes, mean a 0.021, under the
  eligibility floor and change the population). Most of the lead survives every matched comparison that could be
  made (f at least 0.85, lower bounds at least 0.70), but the unmatched top stratum, where most of N2's signal lies,
  is not settled by them.

### D2, alignment

- **Conditions met:** T = 0.481 [0.379, 0.580] on seed 7600 and 0.479 [0.372, 0.582] on seed 7700 (a share 1.62 times
  the reference median; log 1.2 = 0.182 needed); s, N and A′ nonzero; no bad resamples.
- **P₁/T = −0.20 [−0.38, −0.05] and P₂/T = −0.20 [−0.40, −0.07]** on seed 7600; −0.15 [−0.32, −0.02] and −0.13
  [−0.34, −0.01] on seed 7700. Both intervals lie wholly below 0.5 on both panels: **does not fire.**
- **The alignment part is negative,** with intervals wholly below zero. In aggregate, the difference's alignment
  with the turn read-out improves over 30 ticks in N2 and in 27 of the 30 reference graphs, but less in N2 than in the
  reference median (A′, the share with the norm held at its start, is 1.06 against the reference median 1.17, range
  0.85 to 1.34; 24 of 30 at or above N2). N, the share with
  the alignment held at its start, is 0.412 against 0.231 (none at or above). So the persistence of the activity difference
  accounts for about 1.2 times the total excess, and alignment takes a fifth of it back. In the top quartile of a, A′
  is neutral (0.97 against 0.96) and N carries the excess (0.458 against 0.260).
- Per ensemble (descriptive), P₁/T ranges from −0.08 to −0.23 and P₂/T from −0.16 to −0.29.
- At tick 100 the same holds: N 0.163 against 0.021, A′ 0.90 against 1.19 (28 of 30 at or above N2).
- **Reading.** The focus stays on a store, or more exactly on the persistence of the activity difference. This is
  accounting, not mechanism: it does not show where the difference persists or why.

### The cheap kills

Each reads only on its own diagnostic; a failed kill rejects that test of the idea, not the idea.

- **Gap dissipation: "support", by narrow margins.** At tick 30, a-weighted: geometric ratio 0.191 against the null
  median 0.207 (26 of 30 at or above N2); dynamical ratio 0.0734 against 0.0761 (20 of 30 at or above). At tick 0 the
  dynamical ratio is higher in N2 (0.094 against 0.085; 6 of 30 at or above), so N2's difference moves within 30 ticks
  into directions that the gap layer damps a little less. The rule's reading is support; the effect is small beside
  graph-to-graph spread. **It does not replicate fully:** the rule is coded on seed 7600; applied to seed 7700 it
  reads partial (geometric 0.193, below the median; dynamical 0.0784, above the median 0.0761).
- **Left-right antisymmetry: not rejected, and not distinctive.** The antisymmetric share at tick 30 is 0.468 (0.486
  on seed 7700), far above the 10% that would reject the bilateral idea; but every null graph is at or above it (median
  0.493), and the antisymmetric part's retention (0.416 against 0.241) tracks the paired neurons' whole difference
  (0.405 against 0.227). Nothing here singles out the antisymmetric part.
- **Equal tau: the lead survives.** With each genome's taus set to their geometric mean, N2's share (paired eligible
  genomes) falls from 0.444 to 0.234, and the reference median from 0.271 to 0.075. The intact lead is 0.173 and the
  equal-tau lead 0.159 (92%); 1 of 30 graphs is at or above N2 under equal taus (SH-recip-2050008). So tau heterogeneity
  raises everyone's retention, the nulls' relatively more, but does not make the lead. The permutation diagnostic: the
  Spearman correlation of r_i(30) between intact and tau-permuted genomes is 0.33 in N2 and 0.30 to 0.43 in the five
  nulls, so the taus matter for *which* genomes retain, about equally in N2 and the nulls.
- **Growers: the transient-growth family is not rejected.** On 512 independent genomes (seed 7602), in N2: under the
  frozen midpoint Jacobian at the ramp's end (a linearisation, not the observed nonlinear trajectory), 4.8% of the
  eligible genomes have a linear state norm that grows over 10 ticks with spectral radius below 1, and they carry 29.5% of
  the tick-30 numerator (the kill needed under 2% and under 10%). In the five nulls (one per ensemble): 0 to 0.6% of
  genomes and 0 to 4.8% of the numerator. Radius above 1: 3.6% of N2's genomes, carrying 16% of the numerator, against
  0 to 0.4% in the nulls. The tanh-consistent forecast's Spearman with observed r(30) is 0.93 in N2 (0.95 without the
  radius-above-1 genomes) against 0.997 or more in every null: N2's retention is less linear. One null graph per
  ensemble is a small reference: these are higher in N2 than in the five sampled null graphs, a lead, not a
  measured enrichment. It does not contradict the earlier network-level spectra.
- **Complement erasure (descriptive; the sets are N2's neurons).** Keeping only `top30_start` (result-defined, from
  N2) leaves N2 at 0.392 of its intact a, against 0.103 for the reference median; keeping only the anatomy core C3
  leaves 0.299 against 0.082. Erasing `top30_start` itself leaves 0.116, below all 30 null graphs (median 0.202);
  erasing C3 leaves 0.232 against 0.214 (6 of 30 at or above). Caveat: the null graphs keep only 13 to 19% of N2's
  edges inside these sets (`anatomy.json`, `kept_median_all`), so the same neurons are not a core there. And the
  erasure is made once, at the ramp's end: the erased network stays connected and can regenerate differences, so
  preservation after erasure does not locate the store (Astra). What the numbers show is that when only N2's head-core
  neurons keep their difference, N2 keeps 0.392 (`top30_start`) or 0.299 (C3, defined from the anatomy alone) of its
  intact a, two thirds of its intact share in C3's case, against about 0.1 in the nulls. Whether the core holds the
  difference or only re-seeds it is M4's question, with controls matched for erased norm.

### Settling, and the handoff to M2

- **A5, on 03mc's arrays.** Averaged over each ensemble's 128 pairwise contrasts, the settling cohort carries a
  fraction **0.30 to 0.38** of the mean tick-30 lead (SH 0.31, SH-route 0.35, SH-class 0.35, SH-mirror 0.38, SH-recip
  0.30) and **0.66 to 0.68** of the mean tick-300 lead. Descriptively, N2's share at tick 30 without its 26
  cohort genomes is 0.399 (over all genomes, `share30_without_cohort`), still at the top (0 to 2 graphs at or above per ensemble).
- **B2, fresh panels:** N2 has 14 and 12 cohort genomes (C(30) = 0.081 and 0.060); the reference median is 0 (range 0
  to 5).
- **So settling is a minority of the tick-30 lead and most of the tick-300 lead.** The rest, about two thirds at
  tick 30, is whatever fails the settled-and-remaining criterion: graded slower fading is one candidate, not
  established (Astra). That is the M2 "split" question's prior.

## Part A: the accounting on 03mc's arrays, and a correction

On 03mc's arrays (2048 genomes per graph, `accounting.json`):

| Quantity (eligible genomes, tick 30) | N2 | Ensemble medians | Graphs at or above N2, per ensemble |
|---|---|---|---|
| eligible share | 0.435 | 0.248 to 0.285 | 0, 0, 2, 1, 2 |
| **mean per-genome retention E[r]** | **0.586** | 0.370 to 0.412 | **0 in every ensemble** |
| covariance term Cov(a, r)/E[a] | −0.152 | −0.111 to −0.128 | 97 to 127 |
| median per-genome retention | 0.245 | 0.205 to 0.235 | 17 to 46 (`runs/memory-spikes/check_mixture.txt`) |
| upper quartile of r | 0.558 | 0.403 to 0.448 | 0 to 3 |
| growth fraction r > 1 | 0.115 | 0.068 to 0.079 | 0 in every ensemble |
| share after trimming the top 2% by \|δy(30)\| (all genomes) | 0.341 | 0.230 to 0.261 | 0 to 3 |
| share after trimming the top 5% (all genomes) | 0.269 | 0.214 to 0.242 | 10 to 26 |
| overlap of top-10% contributors, ticks 300 and 30 | 0.538 | 0.296 to 0.332 | 0 to 3 |

- **The amplitude weighting does not create the lead.** The exact decomposition gives eligible share = E[r] +
  Cov(a, r)/E[a]. N2's unweighted mean retention is beyond every one of the 640 graphs, and the weighting *lowers*
  N2's share more than it lowers most graphs' (its covariance term is more negative).
- **Where the mean comes from.** Within amplitude strata, N2's mean retention is higher than the median graph's in
  every used stratum (the strata below the pooled 90th percentile). The lowest stratum (a ≈ 0.002) has a mean r of 2.5 in N2 against 1.2, the small differences that
  grow; in SH, strata 3 to 9 have 0.34 to 0.63 against 0.19 to 0.29 (the other ensembles are similar). The median genome is ordinary, the upper quartile of
  retention is extreme, and trimming the top 5% of contributors by |δy(30)| leaves N2 inside each ensemble's range (10
  to 26 graphs at or above). So the lead is not an artefact of weighting; it is present in every supported amplitude
  stratum, and the largest contributors carry much of it. Which genomes, ranked by retention, carry it has not been
  measured (Astra).
- **The high-share null graphs get there differently** (descriptive). Two of the graphs selected for the highest
  03mc share beat N2 on the fresh panels: SH-recip-2050039 (0.562) and SH-class-2030099 (0.544). On 03mc's arrays
  they have positive covariance terms (0.024, 0.143), mean retentions of 0.486 and 0.366, and large settling cohorts
  (126 and 68 genomes, C(30) = 0.25 and 0.34; without the cohort their all-genome shares fall to 0.357 and 0.260). On
  the fresh panels their cohorts are 64 and 34 genomes. On 03mc's arrays the cohort's contribution C(30) is about
  half and two thirds of their eligible shares (0.253 of 0.511, 0.341 of 0.509), against 0.14 of N2's (0.062 of
  0.435). Most of N2's tick-30 lead lies outside its settling cohort, and that remainder's dynamics are unclassified;
  these two graphs lean much more on settling.

**Correction to the memory roadmap's finding 1** (to be added to [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md) beside the
finding, dated, without removing it). Finding 1 says: *"The typical N2 brain is not shown to forget more slowly"*, and
*"What is extreme is the registered, amplitude-weighted share"*. The first sentence stands for the median genome. The
second is misleading: M1's exact decomposition shows that N2's unweighted mean per-genome retention is also extreme
(0.586; no graph of 640 reaches it), and that the amplitude weighting reduces N2's share. N2's retention is above
the median graph's in every amplitude stratum with common support, and its largest contributors carry much of the
lead. Finding 1's "amplitude-retention association is weaker in N2"
(a Pearson correlation of log a against r, −0.13 against −0.39 to −0.42) does not carry over to the exact covariance
term, which is more negative in N2 (−0.152 against medians of −0.111 to −0.128); the two measure different things.
Other statements in the memory roadmap that M1 overtakes get dated annotations beside them: finding 4's row on
transient growth (under the frozen ramp-end Jacobian, transient growers with radius below 1 are more common in N2
than in the five null graphs sampled); finding 4's tau row ("interactions, tau permutation and equal taus are
untested": equal taus and the permutation diagnostic have now run); and finding 5's rows on amplitude ("untested")
and on persistence against alignment (M1 has measured both).

**A correction to Claude's own message to the owner** (20 October, while M1 was running): Claude wrote that "the
average genome on N2 keeps 0.59 of its difference" and that the lead "comes from the upper half of genomes generally,
not from a handful of outliers". The 0.59 is the mean, which the small, growing differences inflate; the median is
ordinary. And trimming the top 5% of contributors brings N2 inside the ensembles' range, so "upper half generally"
overstated it. What M1 supports: the median genome is ordinary, the upper quartile of retention is extreme, the
retention is higher in every supported amplitude stratum, and the largest contributors carry much of the lead.
(Claude's next message said "roughly the top quarter of genomes", which also goes further than the files: no
measurement ranks the carriers by retention.)

## Part C: the anatomy predictors (frozen for M3)

- **N2 is extreme on local density.** With K = the read-out and its one-step in-neighbours, N2's |K| is 84, smaller
  than every null graph (medians 120 to 138), and its density C1 (0.118) and stub-normalised density C1′ (1.72) are
  above every null graph in every ensemble. C2, the write-read walks, is above every graph in four ensembles and at the
  78th percentile in SH-class.
- **Within ensembles they predict nothing much.** Spearman correlations with the tick-30 share, the upper quartile, the
  cohort size and the growth fraction are all between −0.19 and 0.21 on all 128 graphs, and change sign between halves
  in several cases. C2 has the most consistent sign (0.21 and 0.20 with the share in SH and SH-class, near zero
  elsewhere). Under the plan's "no veto" rule this rejects these predictors as within-ensemble predictors, not a
  structural handle: N2's density lies outside the nulls' range, so the within-ensemble variation does not test it.
- **C3,** the anatomy core (top 30 of K by internal degree): RIAL/R, RIML/R, RIBL/R, RICL/R, RIS, AIBL/R, the eight
  read-out neurons (SMDDL/R, SMDVL/R, RMDDL/R, RMDVL/R), RMDL/R, SMBDR, RMGL, RMHL, CEPDL/R, CEPVL/R, OLLR and SAAVR. It shares 18 neurons with `top30_start` and 5 with batch 7's hubs. The
  null graphs keep 13 to 19% of N2's chemical edges inside it.
- **Inspection** of each ensemble's top 5 graphs by share and by cohort: their predictor values sit near their
  ensemble's medians (C1 within 0.0101 of the median), and they keep 10 to 23% of N2's edges inside C3 or
  `top30_start`, against medians of 13 to 19% for all graphs.

## What this changes

Pointers, not proofs, and D1 is inconclusive:
- **D2 does not fire,** so the focus stays on persistence of the activity difference, not read-out geometry.
- **Most of the lead survives every amplitude match that could be made,** but the rule could not read. A targeted
  replication (smaller k on N2 only, with coverage reported against the original population and the vacuous balance
  addressed) is written as a dated amendment to the plan before it runs. Both reviewers agree M2's pilot need not wait
  for it; Astra would run it before M2's large census. Smaller k might repair coverage; it does not guarantee a
  reading.
- **Tau heterogeneity does not make the lead** (equal tau), and the bilateral idea finds nothing distinctive.
- **M2's pilot goes ahead as planned,** with two inputs: settling carries about a third of the tick-30 lead and two
  thirds of the tick-300 lead; and under the frozen Jacobian, transient growers with radius below 1 are more common in
  N2 than in the five null graphs sampled, so the census should classify them beside the settled genomes.
- **M3 and M4 have a head start:** when everything outside C3, defined from the anatomy alone, is erased, N2 keeps
  two thirds of its share and the nulls about a third of theirs; whether the core holds or re-seeds the difference is
  M4's question, with controls matched for erased norm.

## Not done, or limits

- D1's coverage condition was not met; the replication with smaller k is not run.
- The gap kill's support is on seed 7600 only; seed 7700 reads partial.
- The grower and permutation diagnostics use one null graph per ensemble.
- The complement erasures use N2's neuron sets in every graph; there are no per-graph cores.
- The selected graphs are reported beside the reference, never pooled; two of the ten beat N2 on fresh panels.
- Everything here is on one probe (a 10-tick ramp from 0.25 or 1.75 of the final food level).

## Amendment 1's result: D1's targeted replication (2026-10-20)

*Added after the replication ran, without changing the text above. The design is M1-PLAN's amendment 1, reviewed in
two rounds and committed and pushed before it ran (d025d7a, D351). Numbers from `runs/memory-m1/d1_small_k.json`
(compute in `d1_small_k-compute-record.json`, the run's console output in `d1_small_k_run.txt`).*

- **The run.** On 2026-10-20 at 14:33 UTC, at commit d025d7a: N2's two panels with M1's four amplitude arms and four
  new ones (k = 1/8, 1/16, 1/32, 1/64), 184 s of wall-clock time for the recorded section, exit 0. The rerun reproduced M1's arrays exactly for the old
  arms (largest gap 0; the batch had M1's row count).
- **D1 does not fire.** On D1's basis (a), the conditions are now met on both panels:
  - coverage 100% of N2's intact-arm numerator and denominator;
  - the baseline lead ratio 1.69 and 1.76;
  - balance: the worst used stratum is 9.5% (seed 7600) and 9.3% (seed 7700) from the reference median's E[a | k],
    in stratum 0; every other used stratum is within about 2.15%.

  f = **1.01 [0.96, 1.05]** on seed 7600 and **1.03 [0.98, 1.07]** on seed 7700, with no bad resamples. Both
  intervals lie wholly above 0.25, so D1 does not fire: **amplitude does not account for most of N2's tick-30 lead;
  at matched amplitude more than a quarter of it remains.** Both point estimates are above 0.75 (descriptive).
- **What f is here** (fixed in the amendment). f is the fraction of N2's lead *within the used strata* that survives
  standardisation, over a mixture of observations that the new arms changed. It is not the fraction of the original
  intact lead removed. Beside it, descriptively: N2's standardised lead is 0.175 and 0.195, against M1's intact
  eligible leads of 0.170 and 0.169 (ratios 1.03 and 1.15). The new arms supply 32% (seed 7600) and 25% (seed 7700)
  of N2's used-strata numerator, and the old arms the rest. They are most of N2's observations in the lowest strata
  (85% and 84% in stratum 0, 58% and 59% in stratum 2) and few in the highest (16% and 10% in stratum 9). So the
  result is carried mostly by M1's old-arm observations, and the new arms chiefly make coverage complete (Fable).
- **Scale sensitivity** (diagnostics, gating nothing). N2's median within-genome ratios r(1/64)/r(1/32) and
  r(1/8)/r(1/4) are 0.9999 and 0.9998 (seed 7600), 0.9999 and 0.9998 (seed 7700), inside the band [0.8, 1.25], so the
  reading carries no annotation. N2's share against each new arm's own start is 0.47, 0.53, 0.56 and 0.54 at
  k = 1/8 to 1/64 (seed 7600) and 0.56, 0.45, 0.44 and 0.46 (seed 7700), against its intact 0.444 and 0.443. As k
  falls, the population above the floor shrinks (849 to 385 genomes at seed 7600), so these shares are over different
  genomes.
- **On ‖δa(0)‖** (descriptive, as planned). The balance condition fails there, and badly: in the used ‖δa(0)‖
  strata, N2's mean a is 1.3 to 2.4 times the reference median's (worst 2.44, seed 7600). The imbalance predates the
  new arms: on M1's old arms alone it is 1.4 to 2.4 (Fable; annotated at M1's ‖δa(0)‖ reading above). In strata 1 to
  9, N2's mean ‖δa(0)‖ is within about 1.2% of the reference median's (`check_da_balance.json`), so there the higher a means that, over the
  mixture of scaled arms at matched norm, N2's activity difference at the follow-up's start is about twice as visible
  to the turn read-out. Stratum 0 is not norm-matched (N2's mean norm is 0.59 of the reference's), and the statement
  does not cover it (Astra). f = 1.01 and 1.02
  on that basis, with the conditions unmet; the standardised lead is 0.61 and 0.65 of the intact lead. M1's own
  ‖δa(0)‖ reading (f = 0.85 [0.70, 0.98] and 0.92 [0.82, 1.02], above) was on the old arms only.
- **Reading.** On the a basis and against the reference panel, D1 is resolved on this probe: matching amplitude
  across graphs, with every genome of the fixed B3 population (919 and 926 of 1024) represented at some matched
  amplitude, leaves N2's lead in place. This is accounting, not mechanism. The match is on a, with mismatched k:
  N2's matched observations in the low strata come mostly from strongly shrunk arms, and the nulls' from natural or
  enlarged ones. The two median small-k diagnostics trigger no annotation; the effect of mismatched k on the weighted
  comparison remains unquantified (Astra). The ‖δa(0)‖ imbalance is a separate, descriptive observation about the
  starting alignment of the difference with the read-out (a = ‖c‖ ‖δa‖ |cos θ|). D2 measured the change in alignment
  over the follow-up, not its starting level, so this is a separate quantity, and it does not establish an
  explanation of retention.

