# M6, option 0: is the history effect selection built a switch or slow fading? — results

*Draft 1, 2026-10-30, before review. Exploratory and descriptive: the plan ([`M6-0-PLAN.md`](M6-0-PLAN.md), draft 2,
D376) fixed the genomes, the probe, the classes, the comparisons and the readings before the run. Nothing here is a
pre-registration. Numbers come from `runs/memory-m6-0/`:
- the genome list (`genomes.json`) and the input banks (`banks.json`);
- each bank's first pass (`first-own.json`, `first-03mc.json`) and second pass (`second-own.json`,
  `second-03mc.json`); the saved states (`first-*-states.npz`) stay local;
- `reading.json`, written by [`m6_0_read.py`](../../scripts/memory_m6/m6_0_read.py) from those records, no
  simulation (console output `runs/m6-0-read-log.txt`);
- the compute record `compute.json`, and the run's log `runs/m6-0-run-log.txt`.

[`scripts/memory_summary.py`](../../scripts/memory_summary.py) reads `reading.json` into
[`summary.json`](summary.json) (`M6-0`). Interpretations the plan did not fix are marked **after the data**.*

## In short

- **The reading on switches is negative.** In the fixed wording, as the reader writes it: "We did not detect
  enrichment of probe-defined switches in g39 champions relative to the mutation-only control; 1 were found".
  - On the primary bank (each run's own), 1 of the 102 generation-39 champions is a switch (separate states), against
    5 of the 408 drift genomes and none of the 102 generation-0 champions.
  - g39 minus drift, by run, averaged over the 30 graph-and-run blocks: −0.015 (95% interval −0.044 to +0.013) with
    the unresolved drift genomes counted as non-switches, and −0.027 (−0.060 to +0.004) with them counted as
    switches. The plan needed at least 5 g39 switches and an interval above zero.
  - That one switch, T1-MS-N2 run 7's champion, fades on 03mc's bank. On 03mc's bank no g39 champion is a switch.
- **The persistence reading: "selection shortened the history effect's persistence against drift".** Per run, the g39
  champion's τ_stay exceeds a share of its drift replicates', minus one half. The mean over blocks is −0.095
  (−0.170 to −0.013), so the champion outlasts about 41% of its drift replicates rather than half. Against g00 the
  primary bank's interval spans zero (−0.075; −0.186 to +0.042). On 03mc's bank both are below zero.
- **What the effect is, then (after the data):** fast fading.
  - On the primary bank, the median g39 champion keeps 85% of its start difference after 5 ticks, 20% after 30 and
    0.4% after 100. τ_stay (the last time it drops below 10% for good) has a median of 39 to 46.5 ticks by family.
  - The champions' effect is about six times larger at the start (median a 0.161, against 0.026 for drift and 0.028
    for g00), and stays larger in absolute terms: about four times drift's at tick 30.
  - So the size of the effect is what selection built, not its duration. Measured relative to its size, it fades a
    little sooner than drift's.
- **Every check passed:**
  - the run was complete, in 0.96 CPU hours;
  - all 120 consistency checks against 02b passed (24 runs; largest relative difference 1.8e-4);
  - neither bank's audit of 20 fading genomes found a switch;
  - no g39 champion was unresolved on the primary bank, so the bounds cannot straddle the criterion.
- **Next steps, as the plan and the options note set them:** option 3 (biology, a literature review) or option 4
  (stop the thread here). This closes this probe's switch route for 02's champions only. It says nothing against
  useful memory in general, or against switches under other inputs.

## The run

- **One attempt, completed** (`compute.json`: 3445 s recorded, category probe, no failed attempts; commit e469ad1,
  the plan's). GPU hidden, and CUDA never initialised.
- **616 genomes on each of two banks:** g00 102, g39 102, g79 4, drift 408 (`genomes.json`). There are 30 blocks
  (N2 8, SH 16, N2perm 6), holding 49 distinct g00 genomes by parameter hash: the four mappings of one graph and run
  often share their g00 champion, as the plan expected.
- **First pass:** 904 s on the own bank and 799 s on 03mc's.
- **Second pass:** 32 genomes on the own bank (12 not fading + 20 audited) and 25 on 03mc's (5 + 20), about 15 and
  12 minutes. That is about 28 s a genome, against the plan's estimate of about 5 s (M4e's average). The total
  stayed under the plan's "under 1 CPU hour", far from the 5-hour cap.
