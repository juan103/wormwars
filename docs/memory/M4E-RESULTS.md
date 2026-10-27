# M4e: what does a dense block carry? — results

*Draft 4, 2026-10-27, after three rounds of review (Astra 6 and Fable 5.1: both "fix then publish" in rounds 1 and 2,
both "agree" in round 3, whose two minor wording points are taken here; every finding taken; drafts 1 to 3 and the
reviews are archived in [`docs/reviews/20261027-m4e-results/`](../reviews/20261027-m4e-results/)).
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

In review, Astra regenerated the constructions, validated the panels and reproduced the readings, the tables and the
block file's digest; Fable checked every entry against the committed files and matched the digest. Interpretations
the plan did not fix are marked **after the data**.*

## In short

- **Δ_count lowers.** At N2's total weight on the head core's 30 neurons, with every edge of equal magnitude, spreading
  the weight over 260 random edges, N2's count (U_HH), gives fewer separate-states genomes than putting it on 92 to
  126 random edges, the host's count (U_LH): 4 against 31 of 10,240. Δ_count = −0.0026 (95% interval −0.0041 to −0.0012), lower in 9 of the 10 hosts.
  - **The direction holds over every assignment of the unresolved genomes, but only just.** The envelope runs from
    −0.0094 to −0.0004, and −0.0004 is about four genomes in 10,240. The second pass settled 20 of U_LH's and 2 of
    U_HH's unresolved genomes as fading, which narrowed the envelope enough to clear zero. Astra recomputed it with
    each arm's settlements applied alone (`r2-astra.md` in the review archive): U_LH's alone clear it (−0.0001), and
    U_HH's alone do not (+0.0002). On the first pass alone the direction would be "unresolved (the unresolved genomes
    decide it)".
  - **The size does not hold.** "At least 0.001" holds on the counted genomes but not on the envelope, so the size
    field reads "unresolved (the unresolved genomes decide it)".
- **Δ_weight: direction unresolved; no effect of 0.004 or more, as a mean across these ten hosts (a response confined
  to a minority of host graphs may be missed).** At N2's edge count, raising the total weight from the host's (487 to
  771) to N2's (2347) gave 4 separate-states genomes (U_HH) against 12 (U_HL). Δ_weight = −0.0008 (−0.0017 to
  +0.0001). The exclusion holds on the envelope too, the single-host guard does not fire, and the coverage simulation
  allowed exclusions to be read.
- **The second pass was used.** The audit found no fading genome that became separate states, among 783 to 800
  audited fading genomes per arm. The longer hold settled 54 of the unresolved genomes as fading and 2 as separate
  states.
- **Beside the reading (not read):** the equal-magnitude blocks at N2's count and weight do not reproduce N2's
  block's effect. U_HH is the lowest of the eight arms, pooled (U_HH − I −0.0008). That difference has no interval in
  `readings.json`, and one host dominates it (SH-recip-2051100: 9 against 2). N2's block's rise over the intact host
  arrives in three steps of similar size:

  | Step | Mean | 95% interval | Over every assignment of the unresolved genomes |
  |---|---|---|---|
  | N2's uneven weights on the same random support (W − U_HH) | +0.0026 | 0.0008 to 0.0044 | above zero, just (0.0005, about five genomes) |
  | N2's labelled degrees (K − W; S1 and S2 fixed) | +0.0023 | 0.0004 to 0.0043 | unresolved |
  | N2's exact block against K (T − K; S1 and S2 fixed) | +0.0020 | −0.0020 to +0.0059 | unresolved |

  N2's block raises the share over the intact host in all ten fresh hosts (T − I +0.0062, 0.0028 to 0.0095), as it
  did in M4d's ten.
- **What this does not show:** that a block stores the state, or anything about neurons outside C3. Eight
  constructions cannot separate correlated summaries, and a summary that fits is not a mechanism (the plan).

## The run

