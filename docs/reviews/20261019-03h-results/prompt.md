You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing, read-only, 03h's results page before it is published. The repository is on branch `roadmap`, at
HEAD a322cf9 (D340 in `DECISIONS.md`).

**Context:**
- 03h (`experiments/03h-history-use/`) stopped before its pre-registration, by the owner's choice (D339, D340).
- Its pilot ran under a bound registration (`PILOT.md`, D335-D336).
- After the pilot came an exploratory power analysis (D337), then an exploratory amplitude check (D338-D339).

**To review:**
- `experiments/03h-history-use/RESULTS.md`, the page;
- `summary.json`, built by `scripts/e03h_summary.py` from the committed records, with `tests/test_e03h_summary.py`;
- the rewritten `experiments/03h-history-use/README.md`;
- the new 19 October entry at the top of `ROADMAP.md`'s status section;
- the new 03h row and the updated "Next on the roadmap" line in `README.md`.

**Please check:**
1. **Every number and claim against the records:**
   - `pilot/*.json`;
   - `development-records/step0.json`, `step0b.json`, `b-power.json`, `amplitude-check.json` and the compute
     records;
   - `summary.json` and DECISIONS D321-D340.
   Name any that is wrong, untraceable, or stated more strongly than the record supports.
2. **The wording of the findings,** especially:
   - "random brains barely use the bit";
   - "B's rank test could not separate N2";
   - "even under the hypothesis's strongest plausible effect";
   - the history-and-fitness statements;
   - "Not shown".
   Is anything overclaimed, or misleading about N2, about A, or about the memory thread?
3. **Disclosure:**
   - that 03h is exploratory;
   - what was decided after seeing data, and by whom;
   - the departures from the registered rules (the amplitude check is outside PILOT.md's rule);
   - the corrections;
   - the reviews.
4. **Reproducibility:** can an outsider follow "Reproduce it"? Do the README and ROADMAP entries match the page?

Verdict first: "publish" or "revise". Then numbered findings, with file, line and severity. Do not edit files or run
anything.
