# M4d: does N2's head core carry the switch into other graphs? — results

*Draft 3, 2026-10-25, after two rounds of review (Astra 6 and Fable 5.1: both "fix then publish" in rounds 1 and 2;
all findings taken; drafts 1 and 2 and the reviews are archived in
[`docs/reviews/20261025-m4d-results/`](../reviews/20261025-m4d-results/)).
Exploratory: the plan ([`M4D-PLAN.md`](M4D-PLAN.md), draft 5, agreed after four rounds; D363) fixed the hosts, the
arms, the genomes, the outcome, the reading and the rules after it before any arm ran. Nothing here is a
pre-registration. Numbers come from `runs/memory-m4d/`: the hosts' records (`hosts.json`), the blocks' summary
(`blocks-summary.json`; the full `blocks.json` stays local, below), one record per host and arm
(`arms/<host>__<arm>.json`), `companion.json`, `coverage.json` (committed with the plan in 6553a98, before any arm
ran), `readings.json` (written by [`m4d_read.py`](../../scripts/memory_m4/m4d_read.py); console output
`read_log.txt`), and `tables.txt`, written after the data by
[`m4d_tables.py`](../../scripts/memory_m4/m4d_tables.py) from those records (no simulation). Interpretations the plan
did not fix are marked **after the data**.*

## In short

- **The reading is "Unresolved (the unresolved genomes decide it)".** On the genomes the classifier resolved, the
  reading would be the plan's second: "A transplant benefit; an advantage of C3's wiring of m or more over rewired
  copies ruled out, as a mean across these ten hosts (a response confined to a minority of host graphs may be
  missed)". Over every assignment of the unresolved genomes, the upper bound of T against R reaches 0.0087, above the
  margin of 0.004, so the exclusion does not hold. Accepting this screen is not accepting the second reading: the
  wiring's advantage is unresolved.
- **The transplant raises the share of separate-states genomes in every host.** Of 10,240 genomes per arm (1024 in
  each of ten fresh hosts), 4 have separate states with the host's own block (0.04%) and 64 with N2's block in its
  place (0.62% counted; up to 1.11% if every unresolved T genome were a switch). T exceeds I in all ten hosts;
  D_TI = +0.0059 (90% interval 0.0048 to 0.0069), and its lower bound stays above the margin over every assignment of
  the unresolved genomes (0.0046).
- **On the counted genomes, the rewired copies reach most of it.** R, N2's 260 edges rewired at fixed in- and
  out-degrees and out-strengths, has 52 (0.51%); D_TR = +0.0012 (−0.0009 to 0.0032), and T exceeds R in 6 of the 10
  hosts. P, N2's exact edges with shuffled weights, has 69 (0.67%). D, the same count, weights and autapses at random
  positions, has 24 (0.23%).
- **The unresolved genomes are as many as the effect, and they gather in the exact-wiring arms.** T has 50 unresolved
  genomes and R 36, against a difference of 12 separate-states genomes between them. Genomes that do not settle
  (persistent oscillation or unresolved) number 76 in T and 70 in T+G, against 43 to 53 in D, R, Rr and P, and none in
  the intact hosts.
- **The companion** (description): M4c's 141 N2 switch genomes, keeping their C3 weights and their C3 neurons' τ and
  bias with everything else drawn fresh, are classified separate states in 13 of 282 genome–exterior trials in N2
  (control 6) and 25 of 1410 in the hosts' T graphs (control 10). Keeping these core parameters was usually not enough
  to keep the switch under the tested redraws.
- **What this does not show:** that N2's exact wiring inside the head core matters, or that it does not. The plan's
  rule for an unresolved reading applies: no extension without a new plan, and the next step is decided with both
  reviewers and, if it changes direction, the owner. Both reviewers recommend publishing the screen as unresolved and
  putting the direction to the owner (below).

## The run

- **One invocation**, all four stages, from 2026-10-24 01:32 to 2026-10-25 03:52 UTC, on the CPU of the tested
  machine (`m4d-attempt.json`, a copy of the local attempt record; `m4d_log.txt`; exit 0). The attempt record names
  commit 6553a98 (D363) at the start, with the code and configuration directories recorded clean, and the same commit
  at the end. No GPU.
