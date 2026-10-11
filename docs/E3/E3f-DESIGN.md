# E3f: E3d's 6 × 6 island mazes at a horizon of 1 800 ticks (design v1.1)

**Status:** v1.1, bound (D239), after both reviewers' review of v1 (`docs/reviews/20261011-E3f-design/`). Astra
said "bind"; Fable said "revise" with one wording item, taken in §1a. E3f is exploratory: it validates a task, and
it trains nothing.

**The stopping rule** (one formulation): E3f is the last horizon adjustment in this sequence. If it fails, the
failure is reported in the bound wording, and any further design is a new decision by the owner.

**Why it exists** (D237):
- **E3d** (6 × 6, H = 2 400) failed on G1b alone. **E3e** (7 × 7, H = 2 400) failed on G1a and G2a.
- **Both reviewers were consulted** (`docs/reviews/20261011-after-E3e/`).
  - **Astra proposed this validation.** Truncating E3d's saved, hash-verified trajectories at H = 1 800 passes
    every criterion on E3d's calibration block at every k_r. At k_r = 0: B_max 1.761 [1.656, 1.872];
    follower ÷ oracle 0.367 [0.308, 0.428]; B_max ÷ follower 0.151; the seed 6.457, with median legs 4.625.
  - **Fable reached the same horizon range** from the records.
- **Claude reproduced the truncation exactly.** A test shows that the stopping horizon is the only way the horizon
  enters the maze dynamics: `tests/test_e3d_world.py::test_the_horizon_only_stops_the_maze_run`.
  - **What it checks:** a 1 800-tick maze run equals the first 1 800 ticks of a 2 400-tick run, positions and
    visits, for the scripted follower and the random walk on two CPU mazes.
  - **It can fail:** a sabotage variant shows it.
  - **Its scope:** that scope only. It does not establish exact replay of formal GPU runs or of every controller
    and composition (Astra).
- **What that is and is not:** a selection on E3d's block, labelled exploratory. It is not a pass. E3f tests the
  selection on fresh mazes.

**What E3f is:** E3d's bound design (`docs/E3/E3d-DESIGN.md` v2.2, with Amendment 1, its correction and its
erratum in §11), **unchanged except for the differences in §1.** E3d's text is part of E3f's bound text, pinned at
sha256 `37ee0c39868f074446cca43fd0242ce8bf72e9f90127fdafbade60394e4b4147`, as for E3e.

## 1. The differences from E3d

