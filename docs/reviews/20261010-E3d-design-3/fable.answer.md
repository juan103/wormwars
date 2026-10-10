**Verdict: bind and proceed to code, after three textual corrections are made in the file before the binding commit.** None touches the construction, the family, the blocks or the gate's numbers, so no further review round is needed. If the process demands a strict either/or, read them as "revise", items 1-3 below.

## 1. My v2 required changes

All six were taken, and correctly.

- **k_r excludes the goals' sides; the roundabout stated; the "soften" claim dropped.** `docs/E3/E3d-DESIGN.md:56-63` and `scripts/e3d_sizing.py:132` (`a not in s and b not in s`). The sizing was rerun with the production nesting. I checked every cell of the §2 table against `docs/E3/e3d-sizing.json`; all match, including the accepted open shares and 322 of 337.
- **Three contact classes, goal-ring contact on the closed 5 × 5 block, the false reading removed.** §6 lines 264-270; the four G1 readings at lines 234-241 no longer say "impossible".
- **Round-trip wording** fixed to the codebase's legs. Lines 203-204, 209-212, matching `wormwars/e3/maze_measures.py:32`.
- **The 6 × 6 tree reference** and per-arm predictions. Lines 187-189 and 243-248. The 0.69 figure is 48/70, the full tree tour 2(c² − 1) at each size, so the arithmetic holds.
- **A/B keying and the swap.** Lines 46-47 and 50-51.
- **The follower's probe rule, convention and 1.5-cell ahead probe.** Lines 145-157. The sign convention matches `wormwars/world.py:945,955`.

The recommended items were taken too, except that the rule-7 pin list is still incomplete (below).

## 2. New errors in v2.1

**§2, excluded sides and nesting: correct.** I checked the carving geometry against `wormwars/e3/maze.py:89-94` and the script's `touches` test, lines 116-131. With Chebyshev distance 2 or more, one goal's carving never touches the other goal's sides, since that would need a shared post. Each goal therefore keeps exactly the tree's entrances. The k_r prefixes of one permutation give nesting at a shared redraw index, and the design says the redraw breaks it. The count of 78 pairs is right. Two of the final checks are automatic for carved goals: every wall cell in a goal's closed block is its own ring, so island-safety and "no shared component" cannot fail. That is consistent with almost every infeasible draw failing only the distance's lower bound. One limit case the wording covers but should be reported: a goal of tree degree 4 has no ring at all, only four isolated posts in an open plaza. Add each goal's entrance count to §6's per-maze record, since it drives a random walk's discovery rate.

**§3, the blind family: one miscited number.** Line 136 says P-joint scored "2.85-5.96 without noses on its probe block (3.65-5.92 on its test block)". Both ranges are from E3c's test block, and 3.65-5.92 is the **trails-off** condition with the noses intact, not noses removed. See `experiments/E3-ab-organism/E3c/RESULTS.md:144,164,225-228`, and the per-champion values in `experiments/E3-ab-organism/E3c/evaluate.json` under `p_joint` (noses_removed 2.85-5.96, trails_off 3.65-5.92). The decision to include the P arms stands on the correct number. The sentence must be fixed before binding, under rule 5.

**§5, G3a against the family: coherent.** One reading is missing. With G1b at 2.0 and the seed's margin at max(0.5, 0.10 × seed), a G3a failure while G1 passes can only mean the seed itself scores below about 2.5 on the family. That says the engineered navigator or the scent's reach failed, not the blind family or the construction. §9's "the failed criteria say what the next construction must change" is not true for that case. Recommended: one sentence under the readings.

**§4-5, tree reference and predictions: correct.** The reference's goals are E3b-1's dead ends and may lie on the perimeter, which is fine for a size reference. The island and tree families share ids 30 200-30 327. If `islands_for` draws its tree from the same stream as `walls_for`, the island maze at redraw 0 is carved from the same tree as the tree-family maze of that id. That is harmless, and a nice pairing if true. Say whether the streams are shared.

**§6, contact classes: one definition is now trivial.** Goal-ring contact is the head inside the closed 5 × 5 block, which the head enters before the 3 × 3 open block. So "the class of the last component contacted before each visit" is always the visited goal's ring. §5's switching reading, line 235, needs the component before the goal-ring episode. Define it as the last component other than the visited goal's ring, or none. Also give a tie rule for a tick touching two classes, which is possible at posts of different components. The switch rate depends on it.

**§5, the gate's follower.** G1a names "the follower (shared)". G2a, G2b and the oracle's precondition say only "the follower", and both the shared and the trail-free follower are played. Name one.

**§7-8, pins and binding.** The rule-7 full-rollout leg pins the controllers, ids, c, H, colony, chunk and access, but not the maze run seed, the episode or the dtype. Add them. State that the dumper is the new driver run with `--root` at the 40bd50f worktree, as `scripts/e3_equivalence.py:3-8` does, so one script drives both engines. §8 says `calibrate` refuses on any change to the design, and also that amendments are added beside the text. Those agree only if an amendment re-binds at its own commit, as E1's `require_same_code` guard implies at `wormwars/registration.py:149-153`. Say so.

Other checks that passed: the scent arithmetic at σ = 3, reach 9 and nose scale 0.35 gives detectability at d ≤ 8 for the follower's 0.005 threshold (`wormwars/e3/maze_world.py:47,234-240,343`); E3c's W2-turn grid matches `wormwars/e3/e3c_formal.py:18`; the 28-champion count; the tree column's four numbers and ratios; G3b's median form at `scripts/e3b1.py:1061,1348`; the turning radius 0.35/0.30; the oracle's shortest-path hop over `Maze.edges` at `wormwars/e3/maze_controls.py:130-142`. W2's "right-handed" label is unverified here, but the mirror-symmetry argument makes it immaterial.

## 3. Required before binding

1. **§3, line 136:** cite P-joint's noses-removed range as 2.85-5.96 on E3c's test block; drop "probe block", and either drop 3.65-5.92 or label it trails-off.
2. **§6, line 269-270:** define "the last component contacted before each visit" as the last component other than the visited goal's ring, and give a tie rule for a tick in two classes.
3. **§5:** name the shared follower in G2a, G2b and the oracle's precondition.

Recommended, not blocking: the rule-7 pins for run seed, episode and dtype; the goals' entrance counts per maze; the G3a-only-failure reading; whether the island and tree streams are shared; the oracle precondition's "a visit" as any wey or every wey; and the one sentence on re-binding after an amendment.