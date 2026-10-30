# M6 step 1: do the switches' states outlast the input? (plan and code, round 1, the only planned round)

The owner ordered (D379): this quick check first (Fable's suggestion in M6-3's review), then a test of whether the
champions' fading history effect matters for foraging, then stop. The plan is `docs/memory/M6-OUTLAST-PLAN.md`
(draft 1, also `draft1.md` here). The code: `scripts/memory_m6/outlast.py`, `outlast_read.py`,
`sabotage_outlast.py`; tests `tests/test_memory_m6_outlast.py` (11 pass; 14 of 14 sabotages caught,
`runs/outlast-sabotage.txt`). It reuses M2's frozen classifier (`scripts/memory_m2/pilot.py`: `probe_states`,
`follow_from`, `full_classify` with `initial`), and the probe-input context from D376
(`scripts/memory_m1/common.py`: `probe_input`). The disclosed smoke run (4 genomes) found all 4 merging under both
changed inputs.

Read-only; the owner was told "CPU minutes", so keep it proportionate:
1. Will the answer be read honestly? Anything wrong, missing or post hoc in the genomes, the phases (A, B under F0
   or Z, C restored), the classification under a changed input (does `full_classify` with `initial` and the
   context classify correctly under B's input; anything in the classifier that assumes the probe's own ramp?), the
   root match, the outcomes or the readings?
2. Given the smoke result, is there a design issue (for example, should B's length or a partial reduction of the
   input be varied, or is "all merge" already informative enough), without turning a quick check into a study?
3. Anything to cut.
4. Verdict: agree, agree with fixes (list), or revise.
