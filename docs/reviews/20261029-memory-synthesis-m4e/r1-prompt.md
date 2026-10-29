# The memory thread's synthesis, draft 4: M4e and M5's preparation added (round 1)

`docs/memory/SYNTHESIS.md` (draft 3, reviewed by you both on 2026-10-25, archived here as `draft3.md`) covered M1 to
M4d. Since then M4e ran (D367, D368), M5's pilot and power calculation were done (D369-D372), and on 2026-10-29 the
owner postponed M5 for its cost against its benefit (D373). The owner then agreed to Claude's suggestion: update this
synthesis with M4e and M5, then design M6's behaviour question.

What changed (`git diff` against `draft3.md`):
- Title and header; "In short" gains an M4e bullet and an M5 bullet, and "What it adds up to" is revised.
- The routine's table gains M4e and the M5 pilot; the compute total is now 112.43 CPU hours.
- New sections 5 (M4e) and 6 (M5 prepared, then postponed).
- "What holds" gains five rows and changes one; "A reading across the steps" gains an M4e paragraph.
- Limits (the unresolved genomes as a class), lessons (the second pass; a new lesson on weighing cost against benefit
  before a plan), "What comes next", "Who did what" and "Where the numbers come from".
- `scripts/memory_summary.py` now reads M4e's `readings.json`, M5's pilot `report.json` and the adopted power reading
  (`runs/memory-m5-power-welch/power.json`); `docs/memory/summary.json` is regenerated; `tests/test_memory_summary.py`
  gains a sabotage for the new parts (5 pass; the equality test was seen failing before the regeneration).

Sources: `docs/memory/M4E-RESULTS.md`, `M5-PILOT-RESULTS.md`, `M5-POWER-RESULTS.md`, DECISIONS.md D365-D373, and the
committed records named above.

Read-only. Please check:
1. Every new number and reading against its results file or `summary.json`, and every attribution against the
   results files and DECISIONS.md.
2. Overreach: does the new text (especially "What the block carries", "What it adds up to" and the M4e paragraph of
   "A reading across the steps") claim more than M4e's reading and its after-the-data descriptions support?
3. Whether the M5 section and the new lesson describe the postponement fairly.
4. Anything missing that a reader of `main` needs.

Verdict: publish / fix then publish / revise.
