# E4s-1 results: the comparator graft under evolution

Run 2026-10-01 13:22 to 2026-10-02 06:01. Pre-registered (`PREREGISTRATION.md`):
- **Bound** at 023267d, public before any stage ran (D150);
- **Amendment 1,** dated, also before any stage ran (D152);
- **No change since.**

**The run:**
- **Compute:** 16.61 of 24 GPU-hours (`compute-record.json`).
- **Completion:** every stage completed and every gate passed. All ten training batches passed their
  end-of-run assertions; none was refused, stopped or rerun. The evaluation covered all 80 runs.
- **Reviewed** by Astra 6 and Fable 5.1: both said "fix", text only
  (`docs/reviews/20261002-E4s-1-results/`). The text below is corrected; the Corrections section at
  the end quotes what was wrong (D154).
  - Astra re-derived all 240 endpoint scores and 5 152 world-level intervals from the per-world
    counts.

**Where the numbers come from:**
- `report.json`, the registered readings, written by `scripts/e4s1_report.py` from the evaluation
  records;
- `summary.json`, the descriptive numbers, written by `scripts/e4s1_summary.py` from the same records.
  F's scores are re-derived there from the per-world counts.

**The frame, as registered, for every claim below:**
- Stereo sensing is a game-design choice.
- The stereo computation starts in a 4-neuron graft with its own noses and its own path to the motors,
  outside the N2 mask.
- Nothing here is about worm chemotaxis.

## The gates (§3)

| Gate | Test | Result |
|---|---|---|
| G1, re-qualification | L1 on its carrier: lower bound ≥ 5.0, and "uses" | Mean 5.19, lower bound 5.11; "uses". **Passed** |
| G2, CUDA state | ≤ 10⁻⁴ in the host's state, 48 genomes, 4 shapes | Largest difference 2.7 × 10⁻⁶. **Passed** |
| G3, score level | 24 champions, ungrafted against N's construction, within 0.05 | Identical counts in every world for all 24. **Passed** |

## The registered readings (§6)

**O1 (M − N), confirmatory:** **"Supports: the arm evolved with the graft's output ends with a better
final brain than the arm evolved without it."**
- The estimate is +5.19 targets per episode, 90% interval +5.06 to +5.33, over 16 complete pairs.
- All 16 differences are positive (the smallest +4.53). The sign-flip p is 3.1 × 10⁻⁵, the smallest
  possible with 16 pairs.
- M's mean climb, F − G0, is +4.85, with a 90% interval of +4.48 to +5.20 (`report.json`). The
  companion sentence ("N ended lower; M did not improve") therefore does not apply.

**O1b (M − R), confirmatory:** **"Supports: the graft's designed signs beat random signs."**
- The estimate is +3.79, 90% interval +3.32 to +4.25, over 16 pairs; the sign-flip p is 3.1 × 10⁻⁵.
- R − N is +1.40, so random signs were not worse than no graft, and the companion sentence does not
  apply.
- **Read with this:** these are random signs that evolution could not repair.
  - No edge in any arm changed sign between G0 and F.
  - R's smallest final |w| is 1.73: from ±3.0, at the module's σ of 0.02 per generation, 1 000
    generations did not reach zero.
  - So "designed signs beat random signs" means "beat random signs fixed for the run".

**O1c (descriptive):**

| Arm | G0 | F | Climb F − G0 |
|---|---|---|---|
| M | 2.29 | 7.14 (6.57-7.54) | +4.85 |
| N | 0.24 | 1.95 (1.25-2.73) | +1.71 |
| R | 0.38 | 3.35 (0.79-5.79) | +2.97 |

- The difference of the climbs, M against N, is +3.14; against R, +1.88.
- **As stated in advance:** M's and N's G0 bests were picked with and without the graft's output, so
  that difference subtracts the graft's immediate benefit and the two selections' difference, which
  together are G0_M − G0_N = +2.05.
- **The pre-registration also said "a negative climb difference is expected even if M ends higher".
  That expectation failed:** the difference is +3.14.
- **C's scores:** M 7.37, N 2.15, R 3.68.

