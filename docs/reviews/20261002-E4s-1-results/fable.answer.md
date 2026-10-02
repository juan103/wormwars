**Verdict: fix (text only).** Every registered label and headline number I could re-derive from `report.json`, `summary.json`, `eval-endpoints.json` and the gate records holds. The descriptive prose overreaches in several places, and one pattern in the records undercuts the "steering stays in the graft" framing.

I could not run code or open the `.npz` files, so nothing below is checked against the per-world counts. I also did not check the 16.61 GPU-hour total, run 10's validation rank, or the push order.

## 1. What re-derives

- **O1:** the 16 per-run F differences from `eval-endpoints.json` average +5.1932, the smallest is run 6 at +4.531, and all are positive. The label and the sign-flip p (2/2¹⁶) are right.
- **O1b and R − N:** 7.1415 − 3.3489 = +3.7927, and R − N = +1.4006.
- **O1c:** the table and the +3.14, +1.88 and +2.05 match (5.19 − 2.05 = 3.14).
- **O2:** R's six counts, the Mc counts (5/16, 8/8, 3/8, 2/8, 0/16), the O2b bands and the G0 user means (2.8, 0.2) match.
- **C2, O3 and the E3 rule:** all match `report.json`; run 10's hold-out is 1.4493 × 5.2031 = 7.54.
- **Gates:** G1 is 5.193 with lower bound 5.113; G2 is 2.71 × 10⁻⁶; G3 has `identical_worlds` 1.0 for all 24.

## 2. Unsupported claims, departures and overreach

1. **"The host did not come to steer by the difference itself"** (RESULTS), **"The host does not learn stereo by itself"** (folder README), **"The steering stays in the graft"** (all three files). Three problems:
   - §11 says E4s-1 cannot show transfer of a computation into the host, and these read as the negative of that.
   - In 8 of 16 M runs the blind-module baseline (F score minus real − module mean) is 0.03-0.30 targets: runs 1, 2, 8, 11, 12, 13, 14, 15. H compares two near-zero scores there, so "no material benefit" is forced by the floor.
   - H is not zero where it can be measured. M run 0 at F has +0.10 [0.07, 0.13] and +0.17 [0.14, 0.21]. M run 5's champion C is "unclear" at +0.21 and +0.40 [0.33, 0.47]; run 7's C is "unclear" and negative.
   - Correction: "H is 'no material benefit' at F in all 16 M runs; in 8 of them the blind-module baseline is near zero, so H is uninformative there; two champions are 'unclear'." Drop the bold sentence and reword the README lines.

2. **"Before writing, every headline number was re-derived from the per-world counts."** `e4s1_summary.py` re-derives only F's mean scores from the counts (`F_from_counts`). Contrasts, G0, C and along-training come from the JSON summaries. Either commit the check or say "F's scores were re-derived" (rule 5).

3. **"M's mean climb … has an interval excluding 0."** The interval is computed in `e4s1_report.py` but never written to `report.json`; only `companion: null` is. The claim is true, since all 16 climbs are at least +3.20. Record the interval or cite the minimum.

4. **"its host amplifies the module, so the whole brain's open-loop stereo gain rises from 22 at G0 to 117 at F"** (F0). 117 is a mean over 8 runs with range 9.6 to 428. At least one run ends below the G0 minimum of 12.5. Give the median or range, and say "in some runs".

5. **"The module's weights barely moved … Its τ and biases evolved too."**
   - The mean |w| of 2.79 is right, but the minimum is 2.22, and the same section shows that restoring L1 collapses the score to 0.72. "Barely moved" contradicts the co-adaptation claim; say "shrank 7% on average (the bound allows only shrinking)".
   - No τ or bias number exists in `summary.json`. Add one or drop the sentence.
   - "Leaves 0.72" hides a range of 0 to 4.72.

6. **"so freeing the module helped by about 0.8"** (O3). This is causal wording for an 8-pair descriptive mean with no interval. Write "M ended 0.77 above F0 (8 pairs, descriptive)". §2 registered F0 − M to address a loss of use, which did not happen; say so.

