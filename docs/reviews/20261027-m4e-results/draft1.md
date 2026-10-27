# M4e: what does a dense block carry? — results

*Draft 1, 2026-10-27, before review.
Exploratory: the plan ([`M4E-PLAN.md`](M4E-PLAN.md), draft 4, agreed after three rounds; D367) fixed the hosts, the
arms, the genomes, the outcome, the second pass and the readings before any arm ran. Nothing here is a
pre-registration. Numbers come from `runs/memory-m4e/`:
- the hosts' records (`hosts.json`);
- the blocks' summary (`blocks-summary.json`; the full `blocks.json` stays local, below);
- one record per host, draw and arm (`arms/<host>__d<draw>__<arm>.json`);
- `coverage.json` (committed with the plan in 46869e7, before any arm ran);
- `readings.json` (written by [`m4e_read.py`](../../scripts/memory_m4/m4e_read.py); console output `read_log.txt`);
- `tables.json` (written after the data by [`m4e_tables.py`](../../scripts/memory_m4/m4e_tables.py) from those
  records, no simulation; console output `tables_log.txt`);
- the run's log `m4e_log.txt`.

Interpretations the plan did not fix are marked **after the data**.*

## In short

- **Δ_count lowers.** At N2's total weight on the head core's 30 neurons, with every edge of equal magnitude, spreading
  the weight over N2's 260 edges (U_HH) gives fewer separate-states genomes than putting it on the host's own 92 to
  126 (U_LH): 4 against 31 of 10,240. Δ_count = −0.0026 (95% interval −0.0041 to −0.0012), lower in 9 of the 10 hosts.
  The direction holds over every assignment of the unresolved genomes (envelope −0.0094 to −0.0004). The size does
  not: "at least 0.001" holds on the counted genomes but not on the envelope, so the size field reads "unresolved (the
  unresolved genomes decide it)". In the plan's words, a summary that grows with concentration (S2, S3) is favoured
  over the summed weight.
- **Δ_weight: direction unresolved; no effect of 0.004 or more, as a mean across these ten hosts (a response confined
  to a minority of host graphs may be missed).** At N2's edge count, raising the total weight from the host's (487 to
  771) to N2's (2347) changed little: 12 separate-states genomes (U_HL) against 4 (U_HH). Δ_weight = −0.0008 (−0.0017
  to +0.0001). The exclusion holds on the envelope too, the single-host guard does not fire, and the coverage
  simulation allowed exclusions to be read.
- **The second pass was used, and it decided Δ_count's direction.** The audit found no fading genome that became
  separate states, among 783 to 800 audited fading genomes per arm. On the first pass's classes alone, Δ_count's
  direction would have been "unresolved (the unresolved genomes decide it)". The longer hold settled 54 of the
  unresolved genomes as fading and 2 as separate states.
- **Beside the reading (not read):**
  - N2's uneven weights on the same random support raise the share over equal magnitudes (W − U_HH +0.0026,
    0.0008 to 0.0044, above zero on the envelope too).
  - N2's labelled degrees add more on the counted genomes (K − W +0.0023, 0.0004 to 0.0043), but not over every
    assignment of the unresolved genomes.
  - N2's exact block against K is unresolved (T − K +0.0020, −0.0020 to +0.0059).
  - N2's block raises the share over the intact host in all ten fresh hosts (T − I +0.0062, 0.0028 to 0.0095), as it
    did in M4d's ten.
- **What this does not show:** that a block stores the state, or anything about neurons outside C3. Eight
  constructions cannot separate correlated summaries, and a summary that fits is not a mechanism (the plan).

## The run

- **One invocation**, the three stages (`hosts`, `blocks`, `arms`), from 2026-10-26 02:19 to 2026-10-27 10:59 UTC, on
  the CPU of the tested machine (`m4e-attempt.json`, a copy of the local attempt record; `m4e_log.txt`; exit 0). The
  attempt record names commit 46869e7 (D367) at the start, with the code recorded clean, and the same commit at the
  end. No GPU.
- **Compute** (`m4e-compute-record.json`, a copy of the local `compute.json`): one attempt, completed, 2.25 × 10¹⁰
  neural updates and 117,571 s (32.7 h), category probe, inside the 48-hour cap and within the plan's 33 to 34 hours.
  The 160 panels took 32.5 h by the log: 3.1 to 3.2 h for each of I, U_LL, U_HL and U_HH, and 4.5 to 5.4 h for U_LH,
  W, K and T. The second pass took 10.2 h of it, for 6837 genomes. Panels took 517 to 1660 s each.
