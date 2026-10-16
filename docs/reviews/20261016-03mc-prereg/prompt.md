You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Review, read-only, of a pre-registration and its formal code in this repository (branch roadmap, the commit named in
DECISIONS.md D289).

You agreed design v2.2 of `experiments/03mc-p4-confirm/DESIGN.md` (D285-D288). Now, before anything fresh is drawn,
please review together:
- `experiments/03mc-p4-confirm/PREREGISTRATION.md` (draft 1): the binding rules; the design keeps the reasons;
- `scripts/p4mc.py`: the formal runner (audit, build, check, run, report; guards; resume; the empty-deletion stop);
- `wormwars/exp03/mc_report.py`: the report (every question, Holm, the wordings, the secondaries);
- `wormwars/exp03/mc.py`, `wormwars/exp03/twin.py`, `scripts/p4mc_equivalence.py`, the two new instances in
  `scripts/exp03.py`;
- the tests: `tests/test_p4mc.py`, `tests/test_exp03_mc.py`, `tests/test_exp03_twin.py`, `tests/test_p4mc_equivalence.py`.
D289 says what was done, including that the runner was written before its tests (with sabotage checks after) and a
weakness found in the append-only check. A CPU smoke run of every stage is in `runs/p4mc-smoke/` (its records under
`runs/p4mc-smoke/record/`; toy sizes, its own salt and seeds).

Please check:
1. Does the pre-registration fix every rule a reader needs (measures, tests, outcome wordings, completeness, the
   cap, stop rules), consistently with design v2.2? Anything ambiguous or missing?
2. Does the code do exactly what the pre-registration says? In particular: the plan and its order; the genome
   streams (salt, seeds, Q-B's batches, the paired permutations); deletions; validity and the floors; Q-A's change,
   Q-D's share, Q-C's reference response; Q-B's pooled bootstrap and tests; the controls; Holm with missing
   questions; the single-signal records (versus 03's `report.build`); the wordings.
3. The guards: binding through bound.json (and `code_commit`), append-only, code unchanged, formal environment,
   the freshness audit and content check, resume refusals, the cap, the pre-run check gate.
4. Anything that could let a fresh draw happen before binding, a formal input be touched by a smoke run, or a
   result be lost or overwritten.

Answer "bind" or "fix first", then numbered findings with file:line, evidence and a proposed fix. Keep to what you
verified; say what you could not check. Please run no GPU work and draw no fresh graph or genome (no `p4mc.py build`
without --smoke).
