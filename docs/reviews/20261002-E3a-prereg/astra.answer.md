**Verdict: bind after fixes.** I checked `roadmap` at `a7177e7`, the cited design/reviews, frozen inputs and relevant code. No files were changed and no E3 stages were run.

**D163:** Most pins are carried in: separate gate worlds, separation-based tolerances, end-of-window readings, stimulus pooling/rounding/censoring, census-zero wording, S2-b’s asymmetric comparison, comparator self/mutual ties, reset write and retained Stage 3 indices. Two qualifications:

- B-task’s sensory-blind start is **deliberately replaced**, with the departure disclosed.
- B-task’s τ draws say “log-uniform” without explicitly giving the bounds. State `[0.5, 20]`, and explicitly state the bias clipping bounds.

**§12:** The S-shuttle correction is right. `freeze.json` confirms `(8192, 1, 0)` overall and `(32, 1, 0.2)` for `k ≤ 32`; the blind-controller settings and both input-file hashes also match.

The oracle change needs different wording. Its formula is a **straight-run plus stationary-turn reference**, not an established geometric maximum: [the engine turns and moves in the same tick](D:/Claude/random/wormWars/wormwars/world.py:799), and reversal angles depend on entry geometry. Choosing 0.6 before running is legitimate, but it is a new threshold choice, not a demonstrated kinematic correction. Name the reference accordingly and pin the integer count—for example `1 + floor((600 − first_leg_time)/later_leg_time)`—including whether individual leg times are rounded.

The remaining binding fixes are:

1. **Repair the stage dependencies.** [§5](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/PREREGISTRATION.md:188) selects champions after Stage 3, although Stage 3 starts from Stage 2 champions. Validate and freeze Stage 2 champions before Stage 3. Champion calibration also cannot occur before champions exist. G1’s clamp applicability currently refers to calibration scheduled after G1; “every memory assay” additionally suggests the release assay, whose D is not yet available. Specify the actual dependency order and precisely which assays gate G1.

2. **Replace the fixed-point grid’s root isolation.** [§6’s method](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/PREREGISTRATION.md:296) can miss a stable/unstable pair inside one grid cell. I checked an allowed float32 example:
   `w = 1.0119999647140503`, `b = 0.0008732174756005406`.
   The grid detects only one root. It misses a stable root near `−0.109338956`, whose derivative is approximately `−2.73e−6`; the other stable root is near `0.219702890`. They meet both registered thresholds. Bracket using the stationary points `±acosh(sqrt(w))` when `w > 1`, then bisect monotone intervals. This flaw also exists in the agreed design.

3. **Finish the assay contract.** Specify integer rounding for `W`, when W starts relative to the stimulus, and how stable states acquire A/B labels while allowing mirrored polarity. Handle an empty uncensored-duration pool, not just “no confirmed visit.” Also specify the release starting state when “otherwise monostable” includes multiple equilibria separated by less than 0.1. Enumerate applicability: scripted controls and L1-switch have no q; random-search champions and census qualifiers need explicit calibration and clamp coverage.

4. **Correct the component ablation.** [The offset expression](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/PREREGISTRATION.md:265) should be `|u_with − u_without|`, not `|u_with| − |u_without|`; the latter can pass a substantial steering change. B-shared needs a separate definition: its nose pairs do not each own 16 motor-output edges. Specify which nose-to-comparator edges are removed and how its contributions are measured.

5. **Complete B-task’s symmetry and ties.** [The nose-pair rule](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/PREREGISTRATION.md:368) leaves nose self/mutual edges unresolved. Under independent residual draws, equal sensory inputs need not produce equal nose states, defeating the claimed zero added turn. Specify the full within-pair block, as done for comparators. For random sampling, also say whether final-validation ties use original draw `j` or position in the sorted shortlist.

6. **Fix the census interpretation.** [S2-c](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/PREREGISTRATION.md:449) checks only selectors passing a 16-world screen. Its Clopper–Pearson interval therefore bounds the probability of **passing the screen and full check**, not the probability of being a working selector: screen false negatives remain unchecked. Either change the estimand and zero wording or check every draw. Also remove or justify “the GA distribution contains no working selector”; monostability alone does not establish that under the registered working criterion.

7. **Resolve comparative readings and incomplete runs.** B-task inherits S2-b’s “neither found a working selector” branch without a valid B-task working assessment: its recurrent inputs invalidate the autonomous scalar-q equation. Give it a performance-only comparison or a separate criterion. Pin how missing pairs affect S2-a/S2-b, and what happens after a finally stopped Stage 2 batch. The per-run “not read” sentence does not settle arm-level readings.

8. **Finish reproducibility, admission and tests.** Restore the design’s 25-generation checkpoint schedule; define Stage 3’s single-source skill measurement. Pin projection shapes/timing rules, evaluation compositions, and CPU G-E genomes/configurations. Include validation, calibration and evaluation in the minimum-plan estimate. Add tests for these dependencies, admission/refusal/reductions, missing outcomes, screening false negatives, the root counterexample, nose symmetry and graft-registry reconstruction.

The proposed world blocks do not overlap the earlier ranges I checked, and random sampling’s generation-to-world pairing matches `train_ids`. The existing `evolve_batch` can supply final populations, but its `champion_index()` selects among checkpoints; the runner must explicitly implement this draft’s final-population champion rule.