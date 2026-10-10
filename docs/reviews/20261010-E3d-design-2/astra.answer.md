**Verdict: revise.** The carved construction is sound, and I would retain 6 × 6 and the smallest-qualifying-\(k_r\) procedure. The remaining problems concern the blind benchmark, what the gate establishes, and several measurement definitions.

I verified HEAD `292508f`, read both v1 reviews and the referenced implementation, and made no file changes. Python was unavailable, so I could not rerun the sizing script or repository dynamics. I checked the geometry separately in memory; those checks support the carving, not behavioural performance.

Most of my v1 requests were taken correctly: geometric and behavioural claims are separated; shared goal components are forbidden; spawns are corrected; the blind family is expanded; calibration uses the gate; confirmation uses the declared maximum; discovery, structure and component measures are added; and rule 7 now names an independent full-rollout reference. D222’s statement that *every* required change was taken is nevertheless too strong for the reasons below.

The geometry in **§2 is correct** against [`maze.py`](/D:/Claude/random/wormWars/wormwars/e3/maze.py:89). A segment opening removes its three intermediate raster cells and preserves its endpoint posts. Each goal has eight outward segments incident on its four posts. Opening those disconnects its remaining boundary walls from the rest. Chebyshev separation of at least two prevents shared posts; subsequent openings cannot reconnect components. The resulting “ring” can comprise several disconnected pieces, rather than one enclosing wall, which is acceptable for the stated guarantee. Connectivity is preserved by adding edges.

**Does it retain enough maze?** Plausibly, but the current evidence does not establish that. The raw-draw open shares of approximately 0.69–0.76 leave substantial barriers, and selecting the smallest qualifying \(k_r\) is sensible. Detours, junctions and visibility on the **accepted distribution** must determine how much navigation remains. A behavioural pass alone does not demonstrate substantial routing difficulty.

I accept G1a’s quarter-ratio, G2a’s one-third ratio, G2b’s four-visit floor, and G3a’s practical margin as exploratory operational thresholds. The tree column’s arithmetic and cited values check out; its explicit warning about different blocks makes it acceptable as an illustration, not a paired tree-versus-island comparison. The confirmation maximum is also legitimate. Reporting scent reach rather than rejecting those placements is reasonable.

Required changes:

1. **Include the other known scent-free champions in the benchmark.**

   [§3](/D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:113) includes only the S champions with noses removed in \(B_{\max}\), although it already schedules noses-removed plays for P-sel, P-joint and the seed.

   These are credible adversaries supported by existing evidence. [E3c’s results](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:142) report P-joint noses-removed scores of **2.85–5.96**, and classify all four P-sel champions as nose-independent. Excluding them permits a pass despite an already-known controller solving the new task without scent.

   Include all these noses-removed conditions in calibration and confirmation’s blind maximum. This closes a concrete omission; I am not asking for an unlimited search over hypothetical algorithms.

2. **Make “rarely completes a round trip” an actual criterion, and correct the visit arithmetic.**

   G1b does not establish the promise in §1(a). A population where two-thirds make three visits and one-third make none averages two visits while **two-thirds complete a round trip**. It can pass G1a as well if the follower averages eight.

   Add a prespecified limit on the maximum blind round-trip share if “rarely” remains part of the question. For example, a ceiling of 10% would give that word a clear operational meaning. Alternatively, explicitly narrow the claim to low average blind throughput.

   The explanatory wording in [the gate table](/D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:169) also needs correction. Existing [`maze_measures.legs`](/D:/Claude/random/wormWars/wormwars/e3/maze_measures.py:32) defines legs as `max(visits − 1, 0)`:

   - Three visits, A→B→A, complete one round trip.
   - Four visits complete three legs, not two round trips.
   - Five visits complete two round trips.

   Four mean visits remains a defensible absolute performance floor; describe it as four mean visits.

3. **Remove the false “no island contact is impossible” interpretation.**

   [§4](/D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:189) says a successful blind control without island contact indicates a construction fault. That is wrong under §5’s contact definition.

   Consider a goal with an open north entrance. A centreline entry passes through raster positions
   \((4i,4j+2)\), \((4i+1,4j+2)\), and \((4i+2,4j+2)\).
   Their 3 × 3 neighbourhoods contain neither entrance post; the entrance segment is open. The animal therefore scores a visit without recorded island contact. More generally, routes along open maze-cell centrelines can avoid this contact neighbourhood throughout.

   The geometric guarantee excludes **remaining beside the perimeter component**, not traversing free space without approaching an island wall.

   Read this outcome as free-space coverage or excursions requiring trajectory inspection. Likewise, high island-contact share alone does not establish switching: the island could be the first component acquired. Record initial acquisition and relate component transitions to visits before assigning that explanation.

   Two other readings should be qualified:

   - A random-walk failure establishes that the tested walk succeeds; “too open or too small” is a possible explanation, not an identified cause.
   - An oracle below the follower is an unqualified reference, not necessarily a software or construction fault—the oracle is explicitly not optimal.

