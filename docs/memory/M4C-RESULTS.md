# M4c: is RIA's part of the switch more than its weight? — results

*Draft 3, 2026-10-23, after two rounds of review (Astra 6 and Fable 5.1: both "fix then publish" in round 1, both
"agree" in round 2 with small findings, all taken; drafts 1 and 2 and the reviews are archived in [`docs/reviews/20261023-m4c-results/`](../reviews/20261023-m4c-results/)). Exploratory: the plan ([`M4C-PLAN.md`](M4C-PLAN.md), draft 3, agreed after two
rounds; D361) fixed the genomes, the arms, the controls, the outcome and the reading before any arm ran. Nothing here is
a pre-registration. Numbers come from `runs/memory-m4c/`: the census records of the fresh panels (`census/<panel>.json`),
`sets.json`, the panel records (`<panel>.json`), `readings.json` (written by
[`m4c_read.py`](../../scripts/memory_m4/m4c_read.py); console output `read_run.txt`), and `tables.txt`, written after
the data by [`m4c_tables.py`](../../scripts/memory_m4/m4c_tables.py) from those records and N2's local wiring (no
simulation). Interpretations the plan did not fix are marked **after the data**.*

## In short

- **The reading is positive: "RIA's core edges erase the switch more often than every weight-matched control
  family".** On 141 fresh N2 switch genomes, cutting RIAR's 26 C3-internal edges for 30 ticks sends both histories
  into one basin in 72% of them, and RIAL's 29 edges in 58%. Edge sets of the same summed anatomical weight erase 22%
  to 30%, whichever of the three fixed schemes draws them. All six differences are +0.32 to +0.46, and their 90%
  intervals' lower bounds (0.23 to 0.38) are above the margin of 0.10.
- **No single control set reaches either side** (60 sets per side): the largest erases 46% (an exterior set, against
  RIAR's 72%) and 42% (against RIAL's 58%).
- **M4b's dissection repeats on fresh genomes** (description): RIAR and RIAL erase 0.716 and 0.582, against M4b's
  0.714 and 0.607 on its 28 genomes. The order of C3's 30 neurons, each cut alone, correlates with M4b's at Spearman
  +0.86.
- **The descriptive arms point the same way** (not read). The heaviest 26 or 29 core edges avoiding RIA carry more
  weight than RIA's (1.07 and 1.27 times), and for RIAL also more squared weight (1.11 times). They erase 47 and 48 of
  the 141; the two sets are nested (RIAL's 29 contain RIAR's 26), so this is close to one observation (Fable). The only
  other neurons whose edges admit a same-count, edge-by-edge matched set within 5% of RIA's weight are AVAL and AVAR
  (AVAR for RIAR, both for RIAL; Fable); those sets (26 or 29 of their 106 edges not touching RIA) erase 2 to 4. RIA's non-core edges (298 and 331 of weight)
  erase 49 (RIAR) and 36 (RIAL).
- **What this does not show:** that RIA stores the switch. The result is about N2 alone, a 30-tick cut, and three
  sampling schemes, none of which removes one core neuron's chemical connections inside the core, as cutting RIA does.
  Even that cut leaves RIA's gap junctions and RIAR's autapse in place (Astra).

## The run

- **The census** ran from 2026-10-23 15:55 to 18:47 UTC (2.9 h) on the CPU of the tested machine. It was started
  during the plan's review round 1, as the plan discloses. Its attempt record (`m4c-attempt-census.json`, a copy of
  the local one) names commit f2c025c with a dirty tree, and 69fb86a at its end: D361 was committed while the census
  ran, and the process ran the 15:55 version of `m4c.py` throughout. **That version is not archived** (Fable). What can
  be checked: between f2c025c and 69fb86a only the M4c plan, code, tests, reviews and records changed (`DECISIONS.md`,
  `docs/memory/M4C-PLAN.md`, `MEMORY-ROADMAP.md`, the review archive, `scripts/memory_m4/m4c.py`, `m4c_read.py`,
  `sabotage_m4a.py`, `README.md`, `tests/test_memory_m4a.py` and two test logs; `git diff --name-only`), so M2's census
  code and the library are the same; plan draft 1 (archived) describes the same census computation as draft 3 (seeds,
  panel size, C1 skipped, `census.run_panel`, role "fresh"); review rounds 1 and 2 changed only how the records are
  checked and used. The committed code's `census_record` checked every record's metadata and array alignment before
  every arm and on reading; that is not a check that the executed code was the committed one (Astra).
