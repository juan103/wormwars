# M6 option 0: the results (round 1)

M6 option 0 has run under its plan (`docs/memory/M6-0-PLAN.md`, draft 2, committed and pushed in D376, e469ad1,
before the run). The results draft is `docs/memory/M6-0-RESULTS.md` (draft 1, also at
`docs/reviews/20261030-m6-0-results/draft1.md`). The records are in `runs/memory-m6-0/`: genomes.json, banks.json,
first-own.json, first-03mc.json, second-own.json, second-03mc.json, reading.json and compute.json. They were written
by `scripts/memory_m6/m6_0.py` and `scripts/memory_m6/m6_0_read.py`. The run's log is `runs/m6-0-run-log.txt` and the
reader's is `runs/m6-0-read-log.txt`. `scripts/memory_summary.py` now reads reading.json into
`docs/memory/summary.json` (`M6-0`). The local npz state files need not be read.

Read-only, one round planned; please keep it proportionate.
1. **Numbers:** does every number in the draft match the records? Re-derive what you can, especially the
   "after the data" table (medians of a, d(t)/a, absolute d and the returns flag) and the list of non-fading
   genomes.
2. **The readings:** did the reader apply the plan's fixed readings and wording correctly? That covers the
   inconclusive branch, enrichment, the negative wording and persistence. And do the records support "shortened"?
3. **Overclaiming:** the draft's interpretation, marked "after the data", says selection made the effect larger
   rather than longer-lived. It is a transient of a few tens of ticks, not a second stable state. τ_stay is
   relative to a, and the champions' a is about six times drift's. Is the interpretation fair, and is that caveat
   stated clearly enough? Anything else that says more than the data shows?
4. **The roadmap step:** the draft follows the plan's branch to options 3 or 4. Is that right?
5. Your verdict: agree, fix then publish (list the fixes), or revise.
