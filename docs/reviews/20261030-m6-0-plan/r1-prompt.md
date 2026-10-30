# M6 option 0: the plan (round 1, the only planned round)

The owner chose option 0 of `docs/memory/M6-OPTIONS.md` ("Sure, option 0"). The plan is `docs/memory/M6-0-PLAN.md`
(draft 1, also at `docs/reviews/20261030-m6-0-plan/draft1.md`). The throwaway spike it discloses is
`docs/reviews/20261030-m6-0-plan/spike.py` (output: all 16 T1-M0-N2 g00/g39 champions fading on 03mc's bank, about
0.75 s per genome). Context: `docs/memory/M6-OPTIONS.md` and its review (`docs/reviews/20261029-m6-options/`),
`experiments/02b-champion-analysis/` (analyse.py: `typical_input`, `history_one`, `drifted`; history.json;
RESULTS.md section 2), the probe and classifier (`scripts/memory_m1/common.py`, `scripts/memory_m2/pilot.py`,
`scripts/memory_m2/classify.py`), M4e's second pass (`scripts/memory_m4/m4e.py`), and `wormwars/exp02/grid.py`.
02's genomes are local (`runs/exp02-screening/*.npz`, `records.jsonl`).

Read-only. The owner was told about 1 to 5 CPU hours and one review round, so please keep it proportionate:
1. Will the answer be read honestly? Anything wrong, missing or post hoc in the genomes, the two banks, the
   consistency check against 02b, the classes, the persistence measure, the comparisons or the fixed readings.
2. The code change (a `probe_input(iface, bank)` context in common.py): is it the right shape, and what must its
   tests catch?
3. Anything that should be cut as not worth its cost.
4. Your verdict: agree, agree with fixes (list them), or revise.
