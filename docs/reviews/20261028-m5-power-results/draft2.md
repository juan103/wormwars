# M5's power calculation: results

*Draft 2, 2026-10-28, for the second review by Astra 6 and Fable 5.1 before the host count goes to the owner. The
design is [`M5-POWER-DESIGN.md`](M5-POWER-DESIGN.md) (draft 4). The script is
[`scripts/memory_m5/m5_power.py`](../../scripts/memory_m5/m5_power.py), with the reading in
[`m5_reading.py`](../../scripts/memory_m5/m5_reading.py). The outputs are `runs/memory-m5-power/power.json` (the
reading as written) and `runs/memory-m5-power-welch/power.json` (the reading with the Welch t added to the balanced
hull, section 3). Draft 1 and the first round's reviews are in
[`docs/reviews/20261028-m5-power-results/`](../reviews/20261028-m5-power-results/). Exploratory design work; nothing
here is a reading of M5. CPU only; each full run took about 45 minutes.*

## In short

- **After the first round's fixes, rule A and the A-or-C choice no longer depend on the reading.**
  - A's cheapest allocation is 1 draw of 512 genomes with an audit of 80 ids per panel: **135 hosts, 92 mean CPU
    hours**, under both readings.
  - Rule C saves **23.0%** (as written) or **22.1%** (Welch) against A under the central scenario. The design's 20%
    rule therefore recommends **C under both readings**.
  - Draft 1's flip (A as written, C with Welch) came from Monte Carlo noise near the threshold, as Fable said.
    These are the **smallest confirmed host counts tested**, on a grid of 5, not exact minima.
- **The false "raises" gate (design, section 4), as written, now passes for A's and C's selections but fails for B's
  and for A's fewest-host one.** Six of 32 null cells exceed the 0.0275 tolerance. Pooled over every null row
  except the ensemble-heterogeneous one, the raw "raises" rate is **2.52%** (95% interval 2.49% to 2.55%). With
  the Welch t it is **2.36%** (2.33% to 2.39%), and every cell passes.
- **What the reading still decides:** B's count (95 or 110 hosts), and C's policy:
  - as written: 1 × 512 × 80, H1 = 95, H_max = 145;
  - with Welch: 1 × 512 × 40, H1 = 110, H_max = 160.

  The expected costs are within about 1 CPU hour of each other.
- **A limit of identification, for the owner's budget decision (Astra):**
  - M5 can show that N2's wiring raises the share of genomes *this protocol confirms* as separate states.
  - It cannot show the direction of the contrast in *underlying* separate states. If 0.002 of Rr's genomes were
    latent switches the protocol leaves unresolved, M5 would still read a confirmed "raises" in about 80% of runs.
    More hosts do not change that.
  - The pilot speaks against that hazard (Fable): none of Rr's 47 unresolved genomes there resolved by 100,000
    ticks.

## What changed since draft 1

The first round's fixes; each new behaviour has a test that was seen failing first. 45 tests pass, and 17 of 17
sabotages fail their tests by assertion (`runs/m5-power-sabotage.txt`).
- **Rr's host SD is fitted jointly with its block-draw term (Astra).** Draft 1 fitted the host SD without the draw,
  then added the draw, which counted it twice. The jointly fitted SDs are 0.478 (host) and 0.192 (draw). The pooled
  host SD is 0.485, against draft 1's 0.495.
- **The host-variance scenarios are solved by quadrature, not on 200,000 sampled hosts (Astra).** Each realises its
  target to within 1e-12.
- **Rule C leaves invalid hosts out of the interim and the reading (Astra).** A run with fewer than two valid stage-1
  hosts in an ensemble stops, incomplete. With every panel invalid, every run now stops (draft 1's code reported 83%
  successes).
- **Rule C reports stage 1's own audit bound** and its coverage, beside the final one's.
- **The exclusion is attempted after an invalid host** when every leave-one-out reading stays valid.
- **The fixed costs now include M4e's timed verification** (a tenth of a verify run per host), and charge one block
  build per draw actually used. Per host, they are 14.2 CPU seconds to build the host, 0.6 per Rr block and 14.9 to
  verify (`fixed-costs.json`).
