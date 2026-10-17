You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a research design in the repository you can read (read-only). Please review
`experiments/03a-self-consistency/DESIGN.md` (design v7, commit 9ded377 on branch `roadmap`).

Context:
- Round 1 (v4), round 2 (v5) and round 3 (v6) answers are archived in `docs/reviews/20261016-03a-design-v4/`,
  `docs/reviews/20261016-03a-design-v5/` and `docs/reviews/20261017-03a-design-v6/`. DECISIONS.md D303-D306 summarise them. DESIGN.md §12 lists every change made
  in response.
- Earlier: a slow-memory scripted check (D304; `experiments/03a-self-consistency/development-records/
  slow-memory-check.json` and `slow_memory_check.py`), and the owner's decision on the one point you disagreed on
  (D305): history use is measured on every brain and reported, not a gate; the roadmap's requirement is annotated
  (ROADMAP.md, section "03a: redesign after 03r"). Please treat that decision as settled; you may say whether the
  design now describes it and its consequences accurately.

Please:
1. Say whether each of your round-3 findings is resolved, partly resolved, or not, and why.
2. Check the new numbers (§2's table, §10's budget) against the committed records and say which you checked.
3. Find anything new that would make the proof of concept uninformative or misleading, especially in the
   bounded-history replay probe, family 2 as one pooled permutation test, the stratified null as now specified, the
   tier order, the pilot criteria, and the cut order.

Answer with a verdict first: "ready for the pre-registration" (possibly with small fixes), or "revise" (list what
must change). Then numbered findings with file and line where possible, and severity. Do not edit files or run GPU
work.
