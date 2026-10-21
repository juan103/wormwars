# M2 census: how much of N2's lead is separate states — results

*Draft 2, 2026-10-21, after one round of review (Astra 6 and Fable 5.1, both "revise"; each was asked twice, by
an accidental double launch, and all four answers are archived with draft 1 in
[`docs/reviews/20261021-m2-census-results/`](../reviews/20261021-m2-census-results/)). Exploratory: the plan
([`M2-CENSUS-PLAN.md`](M2-CENSUS-PLAN.md), draft 5, agreed by both after five rounds; D355) fixed the panels, the
classifier, the estimands, the readings, their thresholds and the checks before anything ran. Nothing here is a
pre-registration. Numbers come from `runs/memory-m2-census/`: the panel records (`<panel>.json`), the checks
(`c1__<panel>.json`, `c2.json`, `c3.json`, `c5.json`; `batch7_check.json`, below), `split.json` and `summary.json` (written by
[`split.py`](../../scripts/memory_m2/split.py)), and `tables.txt`, written after the data by
[`census_tables.py`](../../scripts/memory_m2/census_tables.py) from those records only (no simulation). Anything the
plan did not fix is marked **after the data**.*

## In short

- **Every check passed.** C1 reproduced M1's arrays on all 42 of M1's panels within 5 × 10⁻⁷, C2 named the
  six planted genomes, C3's 20 roots agreed within 1.4 × 10⁻¹⁴, C4 flagged no panel, and C5 reclassified the pilot's
  467 genomes with 100% agreement and no basin change.
