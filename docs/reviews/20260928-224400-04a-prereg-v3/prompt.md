You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Review request: 04a's pre-registration, draft v3 (commit 082210e; the D105 text is in dff52b3)

You reviewed v1 (`b38c7cc`) and v2 (`68f8aa3`); your reviews are in
`docs/reviews/20260928-213057-04a-prereg/` and `docs/reviews/20260928-221414-04a-prereg-v2/`. Both
rounds said "revise". Draft v3 is `experiments/04a-navigation-primitive/PREREGISTRATION.md`; its §12
lists the changes against your v2 must-fixes and suggestions, and `DECISIONS.md` D105 summarises them.
You may read any file; you cannot run anything.

Please check, in the code and not only the text:
1. **Each v2 must-fix:** the formal seeds (1 105 000 onward) disjoint from the pilot's, projection's
   and smoke seeds; the effective-brain-configuration check in `check_genomes`; the rerun rule as
   implemented in `archive_attempt` and the three commands (kill with marker and no record, the
   projection after a stop or over its limit, archived local genomes, the recorded reason, the
   second-stop refusal); `AMENDMENTS.md`; the not-completed record written before any genome save;
   the decoy measure's error record; the qualified exposure wording and the preserved ledgers.
2. **The tests** for those paths in `tests/test_e04a_commands.py` and `tests/test_e04a_evolve.py`.
3. **Anything new that v3 breaks,** including the projection plan now derived from the evolution
   settings (`training_plan`, `projection_verdict`) and the §6 expectation paragraph.

Unrelated to 04a but in the same push, for information only (no verdict needed): D106, a CI finding
that 03's graph files are byte-identical only on Windows, fixed with a content-hash manifest.

End with one line: **"04a pre-registration: ready to bind"** or **"04a pre-registration: revise"**,
must-fixes separate from suggestions, and say what you checked in the code.
