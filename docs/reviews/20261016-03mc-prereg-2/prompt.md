You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Confirmation pass, read-only, on a pre-registration and its formal code in this repository (branch roadmap, the commit
DECISIONS.md D290 describes; compare with c0f1020).

You reviewed draft 1 of `experiments/03mc-p4-confirm/PREREGISTRATION.md` and its code at c0f1020 (run 20261016-023227)
and answered "fix first". D290 lists each finding and the fix. The diff is `git diff c0f1020 HEAD`. The main changes:
- `scripts/p4mc.py`: guards (prereg chain, named code commit, pushed and pinned build, committed stage inputs), the
  build's token for `scripts/exp03.py` (`instance_command_allowed`), `require_build`/`require_check` attestations,
  the repeat check (`repeat_check`, `prerun-repeat.json`), resume refusals (terminal stop, full plan, settings, array
  hashes), the run lock, the guarded and non-overwriting report;
- `wormwars/exp03/mc_report.py`: Q-A's computed lead sentence, counts, N2 intervals, full single-signal records,
  wordings including reversal, descriptives, floors, the transformed kept-share interval;
- `wormwars/registration.py`: `require_pushed`, factored out of `require_formal`;
- `scripts/p4mc_equivalence.py`: `record_path`;
- `wormwars/exp03/mc.py`: the zero-numerator case;
- tests: `tests/test_p4mc.py`, `tests/test_registration.py`, `tests/test_p4mc_equivalence.py`, `tests/test_exp03_mc.py`;
- the pre-registration's draft 2 text, and a dated note in DESIGN.md §7.
A fresh CPU smoke run of every stage, with a resume and two reports, is in `runs/p4mc-smoke/` (toy sizes, its own
salt and seeds).

Please check:
1. Is each of your findings fixed, correctly and without a new error?
2. Does the code still do exactly what draft 2 says?
3. Anything that still blocks binding.

Answer "bind" or "fix first", then numbered findings with file:line, evidence and a proposed fix. Keep to what you
verified; say what you could not check. Please run no GPU work and draw no fresh graph or genome (no `p4mc.py build`
without --smoke).