- **The reading at tick 30 is "inconclusive" on both of N2's panels.** Separate states carry φ_S = 0.47 of N2's
  mean lead over the 30 reference graphs at seed 7600 (90% interval 0.28 to 0.67; unresolved band 0.47 to 0.56) and
  0.35 at seed 7700 (0.14 to 0.55; band 0.35 to 0.36). Fading carries 0.44 and 0.64. Neither "most", "little" nor "a
  part, between a quarter and a half" is established, and none is excluded on both panels: the intervals are too
  wide. The plan expected this (0.44 and 0.32 from M1's cohort alone). **The roadmap's branch is not taken.**
- **The split is by genome** (the plan): each genome's whole |δy(30)| goes to its class, so a separate-states
  genome's transient part counts as separate states. It is not a split of persistent against transient signal.
- **The two parts enter differently** (the plan's composition-retention split). Separate states enter N2's lead by
  N2's **having more of them** (composition and presence, almost all of Λ_S): fewer than 2% of N2's eligible genomes
  (15 and 13) are separate states, holding 9% and 7% of the denominator, and 19 of the 30 reference graphs have none.
  Fading enters by **retention**: N2's fading genomes, taken together, keep 0.38 and 0.40 of their start difference
  at tick 30, against a reference median of 0.27; **after the data**, descriptively, that is above all 30 reference
  graphs (largest 0.34) and all 10 selected graphs (largest 0.37), though not above two of the core-frozen shuffles.
- **Fading's part is transient.** By tick 100 φ_S is 0.58 and 0.63 (point estimates), and at tick 300 it is 0.87
  and 0.99 ("most" on both panels, read as a description, as the plan says). N2's fading genomes keep 0.008 and 0.002 at tick 300.
- **Batch 7's arms, described:** the three core-frozen shuffles have about as many separate-states genomes as N2 or
  more (9, 17 and 26), with the two states differing in the same place (85 to 92% of the difference on the 30 core
  neurons; N2: 92 and 93%), and N2's fading retention (0.36 to 0.41). The three hub-frozen shuffles have fewer (1, 2
  and 4), with a third to a half of their difference on the core; two of them have almost no S(30) (0.001 and 0.009),
  but the third has N2's seed-7700 level (0.068) from 4 genomes. Their fading retention (0.31 to 0.36) is within or
  just above the reference's range. Three graphs per arm, spike rewirings, and a core chosen on N2's result.

## The run

- Run from 2026-10-20 23:01 UTC to 2026-10-21 11:03 UTC on the CPU of the tested machine, at commit d36c9ef (D355),
  all stages in order (`runs/memory-m2-census/census_log.txt`, a copy of the local `census.log`; exit 0). Compute
  (`census-compute-record.json`, a copy of the local `compute.json`): 7.83 × 10⁹ neural updates and 43,317 s (12.0
  hours), category probe. By `stages.json`, C2 took 513 s, the panels 42,743 s, C3 10 s and C5 51 s. By the panel
  records, the 48 panels took 42,732 s between them (median 847 s, the longest 1821 s), in 384 chunks of 95 to 297 s
  (median 105 s). The guard's projection after two panels was 12.8 hours (`guard.json`), under the
  16-hour stop; the plan had estimated 10 to 11.
- **All 48 panels ran and are valid by M1's rule:** 49,152 genomes drawn, 47,084 eligible (937 to 1010 per panel).
  No batch-7 arm failed to regenerate, so none was skipped. A pass left no file (Fable), so after the run
  [`batch7_record.py`](../../scripts/memory_m2/batch7_record.py) reran the same deterministic check and recorded
  the matched edge counts, triangle counts, reciprocal pairs, kept fractions and accepted swaps for each of the six
  arms (`batch7_check.json`: all match). The ineligible genomes hold at most 4.8% of a panel's tick-30 numerator
  (SH-route-2020011; N2: 0.17% and 0.15%) and at most 0.5% of its denominator.

## The checks

| Check | Threshold (the plan's) | Result | Reading |
|---|---|---|---|
| **C1**, reproduction of M1 | stop if > 1% of a panel's genomes differ by > 10⁻³ in a or \|δy(30)\| | 42 panels; largest gaps 5.3 × 10⁻⁷ (a), 5.1 × 10⁻⁷ (\|δy(30)\|), 4.6 × 10⁻⁷ (\|δy(100)\|); no genome above 10⁻³; no change of eligibility or cohort; eligible shares and C(30), C(300) within 1.7 × 10⁻⁷ of M1's | **passes** |
| **C2**, the planted genomes through the census path | all six named exactly | six of six | **passes** |
| **C3**, P³² against the tick's automatic derivative | 20 roots, within 10⁻⁸ | largest gap 1.4 × 10⁻¹⁴ | **passes** |
| **C4**, resolution per graph | unresolved ≤ 5% of eligible genomes and ≤ 10% of the eligible tick-30 numerator | at most 0.9% of genomes (core-frozen-shuffle2) and 4.2% of the numerator (the same); N2: 0.2% and 3.4% (seed 7600), 0.1% and 0.1% (7700) | **no panel named** |
| **C5**, the pilot's 467 genomes again | classes agree for ≥ 95%; every separate-states history reaches the same root | 467 of 467 agree; no basin change | **passes** |

C1's gaps are presumably float32 rounding between M1's one batch of 1024 and the census's chunks of 128 (not
tested). So the census's arrays agree with M1's within 5 × 10⁻⁷, and M1's per-genome numbers apply to these brains
to that tolerance.

## The classes

| Panels | Eligible genomes | Separate states | Fading | Oscillation | Unresolved | Graphs with any separate states |
|---|---|---|---|---|---|---|
| N2 (seeds 7600, 7700) | 990, 1003 | 15, 13 | 972, 987 | 1, 2 | 2, 1 | 2 of 2 |
| The 30 reference graphs | 29,315 | 38 | 29,265 | 2 | 10 | 11 of 30 |
| The 10 selected graphs | 9817 | 387 (12 to 78 per graph) | 9428 | 0 | 2 | 10 of 10 |
| Core-frozen shuffles (3) | 2973 | 52 (9, 17, 26) | 2893 | 12 | 16 | 3 of 3 |
| Hub-frozen shuffles (3) | 2986 | 7 (1, 2, 4) | 2977 | 0 | 2 | 3 of 3 |

The separate states include 11 "separate states, read-out silent" genomes: one on a reference graph
(SH-recip-2050008) and ten on five selected graphs; none on N2 or batch 7's arms (`tables.txt`; draft 1 said none,
Astra). Per panel: `tables.txt`, "C4 and classes per panel".

