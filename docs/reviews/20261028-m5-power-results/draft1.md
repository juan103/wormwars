# M5's power calculation: results

*Draft 1, 2026-10-28, for review by Astra 6 and Fable 5.1 before the host count goes to the owner. The design is
[`M5-POWER-DESIGN.md`](M5-POWER-DESIGN.md) (draft 4). The script is
[`scripts/memory_m5/m5_power.py`](../../scripts/memory_m5/m5_power.py), with the reading in
[`m5_reading.py`](../../scripts/memory_m5/m5_reading.py). The outputs are `runs/memory-m5-power/power.json` (the
design as written) and `runs/memory-m5-power-welch/power.json` (one proposed change, section 3). Exploratory design
work; nothing here is a reading of M5. CPU only; each full run took about 40 minutes.*

## In short

- **The design's own rules flag two problems,** and both need the reviewers before the owner sees a count.
  - **The fixed-H rules' false "raises" gate fails.** Pooled over every null cell of the four selected allocations,
    the raw "raises" rate is 2.56% (95% interval 2.53% to 2.60%) against the nominal 2.5%. Per cell, the 95% upper
    bound exceeds the 0.0275 tolerance in some rows of every selected allocation. The unqualified rate is 1.2%.
    - The cause is the Student-t: false "lowers" run at 2.3%, so the t is nominal two-sided and skewed one-sided.
    - Adding the stratum-aware Welch t to the balanced hull brings the pooled rate to 2.39%, and every gate passes.
      It costs 0 to 10 hosts.
  - **The unresolved-share flag fires in about 88% of runs with nothing wrong,** because the pilot's Rr has more
    unresolved genomes than T. As defined, it carries no information.
- **The host counts** (80% unconditional power at a protocol effect of 0.002, mean CPU hours):

  | Rule | Allocation (D, G, A) | Hosts | CPU h (as written) | With Welch |
  |---|---|---|---|---|
  | A, cheapest | 1 × 512, 80 | 130 (Welch 140) | 88 | 95 |
  | A, fewest hosts | 2 × 1024, 160 | 65 | 173 | 173 |
  | B, cheapest | 1 × 512, 40 | 110 | 66 | 66 |
  | B, fewest hosts | 2 × 1024, 80 (Welch: 160) | 30 | 70 | 80 |
  | C (two-stage) | 1 × 512, 40 | 110 to 155 (Welch 160) | 72 central, 89 core | 72 central, 92 core |

- **The choice between A and C turns on the reading.** As written, C saves 19.1% against A under the central
  scenario, below the 20% threshold, so the rule recommends A. With the Welch t, A's cheapest needs 140 hosts, C
  saves 24.7%, and the rule recommends C.
- **The audit scenario sets much of the count.** At τ = 0, A's cheapest allocation needs about 95 hosts, not 130.
  The unqualified H exceeds the raw-only H by more than a third in 11 of 12 allocations. By the pre-registered
  reporting rule, M5's pre-registration must name the qualifier's noise as the reason when it fixes A.

## What ran

- `fit`: the pilot's inputs and fits. The logit host SD is 0.495 (T 0.492, Rr 0.497), Rr's draw SD 0.189 (the pilot's
  1.53e-6), the first-to-final table (T 9 of 42 and Rr 12 of 60 to fading, Rr 1 to oscillation, 1 in 153 to separate
  states), and the panel-time regression (time against first-pass unresolved count, correlation 0.76 in T and 0.90 in
  Rr). Fixed costs are 15.4 CPU seconds per host (`fixed-costs.json`, `m5_power_timing.py`).
- **The scenarios solve as the reviewers computed:** ρ = 0.616 for 7.6e-6, 0.193 for 1.52e-5, and ρ = 0 with σ²
  scaled by 1.53 for 3.0e-5. At the central ρ = 1, the implied per-arm count variances are 15.6 (T) and 16.4 (Rr),
  with a count correlation of 0.61; the pilot's were 22.5, 15.4 and 0.70, at T's higher rate.