- **One invocation**, the three stages (`hosts`, `blocks`, `arms`), from 2026-10-26 02:19 to 2026-10-27 10:59 UTC, on
  the CPU of the tested machine (`m4e-attempt.json`, a copy of the local attempt record; `m4e_log.txt`; exit 0). The
  attempt record names commit 46869e7 (D367) at the start, with the code recorded clean, and the same commit at the
  end. No GPU.
- **Compute** (`m4e-compute-record.json`, a copy of the local `compute.json`): one attempt, completed, 2.25 × 10¹⁰
  neural updates and 117,571 s (32.7 h), category probe. That is inside the 48-hour cap and just under the plan's 33
  to 34 hours.
  - By the log, the 160 panels took 32.5 h: 3.1 to 3.2 h for each of I, U_LL, U_HL and U_HH, and 4.5 to 5.4 h for
    each of U_LH, W, K and T.
  - The second pass took 10.2 h of that, for 6837 genomes.
  - Single panels took 517 to 1660 s.
- **The hosts:** all ten from their first seeds, none skipped (SH-2011100, SH-2011101, SH-route-2021100,
  SH-route-2021101, SH-class-2031100, SH-class-2031101, SH-mirror-2041100, SH-mirror-2041101, SH-recip-2051100,
  SH-recip-2051101). Their C3 blocks hold 92 to 126 off-diagonal edges (weight 487 to 771, 5 to 29 reciprocal pairs;
  `hosts.json`).
- **The blocks** (`blocks-summary.json`; per arm, the range over the 20 host-draws):

  | Arm | Edges | Weight | Reciprocal pairs | Autapses | S2 | S3 |
  |---|---|---|---|---|---|---|
  | I | 92 to 126 | 487 to 771 | 5 to 29 | 2 to 4 | 7.3 to 22.6 | 0.38 to 0.84 |
  | U_LL | 92 to 126 | 487 to 771 | 2 to 11 | 2 to 4 | 3.2 to 6.3 | 0.32 to 0.78 |
  | U_LH | 92 to 126 | 2347 | 2 to 11 | 2 to 4 | 54.7 to 75.0 | 1.31 to 1.57 |
  | U_HL | 260 | 487 to 771 | 32 to 46 | 2 to 4 | 1.1 to 2.9 | 0.21 to 0.78 |
  | U_HH | 260 | 2347 | 32 to 46 | 2 to 4 | 26.5 | 0.92 to 0.96 |
  | W | 260 | 2347 | 32 to 46 | 2 to 4 | 70.9 | 1.27 to 1.84 |
  | K | 260 | 2347 | 34 to 44 | 2 to 4 | 70.9 | 1.26 to 1.81 |
  | T | 260 | 2347 | 75 | 8 | 70.9 | 1.71 |

  S1 is the summed weight on the brain's scale (17.2 to 27.3 at the host's weight, 83.04 at N2's), S2 the summed
  squares, and S3 the square root of the spectral radius of M∘M (the plan). K's reciprocal pairs were brought within 2
  of W's in all 20 host-draws (`m4e_log.txt`; "matched" True every time).
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
Student-t interval. The envelope is the plan's: it covers every assignment of the genomes the classifier left
unresolved.

| Contrast | Mean | 95% interval | Hosts below / at / above 0 | Envelope | Direction | Size |
|---|---|---|---|---|---|---|
| **Δ_weight** (U_HH − U_HL) | −0.0008 | −0.0017 to +0.0001 | 4 / 6 / 0 | −0.0019 to +0.0004 | direction unresolved | no effect of 0.004 or more, as a mean across these ten hosts (a response confined to a minority of host graphs may be missed) |
| **Δ_count** (U_HH − U_LH) | −0.0026 | −0.0041 to −0.0012 | 9 / 0 / 1 | −0.0094 to −0.0004 | **lowers** | unresolved (the unresolved genomes decide it) |

**The rules, in order** (`readings.json`):
- **Δ_weight.** The interval contains 0, so the direction is unresolved. Both the interval and the envelope lie inside
  (−0.004, 0.004), so the exclusion holds. The largest host difference is 0.0039, so the single-host guard (0.01)
  does not fire. The coverage simulation (`coverage.json`, before any arm) allowed exclusions to be read.
