**Verdict: revise.** The basis is sound, and the task itself needs no change beyond §1. Three things in the inheritance and the thin runner would put a wrong label or wrong ids into a committed record. They are cheap to fix. The rest is pre-statement.

## 1. Is "E3d unchanged except §1" sound?

Yes. The construction, the world, the records and the gate are general in c. I checked `wormwars/e3/islands.py` for the interior, the pairs and the distance bound, `maze_world.py` for the arena, the scent and the trails, and `e3d_records.py` for coverage, the measures and the scent-reach flag. Nothing there assumes c = 6. The hygiene exemption admits indices below 8, so 0 to 6 pass.

**Horizon and scent should stay fixed.** Changing either would confound the size effect and alter the task E4 inherits. But the design should say what the fixed values imply at c = 7, because E3d's text has no reading for the failure they make likely:

- **G2a is the criterion most at risk, not G1b.** The scent's reach is 9 grid cells, about two maze cells, and the trail decays per tick. Both are fixed while routes lengthen, so the shared follower's discovery cost grows faster than the oracle's route. At c = 6 G2a passed narrowly. The follower over the oracle was 0.37 to 0.39, with every interval crossing one third. E3d §5 pre-states readings for a G1 failure and for a G3a-only failure. It has none for G2a. E3e should add one before binding.
- **G1b's expected margin is thin.** The walk already covered 90 to 95 percent of the 6 × 6 cells, so its visits scale roughly with the inverse area. That puts it near 1.7 to 1.9 against 2.0, with E3d's intervals about ±0.13 wide. The gate is on point estimates, so this is fine, but the owner should know 7 × 7 is a modest step.
- **The absolute limits are the point of the choice.** G1a passed at 0.14 to 0.15 and is unaffected by size. A pass at c = 7 comes from everyone's scores falling, as E3e's horizon paragraph already says.
- **The blind family's grids** are controller parameters and carry over. But see the projection.

**The projection will probably need deeper reductions than E3d's.** The stage times at c = 7 on fresh mazes, so it self-corrects. The "about 2 h" in §3 is an actual-cost guess, not the projection, and the two differ:

| | projected | actual |
|---|---|---|
| E3d calibration, c = 6 | 0.98 h, from `project.json`'s seconds per world and the plan | 0.68 h, `compute-record.json` |
| E3d full plan, reduced once | 2.38 h plus 0.25 h reserved | not played |

The field work scales with the grid area, 841 cells against 625. A projection near 3 h would trigger reduction 2, the W2-turn grid, and perhaps reduction 3, the tree reference cut to 64 mazes. Both are declared. The design should say so, so that the blind family actually played is not a surprise.

## 2. Size-specific text E3e's §1 misses

- **Reduction 3's ids.** E3d §7 and `scripts/e3d.py` line 89 hard-code the tree reference's cut to ids 30 200-30 263. E3e's table lists the blocks but not this. If the override covers `blocks` and not `reductions`, a triggered reduction 3 plays trees at E3d's ids under the new seed, unpaired with the confirmation block and the tangent diagnostic, against E3d §4's "common ids" rule.
- **The pair count.** Rows and columns 1-5 give 228 pairs at Chebyshev distance at least 2. The sizing file's random rows show 228 distinct placements. State it as E3d stated 78.
- **The coverer rationale** in E3d §4, 48 moves at c = 5 and 70 at c = 6. The lap is 96 at c = 7, so size alone predicts 0.73 × from c = 6 for a lap-coverer. Worth restating since it is what the owner's choice banks on.
- **The hygiene bound** holds, but its comment at `tests/test_publication_hygiene.py` line 97 says the largest maze is 6 × 6. Update it with E3e's first record.
- **The records** need nothing. The sizing's c = 7 rows are appended last in one sequential stream, so the earlier rows are unchanged, as the script's comment claims. The quoted values match the file. The third feasible share is 0.645, shown as 0.65.

## 3. The qualification and the thin runner

**The tour at c = 7 is enough.** The other qualification tests are local geometry, independent of size. State the run seed the test uses, 1 190 000, and that 2 400 ticks is ample for a lap of 96 moves.

**The thin runner is the right choice,** but §3's override list is incomplete. From reading `scripts/e3d.py`, the complete set is: the registry's design path, binding commit, design hash, seed, c, the four blocks and reduction 3's ids; the module globals for the folders, the design and the guarded list, then `configure()` called again; the scripts guard naming `scripts/e3e.py`; the smoke folder, which the smoke function sets with a global; the main block's accounting name and compute record; and the verdict labels. The equivalence references deliberately stay E3d's, which §3 should say.

**The labels are the real defect.** The gate's verdicts and the calibration choice in `wormwars/e3/e3d_gate.py` lines 66 and 81 read "E3d: passed", "E3d: failed", "E3d: not evaluable" and "E3d: failed at calibration". The runner's outcomes and the report's "not completed" do too. Unchanged, E3e's committed records would carry E3d's label. A module-level label constant the thin runner sets is the cleanest fix. It touches an analysis file under `wormwars/`, so the design should say explicitly that it is not a rollout-engine change and that E3d's full-rollout references therefore stand.

## 4. Revise

1. **Bind both design files.** E3e's bound text is E3e-DESIGN.md plus E3d-DESIGN.md with its amendments. The guard hashes only the path in the runner's design field. Pin E3d's sha256 too and add it to the guarded list. Otherwise a later amendment to E3d's file changes E3e's inherited text unnoticed.
2. **Relabel every verdict string "E3e",** with a test that no committed record string starts with "E3d:".
3. **Put reduction 3's ids, 31 200-31 263, in §1's table and in the override,** with a test.

Non-blocking, but before binding: a pre-stated reading for a G2a failure; the note that deeper reductions are likely and the 2 h figure is not the projection; the 228 pairs; the 96-move lap; the qualification's seed; the hygiene comment.