- **The calibration check passes.** Every pilot value lies inside the simulated central 95%, at the pilot's fitted
  rates. The quantiles of the observed values are: SD 0.44, half-width 0.44, T's count variance 0.76, Rr's 0.60,
  correlation 0.70, unresolved 0.54 and 0.57. (Under the Welch variant the half-width's quantile is 0.11, because
  the hull it simulates is wider at ten hosts than the pilot's.)
- `families`, `nulls`, `scenarios`, `c`, `report`, as the design fixes them. K is 24 for A's and B's families and 2
  for C's.

## 1. The host counts by allocation (as written; 80%)

| (D, G, A) | A: hosts, CPU h | B: hosts, CPU h | A raw-only H | A at τ = 0 |
|---|---|---|---|---|
| 1, 512, 40 | 155, 93 | 110, 66 | 95 | 105 |
| 1, 512, 80 | 130, 88 | 100, 68 | 95 | 95 |
| 1, 512, 160 | 125, 105 | 90, 75 | 90 | 95 |
| 1, 1024, 40 | 115, 129 | 75, 84 | 60 | 75 |
| 1, 1024, 80 | 100, 120 | 60, 72 | 65 | 70 |
| 1, 1024, 160 | 90, 122 | 55, 75 | 60 | 70 |
| 2, 512, 40 | 100, 118 | 60, 71 | 60 | 65 |
| 2, 512, 80 | 90, 120 | 50, 67 | 60 | 70 |
| 2, 512, 160 | 85, 140 | 45, 74 | 60 | 70 |
| 2, 1024, 40 | 80, 175 | 40, 88 | 50 | 55 |
| 2, 1024, 80 | 75, 176 | 30, 71 | 50 | 55 |
| 2, 1024, 160 | 65, 173 | 30, 80 | 50 | 55 |

Every allocation was confirmed in both families. The raw-only and τ = 0 columns are coarse point estimates from
400 runs, descriptive. The 90% families need roughly 1.4 times the hosts (A's cheapest: 185 hosts, 126 CPU hours).

**Why so many more hosts than the orientation's 23 to 59:**
- **The success event:** six readings, not one. At A's cheapest allocation under the core scenario, raw "raises"
  holds in 92% of runs and the unqualified one in 80%. The audit qualifies 7.6% and the unresolved sensitivities
  3.0%.
- **The audit at the bound:** at τ = 0.00131 in both arms, the pooled-rate adjustment's noise qualifies true
  "raises", which is Fable's round-2 point 7.
- **D = 1, G = 512 is the cheapest per unit of power,** as Fable predicted, so the cheapest allocations use many
  small hosts. The fewest-host allocations (2 × 1024) cost about twice as much.

## 2. The selected allocations under the scenarios (as written; R = 4000, pointwise)

A's cheapest (1, 512, 80; 130 hosts), the unqualified "raises" rate:

| Scenario | Unqualified | Raw | Notes |
|---|---|---|---|
| Base, core (1.52e-5) | 0.798 | 0.922 | the selection scenario |
| Base, central | 0.915 | 0.986 | |
| Host component 3.0e-5 | 0.711 | 0.838 | |
| δ = 0.001 / 0.003 | 0.269 / 0.988 | 0.416 / 0.999 | core |
| Proportional / sparse / one-ensemble | 0.767 / 0.711 / 0.716 | | core |
| τ = 0 | 0.892 | 0.921 | |
| τ in Rr only (also host-concentrated) | 0.303 (0.323) | 0.933 | latent contrast 0.0009: the audit qualifies, as it should |
| τ in T only | 0.902 | | latent contrast 0.0031 |
| Rr's draw at M4e's T − K value | 0.775 | | |
| Rr at 0.0090 (0.0031), ρ of the core | 0.579 (0.952) | | the base rate matters |
| Latent switches in Rr's unresolved | 0.789 | | the protocol "raises" while the latent contrast is 0 |
| 12.6% overhead | 0.801 | | 99.7 CPU h |
| 1% invalid panels | 0.803 | | |

- **Unlike the rest of the table, the latent scenarios are a hazard, not a power loss.** When 0.002 of Rr's genomes
  are latent switches classified unresolved, M5 reads an unqualified "raises" in 79% of runs although the latent
  contrast is 0. The unresolved sensitivities qualify only 5.6%, since each adds 0.0253 of the unresolved
  genomes, not all of them.
  - The envelope crosses zero in every run of every scenario (its width is 0.0078). So the agreed wording, that the
    contrast in underlying separate states is unidentified, applies to every M5 outcome.
  - The unresolved-share flag fires in 100% of these runs, but also in about 88% of runs with no latent switches.
- **The exclusion** "no effect of 0.002 or more" holds in 83% (core) and 98% (central) of runs at δ = 0, and in 1.6%
  at δ = 0.002, below its nominal 2.5%.
- **The audit bound covers the realised hidden transitions** in 95% to 96% of runs per arm. Its coverage of the rate
  is reported per scenario.

B's cheapest (1, 512, 40; 110 hosts) reads 0.816 central and 0.699 core: rule B's known loss.

## 3. The false "raises" gate, and the proposal

**The gate** (design, section 4): per null cell, R = 40,000, the one-sided 95% upper bound at most 0.0275 for A and B.
It fails for all four selected allocations, in one to three of the six null rows each.

**The diagnosis.**
- *The calibration first.* The first full run (kept as `power-sampled-calibration.json`) calibrated δ on a sample of
  200,000 hosts. That left a protocol contrast of +8e-6 (3.4 SE) at δ = 0, so its null rates ran high. The
  calibration is now exact, by quadrature (`expected_raw`; `test_the_calibration_is_exact` against a million
  simulated hosts), and the null protocol contrast is within 1 SE of zero. Every number here is from the exact
  version.
- *What remains is the reading's.* Split by component at two allocations under the central null (R = 40,000):

  | | Bootstrap alone | t alone | Hull (as written) | Hull with Welch | t's false "lowers" |
  |---|---|---|---|---|---|
  | 1, 512, 80; H = 130 | 0.0292 | 0.0256 | 0.0252 | 0.0248 | 0.0238 |
  | 2, 1024, 80; H = 30 | 0.0465 | 0.0263 | 0.0263 | 0.0228 | 0.0230 |

  The stratified percentile bootstrap is anticonservative on its own (up to 4.7% at 6 hosts per ensemble). The hull
  hides that behind the t. The plain-s² t is nominal two-sided but skewed: about 2.6% "raises" against 2.3% "lowers".
  The per-host contrast is skewed, since Rr's counts carry the block-draw term and differ from T's in their
  unresolved and oscillation shares.

**The proposal** (`M5_WELCH_TOO=1`, off by default, tested): in the balanced case, the hull also takes the
stratum-aware Welch t that the unbalanced case already uses. The envelope gets the matching per-ensemble bound.
- Pooled null raw rate 2.39%, unqualified 1.11%; every gate passes.
- Selected H moves by 0 to 10 hosts: A's cheapest 130 → 140, B's fewest 2 × 1024 × 80 → 2 × 1024 × 160 at 30 hosts.
- C's H_max moves 155 → 160.

**The alternatives** I see, for the reviewers:
- (a) the Welch t in the balanced hull (the proposal);
- (b) keep the reading and widen the tolerance, accepting about 2.6%;
- (c) report raw "raises" only as qualified, so that M5's claims rest on the unqualified event (1.2% at zero);
- (d) a bias-corrected bootstrap in place of the percentile one.

Under the design's rule ("the reading is revisited before M5's plan"), this is that revisit. It is made after
seeing simulated nulls, not M5's data.

## 4. Rule C

- **The nominated allocation** is 1 × 512 × 40, at the lowest expected central cost among the twelve, each of which
  reached the bound at 1.52e-5.
- **Its parameters:** H1 = 110 (B's), H_max = 155 (160 with Welch), with the cap at 1.5 times the fixed-H mean cost
  at H_max.
- **Confirmed under all three core scenarios:**

  | Scenario | Unqualified | Mean H | Mean CPU h (p95) |
  |---|---|---|---|
  | Central | 0.842 | 119 | 72 (84) |
  | Core | 0.809 | 148 | 89 (96) |
  | Above (3.0e-5) | 0.733 | 154 | 93 (97) |

  It reaches H_max in 1% of central runs, 61% of core runs and 95% of runs above the range.
- **C's nulls pass its 0.030 tolerance.** Its raw rates are 2.5% to 2.6%, the same t skew.
- **The choice rule:** C's central cost is 71.6 h against A's 88.4 h, a saving of 19.1%, under the 20% bar, so it
  recommends A. With the Welch t: 71.7 h against 95.3 h, 24.7%, so C.
- An adaptive rule is sensitive to a choice like this. If C is offered, the owner should see both numbers.

## 5. What the owner will be asked (after this review)

A host count and its CPU cost, from:
- **A** (robust to the core range): 130 to 140 hosts, 88 to 95 CPU hours, at 1 draw of 512 genomes and an audit of
  80 ids per panel;
- **C** (adaptive): 110 hosts first, then up to 155 to 160; 72 hours expected if the pilot's spread holds, 89 to 92
  at the core range;
- **B** (cheapest, underpowered at the core range): 110 hosts, 66 hours, 70% power at the core range.
- Beside them: the fewest-host versions (65 hosts at 173 hours for A), and the price of the τ-at-the-bound
  assumption (about 95 hosts for A at τ = 0).

All three fit the CPU over several days. None needs the GPU.

## Deviations and notes

- **The simulation's tests were written after its code** (rule 9 asks for each test to be seen failing first).
  `scripts/memory_m5/sabotage_m5_power.py` shows that each can fail: 17 of 17 sabotages fail their tests by
  assertion (`runs/m5-power-sabotage.txt`). The reading's tests (`m5_reading.py`) were seen failing first.
- **The calibration bug** (section 3), found by the gate and fixed before these results.
- **A reporting bug,** fixed: the envelope and the unresolved flag were computed only for runs with every panel
  valid, which are 7% of runs in the 1%-invalid scenario. Unbalanced runs now get MR.envelope. The baseline's
  scenarios stage was rerun (`power-scenarios2.log`).
- **The raw-only and τ = 0 host counts** are coarse (R = 400) point estimates, as the design's descriptive column.
- **The coarse pass stops** an allocation's grid once its power exceeds 0.98. The H grid ran to 150 in the coarse
  pass and to 300 in the refinement.

## Reproduce it

```
python scripts/memory_m5/m5_power_timing.py        # fixed-costs.json (minutes)
python scripts/memory_m5/m5_power.py               # every stage, about 40 minutes, runs/memory-m5-power/
M5_WELCH_TOO=1 M5_POWER_OUT=runs/memory-m5-power-welch python scripts/memory_m5/m5_power.py
python -m pytest tests/test_memory_m5_power.py
python scripts/memory_m5/sabotage_m5_power.py
```