7. **"M passes the carrier's 5.2 by generation 100."** That is 5.22 (mean of bests, 256 along-training worlds) against 5.20 (L1, 1 024 hold-out worlds). Different worlds, 0.02 apart, and a mean across runs. Write "reaches about the carrier's level".
   - "N stays near the plateau's level throughout" is wrong at generation 0 (0.24). From generation 100 it is 1.6-1.9, below 2.19.

8. **"is kept and used by evolution in every run"** (RESULTS) and **"all 16 runs keep using the module"** (front page). §5 says no history between G0 and F is claimed. Use the registered label, "uses at both endpoints in 16 of 16 M runs", and limit "every run" to M.

9. **The "Shown" list mixes confirmatory and descriptive.** "The host and module co-adapt: the evolved host depends on the evolved module, not on L1" comes from the lesion and reset measures and should be tagged descriptive.

10. **O1c omits a registered sentence.** The pre-registration states "a negative climb difference is expected even if M ends higher". The result was +3.14. RESULTS quotes the "stated in advance" paragraph but not that the expectation failed. Add it.

11. **Registered reporting items missing from the text; "Deviations: None" should list them or point to the records:**
    - R's final edge signs and magnitudes, and each draw's G0 K_D and K_C (§5, §6). The text has only "no sign flips in any arm".
    - C's scores (M 7.37, N 2.15, R 3.68).
    - The Mc carrier shares and the closed-loop motor measures.
    - F0's "8 of 8" Mc is true by construction (frozen module, share exactly 1.0); say so.

12. **C2 "harmful at G0 … in all 8 runs".** G0 is 32 copies of one genome, so this is one measurement repeated eight times (score 0.876, contrast −1.72 in every run). Say so.

13. **O2 label wording.** RESULTS writes "uses at F, G0 unclear" and "no use at F, G0 unclear"; the registered labels use semicolons. Trivial, but they are fixed labels.

14. **The frame.** §1 requires it "stated in every claim". The folder README's status bullets and D153 state the results without it. The front-page row carries it only in the Question cell.

15. **Stale or broken text:**
    - Front page, lines 4-5: "E4s-1 is pre-registered and running".
    - Front page, E4s status cell: "and running", beside "results under review" in the same row.
    - Folder README: "Status (2026-10-01)" describes 2 October events.
    - Folder README: "(pre-registered, running)" under "Extend it".
    - Folder README, lines 16-17: "The plan is …" is fused onto the last status bullet.
    - Folder README: O1b's +3.79 is given without its interval.

## 3. What the records show that the text misses

- **Several M brains score well above the plateau with no stereo cue reaching the module.** The score with the module's noses on the mean (F minus real − module mean) is 4.51 in run 9, 3.65 in run 0, 3.07 in run 10 and 2.47 in run 3. H is "no material benefit" in those runs, so the host is not using the difference either.
  - Run 9 keeps 4.5 of its 7.2 targets with no left-right difference in use anywhere. That is twice the "non-stereo plateau" of 2.19.
  - So part of M − N is a non-stereo benefit of the graft's output path. Common-mode drive or a turn bias are guesses; the records do not say which.
  - O1's wording ("the graft's output") survives. "Three times the non-stereo plateau" and "the steering stays in the graft" need this beside them.
  - The mean blind-module score across M is about 1.26; the distribution is bimodal: eight runs near 0 and four above 2.4.

- **O1b is conditional on signs that could not change.** There are zero sign flips in any arm, and R's smallest |w| is 1.73. At factor 0.25 the per-generation σ is 0.02 from a start of ±3.0. "Designed signs beat random signs" therefore means "beat random signs that evolution could not repair in 1 000 generations at this scale". State that next to "The designed signs matter".

- **R's use is not monotone along training:** 2, 10, 8, 8, 11, 10 runs. The text gives only the first two.

- **One coincidence to check against the counts.** M run 10's F, S run 0's F and M run 3's C all score exactly 7.541015625 (7 722 targets), which is also M's maximum. Confirm that the per-world vectors differ, to rule out a duplicated key or a ceiling.