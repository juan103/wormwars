**Verdict: fix then publish.** The records support the story and almost every number. Four numbers are mis-rounded, three figures are not traceable to any committed file, one mechanistic sentence overclaims against D257's own correction, and the composition caveat the reviewers raised is missing.

## Numbers

1. **RESULTS §1, line 24-25, children and elite means (2.5-2.8, 2.9-3.1, 5.5-5.9, 5.5-6.0) are not in `pilot-attempt1-summary.json`.** The file holds only population means, best-by-generation and the 90-99 summaries, and `scripts/e4_pilot_attempt1.py` does not compute children or elite means. They come from D253 ("free, from the saved matrices"). Fix: either extend the script and regenerate the summary (needs the local matrices), or cite D253 and say the numbers are from a local, unregenerated computation.

2. **RESULTS §1, line 27, "E-G's per-maze SD is about 3.7" is Fable's figure from the E3c pilot review, repeated in D253.** From `headroom.json` block A, E-G's per-maze SD is about 4.2 (16 mazes, CPU). Fix: "about 4 (Fable, D253; 4.2 on stage A's block, `headroom.json`)".

3. **Mis-rounded:** §2 table, module B is 2.81 (2.8054), not 2.80. §3, bias 0.05 is 6.72 (6.7248), not 6.73. §3 table, nose-origin cut at 0.25 is 6.25 (6.2548), not 6.26. §1, the 90-99 best range is 6.2-6.9 (run 3: 6.245), not 6.3-6.9. D252 and D256 carry the same three slips; add a dated correction line there.

4. **§1, "the population mean sits near 2.4-3.4 for 100 generations" is not a number in the file.** Per-run means over 90-99 are 3.10-3.35; single generations range 1.49 to 5.16. Fix: give those two ranges and name the field.

5. **Compute, 4.20 against D258's "about 4.4" and "25.6 remaining".** The two compute records sum to 15 124 s = 4.20 h, leaving 25.8. D258 repeats Fable's review estimate. Fix: a one-line correction in D258 or a note in RESULTS that D258's 4.4 was an estimate.

6. **"a run that failed at its last step" (line 9) has no record.** Only its time survives: 4 298 − 1 304 − 2 061 = 933 s. Fix: give the seconds and say its partial output was not kept.

7. **§3, "a ratio of about 4, as predicted from the module's gains (18 and 6)".** 18/6 predicts 3; observed 4.1. Fix: "about 4; the gains Fable computed (18 and 6, D255) predict about 3".

## Claims

8. **§3, line 82, "removing the nose-origin links rescues most" overclaims, and D257 already corrected it to "more rescue".** At 0.25 the cut recovers 1.67 of a 3.39 loss (49%); at 1.0, 1.74 of 5.90 (29%). Fix: "rescues about half the loss at 0.25 and under a third at 1.0; cutting the comparator-origin links rescues little (0.40 and 0.01)".

9. **§3, line 70, "the loss is mostly the share of children that break" is stated as fact.** It is Fable's reading (D257); the records hold no per-child distribution to test it. Fix: "(a reading, Fable, D257)".

10. **Header and README status, "the pilot and its follow-ups showed that it would most likely spend about 20 GPU-hours on an inconclusive null".** The data did not show it; both reviewers estimated it (D257, both reviews). Fix: "both reviewers estimated (D257) that it would spend about 20 GPU-hours".

11. **§5 is otherwise sound.** The "can say" bullets are each supported; "cannot say" matches D257; the attributions to Fable (P1-cut equivalent by construction, P2 unclear at R = 8) and Astra (inconclusive null) match their stage A answers verbatim. README's "What was found" is consistent with the records.

## Missing

12. **Composition.** D257 records that E-G is played as one strain and the children as a 116-strain batch, so E-G's level beside the children is not exact to the last digit. Neither document says so, and `diagnostics.json` and `calibration.json` record no composition (pilot.json does). Add one sentence in §2 or §3, and extend the README's reproducibility line to "the same GPU, environment and batch composition (rule 6)".

13. **Block-dependence.** E-G makes 4.03 on the load block, 7.63 on validation, 7.97 on block A. Weights and τ alone cost nothing on the load block but 7% on block A. State this once, so "the whole load came from the biases" is read as block-specific.

14. **P1-cut, P2 and R are undefined** in RESULTS. Add a gloss or a pointer to E4-DESIGN §4-5.

15. **`headroom.json` was recorded from a dirty tree** (`provenance.dirty: true`). Say so beside its citation in §4.

16. **Owner and reviewers.** Present and adequate: D257's recommendation, D258's decision, Fable's reading, Astra's correction. Fine.

## Housekeeping

17. `diagnostics-partial.json` and `calibration-partial.json` in the folder are untracked; commit or delete before publishing.
18. `docs/E4/E4-D-DESIGN.md` is titled v2.2 but its Status line still says v2.1; the README cites v2.2.
19. §1 "T-F's mutation mask at factor 0.25 (w_sigma 0.08, tau_sigma 0.15, bias_sigma 0.05)" reads as if those were the effective sigmas. Write "factor 0.25 of (w 0.08, τ 0.15, bias 0.05)".

## Style

20. The §3 "biases" paragraph and the header paragraph run 60-80 words per sentence with nested parentheses. Split at the semicolons. Otherwise the layout follows the repository's pattern.

Verified and correct, for the record: 3.01 and 1.19 GPU-hours, 56 s per generation, cap at X+'s generation 80, run-seed pairing (`e4.py:143`), 6.23, the validation figures 7.63 / 6.16 / 6.52 / 7.08 / 6.68, 1.94 / 0.21 / 1.14, the whole diagnostics table except module B, 3.66→2.00, 6.59→4.38, 6.52→4.34, 7.97, 3.38 / 6.86, 93% and 94%, the cross-link ladder, the rest of the intervention table, the headroom figures and 22%, the 22 and 35 GPU-minutes, and that `calibration.py` was committed (aee0194, clean) before stage A ran.