**O2 (the module's use at the two endpoints),** in the registered labels:

| Arm | Reading | Counts | Retention among G0 users |
|---|---|---|---|
| M | **uses at both endpoints** | 16 of 16 | 1.0 |
| R | **no label named** | uses at F only 5; uses at F; G0 unclear 3; uses at both endpoints 2; uses at neither endpoint 3; unclear at both endpoints 2; no use at F; G0 unclear 1 | 1.0 (2 G0 users) |
| F0 | uses at both endpoints | 8 of 8 | 1.0 |
| U | uses at both endpoints | 8 of 8 | 1.0 |
| S | uses at both endpoints | 8 of 8 | 1.0 |

**Beside the labels, as registered:**
- **H, the host's own use of the difference while the module is blind,** is "no material benefit" at
  F in all 16 M runs. F0 has one "unclear" at F. Two M champions (C) are "unclear".
  - **In 8 of the 16 M runs H is uninformative.** There, the score with the module's noses on the
    mean is near zero (below 0.35: runs 1, 2, 8, 11, 12, 13, 14 and 15), so H compares two near-zero
    scores.
  - **Transfer of the computation into the host was not shown,** as §11 says. Final performance
    depends strongly on the graft (below).
- **Mc, the evolved module alone on the carrier,** holds in 5 of 16 M runs, 3 of 8 U, 2 of 8 S and 0 of
  16 R. In F0 it is 8 of 8, by construction: the module is frozen, and its carrier share is exactly 1.
- **The G0 population's users:** a mean of 2.8 of 32 per M run, and 0.2 per R run.

**O2b (score with use):** all 16 M runs, and all F0, U and S runs, fall in the band **at least 0.9**.
- M's F scores average 1.37 times L1's alone on its carrier (5.20) on the same worlds.
- R's two "uses at both endpoints" runs are in the lower bands: one at 0.5-0.9, one below 0.5.

**C2 (04a run 2 with the graft):**
- **The reading is "harmful" at G0 and "uses" at F, in all 8 runs.**
- C2's G0 is 32 copies of one genome, so its G0 is one measurement repeated eight times: score 0.88,
  real − module mean −1.72.
- At F, the 8 runs score 6.71 (6.26-7.21), against 2.60 for the ungrafted champion on the same worlds.

**O3 (descriptive):**
- **The arms against M** (8 pairs each, descriptive, no interval): M ended 0.77 above F0, 0.97 above
  U, and 0.01 above S.
  - §2 registered F0 − M to address a loss of use. No loss of use happened: F0 and M both "use at
    both endpoints" in every run.
- **Split by G0's open-loop |turn offset| (8 against 8):** M − N is +5.22 in the low-offset half and
  +5.17 in the high-offset half. All 16 runs "use at both endpoints".

**E3's artefact rule (§7):** **the two E4s-1 conditions are met. Replacement remains conditional on
E3's own positive control.**
- 16 of 16 M runs "use at both endpoints".
- The chosen genome is the F of M run 10: its final validation mean is the highest (7.52), its
  hold-out mean is 7.54, and its O2b is 1.45.
- **What E3 would inherit is a whole-brain artefact.**
  - Run 10's module scores 0 alone on both carriers.
  - Silencing it leaves 0, and restoring L1 leaves 0.04.

## What else the records show (descriptive; `summary.json`)

**Part of M − N is not stereo use** (Fable).
- With the module's noses fed the mean, so that no left-right difference reaches the module, M's final
  brains keep 1.26 targets per episode on average.
- The distribution is bimodal: eight runs are near 0, and four keep 2.47-4.51 (run 9 keeps 4.51 of its
  7.21).
- The host shows no stereo use either (H), so this part of the graft's benefit comes through its
  output path without the difference: perhaps a common-mode drive or a turn bias. The records do not
  say which.
- O1's wording, "the graft's output", stands. A comparison of M with the non-stereo plateau has to be
  read with this.

**The graft is necessary to the evolved brains, and host and module co-adapt** (an interpretation
consistent with the interventions; no history was traced):
- **Silencing the module** costs M's final brains 7.03 targets per episode on average: they fall to
  0.11.
- **Putting L1's designed parameters back** (M's reset, and the L1 rescue) leaves 0.72 on average,
  ranging from 0 to 4.72.
- **The module's weights shrank 6.9% on average** (mean |w| 2.79 against 3.0; the bound allows only
  shrinking), with a minimum of 2.22. There were no G0-to-F sign differences in any arm.
- **The module's τ and biases moved too:** mean absolute changes of 0.69 and 0.12 in M.
- **Alone on the carriers, the evolved modules differ.**
  - 5 of 16 M modules meet "uses", and each of those beats L1 on at least one carrier orientation (for
    example run 4, 6.93 against 5.20 at +0.2).
  - 10 of 16 score 0 on both carriers, while their whole brains score well.

**Along training** (the best of each generation, on 256 worlds):

| Generation | 0 | 100 | 250 | 500 | 750 | 999 |
|---|---|---|---|---|---|---|
| M: mean score | 2.22 | 5.22 | 6.36 | 6.86 | 7.01 | 7.08 |
| M: selected brains using the module | 16 | 16 | 16 | 16 | 16 | 16 |
| N: mean score | 0.24 | 1.65 | 1.61 | 1.79 | 1.76 | 1.92 |
| R: selected brains using the module | 2 | 10 | 8 | 8 | 11 | 10 |

- By generation 100, M's mean reaches 5.22, about the carrier reference of 5.20, measured on other
  worlds.
- From generation 100 on, N averages 1.61-1.92.
- R's use is not monotone.

**The open-loop stereo gain K_D at m = 0.08** (the whole brain, the medians across runs):

| Arm | G0 | F | Range at F |
|---|---|---|---|
| M | 15.6 | 18.2 | 13.1-32.0 |
| F0 | 16.8 | 45.5 | 9.6-428 |
| U | 16.8 | 12.3 | 6.7-30.9 |
| S | 16.8 | 21.8 | 15.9-41.7 |
| C2 | 7.5 | 16.9 | 11.1-23.9 |