- **The sets and the arms** ran from 18:47 to 21:38 UTC (2.9 h) at commit 69fb86a (D361), clean tree, panels in order
  (`m4c-attempt-arms.json`; `m4c_arms_log.txt`, a copy of the local `arms.log`; exit 0). `sets.json` was rebuilt and matched the plan's numbers
  (X ratios 0.980 to 1.020; W 67 to 99 edges; C ratios 0.980 to 1.018; C's acceptance 0.10 and 0.33).
- **Compute** (`m4c-compute-record.json`, a copy of the local `compute.json`): two attempts, both completed, 2.19 ×
  10⁹ neural updates and 20 589 s in all, category probe (census 1.32 × 10⁹ and 10 302 s; arms 8.66 × 10⁸ and
  10 287 s). Slower than planned (about 5.7 h against 5), probably because the CPU was shared for part of the run (census chunks
  took 100 s at first and up to 420 s later). No GPU.
- **The genomes:** all 8 panels valid (none dropped); 141 separate-states genomes (19, 19, 17, 26, 14, 21, 12, 13 per
  panel; `m4c_census_log.txt`), so the four extra panels were not needed.
- **Every check passed.** Every panel's genome ids equal its census's separate-states genomes; all 165 arms complete,
  none extra; the side arms equal their dissection arms; every genome's intact arm kept both roots (141 of 141); every
  set passed its rules on rebuilding.

## The reading

| Side (E_s, 90%) | Family | E_f | D_f (90%) | Largest set | Sets reaching E_s | Squared-weight ratio (min, mean, max) |
|---|---|---|---|---|---|---|
| **RIAR** 0.716 (0.652 to 0.780) | X, exterior | 0.296 | +0.421 (0.339 to 0.501) | 0.461 | 0 of 20 | 0.93, 1.02, 1.07 |
| | W, core, more edges | 0.254 | +0.462 (0.382 to 0.539) | 0.305 | 0 of 20 | 0.32, 0.47, 0.63 |
| | C, core, same count | 0.289 | +0.428 (0.348 to 0.507) | 0.340 | 0 of 20 | 0.75, 0.76, 0.78 |
| **RIAL** 0.582 (0.511 to 0.652) | X, exterior | 0.217 | +0.364 (0.287 to 0.442) | 0.418 | 0 of 20 | 0.96, 1.01, 1.11 |
| | W, core, more edges | 0.249 | +0.333 (0.260 to 0.408) | 0.319 | 0 of 20 | 0.41, 0.53, 0.69 |
| | C, core, same count | 0.265 | +0.317 (0.234 to 0.396) | 0.340 | 0 of 20 | 0.88, 0.90, 0.93 |

**The reading: "RIA's core edges erase the switch more often than every weight-matched control family"**
(`readings.json`). All six lower bounds exceed 0.10; the smallest is RIAL against C (0.234). The intervals resample
the genomes and the family's 20 sets; they are conditional on N2's wiring.

**Every outcome** (genomes; each family pooled over its 20 sets, so its counts sum to 20 × 141 = 2820; `tables.txt`):

| Arm | Both kept | Erased | Swapped | Other root | Not reached |
|---|---|---|---|---|---|
| intact | 141 | 0 | 0 | 0 | 0 |
| RIAR | 25 | 101 | 1 | 1 | 13 |
| RIAL | 48 | 82 | 1 | 2 | 8 |
| RIAR: X / W / C | 1676 / 1835 / 1730 | 834 / 717 / 814 | 1 / 0 / 1 | 20 / 9 / 2 | 289 / 259 / 273 |
| RIAL: X / W / C | 1926 / 1851 / 1787 | 613 / 701 / 746 | 0 / 0 / 1 | 13 / 10 / 6 | 268 / 258 / 280 |

"Not reached" counts as not erased, as the plan says. It is about 9% and 6% of the side arms' genomes and 9% to 10% of
the controls' genome–set pairs (Astra).

**Per panel** (`tables.txt`): each side erases more than the mean of every family in all 8 panels. RIAR erases 0.54
to 0.83 per panel and RIAL 0.50 to 0.69; the family means range from 0.14 to 0.46.

**The spread of the controls' sets** (each set's erased fraction over the 141 genomes; `tables.txt`):

