# E3e: E3d's island mazes at 7 × 7 (design v1, for review)

**Status:** draft v1, for review by both reviewers, then binding. E3e is exploratory: it validates a task, and
it trains nothing.

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
erratum in §11), **unchanged except for the differences listed in §1.** E3d's §4 requires fresh calibration and
confirmation blocks for a revised construction, so E3e plays new ones. Everything this note does not change is
E3d's text, and is read from it.

## 1. The differences from E3d

| | E3d (bound) | E3e |
|---|---|---|
| Maze size c | 6 (a 25 × 25 grid) | **7 (a 29 × 29 grid)** |
| Interior cells (goal candidates) | rows and columns 1-4: 16 cells, 78 pairs | **rows and columns 1-5: 25 cells**; the pairs whose rings share no post |
| A-B graph distance | [⌈c/2⌉ + 1, 2c] = [4, 12] | **[5, 14]**, the same rule |
| Maze run seed | 1 190 000 | **1 191 000** |
| Calibration block | ids 30 000-30 127 | **ids 31 000-31 127** |
| Confirmation block | ids 30 200-30 455 | **ids 31 200-31 455** |
| Tree reference | ids 30 200-30 327 at c = 6 | **ids 31 200-31 327 at c = 7** |
| Tangent diagnostic | ids 30 200-30 263 | **ids 31 200-31 263** |
| The wall-follower's tree-tour qualification | 10 6 × 6 trees (ids 40 000-40 009) | **the same test also at c = 7**: it enters all 49 cells within 2 400 ticks in at least 9 of 10 trees (ids 40 000-40 009 at c = 7) |

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

**The horizon stays 2 400 ticks.** The owner chose a larger maze, not a shorter horizon. A larger maze lengthens
every route, so the navigators' scores will fall too; G2a and G2b test that they stay high enough.

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

**`scripts/e3e.py`:** a thin runner that loads `scripts/e3d.py` and overrides:
- its registry: c, the run seed and the blocks;
- its folders: `experiments/E3-ab-organism/E3e/`, `runs/e3e/`;
- its design path, its binding constants, and the runner checked by the scripts guard.

E3d's stages, gate, records and report are reused unchanged.

**Tests, each seen failing:**
- the overrides: c = 7, the blocks, the seed, the folders, the design path, the guard checking `scripts/e3e.py`;
- the c = 7 tree-tour qualification above;
- the construction's tests run at c = 7 too (interior range, distance bound, feasibility of the calibration ids).

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

## 5. Decisions open for the reviewers

1. **Is "E3d unchanged except §1"** a sound basis, or does the size change need anything else, for example the
   horizon or the scent's reach relative to the larger corridors' lengths?
2. **The wall-follower's qualification at c = 7:** enough, or should all of E3d's qualification tests repeat?
3. **The thin-runner approach** (overriding E3d's runner) against a copied runner.
