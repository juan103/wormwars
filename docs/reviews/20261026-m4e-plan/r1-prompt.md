# M4e plan and code, round 1

You agreed M4e's design in two rounds (`docs/reviews/20261025-dense-block-design/`). Please review, read-only, the plan
`docs/memory/M4E-PLAN.md` (draft 1) and its code before any formal arm runs:
- `scripts/memory_m4/m4e.py` (hosts, blocks, paired genomes via m4d, the first pass, the second pass, records,
  `verify_run`, `validate`);
- `scripts/memory_m4/m4e_read.py` (the two-field readings, the envelope, the dose model, the coverage simulation);
- the change to the frozen classifier's orchestration, `scripts/memory_m2/pilot.py` (`git diff HEAD --
  scripts/memory_m2/pilot.py`: two optional parameters, `follow_ticks` and `tail_from`);
- `tests/test_memory_m4e.py` (18 pass) and `scripts/memory_m4/sabotage_m4e.py` (20 of 20 fail as they must);
- `scripts/memory_m4/m4e_stage0.py` and `runs/memory-m4e/stage0.json` (stage 0, background only);
- `runs/memory-m4e/coverage.json` (the coverage simulation, run before any arm);
- the smoke logs `runs/m4e-smoke128-log.txt` and `runs/m4e-smoke128b-log.txt` (the second, after the faster rerun).

Choices made while writing, for you to check:
1. **The second pass's oscillation rerun starts from the tick-21,800 state** of the batched continuation rather than
   repeating ticks 2000 to 21,800 per genome (a test shows the recorded substeps are bitwise identical; on the smoke
   both ways gave identical classes and reasons for all second-pass genomes). Is that faithful to the rules you asked
   for (the same rules, windows shifted, the 20,000-tick float64 cap unchanged)?
2. **U_HX is out** by the plan's own rule after the smoke (about 54 projected hours with it, against the 40-hour
   limit). Its text stays, marked not run.
3. **Power:** the coverage simulation shows a screen for effects of about 0.004: "raises" in 56% to 82% of screens at a
   spread δ = 0.004, much less on a raised base or by ensemble. Is that acceptable for this exploratory screen, or should
   hosts be added (cost about 2.9 h per host on an unshared CPU)?
4. **K's reciprocal matching** targets W's count within 2 with further degree-preserving swaps; the fallback records
   the achieved count.
5. **The audit:** 8 pre-drawn ids per host, draw and arm (about 160 per arm, 1280 overall in 8 arms); any audited
   fading genome that becomes separate states drops the second pass from the reading.
6. **The dose model** fits the U arms only (U_LL, U_LH, U_HL, U_HH without U_HX: four points per host) and assesses W
   and K against the host's curve.

Please look for bugs in the code especially (wrong seeds, a block rule not enforced, the merged classes, the envelope at
95%, the dose model, validate/verify gaps), plan text that says more than the code does, and anything that would make a
reading wrong. Rank findings. Verdict: agree / revise.
