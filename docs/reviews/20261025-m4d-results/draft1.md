# M4d: does N2's head core carry the switch into other graphs? — results

*Draft 1, 2026-10-25, for review by Astra 6 and Fable 5.1. Exploratory: the plan ([`M4D-PLAN.md`](M4D-PLAN.md), draft
5, agreed after four rounds; D363) fixed the hosts, the arms, the genomes, the outcome, the reading and the rules after
it before any arm ran. Nothing here is a pre-registration. Numbers come from `runs/memory-m4d/`: the hosts' records
(`hosts.json`), the blocks' summary (`blocks-summary.json`; the full `blocks.json` stays local, below), one record per
host and arm (`arms/<host>__<arm>.json`), `companion.json`, `coverage.json` (written before any arm ran),
`readings.json` (written by [`m4d_read.py`](../../scripts/memory_m4/m4d_read.py); console output `read_log.txt`), and
`tables.txt`, written after the data by [`m4d_tables.py`](../../scripts/memory_m4/m4d_tables.py) from those records (no
simulation). Interpretations the plan did not fix are marked **after the data**.*

## In short

- **The reading is "Unresolved (the unresolved genomes decide it)".** On the genomes the classifier resolved, the
  reading would be the plan's second: "A transplant benefit; an advantage of C3's wiring of m or more over rewired
  copies ruled out, as a mean across these ten hosts". Over every assignment of the unresolved genomes, the upper
  bound of T against R reaches 0.0087, above the margin of 0.004, so the exclusion does not hold.
- **The transplant raises the share of separate-states genomes in every host.** Pooled over ten fresh hosts of 1024
  genomes each, 4 of 10,240 intact-host genomes have separate states (0.04%) and 64 with N2's block in place of the
  host's (0.62%). T exceeds I in all ten hosts; D_TI = +0.0059 (90% interval 0.0048 to 0.0069), and its lower bound
  stays above the margin over every assignment of the unresolved genomes (0.0046).
- **The rewired copies get most of it.** R, N2's 260 edges rewired at fixed in- and out-degrees and out-strengths, has
  52 (0.51%); D_TR = +0.0012 (−0.0009 to 0.0032), and T exceeds R in 6 of the 10 hosts. P, N2's exact edges with
  shuffled weights, has 69 (0.67%). D, the same count, weights and autapses at random positions, has 24 (0.23%).
- **The unresolved genomes are as many as the effect.** T has 50 unresolved genomes and R 36, against a difference of
  12 separate-states genomes between them. Counting all of T's unresolved genomes for it gives D_TR = +0.0061 (0.0037
  to 0.0085); counting all of R's against it, −0.0023 (−0.0053 to 0.0006).
- **The companion** (description): M4c's 141 N2 switch genomes, keeping their C3 weights and their C3 neurons' τ and
  bias with everything else drawn fresh, have separate states in 13 of 282 in N2 (control 6) and 25 of 1410 in the
  hosts' T graphs (control 10). Most of those genomes' switches do not survive a fresh exterior.
- **What this does not show:** that N2's exact wiring inside the head core matters, or that it does not. The plan's
  rule for an unresolved reading applies: no extension without a new plan, and the next step is decided with both
  reviewers and, if it changes direction, the owner.

## The run

- **One invocation**, all four stages, from 2026-10-24 01:32 to 2026-10-25 03:52 UTC, on the CPU of the tested
  machine, at commit 6553a98 (D363), clean tree at start and end (`m4d-attempt.json`, a copy of the local attempt
  record; `m4d_log.txt`; exit 0). No GPU.
- **Compute** (`m4d-compute-record.json`, a copy of the local `compute.json`): one attempt, completed, 1.25 × 10¹⁰
  neural updates and 94,819 s (26.3 h), category probe, inside the 30-hour cap. The 70 panels took 25.2 h (`tables.txt`:
  I 2.7 h, the six block arms 3.4 to 4.1 h each), against the plan's 16.5 to 25. Panels finished on the evening of 24
  October took 2300 to 3200 s, against about 1250 s before; the CPU was probably shared then.
