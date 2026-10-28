# M5's pilot: design inputs for the power calculation — results

*Draft 1, 2026-10-28, for review by Astra 6 and Fable 5.1. Descriptive design inputs, not a reading: the plan
([`M5-PILOT-PLAN.md`](M5-PILOT-PLAN.md), draft 3, D369) fixed the stages, the checks and what each result does to M5
before stage (a) ran. The pilot runs on M4e's ten published hosts, so none of its data enter M5's reading; M5's hosts
will be fresh. Numbers come from `runs/memory-m5-pilot/`: `report.json` (written by
[`m5_pilot_read.py`](../../scripts/memory_m5/m5_pilot_read.py); console output `read_log.txt`), `rr-summary.json`,
`arms/`, `longer/`, `audit/`, `composition-check.json`, the run's log `m5_pilot_log.txt`, and the compute records.
Anything the plan did not fix is marked **after the data**.*

## In short

- **The horizon rule keeps 22,000 ticks.** None of the 117 genomes unresolved at 22,000 ticks (T 33, K 37, Rr 47)
  was resolved at 100,000: s = 0 and r = 0, with r's one-sided 95% upper bound 0.025. By the plan's rule (s < 0.5),
  M5 keeps the 22,000-tick protocol and its unresolved genomes are a class at that horizon.
- **The audit found no transition.** 0 of 1500 first-pass fading genomes per arm changed class at 22,000 ticks, in
  any way. Pooled with M4e's panel audits of the same arm, 0 of 2283 to 2286 per arm: a one-sided 95% upper bound of
  0.0013 per arm, which the power simulation uses.
- **Rr on M4e's protocol:** 59 separate-states genomes in 10,240, against T's 75 and K's 55; 47 unresolved (T 33,
  K 37).
- **T − Rr's spread is close to pure genome sampling.** Per-host SD 0.0034 over ten hosts; the method-of-moments host
  component is negative and set to zero; draws 6%, genomes 94% (paired). M4d's first-pass T − Rr (SD 0.0033, 17%
  host and draw) agrees; M4e's T − K (SD 0.0055, 51% host), which the pilot's reader reproduces, is the outlier.
- **T − Rr's mean, reported and not used:** +0.0016, hull interval [−0.0008, +0.0040], 6 of 10 hosts above zero.
  The planning effect stays 0.002 (plan; Fable, round 1).
- **Two choices now fall due** (plan): the audit's branch for M5 and the qualifier's form. Proposals below.

## The run

- **When and what:** one attempt, completed, from 13:56 UTC on 27 October to 13:21 UTC on 28 October, on the CPU of
  the tested machine, at commit 135f8e4 (code clean at the start; `m5-pilot-attempt.json`, a copy of the local
  attempt record; `m5_pilot_log.txt`; exit 0).
  - The attempt records b2baeef at its end: D370 (a test's platform scope and a dated annotation in the plan) was
    committed during stage (b). No code the pilot ran changed.
- **Compute** (`m5-pilot-compute-record.json`, a copy of the local `compute.json`): 84,326 s (23.4 h) of the 30-hour
  cap; 1.35 × 10¹⁰ neural updates. By stage: (b) 32,197 s, (c) 18,920 s, the rest (a) with `m4e.verify_run()`.
- **The checks before any continuation:** `m4e.verify_run()` passed; every panel record validated; the composition
  check reproduced one genome per arm bit for bit in its original chunk of 128 with the float32 hold equal
  (`composition-check.json`: T genome 118, K 11, Rr 226 of SH-2011100 d0).
- **The state check** passed on every (b) genome: each replay batch's hold equalled its original chunk's.
- **The registered replay check and its remedy.**
  - Outside the fallbacks, the largest root-field deviation was 1.4e-13 (T), 6.7e-12 (K) and 3.8e-10 (Rr) in (b),
    and 0 in (c): the audit's fading genomes reproduced bit for bit.
  - **Seven fallbacks**, all in (b) (T 2, K 3, Rr 2), all on genomes unresolved by a failed or marginal root search.
    In every one the class, the reason and the write amplitude were identical, and the panel rerun with
    `m4e.classify_panel` reproduced M4e's record bit for bit, so the stage continued as the plan fixed.
  - Their deviations were larger than the smoke's 3e-13: from 5.7e-9 to **1.0e-3** relative (K genome 474 of
    SH-route-2021101 d0, root distance 1.0159 recorded, 1.0169 replayed). The hold being identical, this is the root
    search's composition dependence on hard cases, as the plan anticipated, but larger than the smoke suggested.
