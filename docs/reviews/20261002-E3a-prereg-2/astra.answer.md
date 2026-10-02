**Verdict: bind after fixes.** I checked `roadmap` at `3a513e6`, both archived reviews, design v2.4, and the relevant code. Four remaining gaps:

1. **G1 still depends on later calibration.** [The clamp applicability rule](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/PREREGISTRATION.md:337) unconditionally excludes organisms missing a goal phase on calibration worlds, but E’s calibration follows G1. Restrict that condition to organisms using calibration-derived states, or explicitly exempt E’s G1 assays.

2. **Stage 3 checkpoint skills need their own calibration coverage.** [The new measurement](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/PREREGISTRATION.md:393) requires states and goal assignments for checkpoint candidates. Stage 13 calibrates only champions and census qualifiers. Include frozen checkpoint candidates, with an explicit unavailable-state result. Also settle whether their first-entry shares use the assay worlds or test worlds: the surrounding paragraph says test worlds, while the referenced clamp assays specify assay worlds.

3. **The non-bistable release starting state remains ambiguous.** [“Smallest |q|”](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/PREREGISTRATION.md:318) can tie. I checked the allowed float32 value `w_qq = 1.000100016593933`, `b_q = 0`: stable roots are approximately `±0.0173221183`. Their separation is below 0.1, so this is registered as monostable, but neither root uniquely wins. Add a deterministic tie-break and a rule for multiple equilibria when none meets the registered stability threshold.

4. **Projection-to-admission accounting is still incomplete.** [The timing shapes](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/PREREGISTRATION.md:214) do not fix the workload used to calculate projected totals—particularly qualifier full checks before their number is known, and checkpoint assays/calibration. Pin those counts or bounding rules, how screening updates them, and actual evaluation chunk compositions. These choices can change reductions, admission, and champion selection.

Against Astra’s first-draft numbered fixes:

| Fix | Status |
|---|---|
| 1. Stage dependencies | Partial: principal order fixed; G1 dependency remains. |
| 2. Root isolation | Resolved. Stationary-point bracketing recovers the checked counterexample. |
| 3. Assay contract | Partial: release-start ambiguity remains. |
| 4. Component ablation | Resolved. |
| 5. B-task symmetry and sampling ties | Resolved. |
| 6. Census interpretation | Resolved. |
| 7. Comparative readings and incomplete runs | Resolved. |
| 8. Reproducibility, admission and tests | Partial: checkpoint coverage and projection details above. |

The state-to-goal assignment now handles mirrored champions coherently. The reset’s timing correction is present. B-task’s within-pair ties preserve equal-state symmetry at equal sensory inputs. The census interval now targets the screened-and-checked probability correctly. Admission’s **formula** is unambiguous; its projected workload still needs completing.

No files were changed and no E3 stages were run.