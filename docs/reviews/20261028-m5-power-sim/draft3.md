# M5's power calculation: the design, before the script

*Draft 3, 2026-10-28, after two rounds with Astra 6 and Fable 5.1 (round 1: Fable "revise, narrowly", Astra
"revise"; round 2: Fable "agree, with five corrections", no further design round needed, Astra "revise"; archived in
[`docs/reviews/20261028-m5-power-sim/`](../reviews/20261028-m5-power-sim/), with drafts 1 and 2). Every round-2 point
is taken here; the script's review round checks that they went in (Fable), and Astra sees this draft first. It settles the two questions the pilot left open (D371): the rule
that turns the host-variance range into one host count, and the audit's estimator and decision rule. It also fixes the
simulation's model, scenarios, grid, Monte Carlo rule and cost model. The power calculation is exploratory design
work; M5 itself is pre-registered later (rule 2). Every pilot number below is from
`runs/memory-m5-pilot/report.json`, its panel records and [`M5-PILOT-RESULTS.md`](M5-PILOT-RESULTS.md); both
reviewers recomputed the ones they relied on.*

**What round 1 changed** (details in each section):
- **The audit has a fixed size, with no trigger and no second tranche** (section 3). Both reviewers showed that under
  the scenario that sets H, the trigger fires almost always (99.8% at 30 hosts, Astra; Fable). Astra showed that the
  two-stage Clopper–Pearson bound then covers 93%, not 95%. Fable showed that a retroactive tranche needs stored
  tick-2000 states. A fixed audit, drawn as M4e draws it, avoids all three. Its size becomes part of the allocation.
- **The first tranche is M4e's: 40 random ids of the panel, drawn before classification,** and the audit is the
  first-pass fading genomes among them (both; draft 1 said "40 first-pass fading genomes").
- **The model's counts are coherent** (Astra): a multinomial first pass, then a first-to-final table, with host
  propensities for every class.
- **δ is calibrated on the whole protocol** (Astra), and both the protocol and the latent contrast are reported (Fable).
- **The host-variance scenarios keep each arm's host variance at the pilot's** and lower the arms' correlation
  (Fable).
- **Rule A is the default; rule C is evaluated against acceptance criteria fixed here** (Astra), with its mapping fixed
  now (Fable).
- The success event, the selection rule, the cost model and two sabotages are corrected.

**What round 2 changed:**
- **The host variance is fixed on the logit scale,** the same σ² in both arms, and the scenarios are defined at one
  stated rate (Astra: draft 2 mixed the logit and count scales; Fable: the ρ labels were at the wrong rates). Targets
  that cannot be reached are reported as such.