- **Δ_count.**
  - The upper bound, −0.0012, is below 0, so the contrast lowers. On the envelope the upper bound is −0.0004, so the
    direction stands.
  - The upper bound is also below −0.001, so on the interval the size field reads "at least 0.001". On the envelope
    it reads "size unresolved".
  - Under the plan's rule, a size sub-field stands only if it holds on both. None does, so the size field reads
    "unresolved (the unresolved genomes decide it)". The largest host difference is 0.0059.

**The first pass alone** (reported beside it; `readings.json` "first_pass_reading"):
- The counted means and intervals are the same, because the second pass changed no counted separate-states genome in
  either contrast's arms.
- The envelope is wider: Δ_count −0.0121 to +0.0005, Δ_weight −0.0019 to +0.0006.
- On the first pass, Δ_count's direction would read "unresolved (the unresolved genomes decide it)". U_HH had 5
  unresolved genomes after the first pass and 3 after the second; U_LH had 59 and 39.

**Precision, as the plan expected.** The plan expected half-widths of 0.0012 to 0.0025, contrasts below about 0.003
mostly leaving the size unresolved, and power for spread effects of about 0.004 and more. Δ_count's half-width is
0.0015.

## The second pass

- **Used.** No audited fading genome became separate states, so the reading's classes are the second pass's wherever
  it ran (`second_pass_used` true, `audit_failed` empty). The audit covered 783 to 800 fading genomes per arm
  (`audited_fading_per_arm`). With no transition, each arm's transition rate is bounded below 0.0037 to 0.0038
  (one-sided 95%). That is enough at the 0.004 margin but not at the 0.001 benchmark (the plan). Bounding a rate below
  0.001 would take about 3000 audited fading genomes per arm (Astra).
- **What the envelope does not cover.** It covers the genomes left unresolved, given every other genome's class. It
  does not allow for transitions the audit could have missed among unaudited fading genomes (Astra).
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

  No separate-states, read-out-silent or oscillating genome changed class. The second pass settled 56 of the 201
  first-pass unresolved genomes (28%). The smoke's estimate of its cost was about 75 s per unresolved genome
  processed, settled or not.

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

*After the data:*
- The low-coupling arms (I, U_LL, U_HL, U_HH) switch almost only in three hosts: SH-2011100, SH-mirror-2041100 and
  SH-recip-2051100. These are the three hosts where the intact host itself switches. In the other seven hosts the four
  arms have 1 separate-states genome in 28,672. This is consistent with a host-dependent baseline that the
  low-coupling blocks do not raise. It does not locate that baseline's source: these arms keep the host's autapses
  inside C3, and each host has its own genome panel. It is a description, not an established subgroup (Fable, Astra).
- The strong arms (U_LH, W, K, T) switch in nearly every host, and they hold almost all the genomes that do not
  settle: 34 to 63 per arm, against 0 to 3.

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
- T − K's largest single host difference is 0.0127 (SH-2011100).
- The interaction's interval is below zero, but its envelope reaches +0.0001, so its sign holds on the counted
  genomes only, not over every assignment of the unresolved ones.

**T − K is not exact wiring alone.** T carries N2's 8 autapses and 75 reciprocal pairs, while K keeps the host's 2 to
4 autapses and has 34 to 44 reciprocal pairs (matched to W, not to T). T − K is therefore a package: N2's exact
off-diagonal wiring, its autapses and its reciprocity together (Astra).