- **Compute** (`m4d-compute-record.json`, a copy of the local `compute.json`): one attempt, completed, 1.25 × 10¹⁰
  neural updates and 94,819 s (26.3 h), category probe, inside the 30-hour cap. The 70 panels took 90,532 s (25.15 h;
  `tables.txt`: I 2.7 h, the six block arms 3.4 to 4.1 h each), against the plan's 16.5 to 25 hours. Sixty of the 70
  panels took 790 to 1624 s; the other ten came in two stretches (`m4d_log.txt`): SH-route-2021001's D, R and Rr (1955
  to 2495 s) and, in the evening of 24 October, SH-mirror-2041001's D, P, T and T+G and SH-recip-2051000's I, Rr and P
  (1653 to 3179 s). The CPU was probably shared then: SH-recip-2051000's I panel, with no unresolved genomes, took
  1815 s. The two slowest panels are two of the three with the most unresolved genomes (12 and 10; the third, with 13,
  took 1653 s), so difficult classifications may account for part of the time; the records cannot say how much.
- **The hosts:** all ten from their first seeds, none skipped (SH-2011000, SH-2011001, SH-route-2021000,
  SH-route-2021001, SH-class-2031000, SH-class-2031001, SH-mirror-2041000, SH-mirror-2041001, SH-recip-2051000,
  SH-recip-2051001). Their C3 blocks hold 94 to 127 off-diagonal edges (weight 466 to 861, 0 to 4 autapses, 5 to 38
  reciprocal pairs; SH-recip's two have 24 and 38).
- **The blocks:** every block arm has N2's 260 off-diagonal chemical edges (weight 2347) plus its 8 autapses
  (`blocks-summary.json`). Every R and Rr reached its 5200 accepted swaps. Reciprocal pairs: D 33 to 45, R 35 to 48;
  Rr, P and T 75.
- **The checks.** `m4d_read.py` calls `verify_run` before reading and stops on any failure; it exited 0
  (`read_log.txt`). In the code, `verify_run` regenerates the hosts and matches their content hashes, rebuilds
  `blocks.json` and compares it with the saved one, checks every host's sham genome against `Genome.random` bit for
  bit, and checks that every arm graph changes only inside the block and computes its hash; every panel is then
  validated against its arm, including that hash. Astra reran these checks independently in review, and they passed. All 70 panels
  are valid under M1's rule; no host has more than 5% unresolved genomes in any arm.

## The reading

| Contrast | Mean | 90% interval (hull) | Hosts above 0 | Envelope over the unresolved |
|---|---|---|---|---|
| **D_TI** (T − I) | +0.0059 | 0.0048 to 0.0069 | 10 of 10 | 0.0046 to 0.0125 |
| **D_TR** (T − R) | +0.0012 | −0.0009 to 0.0032 | 6 of 10 | −0.0054 to 0.0087 |

The interval is the hull of the host bootstrap and the Student-t interval, as the coverage simulation required
(`coverage.json`; `t_widened` true). Here the Student-t interval is the wider on both sides, so the hull equals it
(bootstrap: D_TI 0.0050 to 0.0067, D_TR −0.0006 to 0.0028; `tables.txt`). The largest host differences are 0.0088
(T − I) and 0.0059 (T − R), so the single-host guard (0.01) does not fire.

**The rules, in order** (`readings.json`): lower(D_TI) 0.0048 > 0.004 and upper(D_TR) 0.0032 < 0.004 give the second
reading. Recomputed on the envelope, lower(D_TI) 0.0046 still passes, but upper(D_TR) 0.0087 does not fall below the
margin and lower(D_TR) −0.0054 does not rise above it, so the envelope's reading is "Unresolved". The two differ, so
the reading is **"Unresolved (the unresolved genomes decide it)"**. The envelope's lower bound for D_TI (0.0046) is
below the counted one although I has no unresolved genomes, because a mixed assignment has more spread across hosts
(Fable).

**Each end of the box** (hull intervals; `tables.txt`):

| Contrast | Counted only | Unresolved all against T | Unresolved all for T |
|---|---|---|---|
| T − I | +0.0059 (0.0048 to 0.0069) | the same (I has none) | +0.0107 (0.0090 to 0.0125) |
| T − R | +0.0012 (−0.0009 to 0.0032) | −0.0023 (−0.0053 to 0.0006) | +0.0061 (0.0037 to 0.0085) |

*Checked after the data:* no assignment of the unresolved genomes turns the reading positive. With the classifier's
outcomes fixed, each host's difference moves in steps of one genome, and the bootstrap's lower bound rises with every
host's difference (each resample's mean is a non-negative weighting of them; the same resamples are used throughout).
At the all-for-T end it is 0.00400391, above the margin of 0.004 only in the sixth decimal; the Student-t lower bound
there is 0.00365592, so the hull's is too. Every other assignment lies at or below the end with one host one genome
lower, whose bootstrap lower bound is at most 0.00390625 (`tables.txt`). Since D_TI's envelope stays above the
margin, "no transplant effect" is impossible as well. A resolution could therefore yield only the second reading,
"Unresolved", or, if it leaned to T in SH-mirror-2041001 (whose T − R reaches 0.0107 at the all-for-T end), "Unresolved
(a single host responds)" (Fable). This shows the decision rule cannot pass; it does not exclude a true wiring
advantage of 0.004 (Astra).

