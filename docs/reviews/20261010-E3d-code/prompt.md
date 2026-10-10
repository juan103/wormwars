You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E3d's code and Amendment 1: please review before any GPU play

You are reviewing, read-only, the WormWars repository in the current directory, at aa6ca4a (branch `roadmap`).

**The bound design:** `docs/E3/E3d-DESIGN.md`, v2.2, bound at 65b77fb (D225), which you both said "bind" to.
**Amendment 1** is appended as §11 (D226). It changes the scripted wall-follower's policy, after the
qualification tests that the bound text requires failed the policy as bound.

**The code to review** (`git diff 65b77fb aa6ca4a`):
- `wormwars/e3/islands.py`: the carved island construction (§2), with `tests/test_e3d_islands.py`;
- `wormwars/config.py` and `wormwars/e3/maze_world.py`: the `maze_family` switch, with
  `tests/test_e3d_world.py`;
- `wormwars/e3/e3d_controls.py`: the wall-follower (§3 and Amendment 1), with
  `tests/test_e3d_wall_follower.py`;
- `wormwars/e3/e3d_records.py`: the records (§6), with `tests/test_e3d_records.py`;
- `wormwars/e3/e3d_gate.py`: the gate, the choice of k_r, the predictions and the bootstrap (§4-5), with
  `tests/test_e3d_gate.py`;
- `scripts/e3d.py`: the stages, with `tests/test_e3d_runner.py`;
- `scripts/e3d_equivalence.py` and `experiments/E3-ab-organism/E3d/equivalence-reference-cpu.json`: the
  full-rollout rule-7 leg. The CPU leg is identical to 40bd50f tick by tick; the GPU reference is not yet made;
- the sizing script, unchanged in purpose: `scripts/e3d_sizing.py`.

**Please answer, citing files and lines:**
1. **Amendment 1:** is it a legitimate amendment, made before any play and for the stated reason? Is the
   amended policy a fair "strongest hugger"? Are the two qualification thresholds set after the first run
   acceptable as disclosed?
2. **Does the code implement the bound design (with Amendment 1)?** Look for any departure that would change a
   reading:
   - the construction and its keying;
   - the blind family and who plays where;
   - the B_max members, one per champion;
   - the gate's criteria and precondition;
   - the choice of k_r;
   - the predictions;
   - the bootstrap;
   - the records' definitions, especially contact and the at-visit classes;
   - the projection and its reductions;
   - the binding guard.
3. **Are the tests adequate?** Name any that could not fail, and any behaviour the design requires that no test
   covers.
4. **Rule 7 and rule 6:** is the equivalence leg sound? What else must hold before the GPU plays?
5. **Your verdict:**
   - "run" (the GPU legs and plays may start after the owner is told);
   - or "fix first", with a numbered list limited to what would make a result wrong or uninterpretable.