- **New diagnostics in the outputs:**
  - each null cell's parts: the bootstrap alone, the t's "raises" and "lowers", and the Welch t;
  - two further null rows, the ± and ensemble nulls at the core scenario as well as the central one (Fable);
  - the realised host component per effect spread;
  - the simulated first-to-final counts in the calibration check;
  - the share of runs over 1.25 times the mean cost;
  - the audit bound pooled with M4e's audits, as a comparison;
  - the unbalanced reading's coverage under unequal ensemble spreads;
  - rule C's invalid-panel sensitivities (stage `c_sens`).

## The fit and the calibration check

- **The scenarios now solve to:**
  - ρ = 1 for the central scenario;
  - ρ = 0.594 for 7.6e-6;
  - ρ = 0.147 for 1.52e-5;
  - ρ = 0 with σ² scaled by 1.60 for 3.0e-5.

  These lie near, not at, the reviewers' 0.616 and 0.193, which were computed from draft 1's separately fitted SD.
  At the central scenario, the implied per-arm count variances are 15.2 (T) and 16.0 (Rr), with a correlation of
  0.60.
- **The calibration check passes.** Every pilot value lies inside the simulated central 95%, at the pilot's fitted
  rates. The quantiles of the observed values are:

  | Pilot value | Quantile |
  |---|---|
  | SD | 0.43 |
  | Half-width | 0.43 (0.11 with Welch: the Welch hull is wider at ten hosts than the pilot's) |
  | Count variance, T / Rr | 0.78 / 0.61 |
  | Correlation | 0.71 |
  | Unresolved share, T / Rr | 0.54 / 0.57 |
  | First-pass unresolved, T / Rr | 0.54 / 0.56 |
  | Unresolved that became fading, T / Rr | 0.55 / 0.55 |

## 1. The host counts by allocation (80%)

Hosts and mean CPU hours, at the confirmed H. Where the two readings differ, the table shows the Welch figure after
a slash.

| (D, G, A) | A | B | A's raw-only H | A at τ = 0 |
|---|---|---|---|---|
| 1, 512, 40 | 155, 94 | 110, 67 | 95 | 105 |
| 1, 512, 80 | **135, 92** | 95, 65 / 100, 69 | 90 | 95 |
| 1, 512, 160 | 125, 105 / 130, 109 | 85, 72 | 95 | 100 / 105 |
| 1, 1024, 40 | 120, 135 | 75, 84 | 65 | 75 |
| 1, 1024, 80 | 105, 126 | 60, 72 | 60 / 70 | 70 / 75 |
| 1, 1024, 160 | 90, 123 / 95, 129 | 50, 68 | 65 | 70 |
| 2, 512, 40 | 100, 118 | 60, 71 | 60 | 75 |
| 2, 512, 80 | 90, 120 | 50, 67 | 65 | 70 / 75 |
| 2, 512, 160 | 80, 132 / 85, 141 | 45, 74 | 65 | 70 |
| 2, 1024, 40 | 80, 176 | 40, 88 | 50 | 55 |
| 2, 1024, 80 | 75, 177 | 30, 71 / 35, 82 | 45 / 50 | 60 |
| 2, 1024, 160 | 70, 187 | 30, 80 | 55 | 55 |

- **Every allocation was confirmed in both families under both readings.**
- **The descriptive columns are coarse.** The raw-only and τ = 0 columns are point estimates from 400 runs.
- **The selected allocations:**
  - A's cheapest is 1 × 512 × 80 at 135 hosts; A's fewest-host one is 2 × 1024 × 160 at 70 hosts.
  - As written, B's cheapest is 1 × 512 × 80 at 95 hosts, and its fewest-host one 2 × 1024 × 80 at 30. With Welch,
    they are 1 × 512 × 40 at 110 and 2 × 1024 × 160 at 30.
- **At 90%, under both readings:** A's cheapest needs 185 hosts (127 CPU hours) and its fewest-host one 90 hosts (240
  hours); B's cheapest needs 135 hosts (93 hours).
- **How close the selections sit to the threshold.** At A's cheapest allocation, the candidate needs a family-level
  lower bound of 0.80. With R = 4000 runs, 130 hosts gave 3252 successes as written and 3235 with Welch; both fail
  the bound. 135 hosts gave 3290 and 3282, which pass. In draft 1, before the fit's correction, 130 hosts gave 3277
  as written and 3271 with Welch, one either side of the bound. Differences of 5 hosts between runs are within this
  noise.

**Why so many more hosts than the orientation's 23 to 59:**
- **The success event:** six readings, not one. At A's cheapest under the core scenario:
  - raw "raises" holds in 94% of runs, and all six readings in 83%;
  - the audit qualifies 7.0% of runs, the unresolved sensitivities 2.5%, and the combinations alone 2.7%.