- **The hosts:** all ten from their first seeds, none skipped (SH-2011100, SH-2011101, SH-route-2021100,
  SH-route-2021101, SH-class-2031100, SH-class-2031101, SH-mirror-2041100, SH-mirror-2041101, SH-recip-2051100,
  SH-recip-2051101). Their C3 blocks hold 92 to 126 off-diagonal edges (weight 487 to 771, 5 to 29 reciprocal pairs;
  `hosts.json`).
- **The blocks** (`blocks-summary.json`; per arm, the range over the 20 host-draws):

  | Arm | Edges | Weight | Reciprocal pairs | S2 | S3 |
  |---|---|---|---|---|---|
  | I | 92 to 126 | 487 to 771 | 5 to 29 | 7.3 to 22.6 | 0.38 to 0.84 |
  | U_LL | 92 to 126 | 487 to 771 | 2 to 11 | 3.2 to 6.3 | 0.32 to 0.78 |
  | U_LH | 92 to 126 | 2347 | 2 to 11 | 54.7 to 75.0 | 1.31 to 1.57 |
  | U_HL | 260 | 487 to 771 | 32 to 46 | 1.1 to 2.9 | 0.21 to 0.78 |
  | U_HH | 260 | 2347 | 32 to 46 | 26.5 | 0.92 to 0.96 |
  | W | 260 | 2347 | 32 to 46 | 70.9 | 1.27 to 1.84 |
  | K | 260 | 2347 | 34 to 44 | 70.9 | 1.26 to 1.81 |
  | T | 260 | 2347 | 75 | 70.9 | 1.71 |

  S1 is the summed weight on the brain's scale (17.2 to 27.3 at the host's weight, 83.04 at N2's), S2 the summed
  squares, S3 the square root of the spectral radius of M∘M (the plan). K's reciprocal pairs were brought within 2 of
  W's in all 20 host-draws (`m4e_log.txt`; "matched" True every time).
- **The checks.** `m4e_read.py` and `m4e_tables.py` call `verify_run` before reading and stop on any failure. Both
  exited 0 (`read_log.txt`, `tables_log.txt`). `verify_run`:
  - regenerates the hosts and matches their content hashes;
  - rebuilds `blocks.json` and checks every block's rules;
  - checks that every arm leaves everything outside the block as the host's, and that the sham is exact;
  - checks that no magnitude is clamped and that the audit ids are as drawn;
  - validates every panel against its arm's hash, with both passes' columns and class codes.

  All 160 panels are valid.

## The reading

95% intervals each, 90% jointly (Bonferroni over the two). Each interval is the hull of the host bootstrap and the
Student-t interval. The envelope is the plan's: it covers every assignment of the still-unresolved genomes.

| Contrast | Mean | 95% interval | Hosts below / at / above 0 | Envelope | Direction | Size |
|---|---|---|---|---|---|---|
| **Δ_weight** (U_HH − U_HL) | −0.0008 | −0.0017 to +0.0001 | 4 / 6 / 0 | −0.0019 to +0.0004 | direction unresolved | no effect of 0.004 or more, as a mean across these ten hosts (a response confined to a minority of host graphs may be missed) |
| **Δ_count** (U_HH − U_LH) | −0.0026 | −0.0041 to −0.0012 | 9 / 0 / 1 | −0.0094 to −0.0004 | **lowers** | unresolved (the unresolved genomes decide it) |

**The rules, in order** (`readings.json`):
- **Δ_weight.** The interval contains 0, so its direction is unresolved. The interval lies inside (−0.004, 0.004), and
  so does the envelope, so the exclusion holds. The largest host difference is 0.0039, so the single-host guard (0.01)
  does not fire. The coverage simulation (`coverage.json`, before any arm) allowed exclusions to be read.
- **Δ_count.** The upper bound −0.0012 is below 0, so it lowers, and on the envelope the upper bound is −0.0004, so the
  direction stands. The upper bound is also below −0.001, so on the interval the size field reads "at least 0.001". On
  the envelope it reads "size unresolved" (upper −0.0004). Under the plan's rule a size sub-field stands only if it
  holds on both, and none does, so the size field reads "unresolved (the unresolved genomes decide it)". The largest
  host difference is 0.0059.

**The first pass alone** (reported beside it; `readings.json` "first_pass_reading"). The counted means and intervals
are the same, because the second pass changed no counted separate-states genome in either contrast's arms. The
envelope is wider: Δ_count −0.0121 to +0.0005, Δ_weight −0.0019 to +0.0006. On the first pass, Δ_count's direction
would read "unresolved (the unresolved genomes decide it)". U_LH carried 59 unresolved genomes after the first pass
and 39 after the second.

