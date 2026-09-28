You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing T1's results in the WormWars repository (your working directory, branch `roadmap`, HEAD commit). You reviewed T1's plan earlier (`docs/reviews/20260928-074601-T1/`); plan v2 adopted your changes (D086).

Read:
- `docs/foundations/T1.md` §6 "Results" (and §3, the equivalence contract declared in advance);
- `DECISIONS.md` D090;
- the evidence: `docs/foundations/T1_profile.json`, `T1_equivalence_reference.json`, `T1_equivalence_compare.json`, `T1_equivalence_published.json`;
- the code: `wormwars/brain.py` (`Brain.step`, the padding), `wormwars/config.py` (`pad_single_strain`, `from_bundle`), `wormwars/evo/genomes.py` (loaders), `wormwars/exp02/grid.py` (`task_config` pin), `wormwars/accounting.py` (`neural_padding`), `tests/test_t1_padding.py`, `scripts/t1_equivalence.py`, `scripts/t1_profile.py`;
- the updated `docs/REPRODUCIBILITY.md` and T0.md's follow-up note.

Summary of what happened: the switch-off path equals the pre-change engine in all 188 outputs, and 02's 388 stored hold-outs reproduce exactly. With the switch on, 8 of 74 single-strain outputs still differ from their batch. Two causes were diagnosed: `bmm` at 1 and 16 rows per strain depends on the strain count (2-16 strains differ from 32), and reductions over fewer than 16 worlds differ. The contract declared that a mismatch fails the change and is not reclassified, so D090 records the general claim as failed and states a narrower claim that held (single-strain score and energy equal their batch at 20 or more rows per strain). Two "multi-strain" failures were the test's misclassification of a single-strain remainder; a separate rerun showed them equal to the batch.

Please answer:
1. Is the handling honest and consistent with the contract declared in §3? Is anything reclassified that should not be, or overclaimed (for example the narrowed claim's scope, which rests on the shapes tested, or the raw `bmm` check behind the 8-row statement)?
2. Decision 1: adopt padding, on by default for new work, with the narrowed claim? Or change the default, the mechanism (for example padding in `rollout` too, or row padding), or drop it?
3. Decision 2: the contract amendment (composition = strains per chunk × rows per strain × worlds per chunk; equality across compositions claimed only as tested). Right, and stated precisely enough?
4. Decision 3: guidance for E1/04a (one wey per world): checkpoints with at least 20 rows per strain, or accept composition-specific results. Sound?
5. Decision 4: does T1's engineering close (T1.4: profile committed; padding passes its class E test; §2's decisions recorded)? Given that the class E test failed as declared, what exactly should the record say?
6. Any code or test defect in the padding implementation or the equivalence script.

Finish with one line: "T1: close", "T1: close with changes" (list them), or "T1: not yet" (list must-fix items).
