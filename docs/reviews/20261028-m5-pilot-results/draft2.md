# M5's pilot: design inputs for the power calculation — results

*Draft 2, 2026-10-28, after one round of review (Astra 6 and Fable 5.1, both "fix then publish"; every finding taken;
draft 1 and the reviews are archived in [`docs/reviews/20261028-m5-pilot-results/`](../reviews/20261028-m5-pilot-results/)).
Descriptive design inputs, not a reading: the plan
([`M5-PILOT-PLAN.md`](M5-PILOT-PLAN.md), draft 3, D369) fixed the stages, the checks and what each result does to M5
before stage (a) ran. The pilot runs on M4e's ten published hosts, so none of its data enter M5's reading; M5's hosts
will be fresh. Numbers come from `runs/memory-m5-pilot/`: `report.json` (written by
[`m5_pilot_read.py`](../../scripts/memory_m5/m5_pilot_read.py); console output `read_log.txt`), `rr-summary.json`,
`arms/`, `longer/`, `audit/`, `composition-check.json`, the run's log `m5_pilot_log.txt`, and the compute records.
Anything the plan did not fix is marked **after the data**. In review, Astra regenerated all 40 Rr blocks (matching
their sha256), reproduced the audit samples, contrasts, intervals and variance splits, and checked every stage file;
Fable recomputed every table cell, bound and contrast from the files. After review the reader gained the fallbacks'
details, per-panel audit bounds, full class breakdowns, per-host totals and the untruncated host moment; every value
it reported before is unchanged (checked key by key).*

## In short

- **The horizon rule keeps 22,000 ticks.** None of the 117 genomes unresolved at 22,000 ticks (T 33, K 37, Rr 47)
  was resolved at 100,000: s = 0 and r = 0, with r's one-sided 95% upper bound 0.025. By the plan's rule (s < 0.5),
  M5 keeps the 22,000-tick protocol and its unresolved genomes are a class at that horizon.
- **The audit found no transition.** 0 of 1500 first-pass fading genomes per arm changed class at 22,000 ticks, in
  any way. Pooled with the arm's own panel audits (M4e's for T and K, stage (a)'s for Rr), 0 of 2283 to 2286 per arm:
  a one-sided 95% upper bound of 0.0013 per arm, which the power simulation uses.
- **Rr on M4e's hosts:** 59 separate-states genomes in 10,240, against T's 75 and K's 55; 47 unresolved (T 33,
  K 37).
- **T − Rr's spread is close to genome sampling alone.** Per-host SD 0.0034 over ten hosts; the method-of-moments host
  component is negative (−2.1e-6) and set to zero; draws 6%, genomes 94% (paired). M4d's first-pass T − Rr (SD 0.0033,
  17% host and draw combined) is similar. M4e's T − K (SD 0.0055, 51% host), which the pilot's reader reproduces, is
  the larger historical source. Ten hosts determine the host component weakly: its one-sided 95% upper limit from
  this pilot is about M4e's T − K value.
- **T − Rr's mean, reported and not used:** +0.0016, hull interval [−0.0008, +0.0040], 6 of 10 hosts above zero.
  The planning effect stays 0.002 (plan; Fable, round 1).
- **The two choices that fell due are agreed** (both reviewers): a sampled audit, not a completed one, and the
  calibrated qualifier as a protocol sensitivity with the logical bounds beside it. Details for M5's plan below.

## The run