4. **Correct and complete the sizing report.**

   The main feasibility error from v1 is fixed. [`placements()`](/D:/Claude/random/wormWars/scripts/e3d_sizing.py:66) checks separation, final graph distance and spawn existence. For carved draws, the script correctly checks the **nominated pair**, rather than accepting some other feasible pair.

   But the report still needs these distinctions:

   - **“Of 73” is an observed count, not the placement space.** There are 78 unordered interior pairs satisfying the post-separation rule. The carved samples observed 73. The script’s `distinct_placements` counts observed support; it does not prove that other pairs are impossible.
   - **Open share includes rejected draws.** [`summarise()`](/D:/Claude/random/wormWars/scripts/e3d_sizing.py:136) computes placement entropy from feasible rows but open share from all rows. Report raw and accepted open shares separately.
   - **The requested placement histogram is missing.** The script builds its weights internally but saves only summary statistics. Save the pair-level frequencies.
   - **The sizing does not implement nested \(k_r\) draws.** It uses independent samples across settings and `rng.choice(..., size=k_r)`, whereas §2 specifies prefixes of one permutation. That is adequate for marginal first-draw feasibility sizing, but does not validate nesting or the production redraw scheme. Say so, and test the production sampler separately.

   Also qualify “placements are drawn uniformly”: the **proposal** is uniform; acceptance conditions generally change that distribution.

5. **Resolve the measurement discrepancies before implementation.**

   Several definitions in [§5](/D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:206) cannot simply reuse the existing functions:

   - **Later-leg rate:** v2 says “after the first two”; [`later_leg_rate()`](/D:/Claude/random/wormWars/wormwars/e3/maze_measures.py:41) measures legs per elapsed time after the **first visit**. Choose one explicitly, including how nonqualifying animals contribute.
   - **Median legs:** E3b-1 takes the median **over colony means**, as implemented in [`scripts/e3b1.py`](/D:/Claude/random/wormWars/scripts/e3b1.py:1348). That differs from the median over individual animals. Specify which G3b uses.
   - **Discovery of B:** [`MazeWorld._post_move()`](/D:/Claude/random/wormWars/wormwars/e3/maze_world.py:378) records `first_b_tick` only for a confirmed B visit after A. It does not record an incidental first discovery of B before A. Add raw first-entry times if discovery means physical arrival, and specify handling of nonarrivals.
   - **Scent reach:** the \(d≤8\) flag is a grid-field proxy. Actual nose readings use offsets, bilinear interpolation and occlusion. The neural seed also does not implement the scripted follower’s hard `0.005` branch. Retain the flag, but do not present it as an exact detectability classification for every navigator.

   Add hand-computed tests for these measures, coverage and the corrected round-trip criterion.

6. **Finish the executable protocol and qualification details.**

   The wall-follower’s policy is sufficiently concrete to implement, and privileged sensing is acceptable. However, [§3](/D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:124) still needs to specify raster sampling—Boolean cell lookup versus interpolated values and a threshold—plus boundary handling. Privilege alone does not establish that it is a stronger hugger than W2.

   Its qualification should include convex corners, isolated posts and separated components. Retaining one component on a tree is not a meaningful switching test because every wall belongs to the same component. Keep the full-tree-tour test, and require qualification before interpreting its island performance.

   Before play, also freeze:

   - Episode number, A/B orientation assignment, and RNG streams for carving, openings, spawns and random-walk noise. The existing [persistent walk](/D:/Claude/random/wormWars/wormwars/e1/controllers.py:52) consumes shape-dependent sequential random draws.
   - The exact reduced grids and a stop rule if both prescribed reductions still exceed three GPU-hours.
   - Whether the oracle precondition applies during calibration as well as confirmation.
   - Bootstrap calculations that resample paired mazes and **recompute the maximum across all blind settings** in each resample.
   - Which organisms play on each block: §5 says every organism on both, whereas §6’s compute schedule reserves most champion conditions for confirmation.

   **Rule 7 itself is now correctly directed.** The pre-change `40bd50f` reference, zero tolerance and separate CPU/GPU comparisons address my v1 requirement. Pin the controllers, IDs, horizon, compositions and replay settings used by that reference. Test nesting at a shared redraw index; accepted mazes can legitimately differ after redraws. For the oracle, distinguish shortest graph next hops from an exactly shortest continuous trajectory.

The champion predictions can remain descriptive. Specify whether they apply per champion or to arm means. Intact S transfer with poor noses-removed performance would defeat the **collapse prediction**, but would support scent dependence on the new task; it would not contradict the anti-blind objective. P-joint retaining half its score remains a tentative transfer prediction, not evidence that navigation was retained.