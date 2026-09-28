You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Confirmation review in the WormWars repository (your working directory, branch `roadmap`, HEAD). You reviewed T1's results (D090) earlier; your answers are in `docs/reviews/20260928-120548-T1-results/`. D091 (`DECISIONS.md`) and `docs/foundations/T1.md` §7 respond to them.

Please check:
1. Is each of your points resolved, correctly? Name any that are not, with file:line.
2. The evidence: do the claims in T1.md §7, the new `docs/REPRODUCIBILITY.md` block, T0.md's dated correction and AGENTS.md rule 6 match the committed files exactly (`docs/foundations/T1_diagnostics.json`, `T1_equivalence_v2_*.json`)? Is anything still overclaimed or untraceable?
3. The code fixes: `wormwars/brain.py` (legacy layout), `wormwars/evo/genomes.py` (a supplied config keeps the file's padding setting), `wormwars/evo/rollout.py` (starting food), `wormwars/accounting.py` (child ledgers), `scripts/t1_equivalence.py` and its tests `tests/test_t1_equivalence_script.py`, `scripts/t1_diagnostics.py`, `tests/test_t1_padding.py`. Any defect?
4. The reference engine `ffeb541` (merged with strategy "ours" in `2f423dd`): is this an honest pre-change reference given the three support files it carries?
5. The proposed decisions in §7 (padding kept as a mitigation; the contract amendment; E1 guidance) and the closure-by-amendment text. Confirm or change.
6. Also new: a plain-words section "What the three signals measure, in plain words" in `experiments/03-generation0/README.md` (and a short version in the main `README.md`'s 03 section). Is every statement accurate against 03's PREREGISTRATION.md §4-§5, RESULTS.md and 03r's RESULTS.md?

Finish with one line: "T1: close by amendment", or "T1: not yet" (list must-fix items); and separately "Signals text: accurate" or "Signals text: fix" (list).