| | E3d (bound) | E3f |
|---|---|---|
| Horizon H | 2 400 ticks | **1 800 ticks** |
| k_r | {0, 2, 4}, the smallest qualifying | **{0} only:** fixed for the maze structure it keeps (the most closed walls), not because it won a comparison (Astra) |
| Maze run seed (the mazes' random stream, not the organism) | 1 190 000 | **1 192 000** |
| Calibration block | ids 30 000-30 127 | **ids 32 000-32 127** |
| Confirmation block | ids 30 200-30 455 | **ids 32 200-32 455** |
| Tree reference | ids 30 200-30 327 at c = 6 | **ids 32 200-32 327 at c = 6, H = 1 800** |
| Tangent diagnostic | ids 30 200-30 263 | **ids 32 200-32 263** |
| Reduction 3 | the tree reference's first 64 ids | the same rule: **32 200-32 263** |
| The verdict wording | "E3d: …" | **"E3f: …"** |

**Unchanged** (E3d's text):
- **c = 6** and the carved-island construction;
- **the world:** colonies of 8, shared trails (μ 0.01, λ 0.02, δ 0.05, d₀ 1.142), the scent's σ and reach, the
  visit rule;
- **the blind family and its grids,** the navigators, the seed and E3c's 28 champions, who plays where;
- **the gate:** G1a-G3b and their thresholds, and the oracle's precondition;
- **the bootstrap,** the readings, the champions' predictions (against the H = 1 800 tree reference) and the
  records;
- **the compute ceiling** of 3 GPU-hours and the reductions in order.

## 1a. The horizon in E3d's text, and what the absolute criteria mean at 1 800 ticks (Fable)

- **Where E3d names the horizon:** in four places, each read here at H = 1 800.
  - **§1(c):** "the rest of the task is E3b-1's" now reads with the horizon at 1 800 ticks. The question a pass
    answers is about this horizon.
  - **§3:** "H = 2 400" reads H = 1 800.
  - **§5's tree column** stays a historical illustration at 2 400.
  - **§7's rule-7 leg** keeps its pinned 2 400 ticks: the engine is unchanged. E3f's `g-e` therefore does not run
    its own horizon on the GPU; the truncation test covers that path on the CPU.
- **The absolute criteria are counts per horizon, not rescaled:** G1b (2.0 visits), G2b (4.0), G3a's margin and
  G3b's two legs.
  - At 1 800 ticks, G1b's cap corresponds to about 2.67 visits per 2 400 ticks, above the walk's 2.34 that failed
    E3d.
  - On E3d's block, the truncated B_max grows near-linearly with H: 1.58, 1.76, 1.96 and 2.34 at 1 600, 1 800,
    2 000 and 2 400 ticks.
  - So a G1b pass at 1 800 reflects the shorter window, not a change in the blind family's throughput.
- **The horizon-robust test is carried by G1a and G2a,** the blind control against the follower and the follower
  against the oracle.
- **Why this is legitimate:** the horizon is a task parameter that E4 inherits, so the task validated is the task E4
  plays. It is stated here so that a pass is not read as a lower blind throughput.
- **The truncation's prediction covers E3d's played blind family:** E3d played its first reduction, with three
  walk settings. E3f's projection may admit more walk settings, which could raise E3f's B_max (Astra). That is a
  risk to the prediction, not a defect of the validation.
- **Calibration is a sequential screen** with the same criteria as confirmation, not a choice. A pass needs both
  blocks to pass. On G2a alone, a false failure on one block is roughly a one-in-five event at the predicted point
  (Fable). The design accepts that risk.

**With k_r = 0 only, calibration's choice is degenerate:** calibration passes if its point estimates meet G1-G3, the
precondition and the feasible floor, and then confirmation is played. A calibration failure is reported in full
(E3e §1a's rule, carried in) and confirmation is not played.

**The G2a reading** is E3e's bound wording, labelled for E3f: "A G2a failure means the shared scripted follower falls
below the required one-third of oracle throughput on this block. Increased discovery cost associated with fixed
scent reach and trail decay is a possible explanation, to check against discovery, scent-reach, no-first-visit and
later-leg records—not an identified cause. Blind-control performance is assessed separately by G1."

## 2. What the truncation predicts, and the risks (exploratory, stated before any play)

On E3d's block at k_r = 0 and H = 1 800 (truncated):

| B_max | follower | oracle | seed | G1a | G1b | G2a | G3a margin | G3b |
|---|---|---|---|---|---|---|---|---|
| 1.761 | 11.63 | 31.70 | 6.46 | 0.151 | 1.761 < 2.0 | 0.367 | 4.70 | 4.63 |

- **The narrowest criteria:** G2a (interval 0.308-0.428 on E3d's block) and G1b (B_max's interval reaching 1.872).
  A fresh block can fail either; that would be reported, not adjusted.
- **The horizon was chosen on E3d's block,** so E3f's blocks are new mazes (seed and ids). No E3f maze has been
  played.

## 3. Code

- **`scripts/e3f.py`:** a thin runner over `scripts/e3d.py`, as `scripts/e3e.py`. It sets H = 1 800,
  k_r = [0], the seed, the blocks, the label, the folders, both bound designs and both guarded runners.
- **No engine change.** E3d's full-rollout references stand; `g-e` runs as before.
- **Tests, each seen failing:**
  - the overrides (H, k_r, seed, blocks, folders, label, both designs, both runners guarded, reduction 3's ids);
  - every E3f calibration id builds at k_r = 0;
  - the horizon-truncation test above, with the random walk added and a sabotage variant;
  - the summary script reports a confirmation block when one exists, as it reports calibration: the gate, the
    intervals, the scent split, the navigators' later-leg rates and discovery medians, the B_max member's detail,
    the champions' exact counts and the trail-free follower (Fable, before binding).
- **Compute:** about 0.5-1 GPU-hour by Astra's extrapolation, within the ceiling of 3. `project` measures it.
- **The owner is told before any GPU use.**

## 4. What happens next

- **If E3f passes:** E4 uses 6 × 6, k_r = 0, H = 1 800, with its own blind references played on its own mazes.
- **If it fails:** the stopping rule above applies.

**For E4's design, from the consultation** (not part of E3f; recorded so that they are not lost):
- the blind references are a precondition for each arm's navigation, not a threshold for the effect;
- re-measure the references on E4's mazes;
- separate navigation competence from transfer;
- controls for trails and environmental information paths;
- real module isolation. The seed's inactive module is suppressed by saturation, not disconnected
  (`wormwars/e3/organism.py`).

## 5. Decisions open for the reviewers

1. **Is "E3d unchanged except §1"** sound at the shorter horizon?
2. **k_r = 0 only,** with a degenerate calibration choice: acceptable?
3. **The pre-stated stopping rule** (no further horizon adjustment).
