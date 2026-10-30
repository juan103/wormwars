# M6, step 1: do the switches' states outlast the input? — results

*Draft 1, 2026-10-30, before review. Exploratory and descriptive. The plan ([`M6-OUTLAST-PLAN.md`](M6-OUTLAST-PLAN.md),
draft 2, D380) fixed the genomes, the phases, the measures and the wordings before the run. Nothing here is a
pre-registration. Numbers come from `runs/memory-m6-outlast/`:
- `genomes.json`, the manifest;
- `run.json`, one row per genome, with each phase's class, the root match, B's separations and C's root distances;
- `reading.json`, written by [`outlast_read.py`](../../scripts/memory_m6/outlast_read.py), with no simulation;
- the logs `run_log.txt` and `read_log.txt`;
- the compute record `outlast-compute-record.json`.

The arrays of roots (`roots.npz`) stay local. Interpretations the plan did not fix are marked **after the data**.*

## In short

**In the fixed wordings, as the reader writes them:**
- **F0:** "54 of 169 switches held two states during a 2000-tick removal of the food input", and "53 of 169 switches
  returned to their original states after a 2000-tick removal of the food input".
- **Z:** "55 of 169 switches held two states during a 2000-tick removal of all sensory input (1 unresolved)", and
  "54 of 169 switches returned to their original states after a 2000-tick removal of all sensory input".

**About a third of the switches keep two states with no sensory input at all, and two thirds need their input.**
- Under Z, 55 of 169 held: 33%, with a 95% interval of 26% to 41% over both unresolved bounds. Almost every one that
  held came back to its original two states when the input returned.
- The other 113 merged during the removal. After restoration, 112 of them had both histories in the rising-start
  history's state.
- F0 and Z agree on 163 of the 169 genomes.

**What this means (after the data).** The switches are not all of one kind.
- **About a third are multistable without any input.** The network alone holds the two states, so the bit set by the
  food history outlasts a 2000-tick absence of every sensory signal.
- **About two thirds are two states only under the held input,** the broad kind M6-3 found in earlier connectome
  models. They lose the bit when the input goes. On its return they settle into the rising-start state, as the plan
  expected for a step rise from a single input-free state.

**Every check passed:**
- the run was complete, in 0.20 CPU hours;
- all 169 genomes reproduced their census class in A;
- all 169 rebuilt roots equal the census's stored roots: the largest difference was 0.0, exactly;
- the 4 genomes seen before the plan merged in the run too.

## The run

- **One attempt, completed.** The compute record shows 731 s, category probe, no failed attempts, at commit
  7e3e5e7, the plan's.
- **169 genomes in 10 panels,** each run through A, then B and C for each arm.
- **Consistency:** 169 of 169 reproduced the census class. No genome was excluded, and the stop rule (a ninth failure)
  never came near.
- **Census roots:** all 169 within 1e-6 of the stored roots, with a largest difference of 0.0. The rebuild and the
  change of batch composition, from the census's chunks of 128 to 12 to 26 genomes here, changed nothing.

## The measures

| | F0 (food off) | Z (all sensory input off) |
|---|---|---|
| Held in B | 54 (32%; 95% interval 25% to 39%) | 55, 1 unresolved (33% to 33%; 26% to 41% over both bounds) |
| Recovered in C | 53 (31%; 25% to 39%) | 54 (32%; 25% to 39%) |
| Merged in C | 115: both at the rising-start root 114, at the falling-start root 1 | 114: rising-start 112, falling-start 2 (one of them a genome that held in B) |
| Other in C | 1 (new roots) | 1 (new roots) |
| B's classes | fading 114, separate states 53, read-out silent 1, persistent oscillation 1 | fading 112, separate states 54, read-out silent 1, oscillation 1, unresolved 1 |

**Held against recovered:**
- **Under F0,** every held genome but one recovered; the exception has new roots in C.
- **Under Z,**
  - 53 held and recovered;
  - 1 held and then merged;
  - 1 held, with new roots in C;
  - the unresolved one recovered.

**How fast the merging is** (B's separation between the two histories, the maximum absolute state difference; median
over all 169):

| Tick of B | 0 | 10 | 30 | 100 | 300 | 2000 |
|---|---|---|---|---|---|---|
| F0 | 4.32 | 4.25 | 3.30 | 0.20 | 1.1e-4 | 8.4e-5 |
| Z | 4.32 | 4.25 | 3.35 | 0.20 | 9.2e-5 | 8.0e-5 |

The merging genomes lose most of their separation between ticks 30 and 300. The largest separation stays near 8.7
throughout, from the genomes that hold.

**By subclass:**
- All 4 read-out-silent switches merged under both arms.
- Of the 165 switches with a read-out difference, 53 (F0) and 54 (Z) recovered.

**By panel:** the number recovered under Z ranges from 3 of 12 to 8 of 19 (`reading.json` → `by_panel`).

**Beside the reading (after the data; not fixed in the plan):** the switches that held under Z had a larger median
distance between their two A roots (5.37 against 3.84) and a larger median read-out difference (0.52 against 0.36)
than those that merged. That is description only, with no interval.

## What this means for the roadmap

**On the thread's question:** the model's switch is not one thing. About a third of N2's switches are input-free
multistability: the two states belong to the network's own dynamics and survive a full removal of sensory input.
The rest are two states that exist only under the held input. This refines M6-3's statement that the thread's
switches are "attractors of a known kind": that holds for about two thirds. For the other third, the comparison with
Kunert-Graf's input-dependent bistability does not apply.

**What it cannot show:**
- that a shorter interruption, or a partial reduction of the input, would also erase the states that merged;
- that the merged genomes have no other input-free attractor;
- anything about behaviour.

**Next, by the owner's order (D379):** a test of whether the evolved champions' fading history effect matters for
their foraging, designed and costed first; then the thread stops.

## Deviations and notes

- **None from the plan.** The run, the measures and the wordings are as fixed.
- **The smoke run's 4 genomes all merged,** and the full run shows that this was not representative: a third hold.
  The plan disclosed them and kept them in. They are in every count.

## Reproduce it

```
python scripts/memory_m6/outlast.py        # CPU, about 12 minutes; rebuilds the genomes from the census records
python scripts/memory_m6/outlast_read.py   # writes runs/memory-m6-outlast/reading.json; seconds
python scripts/memory_m6/sabotage_outlast.py   # rule 9: 23 sabotages, each caught
```

The census records are committed. Their local state arrays are needed only for the root comparison. CPU runs repeat
exactly on the same machine and platform (AGENTS.md rule 6).