- **The audit at the bound.** At τ = 0.00131 in both arms, the adjustment's noise qualifies true "raises" (Fable's
  round-2 point 7). At τ = 0, A's cheapest allocation would need about 95 hosts, not 135. The unqualified H exceeds
  the raw-only H by more than a third in 9 of 12 allocations as written (10 of 12 with Welch). So, by the reporting
  rule, M5's pre-registration names the qualifiers' noise as the reason when it fixes A.
- **Many small hosts.** D = 1 with G = 512 is the cheapest per unit of power, as Fable predicted. The fewest-host
  allocations cost about twice as much.

## 2. A's cheapest allocation under the scenarios (R = 4000, pointwise)

1 × 512 × 80 at 135 hosts. The two readings agree to within 0.003 in every row; the figures below are as written.

| Scenario | Unqualified | Raw | Realised host component | Notes |
|---|---|---|---|---|
| Base, core | 0.829 | 0.939 | 1.52e-5 | the selection scenario |
| Base, central | 0.930 | 0.992 | 0 | |
| Host component 7.6e-6 / 3.0e-5 | 0.875 / 0.721 | 0.969 / 0.844 | 7.6e-6 / 3.0e-5 | |
| δ = 0.001 / 0.003, core | 0.284 / 0.987 | 0.442 / 0.999 | | |
| Spread: proportional / uniform | 0.790 / 0.812 | | 2.14e-5 / 1.65e-5 | core |
| Spread: sparse / one ensemble | 0.720 / 0.738 | | 3.14e-5 / 3.14e-5 | core; the spread doubles the host component |
| τ = 0 | 0.903 | 0.933 | | |
| τ in Rr only (host-concentrated) | 0.314 (0.313) | 0.933 | | latent contrast 0.0009: the audit qualifies, as it should |
| τ in T only | 0.902 | | | latent contrast 0.0031 |
| Rr's draw at M4e's T − K value | 0.801 | | | |
| Rr at 0.0090 / 0.0031, ρ of the core | 0.622 / 0.956 | | | the base rate matters |
| Latent switches in Rr's unresolved, core | 0.799 | 0.933 | | the latent contrast is 0 |
| 12.6% overhead | 0.812 | | | 104 CPU hours |
| 1% invalid per panel (R = 1000) | 0.820 | | | |
| Unequal ensemble spreads, 5% invalid (R = 1000) | 0.743 | | | every run unbalanced |

- **The latent scenarios are a hazard to interpretation, not a loss of power.**
  - The unresolved sensitivities add 0.0253 of the unresolved genomes, not all of them. So they qualify only a few
    of these runs.
  - The envelope crosses zero in at least 99.9% of runs in every scenario, and in every run in most. For these
    simulations, the agreed wording therefore applies: the contrast in underlying separate states is unidentified.
    Simulation cannot say that this holds for every future outcome.
- **The unresolved-share measure is descriptive (Astra).**
  - Its zero-threshold flag fires in about 89% of baseline runs. The model carries the pilot's real Rr − T
    difference in unresolved shares, and the flag detects it correctly.
  - It is not a diagnostic for latent switches. M5 should report each arm's share, the difference and its
    interval, with no flag.
  - Fable proposes replacing it with a continuation sample in M5 itself, run to 100,000 ticks. That would bound the
    hazard directly; it is for M5's plan.
- **The exclusion** "no effect of 0.002 or more" holds at δ = 0 in 86% (core) and 98% (central) of runs. At
  δ = 0.002 it holds in 1.4% and 1.1%, below the nominal 2.5%.
- **The unbalanced reading covers the true protocol contrast** in 95.0% of 1000 runs under unequal ensemble spreads
  with 5% invalid panels.
- **The audit bound,** per run and pooled per arm, covers τ in 96% to 97% of runs.
  - Pooled with M4e's 2283 and 2286 audited genomes, it would cover in only 82% to 89%, since the H-setting
    scenario puts τ at the bound. So M5 uses its own audit.
  - It covers the realised hidden transitions in 94% to 96% of runs.

B's cheapest reads 0.829 central and 0.678 core as written, and 0.806 and 0.692 with Welch: rule B's known loss.

## 3. The false "raises" gate

