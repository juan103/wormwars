# M4b: is the switch held where its states differ? — results

*Draft 1, 2026-10-23, for review by Astra 6 and Fable 5.1. Exploratory: the plan ([`M4B-PLAN.md`](M4B-PLAN.md), draft
3, agreed after three rounds; D359) fixed the arms, the controls, the outcome and the reading before anything ran.
Nothing here is a pre-registration. Numbers come from `runs/memory-m4b/`: the panel records (`<panel>.json`) and
`readings.json` (written by [`m4b_read.py`](../../scripts/memory_m4/m4b_read.py), its console output in
`read_run.txt`). Anything the plan did not fix is marked **after the data**.*

## In short

- **The reading is "unresolved".** N2 is clear: cutting the edges among a switch genome's 30 most-differing neurons
  for 30 ticks erases its switch in 89% of N2's 28 genomes, against 31% under as many weight-matched exterior edges
  and 11% under as many outgoing edges (D = +0.58 and +0.79; 90% intervals 0.44 to 0.71 and 0.62 to 0.93). In the
  selected graphs the own cut erases 31% against 11% for either control (D = +0.20 and +0.21), but the intervals,
  resampled over the 10 graphs, run from −0.03 and −0.02 to 0.44: the plan needs both lower bounds above 0.10.
- **After the data, the selected graphs split in two.** In SH-class-2030099 and SH-recip-2050040 the own cut erases
  83% and 90% of their switches against 1% to 7% for the controls; in the other eight it erases about as many as the
  controls do (6% to 42%, against 2% to 39%). The group's interval is wide because of that split, not because the
  effect is small everywhere.
- **The reference and core-frozen groups (not read) look like N2:** the own cut erases 55% and 75% of their switches,
  against 19% and 24% to 29% for the controls, with both contrasts' 90% intervals at or above 0.19.
