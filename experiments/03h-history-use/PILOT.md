# 03h: the pilot's registration (draft, for review; DESIGN.md v3.2 §7.3)

**Status:** draft 1, 2026-10-19. Not bound.
- **Before any registered gate or pilot stage runs,** this registration is reviewed by both, bound (committed, its hash
  recorded) and pushed.
- **The owner's GPU word** was given on 2026-10-19 ("you have my go ahead for the gpu I'm not using it now"). It covers
  step 0, the gate and the pilot. The formal run will be asked separately.
- **Nothing here is a test of 03h's questions.** The pilot sets W, checks detectability, sets the sham's rates, and
  checks the manipulation, by the rules below.

## 1. Stages, in order

| Stage | Command | What it runs | GPU |
|---|---|---|---|
| G1 | `scripts/e03h.py gate` | the scripted gate's level and relief parts (§2) | about 0.05 h |
| S1 | `scripts/e03h.py sham-rates` | the pilot's restricted part: level trajectories on the 3 pilot graphs (§3) | about 0.05 h |
| G2 | `scripts/e03h.py gate-sham` | the gate's sham part, with S1's rates frozen (§2) | about 0.02 h |
| P | `scripts/e03h.py pilot` | the three conditions on the 3 pilot graphs (§4), and the readings of §5 | about 0.2 h |
| P′ | `scripts/e03h.py pilot --amplitude 0.5` | only by §5.4's rule | about 0.2 h |

- **Each stage refuses to run** if the stage before it has not completed with its criteria met.
- **Each stage also refuses** if this file's hash differs from the bound one, or if the guarded tree is dirty.
- **The cap:** 1.0 GPU-hour for everything before the pre-registration: step 0, G1, S1, G2, P and P′. It is counted
  by T0's accounting, across attempts.
- **Records:** `experiments/03h-history-use/pilot/<stage>.json`.

## 2. The scripted gate

**Its configuration:**
- 02's T1 (`grid.task_config(Config(), "T1")`), with N2's motor gains from 02's committed calibration
  (`experiments/02-screening/calibration.json`, as 02's own gate used them);
- 03h's interface variant, with the bit at amplitude 0.25.

**Its worlds** (ids disjoint from every earlier range and from §3-§4's):
- tuning: 3 610 000-3 610 063 (64 worlds), run seed 3 612 001;
- check: 3 611 000-3 611 255 (256 worlds), run seed 3 612 002.

**Its families:** each is tuned by `tune_batched` on the tuning worlds, with ties going to the first maximum. 02's
nesting rule applies: a richer family is tuned around the poorer family's optimum (each parameter at its grid
neighbours), and falls back to the poorer family exactly if it does not beat it on the tuning worlds.
- **K:** `LevelKinesis` on 02's `K_GRID` (`scripts/exp02.py`).
- **Graded:** `GradedKinesis` on slow {0, 0.25, 0.5, 0.75, 1.0} × fast {0.5, 0.75, 1.0} × scale {0.03, 0.1, 0.3, 1.0,
  3.0} × turn {0, 0.1, 0.2, 0.4, 0.7}.
- **memoryless:** the better of K and Graded on the tuning worlds.
- **memoryless + bit:** `BitKinesis` around K's optimum, with `fall_turn` in 02's `FALL_GRID`. It falls back to the
  memoryless optimum.
- **memory:** the best of:
  - the memoryless optimum;
  - `MemoryKinesis` around K's optimum, with 02's `FALL_GRID`;
  - `SlowMemoryKinesis` at `MemoryKinesis`'s optimum, over T in {1, 2, 5, 10, 20}, with `use_memory` 1 and `use_bit`
    0. T = 1 is that `MemoryKinesis` itself, so this family nests it.
- **memory + bit:** the best of:
  - the memoryless + bit optimum;
  - `SlowMemoryKinesis` at the memory optimum's speed, turn and fall parameters, over T in {1, 2, 5, 10, 20}, with
    `use_memory` in {0, 1} and `use_bit` in {0, 1}. Each source of "falling" can be switched off.
- **The cost:** tuning the slower families at their base family's optimum, not over the full grids, keeps the gate at
  about 150 000 tuning episodes. The full grids would need about a million.

**Each family is tuned under its own condition:** the "+ bit" families under relief (G1) or sham (G2), the others
under level.

**The check:** each chosen policy is scored once on the check worlds, under its condition. Intervals come from a
paired bootstrap over the check worlds: 20 000 resamples, seed 0, as 02's `_paired`.

**The criteria** (DESIGN §4):
- **G1, level:** the 95% lower bound of (memory − memoryless) ≥ 0.5.
- **G1, relief:** the 90% interval of (memory + bit − memoryless + bit) inside ±0.3.
- **G1, reported:**
  - the recovered share, (memoryless + bit − memoryless) / (memory − memoryless), with its interval;
  - every family's parameters and its grid-edge flags (02's `_edges`).
- **G2, sham:** under sham, the 90% interval of (memoryless reading the sham − memoryless) inside ±0.3. Under sham,
  the "memoryless + bit" family reads the sham bit.

**The consequences:**
- G1's level part fails: 03h stops and is reported.
- G1's relief part or G2 fails: 03h stops for redesign (DESIGN §4).

## 3. S1: the sham's rates (and the timing)

**The graphs:** 3 SH-mirror-ASK graphs, seeds 3 630 001, 3 630 002 and 3 630 003, 20 passes. A failed sampler is
retried with the next seed. They are never formal graphs and never N2.

