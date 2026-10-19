# 03h: the pilot's registration (DESIGN.md v3.3 §7.3)

**Status:** draft 3, 2026-10-19, for review.
- **What it follows:** design v3.3 (D330), in which B is the only registered claim. It takes the review of draft 2 and
  its code (run 20261019-100138, D333).
- **Binding:** `scripts/e03h.py bind` records this file's and DESIGN.md's hashes. That record is committed and pushed
  before any stage runs, and D-numbered with its commit. Every stage refuses if either file then differs.
- **The owner's GPU word,** 2026-10-19 ("you have my go ahead for the gpu I'm not using it now"), covers step 0, the
  gate and the pilot. The formal run will be asked separately.
- **Nothing here is a test of 03h's questions.** The pilot:
  - sets the sham's rates, W and the amplitude;
  - checks the manipulation and the budget;
  - reports A2's power;
  - all by the rules below.

## 1. Stages, in order

| Stage | Command | What it runs | GPU, estimated |
|---|---|---|---|
| G1 | `scripts/e03h.py gate` | the scripted gate's level and relief parts (§2) | 0.1-0.2 h |
| S1 | `scripts/e03h.py sham-rates` | the restricted part of the pilot: level trajectories on the 3 pilot graphs (§3) | about 0.05 h |
| G2 | `scripts/e03h.py gate-sham` | the gate's sham part, with S1's rates and G1's families (§2) | about 0.05 h |
| P | `scripts/e03h.py pilot` | the three conditions on the 3 pilot graphs (§4); the readings of §5 | about 0.2 h |
| P′ | `scripts/e03h.py pilot --amplitude 0.5 --rerun --reason "..."` | only by §5.4's rule | about 0.2 h |

**A stage refuses when:**
- the stage before it has not completed with its criteria met;
- an upstream record has changed since a downstream record read it. Each record carries its predecessors' hashes,
  so a rerun S1 cannot leave an older G2 authorising P (Astra);
- PILOT.md or DESIGN.md differs from the bound hashes;
- the guarded tree is dirty, or HEAD is not pushed.

**The cap:** 1.0 GPU-hour for everything before the pre-registration (step 0 and 0b, G1, S1, G2, P and P′), counted by
T0's accounting across attempts.
- It is checked before each stage and before every bounded unit of work: each tuning unit, each check score, each
  graph's calibration, and each rollout.
- A unit that has started runs to completion, and the record notes any overrun (`over_cap_at_end`).

**Records:** `experiments/03h-history-use/pilot/<stage>.json`.
- The per-genome arrays stay local, in `runs/e03h/pilot/states/`, with their sha256 in the record (Fable).
- The pilot graphs and genomes are rebuilt from their seeds and checked by hash.

## 2. The scripted gate

**Its configuration:**
- 02's T1 (`grid.task_config(Config(), "T1")`), with N2's motor gains from 02's committed calibration
  (`experiments/02-screening/calibration.json`), as 02's own gate used them;
- 03h's interface variant, with the bit at amplitude 0.25;
- CUDA inside `replay_mode()` (Fable).

**Its worlds:**
- tuning: 3 640 000-3 640 063 (64 worlds), run seed 3 642 001;
- check: 3 641 000-3 641 255 (256 worlds), run seed 3 642 002.

**Its families:** each is tuned by `tune_batched` on the tuning worlds, with ties going to the first maximum. 02's
nesting rule applies: a richer family is tuned around the poorer family's optimum and falls back to it exactly if it
does not beat it on the tuning worlds.
- **K:** `LevelKinesis` on 02's `K_GRID`.
- **Graded:** `GradedKinesis` on slow {0, 0.25, 0.5, 0.75, 1.0} × fast {0.5, 0.75, 1.0} × scale {0.03, 0.1, 0.3, 1.0,
  3.0} × turn {0, 0.1, 0.2, 0.4, 0.7}.
- **memoryless:** the better of K and Graded.
- **memoryless + bit:** `BitKinesis` around K's optimum, each parameter at its grid neighbours, with `fall_turn` in 02's
  `FALL_GRID`. It falls back to the memoryless optimum.
- **memory:** the best of:
  - the memoryless optimum;
  - `MemoryKinesis` around K's optimum, with `FALL_GRID`;
  - `SlowMemoryKinesis` at `MemoryKinesis`'s speed and turn parameters, over T {1, 2, 5, 10, 20} × `FALL_GRID`, with
    `use_memory` 1 and `use_bit` 0. T is tuned jointly with the fall parameters (Fable), and T = 1 contains
    `MemoryKinesis`.