## Every class by arm

Pooled over the ten hosts, 10,240 genomes per arm (`tables.txt`):

| Arm | Separate states | Of which read-out silent | Fading | Persistent oscillation | Unresolved |
|---|---|---|---|---|---|
| I | 4 | 0 | 10,236 | 0 | 0 |
| D | 24 | 0 | 10,163 | 10 | 43 |
| R | 52 | 1 | 10,145 | 7 | 36 |
| Rr | 32 | 1 | 10,157 | 15 | 36 |
| P | 69 | 1 | 10,125 | 5 | 41 |
| T | 64 | 1 | 10,100 | 26 | 50 |
| T+G | 50 | 0 | 10,120 | 20 | 50 |

**Per host** (separate states, unresolved in brackets, of 1024):

| Host | I | D | R | Rr | P | T | T+G |
|---|---|---|---|---|---|---|---|
| SH-2011000 | 0 (0) | 3 (3) | 2 (3) | 2 (7) | 13 (4) | 7 (5) | 2 (4) |
| SH-2011001 | 0 (0) | 4 (7) | 3 (0) | 4 (1) | 9 (7) | 9 (3) | 4 (4) |
| SH-route-2021000 | 0 (0) | 1 (1) | 9 (3) | 0 (0) | 1 (0) | 4 (3) | 8 (5) |
| SH-route-2021001 | 0 (0) | 0 (3) | 5 (4) | 0 (1) | 2 (1) | 6 (3) | 9 (2) |
| SH-class-2031000 | 0 (0) | 2 (3) | 3 (2) | 1 (4) | 1 (2) | 4 (6) | 4 (5) |
| SH-class-2031001 | 0 (0) | 2 (7) | 7 (1) | 2 (4) | 19 (0) | 7 (1) | 5 (1) |
| SH-mirror-2041000 | 1 (0) | 2 (1) | 4 (0) | 1 (3) | 6 (4) | 7 (4) | 7 (4) |
| SH-mirror-2041001 | 0 (0) | 2 (2) | 7 (5) | 6 (5) | 2 (4) | 6 (12) | 2 (10) |
| SH-recip-2051000 | 2 (0) | 5 (8) | 5 (10) | 15 (8) | 8 (13) | 10 (5) | 7 (8) |
| SH-recip-2051001 | 1 (0) | 3 (8) | 7 (8) | 1 (3) | 8 (6) | 4 (8) | 2 (7) |
| **total** | 4 (0) | 24 (43) | 52 (36) | 32 (36) | 69 (41) | 64 (50) | 50 (50) |