- **When and what:** one attempt, completed, from 13:56 UTC on 27 October to 13:21 UTC on 28 October, on the CPU of
  the tested machine, at commit 135f8e4 (code clean at the start; `m5-pilot-attempt.json`, a copy of the local
  attempt record; `m5_pilot_log.txt`; exit 0).
  - The attempt records b2baeef at its end: D370 (a test's platform scope and a dated annotation in the plan) was
    committed during stage (b). No code the pilot ran changed.
- **Compute** (`m5-pilot-compute-record.json`, a copy of the local `compute.json`): 84,326 s (23.4 h) of the 30-hour
  cap; 1.35 × 10¹⁰ neural updates. The recorded subtotals (Fable, Astra):

  | Component | Seconds |
  |---|---|
  | (a): the 20 Rr panel classifications (`counts.Rr.*.panel_seconds`) | 22,579 |
  | (b): recorded phases (`seconds.longer`) | 32,197 |
  | (c): recorded phases (`seconds.audit`) | 18,920 |
  | Not attributed by any record | 10,630 |

  The phase timers exclude the composition check and the seven fallbacks' panel reruns (each a full
  `m4e.classify_panel` of 512 genomes). The unattributed part holds those, `m4e.verify_run()`, the blocks'
  construction and overhead; no record splits it further.
- **The checks before any continuation:** `m4e.verify_run()` passed; every panel record validated; the composition
  check reproduced one genome per arm bit for bit in its original chunk of 128 with the float32 hold equal
  (`composition-check.json`: T genome 118, K 11, Rr 226 of SH-2011100 d0). It covers the first pass, by design; Rr
  226's second pass is itself one of the fallbacks below (Fable).
- **The state check** passed on every (b) genome: each replay batch's hold equalled its original chunk's.
- **The registered replay check and its remedy.**
  - Outside the fallbacks, the largest root-field deviation was 1.4e-13 (T), 6.7e-12 (K) and 3.8e-10 (Rr) in (b),
    and 0 in (c): the audit's fading genomes reproduced bit for bit.
  - **Seven fallbacks**, all in (b) (T 2, K 3, Rr 2; five at the first pass, two at the second), all unresolved
    genomes whose reason includes "Newton failure", the population the plan's remedy named (Fable). In every one the
    class and the reason were identical, and so was the write amplitude wherever recorded. The panel rerun with
    `m4e.classify_panel` reproduced the failing genome's recorded fields for the failing pass bit for bit (Astra), so
    the stage continued as the plan fixed.
  - Their normalized deviations, |Δ| / max(1, |recorded|), were larger than the smoke's 3e-13: from 5.7e-9 to
    **1.04e-3** (K genome 474 of SH-route-2021101 d0, root distance 1.0159 recorded, 1.0169 replayed; every fallback
    with both deviations is in `report.json`, `longer_replay.*.fallback_details`). The hold being identical, this is
    the root search's composition dependence on hard cases, as the plan anticipated, but larger than the smoke
    suggested. The plan's remedy set an exact-rerun condition, not a largest deviation (Astra).
- **Rr's blocks** (`rr-summary.json`): all 20 pass the checks (N2's labelled degrees, every source's sorted
  magnitudes, 75 reciprocal pairs, N2's diagonal, 260 edges, M4e's outside and clamp checks). The chain accepted 10.0
  to 10.3% of its attempted swaps for the blocks run, 9.8 to 10.4% over all 40 blocks. The blocks stay local (rule 1); their sha256 are committed.

## (a) Rr against N2's block

**How much of N2's block Rr keeps** (over the 20 blocks: minimum, mean, maximum).

| | First block (run) | Continued chain (described) |
|---|---|---|
| Edges shared with N2 (of 260) | 93, 104.0, 112 | 98, 107.1, 119 |
| of N2's 150 reciprocal edges | 52, 59.2, 67 | 56, 63.0, 71 |
| of N2's 110 non-reciprocal edges | 38, 44.8, 52 | 37, 44.1, 53 |
| shared with the same magnitude | 8, 20.2, 33 | 11, 19.6, 32 |
| minimum-weight overlap | 0.23, 0.26, 0.30 | 0.19, 0.26, 0.31 |
| N2's weight share on shared edges | 0.38, 0.46, 0.52 | 0.40, 0.47, 0.52 |
| S3 | 1.32, 1.64, 2.06 | 1.21, 1.59, 1.98 |

