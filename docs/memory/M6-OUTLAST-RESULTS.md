# M6, step 1: do the switches' states outlast the input? — results

*Draft 2, 2026-10-30, after one round of review (Astra 6 and Fable 5.1: both "fix then publish"; every fix taken;
draft 1, the prompt and the reviews are in
[`docs/reviews/20261030-m6-outlast-results/`](../reviews/20261030-m6-outlast-results/)). Astra recomputed the reader's
output exactly and checked every match and outcome against the local root arrays; Fable re-derived the counts from the
records. Exploratory and descriptive: the plan ([`M6-OUTLAST-PLAN.md`](M6-OUTLAST-PLAN.md), draft 2, D380) fixed the
genomes, the phases, the measures and the wordings before the run. Nothing here is a pre-registration.

Numbers come from `runs/memory-m6-outlast/`:
- `genomes.json`, the manifest;
- `run.json`, one row per genome, with each phase's class, the root match, B's separations and C's root distances;
- `reading.json`, written by [`outlast_read.py`](../../scripts/memory_m6/outlast_read.py), with no simulation;
- the logs `run_log.txt` and `read_log.txt`;
- the compute record `outlast-compute-record.json`.

The arrays of roots (`roots.npz`) stay local. Tables that cross the planned measures come from `run.json`, and the
text says so. Interpretations the plan did not fix are marked **after the data**.*

## In short

**In the fixed wordings, as the reader writes them:**
- **F0:** "54 of 169 switches held two states during a 2000-tick removal of the food input", and "53 of 169 switches
  returned to their original states after a 2000-tick removal of the food input".
- **Z:** "55 of 169 switches held two states during a 2000-tick removal of all sensory input (1 unresolved)", and
  "54 of 169 switches returned to their original states after a 2000-tick removal of all sensory input".

**About a third held two stable states with no sensory input; most of the rest faded to one state.**
- **During the removal (Z),** 55 of 169 held: 32.5% to 33.1% over the unresolved bounds, with 95% intervals of 26% to
  40% and 26% to 41%. The other 114 were:
  - 112 that faded to one state;
  - 1 that settled into a single persistent oscillation (seed 7600, genome 1019);
  - 1 that was unresolved.
- **After restoration,** 54 returned to their original two states. 53 of these had held, and the other was the
  unresolved genome. Of the 112 that faded, 111 ended with both histories in the rising-start history's state.
- **The two arms agree** on whether a switch held for 163 of the 169 genomes, and on the outcome after restoration
  for 162.

**What "held under Z" means.** By the classifier's rules, two located fixed points, each linearly stable and each
reached by its history, under zero sensory current with the biases kept. That is stronger than "still apart at tick
2000".

**What this means (after the data).**
- **The switches sort into the two kinds M6-3 listed.** About a third hold their two states when the sensory input
  is removed. That is the kind Liu J et al. 2022 describe, a state kept "when external input terminates".
- **Most of the rest are like Kunert-Graf et al. 2017's coexisting states under constant input.** From these two
  starts, the two states did not survive the removal.
- **For the switches that merged, the food channels are what sustain the bistability** (Fable). F0, which removes only
  food, and Z give the same answer almost everywhere.
- **This refines the switches' input dependence.** It does not take any of them outside known attractor mechanisms.
  D378's annotation in [`SYNTHESIS.md`](SYNTHESIS.md), "attractors of a known kind", holds for all 169 (Astra, Fable).

**Every check passed:**
- the run was complete, in 0.20 CPU hours;
- all 169 genomes reproduced their census class in A;
- all 169 rebuilt roots equal the census's stored roots, with a largest difference of 0.0. The compared roots are
  Newton-refined in float64, so the same roots were located; the float32 trajectories were not compared (Fable);
- the 4 genomes seen before the plan merged in the run too.

## The run

- **One attempt, completed.** The compute record shows 731 s, category probe, no failed attempts, at commit 7e3e5e7,
  the plan's.
- **169 genomes in 10 panels,** each run through A, then B and C for each arm.
- **Consistency:** 169 of 169 reproduced the census class; no genome was excluded.
- **Census roots:** all 169 within 1e-6 of the stored roots, with a largest difference of 0.0, after the change of
  batch composition from the census's chunks of 128 to 12 to 26 genomes here.

## The measures

| | F0 (food off) | Z (all sensory input off) |
|---|---|---|
| Held in B | 54 (32%; 95% interval 25% to 39%) | 55, 1 unresolved (32.5% to 33.1%; intervals 26% to 40% and 26% to 41%) |
| B's other classes | fading 114, persistent oscillation 1 | fading 112, persistent oscillation 1, unresolved 1 |
| Recovered in C | 53 (31%; 25% to 39%) | 54 (32%; 25% to 39%) |
| Merged in C | 115: both at the rising-start root 114, at the falling-start root 1 | 114: rising-start 112, falling-start 2 (one of them a genome that held in B) |
| Other in C | 1 | 1 |

