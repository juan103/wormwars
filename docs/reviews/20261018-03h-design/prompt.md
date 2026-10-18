You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a draft design in the repository you can read (read-only): **03h design v1**,
`experiments/03h-history-use/DESIGN.md`, at commit de22cc4 on branch `roadmap` (DECISIONS.md D321). It was written
from your scoping-round advice (`docs/reviews/20261018-memory-thread-scope/`). Nothing is coded or run.

## Please

1. Say whether the design tests what it claims, in question A (the within-graph history-to-fitness link, level
   against relief) and question B (N2's generation-0 upper tail, level against relief, against SH and SH-route).
   Name any confound, leak or statistical error, with section and severity.
2. Answer §8's open questions:
   - the receiving neurons for `food_fell` (the proposal is ASKL/ASKR, silent in Task N);
   - SH-route or SH-mirror, and the graph counts;
   - A's statistic and its smallest effect of interest;
   - B's statistic;
   - whether Astra's frozen-champion check belongs alongside A, after it, or not at all;
   - the cap.
3. Check the facts the design cites, against the files (§1, §2, §6).
4. Name anything that must be decided before a pre-registration can be written, that the design leaves open.

Answer with a verdict first: "ready for the pre-registration" (possibly with small fixes) or "revise". Then give
numbered findings. Do not edit files or run anything.
