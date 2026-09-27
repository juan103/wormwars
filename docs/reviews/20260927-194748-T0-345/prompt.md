You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Review: T0 items 3-5 (CPU parts), and the jitter test owed from item 1

T0 plan v2.1 (`docs/foundations/T0.md`) is agreed, and items 1-2 are agreed. The CPU parts of
items 3-5 are now implemented at b966a93 (branch `roadmap`, read-only). `DECISIONS.md` D073
records them.

**Files:**
- `tests/test_t0_items345.py`;
- `wormwars/config.py` (`check_ledger_every_tick`);
- `wormwars/world.py` (`energy_ledger_rel_error`, the per-tick tracking at the end of `tick`);
- `wormwars/evo/rollout.py` (`ledger_rel_error`, `_nanmax`);
- `wormwars/evo/evolve.py` (the island validation at the top of `evolve`, and the
  `_breed_islands` docstring).

**Deferred to the GPU** (03r is using it): replay mode, the default-CUDA tolerance, historical
replay, CUDA ledger identity, and the single-island regression against a published log.

**Please check:**
- Do these meet sections 3 (CPU), 4 and 5 of the plan?
- Is the ledger check correct? Check the relative normalisation, the per-tick maximum, NaN
  propagation, and that it is opt-in with its cost.
- Are the island validation rules right?
- Is the end-to-end jitter test adequate? D073 also records a pre-existing layout dependence in
  wey placement for mixed headcounts. Is that diagnosis right?
- Is anything missing before the T0 gate, apart from the GPU items?

Findings ranked **must fix**, **should fix**, **minor**. End with: "items 3-5 CPU: accept" or
"not yet".
