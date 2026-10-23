# M4b: is the switch held where its states differ? — results

*Draft 3, 2026-10-23, after two rounds of review (Astra 6 and Fable 5.1, both "revise" twice, round 2 on reporting
corrections, all taken; drafts 1 and 2 and the reviews are archived in [`docs/reviews/20261023-m4b-results/`](../reviews/20261023-m4b-results/)). Exploratory: the plan
([`M4B-PLAN.md`](M4B-PLAN.md), draft 3, agreed after three rounds; D359) fixed the arms, the controls, the outcome and
the reading before anything ran. Nothing here is a pre-registration. Numbers come from `runs/memory-m4b/`: the panel
records (`<panel>.json`), `readings.json` (written by [`m4b_read.py`](../../scripts/memory_m4/m4b_read.py); console
output `read_run.txt`), and `tables.txt`, written after the data by [`m4b_tables.py`](../../scripts/memory_m4/m4b_tables.py)
from those records (no simulation). Interpretations the plan did not fix are marked **after the data**.*

## In short

- **The reading is "unresolved".** In N2, cutting for 30 ticks the edges among a switch genome's 30 most-differing
  neurons ("own") sends its two histories into one basin in 89% of the 28 genomes, against 31% under as many exterior
  edges and 11% under as many outgoing edges (D = +0.58 and +0.79; 90% intervals 0.44 to 0.71 and 0.62 to 0.93). In
  the selected graphs the own cut does so in 31%, against 11% for either control (D = +0.20 and +0.20), but the
  intervals, resampled over the 10 graphs, reach −0.03 and −0.02: the plan needs both lower bounds above 0.10.
- **The selected graphs are split** (the per-graph table is the plan's; its reading is after the data): in
  SH-class-2030099 and SH-recip-2050040 the own cut erases 83% and 90% of the switches, against 1% to 7% for the
  controls, and these two graphs hold 89 of the group's 121 own-cut erasures. In the other eight the own cut erases 6%
  to 42%, and in six of them fewer than the exterior control, three of them by 7 points or more (for example
  SH-2010091: 14% against 35%).
- **The other groups (not read):** the reference graphs (11 of the 30 have separate-states genomes) and the
  core-frozen shuffles go the same way as N2, less strongly: own 55% and 75%, against 19% and 24% to 29% for the
  controls; the hub-frozen shuffles' 7 genomes are inconclusive (own 43%; the exterior contrast's interval spans zero).
- **The controls are not fully weight-matched** (Astra, Fable): the exterior sets carry a median 0.92 to 0.95 of the
  own set's anatomical weight across the groups; the outgoing sets only 0.39 in N2 and 0.53 in the core-frozen shuffles (0.83 in
  the selected and reference graphs), because the stratification fell back to lighter edges where heavy outgoing ones
  ran short. The outgoing contrast in N2 is therefore weaker than its name says.
- **The dissection of N2's core (description, 28 genomes):** cutting only **RIA's** C3-internal edges (RIAR's 26 or
  RIAL's 29 of C3's 260) erases 20 and 17 of the switches; all of C3 erases 26; 14 of C3's 30 neurons, cut alone, erase
  none, and 5 erase one.

## The run

- Run on 2026-10-23 from 07:13 UTC, 41 minutes on the CPU of the tested machine, at commit e04366e (D359), all
  panels in order (`runs/memory-m4b/m4b_log.txt`, a copy of the local `m4b.log`; exit 0). Compute
  (`m4b-compute-record.json`, a copy of the local `compute.json`): 2.65 × 10⁸ neural updates and 2487 s, category
  probe.
- **Every check passed.** All 29 panels with separate-states genomes present and validated on reading (genome ids,
  graph, role, every arm, info); every genome's intact arm kept both roots (512 of 512); N2's intact and C3 outcomes
  equal M4a's Part 2 exactly. No own set was empty. For the 3 N2 genomes with fewer outgoing edges than own edges, all
  their outgoing edges were cut (D_out without them: +0.76).
- **The own sets:** N2's 30 most-differing neurons enclose 146 to 197 edges (median 168), overlap C3 in 14 neurons
  (median) and hold 0.99 of the states' squared difference (median); the selected graphs' enclose 52 to 127 (median
  84), overlap C3 in 6 and hold 0.94.

## The reading

| Group (resampling unit) | Genomes | Own cut erased | Exterior | Outgoing | D_ext (90%) | D_out (90%) |
|---|---|---|---|---|---|---|
| **N2** (genomes, one graph) | 28 | 0.893 | 0.314 | 0.107 | +0.579 (0.436 to 0.707) | +0.786 (0.621 to 0.929) |
| **Selected** (10 graphs) | 387 | 0.313 | 0.112 | 0.108 | +0.201 (−0.027 to 0.437) | +0.205 (−0.019 to 0.444) |
| Reference (11 graphs), not read | 38 | 0.553 | 0.189 | 0.189 | +0.363 (0.227 to 0.480) | +0.363 (0.190 to 0.508) |
| Core-frozen (genomes, 3 graphs), not read | 52 | 0.750 | 0.288 | 0.238 | +0.462 (0.342 to 0.573) | +0.512 (0.400 to 0.623) |
| Hub-frozen (genomes, 3 graphs), not read | 7 | 0.429 | 0.200 | 0.143 | +0.229 (−0.114 to 0.600) | +0.286 (0.086 to 0.514) |