**What "unresolved" is here** (`tables.txt`; a genome's reason lists every failure it met). The commonest failures
are "unconfirmed candidate" (22 to 37 per block arm) and "unstable or marginal root" (20 to 38). In M2's classifier
([`classify.py`](../../scripts/memory_m2/classify.py), `oscillation`), an unconfirmed candidate is a history that
looked like an oscillation, whose roots located from the orbit are all unstable, and whose cycle was not confirmed (no
period found, or the late range fell below the persistence threshold) (Astra, Fable). These are mostly histories that
have not settled, not second stable states that missed confirmation, so resolving them would need a longer horizon
rather than a better root search. The intact hosts have none.

*After the data* (Fable): the genomes that do not settle (persistent oscillation plus unresolved) are 76 in T and 70 in
T+G, against 53 in D, 43 in R, 51 in Rr, 46 in P and 0 in I. They are not spread evenly over the arms; they are
commonest with N2's exact weighted block (T and T+G). P keeps N2's exact edges with shuffled weights and has 46, so
the pattern does not separate the edges from the placement of their weights (Astra).

## The descriptive contrasts (not read)

| Contrast | What the two arms differ in | Mean | 90% interval |
|---|---|---|---|
| D_DI (D − I) | count, weight, autapses and topology together | +0.0020 | 0.0013 to 0.0026 |
| D_RD (R − D) | N2's in- and out-degrees and out-strengths | +0.0027 | 0.0010 to 0.0045 |
| D_RI (R − I) | everything D − I changes, plus R − D | +0.0047 | 0.0034 to 0.0060 |
| D_TRr (T − Rr) | N2's exact wiring, with reciprocal pairs kept in both | +0.0031 | 0.0012 to 0.0050 |
| D_TP (T − P) | which edge carries which weight | −0.0005 | −0.0035 to 0.0025 |
| D_(T+G)T | N2's 44 gap junctions inside the block | −0.0014 | −0.0031 to 0.0004 |

By ensemble (separate states over its two hosts, of 2048), T has 10 to 16 and I 0 to 3 in every ensemble; R ranges
from 5 (SH) to 14 (SH-route), P from 3 (SH-route) to 22 (SH).

*After the data:* the same envelope over the unresolved genomes as the reading's (`tables.txt`): R − I 0.0033 to
0.0106 and D − I 0.0009 to 0.0082 stay above zero; R − D (−0.0043 to 0.0090), T − Rr (−0.0035 to 0.0108), T − P
(−0.0080 to 0.0084) and (T+G) − T (−0.0093 to 0.0057) do not.

*After the data*, all on counted genomes only:
- **The ladder.** R reaches most of T's rise over I, D less than half of it; T − R's interval includes zero. The
  ladder is not a chain of single additions (the plan), and the ratios of these noisy means are not robust over the
  unresolved assignments, so they describe these arms, not separable causes (Fable, Astra).
- **Rr below R.** Keeping N2's 75 reciprocal pairs while rewiring gave fewer separate-states genomes than rewiring
  without them (32 against 52; Rr − R −0.0020, −0.0049 to 0.0010), so T − Rr is larger than T − R. Each host has one R
  and one Rr draw; 15 of Rr's 32 are in one host (SH-recip-2051000), and Rr exceeds R in two hosts. This does not
  show that keeping reciprocity lowers switching in general, nor separate the rewiring's effect from the particular
  draw.
- **P and T.** The pooled counts are close (69 and 64), but P varies most across hosts (1 to 19 per host, against T's
  4 to 10), T − P per host runs from −0.0117 to +0.0039, and the interval is as wide as the whole transplant
  effect (0.0059), reaching about half of it on either side. The same genome is separate states in both arms only once (63 in T only, 68 in P only): moving the weights
  changes which genomes switch almost completely (Astra, Fable). The same holds for T and R (1 in both) and for R and
  Rr (1); T and T+G share 25 of their 64 and 50.
- **N2's gap junctions** inside the block did not increase the counted share; if anything it is lower (50 against 64;
  the interval reaches zero), with 50 unresolved genomes in each arm.

