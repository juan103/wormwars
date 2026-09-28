You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Review request: 04a's pre-registration, draft v2 (commit 68f8aa3)

You reviewed draft v1 (`b38c7cc`); your reviews are in `docs/reviews/20260928-213057-04a-prereg/`.
Both said "revise". Draft v2 is `experiments/04a-navigation-primitive/PREREGISTRATION.md`; its §11
lists every change against your must-fixes and suggestions, and `DECISIONS.md` D104 summarises them.
You may read any file; you cannot run anything.

Please check:
1. **Is each of your must-fixes actually fixed in the code,** not only in the text? Key places:
   `scripts/e04a.py` (`use_smoke`, `cmd_project`, `require_projection`, `require_earlier`,
   `check_genomes`, `archive_attempt`, `run_rules`, `cmd_evaluate`/`extras`), `wormwars/e04a/evolve.py`,
   and the tests `tests/test_e04a_commands.py`, `tests/test_e04a_evolve.py`, the end of
   `tests/test_e1_task.py`.
2. **The development records** in `experiments/04a-navigation-primitive/development-records/`: the
   reconstruction of the 24 exposed training ids, the engine-equivalence results, and the pilot.
   Is the disclosure in §9 complete and fair? Is moving the training range the right remedy?
3. **The pilot's plateau (§9, §11 "Open for review v2").** In 200 generations on smoke ids, the best
   genome's validation mean went from about 0.2 to about 1.7 by generation 25 and stayed about
   1.0-2.1 to generation 199. Rule 1 needs 80% of episodes with at least 2 targets. Should the
   registration keep 1 000 generations with 02's optimizer (accepting a likely "some runs passed" or
   "not passed", which E2's optimizer screen then addresses), or change something before binding? If
   a change, what exactly, and does it stay within the cap?
4. **Any new problem** introduced by v2: the new rule 4 (real minus the champion's own constant
   probe, lower bound above 0.5), the rerun rule, the projection formula, local-only genome files.

End with one line: **"04a pre-registration: ready to bind"** or **"04a pre-registration: revise"**,
must-fixes separate from suggestions, and say what you checked in the code.