**The reading: "unresolved"** (`readings.json`). N2 meets both conditions; the selected graphs meet neither lower
bound, and their upper bound against the exterior (0.437) is above the margin, so it is not "not shown" either.

**Every outcome** (genomes; the controls pooled over their 5 sets; `tables.txt`):

| Group | Own cut: kept / erased / swapped / other root / not reached | Exterior | Outgoing |
|---|---|---|---|
| N2 | 2 / 25 / 0 / 0 / 1 | 90 / 44 / 0 / 0 / 6 | 120 / 15 / 0 / 0 / 5 |
| Selected | 249 / 121 / 1 / 0 / 16 | 1625 / 217 / 0 / 0 / 93 | 1642 / 209 / 0 / 1 / 83 |
| Reference | 9 / 21 / 0 / 0 / 8 | 105 / 36 / 0 / 0 / 49 | 104 / 36 / 0 / 5 / 45 |
| Core-frozen | 3 / 39 / 1 / 0 / 9 | 138 / 75 / 0 / 0 / 47 | 155 / 62 / 0 / 0 / 43 |
| Hub-frozen | 0 / 3 / 0 / 0 / 4 | 20 / 7 / 0 / 0 / 8 | 20 / 5 / 0 / 0 / 10 |

"Not reached" counts as not erased, as the plan says.

**By the own set's size** (terciles within each group, pre-stated; `tables.txt`):

| Group | Tercile (genomes) | Own | Exterior | Outgoing | D_ext | D_out |
|---|---|---|---|---|---|---|
| N2 (bounds 162, 172 edges) | low (10) / mid (9) / high (9) | 0.80 / 1.00 / 0.89 | 0.44 / 0.42 / 0.07 | 0.10 / 0.20 / 0.02 | +0.36 / +0.58 / +0.82 | +0.70 / +0.80 / +0.87 |
| Selected (79, 90) | low (130) / mid (132) / high (125) | 0.27 / 0.45 / 0.21 | 0.13 / 0.11 / 0.10 | 0.10 / 0.09 / 0.13 | +0.14 / +0.34 / +0.11 | +0.17 / +0.36 / +0.08 |
| Reference (80, 91) | low (14) / mid (11) / high (13) | 0.57 / 0.55 / 0.54 | 0.19 / 0.18 / 0.20 | 0.14 / 0.25 / 0.18 | +0.39 / +0.36 / +0.34 | +0.43 / +0.29 / +0.35 |
| Core-frozen (120, 133) | low (18) / mid (18) / high (16) | 0.89 / 0.67 / 0.69 | 0.32 / 0.28 / 0.26 | 0.28 / 0.14 / 0.30 | +0.57 / +0.39 / +0.43 | +0.61 / +0.52 / +0.39 |
| Hub-frozen (85, 98) | low (3) / mid (2) / high (2) | 0.33 / 0.00 / 1.00 | 0.00 / 0.40 / 0.30 | 0.20 / 0.00 / 0.20 | +0.33 / −0.40 / +0.70 | +0.13 / 0.00 / +0.80 |

The selected graphs' own sets (median 84 edges) are half the size of N2's; by the plan's pre-statement, a weaker
effect there is not evidence against the targeting rule.

**The controls' weight** (per genome, the mean over its 5 control sets of their summed anatomical weight, over the own
set's; the median over genomes;
`tables.txt`): exterior 0.92 to 0.95 in every group; outgoing 0.39 (N2), 0.53 (core-frozen), 0.69 (hub-frozen), 0.83
(selected) and 0.84 (reference). The outgoing controls in N2 and the core-frozen shuffles carry about half the own
set's weight or less, which favours the own cut against them; the exterior controls are close to matched.

## Per graph

Every graph's E_own, E_ext and E_out is in `readings.json` (`per_graph`) and `tables.txt`. The selected graphs:

| Graph | Genomes | Own cut | Exterior | Outgoing | Own edges (median) |
|---|---|---|---|---|---|
| SH-class-2030099 | 35 | **0.829** | 0.006 | 0.011 | 85 |
| SH-recip-2050040 | 67 | **0.896** | 0.072 | 0.063 | 83 |
| SH-2010075 | 12 | 0.417 | 0.250 | 0.383 | 78 |
| SH-route-2020092 | 20 | 0.300 | 0.390 | 0.340 | 71 |
| SH-2010091 | 21 | 0.143 | 0.352 | 0.267 | 89 |
| SH-route-2020004 | 17 | 0.118 | 0.188 | 0.024 | 73 |
| SH-class-2030029 | 78 | 0.090 | 0.069 | 0.103 | 89 |
| SH-mirror-2040124 | 50 | 0.080 | 0.108 | 0.088 | 72 |
| SH-mirror-2040028 | 16 | 0.062 | 0.100 | 0.100 | 87 |
| SH-recip-2050039 | 71 | 0.056 | 0.065 | 0.082 | 98 |