- **Persistent oscillations,** 17 genomes, none in the pilot: one on N2 at seed 7600 (genome 777, period 11.3
  ticks), two at 7700 (20.8 and 42.9 ticks), two on one reference graph (SH-recip-2050008), and 12 on the
  core-frozen shuffles (periods 11.6 to 44.1 ticks). Their contribution O(30) is at most 0.014 (core-frozen-shuffle2,
  whose eligible share is 0.54), and 0.0003 on N2. "Persistent" means over the 22,000 ticks observed, and the period
  search covers cycles up to 50 ticks (the pilot's limits).
- **The unresolved,** 33 genomes. On N2 at seed 7600 they are the pilot's two: genome 26, the sustained motion
  without a period (2.0% of the eligible tick-30 numerator), and genome 349, the float32 stall 1.38 × 10⁻³ from its
  root (1.4%). At tick 300 genome 349 holds most of N2's unresolved numerator (|δy| 0.71 against genome 26's 0.13).
  Reasons per panel: `tables.txt`.

## The split at tick 30: the reading

| | N2, seed 7600 | N2, seed 7700 |
|---|---|---|
| Λ, N2's mean lead over the 30 reference graphs | 0.171 (0.127 to 0.214) | 0.170 (0.126 to 0.214) |
| N2's lead by M1's definition (minus the reference median) | 0.170 | 0.169 |
| Resamples with Λ ≤ 0 | 0 of 2000 | 0 of 2000 |
| **φ_S**, separate states | **0.47** (0.28 to 0.67) | **0.35** (0.14 to 0.55) |
| band: φ_S⁻ to φ_S⁺ | 0.47 (0.28 to 0.67) to 0.56 (0.35 to 0.76) | 0.35 (0.14 to 0.55) to 0.36 (0.15 to 0.56) |
| **φ_F**, fading | **0.44** (0.24 to 0.65) | **0.64** (0.44 to 0.85) |
| band: φ_F⁻ to φ_F⁺ | 0.44 (0.24 to 0.64) to 0.53 (0.33 to 0.72) | 0.64 (0.44 to 0.85) to 0.65 (0.45 to 0.86) |
| φ_O, oscillation | 0.001 | 0.001 |
| φ_U, unresolved | 0.087 (−0.001 to 0.19) | 0.001 |
| **Reading** | **inconclusive** | **inconclusive** |

Points with 90% bootstrap intervals (`summary.json`, `split.json`). Both panels are read against the same 30 seed-7600
reference panels, so their agreement replicates N2's draw of genomes, not the reference.

**The readings.** At seed 7600, lower(φ_S⁻) = 0.28 is above a quarter but not above a half, and upper(φ_S⁺) = 0.76
is above a half: neither "most" nor "a part, between a quarter and a half". At seed 7700, lower(φ_S⁻) = 0.14 and
upper(φ_S⁺) = 0.56: neither "little" nor "a part". By the plan's combination (rule 2, the same reading on both
panels), **the result is "inconclusive"**. In words, what the 90% intervals do exclude, in the plan's sense: at seed
7600 separate states carry **at least a quarter** of N2's lead; at seed 7700 they carry **at most about 56%** of it,
and fading at least 44%. So "little" is excluded at seed 7600 and "most" at seed 7700, but neither on both. φ_F's
intervals exclude zero on both panels. Over both panels, separate states carry between about 0.14 and 0.76 of the lead, and fading between about 0.24
and 0.86.

**The branch** ("settling explains little of the excess"): not taken, since the combined reading is not "little".

**Against the expectation.** The plan expected about 0.44 and 0.32 if the separate states were exactly M1's cohort;
the census gives 0.47 and 0.35. Every cohort genome on every panel is separate states except N2's genome 349
(unresolved), and the separate states outside the cohort add a little on N2 (3 genomes over both panels, with a
summed |δy(30)| of 2.5, against 15.7 for the cohort's separate states) and a little to the reference (10 genomes over
30 graphs, 1.1 against 3.6; `tables.txt`,
"M1's cohort against separate states").

**The unresolved band** is wide only at seed 7600, where genomes 26 and 349 hold 3.4% of N2's eligible tick-30
numerator, and so 9% of Λ (genome 26 5.2% of Λ, genome 349 3.6%; `tables.txt`). The radius sensitivity (below) makes genome 349 separate states and gives φ_S = 0.51 there.

