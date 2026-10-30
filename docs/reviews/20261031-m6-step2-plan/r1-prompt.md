# M6 step 2: the plan and code (round 1, the only planned round)

The design note (`docs/memory/M6-STEP2-DESIGN.md`) was reviewed by you both (`docs/reviews/20261030-m6-step2-design/`,
both "proceed to a plan, with fixes"). The plan is `docs/memory/M6-STEP2-PLAN.md` (draft 1, also `draft1.md` here).
The code: `scripts/memory_m6/step2.py`, `step2_read.py`, `sabotage_step2.py`; tests `tests/test_memory_m6_step2.py`
(10 pass; 15 of 15 sabotages caught, `sabotage-step2.txt` here). It reuses M6-0's genome helpers
(`scripts/memory_m6/m6_0.py`), 02b's setup and `rollout`, and M2's probe (`scripts/memory_m2/pilot.py`).

Read-only; proportionate (about 3.7 CPU hours, capped at 5):
1. Were your design fixes taken correctly? Anything wrong, missing or post hoc in the arms, the exact rescaling
   (substeps set on the genome's own config, since `Brain` reads `genome.cfg.substeps`), the batch composition, the
   checks, the measures, the averaging or the fixed wordings?
2. Does the code do what the plan says (in particular `score_run`, `probe_one`, the reader's control comparison,
   the T1 minus T0 pairing and the validation)?
3. Anything to cut.
4. Verdict: agree, agree with fixes (list), or revise.
