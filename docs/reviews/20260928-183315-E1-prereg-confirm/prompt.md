You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Confirmation review in the WormWars repository (your working directory, branch `roadmap`, HEAD). You reviewed E1's pre-registration v1 (answers in docs/reviews/20260928-181005-E1-prereg/). DECISIONS.md D095 lists the changes; see `git show HEAD` (and `git diff f83bd19 HEAD`).

Please check:
1. Is each of your must-fix points resolved correctly in experiments/E1-navigation/PREREGISTRATION.md v2, scripts/e1.py and the tests (tests/test_e1_script.py, tests/test_e1_task.py)? Name any that are not, with file:line.
2. Did the revision introduce new defects? In particular the guards (require_formal, start_marker, validate_freeze, require_same_code_as_pilot, check_cap and the CapReached path in cmd_gate), the cue rule in gate_rules, the leg endpoints in wormwars/world.py (_ev_start/_ev_end) and `secondary`, and the smoke isolation (use_smoke).
3. Is §7's disclosure now complete and accurate? Is starting every stage at index 1 000 of its range an adequate, non-data-driven remedy?
4. Anything that must change before the binding commit is pushed and the pilot runs.

Finish with one line: "E1 pre-registration: ready to bind" or "E1 pre-registration: revise" (list must-fix items).
