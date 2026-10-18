You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

## Question

You are reviewing research code in the repository you can read (read-only): 03a's implementation and its pilot-dev
plan, at commit a4956e5 on branch `roadmap` (DECISIONS.md D308).

Context:
- The design is `experiments/03a-self-consistency/DESIGN.md` v7.1, agreed by both of you as the basis of the
  pre-registration after four rounds (D302-D307; reviews archived under `docs/reviews/2026101*-03a-design-*`). Treat
  the design as settled; this round is about whether the code implements it correctly and whether pilot-dev, as
  planned, will produce what the pre-registration needs.
- The code: `wormwars/e03a/` (reinsert.py, search.py, null.py, stats.py, panel.py, structural.py, probe.py, arms.py),
  `scripts/e03a.py` (pilot-dev's stages and family 2's validation), one change to `wormwars/accounting.py` (a
  `search` category). Tests: `tests/test_e03a_*.py`.
- The plan: `experiments/03a-self-consistency/PILOT-DEV.md`. §4 lists the implementation choices the design left
  open, among them one departure from the design's text (NIP brains pinned on the intact mask rather than evolved on
  a separate mask); §5 maps each of DESIGN.md §8's implementation tests to its test, and states that the tests were
  written after the code and then checked with planted bugs (`development-records/mutation_check.py`).
- Records: `experiments/03a-self-consistency/family2-validation.json` (family 2's simulated-null validation, 20 000
  datasets per scenario) and `development-records/mutation-check.txt`.
- Nothing has run on the GPU since the exploratory checks. Pilot-dev (at most 6 GPU-hours) runs only after this
  review and the owner's word.

Please:
1. Check that the code implements DESIGN.md v7.1 as written, especially: the union mask and the copied background;
   initialisation and proposals that cannot see X's true partners; replica exchange (acceptance, swaps, the result);
   the strata (kinds, degree tertiles, tie and merge rules) and the within-strata permutation null; the recovery
   statistic and p; family 2's exact test, Holm, the floor and withholding; the three-state comparisons; the panel
   rule; the structural comparators; the replay probe's timing (first affected action at 2L + 1) and its calibrators.
   Report bugs with file and line.
2. Say whether each test checks the property it claims, and whether any could pass while the property fails.
3. Review PILOT-DEV.md: the choices in §4 (especially NIP pinning), the choice of pilot-dev's two targets, the tuning
   rounds and their rules, the measurements in §3, and the budget. Will pilot-dev give the pre-registration what
   DESIGN.md §8 says it must (the frozen settings, δ_eval and δ_search, throughputs, diagnostic thresholds)?
4. The concern stated in D308: the search may find partners too slowly with 301 candidates per type. Is 100
   generations plausible, and is pilot-dev's measurement of it adequate?
5. Anything else that would waste pilot-dev's GPU budget or make its output misleading.

Answer with a verdict first: "ready for pilot-dev" (possibly with small fixes), or "revise" (list what must change).
Then numbered findings with file and line where possible, and severity. Do not edit files or run anything.
