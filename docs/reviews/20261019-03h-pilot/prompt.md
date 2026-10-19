You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing, read-only, the pilot's registration and code for 03h, at commit 4fae0d1 on branch `roadmap`
(DECISIONS.md D332).

**Context:**
- **The design:** `experiments/03h-history-use/DESIGN.md` v3.3. After step 0 (D329) and step 0b (D331), the owner made
  B the only registered claim, with A a pre-specified secondary (D330, §13).
- **The registration:** `experiments/03h-history-use/PILOT.md`, draft 2, to be bound before any gate or pilot stage
  runs.
- **The code:** `scripts/e03h.py`; `wormwars/e03h/gate.py`, `pilot.py`, `probes.py` and `__init__.py`
  (`interface_03h(amplitude)`); `wormwars/evo/rollout.py` (the `food_fell_counts` output).
- **The tests:** `tests/test_e03h_gate.py`, `test_e03h_pilot.py`, `test_e03h_probes.py`,
  `test_e03h_pilot_driver.py`, and `test_e03h_food_fell.py`'s rollout-count test.
- **GPU:** the owner's GPU word covers the gate and the pilot once PILOT.md is bound. So far only step 0, step 0b, the
  rule-7 checks and the CUDA smoke preflight have run on the GPU.

**Please:**
1. Say whether PILOT.md draft 2 is ready to bind. Look in particular at:
   - the gate's family construction and nesting, and its cost;
   - the amplitude rule keyed on the decile shift;
   - B's pilot readings;
   - the reported power;
   - the projection and its stop;
   - the seeds and ranges.
2. Say whether the code implements PILOT.md and design v3.3 §13. Name any bug that would mislead G1, S1, G2 or P, or
   the formal run's sizing, with file, line and severity.
3. Name any gap in the tests.
4. Say whether `rollout`'s new output changes anything for earlier experiments.

Answer with a verdict first: "bind and run" (possibly with small fixes) or "revise". Then give numbered findings. Do
not edit files or run anything.