- **The 16 genomes seen before the plan** (the spike: T1-M0-N2 g00 and g39 on 03mc's bank) are all fading here too,
  as the spike found. They are in every count.

## The checks before the reading

| Check | Result |
|---|---|
| Run complete (no cap) | yes |
| Consistency against 02b (`history.json`): a vs \|raw_turn final\|, d(5) vs \|raw_turn after\|, bank food vs `typical_food`, for the 24 T1-M0 N2 and SH runs' g00 and g39, within 2% or 1e-3 | 120 of 120; largest relative difference 0.00018 |
| Audit: 20 first-pass-fading genomes per bank, held to 22,000 ticks | all 40 still fading; 0 failures |
| Primary bank's unresolved g39 bounds straddling the criterion | no: 0 unresolved g39 |

## Every class

Classes after the second pass where it ran, by tag and family (switches / unresolved / n). Every genome not listed as
a switch or unresolved is fading, except one persistent oscillation on 03mc's bank (a drift genome).

| Tag / family | Own bank (primary) | 03mc's bank (secondary) |
|---|---|---|
| g00 / N2 | 0 / 1 / 32 | 0 / 0 / 32 |
| g00 / SH | 0 / 0 / 64 | 0 / 0 / 64 |
| g00 / N2perm | 0 / 0 / 6 | 0 / 0 / 6 |
| g39 / N2 | **1** / 0 / 32 | 0 / 0 / 32 |
| g39 / SH | 0 / 0 / 64 | 0 / 0 / 64 |
| g39 / N2perm | 0 / 0 / 6 | 0 / 0 / 6 |
| g79 / N2 and SH | 0 / 0 / 4 | 0 / 0 / 4 |
| drift / N2 | 2 / 1 / 128 | 1 / 1 / 128 |
| drift / SH | 1 / 1 / 256 | 1 / 0 / 256 |
| drift / N2perm | 2 / 1 / 24 | 0 / 1 / 24 |

**Every genome that was not fading on either bank** (first-pass class → after the second pass):

| Run | Genome | Own bank | a | 03mc's bank | a |
|---|---|---|---|---|---|
| T1-MS-N2 run 7 | **g39** | separate states | 0.175 | fading | 0.090 |
| T1-M0-N2 run 7 | g00 | unresolved | 0.077 | fading | 0.157 |
| T1-M0-N2perm1 run 1 | drift 1 | separate states | 0.014 | fading | 0.055 |
| T1-M0-N2perm2 run 0 | drift 3 | separate states | 0.028 | fading | 0.010 |
| T1-M0-N2perm2 run 1 | drift 2 | unresolved | 0.025 | unresolved | 0.021 |
| T1-MS-N2 run 1 | drift 0 | unresolved → fading | 0.056 | persistent oscillation | 0.009 |
| T1-MS-N2 run 4 | drift 1 | unresolved | 0.002 | unresolved | 0.006 |
| T1-MS-SH5 run 1 | drift 2 | separate states | 0.201 | separate states | 0.183 |
| T1-R1-N2 run 0 | drift 2 | separate states | 0.192 | fading | 0.021 |
| T1-R1-N2 run 4 | drift 1 | separate states | 0.042 | separate states | 0.043 |
| T1-R1-SH3 run 0 | drift 1 | unresolved → fading | 0.009 | fading | 0.002 |
| T1-R2-SH3 run 0 | drift 3 | unresolved | 0.116 | fading | 0.028 |

No genome was "separate states, read-out silent". Of the 6 switches on the own bank, 2 are also switches on 03mc's;
the other 4 fade there (**after the data:** the class depends on the input bank, as the plan's choice of a primary
bank anticipated). For context only: the drift genomes' switch share on 03mc's bank, 2 of 408 (0.5%), is in the
range of the census's random-genome rates (N2 under M0 about 1.5%, the shuffles near 0.1%). The g00 genomes are the
best of 32 random genomes, not random draws.

## The comparisons

**1. Switches, primary bank** (per run, g39's indicator minus the share of its four drift replicates that switch;
mean over the 30 blocks; 10,000 cluster resamples):

| Against | Unresolved counted as | Mean | 95% interval |
|---|---|---|---|
| drift | non-switches | −0.015 | −0.044 to +0.013 |
| drift | switches | −0.027 | −0.060 to +0.004 |
| g00 | non-switches | +0.008 | 0.000 to +0.025 |
| g00 | switches | 0.000 | 0.000 to 0.000 |

**2. Persistence** (per run, the share of eligible drift replicates whose τ_stay the g39 champion's exceeds, ties a
half, minus one half; mean over blocks):

| Bank | Against | Mean | 95% interval | Runs skipped (no eligible pair) |
|---|---|---|---|---|
| own (primary) | drift | −0.095 | −0.170 to −0.013 | 0 |
| own (primary) | g00 | −0.075 | −0.186 to +0.042 | 3 |
| 03mc (secondary) | drift | −0.116 | −0.182 to −0.050 | 0 |
| 03mc (secondary) | g00 | −0.194 | −0.285 to −0.099 | 4 |

**Medians of the restricted τ_stay** (ticks; eligible genomes, a ≥ 1e-3):

| Tag | Own: N2 | Own: SH | Own: N2perm | 03mc: N2 | 03mc: SH | 03mc: N2perm |
|---|---|---|---|---|---|---|
| g00 | 49 | 47 | 50 | 52 | 43 | 54.5 |
| g39 | 46.5 | 39 | 41.5 | 47 | 39 | 30.5 |
| g79 (2 + 2 genomes) | 69.5 | 50.5 | — | 59 | 48 | — |
| drift | 59 | 47 | 51.5 | 55 | 46 | 41 |

Censored ("beyond 2000") on the own bank: 1 g39 (the switch), 7 drift, 0 g00. Below the floor: 3 g00 and 7 drift.

**How the effect fades** (**after the data**; medians over eligible genomes, own bank; d(t)/a, and the absolute d):

| Tag | a | d(5)/a | d(30)/a | d(100)/a | d(30) | d(100) | Returns above 10% after first crossing |
|---|---|---|---|---|---|---|---|
| g00 | 0.028 | 0.79 | 0.23 | 0.0068 | 0.0064 | 0.00015 | 16 of 99 |
| g39 | 0.161 | 0.85 | 0.20 | 0.0039 | 0.0262 | 0.00050 | 5 of 102 |
| drift | 0.026 | 0.79 | 0.25 | 0.0088 | 0.0060 | 0.00026 | 116 of 401 |

The champions' larger effect also fades more cleanly. Few of them cross back above 10% after first dropping below it
(5 of 102, against 116 of 401 drift genomes), which may be one reason their τ_stay is shorter. This was not a fixed
comparison.

**3. Beside 02b** (the 24 T1-M0 N2 and SH runs): every g39 champion is fading. Every g00 champion is fading except
T1-M0-N2 run 7's, which is unresolved. On the own bank, the median a is 0.169 for g39 and 0.035 for g00, and the
median τ_stay is 40.5 and 45.5 ticks. The new drift genomes' a (median 0.023 over 96) sits beside 02b's drift
|raw_turn final| (median 0.035 over 96): two unpaired draws of the same control, never paired. The full table is
`reading.json` → `beside_02b`.

**4. The g79 snapshots:** all four are fading on both banks. On the own bank, their τ_stay against their run's g39
champion is 98 against 51 (T1-M0-N2 run 0), 41 against 50 (run 1), 57 against 24 (SH1 run 0) and 44 against 42
(SH2 run 0). Their a is 0.16 to 0.34. Four cases, no reading.

## What this means for the roadmap

The plan's branch for this outcome: the g39 champions are mostly fading, so the 02b effect is described by its
persistence, and options 3 or 4 are the honest next steps ([`M6-OPTIONS.md`](M6-OPTIONS.md)). Options 5 and 2 were
conditional on enrichment and are not taken.

**After the data:** selection on T1 made the history effect larger, not longer-lived. On this probe it is a transient
of a few tens of ticks, not a second stable state. Whether a transient this short is used in the task is a question for behaviour, not for this classifier.

## Deviations and notes

- **The second pass took about 28 s a genome,** not the 5 s the plan took from M4e's average. The reason was not
  examined. The total stayed under one CPU hour.
- **"1 were found":** the fixed wording's "N were found", with N = 1, reproduced as the reader writes it.
- **The CI poller for D376** passed a short commit hash to `gh run list --commit`, matched nothing and logged
  empty lines. D376's CI was checked by hand: green (run 41091349858).

## Reproduce it

```
python scripts/memory_m6/m6_0.py        # CPU, about 1 hour; needs 02's local T1 genomes (runs/exp02-screening/)
python scripts/memory_m6/m6_0_read.py   # writes runs/memory-m6-0/reading.json; seconds
python scripts/memory_summary.py        # writes docs/memory/summary.json
```

CPU runs repeat exactly on the same machine and platform (AGENTS.md rule 6). 02's genomes are not in the repository,
so the run needs a local copy of 02's screening outputs. The reader and the summary need only the committed records.
