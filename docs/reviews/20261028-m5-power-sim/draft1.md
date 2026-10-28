# M5's power calculation: the design, before the script

*Draft 1, 2026-10-28, for review by Astra 6 and Fable 5.1 before `scripts/memory_m5/m5_power.py` is written. It
settles the two questions the pilot left open (D371): the rule that turns the host-variance range into one host
count, and the audit's estimator and decision rule. It also fixes the simulation's model, scenarios, grid, Monte
Carlo rule and cost model. The power calculation is exploratory design work; M5 itself is pre-registered later
(rule 2). Every pilot number below is from `runs/memory-m5-pilot/report.json` and
[`M5-PILOT-RESULTS.md`](M5-PILOT-RESULTS.md).*

## What is already agreed (D369, D371)

- **Arms:** T (N2's C3 block) against Rr (`m4d.rewire(..., keep_recip=True)`), paired on the same genome panel and
  signs in each host-draw. Hosts are fresh graphs from 03's five ensembles, in equal numbers.
- **Protocol:** M4e's classifier and production composition: the first pass to 2000 ticks; the second pass to 22,000
  ticks on every genome not classified fading by the first pass, and on the audit's genomes. The 22,000-tick horizon
  is kept (the pilot's rule). The unresolved genomes are a class.
- **Primary:** per host, the share of all its genomes confirmed as separate states (codes 0 and 1) by that protocol,
  T minus Rr. Unresolved genomes count as not confirmed.
- **Criterion:** "raises" if the lower end of a two-sided 95% interval is above zero; a nominal 2.5% false "raises".
  Planning effect 0.002 at 80% power; power also at 0.001, 0.003, 0.004, and 90% beside 80%. Not the pilot's +0.0016.
- **Secondaries:** the share not classified as fading, each arm's unresolved share, the resolved-only share, and an
  exclusion at 0.002 with a leave-one-host-out guard.
- **Unresolved genomes:** the calibrated adjustment at r's bound (0.0253) is the protocol sensitivity, in each one-arm
  case; Astra's envelope [c_T − c_Rr − u_Rr, c_T − c_Rr + u_T] is reported beside it as the logical bounds.
- **Audit:** a sampled audit with a second tranche, not a completed one. The simulation carries a transition rate at
  the pooled per-arm upper bound (0.00131 per first-pass fading genome), never zero, plus arm-asymmetric and
  host-concentrated scenarios.
- **Recorded in M5** (carried to its plan, not part of this design): batch membership, a hash of each genome's float32
  hold at 2000 and 22,000 ticks, a reference chain for each host's Rr block, the original-composition replay for
  adjudicating a discrepancy.

## 1. The reading the simulation applies

Per host h, with D draws of G genomes per arm: d_h = (S_T,h − S_Rr,h) / (D G), S the confirmed count over the host's
draws.

- **The estimate** is the ensemble-weighted mean m = Σ_e (1/5) m̄_e, the mean of the five ensembles' host means. With
  equal allocation it equals the plain mean of the d_h. The target is this mean across the five ensembles, which are
  fixed strata (Astra, round 1).
- **The interval** is the hull of two 95% intervals:
  - the **host bootstrap, stratified**: each resample draws H/5 hosts with replacement within each ensemble; B = 2000,
    percentile interval, one fixed seed;
  - a **Student-t** interval: m ± t(0.975, n − 1) × SE, with SE² = s² Σ_e (1/5)² / n_e, s² the plain sample variance
    of all n hosts' d_h about their mean, n_e the hosts in ensemble e. With equal allocation SE² = s²/H, M4e's t. The
    plain s² includes any between-ensemble variance, so the t is conservative for the stratified target (this answers
    Fable's round-2 question of which t).
- **Fields:** "raises" (lower end above 0), "lowers" (upper end below 0), or "direction unresolved".
- **The exclusion** (secondary): "no effect of 0.002 or more, as a mean across these five ensembles" if the hull lies
  inside (−0.002, +0.002), and still does with each host left out in turn. With a host left out, the weights stay 1/5
  per ensemble (Astra, round 2), the bootstrap resamples the remaining n_e hosts in each ensemble, and the t uses the
  same SE formula with n = H − 1. A leave-one-out check does not exclude an effect confined to a rare host type
  (Astra); the wording says so.
- **The audit qualifier** (section 3): the reading is recomputed on the audit-adjusted counts.
- **The unresolved sensitivity** (agreed form): the reading recomputed with S_Rr,h + 0.0253 U_Rr,h in place of S_Rr,h,
  and separately with S_T,h + 0.0253 U_T,h. Only the first can remove a "raises"; the second can remove a "lowers".
- **The envelope**, reported, not a criterion: the bootstrap on the lowest assignment (every unresolved genome counted
  against T, d^lo) and on the highest (d^hi), and a scalable conservative t bound (Astra, round 2): for a host vector
  with d_i in [d^lo_i, d^hi_i], s² ≤ Σ_i max{(d^lo_i − c)², (d^hi_i − c)²} / (n − 1) for any fixed c (the mean
  minimizes the sum of squares), so the t interval [m(d^lo) − t SE_max, m(d^hi) + t SE_max] contains every corner's.
  c is the midpoint of m(d^lo) and m(d^hi). A test checks containment against M4e's exhaustive 2^H enumeration for
  every H ≤ 12. The simulation reports how often the envelope crosses zero; when it does, M5's wording says the
  contrast in underlying separate states is unidentified (D371).
- **Unconditional success** (Astra, round 2), the event the 80% target concerns: an **unqualified "raises"**. That
  is: "raises" on the raw counts, and on the audit-adjusted counts, and at the Rr-side unresolved sensitivity, in a run
  that completed within its cap with every panel valid. Every other branch stays in the denominator and is reported
  separately: raises qualified by the audit, raises qualified by the unresolved sensitivity, direction unresolved,
  lowers, the exclusion, an incomplete run. The envelope crossing zero is reported, not part of success: its width
  (0.0078 at the pilot's shares) exceeds the planning effect at every H.

## 2. The model of an M5 run

Each simulated run draws H hosts (H/5 per ensemble), D draws per host, G genomes per draw, and two arms per draw.
Genomes are not simulated individually: each panel's class counts are drawn from its probabilities, which is exact
for the reading, since the reading uses only counts.

**The separate-states probability, per arm, host and draw:**

logit p_a,h,d = μ_a + u_h + w_a,h + v_h,d [Rr only] + effect terms.

- **u_h, the shared host base rate** (Fable): normal, SD σ_u, the same in both arms. In the pilot both arms are
  overdispersed across hosts: T's per-host counts over 1024 genomes have variance 22.5 against a binomial 7.4, Rr's
  15.4 against 5.9, and the two correlate across hosts at 0.70. After the binomial noise is removed, the implied
  correlation of the underlying host rates is at its ceiling of 1. σ_u is fitted to these two variances (about 0.5
  on the logit scale; the script fits it and reports the fit).
- **w_a,h, the arm × host interaction:** normal, independent between arms, SD σ_w. This is the part of the host
  effect the arms do not share, so it alone makes the contrast's host component. σ_w is set per scenario so that the
  contrast's host component on the probability scale, Var_h(p_T,h − p_Rr,h) at zero effect, equals the scenario's
  value (below), found numerically.
- **v_h,d, Rr's block draw:** normal, SD σ_v, fitted to the pilot's draw component (1.5e-6 per draw of 512), with a
  scenario at zero. T has no block draw, and its genomes and signs are drawn per genome, so T has no draw term
  (Astra, round 1; `m4d.paired_genome` takes a sign array with one row per genome).
- **μ_a:** Rr's marginal rate is the pilot's 0.0058 (central) and, as sensitivities, M4d's 0.0031 and a high 0.0090;
  T's follows from the effect.
- **Pairing:** given the panel probabilities, the two arms' outcomes are independent across genomes. The pilot had 1
  genome of 10,240 confirmed in both arms against 0.4 expected under independence. Positive dependence would shrink
  the contrast's variance, and negative dependence can enlarge it by at most 2 p_T p_Rr per genome, about 0.6% of
  the genome variance at the pilot's rates, so independence is conservative within that margin. Stated, not claimed
  exact (Astra, round 2).

**The other classes, per panel and arm:** unresolved and persistent oscillation counts are drawn from beta-binomials
fitted to the pilot's per-panel counts (T's unresolved 0 to 6 of 512, Rr's 0 to 10; oscillation T 30, Rr 25 in
total), independently of the separate-states count. The rest of the panel is fading. They feed the secondaries, the
unresolved sensitivity and the envelope.

**The first pass and the audit.** The pilot's separate states were all first-pass confirmations (75 of 75 in T, 59 of
59 in Rr), so separate states are drawn at the first pass. The first-pass fading genomes are 98.6% of a panel. Each
carries a latent transition flag, true with probability τ_a,h: continued to 22,000 ticks it would be confirmed as
separate states. A transition counts in the raw primary only if its genome is audited (section 3). The scenarios:
- **symmetric at the bound:** τ = 0.00131 in both arms, every host (the pilot plan's registered rule, "a transition
  rate at the pooled upper bound, never zero");
- **zero:** τ = 0, for reference;
- **Rr only** and **T only:** 0.00131 in one arm, 0 in the other (Astra: transitions concentrated in either arm);
- **host-concentrated:** τ = 0.00655 (five times the bound) in a random 20% of hosts, both arms.

**The effect** is set on the marginal probability scale of the estimand (Astra, round 1): the mean over hosts of
p_T − p_Rr equals δ, by numerical calibration, for δ in {0, 0.001, 0.002, 0.003, 0.004}. Its spread across hosts:
- **constant:** p_T,h = p_Rr,h + δ in every host;
- **proportional** (Fable): a logit shift in T, the same in every host, so high-base-rate hosts gain more and the
  interaction is nonzero under a true effect;
- **uniform:** each host's δ_h drawn uniformly on [0, 2δ];
- **sparse:** each host a responder with probability 0.2, its effect 5δ (Astra: random, not one in every five);
- **one ensemble:** the whole effect in one ensemble, 5δ there;
- **± effects with mean zero:** δ_h = +0.004 or −0.004 with equal probability, a null in the mean with extra host
  variance (type-I check).

**The host variance scenarios** (the contrast's host component, Var_h at zero effect, per host, probability scale):
- **0**, the pilot's moment estimate truncated (the central scenario, Fable: the same control on the same protocol);
- **7.6e-6**, half of M4e's T − K;
- **1.52e-5**, M4e's T − K, the top of the core range;
- **3.0e-5**, above it (Astra: a scenario above the range; near the pilot's plug-in upper limit for the host means'
  variance, 3.05e-5, which the results note calls a rough calculation).
M4d's T − R and T − Rr host-and-draw residuals (first pass only, labelled so) lie inside this range.

**The latent scenarios** (Astra, round 2: protocol truth and latent truth kept apart). The protocol contrast is what
the primary estimates; the latent contrast counts every genome that would be confirmed given unlimited time. In the
**control-enriched** scenario the protocol contrast is +0.002 and the latent contrast zero, because Rr carries 0.002
of its genomes as latent switches classified unresolved (raising its unresolved share from 0.0046 to 0.0066). The
simulation reports how often M5 then reads "raises" (a misleading reading of the latent contrast, not a type-I error
of the protocol), how often the unresolved sensitivity or the unresolved-share secondary flags it, and how often the
envelope crosses zero. A T-enriched mirror is reported too.

**Calibration check** (Fable, round 1; not a sabotage, Astra): the model at the central scenario and the pilot's
design (ten hosts, D = 2, G = 512, δ = 0) is simulated 4000 times. The report gives where the pilot's observed
per-host SD of T − Rr (0.00336), its hull half-width (0.0024), each arm's per-host count variance and the unresolved
shares fall in the simulated distributions. A value outside the central 95% is reported and the model revisited
before any host count is given.

## 3. The audit: estimator and decision rule

Astra's list (D371), answered in order.

- **The trigger:** an audited first-pass fading genome confirmed as separate states at 22,000 ticks (M4e's predicate).
  Every other class change is recorded and reported, and does not trigger. The trigger is evaluated per arm and acts
  on **both** arms: a transition in either arm's first tranche starts the second tranche in both (symmetric
  classification effort, Astra, round 2).
- **The tranches:** the first tranche is M4e's, 40 first-pass fading genomes per panel and arm, drawn without
  replacement by a fixed seed (its cost is inside the pilot's panel times). The second tranche is 120 more per panel
  and arm, drawn before the run from the remaining first-pass fading genomes by its own seed, run only if triggered.
  Both are simple random samples within the panel, so they combine by pooling: per arm, the estimated rate is
  τ̂_a = (transitions in both tranches) / (genomes audited in both tranches), over all panels.
- **No double counting:** an observed transition is confirmed by the protocol and counts in the raw S. The adjustment
  applies τ̂_a only to the panel's first-pass fading genomes that were not audited: S^adj_a,h = S_a,h + τ̂_a F^un_a,h.
  With no transition in an arm, its adjustment is zero.
- **The primary stays raw** (the protocol's confirmations, as agreed). The audit-adjusted contrast is a separately
  labelled qualifier, not a new estimand: a "raises" that fails on the adjusted counts reads "raises, qualified by the
  audit". Only Rr's transitions can remove a "raises".
- **The uncertainty, zero events included:** the adjustment uses the point estimate τ̂ (Fable, round 2). The audit's
  sampling uncertainty enters the reading as a **bias limit** reported beside the contrast (Fable, D371): with U_a the
  arm's one-sided 95% Clopper–Pearson bound from M5's own audit and f_a the arm's mean unaudited first-pass fading
  share, hidden transitions could move the contrast by at most −U_Rr f_Rr to +U_T f_T. The bound pooled with the
  pilot's and M4e's audits of the same arm (T: 0 of 2283 so far; Rr: 0 of 2286) is reported beside M5's own, labelled
  as assuming a protocol-level rate (Fable, D371). The per-arm bounds are not simultaneous for both arms (Astra). The
  data-dependent second tranche is not corrected for analytically; the simulation measures the whole procedure with
  it.
- **Which outcome needs 80% unconditional power:** the unqualified "raises" (section 1), under the audit's symmetric
  scenario at the bound. The asymmetric and host-concentrated scenarios are reported as limits. In particular, Rr-only
  transitions at the bound make the latent contrast smaller than the protocol's by about 0.0012, so the audit then
  qualifies many "raises", and should.
- **No risk-targeted stratum.** Fable proposed auditing a weakest-margin stratum; Astra noted that the recorded fields
  do not define a margin (the root distance is between two located roots; the read-out difference does not decide the
  fading verdict). No stratum is used. M5 records the root diagnostics at every horizon, so a later study could
  define one.

## 4. The grid, the Monte Carlo rule and the answer

- **Grid:** H from 10 to 150 in steps of 5 (to 300 for δ = 0.001 and the scenario above the range); D in {1, 2};
  G in {512, 1024}. Every scenario of section 2, with the base case: Rr at 0.0058, constant effect, σ_v fitted,
  audit symmetric at the bound.
- **Monte Carlo:** a coarse pass at R = 400 runs per cell, then R = 4000 in every cell within 0.1 of the target
  power. Each run applies the whole reading with B = 2000 (the bootstrap means are a matrix product of the host
  contrasts with a fixed resample-count matrix per H, so B costs little).
- **The selection rule** (Astra, rounds 1 and 2), fixed here: a cell qualifies if its power's one-sided 95%
  Clopper–Pearson lower bound at R = 4000 is at least 0.80. The selected cell is the smallest qualifying H; it is then
  confirmed by an independent simulation with a fresh seed and R = 4000, which must also qualify, or the next H is
  tried. The same rule at 0.90 gives the 90% column.
- **The answer for each allocation:** the fewest hosts and the cheapest allocation that qualify (Astra), with the
  range across the host-variance scenarios. The genome variance scales as 1/(DG) and the host component does not,
  so at a fixed number of genomes more hosts are never worse (Fable, round 1): D = 1, G = 512 is expected to be the
  cheapest, D = 2, G = 1024 the fewest hosts.
- **Also reported per cell:** the false "raises" rate at δ = 0 (with its Monte Carlo bound; the nominal is 2.5%,
  the hull should sit below it) under every audit and spread scenario; the probabilities of every reading; the
  envelope crossing zero; the exclusion at δ = 0 and δ = ±0.002; the misleading-reading rates of the latent scenarios.

## 5. The host count: three rules, one recommended

The pilot puts the contrast's host component at zero, weakly determined on ten hosts; M4e's T − K, a different
contrast, puts it at 1.52e-5. Orientation (normal approximation, D = 2, G = 512): about 23 to 27 hosts at the pilot's
spread, about 59 at M4e's. The rule is fixed before the script runs.

- **A. Fixed H at the top of the core range:** the H that qualifies at a host component of 1.52e-5. Robust to the
  variance, about twice the compute if the pilot is right.
- **B. Fixed H at the central scenario,** the pilot's; the power at 1.52e-5 and 3.0e-5 reported beside it. Cheapest
  if the pilot is right, underpowered (about 50% by the normal approximation) if M4e's spread applies.
- **C. An internal pilot inside M5 (recommended):** M5's first H1 hosts are rule B's count. After they finish, a
  script computes only the sample variance s² of their per-host contrasts, never their mean or any interval, and
  sets the final H = the smallest multiple of 5 that the power table, pre-computed here, gives for that variance,
  clipped to [H1, H_max], with H_max rule A's count. The first hosts count in the final reading. This is Wittes and
  Brittain's internal pilot (1990): for normal data the sample variance is independent of the mean, so re-estimating
  H from it alone inflates the error rate little, and for these sparse counts the simulation measures it rather than
  assuming it.
  - *Why C:* the unknown that decides H is the variance of exactly this contrast, and M5's own first hosts measure
    it, on fresh hosts and on more than the pilot's ten. It spends A's compute only if the variance calls for it.
  - *What it costs:* a fixed H is replaced by a range [H1, H_max] with its cost range. The owner approves the
    maximum. The interim is one registered look at s² alone; nothing else is read before the last batch.
  - *What it needs:* the power table indexed by s² (the script produces it), the interim's script and its test that
    it outputs no mean, and the simulation of the two-stage procedure under every scenario, its type-I rate included.
- The script computes all three, so the reviewers and the owner see their costs side by side; the owner chooses.

## 6. Cost

- **Panel times:** each simulated host draws its T and Rr panel times by resampling a pilot host (both arms, both
  draws together), so a slow host is slow in both arms as in the pilot: T's panels ran 665 to 1511 s (mean 979), Rr's
  537 to 2195 s (mean 1129), the second pass and the first tranche included. G = 1024 doubles a panel's time, a
  linear assumption the report labels. D = 1 takes one of the host's two draws.
- **The second tranche:** 120 genomes per panel and arm at 3.5 to 3.7 s each, about 7 to 7.5 minutes per panel, when
  triggered.
- **Fixed costs:** host sampling, Rr blocks and their reference chains, and the verification, timed on M4e's hosts
  before the script runs and added per host. The pilot's 10,630 seconds outside its stages' recorded phases (12% of
  its compute) are carried as an overhead sensitivity.
- **Reported:** mean, median and 95th percentile CPU hours per allocation, and the probability of exceeding a cap set
  at 1.25 and 1.5 times the mean. At the pilot's times a host costs about 1.2 CPU hours at D = 2, G = 512, so about
  27 to 32 CPU hours under rule B and about 69 under rule A, before the second tranche.
- **Invalid panels:** none in the pilot's 20 Rr panels or M4e's 160. Modelled at zero, with a sensitivity at 1% per panel;
  a host with an invalid panel leaves the reading, its ensemble keeping its 1/5 weight.

## 7. The script, its tests and its review

`scripts/memory_m5/m5_power.py`, writing `runs/memory-m5-power/power.json` and a short report. Pure numpy and scipy,
CPU, seeded. Tests (`tests/test_memory_m5_power.py`), each seen failing first; sabotages
(`scripts/memory_m5/sabotage_m5_power.py`) that break, one at a time:
- the pairing (arms drawn from different panels' probabilities);
- the stratification (a bootstrap resampling across ensembles; weights not 1/5 after a host is left out);
- the audit (an observed transition counted twice; the adjustment applied to audited genomes; the second tranche in
  one arm only);
- the marginal calibration (δ applied on the logit scale without calibration);
- the denominator (incomplete runs dropped);
- the envelope bound (a variance bound centred badly enough to miss a corner);
- the interim (s² computed from the contrasts' mean-shifted values, or the mean written out).
Plus the checks: false "raises" at δ = 0 and no host variance within Monte Carlo error of the hull's rate; power
monotone in δ; the envelope bound contains the exhaustive envelope for H ≤ 12; the calibrated δ recovered within its
Monte Carlo error; the reader's interval reproduces M4e's published T − K from its records.

Then one review round on the script and its output (both), the host count and cost to the owner, and M5's plan and
pre-registration.

## Questions for the reviewers

1. The reading (section 1): the stratified bootstrap with the plain-s² t, the leave-one-out rule, and "unqualified
   raises" as the 80% event. Anything wrong or missing?
2. The model (section 2): the shared host effect plus an interaction, T without a draw term, beta-binomial
   unresolved and oscillation counts, the scenario set. Is anything needed for a correct host count missing, or
   anything here that would bias it?
3. The audit (section 3): the trigger acting on both arms, tranches of 40 and 120 per panel, the pooled point
   estimate on unaudited fading genomes only, the bias limit, no stratum. Does this answer your list?
4. The host count (section 5): A, B or C? If C, is the variance-only interim sound here, and what must its
   simulation show?
5. The Monte Carlo rule and the cost model (sections 4 and 6): adequate?

Verdict: agree (the script may be written) / revise.
