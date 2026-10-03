**Verdict: fix then publish.** The numbers in RESULTS.md match the committed records, the exit criteria are read correctly, and the labelling is honest. The fixes are to wording and disclosure, not to the findings. Details follow.

## 1. Numbers and claims

Every number I checked traces to `report.json`, `timing.json`, `stage-c.json`, `stage-b3.json`, `recheck-a.json`, `stage-a.json` or `compute-record.json`, including the "In brief" figures, the criterion 2-4 tables, the polarity table, the gradient shares, the replay coefficients, the exposure residuals, the route overlap, the single-wey figures and the 2.62 GPU-hours. One rounding slip: K_D × level at 0.891 is 17.04 × 0.891 = 15.2, not 15.1.

Overstated or loose, in "In brief":

- **"Exposure was matched"** holds for replay only. Scramble's nose exposure is a small fraction of the live peers' field, and the plan said this would be reported, not matched.

| | Peers exposure | Scramble exposure |
|---|---|---|
| Follower | 0.409 | 0.031 |
| Seed | 0.103 | 0.019 |

- **The heading "Trails from another episode mislead" covers scramble**, which is not from another episode. Split the two.
- **"since they mark the wrong route" is a mechanism claim**, the same genre Astra corrected in the interim report. Replay and scramble are both below *none* as well as below *own* (replay − none is about −1.5 for the follower and −0.6 for the seed; scramble − none about −2.1 and −0.8). Scramble, with almost no exposure, hurts about as much as replay. That fits "any peer field not laid toward the colony's own sources is harmful, likely by pulling the controller out of its exploration" at least as well as "it marks the wrong route". Report the fact, offer the reading as a reading.
- **"at any setting"** for the polarity test: it was run at Stage B's 24 live settings and at the chosen one. The 30 widened settings were not polarity-tested.
- **Understated:** the seed is only +1.09 [0.44, 1.77] visits above the blind wall-follower W2 alone, out of 5.78. Most of the seed's maze performance is the engineered reflex. That belongs in "In brief", because it frames what E3b-1's gate can mean.

Elsewhere:

- The stage table's "23 of 54 settings qualified, 30 of them widened" reads as 30 of the 23. It should say 54 settings, 24 live plus 30 widened, 23 qualified.
- S3r3's turn bias of −0.76 comes from an exploratory CPU look with no committed record (rule 5). Commit it or label it as uncommitted.
- `report.json` has `component_tests.active.passed: false`. RESULTS.md should say that flag fails only at the 99th percentile level (1.82), above the cap, and that `active_passed_up_to_high_level` is true.

## 2. The exit criteria

- **Criterion 1.** The GPU-leg omission is disclosed in the criterion, but not in "In brief" or the stage table, and "passed on the CPU" is doing a lot of work. Worse: the two committed compare records were made at engine step 1 (compared commits 828c2d8 and 4af5862). Steps 2 to 4 and the later fixes came after, and `wormwars/world.py`, `config.py` and `evo/rollout.py` carry maze dispatch code. The claim "bitwise identical to the engine at 84ff98a" needs a record at the final commit. Rerunning `scripts/e3_equivalence.py` on the CPU takes minutes; do it and commit the record before publishing. Say the GPU leg is owed in "In brief".
- **Criteria 2 to 4.** Read correctly. Criterion 2's headroom minimum 2.54 is 2 × 0.22 × 5.78, with 0.22 the 12-run, CV 0.282, normal MDE in `power.json`. Criterion 3's follower bounds exceed 0.5, the peer measure is wholly below 0 for both controllers, the seed's shared − none lower bound is above 0. The seed's shared − own in rate has a lower bound of 0.0009, in effect zero; RESULTS does not lean on it, which is right.
- **Criterion 5.** Failed as sized, arithmetic verified: 0.0565 s per tick × 2400 × 6144/4096 = 203.5 s per generation; × 500 / 3600 = 28.26 h; × 2 × 1.25 = 70.7 h.
- **Criterion 6.** Honestly stated. The 0.74 is between-maze spread, not run spread, and the text says so.

## 3. E3b-1: fixed, open, and the budget

**Fixed by E3b-0:** c = 5, H = 2400, colony 8 on 4 spawns; μ 0.01, λ 0.02, δ 0.05, d₀ 1.142; scents σ 3, reach 9; seed E + W2 with D176's resting-turn pin, W2 frozen across arms; the replay rule (donor episode +1000, different endpoints, coefficient frozen from a selection pre-pass); untouched maze blocks for E3b-1 (0-255 and 1000-1255 are spent); 12 runs per arm with a calibrated one-sided test; MDE 0.22 for the margin; no directional-trail claim; D = 141; criterion 4's levels.

**Still open:** generations, worlds per genome, population, the no-trails arm's size, which parameters mutate (W2's must stay frozen), how the replay coefficient is set for tuned colonies (0.64 is the seed's; each champion's exposure differs, so re-derive per champion on selection mazes before any test maze), and the trail claim's size. Size it to the seed's +0.69 shared − none and −196 ticks peer effect, not to the follower's.

**The budget.** Hours per arm scale as 28.3 × (G/500) × (W/16). The owner's ceiling leaves about 27 h after E3b-0.

| G | W | Two arms, with reserve | Fits plan's 24 h |
|---|---|---|---|
| 500 | 16 | 70.7 | no |
| 250 | 16 | 35.3 | no |
| 300 | 8 | 21.2 | yes, before validation and evaluation |
| 250 | 8 | 17.7 | yes |
| 200 | 8 | 14.1 | yes, with room |

Two cautions on the plan's cut order. E3a's Stage 3 curves (`train-3.json`) show two of eight runs making most of their gain after generation 375, while two plateaued by about 250. Cutting generations to 200 would have truncated the slow climbers, which makes a null less interpretable. Halving worlds per genome instead raises selection noise: with a between-maze CV of 0.74, a genome's score has a standard error near 26% of its mean at 8 worlds against 18% at 16. My recommendation is G 250 to 300 with W 8, both arms kept at 12 runs, horizon untouched, and the no-trails arm shrunk to 6 runs before any further cut. Also retime at the actual compositions (3072 and 4608 worlds) before registering; the 4096-world figure assumes linear scaling, and the projection omits validation and the 2 × 2 evaluation, which should be budgeted explicitly.