**After the data:** these overlap summaries changed little after another 5200 accepted swaps (Astra). Paired over the
20 chains, the continued block shares 3.15 more edges with N2 (SD 8.0, t 1.8) and 3.8 more of N2's reciprocal edges
(SD 6.1, t 2.8). That direction is the opposite of under-mixing: a chain started at N2 and not yet mixed would leave
its first block closer to N2 than its continuation (Fable). So there is no sign of under-mixing on the overlap with
N2, the only coordinate checked; two chain lengths do not establish mixing.

Rr shares about 40% of N2's edges, but only about 20 with the same magnitude. T − Rr tests the plan's estimand: N2's
weighted arrangement inside C3 beyond its labelled degrees, each neuron's outgoing anatomical magnitudes, its diagonal
and its count of reciprocal pairs (plan, "What M5 is to test").

**Every class by arm** (merged classes at 22,000 ticks, 20 panels of 512 genomes per arm).

| Arm | Separate states | Unresolved | Not classified fading | Eligible | Mean panel time |
|---|---|---|---|---|---|
| T | 75 | 33 | 138 | 9770 | 979 s |
| K | 55 | 37 | 102 | 9823 | 908 s |
| Rr | 59 | 47 | 131 | 9799 | 1129 s (537 to 2195) |

T and K are M4e's own records. Rr's 59 are all first-pass confirmations (`separate_first_pass` equals `separate` in
every Rr panel), so the gap to M4d's Rr (32 of 10,240, first pass, `M4D-RESULTS.md`) is M4d's other hosts and draws,
not the second pass (Fable). T moved too: 64 on M4d's hosts against 75 here. The ratio Rr/T went from 0.50 on M4d's
hosts to 0.79 on M4e's, which answers Fable's round-1 concern that the control's rate might be half T's or K's: on
these hosts it is not. Rr has the most unresolved genomes and the slowest panels; the slowest are SH-recip's (2195
and 2024 s).

**T − Rr over the ten hosts** (`report.json`, `at_22000.T_minus_Rr`).
- Per host: +0.0059, +0.0029, −0.0010, +0.0010, 0.0000, +0.0059, −0.0039, −0.0020, +0.0049, +0.0020.
- Mean +0.0016, hull interval [−0.0008, +0.0040], 6 of 10 hosts above zero, SD 0.0034.
- **The variance split** (paired genome part, per draw of 512 genomes): host 0 (the moment estimate, 1.13e-5 −
  1.34e-5 = −2.1e-6, `host_moment`), draw 1.5e-6, genome 2.5e-5; as shares of a host's contrast variance, draws 6%,
  genomes 94%. The independent-binomial version gives 0, 5% and 95%.
- **The truncation matters for the power script** (Astra): the observed SD of the host contrasts is 0.00336, but the
  non-negative components imply sqrt((1.5e-6 + 2.5e-5) / 2) = 0.00365. The simulation must not equate the two.
- **The pairing buys nothing here:** 1 genome of 10,240 is confirmed as separate states in both arms. The paired
  tables (`at_100000.paired_T_by_Rr`, identical at 22,000) show T's separate-states genomes mostly fading in Rr, and
  Rr's mostly fading in T.
- **T − K**, recomputed by the same reader from M4e's records: +0.0020, SD 0.0055, split 51/8/41, as published.
- **Why the two contrasts differ** (Fable, **after the data**). Per host over 1024 genomes (`per_host_totals`), T's
  confirmations are 17, 3, 7, 5, 12, 10, 2, 6, 10, 3; Rr's 11, 0, 8, 4, 12, 4, 6, 8, 5, 1; K's 4, 6, 4, 3, 6, 3, 7,
  4, 14, 4. T and Rr are both overdispersed against a binomial and correlate across hosts at 0.70; T and K at 0.06.
  A contrast's host component is the host effect the control does not share; Rr shares T's, K does not.

**The host-variance sources now** (per-host SD; host-and-draw share).

