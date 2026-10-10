**Verdict: revise — one required change, in the contact diagnostics.** The construction and G1–G3 do not need changing.

I verified HEAD `44b81c0`, read the archived [Astra v2 review](/D:/Claude/random/wormWars/docs/reviews/20261010-E3d-design-2/astra.answer.md), and checked the design against the referenced code and sizing JSON. I changed nothing. Python was unavailable, so I did not rerun the sizing or dynamics.

**The v2 required changes were largely taken correctly:**

- **Excluded sides and nesting:** [§2](/D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:44) and [`carved()`](/D:/Claude/random/wormWars/scripts/e3d_sizing.py:103) agree: both goals’ sides are excluded, and each \(k_r\) uses a prefix of one permutation. The qualification that accepted mazes can cease to be nested after different redraws is correct. Observed support, proposal versus acceptance, histograms, and accepted open shares are now distinguished. The reported **322 of 337** failures and the 6 × 6 table agree with [the JSON](/D:/Claude/random/wormWars/docs/E3/e3d-sizing.json).

- **Blind family and G3a:** [§3](/D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:123) includes all 29 noses-removed organisms on calibration and confirmation. This matches [`without_scent()`](/D:/Claude/random/wormWars/wormwars/e3/attribution.py:182). Including the seed’s ablation in \(B_{\max}\) is coherent: G3a requires the intact seed to beat its own ablation, as well as every other blind member. It creates neither circularity nor an impossible inequality.

- **Claims and measures:** [§5–6](/D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:204) correctly narrow the claim to average throughput, define G3b over colony means, adopt the existing later-leg rate, distinguish raw discovery from confirmed B visits, and qualify the scent flag. Recomputing the blind maximum inside each bootstrap resample is specified correctly.

- **Tree reference and predictions:** [§4–5](/D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:182) remove the maze-size difference and define the predictions at arm level. The P-joint qualification is appropriate. This compares complete maze families, including their different placement rules; it does not isolate carving alone. Also, any *paired* tree–island comparison must use their common IDs; the declared full-block arm-mean ratios remain valid descriptive comparisons.

- **Qualification, rule 7 and binding:** [§7–8](/D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:280) address the outstanding protocol requests: probe semantics, qualification cases, streams, reductions, block membership, independent pre-change reference, zero tolerance, controllers, horizons, composition and replay setting. Binding before calibration is appropriate. These are specifications to verify during implementation, not equivalence results already established.

**Required change:**

1. **Separate goal-block occupancy from physical wall-component contact.**

   [§6](/D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:257) now defines “goal-ring contact” by entering the closed 5 × 5 block, but uses that contact to report component acquisition and switches. Those are different things.

   A goal ring can contain several disconnected wall components, as §2 explicitly acknowledges. Entering its block does not identify which component was contacted—or establish physical wall contact at all. The new tree reference makes the conflict sharper: its walls belong to the perimeter component, yet the unconditional goal-block rule assigns “goal-ring contact” there too. A tree trajectory can therefore receive competing classifications or apparent switches despite there being only one wall component.

   The “last component contacted before each visit” also becomes largely tautological: entering the surrounding goal block registers the target ring before entering the visit block.

   **Keep goal-block entry as a separate flag. Define component acquisition and switches using actual raster component IDs, with their perimeter/goal-ring/other-island classes.** Specify how no-contact ticks affect the remembered component and when the pre-visit contact is sampled. On a tree, all actual wall contacts must remain perimeter contacts and physical component switches must be zero. Add hand-computed cases for a centreline goal entry without nearby walls, a fragmented ring, and a tree goal.

The old false “no island contact is impossible” reading was removed correctly. Its replacement introduced this measurement problem. It affects the proposed mechanism readings and qualification records, rather than the gate thresholds.