**B's status against C's outcome** (from `run.json`; Astra's table):

| Arm | B | Recovered | Merged | Other |
|---|---|---|---|---|
| F0 | held | 53 | 0 | 1 |
| F0 | not held | 0 | 115 | 0 |
| Z | held | 53 | 1 | 1 |
| Z | not held | 0 | 113 | 0 |
| Z | unresolved | 1 | 0 | 0 |

**Notes on the table:**
- **The oscillating genome** (seed 7600, genome 1019) is among the "not held". Its histories were still 2.5 (F0)
  and 2.1 (Z) apart at B's end. In C they joined at the rising-start root.
- **The "other" genome** (seed 7806, genome 559) was read-out silent in B under both arms. In C, one history was
  back at its own A root and the other at a third root. Its read-out difference there was 0.001, against 0.82 in
  A. It counts as "separate states" only relative to B's end, as the plan intended.
- **Where the arms differ.** On the outcome, 7 genomes differ between the arms: two each in seeds 7805 and 7808, and
  one each in 7700, 7802 and 7803.

**How fast the separation falls** (B's separation between the two histories, the maximum absolute state difference;
median over all 169):

| Tick of B | 0 | 10 | 30 | 100 | 300 | 2000 |
|---|---|---|---|---|---|---|
| F0 | 4.32 | 4.25 | 3.30 | 0.20 | 1.1e-4 | 8.4e-5 |
| Z | 4.32 | 4.25 | 3.35 | 0.20 | 9.2e-5 | 8.0e-5 |

In the genomes that faded, most of the separation was lost between ticks 30 and 300. The largest separation, 8.6 to
8.7 throughout, comes from one held genome (seed 7808, genome 795).

**By subclass and panel** (the reader's breakdowns are of C's outcome):
- All 4 read-out-silent switches merged under both arms.
- Of the 165 switches with a read-out difference, 53 (F0) and 54 (Z) recovered.
- The recovery rate under Z by panel runs from 4 of 21 (19%, seed 7806) to 8 of 19 (42%, seed 7802).

**Beside the reading (after the data; not fixed in the plan):** the 55 switches that held under Z had a larger median
distance between their two A roots (5.37) and a larger median read-out difference (0.52) than the 113 that did not
hold. Those had 3.84 and 0.36; against the 112 that faded, 3.85 and 0.35. That is description only, with no
interval.

## What this does and does not establish

**It establishes:**
- **Multistability without sensory input,** in the 55 held cases: at least two locally stable fixed points under zero
  sensory current, reached from the two histories, with the biases kept.
- **Loss of the tested distinction** in the 112 that faded.

**It does not establish:**
- **That the input-free states are A's states.** The roots move under Z; for example, the distance between seed 7600's
  genome 227's two roots is 4.86 under Z and 5.06 in A. "Recovered" shows that each maps back to its own A state when the
  input returns, which is the test that matters (Fable).
- **Exactly two attractors,** or that every held pair returns: two of the 55 did not.
- **That the switches that faded have no other input-free attractor.** The two starts can enter one basin while other
  input-free attractors remain (both).
- **Anything about basin size or robustness.** The model is deterministic and noiseless, so "the bit outlasts the gap"
  holds for a quiet gap (Fable).
- **The effect of a shorter interruption or a partial reduction.** The test was an abrupt removal of 2000 ticks.
- **Anything about behaviour.**

## What this means for the roadmap

**On the thread's question:** the switches are of the two known kinds M6-3 listed, in a ratio of roughly one to two.
About a third are multistable without sensory input. Most of the rest are two states that, from these starts, need
the food input. **Next, by the owner's order (D379):** a test of whether the evolved champions' fading history effect
matters for their foraging, designed and costed first; then the thread stops.

## Deviations and notes

- **None from the plan.** The run, the measures and the wordings are as fixed.
- **The smoke run was not representative.** Its 4 genomes all merged, while the full run shows a third holding. The
  plan disclosed them and kept them in, and they are in every count.

## Reproduce it

```
MEMORY_M6_OUTLAST_OUT=runs/outlast-rerun python scripts/memory_m6/outlast.py   # a fresh folder; about 12 minutes
MEMORY_M6_OUTLAST_OUT=runs/outlast-rerun python scripts/memory_m6/outlast_read.py
python scripts/memory_m6/sabotage_outlast.py   # rule 9: 23 sabotages, each caught
```

The run stage skips itself where `run.json` exists, so a rerun needs a fresh output folder (Astra). The census records
are committed; their local state arrays are needed only for the root comparison. CPU runs repeat exactly on the same
machine and platform (AGENTS.md rule 6).