**Per ensemble** (descriptive; N2 against each ensemble's six graphs), φ_S at seed 7600 is 0.44 to 0.53, and at 7700
0.31 to 0.40 (`tables.txt`).

## Composition, retention and presence

Λ_X splits into composition (N2 has more of the class), retention (N2's class keeps more within it) and presence
(the pairs where one graph has no genome of the class), each a mean over the 30 pairs (N2, g):

| Tick 30 | Seed 7600 | Seed 7700 |
|---|---|---|
| **S:** N2's share of the denominator w_S (reference mean) | 0.090 (0.008) | 0.067 (0.008) |
| S: N2's own retention ρ_S | 0.98 | 1.02 |
| Λ_S = composition + retention + presence | 0.081 = 0.025 − 0.001 + 0.056 (19 presence pairs) | 0.060 = 0.017 + 0.000 + 0.043 (19) |
| **F:** w_F (reference mean) | 0.900 (0.992) | 0.931 (0.992) |
| F: ρ_F, N2 (reference median, range) | 0.38 (0.27, 0.18 to 0.34) | 0.40 (the same) |
| Λ_F = composition + retention + presence | 0.076 = −0.030 + 0.105 + 0 | 0.110 = −0.020 + 0.130 + 0 |

- **Separate states:** N2 has them and most reference graphs do not. The class as a whole keeps about its whole
  start difference at tick 30 (ρ_S 0.98 and 1.02), though its genomes vary (|δy(30)|/a from 0.77 to 1.69 at seed
  7600 and 0.27 to 1.46 at 7700; `tables.txt`), and the retention term is near zero. So almost all of Λ_S is N2's
  having more of the class.
- **Fading:** N2 has slightly fewer fading genomes by weight (composition negative), and together they keep more of
  their start difference at tick 30. This is the roadmap's "graded slower fading", measured as the plan defined it:
  retention alone is 0.105 and 0.130, more than Λ_F. ρ_F is an amplitude-weighted aggregate over the class, so it
  does not say that most individual fading genomes fade more slowly.
- **After the data, descriptively:** N2's ρ_F(30), 0.378 and 0.402, is above every one of the 30 reference graphs
  (0.181 to 0.337) and of the 10 selected graphs (0.191 to 0.365). The ranking has no interval, and the seed-7600
  panels share one draw of genomes. The selected graphs, chosen in 03mc for their share or their cohort, have a
  median of 0.27, the reference's. Two core-frozen shuffles are above both N2 panels (0.411 and 0.406), and one
  hub-frozen shuffle above every reference graph (0.355).
- **Fading's asymptotic rate** (the slowest mode of P³² at the common root, the |δy(30)|-weighted median per graph,
  per tick): N2 −0.039 and −0.042, the reference median −0.044 (−0.047 to −0.037); N2 is slower than 28 and 22 of the
  30. As the plan says, this is the late rate, not tick-30 retention, which is mostly transient.

## The contributions over time

From the recorded δy, no new simulation (`split.json`, `over_time`; `tables.txt`):

| Tick | 10 | 30 | 50 | 100 | 200 | 300 | 1000 | 2000 |
|---|---|---|---|---|---|---|---|---|
| Λ, seed 7600 | 0.149 | 0.171 | 0.140 | 0.137 | 0.104 | 0.093 | 0.097 | 0.088 |
| φ_S, seed 7600 | 0.56 | 0.47 | 0.57 | 0.58 | 0.77 | 0.87 | 0.82 | 0.90 |
| φ_F, seed 7600 | 0.34 | 0.44 | 0.38 | 0.36 | 0.17 | 0.06 | −0.00 | −0.00 |
| Λ, seed 7700 | 0.152 | 0.170 | 0.140 | 0.094 | 0.066 | 0.059 | 0.062 | 0.058 |
| φ_S, seed 7700 | 0.40 | 0.35 | 0.43 | 0.63 | 0.88 | 0.99 | 0.93 | 0.99 |
| φ_F, seed 7700 | 0.60 | 0.64 | 0.56 | 0.32 | 0.10 | −0.00 | −0.01 | −0.01 |

The separate states' contribution is flat from tick 0 (N2: 0.090 and 0.067; reference mean 0.008 to 0.010). Fading's
falls from 0.90 and 0.93 at tick 0 (0.99 in the reference) to 0.34 and 0.37 at tick 30 (0.26), 0.07 and 0.05 at tick
100 (0.02), and about 0.0001 at tick 2000. Fading's lead over the reference, Λ_F, peaks at tick 20 (0.092) and tick
26 (0.113), close to tick 30 (0.076 and 0.110; after the data, `over_time`). At seed 7600 at tick 300, the lead
not carried by separate states is fading's (φ_F 0.06), the unresolved's (φ_U 0.07, of which genome 349's stall
0.062 and genome 26's sustained motion 0.011 before the reference's U is subtracted; Astra) and oscillation's
(0.004).

**At tick 300** (read as a description, by the same rules): "most" on both panels. φ_S = 0.87 (0.71 to 0.96; band
0.86 to 0.94) and 0.99 (0.92 to 1.04; band 0.99 to 0.99); Λ = 0.093 and 0.059, with 0 and 5 resamples of Λ ≤ 0.
M1's A5 had the cohort carrying 0.66 to 0.68 of the tick-300 lead and 0.30 to 0.38 of the tick-30 lead, on
03mc's arrays and against 03mc's ensembles; the reference here is M1's 30 fresh random graphs, so the numbers are
not directly comparable, but the pattern is the same: a minority to a half at tick 30, most at tick 300.

## Batch 7's core-frozen and hub-frozen shuffles

| | Separate states | S(30) | F(30) | s(30) | Where the two states differ: core / hubs / rest (read-out) | ρ_F(30) |
|---|---|---|---|---|---|---|
| N2, seeds 7600 and 7700 | 15, 13 | 0.089, 0.068 | 0.34, 0.37 | 0.44, 0.44 | 0.92 / 0.00 / 0.08 (0.60); 0.93 / 0.00 / 0.07 (0.68) | 0.38, 0.40 |
| Core-frozen 0, 1, 2 | 9, 17, 26 | 0.078, 0.123, 0.209 | 0.37, 0.30, 0.30 | 0.46, 0.44, 0.54 | 0.85 to 0.92 / 0.01 to 0.02 / 0.07 to 0.13 (0.49 to 0.65) | 0.41, 0.36, 0.41 |
| Hub-frozen 0, 1, 2 | 1, 2, 4 | 0.001, 0.009, 0.068 | 0.35, 0.31, 0.30 | 0.36, 0.32, 0.37 | 0.34 to 0.53 / 0.06 to 0.13 / 0.34 to 0.56 (0.11 to 0.26) | 0.36, 0.31, 0.32 |
| The 30 reference graphs | 38 in all | 0.008 (mean) | 0.26 (mean) | 0.27 (mean) | per graph with any: core 0.03 to 0.42 | 0.27 (median) |
| The 10 selected graphs | 12 to 78 | 0.04 to 0.39 | 0.16 to 0.33 | 0.25 to 0.56 | core 0.05 to 0.77 | 0.27 (median) |

"Where": the fraction of ‖v₁* − v₂*‖² on batch 7's 30 core neurons, its 30 hub neurons and the rest, per graph,
weighted by |δy(30)|; the 8 read-out neurons lie inside the core.

So, descriptively, to the roadmap's question: **the core-frozen graphs keep N2's number of separate-states genomes
or more, with the states differing on the core as in N2, and N2's fading retention. The hub-frozen graphs have
fewer separate-states genomes, with heterogeneous contributions (S(30) 0.001, 0.009 and 0.068), their difference a
third to a half on the core, and fading retention within or just above the reference's range; their s(30), 0.32 to
0.37, lies between N2's and the reference's.** Counts and averaged locations do not show that these are the same
states as N2's (Astra). The caveats are the plan's: three graphs per arm, spike rewirings rather than 03's samplers,
and a core chosen on N2's start difference, so that the separate states' location on it is partly by construction. In the selected and reference graphs the two states differ mostly off the core
(except SH-class-2030029, 0.77, and SH-recip-2050039, 0.51): separate states in the nulls live elsewhere.

## The other descriptions

- **M1's cohort against the classes.** On N2, 26 cohort genomes over both panels, 25 of them separate states (the
  26th is genome 349, unresolved), and 3 separate-states genomes outside the cohort. On the reference, 28 cohort
  genomes, all separate states, and 10 outside. On the selected graphs, 351 and 36; core-frozen 38 and 14; hub-frozen
  3 and 4. With numerators: `tables.txt`.