**The gate** (design, section 4): R = 40,000 runs per null cell. For A and B, the one-sided 95% upper bound must be
at most 0.0275, for both the raw and the unqualified rate. Each selected allocation has eight null rows: four host
variances under a constant null, and the ± and ensemble nulls at the central and core scenarios.

**As written,** six of 32 cells fail, all on the raw rate, with upper bounds of 0.0278 to 0.0282:

| Selection | Failing rows |
|---|---|
| A's cheapest (135 hosts) | none |
| A's fewest (70 hosts) | half and core, constant |
| B's fewest (30 hosts) | central, constant |
| B's cheapest (95 hosts) | central and half, constant; core, ± |

Every unqualified rate is at most 1.6%. **C's nulls pass** their 0.030 tolerance (raw at most 2.65%, upper bound
0.0279).

**The pooled rates,** over the four selections:

| Pool | As written | Welch |
|---|---|---|
| All 32 cells, raw | 2.09% | 1.96% |
| Without the ensemble null (24 cells), raw | 2.52% (2.49% to 2.55%) | 2.36% (2.33% to 2.39%) |
| The same 24 cells, unqualified | 1.23% | 1.14% |

Draft 1 said "pooled over every null cell" of a rate that left the ensemble null out. Its 2.56% (2.53% to 2.60%)
was the restricted pool.

**The diagnosis, from the saved parts.** Averaged over the 16 constant-null cells, the parts are:
- the t alone: 2.53% "raises" and 2.40% "lowers";
- the bootstrap alone: 3.5% "raises" (4.6% at 30 hosts);
- the Welch t alone: 2.45%.

So the hull's raw rate is the t's. The t is approximately calibrated two-sided in these simulations, but leans
slightly toward "raises". The ensemble null's raw rate is far lower (0.1% to 1.4%): there the ensembles' effects
cancel, which the stratified t counts as signal variance.

**What a cell's gate can detect.**
- At R = 40,000, the upper bound sits about 0.0013 above the observed rate. So a cell passes only if its observed
  rate is at most about 2.62%.
- At a true rate of 2.52%, the pooled one, the sampling error alone puts about one cell in ten above that.
- That is roughly three of 32, against the six observed. So part of the as-written failure is the per-cell rule's
  own noise, and part is the t's lean.

**The two positions from round 1:**
- **Fable:** keep the reading and repair the gate (for example, a pooled per-allocation tolerance), and state
  M5's true raw rate, about 2.5%, in its pre-registration. The A-or-C flip was threshold noise.
- **Astra:** add the Welch t to the balanced hull, keep the tolerances, and recommend C if it holds after the
  fixes.