In some F0 runs the host amplifies the frozen module's output strongly; two runs account for most of
the arm's mean.

**The final populations of M:** 258 of 512 strains have a real − module-mean lower bound above 0.5. That
is a single contrast, not the full "uses" classification.

**R's draws alone** (each on the carrier at G0): K_D at m = 0.08 averages −2.0 (from −22.4 to +3.2).
Random signs mostly cancel or reverse the module's stereo gain.

**A checked coincidence:** M run 10's F, S run 0's F and M run 3's C all total exactly 7 722 targets, the
maximum. Their per-world counts differ (`summary.json`).

## What this shows, and what it does not

**Shown, within this game and task:**
- **Confirmatory (O1, O1b):**
  - the arm evolved with the 4-neuron comparator's output ends 5.2 targets per episode above the arm
    evolved without it;
  - and 3.8 above a graft of the same shape whose random signs were fixed for the run.
- **Registered, descriptive (O2, O2b):** the selected M brains "use at both endpoints" in 16 of 16 runs,
  at least 0.9 of L1 alone.
- **Descriptive:**
  - the evolved brains depend on the graft, and on their evolved module rather than on L1 as
    designed;
  - part of the graft's benefit is not stereo use.

**Not shown:**
- **Anything about worm chemotaxis:** the stereo sensing is a game-design choice.
- **Transfer of the computation into the host:** H stays "no material benefit", and is uninformative
  in half the runs.
- **A history between G0 and F,** or continuous use between the sampled generations: no ancestry was
  traced.
- **Population-wide retention:** half of M's final strains pass the single contrast.
- **That the comparator is the best design:** L2-L4 and rings were never tried.
- **That this generalises beyond Task N.**

## Deviations

- **A recording defect** (Astra). The endpoint stage cast every per-world array to int16, including
  the closed-loop motor measures, which are fractions.
  - All 1 440 stored motor arrays are therefore zeros (`summary.json`, `motor_arrays`).
  - The per-episode motor means in `eval-endpoints.json` were computed before the cast and are
    intact.
  - The per-world motor audit trail Amendment 1 and D152 intended is lost. The target counts and every
    registered outcome are unaffected.
  - The records are left as they are.
- **The analytic mutation counts** (Amendment 1.3) rest on the tested factors and the N and F0
  assertions. They are not observed per breeding step.

## Corrections (2026-10-02, results review; D154)

The first version (commit 51f3dfa) said, now corrected above:

1. "**The host did not come to steer by the difference itself.**" and "The steering stays in the
   graft". H tests the host while the module is blind; it is uninformative in 8 of 16 runs, and §11
   excludes claims about transfer. Now: H is "no material benefit" under the module-blind assay, final
   performance depends strongly on the graft, and transfer was not shown (both).
2. "So the gain is a co-adapted host-and-module system, not a better module." Too categorical. 5 of the
   evolved modules beat L1 alone on a carrier, and 10 score 0 there (Astra).
3. "E3's artefact rule (§7): met." §7 also requires E3's positive control. Now: "the two E4s-1
   conditions are met; replacement remains conditional on E3's positive control" (both).
4. "is kept and used by evolution in every run" and "all 16 runs keep using the module". These overstate
   continuity: only selected brains at G0, F and six sampled generations were measured. And "no sign
   flips" compared endpoints (both).
5. "M passes the carrier's 5.2 by generation 100. N stays near the plateau's level throughout." That is
   5.22 against 5.20 on other worlds, and N starts at 0.24 (both).
6. "its host amplifies the module, so the whole brain's open-loop stereo gain rises from 22 at G0 to
   117 at F". That is a mean over a range of 9.6-428; the median is 16.8 to 45.5 (both).
7. "Before writing, every headline number was re-derived from the per-world counts". Only F's scores
   were re-derived in the committed script (Fable).
8. "has an interval excluding 0" for M's climb: the interval was not recorded. It now is: +4.48 to
   +5.20 (Fable).
9. "The module's weights barely moved … Its τ and biases evolved too." They shrank 6.9%, and the τ and
   bias changes had no number; both are now given (Fable).
10. "so freeing the module helped by about 0.8": causal wording for an 8-pair descriptive mean (Fable).
11. O1c omitted that its registered expectation, a negative climb difference, failed (Fable).
12. "harmful at G0 … in all 8 runs" for C2: one genome measured eight times (Fable).
13. "Deviations: None" missed the int16 cast of the motor arrays (Astra). Also missing were several
    registered reporting items: R's final signs and magnitudes, R's draws' K_D and K_C, C's scores, and
    the Mc carrier shares (Fable).
14. "uses at F, G0 unclear" and "no use at F, G0 unclear": the registered labels use semicolons
    (Fable).
15. Missing: that part of M − N is not stereo use (Fable), and that "designed signs beat random signs"
    concerns signs that could not change (Fable).