**Calibration:** per graph, under level, by 03's procedure (`calibrate_in_world` to `grid.TARGET_DRIVE`, 1 024 strains,
seed 3 631 000), with 03h's interface variant. A failed calibration takes the next graph seed.

**The genomes:** 256 per graph, from `Genome.random` on CUDA. Each graph's generator is seeded by
`genome_seed(name, "03h-pilot:")`.

**The worlds:** pilot selection worlds 3 620 000-3 620 015 (16), run seed 3 622 001, chunks of 4 096 worlds.

**Under level,** the relief bit's transition counts are summed over every graph, genome, world, wey and tick, by the
world's own counting (DESIGN §3). Then p̂01 = N01 / (N00 + N01) and p̂10 = N10 / (N10 + N11).
- If either denominator is zero, 03h stops for redesign.
- The record also gives each graph's counts, and the seconds per graph-condition.

## 4. P: the pilot proper

**What runs:** the same 3 graphs, gains and genomes as S1, under three conditions (level, relief, and sham at S1's
rates).

**The selection bank:** the 16 worlds of §3. Every genome is scored on it under every condition.

**The test bank:** 3 621 000-3 621 063 (64 worlds), run seed 3 622 002. Only each graph's selected decile is scored on
it: the top 26 of 256 on the selection bank, selected per condition, with ties broken by genome index.

**History:** `history(per_history=True)` on 03's bank (`experiments/03-generation0/pilot.json` `bank`), under level,
on the same genome objects. It gives H, S and H_dir as in DESIGN §5.

**The bit's turn response** (the manipulation's second reading):
- per genome, 100 ticks warm at the bank's food level with the bit at 0;
- then one tick with the bit at the amplitude, against one tick with it at 0;
- the difference in the motor turn read-out at that tick.

## 5. The readings and their rules (fixed now)

### 5.1 Reliability (W)

The crossed decomposition of DESIGN §2 per graph, under level, on the selection bank: var_genome / (var_genome +
var_residual / 16), averaged over the 3 graphs.
- If it is ≥ 0.85, W = 16 is kept.
- Otherwise W = 32 for the formal run, and the budget is re-checked against the 6-hour cap.

### 5.2 A's statistics on the pilot

- **Per graph and condition:** ρ_c, the partial Spearman of H with the selection-bank fitness given S
  (`wormwars/e03h/stats.py`).
- **Per graph:** D = ρ_sham − ρ_relief.
- **Reported:** every ρ_c and D, H_dir's ρ, and the top-against-bottom quartile difference.

### 5.3 Detectability (DESIGN §7.7; δ_A is 0.05 in ρ, fixed now)

- **s_graph** is the between-graph SD of D over the 3 pilot graphs. The value used is the larger of that and step 0's
  between-graph SD of ρ_level, if step 0 ran.
- **s_shared** is the SD of the mean of D over the 3 graphs, across 2 000 shared resamples of the 16 selection worlds
  (one resample applied to every graph and condition, with ρ recomputed; seed 3 623 000).
- **SE** = sqrt(s_graph² / 64 + s_shared²).
- **Power** = 1 − Φ(1.96 − 2 × 0.05 / SE).
- If the power is below 0.8, 03h stops for redesign.

### 5.4 The manipulation (Fable)

- **The decile shift:** per graph, the selected decile's test-bank mean under relief minus under sham. Its mean over
  the 3 graphs has a 95% interval from a shared bootstrap of the 64 test worlds.
- **The turn response:** per graph, the mean over its 256 genomes of |the bit's turn response| (§4). It reads as
  moved if it is at least 0.02, on the motor turn read-out's [−1, 1] scale, in at least 2 of the 3 graphs.
- **If neither moves** (the shift's interval contains 0, and the turn response is below 0.02 in at least 2 graphs):
  - the amplitude becomes 0.5, once;
  - P reruns as P′ with the same graphs, genomes and worlds;
  - if neither moves at 0.5 either, 03h stops for redesign.

### 5.5 Timing

- The seconds per graph-condition are measured in S1 and P. The formal run is projected from them.
- If the primary formal run, SH-mirror-ASK and N2, does not fit the 6-hour cap with W from §5.1, 03h stops for
  redesign.
- SH is added only if the projection leaves room.

## 6. What the pilot fixes for the pre-registration

The pilot fixes:
- the sham's rates;
- W;
- the amplitude;
- the timing.

Detectability is checked, not tuned. Every number above is fixed now. The pilot's values for ρ and D are
reported, but are never a test.

## 7. Record and seeds

- **Graph seeds:** 3 630 001 onward.
- **Calibration seed:** 3 631 000.
- **Genome salt:** "03h-pilot:".
- **World ids:** 3 610 000-3 611 255 (gate), 3 620 000-3 620 015 (selection), 3 621 000-3 621 063 (test).
- **Run seeds:** 3 612 001 and 3 612 002 (gate), 3 622 001 and 3 622 002 (pilot).
- **Bootstrap seed:** 3 623 000.
- **The sham's randomness** is not a separate seed. It is the world's keyed stream 0x03F under the bank's run seed
  (3 622 001 for the selection bank, 3 622 002 for the test bank, and 3 612 001 or 3 612 002 in the gate). Every
  condition, genome and graph shares that run seed, so every one of them sees the same sham sequence for a given world
  and wey (DESIGN §5, annotated 2026-10-19).
- All of these are disjoint from 03, 03r, 03mc, 03a, the rule-7 check (3 600 001-3 600 115) and the formal ranges,
  which are fixed in the pre-registration.