*After the data:* in two graphs the own cut erases most switches and the controls almost none, as in N2. In
SH-route-2020092, SH-2010091 and SH-route-2020004 it erases fewer than the exterior control by 7 points or more. In
SH-2010075 it erases 42%, against 25% and 38%. In the remaining four the own cut and both controls all erase at most
11%; in three of them the own cut erases a little fewer than the exterior (by 1 to 4 points), and in SH-class-2030029
a little more. So six of the eight erase fewer under the own cut than under the exterior control (Fable, Astra,
round 2). Their own sets are of ordinary size. In M4a's Part 2, C3's cut
erased 0 of 35 and 2 of 67 switches in the two responding graphs. **RIA does not distinguish them:** RIAL or RIAR is among
the 30 most-differing neurons in 51% and 88% of their switch genomes, against 5% to 87% in the other eight
(`tables.txt`, last section; draft 2 gave the larger of the two neurons' frequencies, Astra).

## The dissection of N2's core (description)

Erased of N2's 28 switches, each cut alone for 30 ticks (every arm with its edge count: `tables.txt`):

| Cut (C3-internal edges) | Edges | Erased |
|---|---|---|
| all of C3 | 260 | 26 |
| C3 without the read-out | 136 | 21 |
| **RIAR's** | 26 | **20** |
| the read-out with the rest of C3 | 105 | 19 |
| **RIAL's** | 29 | **17** |
| SMDVL's, SMDVR's | 19, 21 | 13, 11 |
| RMDL's, RMDR's | 21, 24 | 10, 10 |
| SMDDL's | 25 | 7 |
| AIBR's; RIML's, RIMR's | 14; 24, 22 | 4; 3, 3 |
| the read-out among themselves | 19 | 3 |
| AIBL's | 10 | 2 |
| CEPDR's, RIBL's, RIBR's, RMDVL's, RMGL's | 12 to 16 | 1 each |
| CEPDL's, CEPVL's, CEPVR's, OLLR's, RICL's, RICR's, RIS's, RMDDL's, RMDDR's, RMDVR's, RMHL's, SAAVR's, SMBDR's, SMDDR's | 8 to 26 | 0 |

Edge count does not explain the order: RIS's 26 edges and SMDDR's 25 erase none, RIAR's 26 erase 20. The three
partition arms together are C3's whole set; no partition alone matches it.

## What this means for the roadmap

*Interpretation, after the data.*
- **The fixed reading is "unresolved"**: preferential erasure under the targeting rule holds clearly in N2, and is not
  shown across the selected graphs as a group. What the run shows is susceptibility to a temporary cut: the restored
  network keeps both roots, and "erased" means the two histories ended in one basin. The plan's limits stand: the own
  set is a concentrated subgraph whose feedback the controls do not match, a cut among the differing neurons perturbs
  the difference directly, and the outgoing controls are lighter than the own sets, most in N2.
- **In N2, a small set of edges is enough to erase most switches.** Cutting about 26 to 29 edges of RIA inside the
  head core sends most of N2's 28 switches into one basin, while 14 of C3's 30 neurons, cut alone, send none. There
  is no size-matched control for single neurons outside C3, so this is a description of where the switch is
  vulnerable, not evidence that RIA's connections store it. RIA was already prominent in 03mc, in a different way:
  deleting RIA bilaterally cut N2's food response by 61% with P4 within 0.02 (D294 to D300; a different population
and endpoint, Astra). That
  motivates looking at RIA; it does not confirm a mechanism.
- **Across graphs, the picture is mixed:** two selected graphs respond to the targeted cut as N2 does; the reference
  graphs and core-frozen shuffles go the same way, less strongly; in most selected graphs the cut does not erase most
  switches. Given their smaller own sets (pre-stated), that is not evidence about where their switches are held.
- **Next, for a decision with the owner and the reviewers:** a test of RIA, pre-specified now that the dissection
  points to it, on fresh N2 draws, from the roots: RIA's C3-internal edges against weight- and size-matched sets of
  other neurons' edges, inside and outside C3, with the outgoing-weight shortfall fixed. An RIA-based transplant (M5)
  would depend on that result.

## Deviations and notes

- None from the plan in what ran. The ordering and interpretation of the per-graph table, the RIA frequencies and the
  dissection's order are after the data; the per-graph reporting itself is the plan's (Astra).
- The weight imbalance of the outgoing controls was found in review, from the recorded weights; the plan recorded them
  but did not gate on them.

## Reproduce it

```
py scripts/memory_m4/m4b.py          # about 41 CPU minutes; needs M2's census arrays and M4a's Part 2 records
py scripts/memory_m4/m4b_read.py     # the reading; seconds
py scripts/memory_m4/m4b_tables.py > runs/memory-m4b/tables.txt
```