**Precision, as the plan expected.** The plan expected half-widths of 0.0012 to 0.0025, contrasts below about 0.003
mostly leaving the size unresolved, and power for spread effects of about 0.004 and more. Δ_count's half-width is
0.0015.

## The second pass

- **Used.** No audited fading genome became separate states, so the reading's classes are the second pass's wherever
  it ran (`second_pass_used` true, `audit_failed` empty). The audit covered 783 to 800 fading genomes per arm
  (`audited_fading_per_arm`). With about 800 and no transition, the plan's bound on an arm's transition rate is about
  0.0037 (one-sided 95%): enough at the 0.004 margin, not at the 0.001 benchmark (the plan).
- **The transitions** (first pass → second; every other genome the pass covered kept its class):

  | Arm | Unresolved → fading | Unresolved → separate states | Unresolved after both |
  |---|---|---|---|
  | I | 2 | 0 | 1 |
  | U_LL | 0 | 0 | 0 |
  | U_LH | 20 | 0 | 39 |
  | U_HL | 0 | 0 | 1 |
  | U_HH | 2 | 0 | 3 |
  | W | 8 | 1 | 31 |
  | K | 13 | 1 | 37 |
  | T | 9 | 0 | 33 |

  No separate-states, read-out-silent or oscillating genome changed class.

## Every class by arm

Pooled over the ten hosts, 10,240 genomes per arm, on the reading's classes:

| Arm | Separate states | Of which read-out silent | Fading | Persistent oscillation | Unresolved | Not settled |
|---|---|---|---|---|---|---|
| I | 12 | 0 | 10,227 | 0 | 1 | 1 |
| U_LL | 16 | 0 | 10,224 | 0 | 0 | 0 |
| U_LH | 31 | 0 | 10,166 | 4 | 39 | 43 |
| U_HL | 12 | 1 | 10,226 | 1 | 1 | 2 |
| U_HH | 4 | 0 | 10,233 | 0 | 3 | 3 |
| W | 31 | 0 | 10,175 | 3 | 31 | 34 |
| K | 55 | 0 | 10,138 | 10 | 37 | 47 |
| T | 75 | 1 | 10,102 | 30 | 33 | 63 |

**Per host** (separate states, unresolved in brackets, of 1024; `readings.json` "counts"):

| Host | I | U_LL | U_LH | U_HL | U_HH | W | K | T |
|---|---|---|---|---|---|---|---|---|
| SH-2011100 | 2 (0) | 8 (0) | 7 (3) | 5 (0) | 1 (0) | 0 (4) | 4 (5) | 17 (6) |
| SH-2011101 | 0 (0) | 0 (0) | 3 (5) | 0 (0) | 0 (0) | 2 (1) | 6 (2) | 3 (0) |
| SH-route-2021100 | 0 (0) | 0 (0) | 3 (10) | 0 (0) | 0 (0) | 0 (3) | 4 (5) | 7 (1) |
| SH-route-2021101 | 0 (0) | 0 (0) | 2 (5) | 0 (0) | 0 (0) | 3 (4) | 3 (3) | 5 (1) |
| SH-class-2031100 | 0 (0) | 0 (0) | 2 (2) | 0 (0) | 0 (0) | 2 (0) | 6 (1) | 12 (3) |
| SH-class-2031101 | 0 (0) | 0 (0) | 1 (3) | 1 (0) | 0 (0) | 6 (3) | 3 (2) | 10 (2) |
| SH-mirror-2041100 | 1 (0) | 4 (0) | 0 (1) | 2 (0) | 1 (1) | 2 (4) | 7 (7) | 2 (9) |
| SH-mirror-2041101 | 0 (0) | 0 (0) | 2 (0) | 0 (0) | 0 (0) | 5 (2) | 4 (3) | 6 (3) |
| SH-recip-2051100 | 9 (1) | 4 (0) | 5 (5) | 4 (1) | 2 (2) | 9 (3) | 14 (9) | 10 (5) |
| SH-recip-2051101 | 0 (0) | 0 (0) | 6 (5) | 0 (0) | 0 (0) | 2 (7) | 4 (0) | 3 (3) |
| **total** | 12 (1) | 16 (0) | 31 (39) | 12 (1) | 4 (3) | 31 (31) | 55 (37) | 75 (33) |

*After the data:* the low-coupling arms (I, U_LL, U_HL, U_HH) switch almost only in three hosts: SH-2011100,
SH-mirror-2041100 and SH-recip-2051100. In the other seven hosts they have 1 separate-states genome in 28,672. The
strong arms (U_LH, W, K, T) switch in nearly every host, and they hold almost all the genomes that do not settle (34
to 63 per arm, against 0 to 3).