## Write, hold and read (not read)

Pooled medians by arm (`readings.json` "measures"; the read-out difference is over separate-states genomes; the silent
share is over separate-states genomes at or above `START_FLOOR`):

| Arm | Write (squared norm) | Fraction on C3 | Read-out difference | Read-out-silent share above the floor |
|---|---|---|---|---|
| I | 0.381 | 0.144 | 0.026 (4 genomes) | 0.000 |
| D | 0.456 | 0.233 | 0.313 | 0.000 |
| R | 0.459 | 0.232 | 0.308 | 0.019 |
| Rr | 0.454 | 0.228 | 0.340 | 0.031 |
| P | 0.463 | 0.242 | 0.384 | 0.015 |
| T | 0.436 | 0.217 | 0.329 | 0.016 |
| T+G | 0.430 | 0.208 | 0.630 | 0.000 |

Every block arm writes somewhat more than the intact host, and a larger fraction of the difference falls on C3's
neurons; T writes a little less than D, R, Rr and P. No genome had a zero write difference in any arm. Eligible
genomes (a ≥ `START_FLOOR`) number 9726 to 9863 of 10,240 per arm. As the plan says, the write amplitude does not
isolate keeping from writing.

## The circuitry companion (description)

M4c's 141 N2 switch genomes keep their C3-block chemical weights (signs included) and their C3 neurons' τ and bias;
everything else is a fresh draw. The control is the same fresh draws unchanged (`companion.json`; `tables.txt`):

| Where | Selected | Control | For comparison |
|---|---|---|---|
| N2, two fresh exteriors per genome (seeds 7931, 7932) | 13 of 282 (4.6%) | 6 of 282 (2.1%) | N2's base rate in M4c's census: 1.72% |
| each host's T graph, one fresh exterior (seeds 7941 to 7950) | 25 of 1410 (1.8%), 0 to 4 per host | 10 of 1410 (0.7%) | the T arm: 64 of 10,240 (0.62%) |

In N2 the selected trials are 13 separate states, 268 fading and 1 unresolved; 12 distinct donor genomes switch in at
least one of their two redraws, and one in both. In the hosts, 3 selected and 10 control trials are unresolved. The
controls are consistent with their references (2.1% against 1.72%; 0.7% against 0.62%).

*After the data:* the selected/control ratios are 2.2 in N2 and 2.5 in the hosts (descriptive; in N2 alone, 13
against 6 is small). Keeping these core parameters was usually not enough to keep the switch under the tested exterior
redraws; this joint redraw cannot say how much of the dependence lies in which part of the rest (Astra). The companion
transfers weights and neuronal parameters together, and reclassification shows continued switching, not that the
original roots are kept (the plan).

## What this means for the roadmap

*Interpretation, after the data.*
- **The fixed reading is unresolved, and the rule that made it so is the unresolved genomes.** On the resolved genomes
  the screen points to a transplant benefit without a wiring advantage of 0.004 or more over rewired copies; over
  every assignment of the unresolved genomes it cannot exclude one. No assignment makes it positive.
- **What is robust:** N2's head-core block, placed into fresh null graphs with random parameters, raises the share of
  separate-states genomes over the intact host, in every host and over every assignment of the unresolved genomes
  (counted: from 0.04% to 0.62%). On the counted genomes its rewired copies at the same degrees reach 0.51%, and random
  placement of the same edges 0.23% (descriptive). How much N2's exact wiring adds is between "less than 0.004" and
  "not excluded".
- **The size of what is left.** T − R is small in this sample: +0.0012 counted, and +0.0061 (lower bound 0.0037) with
  every unresolved genome given to T; these ends bound the sample's result, not the true effect. At δ = m the
  positive rule fires in at most 4.5% of simulated screens, as expected at the null boundary, whatever the number of
  hosts (Astra; draft 2 wrongly read this as a ten-host power limit). Whether a confirmatory test is feasible needs a
  power calculation for specified effects above m, the hosts' variability, a planned treatment of unresolved genomes
  (for example a second, longer classification of every arm's unresolved genomes, fixed in advance; the unresolved
  share is 0.3 to 0.5% of genomes here) and a margin set against the hosts' observed base rate (0.04% here, a third of
  the 0.12% the plan took from M2's reference graphs) (Fable, Astra).
