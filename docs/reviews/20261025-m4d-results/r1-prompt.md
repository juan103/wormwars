# Review request: M4d's results, draft 1

You reviewed M4d's plan in four rounds (`docs/memory/M4D-PLAN.md`, draft 5; D363; your answers are in
`docs/reviews/20261024-m4d-plan/`). The run has finished. Please review the results write-up,
`docs/memory/M4D-RESULTS.md` (draft 1), against the plan and the committed outputs. Read-only.

**Outputs** (all in `runs/memory-m4d/`): `readings.json` (from `scripts/memory_m4/m4d_read.py`; console
`read_log.txt`), the 70 panel records `arms/<host>__<arm>.json`, `companion.json`, `hosts.json`, `coverage.json`
(written before any arm ran), `blocks-summary.json`, `tables.txt` (from the new after-the-data script
`scripts/memory_m4/m4d_tables.py`), `m4d-attempt.json`, `m4d-compute-record.json`, `m4d_log.txt`.
`blocks.json` stays local: it holds N2's C3 chemical weights edge by edge (T's and P's entries), which rule 1 forbids
committing; the summary carries its sha256, and `.gitignore` now names it.

**The reading** is "Unresolved (the unresolved genomes decide it)": counted genomes alone give the plan's second
reading (D_TI +0.0059 [0.0048, 0.0069]; D_TR +0.0012 [−0.0009, 0.0032]); the envelope over the unresolved genomes
gives D_TR up to 0.0087. A check added after the data says no assignment can make the reading positive (the bootstrap
lower bound at the all-for-T end is 0.00400, just above m, but the Student-t lower bound there is 0.0037).

Please check, and say what must change before this is committed and pushed:
1. **The reading:** is it the plan's reading, computed as the plan fixed it? Is the after-the-data "no assignment
   makes it positive" argument right (monotone bootstrap; any non-end assignment is at or below the end with one host
   one genome lower)?
2. **Every number** in the write-up against the files. Overclaims, missing caveats, wording that goes beyond the data.
3. **The interpretations marked after the data** (the ladder's shares, Rr below R, P close to T, the companion's
   "95% lose the switch", the write measures). Are any of them misleading?
4. **The blocks.json decision** (kept local, summary committed). Is the summary enough for a reader to check, and is
   anything else committed that carries connectome structure (`hosts.json` has the hosts' in- and out-degrees within
   the block; the hosts are seeded null graphs)?
5. **The next step.** The plan's rule for "Unresolved": reported, no extension without a new plan, the next step
   decided with both reviewers and, if it changes direction, the owner. The write-up lists two options without taking
   one: (a) a planned resolution of the 86 unresolved genomes in T and R (it can only move the reading between the
   second reading and "Unresolved"); (b) accept the screen and let the owner decide the thread's direction (M5 as a
   transplant test, density and degrees, or the M1–M4 write-up). Which do you recommend, and why? Is there a better
   option?

Rank your findings, and give a verdict: agree / fix then publish / do not publish.