## The descriptive contrasts (not read)

Each with the same interval and envelope as the reading (`readings.json` "secondary"):

| Contrast | What the two arms differ in | Mean | 95% interval | Hosts below / at / above 0 | Envelope |
|---|---|---|---|---|---|
| U_LH − U_LL | weight raised at the host's count | +0.0015 | −0.0004 to +0.0033 | 2 / 0 / 8 | −0.0007 to +0.0086 |
| U_HL − U_LL | count raised at the host's weight | −0.0004 | −0.0012 to +0.0004 | 2 / 7 / 1 | −0.0012 to +0.0006 |
| U_LL − I | equal-magnitude random wiring against the host's own (the construction check) | +0.0004 | −0.0015 to +0.0023 | 1 / 7 / 2 | −0.0018 to +0.0024 |
| W − U_HH | N2's uneven weights at fixed support and total | +0.0026 | 0.0008 to 0.0044 | 1 / 1 / 8 | 0.0005 to 0.0078 |
| K − W | N2's labelled degrees (reciprocity matched) | +0.0023 | 0.0004 to 0.0043 | 2 / 1 / 7 | −0.0036 to +0.0095 |
| T − K | N2's exact block against its labelled degrees | +0.0020 | −0.0020 to +0.0059 | 4 / 0 / 6 | −0.0070 to +0.0096 |
| T − I | N2's block against the host's own | +0.0062 | 0.0028 to 0.0095 | 0 / 0 / 10 | 0.0023 to 0.0131 |
| interaction (U_HH − U_HL − U_LH + U_LL) | | −0.0022 | −0.0038 to −0.0007 | | −0.0093 to +0.0001 |

The two-field labels the reader writes for these are in `readings.json`. Of note:
- W − U_HH reads "raises" on both the interval and the envelope.
- K − W reads "raises" on the interval only, so it reads "unresolved (the unresolved genomes decide it)".
- T − I reads "raises, at least 0.001" on both.
- T − K's single largest host difference is 0.0127 (SH-2011100).

