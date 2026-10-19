You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing, read-only, a small exploratory script for 03h in this repository (branch `roadmap`, HEAD 26c580f,
plus two uncommitted files named below). Please check the claims against the files.

**Background.**
- D337 (`DECISIONS.md`; review archived in `docs/reviews/20261019-03h-bpower/`) found that B's registered rank test
  has almost no power, given the pilot (`experiments/03h-history-use/pilot/pilot.json`).
- Fable recommended a disclosed exploratory check at amplitudes 0.5 and 1.0 on the three pilot graphs. Its guide: if
  the decile shift stays under about one between-graph SD, close the ASK-bit relief and stop 03h; if it nears two, a
  redesign round is justified. Astra recommended redesigning B's statistic instead.
- The owner chose the amplitude check first, at about 0.2 GPU-hours, after this script is reviewed. The owner then
  decides between stopping and redesigning.

**The files to review** (uncommitted):
- `scripts/e03h_amplitude.py`: the check. Its docstring states what runs, the readings, the guide (fixed before the
  run), the guards and the cap. It reuses the pilot driver's `scripts/e03h.py` helpers, imported as a module.
- `tests/test_e03h_amplitude.py`: 6 tests, at smoke size on the CPU. They pass. With a sabotaged script, the cap test
  and the refusal test were each seen failing.

**Points to check:**
1. **Correctness.** Does the script measure what its docstring says, against the same graphs, genomes, gains, banks,
   sham rates and engine as the pilot, with every hash checked? In particular:
   - the amplitude's effect on the interface (`wormwars/e03h/__init__.py` `interface_03h`);
   - the claim that level needs no rerun;
   - the per-condition decile selection;
   - the reuse of `PL.b_readings` for the interval and the between-graph SD.
2. **Is the guide well posed?** The ratio is the mean decile shift over its between-graph SD, from three graphs, with
   the thresholds 1 and 2. Should the guide also use the all-genome selection-bank shift, or anything else, fixed
   before the run? Reusing the pilot's banks and the sham's keyed stream: is that acceptable for an exploratory check?
3. **The guards and the cap:**
   - the pushed tree;
   - the engine unchanged since the pilot's bound commit;
   - the shared 1.0-hour pre-registration cap, with 0.209 spent, and this check's own 0.3-hour budget;
   - the run-once rule, with failed attempts kept.
4. **Anything that would mislead the owner's decision,** with file, line and severity.

Verdict first: "run" or "revise". Then numbered findings, short. Do not edit files or run anything.
