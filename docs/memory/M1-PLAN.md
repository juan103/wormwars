# M1: accounting, amplitude and the cheap kills — the plan

*Draft 8, 2026-10-20, after seven rounds of review (rounds 1 to 3: both "revise"; rounds 4 to 7: Fable "agree" with
small fixes, Astra "revise"; drafts 1 to 7 and the reviews are archived in [`docs/reviews/20261020-m1-plan/`](../reviews/20261020-m1-plan/)). Exploratory: nothing here is a
pre-registration. This plan fixes the definitions, panels and decision rules before the analyses run, as
[`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md) asks ("the definition of settling fixed in advance"; formulas "frozen before
validation"). Anything changed after seeing data is labelled as such in the results. CPU only.*

**Facts used in this draft, gathered without looking at any M1 result:**
- a full-size fresh panel (1024 genomes, every arm) took 250 s on this machine;
- N2's two-step in-neighbourhood of the turn read-out holds 207 of 302 neurons, its one-step neighbourhood 84;
- from 03mc's committed records (Fable), N2's mean start amplitude is 0.106, while 604 of the 640 null graphs are
  below 0.03 and none reaches 0.05. So at natural amplitudes N2's genomes sit in the pooled top strata, where the null
  graphs have few genomes, and A2 is expected to be thin there.

## What M1 must decide

- **D1, amplitude.** Does N2's lead in the share shrink to little when genomes are compared at matched amplitude across
  graphs? If so, the focus moves to the size of the response.
- **D2, alignment.** Does the change in alignment with the turn read-out account for most of N2's excess, rather than
  the persistence of the activity difference? If so, the focus moves from a store to read-out geometry.

Both are **accounting**, not mechanism (Astra): D1 cannot show that amplitude causes the lead, and D2 cannot exclude a
store. A rule that fires points the next step; it proves nothing by itself. **Each rule has three outcomes.** It fires,
or does not fire, only when its 90% interval lies wholly on one side of its threshold; otherwise it is
**inconclusive**, as it is when its conditions are not met. An inconclusive rule changes nothing until a targeted
replication (more graphs) resolves it.

M1 also hands M2 the settling cohort's contribution to the lead, runs the round-3 cheap kills, and runs M3's anatomy
predictors, frozen here.

## Definitions (fixed)

From 03mc ([`scripts/p4mc.py`](../../scripts/p4mc.py) lines 530-557, `REGISTERED`; `wormwars/exp03/twin.py`),
unchanged:
- **The history difference** of genome *i* at tick *t* of the follow-up: δy_i(t), the raw turn read-out of the rising
  history minus the falling one. a_i = |δy_i(0)|, its value at the ramp's end.
- **The share** at tick *t*: mean_i |δy_i(t)| / mean_i a_i over all genomes. The primary tick is 30; ticks 100 and 300
  are secondary. **A panel is valid** as 03mc's units are (`p4mc.py` `terms` and `share_ok`): its terms are finite,
  the mean absolute steady contrast (the two start levels' read-outs at the warm-up's end) is at least 10⁻⁴, and
  mean_i a_i is at least 10⁻⁴; and, for a fresh panel, at least 10 genomes are eligible, without which no eligible
  share exists. A fresh panel that is not valid is excluded from the reference and reported; if one of N2's panels is
  not valid, D1 and D2 are inconclusive. A non-finite state anywhere, in any run and any arm, stops the run (checked
  after every tick of the warm-up, the ramp and the follow-up). Any statistic that meets an undefined case (a zero
  denominator, no reference graph left) is reported as unavailable and its rule as inconclusive. Per-genome ratios
  with a zero denominator (a zero state difference in the gap and antisymmetry ratios) are left undefined, not set to
  zero; aggregates use the defined values and report how many were undefined. The separate grower draw gets the same
  validity check as a panel.
- **Eligible:** a_i ≥ 10⁻³. **The eligible share:** the same ratio over eligible genomes. D1, D2 and the kills use the
  eligible share throughout, so that a contrast and its baseline are on one population; the ineligible genomes'
  fractions of the numerator and denominator are reported beside it. **Per-genome retention:** r_i(t) = |δy_i(t)| / a_i.
- **Remaining:** eligible and |δy_i(300)| > 0.1 a_i. **Settled:** the largest range of the voltage, over both
  histories and every neuron, during ticks 291-300 of the follow-up, is below 10⁻⁴ (03mc's `_Range`). **The settling
  cohort** is the genomes that are settled *and* remaining; "settled" alone is never used for it.
- **Activity** a = tanh v. The raw turn read-out is cᵀa, with c = +1/4 on SMDDL, SMDDR, RMDDL, RMDDR and −1/4 on SMDVL,
  SMDVR, RMDVL, RMDVR (`wormwars/exp03/measures.py` lines 82-88). So, exactly, |δy(t)| = ‖c‖ ‖δa(t)‖ |cos θ(t)|, where
  θ is the angle between δa and c. **Zero cases:** when ‖δa_i(t)‖ = 0, cos θ_i(t) is taken as 0. The observed share and
  N do not depend on this convention, but A′ does (Astra): the genome's term in A′ is its starting norm times the
  current cosine. So the count of zero cases is reported, with A′ under the other convention (cos θ_i(t) taken as
  cos θ_i(0)) beside it.
- **The lead,** for any statistic X: X(N2) minus the median of X over the reference null graphs.
- **Uncertainty** on the fresh panels: a bootstrap over graphs (within each ensemble) combined with a bootstrap over
  genomes, the intervention arms of a genome always resampled together; 2000 resamples, 90% percentile intervals. The
  seed-7600 panels share their genome draws index by index (one seed, and every graph has the same 3,709 chemical
  edges), so each resample draws **one** set of genome indices for all of them, and an independent one for N2's
  seed-7700 panel (Astra). A ratio's resamples with a denominator at or below zero are counted as an integer; if more
  than 100 of the 2000, the rule using that ratio is inconclusive, and otherwise they are dropped and their number
  reported. On 03mc's arrays:
  N2's rank among the 128 graphs of each ensemble.

## A. Accounting on 03mc's arrays (seconds)

Inputs: `runs/p4mc/arrays/N2__long.npz` and the 640 `graph__<ensemble>-<id>__long.npz` (2048 genomes each, local), and
`experiments/03mc-p4-confirm/measurements.json`; the script first checks that the arrays reproduce 03mc's committed
shares and settling counts. For every quantity: N2's value, each ensemble's median and range, and N2's rank.

- **A1, the decomposition** on eligible genomes: eligible share = E[r] + Cov(a, r) / E[a], with the population
  covariance (exact). Overall, and within each amplitude stratum of A2.
- **A2, amplitude standardisation, per ensemble.** For each ensemble, the comparison set is N2 and that ensemble's
  128 graphs. **Strata:** the pooled eligible a_i of the comparison set, cut at the deciles, with the top decile cut
  again at the 95th and 99th percentiles: 12 strata. **Common support:** a stratum is used only if every graph of the
  comparison set has at least 10 genomes in it. **Standardised share** of a graph: Σ_k π_k E[|δy(30)| | k] /
  Σ_k π_k E[a | k] over the used strata, with π_k the comparison set's pooled proportions. **Baseline:** the eligible
  share restricted to the same used strata. Reported: the strata dropped, and their share of N2's eligible tick-30
  numerator and of its denominator; N2's genome count per stratum; and, per stratum, N2's E[a | k] beside the median
  graph's (balance). Per-stratum shares, N2 against the ensemble.
- **A3, overlap of contributors:** the fraction of the top 10% of eligible genomes by |δy(300)| that are also in the
  top 10% by |δy(30)|.
- **A4, trimming:** the share at tick 30 after removing each graph's top 2% and top 5% of genomes by |δy(30)|.
- **A5, the settling cohort's contribution:** C_g(t) = Σ_cohort |δy_i(t)| / Σ_eligible a_i, at ticks 30 and 300. Its
  part of N2's lead is taken from **pairwise contrasts, averaged** (Astra): over the 128 graphs G of an ensemble, the
  mean of C_N2(t) − C_G(t) against the mean of s_N2(t) − s_G(t), with s the eligible share. Means of contrasts add up,
  so the ratio is the cohort's fraction of the mean lead. The share with the cohort removed is reported as a
  description only. This is M1's estimate for M2.

## B. Fresh CPU panels

**Graphs.** N2, and **6 graphs per ensemble sampled at random from all 128** (30): one generator,
`numpy.random.default_rng(20261020)`, and per ensemble, in the order SH, SH-route, SH-class, SH-mirror, SH-recip, one
call `choice(128, 6, replace=False)` on that ensemble's graphs sorted by name (a string sort; the ids within an
ensemble have the same number of digits, so it is also the numeric order). Separately, **the selected graphs**: per
ensemble, the one with the highest 03mc tick-30 share and the one with the largest settling cohort (the next by
cohort size if they coincide); 10 in all. A selected graph may also be drawn at random; it is then simulated once and
counted in both roles. The reference null graphs for every summary and rule are the 30 random ones; the selected ones
are reported beside them, never pooled.

**Genomes.** 1024 per graph, `Genome.random` with seed 7600 (fresh; CPU genomes are not 03mc's CUDA genomes). N2 also
gets a second panel, seed 7700. With 1024 genomes N2 should have about 13 genomes in the settling cohort and most null
graphs none (03mc's rates), so B2 is a few-genome proxy; A5 carries M1's estimate (Fable).

**The probe** is 03mc's: a warm-up of 100 ticks at 0.25× or 1.75× the final food level, a 10-tick ramp, and a 300-tick
follow-up at the final level, with T1's 32 substeps, in `scripts/memory_m1/` (it reuses `scripts/memory_spikes/
spikes.py` for the graphs, genomes, input and read-out, not that file's summary). It records δy, δv and δa at ticks
0, 10, 30, 100 and 300, and the settling range. The interventions at the ramp's end run as extra row pairs in one batch
with a 30-tick follow-up; the intact pair runs again alone for 300 ticks. **Check:** the intact pair's tick-0 and
tick-30 differences are compared between the two runs, genome by genome. The two batches have different row
compositions, and T1 §3 claims no bitwise equality across compositions; an unstable genome can amplify a last-bit
difference (Fable). So the per-genome gaps are saved and summarised, and the run **stops for investigation** only if
more than 1% of genomes differ by more than 10⁻³ (the gaps are saved first). Neither outcome is read as establishing its cause (Astra). No share mixes the two runs: every arm, the erasures
included, is read against the batched intact arm's start and eligibility, and B1, B2 and the B4 ratios use the lone
run. The scripts run inside `wormwars.accounting` (rule 8).

- **B1, persistence against alignment (D2).** On eligible genomes, with s(t) the eligible share:
  - **N(t)** = Σ ‖c‖ ‖δa_i(t)‖ |cos θ_i(0)| / Σ a_i: the share if each genome's alignment stayed as at tick 0;
  - **A′(t)** = Σ ‖c‖ ‖δa_i(0)‖ |cos θ_i(t)| / Σ a_i: the share if each genome's activity norm stayed as at tick 0.

  Two exact splits of log s: log N + log(s/N), and log A′ + log(s/A′). Against the reference, with s_ref = the median
  s of the 30 random graphs and N_ref, A′_ref their medians, the **total contrast** is T = log(s_N2/s_ref) and the
  **alignment part** is P₁ = log(s_N2/N_N2) − log(s_ref/N_ref) under the first split and P₂ = log(A′_N2/A′_ref) under
  the second. If s, N or A′ is zero for N2 or for the reference, D2 is unavailable. Reported at ticks 30 and 100,
  overall and per ensemble, and on the top quartile of a; also the per-genome medians of the norm ratio and the
  alignment ratio, descriptively.
- **B2, settling on the fresh panels:** the cohort's size and C(30), as A5.
- **B3, the amplitude arm (D1).** At the ramp's end each pair is also continued with its difference scaled about the
  midpoint, v± ← m + k(v± − m), k ∈ {0.25, 0.5, 2} (k = 1 is the intact arm), on N2 (both panels) and the 30 random
  graphs, 30 ticks. **The pooled population** of a graph: the genomes eligible at **every** k (a ≥ 10⁻³ at k = 0.25
  included), each counted once per k, so the four arms have equal weight; the baseline, the standardisation, the
  bootstrap and the per-k numbers all use this population. Reported per k: the actual ‖δv(0)‖, ‖δa(0)‖ and a, and the
  share at tick 30 against that arm's own start; and the median within-genome ratio r(k = 2)/r(k = 0.5). **Strata:** the pooled deciles (top decile
  split at 95 and 99) of a over N2's two panels and the 30 graphs; **common support:** every one of these 32 panels has
  at least 10 distinct genomes with an observation in a used stratum (Fable, round 5: 10 observations could be 3
  genomes); π_k the pooled proportions of observations. **Coverage is judged per
  genome** (Fable, round 3): an N2 genome is covered if any of its four arms falls in a used stratum. At natural
  amplitude N2's genomes sit above most null observations, so its large arms may fall in strata that are dropped, but
  its small arms reach the nulls' range; what matters is that the genomes carrying N2's lead are represented at some
  matched amplitude. Reported per graph and stratum: the count, E[a | k], and the k composition (Fable: N2's members of a stratum will mostly be at small k, the
  nulls' at large k). Beside it, the same standardisation on ‖δa(0)‖ instead of a, because a mixes the size of the
  state difference with its alignment (Fable); D1 uses a.
- **B4, the cheap kills** (N2 and the 30 random graphs unless stated). Each uses the eligible share at tick 30, and
  "the lead" as defined above against the 30 random graphs. Each reads only on its own diagnostic: a failed kill
  rejects that test of the idea, not the idea (Astra).
  - **Complement erasure:** at the ramp's end, every neuron outside a set is set to its two rows' midpoint; the
    eligible share at tick 30 over the intact a. Two sets: batch 6's `top30_start` (the 30 neurons with the largest
    mean absolute difference at the ramp's end in N2, `batch6.py` line 74; result-defined, labelled so) and the anatomy
    core C3. Both contain the 8 read-out neurons. The erasure of each set itself runs beside it.
  - **The gap dissipation ratios:** the geometric one, δvᵀ L_G δv / δvᵀδv, with L_G the graph's gap Laplacian (the gap
    weights are the same for every genome of a graph); and the dynamical one, the gap term's contribution to the
    Euclidean relative decay rate, δvᵀ T⁻¹ L_G δv / δvᵀδv with T = diag(τ) (Astra). At ticks 0 and 30, as medians and
    a-weighted means. Fable's test, on the a-weighted means at tick 30: N2 below the null median under both: support;
    under one only: partial; under neither: no support for the gap-geometry idea's strong form in this test.
  - **The left-right antisymmetric share:** over the 99 mirror pairs, Σ (δv_L − δv_R)²/2 over Σ (δv_L² + δv_R²), at
    ticks 0 and 30; and the antisymmetric part's retention, ‖δv_anti(30)‖ / ‖δv_anti(0)‖, a-weighted, against the
    same for the paired neurons' whole difference. Fable's test: an a-weighted share under 10% at tick 30 and an
    antisymmetric retention in N2 no higher than the nulls' median: the bilateral idea finds no support here.
  - **The equal-tau control:** the same genomes with each genome's taus all set to its geometric mean. Intact and
    equal-tau shares are computed on one population per graph, the genomes eligible in both (Astra, round 4); the
    equal-tau probe has its own validity check, and the reference is the valid random graphs with at least 10 such
    genomes. The lead **survives** if the equal-tau lead is at least half the intact lead. This tests the taus' heterogeneity only, not
    every time-constant explanation (Astra). The tau-permutation arm is **dropped as a kill**: taus are drawn
    independently of the weights (`brain.py` lines 235-239), so permuting them draws from the same distribution and
    N2's lead would survive by construction (Fable). It runs on N2 and one graph per ensemble only as a per-genome
    diagnostic: the correlation of r_i(30) between intact and permuted genomes.
  - **Growers and the forecast** (Fable): the midpoint Jacobian at the ramp's end (batch 3's method), on 512 genomes,
    for N2 and one random graph per ensemble (6 panels); an independent draw of 512 genomes, seed 7602 (seed 7600 would
    share the panels' chemical signs, Fable). Reported: the fraction of eligible genomes whose linear state
    norm grows over 10 ticks with spectral radius below 1, **and their part of the tick-30 numerator** (a minority can
    carry the weighted signal, Astra); the same for output growers (r(30) > 1); and the Spearman between the forecast
    and the observed r(30) without the radius-above-1 genomes. The forecast is made tanh-consistent: the read-out
    vector is c ⊙ (1 − tanh²(m)), with m the midpoint at the ramp's end, and the forecast retention is
    |c_mᵀ J³⁰ δv(0)| / a. Fable's test, on N2: growers with radius below 1 under 2% of genomes *and* under 10% of the
    numerator: the transient-growth family finds no support in this one-direction, frozen-linearisation test.

## C. M3's anatomy predictors (minutes; frozen here)

For each of the 641 graphs, on the binary chemical adjacency without autapses (A[i, j] = 1 for an edge i → j); R is
the 8 turn read-out neurons, S the 6 food sensors (AWAL, AWAR, AWCL, AWCR, ASEL, ASER).
- **K.** Fable's fallback applies: N2's two-step in-neighbourhood of R holds 207 of 302 neurons, more than half, so K
  is **R with its one-step chemical in-neighbours** (84 neurons in N2), for every graph. The two-step versions are
  reported beside it, labelled secondary. |K| is reported per graph.
- **C1, local density** (Fable): edges inside K over |K|(|K| − 1). **C1′:** the same count over
  Σ_{i,j∈K, i≠j} k_out(i) k_in(j) / E (E the graph's edge count). C1′ is a reference for a fixed set under a stub
  model, not the exact expectation given how K was selected nor under the ensembles' constraints (Astra).
- **C2, write-read walks** (Fable): w = 1_Sᵀ(A + A²), r = (A + A²) 1_R, C2 = log Σ_j w_j r_j: walks from S through j
  into R of total length 2 to 4, where a length-3 walk is counted twice, once for each split.
- **C3, the anatomy core** (for B4's complement erasure): N2's K ranked by degree inside K (in plus out), the top 30,
  ties broken by name. Every read-out neuron's whole in-degree lies inside K, so the 8 are expected near the top: C3
  is in effect R plus its best-connected afferents (Fable). Its overlap with batch 7's hub set and with `top30_start`
  is reported.

Spearman correlations within each ensemble (128 graphs) between C1, C1′, C2, |K| and four outcomes from 03mc: the
tick-30 share, the upper quartile of r(30), the settling cohort's size, and the growth fraction (r(30) > 1). Reported on
all 128 and on the two halves by graph id (even and odd ids); the halves are a stability check, not validation. **Validation is
reserved:** any predictor revised after this is frozen and tested on freshly sampled graphs in M3. **No veto**
(roadmap, M3). **Inspection** (roadmap, M3): for the top 5 graphs of each ensemble by share and by cohort size, their
predictor values and the fraction of N2's chemical edges inside `top30_start` and inside C3 that each keeps.

## Decision rules (fixed)

- **D1** (on the eligible basis, the same strata for contrast and baseline):
  - f = (standardised share_N2 − median standardised share_ref) / (baseline share_N2 − median baseline share_ref).
  - **B3 decides.** It is the matched comparison: N2 at k = 0.25 and 0.5 reaches the nulls' amplitudes. f on each N2
    panel against the 30 random graphs, with its interval.
  - **Conditions on B3:** a baseline lead of at least 10% (N2's baseline share at least 1.1 times the reference
    median) on both panels; **coverage:** the covered genomes hold at least 75% of N2's intact-arm tick-30 numerator
    and of its intact-arm denominator (over the genomes eligible at every k), on both panels; **balance:** in every used stratum holding at least 10% of N2's numerator, N2's
    E[a | k] is within 25% of the reference median's (the 10% is of N2's whole pooled numerator, as in A2). Panels
    with fewer than 10 genomes eligible at every k take no part in B3. Otherwise D1 is inconclusive.
  - **Fires** ("most of the lead is accounted for by amplitude") if the interval of f lies wholly below 0.25 on both
    panels. **Does not fire** if it lies wholly above 0.25 on both. Otherwise inconclusive. Whether f exceeds 0.75 is
    reported, descriptively.
  - **A2 is a check, not a decider.** Per ensemble, with the same conditions (lead, coverage, balance) on N2; an
    ensemble failing them is "unsupported", as expected for most. If a supported ensemble's f lies on the other side
    of 0.25 from B3's reading, D1 becomes inconclusive.
- **D2** (at tick 30, eligible genomes, all 30 random graphs as the reference):
  - **Conditions:** T ≥ log 1.2 (N2's share at least 20% above the reference median) on both N2 panels, with T's
    interval above 0; s, N and A′ nonzero. Otherwise D2 is inconclusive.
  - **Fires** ("alignment accounts for most of the excess") if the intervals of P₁/T and of P₂/T both lie wholly above
    0.5, on both N2 panels. **Does not fire** if, on both panels, at least one of the two intervals lies wholly below
    0.5. Otherwise inconclusive. The per-ensemble values are descriptive.
  - D2 uses all eligible genomes, a-weighted, rather than only "the genomes that carry the signal": the a-weights
    already put the carriers first, and a cut would be a choice made per graph. The top quartile is reported beside it.
- **For M2:** A5's cohort fraction of the mean lead, per ensemble.
- **The kills' readings** (gap, antisymmetry, equal tau, growers) are coded as written in B4 (`summarise.py`), so they
  are tested like D1 and D2.
- Every other number is descriptive.

## Outputs and cost

Scripts in `scripts/memory_m1/` (a README beside them); outputs in `runs/memory-m1/` (JSON committed; per-genome arrays
and logs local); the results on `docs/memory/M1-RESULTS.md`, reviewed by Astra and Fable before they are committed as
findings. **Cost,** from the measured 250 s per full panel: 42 panels (N2 twice, 30 random, 10 selected), about
2.9 hours; the equal-tau arm about 1 hour; the tau-permutation diagnostic and six Jacobian panels about 40 minutes. In
all about 4.5 to 5 hours of CPU, all on this machine. No GPU.

## Amendment 1, 2026-10-20: D1's targeted replication (written after M1's results, before it runs)

*Added after M1's results ([`M1-RESULTS.md`](M1-RESULTS.md), D350); nothing above is changed. Exploratory, as M1.
Draft 3, after two rounds of review (round 1 both "revise", round 2 both "agree" with small fixes; archived in
[`docs/reviews/20261020-m1-amendment1/`](../reviews/20261020-m1-amendment1/)).
The plan says an inconclusive rule changes nothing until a targeted replication resolves it. D1 was inconclusive on
its coverage condition: with k ≥ 0.25, N2's genomes in B3's used strata (a below 0.087) held only 34% (seed 7600) and
41% (seed 7700) of N2's intact-arm tick-30 numerator, against 75%. Both reviewers asked for smaller k on N2 only, with
coverage against the original population and the vacuous balance condition addressed (M1-RESULTS, "What this
changes").*

**What runs.** N2's two panels only (seeds 7600 and 7700, 1024 genomes each, M1's probe unchanged). The arm batch at
the ramp's end holds M1's four amplitude arms (k = 1, 0.25, 0.5, 2) and four new ones, **k = 1/8, 1/16, 1/32 and
1/64**, each scaling the difference about the midpoint as in B3, followed for 30 ticks. The erasure arms and the lone
300-tick run are not repeated. The new k come from M1's arrays: in N2, the genomes needed for 99% of the numerator have a
up to 2.57 (seed 7600) and 1.96 (seed 7700), which k = 1/32 brings below 0.087. Octave steps put every large genome's
a(k) in the used range for at least one k, if a(k) is close to linear in k (at k = 0.25, N2's mean a is 0.29 of its
intact mean). The null graphs are not rerun: a smaller k there would push most null genomes, mean a 0.021, below the
eligibility floor and change their population (Fable).

**The check before use.** In the rerun, the four arms that M1 ran must reproduce M1's arrays genome by genome (a and
|δy(30)|): with M1's batch policy, the run stops if more than 1% of genomes differ by more than 10⁻³; the largest gap
is reported. The four original arms are then taken from M1's arrays, so the population and the observations M1
analysed are unchanged; the rerun supplies only the new arms.

**Fixed from M1, not recomputed:**
- **the population:** N2's genomes eligible at every original k (a ≥ 10⁻³ at k = 0.25, 0.5, 1 and 2), 919 and 926
  genomes. A new arm's observation enters only if its own a is at least 10⁻³. Below the floor it is dropped, never put
  in stratum 0, and the genome stays in the population;
- **the strata, the used strata and the weights π:** M1's (`summary.json`, `D1_B3_a`: `edges`, `used_strata` 0 to 9,
  `pi`; and `D1_B3_da` for the ‖δa(0)‖ basis). The null graphs' observations and per-stratum values are M1's;
- **the reference:** the 30 random graphs' panels from M1, with the same B3 population.

**Computed as in D1, with N2's new observations added:**
- N2's per-stratum E[|δy(30)| | k] and E[a | k] are over all its observations in that stratum, the old and the new
  arms together. N2's genome count per used stratum is reported; it can only rise;
- the standardised share, the baseline (N2's observations in the used strata, old and new arms) and f = (standardised
  share_N2 − median standardised share_ref) / (baseline share_N2 − median baseline share_ref), on each N2 panel;
- the interval: M1's bootstrap (2000 resamples; one set of genome indices shared by N2's seed-7600 panel and the null
  panels, an independent one for seed 7700; graphs resampled within ensembles), with a fresh generator,
  `default_rng(20261022)`. A genome's arms are resampled together, the new ones included.

**The conditions** (all on both panels):
- **lead:** N2's baseline share at least 1.1 times the reference median (as M1);
- **coverage, against the original population:** an N2 genome of the population is covered if any of its eight arms
  above the floor falls in a used stratum. The covered genomes must hold at least 75% of N2's intact-arm tick-30
  numerator and 75% of its intact-arm denominator, both over the whole population. **This now passes almost by
  construction** (Fable): with k = 1/64 and a(k) close to linear, any genome with a up to about 5.5 lands in a used
  stratum, and N2's largest are 2.57 and 1.96. It stays a condition, and is not guaranteed (Astra), but the reading
  then rests on what the small arms measure (below);
- **balance, replacing M1's.** M1's condition looked only at used strata holding at least 10% of N2's *whole* pooled
  numerator, most of which lay in dropped strata. No used stratum reached 10% (the largest held 4.3% and 5.2%), so it
  tested nothing (`check_b3_balance.json`). Now: in **every used stratum**, N2's E[a | k] must be within 25% of the
  reference median's. A gate on N2's pooled numerator would not match the standardisation, which weights the strata
  by π, nearly uniform (0.105 each, 0.053 for stratum 9): already in M1, seed 7600's stratum 4 held 3.7% of the
  pooled used numerator but 6.4% of the standardised one (Astra); a stratum's part of the standardised share is
  π times its mean numerator (and, in the denominator, π times its mean a), not its part of the pooled numerator
  (Fable, Astra, round 2). Every used stratum has at least 10 of N2's genomes by construction. Every stratum's
  ratio is reported, with the numerator-weighted mean imbalance. If D1 fails only on balance, the strata and the
  reason are named, since the rule is new to real data (Fable).

**The readings** (M1's rule, unchanged):
- **Fires:** f's interval lies wholly below 0.25 on both panels. Wording: "at matched amplitude across graphs, most of
  N2's tick-30 lead is accounted for by amplitude (accounting, not mechanism)".
- **Does not fire:** f's interval lies wholly above 0.25 on both panels. Wording: "amplitude does not account for most
  of N2's tick-30 lead; at matched amplitude more than a quarter of it remains". Whether f exceeds 0.75 is reported
  descriptively.
- **Otherwise inconclusive,** as it is when a condition fails. The A2 check cannot intervene: every ensemble was
  unsupported in M1, and A2 is not rerun.
- **What f is here** (Astra, Fable): the question is D1's, but the estimand moves. The new arms change N2's
  observation mixture and its baseline, and both f's numerator and its denominator will be dominated by shrunk arms.
  So f is the fraction of N2's lead *within the used strata* that survives standardisation, as in M1; it is not the
  fraction of the original intact lead removed. The standardised lead against M1's intact eligible lead is reported
  for both panels beside it.
- **If it is inconclusive again,** D1 stays open on this probe, and later reports keep saying so. No further
  replication is planned, M2 is not held for it, and an inconclusive result is not evidence against amplitude
  (Astra).

**What the small arms measure** (stated before the run):
- shrinking the difference to between 1/64 and 1/8 of its size about the midpoint probes N2's genomes close to their
  linearisation about the **moving midpoint trajectory**, which is not in general the frozen ramp-end Jacobian
  (Astra);
- where the midpoint expands (finding 2; M1's growers), a small difference can grow toward a basin, so a genome's
  retention at small k can exceed its retention at natural amplitude. The comparison is still the matched one D1 asks
  for, but at matched a, N2's observations come mostly from strongly shrunk arms and the nulls' from natural or
  enlarged ones;
- reported per stratum: the k composition. Reported for N2: the fraction of its used-strata numerator from each k;
  its share against each new arm's own start; the median within-genome ratios r(1/64)/r(1/32) and r(1/8)/r(1/4).
  These are **scale-sensitivity diagnostics**, not a validation of rounding: genuine nonlinear evolution can move
  them, and a median near 1 does not exclude errors in influential genomes (Astra). Neither gates the reading. A
  median outside [0.8, 1.25] annotates the reading as "N2's retention depends on scale at small k" (Fable). Float32
  rounding is not expected to matter: a genome at the floor still has per-neuron differences thousands of float32
  steps above resolution (Fable). A demonstrated numerical problem would suspend the reading pending a precision
  check (Astra);
- beside it, descriptive: the standardised lead against M1's intact eligible lead on each panel (0.444 and 0.443,
  against the reference median 0.275), and the same computation on the ‖δa(0)‖ basis.

**Checks that can fail** (in the script's tests, run first): with the new arms left out, the computation must
reproduce M1's point values (N2's standardised and baseline shares, the reference medians, f and the coverage, on
both bases and both panels) from M1's arrays; a new observation below the floor must not enter stratum 0; the new
balance rule must fail a constructed used stratum that is out of balance, however little of the numerator it holds;
coverage must be both zero and positive on constructed cases. The rerun's intact arm is the ramp-end state itself, not
the midpoint plus 1.0 times the difference, so that it adds no rounding (Fable).

**Script and cost:** `scripts/memory_m1/d1_small_k.py`, inside `wormwars.accounting`; output
`runs/memory-m1/d1_small_k.json` (committed), the new arms' arrays `runs/memory-m1/d1_small_k/*.npz` (local). Two
panels with 8 arm pairs for 30 ticks: a few minutes of CPU. This amendment, the script and its tests are reviewed,
committed and pushed before it runs.
