# E3e: E3d's island mazes at 7 × 7 (design v2)

**Status:** v2, bound (D234), after both reviewers' review of v1 ("revise", D233; `docs/reviews/20261011-E3e-design/`). For
a last check, then binding. E3e is exploratory: it validates a task, and it trains nothing.

**Why it exists** (the owner, 2026-10-11; D232):
- **E3d failed at calibration** on one criterion, G1b (`experiments/E3-ab-organism/E3d/RESULTS.md`). A random walk
  reached 2.34-2.53 mean visits per wey against the absolute blind limit of 2.0, covering 90-95% of a 6 × 6
  maze within the horizon.
- **Everything else passed:**
  - wall-followers and E3c's scent-free champions scored almost nothing;
  - the scent follower made 6.5-7 × the random walk.
- **The owner chose option 1** of the five E3d's results listed: a larger maze, 7 × 7, with the same island
  construction, to make random coverage harder without changing the task.

**What E3e is:** E3d's bound design (`docs/E3/E3d-DESIGN.md` v2.2, with Amendment 1, its correction and its
erratum in §11), **unchanged except for the differences listed in §1 and the additions in §1a.** E3d's §4 requires
fresh calibration and confirmation blocks for a revised construction, so E3e plays new ones. Everything this note
does not change is E3d's text, and is read from it.

**E3d's text is part of E3e's bound text** (both reviewers): at its last commit, 202666e, with sha256
`37ee0c39868f074446cca43fd0242ce8bf72e9f90127fdafbade60394e4b4147` (line endings normalised). E3e's runner pins that hash
beside its own design's and refuses if either file changes.

## 1. The differences from E3d

| | E3d (bound) | E3e |
|---|---|---|
| Maze size c | 6 (a 25 × 25 grid) | **7 (a 29 × 29 grid)** |
| Interior cells (goal candidates) | rows and columns 1-4: 16 cells, 78 pairs | **rows and columns 1-5: 25 cells, 228 pairs** whose rings share no post |
| A-B graph distance | [⌈c/2⌉ + 1, 2c] = [4, 12] | **[5, 14]**, the same rule |
| Maze run seed | 1 190 000 | **1 191 000** |
| Calibration block | ids 30 000-30 127 | **ids 31 000-31 127** |
| Confirmation block | ids 30 200-30 455 | **ids 31 200-31 455** |
| Tree reference | ids 30 200-30 327 at c = 6 | **ids 31 200-31 327 at c = 7** |
| Tangent diagnostic | ids 30 200-30 263 | **ids 31 200-31 263** |
| Reduction 3 (the tree reference cut) | ids 30 200-30 263 | **ids 31 200-31 263**, still the confirmation's first 64 (both reviewers: E3d's runner hard-coded the old ids) |
| The verdict wording | "E3d: passed", "E3d: failed", "E3d: not evaluable", "E3d: failed at calibration" | **the same with "E3e"** |
| The wall-follower's tree-tour qualification | 10 6 × 6 trees (ids 40 000-40 009) | **the same test also at c = 7**: each hand on its own enters all 49 cells within 2 400 ticks in at least 9 of 10 trees (ids 40 000-40 009 at c = 7, run seed 1 190 000, as the c = 6 test). A tour of a 7 × 7 tree is 96 directed moves, about 1 100 ticks at the c = 6 pace. E3d's other qualification tests stay as regressions; their geometry does not depend on c |

**Unchanged** (E3d's text):
- **the construction:** carved islands, k_r ∈ {0, 2, 4} nested openings excluding the goals' sides, the checks,
  the redraw (at most 64), the spawns, the streams' keying;
- **the world:** H = 2 400, colonies of 8, shared trails (μ 0.01, λ 0.02, δ 0.05, d₀ 1.142), the scent's σ and
  reach, the visit rule;
- **the controls and organisms:** the blind family and its grids, the navigators, the seed, E3c's 28 champions,
  who plays where;
- **the procedure and the gate:**
  - the smallest qualifying k_r, with the feasible floor of 0.5;
  - B_max as the maximum over all blind settings on confirmation;
  - G1a-G3b and their thresholds;
  - the oracle's precondition;
  - the bootstrap (2 000 resamples, seed 20 261 011);
  - the verdict wording, the readings of a G1 failure and the champions' predictions (against the 7 × 7 tree
    reference);
- **the records** (§6) and the compute ceiling of 3 GPU-hours, with the same reductions in the same order.

**The horizon stays 2 400 ticks.** The owner chose a larger maze, not a shorter horizon. Typical routes are
expected to lengthen, so the navigators' scores are expected to fall too; that is an expectation for newly sampled
mazes, not a guarantee (Astra). G2a and G2b test that they stay high enough.

## 1a. Additions (both reviewers of v1)