**The dose model** (`readings.json` "dose"; the plan's rules):
- Six of the ten hosts have no slope. In each, every U-arm switch is in U_LH, the U arm with the largest S2, so the
  maximum-likelihood slope diverges, and the plan leaves such a host out.
- The four hosts with a slope (SH-2011100, SH-class-2031101, SH-mirror-2041100, SH-recip-2051100) give a mean slope on
  log S2 of −0.16 (−0.62 to +0.30).
- Over those four hosts, W's and K's mean deviations from their host's curve are +0.0018 (−0.0056 to +0.0093) and
  +0.0045 (−0.0029 to +0.0120). In 3 of the four, W's and K's S2 lies outside the U arms' range, so the check
  extrapolates.

*After the data:*
- The rule leaves out the six hosts that show positive separation at the boundary, all their U-arm switches at the
  largest S2. Their sparse counts do not establish a precisely steep response (Astra).
- The four hosts that remain are the three where the low-coupling arms switch, plus one host with a single switch at
  each end of the S2 range.
- Given those exclusions and the sparse sampling of S2, the mean slope is uninformative about the overall response.
  It is not evidence against a rise with S2.

**The per-genome predictor** (`tables.json`; stage 0's largest real part of the eigenvalues of the signed, scaled
block; after the data):
- The arm medians are 0.24 to 0.47 in I, U_LL and U_HL, 0.85 in U_HH, and 1.28 to 1.32 in U_LH, W, K and T.
- Within an arm it separates switching genomes weakly: AUC 0.41 to 0.66, and 0.17 in U_HH, whose 4 switches all sit
  below 0.8.
- Among genomes at 1.2 and above, the share in separate states is 0.32% in U_LH (23 of 7255), 0.38% in W (25 of
  6598), 0.66% in K (47 of 7164) and 0.96% in T (62 of 6456). The predictor's medians within that band rise in the
  same order (1.38, 1.39, 1.42, 1.46). Astra computed these from the saved per-genome values; `tables.json` itself
  stores only each arm's overall median and the band counts.
- In the band from 1.0 to 1.2 the four arms are alike: 0.30%, 0.17%, 0.32% and 0.31%.
- `tables.json` saves each genome's value rounded to five decimals, while the bands use full precision. Thresholding
  the saved U_LH values at 1.2 therefore gives 7256 rather than 7255 (Astra).

## What this means for the roadmap

*Interpretation, after the data.*
- **Changing how concentrated the weight is changes how often genomes switch, on these 30 neurons.**
  - Spreading a fixed weight over more equal-magnitude edges lowered the rate (Δ_count).
  - Putting N2's uneven weights on a fixed support raised it (W − U_HH).

  Both hold over every assignment of the unresolved genomes, by thin margins (about four and five genomes). That makes a coupling-based explanation of part of the transplant benefit plausible. How much of the benefit it
  explains is unresolved (Astra).
- **The arm averages look threshold-like rather than graded** (Fable):
  - Every block with S3 below 1 (I, U_LL, U_HL, U_HH) sits at a similar low rate, including U_HH, whose S2 is 9 to 23
    times U_HL's. This is consistent with Δ_weight's unresolved direction and small counted difference (Astra).
  - The rate rises only in the four arms with S3 of 1.26 and above.
  - No arm has S3 between 0.96 and 1.26, so these arms cannot locate a threshold, or tell a step from a steep rise.
  - The per-genome predictor neither confirms nor refutes a step. Below 1.0 the strong arms have only 354 to 629
    genomes, with 0 to 3 switches, and their within-arm AUCs are 0.60 to 0.66.
  - U_HH, at N2's count and weight with equal magnitudes, does not reproduce any of N2's block's effect.
- **Similar summary values coexist with different rates.** U_LH, W, K and T have similar S2 (55 to 75) and predictor
  medians (1.28 to 1.32) but 31, 31, 55 and 75 separate-states genomes. Above 1.2, K and T switch more than U_LH and W.
  These comparisons cannot say whether a common relationship with some summary explains the differences: in that band
  the predictor's medians also rise in the same order, and the hosts' make-up differs (Astra). S3 (medians 1.47, 1.45,
  1.53, 1.71) orders the four arms weakly, but S3, the labelled degrees, the placement of the weights, reciprocity and
  autapses are entangled in these arms. K − W is unresolved over the unresolved genomes, and T − K is unresolved
  outright.
- **T − I replicates M4d on fresh hosts:**

  | | M4d | M4e |
  |---|---|---|
  | T − I | +0.0059 | +0.0062 |
  | Hosts where T exceeds I | 10 of 10 | 10 of 10 |
  | T's count | 64 | 75 |
  | I's count | 4 | 12 |

  I's 12 come mostly from one host (SH-recip-2051100, 9).
- **For M5.** These are inputs to M5's plan and power calculation (the owner's third item), not a plan.
  - **Two estimands** (the plan's "total wiring advantage" and "residual beyond a summary"; Astra, Fable):
    - T − K, the advantage over a null with N2's weights on N2's labelled degrees, including whatever S3 carries.
    - T − K_S3, against K draws whose S3 is matched to T's by rejection. This is the residual beyond that summary
      (Fable). Two of this run's 20 K draws were within 0.05 of T's S3 (1.714), which suggests roughly ten proposals
      per accepted draw at that tolerance. The acceptance rate and the cost need reassessing for M5's chosen controls,
      especially if they also match autapses or reciprocity (Astra).

    S3 itself depends on the wiring, so a null residual would not show that the wiring has no total effect. M5 must
    also either match T's autapses and reciprocity in the controls or keep T − K as a package estimand.
  - **The target before the power** (Astra). M5 must choose its primary estimand or estimands, and its success
    criterion, before calculating power. Detecting a positive effect, establishing one of at least 0.001 and
    excluding 0.004 are different targets. If both contrasts are primary, the calculation must account for
    multiplicity. The S3-matched control needs its own variance estimate; T − K's cannot be carried over.
  - **The unresolved genomes come before the power calculation** (Fable, Astra). The envelope shifts each host's
    difference by the arm's unresolved share, and more hosts do not shrink that shift. In this run's T − K, the 20
    counted excess switches, 37 unresolved K genomes and 33 unresolved T genomes bound the mean between −0.0017 and
    +0.0052 before any sampling uncertainty. M5's plan must fix how unresolved genomes are treated first. The choices
    are a budget for the unresolved rate with a longer or further pass, or a reading on the resolved genomes with each
    arm's unresolved share as its own outcome and the envelope as a sensitivity check. The audit must also be sized
    for the target effect.
  - **The variance.**
    - T − K's spread across hosts is a standard deviation of 0.0055 here, and M4d's T − R was 0.0035, both at 1024
      genomes per host (Fable).
    - With ten hosts the estimate is uncertain, roughly 0.7 to 1.8 times itself.
    - Astra's rough decomposition of the variance of the estimated host contrasts: about 51% between hosts, 8%
      between draws and 41% genome sampling. It is not pure host heterogeneity, and it is very uncertain with ten
      hosts and two draws.
    - So independent hosts come first, but genomes are not worthless. Under that decomposition, doubling the genomes
      at a fixed number of draws multiplies the spread by about 0.89. Allocation should be compared with the paired
      data.
  - **Orientation only** (the reviewers' reference calculations, archived): at a host spread of 0.0055, a paired
    two-sided test at 5% with 80% power needs about 17 hosts for an effect of 0.004, about 60 for 0.002 and about 240
    for 0.001. That ignores the unresolved genomes and the guard. M5's calculation should simulate the whole reading
    procedure, unresolved genomes included, at effects of 0, 0.001, 0.002 and 0.004 and under sparse host responses.
    It should not choose its target from this run's +0.0020.
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
  `UnicodeEncodeError` printing "Δ" to the Windows console (cp1252). It was rerun with `PYTHONIOENCODING=utf-8`.
  `cmp` found its `readings.json` byte-identical to a copy of the first. That copy was not kept in the repository, so
  this is a reported check, not a committed one (Astra). `read_log.txt` is the second run's. The tables were run the
  same way. No code was changed after the data.
- **What is committed:** `blocks.json` stays local, as in M4d.
  - W, K and T carry N2's C3 weights edge by edge, which rule 1 forbids committing.
  - The committed `blocks-summary.json` gives each block's counts, weight, autapses, reciprocal pairs, degree ranges
    and S1 to S3, with the local file's sha256 (`706c53bc…`).
  - K's and T's degrees are N2's, so they are reported as ranges only.
  - Both reviewers found no rule-1 problem in the committed records.
- **`tables.json`** holds every genome's predictor value (rounded to five decimals) and class. The value is a derived
  scalar of each genome's signed block, not an edge list or a weight.
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
