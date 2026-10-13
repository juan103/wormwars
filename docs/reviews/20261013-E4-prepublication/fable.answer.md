**Verdict: fix then publish.** D263 took every finding of my results review correctly; the revised pages trace to the records. I found one wrong number (one I introduced), one overclaim in E4-D's README, one loose citation, one report the design promised but the page omits, and leftover housekeeping. Every E4-D figure in the tables and bullets checks against the four JSON files.

## Errors

1. **RESULTS §3, line 127, "Cutting the comparator-origin links rescued little (0.40 and 0.01)."** From `calibration.json` `reading2`: at 0.25 the cut gives 4.9768 against intact 4.5838, a rescue of 0.39; at 1.0 it gives 2.0541 against 2.0662, a change of −0.01, a small loss, not a rescue. My review wrote "0.01"; the sign was my slip. Fix: "(0.39 at 0.25; −0.01 at 1.0, no rescue)".

2. **E4-D README line 6, "E4's main task could not show transfer either way."** The main task was not run. What the record holds is both reviewers' judgement that a null would be inconclusive (D257). Fix: "E4's main task was not run; both reviewers judged that its null would be inconclusive (D257, `../RESULTS.md` §5)".

3. **E4-D README line 77, "(σ about 0.02; `../calibration.json`)."** That file records cross-link factors, not a σ. The step is factor 0.25 × w σ 0.08 (`brain.py:277` multiplies the scale into the σ; `arms.py:55` sets the slots' scale to the factor), and 0.08 is in `pilot.json`. The number is right; the citation is not. Fix: "(cross-link factor 0.25 of w σ 0.08, `../pilot.json`; the ladder in `../calibration.json`)".

## Omissions

4. **The scouting block's nose readings are missing.** Design §2 says the scouting block "reports the scaled, occluded nose readings at the start … and their left–right differences" (Astra's point: a wide field does not guarantee a lateral reading). `scout.json` holds them, the README does not. At σ_D = 6 the median |L − R| of a candidate's scent at the start is 0.0005 (the sum's 0.0014), and 9.4% of trials start with a zero difference; at σ = 12 the medians are 0.025 and 0.045. Add one bullet under Scouting with these figures, and say the lateral cue at the start is near zero and develops as the wey moves.

5. **E4-D README line 33 states the outcome as if it were the rule.** "the smallest scent width at which the oracle reached 0.81 … and X0 entered on every trial" reads as if 0.81 were the threshold. Fix: "the smallest width meeting the rule (oracle ≥ 0.75 real-first over all trials, X0 entry rate ≥ 0.75): at σ = 3 the oracle made 0.66; at 6, 0.81, with X0 entering every trial".

6. **Calibration's entry counts.** The chosen w = 3 entered 61 of 64 on the calibration block; every other candidate entered 64 of 64 (`calibrate.json`). The selection is on the all-trials share, so the choice stands, but the page shows entries for evaluation only. Add "(w = 3 entered 61 of 64; every other candidate 64)" after the table.

7. **E4-D README line 23, "A's motor output is gated off throughout."** The latch is checked at every substep until the world's first entry (design v2.3; `e4d.py:114-116`), not to H_t. Fix: "gated off until the entry, checked at every substep".

## Housekeeping

8. **`experiments/E4-two-minds/calibration-partial.json` and `diagnostics-partial.json` are still untracked** (my item 17 last time). Commit or delete before publishing; the E4-D partials are tracked.

9. **Design v2.3's status line still says "Nothing has been played."** Add a dated line: "Played 2026-10-13: scouting (twice, D261), calibration, evaluation; passed (D262)."

10. **README "Reproduce it", line 70.** `guard()` refuses to run a stage whose record exists (`e4d.py:169`), so a reproducer must move the committed records aside first. Say so.

11. **Device.** E4-D's records carry no `device` field (`calibration.json` has one). "CPU only" rests on the design and D262. Fine for now; add the field in the evolutionary E4-D's runner.

## Verified, for the record

RESULTS: the children's and elites' ranges (2.52-2.77, 2.86-3.08, 5.50-5.91, 5.46-5.96), 2.90 and 3.22 across runs, 1.49-5.16, 6.3-6.7 and 6.2-6.9, the SD 4.31 (sample SD of `headroom.json` block A; my 4.2 was the population SD), the compute split (1 304 + 933 + 2 061 = 4 298 s; 4.20 and 25.80), the bias split and ratio, the ladders, the whole intervention table, 1.67 of 3.39, 1.74 of 5.90, the headroom figures, the corrections list, and that every D263 item matches its finding. E4-D: 32 of 32 qualifying, σ_D = 6 by the rule, X0 at exactly 0.5 of entries at every σ, both calibration rows to two places, the oracle 0.906, all seven evaluation rows and entry counts, the bound 0.78125, reversal 106 = 106, every integrity flag true, the test list, the review folders, `docs/E4/rule7/`, and that `scout-attempt1.json` matches `scout.json` on every readout, the medians and spot-checked per-trial readings (no full diff; I cannot run commands here).