- **memory + bit:** the best of:
  - the memoryless + bit optimum;
  - `SlowMemoryKinesis` at the memory optimum's speed, turn and fall parameters, over T, with `use_memory` {0, 1} and
    `use_bit` {0, 1}. When the memory family fell back to memoryless, the base is `MemoryKinesis`'s optimum (Fable,
    Astra).
- **What the restriction means:** tuning the slower families at their base family's optimum is a registered
  restriction. The relief criterion is a statement about these candidates, not about fully retuned slow-memory policies
  (Astra).
- **G2 re-tunes only `BitKinesis`,** under sham. It reuses G1's K, Graded and memoryless families from G1's record
  (Fable).
- **The cost:** G1's tuning is about 100 000-150 000 episodes, and G2's is far less.

**Each family is tuned under its own condition:** the "+ bit" families under relief (G1) or sham (G2), the others
under level.

**The check:** each chosen policy is scored once on the check worlds, under its condition. Intervals come from a
paired bootstrap over the check worlds: 20 000 resamples, seed 0, as 02's `_paired`.

**The criteria** (DESIGN §4):
- **G1, level:** the 95% lower bound of (memory − memoryless) ≥ 0.5.
- **G1, relief:** the 90% interval of (memory + bit − memoryless + bit) inside ±0.3.
- **G1, reported:**
  - the recovered share, with its interval;
  - every family's parameters and its grid-edge flags (02's `_edges`; Fable, Astra).
- **G2, sham:** under sham, the 90% interval of (memoryless reading the sham − memoryless) inside ±0.3.

**The consequences:**
- G1's level part fails: 03h stops and is reported.
- G1's relief part or G2 fails: 03h stops for redesign.

## 3. S1: the sham's rates (and the timing)

**The graphs:** 3 SH-mirror-ASK graphs at consecutive seeds from 3 660 001, 20 passes.
- A sampler failure or a calibration failure takes the next seed, recorded (Fable, Astra).
- P rebuilds the accepted seeds that S1 recorded.
- They are never formal graphs and never N2.

**Calibration:** per graph, under level, by 03's procedure (`calibrate_in_world` to `grid.TARGET_DRIVE`, 1 024 strains,
seed 3 661 000), with 03h's interface variant, starting from T1's default gains.
- It plays world ids 0-1 023 under its own seed. Those numeric ids repeat other experiments' calibration ids, but the
  (seed, id) pairs are distinct.
- **Disjointness means two things:** for registered banks, numeric ids disjoint from every earlier experiment's; for
  calibration, distinct (run seed, world id) identities (Astra).

**The genomes:** 256 per graph from `Genome.random` on CUDA, with the generator seeded by
`genome_seed(name, "03h-pilot:")`. Their sha256 is recorded, and P checks it (Fable).

**The worlds:** selection worlds 3 650 000-3 650 015 (16), run seed 3 652 001, in chunks of 4 096 worlds, inside
`replay_mode()`.

**The rates:**
- Under level, the relief bit's transition counts are summed over every graph, genome, world, wey and tick, by the
  world's own counting (DESIGN §3).
- Then p̂01 = N01 / (N00 + N01) and p̂10 = N10 / (N10 + N11).
- If either denominator is zero, 03h stops for redesign.

## 4. P: the pilot proper

**What runs:** the same 3 graphs, gains and genomes as S1, under three conditions: level, relief, and sham at S1's
rates.
- The level selection scores are S1's: the same genomes, worlds, run seed and interface, with their hash checked.
- The realised counts of the relief bit and of the injected bit are recorded per condition (DESIGN §3).

**The selection bank:** the 16 worlds of §3.

**The test bank:** 3 651 000-3 651 063 (64 worlds), run seed 3 652 002. Only each graph's selected decile is scored on
it: the top 26 of 256 on the selection bank, selected per condition, with ties broken by genome index.

**History:** `history(per_history=True)` on 03's bank, under level, on the same genome objects. It gives H, S and H_dir.

**The bit's turn response** (a diagnostic):
- per genome, 100 ticks warm at the bank's inputs with the bit at 0;
- then one tick with the bit at the amplitude, against one tick with it at 0;
- the difference in the motor turn read-out at that tick.

## 5. The readings and their rules (fixed now)