**The dose model** (`readings.json` "dose"; the plan's rules):
- Six of the ten hosts have no slope. In each, every U-arm switch is in U_LH, the U arm with the largest S2, so the
  maximum-likelihood slope diverges, and the plan leaves such a host out.
- The four hosts with a slope (SH-2011100, SH-class-2031101, SH-mirror-2041100, SH-recip-2051100) give a mean slope on
  log S2 of −0.16 (−0.62 to +0.30).
- W's and K's deviations from their host's curve are +0.0018 (−0.0056 to +0.0093) and +0.0045 (−0.0029 to +0.0120),
  with W and K outside the U arms' S2 range in 3 hosts each.

*After the data:* the rule that leaves those hosts out removes exactly the hosts with the steepest pattern, all
switches at the largest S2. The four remaining hosts are the three with switches in the low-coupling arms, plus one
host with a single switch at each end of the S2 range. So the mean slope describes those four hosts, not the dose, and
should not be read as evidence against a rise with S2.

**The per-genome predictor** (`tables.json`; stage 0's largest real eigenvalue of the signed, scaled block; after the
data):
- The arm medians are 0.24 to 0.47 in I, U_LL and U_HL, 0.85 in U_HH, and 1.28 to 1.32 in U_LH, W, K and T.
- Within an arm it separates switching genomes weakly: AUC 0.41 to 0.66, and 0.17 in U_HH, whose 4 switches all sit
  below 0.8.
- Among genomes above 1.2, the share in separate states is 0.32% in U_LH (23 of 7255), 0.38% in W (25 of 6598), 0.66%
  in K (47 of 7164) and 0.96% in T (62 of 6456).

## What this means for the roadmap

*Interpretation, after the data.*
- **Concentration matters, and the summed weight alone does not set the rate.**
  - At equal magnitudes, the same total weight switched more on fewer, heavier edges (Δ_count).
  - Raising the total weight at N2's count did nothing measurable (Δ_weight), but raising it at the host's count
    tended upward (U_LH − U_LL +0.0015, 8 of 10 hosts).
  - The interaction is negative.
  - N2's uneven weights at the same support raised the share again (W − U_HH).

  Each of these moves with S2 and S3: U_HH's S3 (0.94) is below every strong arm's. So M4d's finding is read here as
  mostly a coupling-strength effect of how concentrated the block's weight is. These are eight constructions on one set
  of 30 neurons, and S2 and S3 are correlated across them, so neither is singled out (the plan).
- **The summaries do not collapse the strong arms.** U_LH, W, K and T have similar S2 (55 to 75) and per-genome
  predictor medians (1.28 to 1.32), but 31, 31, 55 and 75 separate-states genomes. Among genomes with the same
  predictor band, K and T still switch more than U_LH and W. Whether this is S3 (median 1.47, 1.45, 1.53, 1.71, in the
  same order) or the labelled degrees themselves, these arms cannot say. K − W is unresolved over the unresolved
  genomes, and T − K is unresolved outright.
- **T − I replicates M4d on fresh hosts:**

  | | M4d | M4e |
  |---|---|---|
  | T − I | +0.0059 | +0.0062 |
  | Hosts where T exceeds I | 10 of 10 | 10 of 10 |
  | T's count | 64 | 75 |
  | I's count | 4 | 12 |

  I's 12 come mostly from one host (SH-recip-2051100, 9).
- **For M5** (the plan's rules after the reading):
  - The count contrast moved the rate, so M5's controls must match the concentration of the weight. Equal-magnitude
    or summed-weight controls would build a coupling difference into the comparison. K-type controls (N2's weight
    multiset on N2's labelled degrees) match S1 and S2 by construction, but not S3, which stage 0 and this run show is
    higher for N2's block than for most rewired copies.
  - The strong arms carry 34 to 63 not-settled genomes per 10,240 even after a 22,000-tick hold, so M5 carries the
    second pass and a separate dynamics outcome.
  - T − K's host spread (standard deviation 0.0055 across hosts, against 0.0021 for Δ_count) is the input for M5's
    power calculation, the owner's third item. Strong host variation means more hosts, not more genomes (the plan).
- **The plan's limits stand.**
  - Ten hosts, two draws per host, and one set of neurons (C3).
  - The boundary, the exterior and the gap layer are the hosts'.
  - Random parameters, and one classifier, at the frozen horizon and at 22,000 ticks.
  - A null contrast here does not establish equivalence.
  - Location (a dense block on other neurons) and neuron-count size wait for a later stage.

## Deviations and notes

- **What ran:** no deviation from the plan. U_HX was dropped before any formal arm, by the plan's rule (the plan,
  "Decided 2026-10-26").
- **The reader's first invocation** wrote `readings.json`, dose model included, and then stopped with a
  `UnicodeEncodeError` printing "Δ" to the Windows console (cp1252). It was rerun with `PYTHONIOENCODING=utf-8`, and
  its `readings.json` was byte-identical to the first. `read_log.txt` is the second run's. The tables were run the
  same way. No code was changed after the data.
- **What is committed:** `blocks.json` stays local, as in M4d. W, K and T carry N2's C3 weights edge by edge, which
  rule 1 forbids committing. The committed `blocks-summary.json` gives each block's counts, weight, autapses,
  reciprocal pairs, degree ranges and S1 to S3, with the local file's sha256 (`706c53bc…`). K's and T's degrees are
  N2's and are reported as ranges only.
- **`tables.json`** holds every genome's predictor value and class. The predictor is a derived scalar of each genome's
  signed block, not an edge list or a weight.
- The interpretations of the per-host pattern, the dose model's excluded hosts, the predictor bands and everything
  under "What this means for the roadmap" are after the data. The plan fixed only the reading and the items reported
  beside it.

## Reproduce it

**Check the published records** (needs the fetched connectome; minutes):
```
py scripts/memory_m4/m4e.py hosts blocks      # regenerates the hosts (stops if they differ from hosts.json) and
                                              # writes the local blocks.json from its seeds
set PYTHONIOENCODING=utf-8                    # the reader prints "Δ"; a cp1252 console cannot
py scripts/memory_m4/m4e_read.py              # verify_run, then the reading from the committed panels
py scripts/memory_m4/m4e_tables.py            # stops if blocks.json's sha256 differs from blocks-summary.json's
```
With the committed panels in place, `m4e.py arms` validates and skips them rather than recomputing them. `m4e.py`
runs inside the compute accounting, so these checks append an attempt to the local, untracked `compute.json`. The
committed `m4e-compute-record.json` is the run's.

**A fresh run** (about 33 CPU hours here): set `MEMORY_M4E_OUT` to a new folder, then run, all with that same
`MEMORY_M4E_OUT`:
1. `py scripts/memory_m4/m4e_read.py coverage` (before any arm, as in the plan);
2. `py scripts/memory_m4/m4e.py`;
3. `py scripts/memory_m4/m4e_read.py`;
4. `py scripts/memory_m4/m4e_tables.py`.