- **The success event requires all four readings:** raw, audit-adjusted, Rr-side unresolved, joint (both).
- **The envelope has a bound for the unbalanced case** (Astra).
- **Rule C is specified to the end:** its lookup's reference model, H_max found then confirmed once, interim invalid
  hosts, the cap in seconds at H_max (Fable: draft 2's cap failed C at its own test), the audit bound under C (Astra).
- **The candidate H uses the confirmation's Bonferroni level,** K is fixed, and the null tolerance is 0.0275 for A
  and B, 0.030 for C (Fable, Astra).
- The calibration check runs at the pilot's fitted rates, the reader gets a plain mode for M4e's test, and five
  record counts are corrected (both).

## What is already agreed (D369, D371)

- **Arms:** T (N2's C3 block) against Rr (`m4d.rewire(..., keep_recip=True)`), paired on the same genome panel and
  signs in each host-draw. Hosts are fresh graphs from 03's five ensembles, in equal numbers.
- **Protocol:** M4e's classifier and production composition: the first pass to 2000 ticks; the second pass to 22,000
  ticks on every genome not classified fading by the first pass, and on the audit's genomes (`m4e.classify_panel`).
  The 22,000-tick horizon is kept (the pilot's rule). The unresolved genomes are a class.
- **Primary:** per host, the share of all its genomes confirmed as separate states (codes 0 and 1) by that protocol,
  T minus Rr. Unresolved genomes count as not confirmed.
- **Criterion:** "raises" if the lower end of a two-sided 95% interval is above zero; a nominal 2.5% false "raises".
  Planning effect 0.002 at 80% power; power also at 0.001, 0.003 and 0.004, and 90% beside 80%. Not the pilot's
  +0.0016.
- **Secondaries:** the share not classified as fading, each arm's unresolved share, the resolved-only share, and an
  exclusion at 0.002 with a leave-one-host-out guard.
- **Unresolved genomes:** the calibrated adjustment at r's bound (0.0253) is the protocol sensitivity; Astra's envelope
  [c_T − c_Rr − u_Rr, c_T − c_Rr + u_T] is reported beside it as the logical bounds.
- **Audit:** sampled, not completed. The simulation carries a transition rate at the pooled per-arm upper bound
  (0.00131 per first-pass fading genome), never zero, plus arm-asymmetric and concentrated scenarios. *Round 1 of this
  design replaces D371's "with a second tranche" by a fixed size (section 3).*
- **Recorded in M5** (carried to its plan): batch membership, a hash of each genome's float32 hold at 2000 and 22,000
  ticks, a reference chain for each host's Rr block, the original-composition replay for adjudicating a discrepancy.

## 1. The reading the simulation applies

Per host h, with D draws of G genomes per arm: d_h = (S_T,h − S_Rr,h) / (D G), S the confirmed count over the host's
draws (first and second pass, audited genomes at their 22,000-tick class, as `merged_classes` does).

- **The estimate** is the ensemble-weighted mean m = Σ_e (1/5) m̄_e. With equal allocation it equals the plain mean.
  The target is the mean across the five ensembles, which are fixed strata (Astra).
- **The interval, balanced case** (every ensemble with H/5 hosts): the hull of
  - the **stratified host bootstrap**: H/5 hosts drawn with replacement within each ensemble, B = 2000, percentile,
    one fixed seed; and
  - the **plain-s² Student-t**: m ± t(0.975, H − 1) s/√H, s² the sample variance of all H contrasts. It includes any
    between-ensemble variance, so its variance estimate is conservative for the stratified target in expectation
    (Astra: not a finite-sample coverage theorem for sparse outcomes; the simulation measures coverage).
- **The interval, unbalanced case** (a host left out, or a host dropped for an invalid panel): the plain-s² t is not
  conservative there (Astra's example: strata of 1, 2, 2, 2, 2 with the variance in the singleton gives a third of the
  estimator's variance; Fable: with strata of 2, 3, 3, 3, 3 and the variance in the pair, 0.011V against a true
  0.020V). It is replaced by a **stratum-aware t**: SE² = Σ_e (1/5)² s_e²/n_e, s_e² the within-ensemble variance,
  Welch–Satterthwaite degrees of freedom, hulled with the stratified bootstrap. Every ensemble must keep at least 2
  hosts. Its coverage under unequal ensemble variances is checked by simulation. With 2 hosts in an ensemble its s_e²
  has one degree of freedom and the t can approach t(0.975, 1) = 12.7, so the guard below rarely passes under about
  30 hosts; the per-cell exclusion rate shows it (Fable). The full-sample and the leave-one-out hulls use different
  t's, as pre-specified here (Fable).
- **Fields:** "raises" (lower end above 0), "lowers" (upper end below 0), or "direction unresolved".
- **The exclusion** (secondary): "no effect of 0.002 or more, as a mean across these five ensembles" if the hull lies
  inside (−0.002, +0.002), and the unbalanced-case hull still does with each host left out in turn (weights 1/5). A
  leave-one-out check does not exclude an effect confined to a rare host type; the wording says so. The guard is
  computed only when the full-sample hull lies inside the band (Fable). If any ensemble has exactly 2 valid hosts,
  leaving one out would leave 1, so the exclusion is unavailable in that run (Astra).
- **The adjustments** (sections 3 and 1): the audit-adjusted counts S_a,h + τ̂_a F^un_a,h, and the unresolved
  sensitivity S_a,h + 0.0253 U_a,h in one arm at a time.
- **Unconditional success,** the event the 80% target concerns: an **unqualified "raises"**. It requires "raises" on
  all four: the raw counts; the audit-adjusted counts (both arms); the Rr-side unresolved sensitivity alone (D371: in
  each one-arm case); and the **jointly adjusted** counts (audit adjustment in both arms plus the Rr-side unresolved
  adjustment). Passing the parts does not imply passing the joint (Astra, round 1), and passing the joint does not
  imply passing the unresolved part alone, since T's audit adjustment can offset it (both, round 2). The run must
  also complete within its cap, with at least 2 valid hosts in every ensemble.
  - The adjustments' point estimates move the contrast in a known direction: the Rr-side unresolved adjustment and
    Rr's audit adjustment lower it, T's raise it. The interval is recomputed on the adjusted counts, so its width
    changes too, and an adjustment that raises the estimate need not preserve "raises" (Astra).
  - Every other branch stays in the denominator and is reported: raises qualified by the audit, by the unresolved
    sensitivity, or only jointly; direction unresolved; lowers; the exclusion; an incomplete run.
- **The envelope**, reported, not a criterion. It is the bootstrap on the lowest assignment (every unresolved genome
  counted against T) and on the highest, plus a scalable t bound (Astra, round 2 of the power design): for d_i in
  [d^lo_i, d^hi_i], s² ≤ Σ_i max{(d^lo_i − c)², (d^hi_i − c)²}/(n − 1) for any fixed c, so
  [m(d^lo) − t SE_max, m(d^hi) + t SE_max] contains every corner's t interval. c is the midpoint of m(d^lo) and
  m(d^hi). In the unbalanced case the bound is taken per ensemble: s_e² ≤ Σ_{i in e} max{(d^lo_i − c_e)²,
  (d^hi_i − c_e)²}/(n_e − 1), combined as Σ_e (1/5)² bound_e/n_e, with t(0.975, min_e(n_e − 1)), which is at least
  every corner's Welch t (Astra). Tests check containment against exhaustive enumeration for every H ≤ 12, against
  M4e's reader in the balanced case and against the unbalanced reader with strata such as 2, 3, 3, 3, 3 (Astra: a
  box with equal ends already shows the plain bound failing there, half-width 0.0023 against Welch's 0.0254). When the
  envelope crosses
  zero, M5's wording says the contrast in underlying separate states is unidentified (D371); the simulation reports
  how often. Surviving the adjustments does not identify that contrast either (Astra).

## 2. The model of an M5 run

Each simulated run draws H hosts (H/5 per ensemble), D draws per host, G genomes per draw, two arms per draw. Genomes
are not simulated one by one: each panel's counts are drawn coherently (Astra), which is exact for the reading, since
the reading uses only counts and the audit's sample sizes.

**The first pass, per arm, host and draw:** a multinomial over separate states (S1), unresolved (U1), persistent
oscillation (O1) and fading (F1), with probabilities

logit p^c_a,h,d = μ^c_a + u^c_h + w^c_a,h + v^c_h,d [Rr only] + effect terms (separate states only), for c in
{S, U, O},

and F1 = 1 − p^S − p^U − p^O the remainder (about 98.6%). A draw whose three small probabilities sum above 0.2 is
rejected and counted (none is expected at these rates; the count is reported).

- **u_h, the shared host propensity, and w_a,h, the arm-specific one** (Fable, Astra). For separate states, the
  **logit-scale** host variance σ² is fixed, the same in both arms, at the pilot's fit (about 0.49²: 0.487² from T's
  overdispersion and 0.493² from Rr's, both reviewers; the script fits it and reports the fit). The arms' correlation
  ρ splits it: Var(u) = ρσ², Var(w) = (1 − ρ)σ². The pilot's implied correlation is at its ceiling of 1. Holding the
  logit variance fixed does not hold each arm's count-scale variance at the pilot's (T's 15.1, Rr's 9.5): at equal
  rates the two arms' count-scale variances are equal (Astra). Draft 2 said otherwise.
- **The host-variance scenarios** (the contrast's host component, Var_h(p̄_T,h − p̄_Rr,h) at zero effect, per host,
  probability scale, on the **draw-averaged** probabilities, Astra), **defined at Rr's rate of 0.0058 in both arms**,
  each set by solving for ρ numerically (the reviewers' values, by quadrature, with Rr's draw term):
  - **the minimum attainable** (ρ = 1; with the draw term the residual is about 1.5e-12, not exactly 0, Astra): the
    pilot's moment estimate truncated, the central scenario (Fable);
  - **7.6e-6**, half of M4e's T − K (ρ about 0.61, Fable);
  - **1.52e-5**, M4e's T − K, the top of the core range (ρ about 0.17 to 0.18, both);
  - **3.0e-5**, above it (Astra). The ceiling at ρ = 0 is about 1.8e-5, so it takes ρ = 0 and σ² scaled up by about
    1.54 in both arms (Fable).
  - For each, the report gives the implied per-arm host variance on the count scale and the implied correlation of
    the observed counts, beside the pilot's 15.1, 9.5 and 0.70, so the distance from the pilot is visible (Fable).
  - **The realised host component under each effect spread** is reported too: under the proportional spread it rises
    from 1.52e-5 at δ = 0 to about 2.2e-5 at δ = 0.002 (Fable).
  - **The base-rate sensitivities are not crossed with every scenario** (Astra). At Rr's 0.0031 and 0.0090 they run at
    the central ρ = 1 and at the ρ that gives 1.52e-5 at 0.0058, and report the host component that ρ realises there
    (at 0.0031 the ceiling at ρ = 0 is about 5.2e-6, so neither 7.6e-6 nor 1.52e-5 is reachable; at 0.0090 a target
    of 3.0e-5 lies below the ceiling of about 4.3e-5, Astra). **A target a construction cannot reach is reported as
    unreachable and not run.**
  - **A sensitivity in draft 1's parametrisation:** ρ = 1 for the shared part, an added independent w raising both
    arms' variances, at 1.52e-5.
- **v_h,d, Rr's block draw:** normal on the logit scale, its SD fitted to the pilot's draw component (1.5e-6 per draw
  of 512). Scenarios at zero and at **4.6e-6**, M4e's T − K draw component, labelled as K's (Fable: D = 1 gives the
  draw part full weight). Because the link is nonlinear and only Rr has a draw term, u does not cancel exactly in the
  host contrast; the host variance above is computed after averaging over v, and the script checks the marginal means
  and the draw variance jointly (Astra).
- **T has no draw term.** T's block is N2's, fixed, and its genomes and signs are drawn per genome (`m4d.paired_genome`
  takes a sign array with one row per genome; both reviewers checked).
- **Unresolved and oscillation propensities** are host-persistent too, with u^U, u^O and w^U, w^O fitted from the
  pilot's first-pass per-host counts (first-pass unresolved: T 0 to 7 per panel, 42 in all; Rr 0 to 12, 60 in all;
  first-pass oscillation: T 30, Rr 24; both reviewers corrected draft 2, which gave merged ranges and Rr's merged 25).
  Their association with the separate-states propensity is zero in the base case, with a sensitivity at a
  correlation of +0.5 between u^U and u^S (Astra: independence is an assumption the pilot cannot test).
- **μ_a:** Rr's separate-states rate is the pilot's 0.0058 (central), with sensitivities at M4d's 0.0031 and a high
  0.0090.
- **Pairing:** given the panel probabilities, the arms' outcomes are independent across genomes. The pilot had 1
  genome of 10,240 confirmed in both arms against 0.4 expected. Negative dependence can enlarge the contrast's
  variance by at most 2 p_T p_Rr per genome, about 0.6% of the genome variance at the pilot's rates; positive
  dependence shrinks it. Stated, not claimed exact.

**The second pass:** every first-pass non-fading genome is continued, and its final class drawn from a
**first-to-final table** per arm, fitted from the pilot's T records (M4e's) and Rr records. First-pass separate states
stay separate (T 75 of 75, Rr 59 of 59). First-pass unresolved genomes became fading in 9 of 42 (T) and 12 of 60 (Rr),
oscillation in 0 and 1, and stayed unresolved otherwise. K had one first-pass unresolved genome confirmed as separate
states (Fable), so that path is kept at the rate pooled over T, K and Rr, 1 in 153 (42 + 51 + 60 first-pass
unresolved; draft 2's 1 in 139 used K's merged count, both).

**The audit's genomes:** A ids per panel drawn at random from the panel before classification (M4e's `audit_ids`,
A = 40 in M4e). The first-pass fading genomes among them are continued. Each first-pass fading genome carries a latent
transition flag, true with probability τ_a,h,d: continued to 22,000 ticks it would be confirmed as separate states. A
transition counts in the raw primary only if its genome is audited. The transition scenarios:
- **symmetric at the bound:** τ = 0.00131 in both arms, every host (the pilot plan's rule, "a transition rate at the
  pooled upper bound, never zero"); the H-setting scenario;
- **zero**, for reference, with its H reported beside the H-setting one so the owner sees what the conservative audit
  scenario costs (Fable);
- **Rr only** and **T only:** 0.00131 in one arm (Astra);
- **host-concentrated, per arm and both:** five times the bound in a random 20% of hosts (Astra: arm-specific too);
- **panel-concentrated:** five times the bound in a random 20% of panels.

**The effect, calibrated on the whole protocol** (Astra). δ is the expected raw protocol contrast: first-pass
confirmations, second-pass confirmations and audited transitions, averaged over hosts and draws. It is set by solving
numerically for the effect term, per scenario and per allocation (the audit size changes the audited transitions'
share), for δ in {0, 0.001, 0.002, 0.003, 0.004}. The report gives each scenario's protocol contrast and its latent
contrast (all transitions and all latent switches counted), so "0.002" is unambiguous (Fable). The spreads:
- **constant increment:** the same δ added to every host's baseline contrast, which is itself heterogeneous under the
  host-variance scenario (Astra: draft 1's "p_T = p_Rr + δ" contradicted a nonzero host component);
- **proportional** (Fable): one logit shift in T's separate-states propensity, so high-base-rate hosts gain more;
- **uniform:** each host's increment drawn uniformly on [0, 2δ];
- **sparse:** each host a responder with probability 0.2, its increment 5δ;
- **one ensemble:** the increment 5δ in one ensemble only;
- **± null with mean zero:** each host independently, with probability 1/2, gets +0.004 by raising T's propensity,
  or −0.004 by raising Rr's (Astra: independent assignments, not an exact half), so no probability is clipped and
  the expected mean contrast is zero (Astra: clipping a −0.004 at a 0.0031 baseline leaves a mean of +0.00045);
- **ensemble-heterogeneous null** (Fable): +0.004 in two ensembles, −0.004 in two (by raising Rr there), 0 in one.
  This measures the plain-s² t's conservatism and the stratified bootstrap's gain instead of asserting them.

**The latent scenarios** (protocol truth and latent truth kept apart). In the **control-enriched** scenario the
protocol contrast is +0.002 and the latent contrast zero, because Rr carries 0.002 of its genomes as latent switches
classified unresolved (its unresolved share rising from 0.0046 to 0.0066). The simulation reports how often M5 then
reads "raises" (a misleading reading of the latent contrast, not a type-I error of the protocol), how often the
unresolved sensitivity qualifies it, how often the **unresolved-share flag** fires (the hull of Rr's minus T's
per-host unresolved share lying above zero, Fable), and how often the envelope crosses zero. A T-enriched mirror is
reported too.

**Calibration check** (Fable, power-design round 1; a fitted-model check, not a sabotage, Astra): the model at the
central scenario and the pilot's design (ten hosts, D = 2, G = 512, A = 40), **at the pilot's fitted rates, T 0.0073
and Rr 0.0058** (a constant increment of 0.0015; Fable: at δ = 0 T's variance would be compared at the wrong mean),
is simulated 4000 times. With nine degrees of freedom the check is weak: a sample variance's central 95% spans 0.30 to
2.1 times its truth (Fable). The report
places in the simulated distributions: the pilot's per-host SD of T − Rr (0.00336), its hull half-width (0.0024),
each arm's per-host count variance (22.5, 15.4), their correlation (0.70, Fable), the unresolved shares and the
first-to-final counts. A value outside the central 95% is reported, and the model is revisited before any host count
is given.

## 3. The audit: estimator and decision rule

**Why a fixed size** (round 1). Draft 1's trigger and second tranche fail on three counts:
- Under the H-setting scenario the trigger almost always fires: with 40 ids per panel, P(no transition in either arm)
  is about exp(−2 × 0.00131 × 39 × H D), 0.5% at 25 hosts and two draws (Fable), so the second tranche is part of the
  plan's cost, not a contingency.
- The Clopper–Pearson bound computed after a data-dependent second tranche undercovers. At H = 30, D = 2 and Rr-only
  τ = 0.00131, it covers 93.1%, by exact binomial summation (Astra).
- A tranche run after the trigger reaches panels already classified, whose tick-2000 states M4e's records do not keep
  (Fable).

**The audit, as fixed here:**
- **Sampling:** A ids per panel and arm, drawn at random from the panel before classification by M4e's mechanism
  (`m4e.audit_ids`, its own seed family). The first-pass fading genomes among them are continued to 22,000 ticks in
  the panel's second pass, as in M4e. With A = 40 this is exactly M4e's audit (both reviewers: M4e drew 40 of 512, of
  which 783 of 800 in T and 786 of 800 in Rr were fading).
- **The size A is part of the allocation,** A in {40, 80, 160} per panel. A larger audit costs compute and buys a
  smaller hidden contribution and a less noisy adjustment. The cheapest qualifying allocation decides it (section 4).
- **The transitions:** a transition is an audited first-pass fading genome confirmed as separate states at 22,000
  ticks (M4e's predicate). Every other class change is recorded and reported. Nothing is triggered.
- **The estimator:** per arm, τ̂_a = (transitions) / (audited first-pass fading genomes), pooled over panels. A
  transition counts in the raw S (an audited genome's 22,000-tick class replaces its first-pass class in
  `merged_classes`, Fable checked), and the adjustment applies τ̂_a only to the unaudited first-pass fading genomes:
  S^adj_a,h = S_a,h + τ̂_a F^un_a,h. With no transition in an arm, its adjustment is zero. No double counting.
- **The pooled estimate and its weighting** (Astra, rounds 1 and 2). With A ids drawn from each panel's G, every
  genome has the same inclusion probability A/G, so a panel rich in fading genomes contributes more audited fading
  genomes, and the pooled denominator already weights by fading count. For a fixed panel, (G/A − 1) times its
  audited transitions is a design-unbiased estimate of its hidden transitions. Spreading the pooled rate over each
  host's unaudited fading genomes is still a common-rate assumption across hosts, so the adjustment is labelled as
  one, and the simulation checks how well it tracks the actual hidden contribution under the arm-specific, host- and
  panel-concentrated scenarios.
- **The primary stays raw** (the protocol's confirmations, as agreed). The audit-adjusted reading is a labelled
  qualifier, not a new estimand.
- **The bias limit,** reported beside the contrast (Fable, D371): with U_a the arm's one-sided 95% Clopper–Pearson
  bound from M5's own audit and f_a the arm's mean
  unaudited first-pass fading share, hidden transitions at a common rate could move the contrast by at most
  −U_Rr f_Rr to +U_T f_T. The bound pooled with the pilot's and M4e's audits of the same arm (T: 0 of 2283 so far;
  Rr: 0 of 2286) is reported beside M5's own, labelled as assuming a protocol-level rate. The per-arm bounds are not
  simultaneous for both arms (Astra).
  - *Its validity.* Under a fixed H the audit's size does not depend on its outcome, and the bound is valid for the
    common transition probability. Under rule C the final H depends on the interim contrasts, which include audited
    transitions, so the final audit's size is outcome-dependent (Astra). Under C the guaranteed bound is therefore
    stage 1's, fixed in size; the bound over both stages is reported beside it, and its coverage is measured by the
    simulation.
  - *What it bounds* (Astra): the common probability, and so the expected hidden contribution after multiplying by
    the unaudited share, not the realised hidden count. The simulation reports coverage of both, labelled.
- **Under Rr-only transitions at the bound,** the latent contrast is smaller than the protocol's by τ times Rr's
  unaudited fading share. That is about 0.0012 at A = 40 and about 0.0009 at A = 160 with G = 512 (Astra corrected
  draft 1's single 0.0012). The audit then qualifies many "raises", and should. These scenarios are reported as
  limits, not used to set H.
- **No risk-targeted stratum** (Astra: the recorded fields do not define a margin). M5 records the root diagnostics
  at every horizon, so a later study could define one.

## 4. The grid, the Monte Carlo rule and the answer

- **Grid:** H from 10 to 150 in steps of 5 (to 300 for δ = 0.001 and the scenario above the range); D in {1, 2};
  G in {512, 1024}; A in {40, 80, 160}. The base case: Rr at 0.0058, constant increment, Rr's draw at the pilot's
  fit, the audit symmetric at the bound.
- **Monte Carlo for power:** a coarse pass at R = 400 runs per cell, then R = 4000 in every cell within 0.1 of the
  target. Each run applies the whole reading with B = 2000 (the bootstrap means are a matrix product of the host
  contrasts with a fixed resample-count matrix per H).
- **K, fixed in advance** (both): 12 allocations (2 D × 2 G × 3 A) × 2 H values = 24 confirmations in the 80% family,
  plus C's two (its H_max and H_max + 5, section 5), so K = 26. The 90% column is its own family, K = 24.
- **The candidate** (Fable: so the confirmation is not set up to fail): for each allocation, the smallest H whose
  power's one-sided Clopper–Pearson lower bound at R = 4000 is at least 0.80 at the family's level, 1 − 0.05/K.
- **The confirmation, with the search accounted for** (Astra): one independent simulation, a fresh seed and
  R = 10,000, at the candidate H and at H + 5, for every allocation at once, each judged by the same lower bound at
  level 1 − 0.05/K. An allocation's selected H is the smaller of the two that passes. If neither passes, the
  allocation is reported as **not confirmed**, and nothing is searched further. The result is called **the smallest
  confirmed host count tested**, not the true minimum (Astra).
- **The answer for each allocation:** the fewest hosts and the cheapest confirmed allocation (Astra), with the range
  across the host-variance scenarios. At fixed genomes more hosts are never worse when the host component is positive
  (Fable), so D = 1, G = 512 is expected to be among the cheapest. The audit size trades against hosts.
- **What the audit's noise costs** (Fable). Under the symmetric scenario the latent and protocol contrasts are equal, so
  every audit qualification there is false, and the point-estimate adjustment's noise (its shift on the contrast has
  SD about 1.0e-3 at A = 40, H = 27, D = 2, against the contrast's SE near 7e-4) may drive A or H. Beside each
  allocation's selected H the report gives the H at τ = 0 and the raw-only H (the H at which raw "raises" alone
  reaches 80%). A reporting rule fixed here: if the unqualified H exceeds the raw-only H by more than a third, M5's
  pre-registration names the qualifier's noise as the reason when it fixes A.
- **The false "raises" rate,** with its own precision budget (Astra): every δ = 0 cell of a selected allocation is
  run at R = 40,000 (Monte Carlo SE about 0.0008 at 0.025). The acceptance threshold is fixed here: the one-sided 95%
  Clopper–Pearson upper bound of the false "raises" rate, for the **raw** "raises" and for the unqualified one, under
  every host-variance scenario and both nulls (± and ensemble-heterogeneous), must be at most **0.0275 for the fixed-H
  rules A and B**, whose hull is built to sit below 0.025 (Fable), and at most **0.030 for rule C**. These are
  exploratory tolerances of 10% and 20% relative inflation, not certificates of nominal control (Astra: at 0.030 a
  true 0.0275 passes about 91% of the time). The point estimate is reported beside every pass. A selected allocation
  that fails is reported as failing, and the reading is revisited before M5's plan.
- **Also reported per cell:** the probabilities of every reading; the envelope crossing zero; the exclusion at
  δ = 0 and at δ = ±0.002; the latent scenarios' rates; the adjustment's coverage of the hidden contribution.

## 5. The host count: rule A by default, rule C if it passes its tests

The pilot puts the contrast's host component at zero, weakly determined on ten hosts. M4e's T − K, a different
contrast, puts it at 1.52e-5. Orientation (normal approximation, D = 2, G = 512): about 23 to 27 hosts at the pilot's
spread, about 59 at M4e's. The rule is fixed before the script runs.

- **A (the default, Astra).** A fixed H, the selected H at a host component of 1.52e-5. It is robust within that
  scenario specification, not a demonstrated bound on the unknown variance (Astra).
- **B.** A fixed H at the central scenario (the pilot's), with the power at 1.52e-5 and 3.0e-5 beside it (about 50%
  by the normal approximation at 1.52e-5). Defensible only if the owner explicitly accepts that loss (Astra).
- **C (evaluated, Fable's preference).** An internal pilot inside M5, with its rule fixed now:
  - **Stage 1:** H1 hosts, balanced over the ensembles, H1 rule B's selected H.
  - **The interim:** after stage 1's panels finish (with their fixed audits, so nothing later changes their counts),
    a script computes s², the sample variance of stage 1's per-host raw contrasts, and writes s² and the resulting H
    only, never a mean, an interval or a per-host value. s² estimates the **total** per-host contrast variance at the
    chosen D, G and A (host, draw and genome together), which is what the t interval uses; the lookup is indexed by
    it, not by the host component (both).
  - **The mapping:** s² is inflated by the normal-theory one-sided 75% upper limit, s²_75 = s² (n − 1)/χ²(0.25, n − 1),
    n the valid stage-1 hosts (a multiplier of about 1.26 at 25 hosts, 1.23 at 30; Fable: a point estimate under-sizes
    about half the time at a scenario's edge). For these sparse counts it is a normal-reference inflation rule, not a
    demonstrated 75% limit; its adequacy comes from validating the whole procedure (Astra). The final H is the
    smallest H in a table, pre-computed by this script, whose fixed-H power at that total variance is at least 0.80,
    interpolated linearly in s² between the table's rows. It is rounded up to a multiple of 5 and clipped to
    [H1, H_max]. Below the table's range it gives H1, above it H_max.
  - **The lookup's reference model** (Astra: total variance does not determine unqualified power alone). Each
    allocation's table is computed under the base case (Rr at 0.0058, constant increment, δ = 0.002, Rr's draw at the
    pilot's fit, the audit symmetric at the bound, unresolved propensities independent), with the host component
    stepped along the ρ path of section 2 (and the σ² scaling beyond its ceiling) from the minimum attainable to
    4.5e-5. Each row is indexed by its expected total per-host raw contrast variance at δ = 0.002.
  - **H_max, found then confirmed once** (Astra). An exploration simulation, on its own seed, tries H_max from rule A's
    H upward in steps of 5, at most four steps, and takes the first at which the two-stage procedure's power at
    1.52e-5 reaches the candidate bound of section 4. That H_max is frozen, and then confirmed with section 4's one
    confirmation at H_max and H_max + 5 (in the 80% family). If neither passes, or no step reaches the bound, **C is
    reported as not confirmed**. Its power at 3.0e-5 is measured and reported, not assumed (Astra; draft 2 said "less
    than 80% by construction").
  - **Interim invalid hosts** (Astra): s² is computed on the valid stage-1 hosts (at least 2 per ensemble, or the
    interim is not done and C stops as incomplete), n in the inflation is their number, and an invalid host is not
    replaced.
  - **Stage 2** keeps the balance: H − H1 more hosts, a fifth per ensemble. The first hosts count in the final reading.
  - **The cap,** in CPU seconds, fixed before validation (Fable, Astra): 1.5 times the mean cost of a fixed-H run at
    H_max under the central scenario and base case. The same multiple applies to A and B, at their H, under the same
    reference scenario, and is frozen in seconds across every sensitivity (Astra: a cap recomputed per scenario would
    change the policy it evaluates). A lower cap for C would accept less than 80% at 1.52e-5, and would be stated as
    that decision (Fable: draft 2's cap, 1.5 times C's central cost, equalled H_max's mean cost, so about half the
    runs reaching H_max would have exceeded it).
  - *Why it is not simply valid:* the sample variance is independent of the mean only for normal data, and even then
    an internal pilot can bias the final variance estimate and inflate the type-I error (Astra, citing Coffey,
    Kairalla and Muller, 2007). Here the counts are sparse, and a heterogeneous true effect inflates s² and so H
    (Fable). The operator also sees how many transitions the audits found, which reveals nothing about the contrast's
    sign but is reported.
  - **C's acceptance criteria, fixed here** (Astra), in independent validation simulations of the two-stage procedure:
    the false "raises" bound of section 4 (raw and unqualified, at most 0.030 by its 95% upper bound at R = 40,000)
    under every host-variance scenario and both nulls; unconditional power confirmed at 0.80 under the 0, 7.6e-6 and
    1.52e-5 scenarios by section 4's rule; and the distribution of the final H, the frequency of reaching H_max, the
    incomplete-run probability, and the mean and 95th-percentile cost, all reported.
  - **Choosing between A and C:** if C passes and its expected cost under the central scenario is at least 20% below
    A's, with the same cost components in both (Astra), both go to the owner with C recommended; otherwise A is
    recommended. B is shown beside both. The owner chooses. (Fable expects C's mean H near 40 under the central
    scenario against A's 60 or more.)

## 6. Cost

- **Panel time and difficulty are coupled** (Astra: in the pilot, a panel's time correlates with its unresolved count
  at 0.75 in T and 0.84 in Rr). Each simulated panel's time is a per-arm regression on its simulated first-pass
  unresolved and non-fading counts, fitted to the pilot's 20 T and 20 Rr panels, plus a residual resampled by whole
  pilot host (both arms and draws together, so a slow host stays slow). Whole-host resampling of the raw times,
  without the coupling, is a sensitivity.
- **What scales with G, and what does not** (Astra). The first pass scales with G, the second pass with the non-fading
  count, the audit with A. The pilot's panel time includes its 40-id audit, about 39 continuations at 3.3 to 3.7 s
  each (both reviewers' figures from the phase timings), which is subtracted before the panel is scaled and added back
  at the allocation's A. Linear scaling to G = 1024 is a labelled assumption until benchmarked at that composition.
- **Fixed costs:** host sampling, the Rr blocks and their reference chains, and the verification, timed on M4e's hosts
  before the script runs and added per host. The pilot's 10,630 seconds outside its stages' recorded phases (12.6% of
  its compute) are an overhead sensitivity.
- **Reported:** mean, median and 95th-percentile CPU hours per allocation, and the probability of exceeding the cap
  (section 5: 1.5 times the mean cost at the rule's H, or at C's H_max, under the central scenario and base case,
  frozen in seconds). The probability of exceeding 1.25 times is reported beside it. The success event uses the frozen
  1.5 cap.
- **Orientation, before the script:** at the pilot's times a host costs about 1.17 CPU hours at D = 2, G = 512,
  A = 40 (Astra). Each further 40 audit ids add about 0.15 hours per host at D = 2 (four panels of about 39
  continuations at 3.5 s, two arms), so A = 160 adds about 0.48 (Astra). Rule A at 59 hosts is then about 69 to 97
  CPU hours, rule B at 27 hosts about 32 to 45, depending on A.
- **Invalid panels:** none in the pilot's 20 Rr panels or M4e's 160. Modelled at zero, with a sensitivity at 1% per
  panel; a host with an invalid panel leaves the reading (the unbalanced-case interval, its ensemble keeping its 1/5
  weight), and a run with fewer than 2 valid hosts in an ensemble is incomplete (Astra: requiring every panel valid
  would cap success at 30% at H = 30, D = 2 and 1% invalidity).

## 7. The script, its tests and its review

`scripts/memory_m5/m5_power.py`, writing `runs/memory-m5-power/power.json` and a short report. Pure numpy and scipy,
CPU, seeded. Tests (`tests/test_memory_m5_power.py`), each seen failing first; sabotages
(`scripts/memory_m5/sabotage_m5_power.py`) that break, one at a time:
- the pairing (arms drawn from different panels' probabilities);
- the stratification (a bootstrap resampling across ensembles; weights not 1/5 after a host leaves);
- the unbalanced-case t (the plain-s² t used after a deletion; both the singleton example and a permitted one,
  strata of 2, 3, 3, 3, 3 with the variance in the pair, must catch it, Astra);
- the success event (the Rr-side unresolved check dropped, leaving the joint; Astra's example must catch it);
- the unbalanced envelope (the pooled bound used with Welch intervals);
- the audit (an observed transition counted twice; the adjustment applied to audited genomes; audit ids drawn from
  fading genomes only);
- the coherence (independent class counts that can exceed G);
- the marginal calibration (δ applied on the logit scale without calibration; calibration on the first pass only);
- the denominator (incomplete runs dropped);
- the envelope bound (an invalid bound, Σ min in place of Σ max, which the containment test must catch; Astra: a badly
  placed centre only loosens a valid bound);
- the interim (s² computed from stage 2's hosts as well, or from each arm's rates instead of the contrasts; the mean
  written out; Astra: a common shift leaves s² unchanged, so it cannot be a sabotage).
Plus the checks: the false "raises" rate at δ = 0 with no host variance within Monte Carlo error of the hull's;
power monotone in δ; the envelope bound contains the exhaustive envelope for H ≤ 12; the calibrated δ recovered within
its Monte Carlo error. The reader has a **plain mode** (M4e's unstratified bootstrap over all hosts, as M4e's and the
pilot's readers resample, `m5_pilot_read.py`) that must reproduce M4e's published T − K interval from its records
(Astra reproduced it exactly in round 1). The stratified mode's point estimate and t interval must equal M4e's at
equal allocation; its percentile interval differs by construction (Fable).

Then one review round on the script and its output (both), which also checks that round 2's corrections went in;
the host count and cost to the owner; and M5's plan and pre-registration. When this design is committed, D371 gets a
dated annotation recording that its "with a second tranche" is replaced by a fixed audit (rule 2, Fable).

## Questions for the reviewers (round 3)

1. The variance scale (section 2): logit σ² fixed and equal in both arms, scenarios defined at 0.0058, unreachable
   targets reported and not run. Consistent now?
2. The success event's four readings and the unbalanced envelope (section 1).
3. Rule C to the end (section 5): the lookup's reference model, H_max found then confirmed once, interim invalid
   hosts, the cap, the audit bound under C.
4. The candidate at the Bonferroni level, K, and the null tolerances (section 4).

Verdict: agree (the script may be written) / revise.