| Source | Contrast | SD | Host and draw |
|---|---|---|---|
| M4e | T − K | 0.0055 | 59% |
| M4d (first pass only) | T − R | 0.0035 | 12% |
| M4d (first pass only) | T − Rr | 0.0033 | 17% |
| This pilot | T − Rr | 0.0034 | 6% |

M4d's rows are Fable's round-1 recomputation; with one draw per host, M4d identifies only the host and draw residual
combined (about 1.5e-6 for T − R and 1.9e-6 for T − Rr, Astra), not a zero host component. The pilot's row is the same
contrast as M5's on M4e's protocol, but on ten hosts. **After the data** (Fable): with 9 degrees of freedom, the
variance of the host means (1.13e-5) has a one-sided 95% upper limit near 3.1e-5, so the host component can be as
large as about 1.7e-5, M4e's T − K value (1.52e-5). Zero to M4e's T − K is therefore a core scenario range, consistent
with the pilot's own uncertainty, not a confidence interval or a demonstrated upper bound (Astra); the simulation
also needs a scenario above it.

## (b) The longer horizon

| Arm | Genomes | Resolved at 100,000 | Separate states at 100,000 | r's upper bound |
|---|---|---|---|---|
| T | 33 | 0 | 0 | 0.087 |
| K | 37 | 0 | 0 | 0.078 |
| Rr | 47 | 0 | 0 | 0.062 |
| Pooled | 117 | 0 (s = 0) | 0 (r = 0) | 0.025 |

- **The rule:** s < 0.5, so M5 keeps 22,000 ticks (`longer.horizon_rule`: "keep 22,000 ticks"). (b) was complete.
- **The reasons barely move** between 22,000 and 100,000 (`longer.by_arm`): "unstable or marginal root" and
  "unconfirmed candidate" lead in every arm at both horizons; one T genome became "slow". Extending the hold to
  100,000 ticks resolved none under the unchanged classifier, and root-related reasons remained common. This does not
  distinguish limits of the root search from hard dynamics (Astra, Fable). Some look dynamical: K genome 287 of
  SH-mirror-2041101 d0 sits at the same root distance, 2.27, at 2000 and 22,000 ticks with "located root not reached"
  (Fable).
- As the plan says, r does not bound eventual switches among genomes still unresolved at 100,000.

## (c) The audit

| Arm | Audited | Any class change | Fading to separate | Upper bound | Pooled with M4e's panel audits |
|---|---|---|---|---|---|
| T | 1500 | 0 | 0 | 0.0020 | 0 of 2283, 0.0013 |
| K | 1500 | 0 | 0 | 0.0020 | 0 of 2286, 0.0013 |
| Rr | 1500 | 0 | 0 | 0.0020 | 0 of 2286, 0.0013 |

Rr's own panel audits (stage (a), 40 per panel, 786 fading in all) found none either. Per-panel counts and bounds are
in `audit.by_arm.*.by_panel`. **After the data:** pooled over the three arms the count is 0 of 6855. These are
genome-arm evaluations, not independent genomes: the arms share hosts and genome panels (5451 distinct host, draw and
genome identities, Astra). A pooled-binomial bound of 0.00044 would assume a rate the same in every arm, the opposite
of the arm-asymmetric scenario the simulation guards against, and it bounds neither arm nor their difference. It is
not used. The plan's pooling is per arm, and the power simulation uses the unrounded per-arm bounds (0.00131133 for
T, 0.00130961 for K and Rr). The per-arm bounds are not simultaneous 95% assurance for both arms (Astra).

## What this gives the power calculation

