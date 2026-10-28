# M5's power calculation, the script and its results: round 2

Round 1 (`r1-prompt.md`, `r1-fable.md`, `r1-astra.md` in this folder) asked for revisions. Both pipelines were rerun
from scratch after the fixes. The note is now `docs/memory/M5-POWER-RESULTS.md` (draft 2; draft 1 is `draft1.md`
here, and draft 2 is archived as `draft2.md`).

To review:
- the fixes: `scripts/memory_m5/m5_power.py` (the joint Rr fit, the quadrature host component, `run_c`'s invalid
  hosts and stage-1 bound, the exclusion after an invalid host, the fixed costs, the new diagnostics, the new stage
  `c_sens`), and `tests/test_memory_m5_power.py` (45 pass; the 8 added in round 1 were each seen failing first);
- the outputs: `runs/memory-m5-power/power.json` (as written) and `runs/memory-m5-power-welch/power.json` (Welch),
  their logs (`power.log`, `power-c-sens.log`), and round 1's outputs beside them as `power-results-r1.json`;
- the sabotages: `runs/m5-power-sabotage.txt` (17 of 17).

Read-only. Check the numbers you rely on against the JSON files.

**What changed in the results.** After the fixes, A's cheapest allocation is 1 × 512 × 80 at 135 hosts under both
readings. C saves 23.0% (as written) and 22.1% (Welch), so the 20% rule recommends C under both. The round-1
disagreement (Fable: keep the reading, repair the gate, A at 130; Astra: Welch, keep the tolerances, C if it holds)
no longer decides A against C. It still decides B's count, C's policy (1 × 512 × 80 with H1 95 and H_max 145, or
1 × 512 × 40 with H1 110 and H_max 160), and whether the gate passes as designed. As written, 6 of 32 null cells
fail (A's fewest-host and both of B's selections). The pooled raw rate is 2.52%, and the note estimates that about
3 of 32 cells would fail from the per-cell rule's own noise.

What I most need from you:
1. **Are round 1's fixes in, and correct?** Name anything still missing or wrong, especially in `run_c` and the
   joint fit.
2. **The reading: can we agree now?** I propose the Welch t in the balanced hull (section 3 of the note), with M5's
   pre-registration stating the simulated false "raises" rate beside the nominal one. Fable, does your objection
   stand now that the A/C flip has gone? Astra, is anything in the as-written result a reason to reconsider?
3. **The unresolved share** as a descriptive measure with no flag; and Fable's continuation sample to 100,000 ticks
   as an item for M5's plan, not this calculation. Agreed?
4. **The note's claims** against the files: anything overstated or wrong, including the new section on what a
   cell's gate can detect.
5. **What goes to the owner** (section 5 of the note): the table, the identification limit, and anything else they
   must see before choosing.

Rank your points, and give a verdict: agree (to the owner after the stated fixes) / revise.
