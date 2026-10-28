# M5's power calculation, the script and its results: round 1

The design is `docs/memory/M5-POWER-DESIGN.md` (draft 4; its rounds in `docs/reviews/20261028-m5-power-sim/`). Fable
asked that this round check that rounds 2 and 3 went in; Astra said draft 4's amendment was enough before coding.

To review:
- the script: `scripts/memory_m5/m5_power.py` (the model, the calibration, the vectorised reading, the stages),
  `scripts/memory_m5/m5_reading.py` (the reading M5 will use), `scripts/memory_m5/m5_power_timing.py`;
- the tests and sabotages: `tests/test_memory_m5_power.py` (37 pass), `scripts/memory_m5/sabotage_m5_power.py`
  (17 of 17 fail by assertion, `runs/m5-power-sabotage.txt`);
- the outputs: `runs/memory-m5-power/power.json` (as designed), `runs/memory-m5-power-welch/power.json` (the proposal
  in section 3 of the note), their logs, and `power-sampled-calibration.json` (the first run, with the calibration
  bug);
- the note: `docs/memory/M5-POWER-RESULTS.md` (draft 1).

Read-only; check the numbers you rely on against the JSON files, and the code against the design.

What I most need from you:
1. **Does the script implement draft 4?** In particular the model and its calibration (section 2), the six-reading
   success event, the families and the confirmation rule (section 4), and rule C (section 5). Name any departure.
2. **The false "raises" gate fails as written** (pooled raw 2.56%, the t's one-sided skew). Which remedy: (a) the
   Welch t in the balanced hull (the proposal, run in full), (b) a wider tolerance, (c) raw "raises" reported only
   as qualified, (d) something else? This choice also decides A against C under the 20% rule (19.1% as written, 24.7%
   with Welch).
3. **The unresolved-share flag** fires in about 88% of runs with nothing wrong. Drop it, redefine it (for example
   against the pilot's arm difference), or keep it descriptive?
4. **The latent-switch hazard:** with 0.002 of Rr's genomes latent switches classified unresolved, M5 reads an
   unqualified "raises" in 79% of runs. The envelope crosses zero in every run, so the agreed wording already says
   the underlying contrast is unidentified. Is that enough, or should the design change?
5. **The note's claims** against the files: anything overstated or wrong?
6. **What goes to the owner:** A, B and C as in section 5 of the note, or different?

Rank your points, and give a verdict: agree (to the owner after the stated fixes) / revise.
