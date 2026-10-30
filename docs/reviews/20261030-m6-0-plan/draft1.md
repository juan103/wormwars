# M6, option 0: is the history effect selection built a switch or slow fading? — the plan

*Draft 1, 2026-10-30, for one round of review by Astra 6 and Fable 5.1. The owner chose option 0 of
[`M6-OPTIONS.md`](M6-OPTIONS.md) ("Sure, option 0"). Exploratory and descriptive: no pre-registration, but the
genomes, the probe, the classes, the comparisons and the readings are fixed here before the run. CPU only.*

## The question

02b found that 40 generations of selection on T1 built a history effect on the 0.25/1.75 food ramp: generation-39
champions turn differently after the two histories far more than generation 0 or a mutation-only drift control, and
most of the difference survives five more ticks ([`02b RESULTS`](../../experiments/02b-champion-analysis/RESULTS.md),
section 2). **Option 0 asks whether that effect is two stable states (a switch, as M1 to M4e found in a few random
genomes) or a slow return to one state, and how slow.** It does not test whether anything is used in the task
(that would be option 5).

**Seen before this plan.** A throwaway timing spike ran the first pass of M2's classifier on 02's eight T1-M0-N2 runs'
generation-0 and generation-39 champions, on 03mc's bank (the secondary probe below). All 16 were fading, with root
distances near 1e-15 and no read-out difference left at tick 300. Those 16 are therefore seen; they stay in the run,
and the reading says so. Nothing else has been looked at.

## The genomes

Every T1 genome 02 saved (`runs/exp02-screening/`, local, loaded with `allow_pickle=False`), selected by file name
only:

| Tag | What | Count |
|---|---|---|
| g39 | each run's best genome at generation 39 | 102: N2 32 (8 runs × 4 mappings), SH1-SH8 64 (2 runs × 8 graphs × 4 mappings), N2perm1-3 6 (M0) |
| g00 | each run's best of its 32 random generation-0 genomes | 102, the same runs |
| g79 | generation-79 snapshots, where they exist | 4: T1-M0-N2 runs 0 and 1, T1-M0-SH1 and SH2 run 0 |
| drift | each run's g00 mutated 39 times with the run's mutation settings (T1's `MutationConfig`: w 0.08, g 0.04, tau 0.15, bias 0.05) and no selection, 4 replicates, as in 02b | 408 |

The drift genomes are a new draw of 02b's control, made on the CPU: `torch.Generator("cpu")` seeded
20261101 + 10 × (run's index in `records.jsonl`) + replicate. 02b's own drift genomes were drawn on the GPU and are
not reproduced.

Each genome is run on its own graph (`grid.graph_for`), with T1's brain configuration for that graph
(`grid.brain_config_for_graph`), the graph's calibrated gains, and its own food mapping's interface
(`grid.interface_for` with `remaps.json`). The mappings move only the six food sensors; the read-out neurons are the
same under all four (checked, and asserted in the run).

## The probe

M1's probe as M2 runs it: 100 ticks warm-up at 0.25 or 1.75 of the final food level, a 10-tick ramp, then 2000 ticks
at the final level, float32, with each run's rows started together. The same as 02b's history test up to its final
tick, which is the classifier's tick 0.

**Two input banks.**
- **Primary: each run's own bank,** 02b's: the mean sensed signals over ticks 20 to 60 of the run's g39 champion's
  replay on 02b's behaviour worlds, recomputed on the CPU with 02b's `typical_input`. The bank is shared by every
  genome of that run (g00, g39, g79, drift). This is the input on which 02b found the effect.
- **Secondary: 03mc's bank,** the one M1 to M5 used, so that the classes can be set beside the census's rates (N2 under
  M0 about 1.5% of random genomes; the SH ensembles near 0.1%). These rates are context only, not a baseline: they
  are random genomes, on other graphs for the shuffles, without selection.

**A consistency check before anything is read.** On the primary bank, the probe's start difference a (the read-out
difference at the ramp's end) must reproduce 02b's committed `history.json` value (|raw_turn final|) for the 24 T1-M0
N2 and SH runs' g00 and g39 champions, and the recomputed bank's food level must reproduce 02b's `typical_food`. The
tolerance: within 2% relative or 1e-3 absolute, allowing for the CPU replay. A failure stops the reading for
investigation.

**The code change.** The probe hard-codes M0's interface and 03mc's bank (`scripts/memory_m1/common.py`, `at`; the
food level in `pilot.probe_states`, `follow_from` and M4e's `continue_hold`). A context manager in `common.py`,
`probe_input(iface, bank)`, sets both for every path that builds the probe's input, including the oscillation check's
rerun and the second pass. Outside it, the defaults are today's. Tests, each seen failing first: the default path is
bitwise unchanged on a small N2 panel; inside the context, a remapped interface puts the food current on the remapped
sensors and nowhere else; and the oscillation check's rerun inside the context reproduces the first pass's
trajectory.

## The classes

M2's frozen classifier (`scripts/memory_m2/classify.py`, `pilot.full_classify`), first pass at 2000 ticks, as in M4e:
separate states (with "read-out silent" reported apart, and counted as a switch, as M4d and M4e did), fading,
persistent oscillation, unresolved. No eligibility floor (M4d's convention); a is reported for every genome.

**The second pass** (M4e's, at 22,000 ticks): every genome not fading on the first pass, on each bank, plus an audit
of 20 first-pass-fading genomes per bank drawn with `default_rng(20261130 + bank)` (10 among g39 and g79, 10 among g00
and drift). A fading audited genome that becomes separate states after the second pass is reported as an audit
failure, and the reading then says the first pass's fading is not reliable for evolved genomes.

**Unresolved.** If more than a quarter of any group (tag × family × bank) is unresolved after the second pass, that
group's switch share is reported as a range from "none of them" to "all of them", and called not readable on this
probe.

## How slow: persistence

For every genome on each bank, from the first pass's read-out difference d(t) = |y_rising(t) − y_falling(t)|, every
tick to 2000: d(5)/a, d(30)/a, d(100)/a, and the persistence time τ10, the first tick at which d(t) < 0.1 a (M1's
remaining fraction; "beyond 2000" if never). Ratios use genomes with a ≥ 1e-3 (03mc's start floor), and the number
left out is reported per group.

## The comparisons (all descriptive)

The unit is the run: one g39 champion, one g00 champion and four drift genomes per run.

1. **Switches.** Counts of switch genomes by tag, mapping and family (N2, SH, N2perm), on each bank. Per run, g39's
   switch indicator minus the drift replicates' switch share. A one-sided sign test over runs with a non-zero
   difference, all runs and per family. The same for g39 against g00.
2. **Persistence.** Per run, g39's τ10 minus the mean of drift's (and minus g00's), on the primary bank; the median
   over runs and a sign test. "Beyond 2000" ranks above every finite τ10.
3. **Beside 02b.** For the 24 T1-M0 N2 and SH runs, each genome's class and τ10 next to 02b's |raw_turn final| and
   "after" values, with their Spearman correlation across g00, g39 and drift.
4. **The g79 snapshots.** Their classes and τ10 beside their own runs' g39, as four cases.

**State visits, only if there are switch champions.** For each g39 or g79 switch champion, its replay on 02's first
8 probe worlds (`grid.PROBE_IDS[:8]`, the run's seed): the state projected on the line between the two roots,
s(t) = (v(t) − r_falling)·(r_rising − r_falling)/|r_rising − r_falling|², and the share of ticks with s above and
below 0.5 and the number of crossings. A description of whether the task's inputs visit both sides, not a use test.

## The readings, fixed now

- **Switches clearly more often than drift:** at least 5 g39 switch champions on the primary bank and the sign test
  of comparison 1 at one-sided p < 0.05. Then the next step to consider is option 5 or option 2, as the options
  note says.
- **Otherwise:** "selection on T1 did not build switches detectable by this probe"; the 02b effect is described by its
  persistence (comparison 2), and options 3 or 4 are the honest next steps. This closes this probe's switch route
  for 02's champions, not useful memory in general, and not switches under other inputs.
- **The persistence reading:** if g39's τ10 exceeds drift's in a clear majority of runs (sign test one-sided
  p < 0.05), "selection lengthened the history effect's persistence"; the median ratio is reported either way.
- The secondary bank's results are reported beside the primary's, not used for the readings. A disagreement between
  the banks is reported as a dependence on input.

## Outputs, cost and stops

- `scripts/memory_m6/m6_0.py` (stages: banks, drift, classify, persistence, visits), `m6_0_read.py`; outputs in
  `runs/memory-m6-0/` (JSON records committed; genomes stay local); `docs/memory/M6-0-RESULTS.md`; the summary
  script reads it. Compute recorded by `wormwars.accounting`.
- **Cost.** 616 genomes on 2 banks. The first pass measured 0.75 s per evolved genome (the spike): about 15 minutes.
  The second pass costs about 75 s per genome: 40 audited genomes about 50 minutes, plus every non-fading genome
  (none among the 16 seen). Expected under 2 CPU hours. **The run stops at 5 CPU hours** (`CapClock`), what the owner
  was told; if the first pass shows that the second pass would pass the cap, it stops before the second pass and the
  owner is asked.
- Tests, seen failing first: the probe context above; the drift genome equals 39 calls of `Genome.mutate` on the
  stated generator; the genome list is exactly the files in the table, and the run refuses a missing file; a sabotage
  check that a changed class or τ10 changes the reading's summary.