- **The cheaper "reaches" rule** agrees with the full verdict on every history: 94,073 both reached, 95 both not, no
  disagreement.
- **Per graph:** each reference graph's contributions and its cohort cross-tab are in `split.json`
  (`t30.contributions`, `panels.<panel>.cohort_by_separate`); `tables.txt` prints the totals by role and N2's.
- **The locating radius, a sensitivity.** 13 histories of 10 genomes were "not approaching" with a stable root
  between 10⁻³ and 10⁻² away. All 13 reach it under the continuation. Eight genomes would change class: N2's genome
  349 to separate states, and seven unresolved genomes on other panels (one on N2 at seed 7700) to fading; two stay
  unresolved. φ_S at tick 30 would be 0.51 at seed 7600 and unchanged at 7700. The classes and readings above use the
  frozen rule.
- **Settling and share** (the 30 reference graphs): the Spearman correlation of s(30) with the fraction of cohort
  genomes is 0.37 pooled, and with the fraction of separate-states genomes 0.32. Per ensemble, with six graphs and
  mostly zero counts, the coefficients run from −0.27 to 0.65 and say almost nothing, as the plan said. 03mc's
  within-ensemble association stays untested.

## What this means for the roadmap

*Interpretation, after the data.*
- **The split's answer is "both", in proportions the census does not settle.** At tick 30, N2's lead over its null
  ensembles is carried in two parts: by a few genomes classified as reaching two distinct stable roots under this
  probe (15 and 13 of about 1000), and by fading genomes that, as a class, keep more of their difference at tick 30
  than the reference's. The census cannot say which part is larger: the intervals for separate states are 0.28 to
  0.67 and 0.14 to 0.55. By point estimate, separate states carry more than half by tick 100 and nearly all by tick
  300.