### 5.1 Reliability (W)

The crossed decomposition of DESIGN §2, per graph, under level, averaged over the 3 graphs.
- If it is ≥ 0.85, W = 16.
- Otherwise W = 32.

### 5.2 A's statistics (secondary; DESIGN §13)

- **Per graph and condition:** ρ_c, the partial Spearman of H with the selection-bank fitness given S.
- **Per graph:** D = ρ_sham − ρ_relief.
- **Reported:**
  - H_dir's ρ under level;
  - the top-against-bottom H quartile difference under level.

### 5.3 A2's power (reported, not a stop; DESIGN §13)

- **s_graph** is the larger of the between-graph SD of D over the pilot graphs and step 0's 0.060.
- **s_shared** is the SD of the mean of D across 2 000 shared resamples of the 16 selection worlds (seed 3 653 000).
- **SE** = sqrt(s_graph² / 64 + s_shared²).
- **Power** = 1 − Φ(1.96 − 2 × 0.05 / SE).
- It is the normal approximation for A2 alone. It is not B's power, and three graphs do not establish B's power
  (Astra).

### 5.4 The manipulation (DESIGN §13)

**The decile shift:**
- per graph, the selected decile's test-bank mean under relief minus under sham;
- its mean over the 3 graphs has a 95% interval from 2 000 shared resamples of the 64 test worlds (seed 3 653 001);
- it moves if the interval's lower bound is above 0. The interval conditions on the frozen deciles and the three
  graphs. It is a manipulation check, not an effect size (Fable).

**If it does not move at 0.25:** the amplitude becomes 0.5, once. P′ reruns with the same graphs, genomes and worlds.
- If it does not move at 0.5 either, 03h stops for redesign.
- A P′ that fails to complete may be retried. A completed P′ cannot be repeated (Astra).

**Also reported, for B:** each graph's U = T_sham − T_relief, its between-graph SD, and the shared-world SE of the mean
of U from the same resamples (Fable). The turn response is a diagnostic only.

### 5.5 The budget (DESIGN §8's cut order as a decision table; Astra)

**The projection:** from P's timing, the formal run's GPU-hours per graph are 3 conditions × (256 × W + 26 × W_t)
episodes at the measured per-episode seconds, plus graph building, calibration and the history probe.

**Then, in order:**
1. **The primary run** (SH-mirror-ASK, 64 graphs, and N2) at W_t = 64, if it fits the 6-hour cap, with SH (64 graphs)
   added only if that also fits;
2. otherwise, the primary run at W_t = 32, with SH only if that fits;
3. otherwise, 03h stops for redesign.

**The budget takes precedence:** if no plan fits, 03h stops whatever the decile shift (Astra).

**Smoke projections** extrapolate from tiny batches and mean nothing.

## 6. What the pilot fixes for the pre-registration

The pilot fixes the sham's rates, W, the amplitude, W_t and whether SH runs. The values of ρ, D and U are reported, but
are never a test.

## 7. Record, seeds and disclosure

- **Graph seeds:** 3 660 001 onward.
- **Calibration seed:** 3 661 000.
- **Genome salt:** "03h-pilot:".
- **World ids:**
  - gate: 3 640 000-3 640 063 and 3 641 000-3 641 255;
  - selection: 3 650 000-3 650 015;
  - test: 3 651 000-3 651 063.
- **Run seeds:** 3 642 001 and 3 642 002 (gate), 3 652 001 and 3 652 002 (pilot).
- **Bootstrap seeds:** 3 653 000 (A2's s_shared) and 3 653 001 (the decile shift and U).
- **The sham's randomness** is not a separate seed. It is the world's keyed stream 0x03F under the bank's run seed,
  shared by every condition, genome and graph (DESIGN §5, annotated 2026-10-19).
- **Disjointness:** all of these are disjoint from 03, 03r, 03mc, 03a, the rule-7 check (3 600 001-3 600 115), step 0
  (03's own worlds), and every smoke range. Smoke has its own ids and seeds from 3 690 000 (`scripts/e03h.py`
  `SMOKE_CFG`; Astra).
- **Disclosed** (D333): draft 1's banks (gate 3 610 000-3 611 255, selection 3 620 000-3 620 015, test
  3 621 000-3 621 063, and their run seeds) were played in part by the CUDA smoke preflight, because smoke then shared
  them. They are retired, and draft 3 uses fresh banks.
