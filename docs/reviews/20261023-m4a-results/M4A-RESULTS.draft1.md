# M4a: do the head core's connections help maintain the history difference? — results

*Draft 1, 2026-10-23, for review by Astra 6 and Fable 5.1. Exploratory: the plan
([`M4A-PLAN.md`](M4A-PLAN.md), draft 4, agreed after four rounds; D357) fixed the arms, the controls, the measures and
the readings before anything ran. Nothing here is a pre-registration. Numbers come from `runs/memory-m4a/`: the panel
records (`<panel>.json`), Part 2's records (`part2__<panel>.json`), `guard.json`, `stages.json` and `readings.json`
(written by [`m4a_read.py`](../../scripts/memory_m4/m4a_read.py), its console output in `read_run.txt`). Anything the
plan did not fix is marked **after the data**.*

## In short

- **The reading is "unresolved".** For the primary arm (C3's internal edges cut for ticks 1 to 30, read at tick 60),
  C3's cut costs more of the full-state separation than **every one of the 30 sampled external cuts of equal size**
  on both of N2's panels: D = +0.16 at seed 7600 and +0.39 at seed 7700. But at seed 7600 the 90% interval's lower
  end is 0.008, below the 0.10 margin, so that panel is "unresolved"; seed 7700 is "positive". The plan needs both.
  The smoke had predicted "unresolved", for another reason (seed 7700's collapse).
- **C3's cut is also far stronger at once,** as the plan says it would be: 0.24 of the separation gone three ticks
  into the window, against at most 0.07 for any sampled set. A positive reading would not have separated maintenance
  from that stronger initial disruption.
- **Descriptively, the separate-states genomes carry the effect.** On N2, C3's cut removes 0.82 and 0.91 of their
  separation at tick 60, against a median of 0.16 and 0.13 for the sampled sets. **Started from their two stable
  roots (Part 2), 26 of N2's 28 separate-states genomes end with both histories at one root after C3's 30-tick cut**,
  against 14% under the sampled sets. On the selected graphs, whose two states differ mostly off C3 (median fraction
  on C3 0.06), C3's cut erases 12%, the same as the sampled sets (12%). **After the data**, that is a location
  dissociation: cutting C3 erases the switch where the switch lies on C3.
- **Fading genomes lose about a third** of their separation under C3's cut (0.32, 0.33), against a sampled-set median
  of 0.04 and −0.04.

## The run

- Run from 2026-10-22 16:28 UTC to 22:50 UTC on the CPU of the tested machine, at commit 6351537 (D357), all stages
  in order (`runs/memory-m4a/m4a_log.txt`, a copy of the local `m4a.log`; exit 0). Compute
  (`m4a-compute-record.json`, a copy of the local `compute.json`): 2.23 × 10⁹ neural updates and 22,918 s (6.4 hours),
  category probe. By `stages.json`: the two N2 panels 18,517 s, Part 2 1185 s, the reference 3216 s.
- **The cost guard fired as planned.** The first N2 panel took 7360 s, not the smoke's linear 35 minutes (Fable had
  warned that scaling to 1024 strains might not be linear). The projection was 11.1 hours, above 8, so **the
  reference comparison was reduced to one graph per ensemble** (the first in the census's order: SH-2010013,
  SH-route-2020011, SH-class-2030024, SH-mirror-2040045, SH-recip-2050005; `guard.json`).
- **The gates passed.** The intact arm reproduced the census within 5.3 × 10⁻⁷ in a and |δy(30)| on both N2 panels
  (990 and 1003 eligible genomes). Every Part 2 genome's intact arm kept both roots (453 of 453).
- The sampled sets matched as the plan said, each on one property: the degree sets' mean summed endpoint degree 85.7
  to 86.2 against C3's 85.9, with Σ|w| 41.7 to 47.7 against C3's 83.0 (rand0 and rand19 shown; all in the records);
  the weight sets Σ|w| 74.0 to 76.6 at a mean endpoint degree of 66 to 67.

## The readings

| Arm (window, reading tick) | Panel | C3's loss L | Largest sampled loss | D (90% interval) | Collapse c | Reading |
|---|---|---|---|---|---|---|
| **C3-early-30** (1–30, 60), primary | 7600 | 0.505 | 0.347 | +0.159 (0.008 to 0.267) | 0.33 | unresolved (interval across the margin) |
| | 7700 | 0.540 | 0.154 | +0.386 (0.239 to 0.465) | 0.33 | positive |
| C3-early-10 (1–10, 60) | 7600 | 0.308 | 0.210 | +0.098 (−0.015 to 0.193) | 0.53 | unresolved (no collapse) |
| | 7700 | 0.145 | 0.074 | +0.070 (−0.069 to 0.143) | 0.52 | unresolved (no collapse) |
| C3-late-30 (31–60, 100) | 7600 | 0.771 | 0.511 | +0.261 (0.069 to 0.391) | 0.20 | unresolved (interval across the margin) |
| | 7700 | 0.806 | 0.409 | +0.398 (0.222 to 0.540) | 0.23 | positive |

**Combined, every arm reads "unresolved"** (`readings.json`, `readings`). The largest sampled loss was a
weight-stratified set in all six rows (the degree sets' largest: 0.219, 0.123, 0.097, 0.051, 0.344, 0.226).

**Beside the readings, not read** (the plan):
- **Immediate strength:** at the window's third tick, C3's cut has removed 0.24 (early windows) and 0.29 to 0.30 (late
  window) of the separation, against at most 0.062 to 0.067 and 0.025 to 0.026 for any sampled set.
- **The read-out share** tells the same story: C3's loss 0.57 and 0.50 (early-30) against the largest sampled 0.40 and
  0.11.
- **The whole exterior** (2696 edges) loses 0.22 and 0.15 (early-30), less than C3's 260 edges; the 5 uniform sets
  −0.08 to 0.18.
- **The effect-matched controls (flagged):** 526 and 539 genomes matched, the unmatched holding 76% and 77% of the
  intact tick-30 separation. On the matched genomes C3's loss is −0.22 and 0.00 (early-30) against their controls' 0.26
  and 0.08: the selection toward weakly affected genomes that the smoke showed, now on the real panels.
- **The write arm** (the cut during the ramp only) loses 0.16 and −0.02; **gaps off** for ticks 1 to 30 loses −0.07
  and −0.24 (the separation rises, as M1 found for gaps off).

## By class (descriptive)

| Early-30, tick 60 | Seed 7600 | Seed 7700 |
|---|---|---|
| Separate states: genomes | 15 | 13 |
| their loss under C3's cut (median over sampled sets) | 0.82 (0.16) | 0.91 (0.13) |
| their core collapse | 0.07 | 0.06 |
| Fading: genomes | 972 | 987 |
| their loss under C3's cut (median over sampled sets) | 0.32 (0.04) | 0.33 (−0.04) |
| their core collapse | 0.39 | 0.39 |

The separate-states genomes hold most of the intact separation at tick 60 (their v is 0.92 and 0.91 of their start,
against 0.12 and 0.10 for fading). Under the 10-tick cut they lose 0.56 and 0.24; under the late cut, 0.94 and 0.95.

## Part 2: the switch, from its roots (descriptive)

| Group | Genomes | Median fraction of the states' difference on C3 | Erased by C3's cut | Erased by the sampled sets (5 each, pooled) |
|---|---|---|---|---|
| N2 (both panels) | 28 | 0.90 | **26 (93%)**; 1 kept, 1 not reached | 14% (20 of 140); 82% kept |
| The selected graphs | 387 | 0.06 | 45 (12%); 85% kept | 12% (238 of 1935); 83% kept |
| The reference graphs | 38 | 0.26 | 8 (21%); 58% kept, 21% not reached | 21% (40 of 190); 54% kept |

"Erased": both histories end at the same stored root after the 30-tick cut and 300 ticks of the intact network
(M2's reaching rule, float64). Two of the 1935 sampled-set outcomes on the selected graphs reached a third root. On
N2, the C3 cut erases the switch in nearly every genome; where the states lie off C3 (the selected graphs), it erases
no more often than the sampled sets. **After the data,** this is the clearest result of M4a: in N2, C3's internal
connections are needed to keep the two stable states apart, and the effect follows the states' location, not the
cut's size. With 28 N2 genomes and sampled sets of equal size, it is a description, not a test.

## The reference, as a comparison (descriptive)

On the five reference graphs, C3 is N2's neuron set: those graphs keep 97 to 121 chemical edges inside it (N2: 260).
Cutting them for ticks 1 to 30 loses −0.02 to 0.14 of their separation at tick 60, within the range of their own 8
sampled sets (−0.01 to 0.17). N2's lead over these five graphs' mean v(60) is 0.094 intact and 0.011 under the cut
(`n2_lead_over_reference`): **cutting C3 removes most of N2's lead at tick 60**, but the cut is not like-for-like
(N2 loses 260 edges, the reference graphs about 110).

## What this means for the roadmap

*Interpretation, after the data.*
- **The fixed reading is "unresolved"**, on the margin at seed 7600, so M4a does not establish that C3's connections
  contribute more than equally sized external cuts. On the roadmap's decision rule (annotated in D357), nothing is
  dropped for "access".
- **The descriptions point one way.** C3's cut beats every sampled set at the point estimate in all six panel rows
  (D from +0.07 to +0.40); it erases nearly all of N2's switches from their roots while sampled sets erase few; and where switches lie off
  C3 it does no more than they do. What a positive reading could not have done is also not done here: C3's cut is
  nearly four times stronger at once, so "maintenance beyond a stronger initial disruption" is not separated.
- **For M4's next slices:** the switch result suggests the next test is on the separate-states genomes from their
  roots, where the outcome is binary and the location contrast exists: cutting subsets of C3 (the core dissection the
  roadmap lists), and cuts outside C3 placed on the states' own neurons in the selected graphs, which would test
  "location, not C3" directly. M5's transplant would then carry the structure that holds the switch.

## Deviations and notes

- **The reference was reduced to five graphs by the cost guard,** as the plan provided. The first N2 panel took 7360 s
  against the smoke's extrapolated 35 minutes.
- The largest sampled losses all came from the weight family, added in draft 3 after the smoke.
- The per-class and Part 2 statements are descriptive; the plan reads only the panel-level contrast.

## Reproduce it

```
py scripts/memory_m4/m4a.py         # about 6.4 CPU hours here; resumes by panel; needs M2's census arrays (local)
py scripts/memory_m4/m4a_read.py    # the readings; seconds
```