- **The hosts:** all ten from their first seeds, none skipped (SH-2011000, SH-2011001, SH-route-2021000,
  SH-route-2021001, SH-class-2031000, SH-class-2031001, SH-mirror-2041000, SH-mirror-2041001, SH-recip-2051000,
  SH-recip-2051001). Their C3 blocks hold 94 to 127 edges (weight 466 to 861, 0 to 4 autapses, 5 to 38 reciprocal
  pairs; SH-recip's two have 24 and 38).
- **The blocks:** every block arm has N2's 260 edges, weight 2347 and 8 autapses (`blocks-summary.json`). Every R and
  Rr reached its 5200 accepted swaps. Reciprocal pairs: D 33 to 45, R 35 to 48, Rr, P and T 75.
- **Every check passed.** The reader ran `verify_run` first (`read_log.txt`): the hosts regenerated to their content
  hashes, `blocks.json` rebuilt and equal to the saved one, every host's sham genome equal to `Genome.random`'s bit
  for bit, every arm graph changed only inside the block and matched its recorded hash, and every panel validated
  against its arm. All 70 panels are valid under M1's rule; no arm has more than 5% unresolved genomes in any host.

## The reading

| Contrast | Mean | 90% interval (hull) | Hosts above 0 | Envelope over the unresolved |
|---|---|---|---|---|
| **D_TI** (T − I) | +0.0059 | 0.0048 to 0.0069 | 10 of 10 | 0.0046 to 0.0125 |
| **D_TR** (T − R) | +0.0012 | −0.0009 to 0.0032 | 6 of 10 | −0.0054 to 0.0087 |

The interval is the hull of the host bootstrap and the Student-t interval, as the coverage simulation required
(`coverage.json`; `t_widened` true). The largest host differences are 0.0088 (T − I) and 0.0059 (T − R), so the
single-host guard (0.01) does not fire.

**The rules, in order** (`readings.json`): lower(D_TI) 0.0048 > 0.004 and upper(D_TR) 0.0032 < 0.004 give the second
reading. Recomputed on the envelope, lower(D_TI) 0.0046 still passes, but upper(D_TR) 0.0087 does not fall below the
margin and lower(D_TR) −0.0054 does not rise above it, so the envelope's reading is "Unresolved". The two differ, so
the reading is **"Unresolved (the unresolved genomes decide it)"**.

**Each end of the box** (hull intervals; `tables.txt`):

| Contrast | Counted only | Unresolved all against T | Unresolved all for T |
|---|---|---|---|
| T − I | +0.0059 (0.0048 to 0.0069) | the same (I has none) | +0.0107 (0.0090 to 0.0125) |
| T − R | +0.0012 (−0.0009 to 0.0032) | −0.0023 (−0.0053 to 0.0006) | +0.0061 (0.0037 to 0.0085) |

*Checked after the data:* no assignment of the unresolved genomes turns the reading positive. The bootstrap's lower
bound rises with every host's difference, and at the all-for-T end it is 0.00400, just above the margin; but the
Student-t lower bound there is 0.0037, so the hull's is too, and every other assignment has a bootstrap lower bound of
0.0039 or less (`tables.txt`). The reading can lie only between the second reading and "Unresolved".

## Every class by arm

Pooled over the ten hosts, of 10,240 genomes each (`tables.txt`):

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

**The unresolved genomes** (the classifier's first reason; `tables.txt`): in every block arm most are an "unconfirmed
candidate" (a second root located but not confirmed: 17 to 29 per arm), then Newton failures (4 to 12) and candidates
around a stable root (5 to 13). The intact hosts have none.

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

*After the data:*
- **The ladder.** About a third of T's rise over I comes with D (the count, weights and autapses at random positions;
  +0.0020 of +0.0059), and about four fifths with R (+0.0047). The ladder is not a chain of single additions (the
  plan), so these shares describe these arms, not separable causes.
- **Rr below R.** Keeping N2's 75 reciprocal pairs while rewiring gives fewer separate-states genomes than rewiring
  without them (32 against 52), so T − Rr is larger than T − R. Each host has one R and one Rr draw, and 15 of Rr's 32
  are in one host (SH-recip-2051000); Rr exceeds R in two hosts. One block draw per host does not separate the
  rewiring's effect from the particular draw.
- **P and T** are close (69 and 64): moving the weights among N2's own 260 edges changes little in this pool.
- **N2's gap junctions** inside the block add nothing here (50 against 64; interval includes 0).

## Write, hold and read (not read)

Medians by arm (`readings.json` "measures"; the read-out difference is over separate-states genomes only):

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
neurons; T writes a little less than D, R, Rr and P. Eligible genomes (a ≥ `START_FLOOR`) number 9726 to 9863 of
10,240 per arm. As the plan says, the write amplitude does not isolate keeping from writing.

## The circuitry companion (description)

M4c's 141 N2 switch genomes keep their C3-block chemical weights (signs included) and their C3 neurons' τ and bias;
everything else is a fresh draw. The control is the same fresh draws unchanged (`companion.json`; `tables.txt`):

| Where | Selected | Control |
|---|---|---|
| N2, two fresh exteriors (seeds 7931, 7932) | 5 + 8 = 13 of 282 (4.6%) | 4 + 2 = 6 of 282 (2.1%) |
| each host's T graph, one fresh exterior (seeds 7941 to 7950) | 25 of 1410 (1.8%), 0 to 4 per host | 10 of 1410 (0.7%) |

*After the data:* the selected parameters roughly double the share in both places, but 95% of N2's switch genomes
(269 of 282 classifications) lose the switch when everything outside the block is redrawn. In M4c's genomes the switch
depends on far more than the core's own parameters. The companion transfers weights and neuronal parameters together,
and reclassification shows continued switching, not that the original roots are kept (the plan).

## What this means for the roadmap

*Interpretation, after the data.*
- **The fixed reading is unresolved, and the rule that made it so is the unresolved genomes.** On the resolved genomes
  the screen points to a transplant benefit without a wiring advantage of 0.004 or more over rewired copies; over
  every assignment of the unresolved genomes it cannot exclude one. No assignment makes it positive.
- **What is robust:** N2's head-core block, placed into fresh null graphs with random parameters, raises the share of
  separate-states genomes from about 0.04% to about 0.6%, in every host and over every assignment of the unresolved
  genomes. Its rewired copies at the same degrees raise it to about 0.5%, and random placement of the same edges to
  about 0.2% (descriptive). Within this screen, much of what the block carries comes with its size, weights, degrees
  and out-strengths; how much N2's exact wiring adds is between "less than 0.004" and "not excluded".
- **The plan's limits stand.** Ten hosts; one draw of each control block per host; the boundary, the exterior and
  the gap layer are the hosts'; random parameters; one classifier at one horizon. A response confined to a minority
  of host graphs may be missed.
- **The rule for an unresolved reading:** reported, with the rule that made it so; no extension without a new plan;
  the next step decided with both reviewers and, if it changes direction, the owner. Options for that decision, none
  taken:
  - a planned resolution of the unresolved genomes in T and R (86 genomes), fixed before it runs and labelled as
    after this reading; it can move the reading only between the second reading and "Unresolved";
  - accepting the screen as it stands and closing the transplant thread's first stage: the owner decides whether M5
    tests a transplant at all, or density and degrees (the plan's second-reading branch), or whether the thread moves
    to the write-up of M1 to M4.

## Deviations and notes

- **`blocks.json` stays local.** It holds N2's C3 chemical weights edge by edge (T's entries, and P's), which rule 1
  forbids committing. The plan listed it among the outputs without saying it would be committed. The committed
  `blocks-summary.json` gives each block's edge count, weight, autapses, reciprocal pairs and degree ranges, the swap
  chains, and the local file's sha256 (`9e435cb6…`); `m4d.py` rebuilds the file from its seeds and `verify_run`
  compares it.
- None from the plan in what ran.
- Everything in the per-end, ladder, Rr, companion-share and write-measure interpretations is after the data; the
  plan fixed only the reading and the items reported beside it.

## Reproduce it

```
py scripts/memory_m4/m4d.py          # hosts, blocks, arms, companion: about 26 CPU hours here; resumes by panel
py scripts/memory_m4/m4d_read.py     # checks everything, then the reading; seconds
py scripts/memory_m4/m4d_tables.py > runs/memory-m4d/tables.txt
```