- **The coverer arithmetic** (E3d §4's rationale, restated at c = 7): a tree tour is 2(c² − 1) directed moves, 48
  at c = 5, 70 at c = 6 and 96 at c = 7. So size alone predicts about 70/96 = 0.73 × from c = 6 for a lap-coverer
  (Fable). For a random walk that covered 90-95% of the 6 × 6 maze, 7 × 7 is a modest step. A G1b margin near
  2.0 is possible either way.
- **A pre-stated reading for a G2a failure** (Fable; the wording Astra's last check gave, verbatim; E3d had
  readings for G1 and G3a failures only): "A G2a failure means the shared scripted follower falls below the
  required one-third of oracle throughput on this block. Increased discovery cost associated with fixed scent
  reach and trail decay is a possible explanation, to check against discovery, scent-reach, no-first-visit and
  later-leg records—not an identified cause. Blind-control performance is assessed separately by G1."
- **A calibration failure is reported in full** (Astra; D231's correction carried in):
  - **what the report gives:** each calibration k_r's bootstrap intervals for every gate quantity (2 000 resamples,
    seed 20 261 011, B_max recomputed in each), its scent-reach split, and exact counts for the champions' blind
    plays. Confirmation is still skipped;
  - **a fix in the summary:** it no longer assumes the B_max member is a single-strain condition; a champion
    named `arm#strain` resolves to its strain.
- **The projection** is measured at c = 7 by `project`, and its admission decides. The "about 2 h" in §3 is an
  actual-cost guess from E3d's calibration, not a projection. E3d's projection overstated its calibration (0.98 h
  projected against 0.68 h actual). At 841 grid cells against 625, E3e's projection may trigger reduction 2 (the
  W2-turn grid) or 3 (the tree reference cut), both declared in E3d §7. The result names the blind family
  actually played; its maximum does not bound every possible blind strategy (Astra).

## 2. Sizing (CPU; no reading depends on it)

From `scripts/e3d_sizing.py` (seed 20 261 010, 400 mazes per row, the c = 7 rows appended to
`docs/E3/e3d-sizing.json`):

| c | construction | k | first-draw feasible (distance bound ⌈c/2⌉ + 1) | placements seen | effective placements | open share |
|---|---|---|---|---|---|---|
| 6 | carved, k_r | 0 / 2 / 4 | 0.73 / 0.72 / 0.70 | 73 / 73 / 71 | 62.8 / 62.8 / 61.4 | 0.69 / 0.73 / 0.76 |
| 7 | carved, k_r | 0 / 2 / 4 | 0.65 / 0.65 / 0.65 | 156 / 156 / 156 | 136.4 / 136.4 / 136.0 | 0.65 / 0.68 / 0.70 |

At c = 7 the mazes are less open (a 7 × 7 tree opens 48 of 84 internal segments, 0.57), and the goal placements
are twice as varied.

## 3. Code

**No engine change is expected:** `islands.py`, the maze world and the records are general in c.

**`scripts/e3d.py` parameterised, `scripts/e3e.py` a thin runner** (both reviewers: the override list must be
complete):
- **`scripts/e3d.py` gains one experiment record:** the label, the folders (formal and smoke), the design files
  and their hashes, the runner files the scripts guard checks, and the accounting name. Its defaults are E3d's.
  Reduction 3's ids are derived from the tree reference block (its first 64 ids), not written out.
- **`scripts/e3e.py`** sets that record and the registry's c, run seed and blocks, then calls the same stages.
- **The verdict wording** comes from the record's label. `wormwars/e3/e3d_gate.py` takes the label as an
  argument, defaulting to "E3d". It is an analysis module, not the rollout engine, so E3d's full-rollout
  references stand.
- **The scripts guard** checks both runners against the binding commit, with only the binding values blanked.
- **E3d's equivalence references are kept** deliberately: the engine is unchanged since E3d's binding. They
  establish the c = 5 and c = 6 comparisons, not exact replay at c = 7.

**Tests, each seen failing:**
- **the overrides:** c = 7, the blocks, the seed, the folders (formal and smoke), the accounting name, both
  design hashes, both runners guarded, reduction 3 at 31 200-31 263;
- **the labels:** no E3e record or verdict string starts with "E3d:";
- **the c = 7 tree-tour qualification above,** each hand;
- **the construction at c = 7:** interior range, the 228 pairs, the distance bound, feasibility of the
  calibration ids;
- **the full report on a calibration failure** (intervals, scent split, counts), and the summary's handling of a
  multi-strain B_max member.

**Rule 7:** `g-e` runs as in E3d. If the engine is unchanged since E3d's binding, its references stand; if
any engine file changes, a new reference is made from the commit before the change, as in E3d.

**Compute:**
- **a ceiling of 3 GPU-hours.** E3d's calibration took 0.68 h at c = 6; E3e's full plan, if calibration passes,
  is estimated at about 2 h. `project` measures it;
- **the owner is told before any GPU use.**

## 4. What happens next

- **If E3e passes,** E4 can use this family at the chosen k_r, with its own blind references.
- **If it fails,** the failed criteria are reported in the bound wording and the owner decides again. No further
  revision runs without the owner.

## 5. Changes from v1 (both reviews, D233)

- **E3d's design is bound** by hash and guarded with E3e's own (both).
- **Every verdict string reads "E3e";** the gate takes a label (Fable).
- **Reduction 3's ids** come from the tree reference block (both; Astra reproduced the old ids being restored).
- **The runner is parameterised in full:**
  - the folders, formal and smoke;
  - the accounting entry point;
  - both runners guarded (both).
- **A calibration failure is reported in full,** and the summary handles a multi-strain B_max member (Astra).
- **Also added:**
  - the G2a failure reading;
  - the projection note and the "2 h" qualified;
  - the 228 pairs;
  - the 96-move lap;
  - the qualification by hand and its seed;
  - the horizon claim as an expectation (both).

The hygiene exemption's comment ("6 × 6") is updated with E3e's first record; its bound of 8 still holds.