- **The branch is not taken,** since the combined reading is not "little". That is all the rule says: neither
  "little" nor "most" is established at tick 30, and neither is excluded on both panels. Fading's part is not zero
  (its intervals exclude zero on both panels), and by the retention measure above it comes from how much N2's fading
  genomes keep, not from their number. It sits beside settling, not instead of it.
- **For M3 and M4:** freezing the core keeps both parts at about N2's level or above; freezing hubs reduces the
  number of separate-states genomes on all three graphs, their contribution on two, and fading retention to about the
  reference's on two. With three graphs per arm and a core chosen on the result, this is a pointer for M3's core
  defined without the result, not a finding.

## Deviations and notes

- None from the plan in what ran. The tables in `tables.txt` (ρ_F and the asymptotic rates ranked against the
  reference, per arm; the totals by role; the subclass counts; N2's unresolved genomes' contributions) were written
  after the data, from the committed records. `batch7_check.json` was written after the run (above).
- `split.json`'s per-panel counts merge the two separate-states subclasses; the subclass counts come from the panel
  records (`tables.txt`).
- The persistent oscillations are new relative to the pilot, which confirmed none on its 467 genomes: they appear
  among the census's 47,084 eligible genomes. They are named by the pilot's frozen rule and its planted check (C2).

## Reproduce it

```
py scripts/memory_m2/census.py      # about 12 CPU hours; resumes by panel; needs M1's local arrays for C1
py scripts/memory_m2/split.py       # the estimands, readings and bootstrap; seconds
py scripts/memory_m2/census_tables.py > runs/memory-m2-census/tables.txt
py scripts/memory_m2/batch7_record.py   # batch 7's regeneration check, recorded; seconds
```

The panel arrays (`<panel>.npz`) stay local; the panel records, the checks, `batch7_check.json`, `split.json`,
`summary.json` and `tables.txt` are committed.
