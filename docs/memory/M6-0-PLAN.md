# M6, option 0: is the history effect selection built a switch or slow fading? — the plan

*Draft 2, 2026-10-30, after one round of review by Astra 6 and Fable 5.1 (both "agree with fixes"; every fix taken;
draft 1, the prompt, the reviews and the disclosed spike are in
[`docs/reviews/20261030-m6-0-plan/`](../reviews/20261030-m6-0-plan/)). The owner chose option 0 of
[`M6-OPTIONS.md`](M6-OPTIONS.md) ("Sure, option 0"). Exploratory and descriptive: no pre-registration, but the
genomes, the probe, the classes, the comparisons and the readings are fixed here before the run. CPU only.*

## The question

02b found that 40 generations of selection on T1 built a history effect on the 0.25/1.75 food ramp: generation-39
champions turn differently after the two histories far more than generation 0 or a mutation-only drift control, and
most of the difference survives five more ticks ([`02b RESULTS`](../../experiments/02b-champion-analysis/RESULTS.md),
section 2). **Option 0 asks whether that effect is two stable states (a switch, as M1 to M4e found in a few random
genomes) or a slow return to one state, and how slow.** It does not test whether anything is used in the task
(option 5 would).

**Seen before this plan.** A throwaway timing spike ran the first pass of M2's classifier on 02's eight T1-M0-N2 runs'
generation-0 and generation-39 champions, on 03mc's bank (the secondary probe below). All 16 were fading, with root
distances near 1e-15 and no read-out difference left at tick 300. Those 16 are therefore seen; they stay in the run,
labelled as seen before the plan. Nothing else has been looked at.

## The genomes

Every T1 genome 02 saved (`runs/exp02-screening/`, local, loaded with `allow_pickle=False`), selected by file name
only:

