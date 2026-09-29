You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Review request: 04a's results (commit 5312475, branch roadmap)

04a ran as registered (`experiments/04a-navigation-primitive/PREREGISTRATION.md`, v5, bound at
`e3d68be`; your five pre-registration reviews are in `docs/reviews/*04a*`). The outcome, in the fixed
wording, is "04a: passed". Please review `experiments/04a-navigation-primitive/RESULTS.md` and its
README against the committed records in the same folder: `evaluation.json` (verdict, rules, per-world
counts), `evaluation-extras.json`, `evaluation_events.npz`, `train-A.json`, `train-B.json`,
`projection.json`, `compute-record.json`, and the start markers. DECISIONS.md D110 summarises it.
You may read any file; you cannot run anything.

Questions:
1. **Did the run follow the registration?** Check the stage commits, the same-code and environment
   checks, the ids, the seeds, the compositions, the champion selection, the rules as applied
   (`scripts/e04a.py::run_rules`), and the outcome.
2. **Are the numbers in RESULTS.md right?** Recompute what you can from the JSON.
3. **Is the reading fair?** In particular: means of 2.1-2.3 passing an 80%-at-least-2 reliability
   rule because the counts are narrow; the claim that the champions steer by the cue (mirrored and
   constant probes, decoy capture); "slow navigators" (fraction of the oracle, equivalent k, path
   efficiency); the unshaped arm's 4 of 4 and "shaping was not needed"; the module for E3.
4. **Anything overclaimed, missing, or that should be a dated correction** before this goes to main
   (which needs the owner's go).

End with one line: **"04a results: ready"** or **"04a results: fix"**, must-fixes separate from
suggestions, and say what you checked.