| Side | X (min / median / max) | W | C |
|---|---|---|---|
| RIAR (0.716) | 0.078 / 0.298 / 0.461 | 0.191 / 0.266 / 0.305 | 0.241 / 0.294 / 0.340 |
| RIAL (0.582) | 0.099 / 0.188 / 0.418 | 0.170 / 0.252 / 0.319 | 0.213 / 0.262 / 0.340 |

*After the data:* within W, the sets with more concentrated weight erase more (Spearman of a set's erased fraction with
its squared-weight ratio +0.51 for RIAR, +0.70 for RIAL), but W's most concentrated sets (0.63, 0.69 of the side's)
erase 0.277 and 0.255 (Fable). Within X and C the correlation is small (−0.08 to +0.18); C's ratios span a narrow range.

## The descriptive arms (not read)

Erased of the 141 genomes; the squared-weight ratio and the heaviest edge are against the side's own (`tables.txt`):

| Arm | Edges | Weight | Squared ratio | Heaviest edge | Erased |
|---|---|---|---|---|---|
| **RIAR** | 26 | 560 | 1.00 | 57 | **101** |
| RIAR: heaviest core set | 26 | 597 | 0.82 | 56 | 47 |
| RIAR: an AVAR set | 26 | 535 | 0.85 | 52 | 4 |
| RIAR's non-core edges | 33 | 298 | 0.47 | 61 | 49 |
| **RIAL** | 29 | 503 | 1.00 | 48 | **82** |
| RIAL: heaviest core set | 29 | 640 | 1.11 | 56 | 48 |
| RIAL: an AVAL set, an AVAR set | 29, 29 | 479, 487 | 0.94, 0.93 | 56, 52 | 3, 2 |
| RIAL's non-core edges | 34 | 331 | 0.54 | 51 | 36 |
| RIA, both sides | 53 | 1002 | | | 111 |
| all of C3 | 260 | 2347 | | | 116 |

*After the data:*
- **The heaviest core set:** the heaviest 29 core edges avoiding RIA have more total weight, more squared weight and a
  heavier largest edge than RIAL's, yet erase 48 against RIAL's 82; the heaviest 26, heavier than RIAR's in total but
  less concentrated (0.82), erase 47 against 101. The two sets are nested, and RIAL's 48 equals C's best set. This
  tested set does not exhaust explanations by the distribution of weight (Astra).
- **The AVA sets** are 26 or 29 of AVA's 106 chemical edges not touching RIA, matched edge by edge to RIA's weights
  (the plan's star rule), not AVA's whole star (Astra, Fable). Of matched weight and similar concentration, they erase
  2 to 4. AVA is not in C3, so none of these edges is C3-internal.
- **RIA's non-core edges** (each with RIA at one end; the plan's arms, interpreted here) erase 49 and 36 with 298 and
  331 of weight, more than the median exterior set of RIA's full weight (X's median 0.298 and 0.188, about 42 and 27
  genomes), whose edges have both ends outside C3. The comparison is not matched; it says the switch is vulnerable at
  RIA's non-core edges too (Astra, Fable). Cutting both sides' core edges erases 111, close to all of C3's 116.
- In the two sides per genome, 63 genomes are erased by both cuts, 38 by RIAR's only, 19 by RIAL's only and 21 by
  neither; cutting both sides together erases 7 that neither side alone did, and misses 16 that one side alone did.

## The dissection on fresh genomes (description)