- **The dissection of N2's core (description):** cutting only **RIA's** C3-internal edges (RIAR's 26 or RIAL's 29 of
  C3's 260) erases 20 and 17 of N2's 28 switches; C3's whole internal set erases 26. Next come SMDV (13 and 11) and RMD
  (10 each); 14 of C3's 30 neurons, cut alone, erase none, and 5 erase one. C3 without the read-out erases 21; the read-out among
  themselves 3.

## The run

- Run on 2026-10-23 from 07:13 UTC, 41 minutes on the CPU of the tested machine, at commit e04366e (D359), all
  panels in order (`runs/memory-m4b/m4b_log.txt`, a copy of the local `m4b.log`; exit 0). Compute
  (`m4b-compute-record.json`, a copy of the local `compute.json`): 2.65 × 10⁸ neural updates and 2487 s, category
  probe.
- **Every check passed.** All 29 panels present and validated on reading (genome ids, graph, role, every arm, info);
  every genome's intact arm kept both roots (512 of 512); N2's intact and C3 outcomes equal M4a's Part 2 exactly. No
  genome had an empty own set; 3 N2 genomes had fewer outgoing edges than own edges and kept them all (D_out without
  them: +0.76).
- **The own sets:** N2's 30 most-differing neurons enclose 162 to 172 edges (terciles; median 168) and overlap C3 in
  14 neurons (median); they hold 0.99 of the states' squared difference (median). On the selected graphs, 84 edges
  (median), overlapping C3 in 6, holding 0.94.

## The reading

| Group (resampling unit) | Genomes | Own cut erased | Exterior controls | Outgoing controls | D_ext (90%) | D_out (90%) |
|---|---|---|---|---|---|---|
| **N2** (genomes, one graph) | 28 | 0.893 | 0.314 | 0.107 | +0.579 (0.436 to 0.707) | +0.786 (0.621 to 0.929) |
| **Selected** (10 graphs) | 387 | 0.313 | 0.112 | 0.108 | +0.201 (−0.027 to 0.437) | +0.205 (−0.019 to 0.444) |
| Reference (11 graphs), not read | 38 | 0.553 | 0.189 | 0.189 | +0.363 (0.227 to 0.480) | +0.363 (0.190 to 0.508) |
| Core-frozen (genomes, 3 graphs), not read | 52 | 0.750 | 0.288 | 0.238 | +0.462 (0.342 to 0.573) | +0.512 (0.400 to 0.623) |
| Hub-frozen (genomes, 3 graphs), not read | 7 | 0.429 | 0.200 | 0.143 | +0.229 (−0.114 to 0.600) | +0.286 (0.086 to 0.514) |

**The reading: "unresolved"** (`readings.json`). N2 meets both conditions; the selected graphs meet neither lower
bound, and their upper bound against the exterior (0.437) is above the margin, so it is not "not shown" either.

Not every outcome is "kept" or "erased" (`readings.json`, `outcomes`): under the own cut, 1 N2 genome, 16 selected,
8 reference and 9 core-frozen genomes were "not reached", 1 selected and 1 core-frozen genome swapped; "not reached"
counts as not erased, as the plan says.

**By the own set's size** (terciles within each group, pre-stated): in N2 the own cut erases 80%, 100% and 89% across
the terciles, with the exterior controls falling from 44% to 7%; in the selected graphs 27%, 45% and 21%, against 9%
to 13% for either control. The selected graphs' own sets (median 84 edges) are half the size of N2's; a weaker
effect there is not, by the plan's pre-statement, evidence against the targeting rule.

## The selected graphs, per graph (after the data)

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

In two graphs the targeted cut erases nearly every switch and the controls almost none, as in N2; in four it erases
under 10%, as the controls do; the rest lie between. Why these two differ is not addressed here: their own sets are
of ordinary size. In M4a's Part 2, C3's cut (N2's neurons) erased few switches in these graphs; with each genome's own
neurons, two graphs respond as N2 does.

## The dissection of N2's core (description)

Erased of N2's 28 switches, each cut alone for 30 ticks (`readings.json`, `dissection`):

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
| AIBL's; RMGL's, RIBR's, RMDVL's, CEPDR's, RIBL's | 10; 13 to 16 | 2; 1 each |
| the other 14 neurons' (among them RIS, RICL/R, SMDDR, the CEP and RMDD/V cells) | 8 to 26 | 0 |

Edge count does not explain the order: RIS's 26 edges and SMDDR's 25 erase none, RIAR's 26 erase 20. The three
partition arms together are C3's whole set; no partition alone matches it.

## What this means for the roadmap

*Interpretation, after the data.*
- **The fixed reading is "unresolved"**: preferential erasure under the targeting rule holds clearly in N2 and is not
  shown across the selected graphs as a group.
- **In N2, the switch has a small, specific handle.** Cutting about 26 to 29 edges of RIA inside the head core erases
  most of N2's switches, and 14 of C3's 30 neurons cut alone erase none. RIA already stood out in 03m and 03mc:
  deleting it cut N2's food response by 61% while P4 stayed within 0.02 (D294 to D300). Here RIA's connections within
  the core are what keeps the two remembered states apart. A single neuron's edges are a description on 28 genomes,
  not a test.
- **Across graphs, the picture is mixed:** two of the ten selected graphs, the reference graphs and the core-frozen
  shuffles respond to the targeted cut as N2 does; most of the selected graphs do not. Whatever holds those graphs'
  switches is not, for most of their genomes, the connections among the 30 most-differing neurons.
- **Next, for a decision with the owner and the reviewers:** a test of RIA's role, pre-specified now that the
  dissection points to it, on fresh N2 draws: RIA's C3-internal edges against weight-matched sets of other neurons'
  C3-internal edges, from the roots; and whether the two selected graphs that respond have an RIA-like hub among their
  most-differing neurons. M5's transplant, if pursued, would start from RIA's local wiring.

## Deviations and notes

- None from the plan in what ran. The per-graph table and its interpretation, and the dissection's order, are after
  the data.

## Reproduce it

```
py scripts/memory_m4/m4b.py         # about 41 CPU minutes; needs M2's census arrays and M4a's Part 2 records
py scripts/memory_m4/m4b_read.py    # the reading; seconds
```
