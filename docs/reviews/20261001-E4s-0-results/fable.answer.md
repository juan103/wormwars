## 1. Verdict: **fix** (text changes; no rerun needed)

The stage records support the main numbers. The problems are in the framing: three things are under-reported (the carrier's turn bias, the bimodal robustness, the champions with no valley), one sentence overreaches the plan, and many summary numbers have no committed generator.

**What I re-derived and found correct:**
- Sweep: classes 24 / 0 / 23 / 0 / 0; 19 of 24 flagged; k* = 32 for 21 and 16 for 2; 42 harmed; 41 / 39 / 35 at k = 4 / 8 / 2; all 47 improve at 32 and 64; k0 range 0.79–2.96; k = 256 range 7.59–8.48.
- Ladder: 5.177, lower bound 5.099; re-score 5.19 against 4.51–4.80; dynamics 0.335–0.356 and −0.670 to −0.712, all settled at t90 = 3; `on_bounds`; the module sha.
- Populations: 16 / 0 / 0; backgrounds 41 / 107 / 364; 04a run 2 at 0.886, 0.98, −0.28.
- Robustness: 0.921 / 0.776 / 0.0; parent 5.234.
- Compute: 814.5 s = 0.226 h; projection 0.297 h.

**Not re-derived (no tool to compute them):** the sweep's median-score table, the attenuation medians, and the populations' medians (2.06, 1.09–3.30, 53%, −0.06, 0.25, 0.10).

## 2. Claims the records do not support, or that overreach

1. **README: "small k adds at most +0.08 targets per episode (one champion +0.19)".** This is wrong as written. Those figures are the gain at the *first improving k*, not the maximum over small k. In `sweep.json` at k = 1, e2 es run00 gains +0.27 and e2 extension run04 gains +0.21; a further dozen or so champions gain +0.11 to +0.15 at k = 0.25–1.
   - Correction: "at the first improving k, +0.02 to +0.08 (one +0.19); no champion gains more than +0.27 at k ≤ 1".
   - RESULTS's own wording is right, except "the 24 champions gain …, and one gains" should read "23 …, and one".

2. **RESULTS: "the path … crosses a valley" (unqualified), and the headline "A valley".** Five champions are never harmed by the rule: 04a run12, e2 es run00, e2 extension run00, e2 extension run04, e2 ga run02.
   - Three rise essentially monotonically. e2 es run00: +0.27, +0.42, +0.77, +1.36, +2.62, +4.52 at k = 1 to 32. e2 extension run04: +0.21 up to +3.72. e2 ga run02: +0.19 up to +4.60.
   - These champions sit on the plateau with no valley on this path, which cuts against "consistent with the plateau being hard to leave by small steps" as a general reading.
   - Correction: say "for 42 of 47", and name the exceptions.

3. **RESULTS: "The harm is mostly at k = 4 (41), 8 (39) and 2 (35)".** This is an artefact of the adjacency rule. k = 16 can never be "harmed" for a champion that improves at 32, and all 47 do.
   - Pointwise at k = 16, 40 of 47 have their upper bound below 0, and 7 have their lower bound above 0.
   - e2 extension run00 is pointwise harmed at 16 (−0.57, upper bound −0.44) but counted "never harmed".
   - Correction: add the pointwise k = 16 count, labelled descriptive. The "In short" and README phrase "k = 2–16" then has a record behind it.

4. **RESULTS §3: "L1 qualified", with "carrier … turn command 0.2" listed without comment.** The constant turn bias carries a large share of the score. In `ladder.json` `tune_means`, the same module at c = 0 / 0.1 / 0.2 scores 3.86 / 4.74 / 5.27 (indices 201–203).
   - The 5.0 line is cleared only with a carrier bias that is not part of the graft and will not exist on random N2. The c = 0 candidate was never among the top five, so it has no re-score or qualification run.
   - The plan allowed c in the grid, so this is in-plan, but it must be stated beside the 5.18.
   - Also state that the winner sits on the grid corner in every dimension except bias (w_n, w_o, forward and turn at their maxima, τ at its minimum). It is a bound-limited candidate, not an optimum.

5. **README: "It survives mutation at 0.25×"; RESULTS: "the median mutant keeps 78%".** The distribution in `robustness.json` `child_means` is bimodal, and the median hides it. By my hand count:
   - at 0.25×, about 122 of 256 children (48%) score below 0.7, nearly all exactly 0, and the rest score 3.8–5.4;
   - at 0.125×, about 64 of 256 (25%) are destroyed.
   - "The fallback did not trigger" is true, but on a 52 / 48 split. A few more dead children and the median would be 0.
   - Correction: report the destroyed fraction at each scale, and replace "survives" with "about half of the mutants keep ≥ 73% and about half lose everything".

6. **RESULTS §3: the clamp "makes the robustness below look better than it would at an interior point".** This is asserted, not measured. A quarter of the children die at 0.125×, where the weight sigma is 0.01. That looks like a cliff, not gradual gain loss.
   - My guess is that a bias or weight asymmetry, amplified by a gain of about 36, becomes a turn offset. That would fit item 4's sensitivity to c, but I have not verified it.
   - Correction: label the clamp sentence as a hypothesis, and say that the cause of the lethal mutations is not identified.

7. **RESULTS "What E4s-1 takes": "the valley, which predicts that free mutation at 02's scale will not keep a strong gain (U)".** This overreaches, and it contradicts §1's own caveat and the plan ("What mutations would do: the sweep inserts a policy change from outside"). The valley was also measured on evolved champions, not on grafted random N2.
   - What supports U is §4: the median child keeps 0% at 1×.
   - Correction: cite the robustness result, and drop "the valley predicts".

8. **RESULTS §2 and "In short" 2: "shrinks at every stage".** By the table, RIA to the turn motor neurons is flat at two of three levels (0.07 → 0.07), and the turn command (0.09–0.12) is higher than the turn neurons.
   - Correction: "falls from the sensory neurons to RIA, then stays flat".

9. **RESULTS: "Their turn command answers several times more to the common level than to the difference".** Part of that ratio is built into the probe. The script sets L = m + d/2 and R = m − d/2 (`scripts/e4s0.py:537`), so each sensor receives ½ per unit of d and 1 per unit of m.
   - A ratio of 2 at the sensors is by construction (D144 already noted the ±½). The table's sensory ratio is about 3.7.
   - K_C also falls stage by stage (0.82 → 0.40 at m = 0.02), so both gains attenuate. The fairer statement is that the K_D / K_C ratio falls from about 0.27 to about 0.15.

10. **RESULTS: "E1's scripted stereo steerer scores 8.51 at k = 256".** Two conditions are omitted: that figure is with turn bias 0.2, and on E1's tuning worlds (`docs/E4s/DESIGN.md:83`). Say so.
    - The same table gives k = 32 → 5.63, and 4.23 at zero bias. That is the more informative reference for L1, whose gain is about 35 and which scores 5.18 with c = 0.2.

11. **RESULTS: "the graft does not work on this background" (04a run 2).** This is understated. The graft roughly thirds the score: 0.89 against 2.64, both on 04a run 2 (the sweep's k = 0 also gives 2.64, on other worlds).
    - There is no ungrafted run on the same 1 024 worlds, so "a strong right bias" cannot be attributed to the graft.
    - The same champion with an external k = 32 gains +3.46. A graft with gain about 35 is therefore not equivalent to the residual on an evolved background. Say that.

12. **Rule 5: several numbers have no committed generator.** The sweep medians, the attenuation group medians, the G0 bests' 2.06 (1.09–3.30), and the 53% / −0.06 / 0.25 / 0.10 figures are in no record field, and no `.py` reads these JSON files. Commit a small summary script or a `summary.json`.

13. **Rule 3: the five failed attempts are not mentioned.** `compute-record.json` shows sweep through robustness all failing at 706a3fa within 15 seconds. I assume this was the pushed-HEAD guard, but no record gives the reason. Add one line.

## 3. Implications for E4s-1 that the text misses

- **L1 is gain-capped by the genome's bounds.** Its gain of about 36 is the maximum for |w| ≤ 3, and it sits just above the champions' valley edge (16 bad, 32 good). Mutation of the module weights can only lower it.
  - The sweep and E1's steerer say 8.4–8.5 needs k of about 256. The route there is L4×P, which was never tested because the ladder stopped, or N2 paths.
  - E4s-1's score thresholds and its "retained" wording should assume a ceiling near 5, not 8.5.
- **The G0 bests start at plateau level.** Their median is 2.06, against the champions' 2.19. Evolution can gain fitness by the non-stereo route and let the module decay.
  - Score alone will not separate "retained" from "replaced". The D classification at intervals is needed, not only at the end.
  - Only about 8% of individual backgrounds "use" (41 of 512), so each population's G0 has roughly 2–3 users. Founder effects will be strong.
- **The turn offset is a first-order variable.** The carrier needs c = 0.2; random backgrounds have a median |turn| of 0.25 with arbitrary sign; 04a run 2 sits at −0.28 and fails. The "no added output" and random-graft arms do not control for this. Consider recording each background's turn offset at G0 as a covariate.
- **The module factor of 0.25× rests on a knife-edge median.** With about 48% lethal module mutations, selection will purge them (the elites protect), but the frozen-against-free comparison will mostly measure mutational load. Pre-state the destroyed-fraction measure, and consider 0.125× as a sensitivity arm.
- **C2 (04a run 2) starts 1.75 below the ungrafted champion.** "Retained" there first requires repair. Include the ungrafted champion on the same worlds as the reference.