Each C3 neuron's internal edges cut alone (the full table, with M4b's counts beside it, is in `tables.txt`):

| Cut | Edges | Weight | M4c (141) | M4b (28) |
|---|---|---|---|---|
| RIAR's | 26 | 560 | 101 (0.716) | 20 (0.714) |
| RIAL's | 29 | 503 | 82 (0.582) | 17 (0.607) |
| SMDVL's | 19 | 184 | 69 (0.489) | 13 (0.464) |
| RMDR's | 24 | 201 | 51 (0.362) | 10 (0.357) |
| SMDVR's | 21 | 163 | 44 (0.312) | 11 (0.393) |
| RMDL's | 21 | 168 | 36 (0.255) | 10 (0.357) |
| SMDDL's | 25 | 206 | 33 (0.234) | 7 (0.250) |
| the next 10 neurons | 10 to 26 | 69 to 208 | 7 to 23 each | 0 to 4 each |
| the last 13 | 8 to 16 | 26 to 217 | 0 to 5 each | 0 to 1 each |

*After the data* (Astra): the order repeats M4b's (Spearman +0.86 over the 30 neurons). Weight and erasures correlate at +0.56 (+0.46 without
the two RIAs); each C3 edge belongs to two neurons' sets, so these are not independent. *After the data:* per unit of
weight, SMDVL's 19 edges (weight 184, 69 erased) erase more than RIA's; RMDDR's 12 edges (weight 201) erase 1. The
partitions: C3 without the read-out 96, the read-out with the rest of C3 90, the read-out among themselves 24.

## What this means for the roadmap

*Interpretation, after the data.*
- **The fixed reading is positive.** On fresh N2 genomes, removing one RIA's C3-internal connections for 30 ticks
  erases the switch 0.32 to 0.46 more often than removing as much anatomical weight under each of three schemes:
  as many exterior edges of matched weights, more core edges, or as many core edges of the same total. M4b's
  dissection, found after its data, repeats on new genomes.
- **The plan's limits stand.** This does not show that RIA stores the switch. Cutting all of one neuron's core
  chemical connections removes its part in the core's chemical feedback (its gap junctions and RIAR's autapse stay),
  which no scattered control matches; the matched AVA sets are the only single-neuron comparison, they are subsets of
  AVA's edges, and they sit outside the core. RIA's weight is more concentrated than C's sets (squared ratio 0.76 and
  0.90); the heaviest core set, more concentrated than RIAL's, erases fewer, but one set does not exhaust that
  explanation. The set bootstrap assumes C's chain mixes well (the plan's caveat). One graph, one cut length, one
  ensemble of random genomes.
- **What M4c adds:** RIA's prominence in the dissection is not the dissection's selection effect (fresh genomes), and
  not its weight under these schemes. Other core neurons (SMDVL, RMDR, SMDVR) also erase many switches with less
  weight, so among the tested single-neuron cuts of C3's chemical edges RIA's are the strongest, not the only ones
  that matter.
- **Next, for a decision with the owner and the reviewers:** M5 (an RIA-based transplant) becomes a reasonable
  candidate; neither storage nor portability is established. A cheaper step first could compare core neurons' stars against each other at matched weight and count, to
  ask whether RIA differs from SMDVL or RMDR in kind or only in weight.

## Deviations and notes

- None from the plan in what ran. The census was started during review round 1, as the plan discloses; its code was
  the round-1 working tree, not archived, checked as above.
- Everything in the per-panel, spread, concentration, per-genome, per-weight and M4b-comparison analyses, and their
  interpretation, is after the data; the plan fixed only the reading and the items reported beside it.

## Reproduce it

```
py scripts/memory_m4/m4c.py census   # about 3 CPU hours here (8 fresh N2 panels of 1024)
py scripts/memory_m4/m4c.py sets arms   # about 3 CPU hours here (165 arms on 141 genomes)
py scripts/memory_m4/m4c_read.py     # the reading; seconds
py scripts/memory_m4/m4c_tables.py > runs/memory-m4c/tables.txt   # needs the local connectome
```