| Tag | What | Count |
|---|---|---|
| g39 | each run's best genome at generation 39 | 102: N2 32 (8 runs × 4 mappings), SH1-SH8 64 (2 runs × 8 graphs × 4 mappings), N2perm1-3 6 (M0) |
| g00 | each run's best of its 32 random generation-0 genomes | 102, the same runs |
| g79 | generation-79 snapshots, where they exist | 4: T1-M0-N2 runs 0 and 1, T1-M0-SH1 and SH2 run 0 |
| drift | each run's g00 mutated 39 times with the run's mutation settings (T1's `MutationConfig`: w 0.08, g 0.04, tau 0.15, bias 0.05, p 1) and no selection, 4 replicates, as in 02b | 408 |

**The runs are not independent across mappings** (Astra, Fable). 02 seeds each run's generation-0 population from
the graph and run index, not the mapping (`wormwars/exp02/grid.py`, `wormwars/evo/evolve.py`), so the four mappings
of one graph and run start from the same 32 genomes, and their g00 champions are often the same genome. **The unit is
the graph and run index: 30 blocks** (N2 8, SH 16, N2perm 6), each holding one to four runs. The number of distinct
g00 genomes, by a hash of their parameters, is reported.

The drift genomes are a new draw of 02b's control, on the CPU: `torch.Generator("cpu")` seeded from the run's key and
the replicate (the first 8 bytes of sha256 of `"<key>/drift<k>"`, as an integer below 2^63), so the seed does not
depend on the order of `records.jsonl` (Fable). 02b's own drift genomes were drawn on the GPU and are not reproduced.

Each genome runs on its own graph (`grid.graph_for`), with T1's brain configuration for that graph
(`grid.brain_config_for_graph`), the graph's calibrated gains, and its own food mapping's interface
(`grid.interface_for` with `remaps.json`). **Each loaded genome's stored configuration must equal the constructed
one** (the brain runs under the genome's own; the input uses the constructed one; Fable), or the run stops. The
mappings move only the six food sensors; the read-out neurons are the same under all four, and the input context
refuses any interface whose read-out differs.

## The probe

M1's probe as M2 runs it: 100 ticks warm-up at 0.25 or 1.75 of the final food level, a 10-tick ramp, then 2000 ticks
at the final level, float32. The same as 02b's history test up to its final tick, which is the classifier's tick 0;
the turn read-out is four neurons a side, so the start difference a is 02b's raw turn difference (Fable).

**Two input banks.**
- **Primary: each run's own bank,** 02b's: the mean sensed signals over ticks 20 to 60 of the run's g39 champion's
  replay on 02b's behaviour worlds, recomputed on the CPU with 02b's `typical_input`, shared by every genome of that
  run (g00, g39, g79, drift). It is the input on which 02b found the effect, so it measures behaviour under
  g39-conditioned inputs, not an input-independent property (Astra). Each complete bank is saved.
- **Secondary: 03mc's bank,** the one M1 to M5 used, so that the classes can be set beside the census's rates (N2
  under M0 about 1.5% of random genomes; the SH ensembles near 0.1%). Context only, not a baseline, and not used for
  the readings.

**The CPU only.** 02b's analysis module picks CUDA when it is available; the run hides the GPU before torch is
imported (`CUDA_VISIBLE_DEVICES` empty), forces that module's device to the CPU, and asserts at the end that CUDA was
never initialised (Astra, Fable).

**A consistency check before anything is read.** On the primary bank, for the 24 T1-M0 N2 and SH runs' g00 and g39
champions, the probe's a must reproduce 02b's |raw_turn final| and its d(5) 02b's |raw_turn after|
(`history.json`), and the recomputed bank's food level 02b's `typical_food`, within 2% relative or 1e-3 absolute,
allowing for the CPU replay. A failure stops the reading for investigation, and stays documented if its resolution
changes anything here.

**The code change.** The probe hard-coded M0's interface and 03mc's bank. A context in `scripts/memory_m1/common.py`,
`probe_input(iface, bank)`, sets both for every path that builds the probe's input or its food level (`at`, `raw`,
`ramp`, and `final_food`, now read by `pilot.probe_states`, `pilot.follow_from` and M4e's `continue_hold`), so it
reaches the oscillation check's rerun and the second pass. Outside it, the defaults are today's. It refuses nesting,
and it restores the defaults on any exit. Tests, each seen failing first:
- **equivalence to the library's history measure** (`wormwars/exp03/measures.history`, 02b's test in library form,
  which takes the interface and bank explicitly): inside the context, with a remapped interface and a bank whose food
  level differs from 03mc's, the probe's tick-0 and tick-5 read-out differences match its "final" and "after"; and
  outside it, with M0 and 03mc's bank, the same (the old path, by an independent route) (Fable, Astra);
- the food current lands on the remapped sensors only, with the bank's gains and clamp;
- **the oscillation rerun** (`pilot.oscillation_check`) inside the context records the first pass's tail, tick for
  tick, and the same rerun outside it does not (Fable: the rerun runs only on candidates, so a panel test is
  vacuous);
- the second pass's hold continues the first pass's trajectory inside the context;
- restoration after an exception, nesting refused, and an interface with another read-out refused.

M6's driver copies M4e's `continue_hold` and `second_pass` rather than importing M4e, whose import chain creates run
folders (Fable), with a test that the copies equal M4e's bitwise.

## The classes

M2's frozen classifier (`scripts/memory_m2/classify.py`, `pilot.full_classify`), first pass at 2000 ticks, as in M4e:
separate states (with "read-out silent" reported apart; both count as switches, as in M4d and M4e, but read-out-silent
genomes show state separation, not a contribution to the turning effect; Astra), fading, persistent oscillation,
unresolved. No eligibility floor for the classes (M4d's convention); a is reported for every genome.

**The second pass** (M4e's, at 22,000 ticks): every genome not fading on the first pass, on each bank, plus an audit
of 20 first-pass-fading genomes per bank drawn with `default_rng(20261130 + bank)` (10 among g39 and g79, 10 among g00
and drift). An audited genome that is separate states after the second pass is an audit failure.

**Unresolved genomes are never counted as non-switches** (Astra): whenever a group has unresolved genomes after the
second pass, its switch share is reported as the bounds S/n to (S+U)/n, by mapping as well as pooled.

## How slow: persistence

From the first pass's read-out difference d(t) = |y_rising(t) − y_falling(t)|, every tick to 2000, for genomes with
a ≥ 1e-3 (03mc's start floor; the number below it reported per group):
- d(5)/a, d(30)/a, d(100)/a;
- **τ_stay**, the first tick after which d stays below 0.1 a through tick 2000 (M1's remaining fraction), censored as
  "beyond 2000" if d(2000) ≥ 0.1 a; and the first crossing τ_first, with a flag when d returns above 0.1 a after it
  (a signed difference can cross zero and grow again; Astra).
- For arithmetic, the restricted τ = min(τ_stay, 2000); censoring is reported separately (Astra).

## The comparisons (all descriptive)

Per graph and run index (the 30 blocks), with each block's runs averaged within it; uncertainty by a cluster
bootstrap over the 30 blocks (10,000 resamples, `default_rng(20261131)`), 95% percentile intervals.

1. **Switches** (primary bank). Per run, g39's switch indicator minus the share of its four drift replicates that
   switch; the mean over blocks and its interval. The same for g39 against g00. Counts by tag, mapping and family,
   with unresolved bounds. (A sign test of an indicator against a share of four does not test equal rates; Astra.)
2. **Persistence** (primary bank). Per run, the share of its eligible drift replicates whose τ_stay g39's exceeds
   (ties and both censored count a half; "beyond 2000" ranks highest), minus one half; the mean over blocks and its
   interval (Fable's form). A run counts if g39 and at least one replicate pass the floor. The same against g00.
   Medians of the restricted τ by tag and family.
3. **Beside 02b,** for the 24 T1-M0 N2 and SH runs: g00's and g39's class, a, d(5) and τ_stay next to 02b's
   |raw_turn final| and |raw_turn after| for the same genomes. The new drift genomes are set beside 02b's drift values
   as two unpaired sets of four per run, never paired (Astra, Fable).
4. **The g79 snapshots:** class and τ_stay beside their runs' g39, as four cases.

The secondary bank's classes and persistence are reported beside the primary's in the same tables.

## The readings, fixed now

- **Inconclusive** (first, overriding the others): the run incomplete (the cap), the consistency check failed, an
  audit failure, or the primary bank's unresolved bounds straddling the criterion below (it holds at S and fails at
  S + U, or the reverse).
- **Enrichment:** at least 5 g39 switch champions on the primary bank, and comparison 1's interval against drift
  above zero. Then the next step to consider is option 5 or option 2, as the options note says.
- **Otherwise:** "We did not detect enrichment of probe-defined switches in g39 champions relative to the
  mutation-only control; N were found" (Astra, Fable), with the classes that did occur. If the g39 champions are
  mostly fading, the 02b effect is described by its persistence; options 3 or 4 are then the honest next steps. This
  bears on this probe's switch route for 02's champions only, not on useful memory in general, nor on switches under
  other inputs.
- **Persistence:** "selection lengthened the history effect's persistence beyond drift" if comparison 2's interval
  against drift is above zero; "shortened" if below; otherwise "not distinguishable from drift". The medians are
  reported either way.
- A switch or persistence result on the secondary bank only is reported as a dependence on input, never as the
  reading.

**Cut** (Astra): the state-visits replay of draft 1. A projection on the line between two roots shows which side of a
plane the state is on, not visits to either root's basin; meaningful visitation is option 5's.

## Outputs, cost and stops

- `scripts/memory_m6/m6_0.py` (stages: genomes, banks, classify, persistence), `m6_0_read.py`; outputs in
  `runs/memory-m6-0/` (JSON records committed, with each genome's file, parameter hash, record key and drift seed;
  genomes stay local); `docs/memory/M6-0-RESULTS.md`; the summary script reads it. Compute recorded by
  `wormwars.accounting`.
- **Cost.** 616 genomes on 2 banks. The first pass measured 0.75 s per evolved genome in batches of 8: about 15
  minutes. M4e's second pass averaged about 5 s a genome (`M4E-RESULTS.md`; draft 1's 75 s was the smoke's figure
  for unresolved genomes; Fable): the 40 audited genomes take minutes, plus every non-fading genome. Expected under 1
  CPU hour. **The run stops at 5 CPU hours** (`CapClock`), what the owner was told. After the first pass, the second
  pass's time is forecast from the production batches; if the forecast passes the cap, the run stops there and the
  owner is asked (Astra). A capped run is reported as incomplete.
- **Tests,** seen failing first: the probe context above; the drift genome equals 39 calls of `Genome.mutate` on its
  stated generator; the genome list is exactly the files in the table, and the run refuses a missing file; the stored
  configuration check; and **reader sabotage checks** that each fixed wording is produced by its case: enrichment,
  the negative wording, each inconclusive cause (cap, consistency, audit, straddling bounds), censoring in τ_stay, a
  run without an eligible drift replicate, and a secondary-only positive (Astra).