- **The plan's limits stand.** Ten hosts; one draw of each control block per host; the boundary, the exterior and
  the gap layer are the hosts'; random parameters; one classifier at one horizon. A response confined to a minority
  of host graphs may be missed.
- **The next step** (the plan's rule for an unresolved reading: reported, no extension without a new plan, decided
  with both reviewers and, if it changes direction, the owner). Both reviewers recommend publishing this screen as
  unresolved and putting the direction to the owner, and neither recommends resolving the 86 unresolved T and R
  genomes now: a resolution could only give the second reading or "Unresolved" (possibly its single-host form), any procedure
  would be chosen knowing which way the genomes lean, and most of them are unsettled histories rather than near-miss
  second states. It stays available as a separately planned, after-the-data add-on if a crisp label is needed (Astra:
  only if the exclusion at 0.004 would decide something consequential). The choices for the owner:
  - the M1 to M4 write-up (Astra's priority);
  - a separately planned study of what a dense block carries (density and degrees), which the data favour over the
    wiring question: T − I and R − I are above zero in every host and over every assignment, D − I over every
    assignment, and R − D on the counted genomes only (its envelope reaches −0.0043) (Fable, Astra);
  - an M5 transplant test of N2's wiring, whose feasibility needs the power calculation above.

## Deviations and notes

- **What ran:** no deviation from the plan.
- **What is committed:** `blocks.json` stays local. It holds N2's C3 chemical weights edge by edge (T's entries; P's
  carry its edge positions and weight multiset; R's and Rr's its within-block degrees and out-strengths), which rule 1
  forbids committing. The plan listed it among the outputs without saying it would be committed; `.gitignore` now
  names it. The committed `blocks-summary.json` gives each block's edge count, weight, autapses, reciprocal pairs and
  degree ranges, the swap chains, and the local file's sha256 (`9e435cb6…`).
- **What is reported:** the plan listed "each block's in- and out-degrees" beside the reading; for R, Rr, P and T
  those are N2's within-block degree sequence, so they are reported as ranges only (Fable).
- **`hosts.json`** carries each host's per-neuron in- and out-degrees within the block. Those are degrees of seeded
  null graphs (94 to 127 edges among C3's neurons, against N2's 260), not N2's, and carry no edge list or weights; the
  file is a run output written before the arms ran, left as written.
- Everything in the per-end, ladder, Rr, P-and-T, overlap, not-settled, companion-ratio and write-measure
  interpretations is after the data; the plan fixed only the reading and the items reported beside it.

## Reproduce it

**Check the published records** (needs the fetched connectome; minutes):
```
py scripts/memory_m4/m4d.py hosts blocks   # regenerates the hosts (stops if they differ from hosts.json) and
                                           # writes the local blocks.json from its seeds
py scripts/memory_m4/m4d_read.py           # verify_run, then the reading from the committed panels
py scripts/memory_m4/m4d_tables.py > runs/memory-m4d/tables.txt   # stops if blocks.json's sha256 differs from
                                                                   # blocks-summary.json's
```
With the committed panels in place, `m4d.py arms` validates and skips them rather than recomputing them. `m4d.py`
runs inside the compute accounting, so these checks append an attempt to the local, untracked `compute.json`; the
committed `m4d-compute-record.json` is the run's.

**A fresh run** (about 26 CPU hours here): set `MEMORY_M4D_OUT` to a new folder, then
`py scripts/memory_m4/m4d_read.py coverage` (before any arm, as in the plan), `py scripts/memory_m4/m4d.py`, `py
scripts/memory_m4/m4d_read.py`, and `py scripts/memory_m4/m4d_tables.py`, all with the same `MEMORY_M4D_OUT`.