- **Rr's blocks** (`rr-summary.json`): all 20 pass the checks (N2's labelled degrees, every source's sorted
  magnitudes, 75 reciprocal pairs, N2's diagonal, 260 edges, M4e's outside and clamp checks). The chain accepted 10.0
  to 10.3% of its attempted swaps. The blocks stay local (rule 1); their sha256 are committed.

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

Doubling the chain barely moves the overlap (**after the data:** by these measures the chain looks mixed at 5200
accepted swaps, though the continued block shares about three more edges on average). Rr shares about 40% of N2's
edges: a degree- and reciprocity-preserving null on a block this dense shares that much of N2's wiring by
construction, so T − Rr tests the arrangement of the rest (Fable, round 1).

**Every class by arm** (merged classes at 22,000 ticks, 20 panels of 512 genomes per arm).

| Arm | Separate states | Unresolved | Not classified fading | Eligible | Mean panel time |
|---|---|---|---|---|---|
| T | 75 | 33 | 138 | 9770 | 979 s |
| K | 55 | 37 | 102 | 9823 | 908 s |
| Rr | 59 | 47 | 131 | 9799 | 1129 s (537 to 2195) |

T and K are M4e's own records. Rr's rate on this protocol, 0.0058, is near K's, not M4d's first-pass Rr
(32 of 10,240 on M4d's hosts, `M4D-RESULTS.md`), so Fable's round-1 concern that the control's rate might be half K's
does not arise here. Rr has the most unresolved genomes and the slowest panels.

**T − Rr over the ten hosts** (`report.json`, `at_22000.T_minus_Rr`).
- Per host: +0.0059, +0.0029, −0.0010, +0.0010, 0.0000, +0.0059, −0.0039, −0.0020, +0.0049, +0.0020.
- Mean +0.0016, hull interval [−0.0008, +0.0040], 6 of 10 hosts above zero, SD 0.0034.
- **The variance split** (paired genome part): host 0 (the moment estimate, 1.13e-5 − 1.34e-5, is negative), draws
  6%, genomes 94%. The independent-binomial version gives 0, 5% and 95%.
- **The pairing buys nothing here:** 1 genome of 10,240 is confirmed as separate states in both arms. The paired
  tables (`at_100000.paired_T_by_Rr`, identical at 22,000) show T's separate-states genomes mostly fading in Rr, and
  Rr's mostly fading in T.
- **T − K**, recomputed by the same reader from M4e's records: +0.0020, SD 0.0055, split 51/8/41, as published.

**The host-variance sources now** (per-host SD; host-and-draw share).

| Source | Contrast | SD | Host and draw |
|---|---|---|---|
| M4e | T − K | 0.0055 | 59% |
| M4d (first pass only) | T − R | 0.0035 | 12% |
| M4d (first pass only) | T − Rr | 0.0033 | 17% |
| This pilot | T − Rr | 0.0034 | 6% |

M4d's rows are Fable's round-1 recomputation. The pilot's row is the same contrast as M5's on M4e's protocol, but on
ten hosts, so its host component is weakly determined (**after the data**).

## (b) The longer horizon

| Arm | Genomes | Resolved at 100,000 | Separate states at 100,000 | r's upper bound |
|---|---|---|---|---|
| T | 33 | 0 | 0 | 0.087 |
| K | 37 | 0 | 0 | 0.078 |
| Rr | 47 | 0 | 0 | 0.062 |
| Pooled | 117 | 0 (s = 0) | 0 (r = 0) | 0.025 |

- **The rule:** s < 0.5, so M5 keeps 22,000 ticks (`longer.horizon_rule`: "keep 22,000 ticks"). (b) was complete.
- **The reasons barely move** between 22,000 and 100,000 (`longer.by_arm`): "unstable or marginal root" and
  "unconfirmed candidate" lead in every arm at both horizons; one T genome became "slow". **After the data:** these
  genomes look held by the classifier's root search, not by the horizon: four and a half times the ticks resolved
  none. That is a reading of the reasons, not a test.
- As the plan says, r does not bound eventual switches among genomes still unresolved at 100,000.

## (c) The audit

| Arm | Audited | Any class change | Fading to separate | Upper bound | Pooled with M4e's panel audits |
|---|---|---|---|---|---|
| T | 1500 | 0 | 0 | 0.0020 | 0 of 2283, 0.0013 |
| K | 1500 | 0 | 0 | 0.0020 | 0 of 2286, 0.0013 |
| Rr | 1500 | 0 | 0 | 0.0020 | 0 of 2286, 0.0013 |

Rr's own panel audits (40 per panel, 786 in all) found none either. **After the data:** pooled over the three arms,
0 of 6855, a bound of 0.00044. The plan's pooling is per arm, and the power simulation uses 0.0013.

## What this gives the power calculation

The inputs, as the plan fixed them:
- **The horizon:** 22,000 ticks; the unresolved genomes are a class.
- **The rates:** T 0.0073, Rr 0.0058, as scenarios; the planning effect 0.002, not the pilot's +0.0016.
- **The unresolved shares:** T 0.0032, Rr 0.0046 (Rr's per panel from 0 to 10 of 512).
- **The qualifier's input:** r = 0, with its upper bound 0.025, and no other pilot quantity.
- **The audit:** a transition rate of 0.0013 per arm.
- **The variance:** a range of host components, from zero (this pilot, M4d) to M4e's T − K, not a point.
- **The cost:** per-panel times by arm (`report.json`, `counts.*.panel_seconds`), Rr's tail included.

**Orientation only, not the power calculation** (normal approximation, two-sided 5%, 80%, effect 0.002, per-host SD
at M4e's design of 2 draws of 512): about 23 hosts at the pilot's SD of 0.0034, about 59 at M4e's T − K SD of 0.0055.
At the pilot's mean panel times a host costs about 1.2 CPU hours for T and Rr, so about 27 to 69 CPU hours before
the unresolved qualifier, the audit and the t correction.

## Two choices for M5's plan (proposals for review)

**1. The audit's branch.** The plan offers Fable's pre-specified adjustment with a second tranche, or Astra's
completion of both arms' fading genomes.
- *Proposal:* Fable's branch. M5 audits a fixed random sample of first-pass fading genomes per arm, sized in the
  power script; a second tranche is triggered only if the first finds a transition; any transitions found adjust the
  primary by a rule fixed in the plan.
- *Why:* 0 of 6855 audited fading genomes across three arms changed in any way. Completing the audit means continuing
  about 96% of every panel to 22,000 ticks (about 4 s each in (c), so about 35 minutes per panel against a panel's
  15 to 19 minutes), which would about triple
  M5's cost to guard against a rate not yet seen once. The simulation still carries 0.0013 per arm, never zero, and
  its arm-asymmetric scenario (transitions in one arm only) shows what an undetected rate of that size could do.

**2. The qualifier's form.** The plan offers Fable's calibrated adjustment, or Astra's bounds
[c_T − c_Rr − u_Rr, c_T − c_Rr + u_T].
- *What the pilot shows:* Astra's bounds would have width u_T + u_Rr, about 0.0078 at the pilot's shares, nearly four
  times the planning effect, at any number of hosts. A qualifier of that form would mark every M5 outcome as
  undetermined by the unresolved genomes. The calibrated form, with r's upper bound 0.025, moves the contrast by at
  most about 0.025 × 0.0046 ≈ 0.0001.
- *Proposal:* the primary stays as agreed (unresolved count as not confirmed, so the primary's estimand is the
  protocol's confirmations, and the qualifier does not change its reading). The qualifier is Fable's calibrated
  adjustment at r's upper bound, applied to each arm's unresolved share, with both one-arm cases (all of T's
  unresolved at the bound and none of Rr's, and the reverse). Astra's worst-case bounds are reported beside it as the
  envelope, descriptive, with the plan's caveat in the outcome wording: r does not bound switches among genomes the
  protocol leaves unresolved.

## Deviations and notes

- **The reader's console:** run with PYTHONIOENCODING=utf-8 from the start (M4e's lesson).
- **D370** changed a test's platform scope during the run (above); no pilot code changed.
- **The fallbacks' size** (up to 1.0e-3 relative) is larger than the plan's evidence (3e-13). Every fallback met the
  plan's condition for continuing.
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
