# E4s-1 results: the comparator graft under evolution

Run 2026-10-01 13:22 to 2026-10-02 06:01. Pre-registered (`PREREGISTRATION.md`):
- **Bound** at 023267d, public before any stage ran (D150);
- **Amendment 1,** dated, also before any stage ran (D152);
- **No change since.**

**The run:**
- **Compute:** 16.61 of 24 GPU-hours (`compute-record.json`).
- **Completion:** every stage completed and every gate passed. All ten training batches passed their
  end-of-run assertions; none was refused, stopped or rerun. The evaluation covered all 80 runs
  ("not covered": none).

**Where the numbers come from:**
- `report.json`, the registered readings, written by `scripts/e4s1_report.py` from the evaluation
  records;
- `summary.json`, the descriptive numbers, written by `scripts/e4s1_summary.py`;
- both read only the committed records and per-world counts in this folder.

Before writing, every headline number was re-derived from the per-world counts, and they agree.

**The frame, as registered:**
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
- M's mean climb, F − G0, has an interval excluding 0, so the companion sentence ("N ended lower; M did
  not improve") does not apply.

**O1b (M − R), confirmatory:** **"Supports: the graft's designed signs beat random signs."**
- The estimate is +3.79, 90% interval +3.32 to +4.25, over 16 pairs; the sign-flip p is 3.1 × 10⁻⁵.
- R − N is +1.40, so random signs were not worse than no graft, and the companion sentence does not
  apply.

**O1c (descriptive):**

| Arm | G0 | F | Climb F − G0 |
|---|---|---|---|
| M | 2.29 | 7.14 (6.57-7.54) | +4.85 |
| N | 0.24 | 1.95 (1.25-2.73) | +1.71 |
| R | 0.38 | 3.35 (0.79-5.79) | +2.97 |

- The difference of the climbs, M against N, is +3.14; against R, +1.88.
- **As stated in advance:** M's and N's G0 bests were picked with and without the graft's output. So
  that difference subtracts the graft's immediate benefit and the two selections' difference, which
  together are G0_M − G0_N = +2.05.

**O2 (the module's use at the two endpoints):**

| Arm | Reading | Counts | Retention among G0 users |
|---|---|---|---|
| M | **uses at both endpoints** | 16 of 16 | 1.0 |
| R | **no label named** | uses at F only 5; uses at F, G0 unclear 3; uses at both endpoints 2; uses at neither endpoint 3; unclear at both endpoints 2; no use at F, G0 unclear 1 | 1.0 (2 G0 users) |
| F0 | uses at both endpoints | 8 of 8 | 1.0 |
| U | uses at both endpoints | 8 of 8 | 1.0 |
| S | uses at both endpoints | 8 of 8 | 1.0 |

**Beside the labels, as registered:**
- **H, the host's own stereo use** while the module is blind: "no material benefit" at both endpoints
  in all 16 M runs, and in every R, U and S run. F0 has one "unclear" at F. **The host did not come to
  steer by the difference itself.**
- **Mc, the evolved module alone on the carrier,** holds in 5 of 16 M runs (8 of 8 in F0, 3 of 8 in U,
  2 of 8 in S, 0 of 16 in R).
- **The G0 population's users:** a mean of 2.8 of 32 per M run, and 0.2 per R run.

**O2b (score with use):** all 16 M runs, and all F0, U and S runs, fall in the band **at least 0.9**.
- M's F scores average 1.37 times L1's alone on its carrier (5.20) on the same worlds.
- R's two "uses at both endpoints" runs are in the lower bands: one at 0.5-0.9, one below 0.5.

**C2 (04a run 2 with the graft):**
- **"harmful" at G0 and "uses" at F in all 8 runs.**
- Real minus module mean is negative at G0 (as E4s-0 found) and positive at F.
- **The scores:** 0.88 at G0 and 6.71 at F (6.26-7.21), against 2.60 for the ungrafted champion on the
  same worlds.

**O3 (descriptive):**
- **F0 − M:** −0.77, so freeing the module helped by about 0.8 (8 pairs).
- **U − M:** −0.97.
- **S − M:** −0.01.
- **Split by G0's open-loop |turn offset| (8 against 8):** M − N is +5.22 in the low-offset half and
  +5.17 in the high-offset half. All 16 runs "use at both endpoints".

**E3's artefact rule (§7):** met.
- 16 of 16 M runs "use at both endpoints".
- The chosen genome is the F of M run 10, the highest final validation mean, with O2b 1.45 (its
  hold-out mean is 7.54).
- E3's own positive control is still required before it replaces E4s-0's module.

## What else the records show (descriptive; `summary.json`)

**The stereo computation stays in the graft, and the host co-adapts to it.**
- **Silencing the module** costs M's final brains 7.03 targets per episode: they fall to 0.11.
- **Putting L1's designed parameters back** ("reset" for M, and the L1 rescue) leaves 0.72. The host
  evolved around the module as it evolved, not around L1.
- **The module's weights barely moved:** mean |w| 2.79 against 3.0, with no sign flips in any arm. Its
  τ and biases evolved too. In 11 of 16 M runs the evolved module no longer meets "uses" alone on the
  carrier, though the whole brain does.
- So the gain is a co-adapted host-and-module system, not a better module.

**Along training** (the best of each generation, on 256 worlds):

| Generation | 0 | 100 | 250 | 500 | 750 | 999 |
|---|---|---|---|---|---|---|
| M: mean score | 2.22 | 5.22 | 6.36 | 6.86 | 7.01 | 7.08 |
| M: runs using the module | 16 | 16 | 16 | 16 | 16 | 16 |
| N: mean score | 0.24 | 1.65 | 1.61 | 1.79 | 1.76 | 1.92 |

- M passes the carrier's 5.2 by generation 100. N stays near the plateau's level throughout.
- R's runs using the module go from 2 of 16 at generation 0 to 10 at generation 100.

**F0, with the module frozen, still climbs to 6.35:**
- its host amplifies the module, so the whole brain's open-loop stereo gain rises from 22 at G0 to 117
  at F;
- in M, U and S it stays at about 15-23.

**The final populations of M:** 258 of 512 strains have a real − module-mean lower bound above 0.5.

**The plateau, for reference:** E2d's 47 champions reached 2.19 (median, other worlds), and N here
1.95. M's final brains, at 7.14, are about three times that.

## What this shows, and what it does not

**Shown, within this game and task:**
- **A hand-built 4-neuron stereo comparator, grafted onto random N2 brains, is kept and used by
  evolution in every run,** and the brains evolved with it end far above the non-stereo plateau.
  - They end about 5.2 targets per episode above the arm evolved without its output.
  - They end 3.8 above a graft of the same shape with random signs.
- **The designed signs matter,** and the host and module co-adapt: the evolved host depends on the
  evolved module, not on L1 as designed.

**Not shown:**
- **Anything about worm chemotaxis:** the stereo sensing is a game-design choice.
- **Transfer of the computation into the host:** H stays "no material benefit". The steering lives in
  the graft.
- **A history between G0 and F:** no ancestry was traced.
- **That the comparator is the best design:** L2-L4 and rings were never tried.
- **That this generalises beyond Task N.**

## Deviations

None from the pre-registration as amended. One limit of what the records hold: the analytic mutation
counts (Amendment 1.3) rest on the tested factors and the N and F0 assertions. They are not observed
per breeding step.