**My proposal for round 2:** adopt the Welch t (Astra's remedy).
- Fable's objection, that the reading choice flipped A and C, no longer holds. A is 135 hosts under both readings,
  and C wins under both.
- The Welch reading passes every cell of the gate as designed, with no change to the tolerances.
- What it costs:
  - B's cheapest needs 15 more hosts;
  - C's policy moves from 1 × 512 × 80 (95 to 145 hosts) to 1 × 512 × 40 (110 to 160 hosts), at the same expected
    cost.
- The change is made after seeing simulated nulls, not M5's data. It is the revisit the design anticipated ("the
  reading is revisited before M5's plan").
- M5's pre-registration should state the reading's simulated false "raises" rate (about 2.4% raw, 1.1% with all six
  readings) beside the nominal 2.5%.

## 4. Rule C

**The nominated allocation** has the lowest expected central cost among the allocations that reached the bound.
Every allocation reached it within the explored H_max.

| | As written | Welch |
|---|---|---|
| Allocation | 1 × 512 × 80 | 1 × 512 × 40 |
| H1 (B's H) / H_max | 95 / 145 | 110 / 160 |
| Runner-up's central cost | 1 × 512 × 40, 72.2 h (vs 71.3) | 1 × 512 × 80, 73.4 h (vs 72.2) |
| Cap (1.5 × the fixed-H mean cost at H_max) | 149 h | 145 h |

**Confirmed under all three core scenarios** at H_max and H_max + 5. C's family has K = 2, so each confirmation's
lower bound is taken at the 97.5% level. These are the Welch figures, R = 10,000; the as-written ones follow in
brackets.

| Scenario | Unqualified | Mean H | At H_max | Mean CPU h (p95) |
|---|---|---|---|---|
| Central | 0.841 [0.859] | 119 [104] | 0.2% | 72.0 (85.2) [71.2 (83.5)] |
| 7.6e-6 | 0.828 [0.841] | 136 [119] | 12% | 82.4 [81.6] |
| Core | 0.808 [0.820] | 150 [133] | 47% [43%] | 90.7 (99.5) [90.9 (101.6)] |
| Above (3.0e-5) | 0.747 [0.745] | 159 [143] | 91% [88%] | 96.1 [97.9] |
| 1% invalid per panel, core (R = 1000) | 0.830 [0.796] | 150 [133] | | 90.7 [90.8] |
| Unequal spreads, 5% invalid, core (R = 1000) | 0.757 [0.727] | 154 [138] | | 93.7 [94.6] |

- **Every run completed.** No run exceeded 1.25 times the mean cost.
- **The audit bounds:**
  - stage 1's covers τ in 96.6% to 97.9% of runs;
  - the final hosts' covers it in 96.0% to 97.7%.
- **The choice rule:**
  - as written: 71.2 h against A's 92.5 h, a saving of 23.0%;
  - with Welch: 72.0 h against 92.5 h, 22.1%.

  Both clear the 20% bar, so the rule recommends C.

## 5. What would go to the owner (after this round)

Proposed under the Welch reading; the as-written figures differ only for B and C's policy (section 4).

| Rule | Allocation (D, G, A) | Hosts | Mean CPU h | Cap | Power: central / core / 3.0e-5 |
|---|---|---|---|---|---|
| **C (recommended)** | 1, 512, 40 | 110 first, then up to 160 | 72 central, 91 core | 145 h | 0.84 / 0.81 / 0.75 |
| A | 1, 512, 80 | 135 | 92 | 139 h | 0.93 / 0.83 / 0.72 |
| B | 1, 512, 40 | 110 | 67 | 100 h | 0.81 / 0.69 / 0.60 |

Beside the table, the note to the owner gives:
- **A's fewest-host version:** 70 hosts at 187 hours, at 2 draws of 1024 genomes.
- **The 90% column:** A's cheapest needs 185 hosts at 127 hours.
- **The price of assuming τ at the bound:** about 95 hosts for A at τ = 0.
- **The identification limit,** in plain words: M5 can show more protocol-confirmed separate states under N2's
  wiring, but not the direction in underlying states. More hosts do not help with that.
- **The hardware:** CPU only, over several days. No GPU.

## Deviations and notes

- **The simulation's tests were written after its code** (rule 9 asks that each be seen failing first). The
  sabotages show that each can fail, but they do not make up for the order. The reading's tests, and every test
  added in round 1, were seen failing first.
- **The calibration bug.** The first full run calibrated δ on 200,000 sampled hosts, leaving +8e-6 (3.4 SE) of
  protocol contrast at δ = 0; it is kept as `power-sampled-calibration.json`. The calibration is now exact.
- **Two Monte Carlo sizes differ from the section's blanket R = 4000.** The two invalid-panel scenarios use
  R = 1000, since their unbalanced reading runs per run.
- **Refinement stops at the first candidate.** It starts at the lowest H within 0.1 of the goal in the coarse pass,
  and does not evaluate every near-target cell.
- **Probabilities over the 0.2 ceiling are rescaled, not rejected and redrawn.** This happened in at most one draw
  per scenario cell: 3 in all as written, 2 with Welch.
- **The coarse pass stops** an allocation's grid once its power exceeds 0.98. The H grid runs to 150 in the coarse
  pass and to 300 in the refinement.
- **Draft 1's envelope statement was wrong.** It said the envelope crosses zero "in every run" and gave a width of
  0.0078. Some δ = 0.004 cells cross in 99.9% of runs, and 0.0078 is the logical bound's unexpanded width, not the
  sampling envelope's (Astra). The outputs do not store the envelope's width, so this draft quotes none.
- **Round 1's archived results** are kept beside the new ones as `power-results-r1.json` and `.log`, in both output
  folders.

## Reproduce it

```
python scripts/memory_m5/m5_power_timing.py        # fixed-costs.json (minutes)
python scripts/memory_m5/m5_power.py               # every stage, about 45 minutes, runs/memory-m5-power/
M5_WELCH_TOO=1 M5_POWER_OUT=runs/memory-m5-power-welch python scripts/memory_m5/m5_power.py
python -m pytest tests/test_memory_m5_power.py
python scripts/memory_m5/sabotage_m5_power.py
```