The inputs, as the plan fixed them, with the reviewers' additions:
- **The horizon:** 22,000 ticks; the unresolved genomes are a class.
- **The rates:** T 0.0073, Rr 0.0058, as scenarios; the planning effect 0.002, not the pilot's +0.0016.
- **The unresolved shares:** T 0.0032, Rr 0.0046 (Rr's per panel from 0 to 10 of 512).
- **The qualifier's input:** r = 0, with its upper bound 0.0253, and no other pilot quantity.
- **The audit:** the unrounded per-arm bounds (0.00131 per first-pass fading genome), multiplied by the arm's
  first-pass fading share (98.6% in T and Rr) to give an all-genome effect; transitions concentrated in either arm as
  separate scenarios, and heterogeneous host and panel allocations, not only a common arm-wide rate (Astra).
- **The variance, as components, not an SD** (Fable): host, draw and genome parts per draw of 512 genomes, so the
  script can model D and G. Host components from zero to M4e's T − K (1.52e-5) as the core range, with a scenario
  above it (Astra). The model should have a host base-rate effect shared by the arms with a correlation, plus an
  arm × host interaction, so that a proportional effect makes the interaction nonzero under a true effect (Fable).
  The pilot's T − Rr, the same control on the same protocol, is the central scenario (Fable).
- **The cost:** the per-panel time distribution by arm and host (`counts.*.panel_seconds`; SH-recip is slowest in
  every arm), plus the audit tranche (Fable).

**Orientation only, not the power calculation** (normal approximation, two-sided 5%, 80%, effect 0.002, per-host SD
at M4e's design of 2 draws of 512): about 23 hosts at the pilot's observed SD of 0.0034, 27 at the truncated
components' 0.00365, about 59 at M4e's T − K SD of 0.0055. At the pilot's mean panel times a host costs about 1.2
CPU hours for T and Rr, so about 27 to 69 CPU hours before the unresolved qualifier, the audit and the t correction.

**Still open before `m5_power.py` is written** (both reviewers):
- **The rule that turns the variance range into one H** (Fable, rounds 2 and 1 here): either H at the host
  component's upper scenario (about 59 hosts, about 69 CPU hours at D = 2, G = 512), or H at the pilot's point
  estimate with the pessimistic power reported beside it. Written before the script.
- **The audit's estimator and decision rule** (Astra, below).

## Two choices for M5's plan

**1. The audit's branch.** The plan offers Fable's pre-specified adjustment with a second tranche, or Astra's
completion of both arms' fading genomes. **Agreed by both: the sampled audit, not a completed one.**
- *Why:* no audited fading genome changed class in any arm (per arm 0 of 2283 to 2286). Completing the audit means
  continuing about 91% of every panel to 22,000 ticks (98.6% are first-pass fading; 40 per panel are already
  audited). At about 3.5 s per genome for the continuation alone (the 4.1 to 4.3 s per genome in (c) include a
  replayed first pass of about 0.65 s), that is about 29 minutes per panel against a panel's 15 to 19 minutes: two and
  a half to three times M5's cost, a rough replay-based estimate (Fable, Astra), to guard against a rate not seen
  once. The simulation still carries the per-arm bounds, never zero, with an arm-asymmetric scenario.
- *To specify in M5's plan before the power script* (Astra):
  - the trigger (fading to separate states, or any class change), and whether it acts separately by arm;
  - both tranche sizes, their sampling populations, and how they combine;
  - how observed reclassifications and estimated transitions among unaudited fading genomes enter the estimator,
    without double counting;
  - how the audit's uncertainty, zero-event uncertainty included, and the data-dependent second tranche enter the
    inference;
  - which outcome must reach 80% unconditional power;
  - whether the primary stays the raw protocol share with the adjustment labelled separately, or becomes an
    audit-adjusted estimator with its own estimand.
- *Fable's additions:* the outcome wording carries the audit's bound as a bias limit on the contrast, as the envelope
  is reported; pooling across hosts and experiments assumes a protocol-level rate, so M5's own unpooled bound is
  reported beside it; and a risk-targeted stratum. A genome fading at a confirmed stable root cannot leave it under
  deterministic dynamics, so a transition needs a first-pass misclassification. Auditing every first-pass fading genome
  in the weakest-margin stratum (by the recorded root distance and read-out difference) plus the random tranche guards
  where a transition could hide.

**2. The qualifier's form.** The plan offers Fable's calibrated adjustment, or Astra's bounds
[c_T − c_Rr − u_Rr, c_T − c_Rr + u_T]. **Agreed by both, as a sensitivity for the protocol estimand.**
- *What the pilot shows* (Astra's figures): the bounds' width is u_T + u_Rr = 0.0078 at the pilot's shares, nearly
  four times the planning effect, at any number of hosts. They cross zero when the confirmed contrast lies between
  −0.0032 and +0.0046; at the pilot's contrast they are [−0.0030, +0.0048], before sampling uncertainty. The
  calibrated adjustment at r's upper bound moves the contrast by +0.00008 (all of T's unresolved confirmed at the
  bound) or −0.00012 (Rr's), conditional on the calibration assumption: it is not an empirical bound on hidden-state
  bias.
- *Agreed form:*
  - The primary stays as agreed: unresolved genomes count as not confirmed, so the estimand is the protocol's
    confirmations.
  - The **protocol sensitivity** is the calibrated adjustment at r's upper bound, in both one-arm cases. M5's plan says
    in advance that at shares like the pilot's it is at most about 0.0001 and will not change any outcome (Fable).
  - The **logical bounds** are Astra's envelope, reported beside it, descriptive.
  - The outcome wording: the pooled r bounds neither arm's latent switches nor each arm's confirmation probability,
    and applying it to one arm is an assumed scenario (plan). When the envelope permits a sign reversal, M5 says that
    the contrast in underlying separate states is unidentified; passing the calibrated sensitivity must not imply
    otherwise (Astra). The unresolved-share secondary is the only observable guard on the asymmetric case (Fable).

## For M5's plan, from the fallbacks

- **Keep M4e's classifier and its production composition** (Fable): changing the classifier's batching is an engine
  change under rule 7 and would break comparability with M4e. The plan states that the root fields depend on the
  batch's composition and are not claimed across compositions.
- **Predefine the composition and record it** (Astra): deterministic batching, target order, chunk boundaries and the
  handling of a batch of one, with each genome's actual batch membership recorded. A chunk size of 128 alone is not
  enough when target lists change.
- **Record a hash of the float32 hold** (end state, tail, read-out) per genome at 2000 and 22,000 ticks (Fable), so a
  later replay is verifiable on the state alone, without a tolerance on the root fields.
- **Keep the original-composition replay** for adjudicating a discrepancy, and record root diagnostics and any
  rerun's evidence at every horizon (Astra); the pilot's 100,000-tick records hold only class and reason.
- The evidence that class and reason do not depend on composition: no flip in 234 replayed unresolved-genome passes
  and 4500 fading genomes; on the hard cases alone the bound is loose (0 of 234), which does not touch M5's estimand
  (Fable).

## Deviations and notes

- **The reader's console:** run with PYTHONIOENCODING=utf-8 from the start (M4e's lesson).
- **D370** changed a test's platform scope during the run (above); no pilot code changed.
- **The fallbacks' size** (up to 1.04e-3 normalized) is larger than the plan's evidence (3e-13). Every fallback met the
  plan's condition for continuing.
- **The reader after review** added fields only; `report.json`'s earlier values are unchanged. Panels in the
  fallback details and the timings are labelled by host index and draw (`6 d1` is SH-mirror-2041100 d1).
- **Rr's blocks** are not saved; they regenerate from `default_rng(20264001 + hd)` and are checked by their sha256.

## Reproduce it

```
python scripts/fetch_connectome.py
python scripts/memory_m4/m4e.py            # M4e's panels, if not present
python scripts/memory_m5/m5_pilot.py       # stages rr, longer, audit; resumable; about 23 CPU hours
PYTHONIOENCODING=utf-8 python scripts/memory_m5/m5_pilot_read.py
```

Rule 6: the run repeats exactly on the same machine and platform; the replay's root fields are compared by the
plan's registered rule, not claimed bit for bit across batch compositions.
