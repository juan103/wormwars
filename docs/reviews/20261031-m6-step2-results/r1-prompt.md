# M6 step 2: the results (round 1)

M6 step 2 has run under its plan (`docs/memory/M6-STEP2-PLAN.md`, draft 2, committed and pushed in D382, 0d841d1,
before the run). The results draft is `docs/memory/M6-STEP2-RESULTS.md` (draft 1, also at
`docs/reviews/20261031-m6-step2-results/draft1.md`). The records are in `runs/memory-m6-step2/`: genomes.json,
scores.json, probe.json, reading.json and step2-compute-record.json. They were written by
`scripts/memory_m6/step2.py` and `scripts/memory_m6/step2_read.py`. The run's log is `runs/step2-run-log.txt` and the
reader's is `runs/step2-read-log.txt`. A few descriptive figures the plan did not fix come from
`docs/reviews/20261031-m6-step2-results/check_step2.py` (output `check_step2.txt`).

Read-only, one round planned; please keep it proportionate.
1. **Numbers:** does every number in the draft match the records? Re-derive what you can, especially the tables of
   relative changes, the controls' table, T0's matched difference and the validation table.
2. **The readings:** did the reader apply the plan's fixed checks and wordings correctly (the primary, the
   sensitivity, both control wordings, the gate)? The reader's k = 2 list is named `not_below_1` and so lists the
   champions that rose; the draft notes this. Is that handled honestly?
3. **Overclaiming:** the draft's interpretation, marked "after the data", says the champions are tuned to their time
   scale (both directions cost, slowing more), that nothing singles out T1's single-nose task (T0 matches within about
   3 points), that the controls lose less but have less to lose, and that most of the cost goes with the sensory and
   motor neurons' speed (interior arm). Is each fair? Is the warm-up hazard of the slowing arms stated clearly enough?
   Is the association with a, which tracks the intact score, handled correctly?
4. **The roadmap step:** the draft follows the owner's order to stop the thread and fold steps 1, 2 and M6-3 into
   SYNTHESIS.md. Is that right, and is there anything the synthesis must not say?
5. Your verdict: agree, fix then publish (list the fixes), or revise.
