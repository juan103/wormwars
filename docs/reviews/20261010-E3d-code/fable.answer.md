**Scope note:** this session has no shell, so I read every file but could not compute hashes or run git or pytest. Two things are therefore unverified by me: that the constant at `scripts/e3d.py:78` equals the design file's sha256, and that the diff between the binding commit and aa6ca4a touches only `scripts/e3d.py`. Both fail safe if wrong, since `require_bound` would refuse.

## 1. Amendment 1 and 2. Conformance to the bound design

**Amendment 1 is legitimate.** It is dated, appended as §11 without touching the bound text, made before any play, and re-bound at 8b94c36 with D226 recording it. The reason is the one the bound text itself demands: §3 requires the qualification before the follower's results are read, and the bound policy failed it. The code matches §11 exactly: rays at half-cell steps at `wormwars/e3/e3d_controls.py:46-54`, the 12-tick search window at `:31` and `:69-71`, reset only by the side probes, ahead-wall override intact.

**It is a fair strongest hugger.** The bound policy could not acquire a wall from open space at all, so the amended one is strictly stronger at acquisition, and the hugging rule is unchanged once a wall is held. The one behaviour the search state adds, crossing a roundabout in a straight line after 12 ticks, is exactly what §6's contact records measure.

**The post-hoc thresholds are acceptable as disclosed.** They are declared in three places, `tests/test_e3d_wall_follower.py:100-102`, §11 and D226. The bound text named no numbers for that test, and the discriminating assertion is "touched no other component" at `:118`, which was not loosened. The 60% figure is now descriptive rather than binding; say so when the results are written.

**Conformance, checked item by item.** I found no departure that changes a reading.

- **Construction and keying:** streams match §2 at `wormwars/e3/islands.py:109-111`. The post arithmetic at `:70-75` and `:82` is right, so carving opens exactly the eight ring-road segments and nothing else. The k_r pool excludes the goals' sides at `:121`, nesting holds by construction at `:122-123`, checks at `:135-148` are the four of §2 step 6 over the final graph, and the redraw loop allows the original plus 64 redraws.
- **Blind family and who plays where:** `scripts/e3d.py:187-206` gives 56 blind members, intact arms only off calibration, W2 once. The tangent diagnostic is blind-only on the first 64 confirmation ids as §11 fixes.
- **B_max one per champion:** `wormwars/e3/e3d_gate.py:35-43` enumerates every strain of every blind condition.
- **Gate, precondition, k_r, predictions, bootstrap:** `e3d_gate.py:59-67`, `:70-81`, `:89-102` and `:105-124` match §4 and §5, including B_max recomputed inside each resample.
- **Records:** contact, classes, the remembered component, switches by class pair, the at-visit pair and coverage follow §6. The batched version is held equal to the readable one by a test on real island mazes.
- **Projection and reductions:** `scripts/e3d.py:384-420` applies the three reductions cumulatively in order and restores the registry afterwards.
- **Binding guard:** `scripts/e3d.py:129-139` checks the design hash and the engine diff.

Three non-blocking observations:

- **Bootstrap incompleteness.** §5 says every gate quantity gets an interval. G3b's median legs and the oracle's visit share are missing from `e3d_gate.py:109`. Adding them touches the engine, so it needs a re-bind. Re-binding costs nothing before any play, so I would do it now rather than report an exploratory interval later.
- **The guard excludes scripts.** `engine_changes` at `:123-126` diffs only wormwars, configs and requirements. The runner's own registry, block ids, grids and seeds, lives in `scripts/e3d.py` and can change in a committed, pushed commit after binding without refusal. The self-reference problem is real, but a workable rule is to require that `git diff <binding> HEAD -- scripts` names only `scripts/e3d.py` and that its numstat is two lines added, two removed. Provenance records make any such change auditable afterwards, so this is not a correctness risk.
- **Two small record nits.** The tree block's `spawn_candidates` at `:277` is the placement's spawn count, not the candidate count, so the tree summary's number is mislabelled. In the readable `contact`, `e3d_records.py:138-139` counts a tick once per component of a class while `contact_batch` at `:310` counts it once per class. On the 4-lattice a 3×3 window can only ever hold one component, so both the discrepancy and the tie rule are unreachable in E3d's mazes. Harmless, worth a one-line comment.

## 3. Tests and 4. Rule 7

**Tests that cannot fail as written.** `tests/test_e3d_runner.py:65-76` sets the binding commit to HEAD and the hash to the live file, so neither the stale-constant case nor the engine-changed branch is ever exercised. Add an assertion that the registered constant equals `design_sha256()` and a monkeypatched non-empty git diff. `test_redraws_beyond_the_limit_raise` reaches the limit only because c = 3 has no goal pairs, so the redraw-on-failed-check path is covered only indirectly through `im.k` in the nesting and stream tests, which is adequate.

**Required behaviour without a direct test.** The runner's world-to-strain-and-maze mapping in `summarise` at `scripts/e3d.py:287-335` is exercised only by the smoke runs. The "distance" and "spawn" branches of `failed_check` are never shown to fire. The module docstring of the wall-follower test still describes the pre-amendment policy at `tests/test_e3d_wall_follower.py:3-7`. The oracle-on-loops test required by §7 exists at `tests/test_e3d_oracle.py`.

**The equivalence leg is sound.** One driver, old engine imported from a worktree in a fresh subprocess, APIs both engines have, per-tick hashes of positions, headings, goals and visits, events and config hashes, pins compared. The tree family leaves the configuration dictionary unchanged, so the config hashes are comparable. Before the GPU plays these must hold:

1. The GPU reference is made from the 40bd50f worktree with the same device string the compare will use, since `compare` at `scripts/e3d_equivalence.py:122-123` requires the device strings to match. Commit it with its hash.
2. `g-e` passes on CUDA, including E3c's inherited legs.
3. A `--smoke --device cuda` pass of all five stages. D226 says the smoke ran on the CPU only, and the new code has device-dependent paths in `wall_follow_turn`, `tangent_start` and the path recorder.
4. The cap clock counts every category, `wormwars/registration.py:130-137`, so the hours spent by `project` and `g-e` come out of the same 3 hours the projection admits against. Check that the projection plus g-e's measured cost leaves headroom, or the confirmation can stop at the cap.
5. The full-rollout compare runs as a subprocess outside the accounting, so its rollouts are uncounted under rule 8. Small, but say so in the compute record.

## 5. Verdict

**Run,** once the owner is told and items 1 to 4 above hold. Nothing I found makes a result wrong or uninterpretable. If you re-bind for anything, fold in the G3b bootstrap interval and the two guard tests in the same commit.