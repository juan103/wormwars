**Verdict: confirm with fixes.** The diagnosis's numbers check out against the record, the code for `stage-b2` is in place and its smoke run completed, but the amendment does not say what its own cap will select, and that consequence needs to be written down before the run. No further review round is needed if the fixes below are made.

## 1. The second diagnosis

Every number quoted in the amendment matches `stage-b-diagnosis-2.json`. The polarity readings, the zero and occluded shares, the quantiles and the K_D table are all reproduced by the script as written. The two gradient failures at 0.797 are preserved.

What the data support:
- **Facing toward A, 0.3 was unreachable.** The no-trail follower passes in 76.6% of mazes, so the reading's ceiling is 0.234. The synthetic slope reaches exactly that ceiling with a 100% pass. This is a clean result.
- **Facing away, this follower did not use the slope.** Real and permuted trails pass at the same rate at every setting, at 2× and at 4×. The synthetic slope reads +0.016 at 2× and +0.03 at 4×.

Three corrections to the wording:
- Say "did not pass, on 64 mazes", not "cannot be passed". The earlier reviews both noted that a jittered start on a longitudinal slope gives a nonzero steering signal. The evidence is empirical, not structural.
- The synthetic reference is not a pure longitudinal slope. Its distance is a 4-connected breadth-first search, so across a 3-wide corridor it has a Manhattan ridge as steep as the along-route slope. Call it "a reference slope with a centring ridge", or compute the distance along the route's centre line.
- "0.3 was out of reach for any trail" is true for the toward heading only. Facing away, the no-trail rate was 0.016, so there was room. The follower failed that test, not the threshold.

Also note the toward reading is setting-dependent. It is +0.16 at the best-rate setting but −0.08 at the pilot, a difference of about ten mazes in 64. The fixed wording currently turns that into a general claim.

## 2. The amendment as drafted

**The high-level cap is the decisive change, and the draft does not say what it selects.** The new denominator is the positive, unoccluded, after-trail inputs, which the diagnosis puts at about 0.77 of on-route noses. Dividing Stage B's recorded `above_share` by that factor gives the projected qualified share:

| Setting | Stage B above share | Projected qualified share | Rate |
|---|---|---|---|
| μ 0.02, λ 0.04, δ 0.15, d₀ 0.2855 | 0.023 | ≈0.029 | 3.78 |
| μ 0.02, λ 0.04, δ 0.05, d₀ 0.2855 | 0.025 | ≈0.033 | 4.17 |
| μ 0.02, λ 0.04, δ 0.15, d₀ 0.571 | 0.042 | ≈0.054 | 4.23 |
| μ 0.02, λ 0.04, δ 0.05, d₀ 0.571 | 0.047 | ≈0.060 | 4.67 |
| everything else | ≥ 0.045 | ≥ 0.058 | 4.2 to 7.5 |

So two settings pass, the weakest trails in the grid, and the winner is μ 0.02, λ 0.04, δ 0.05, d₀ 0.2855. Three consequences follow and none is in the draft:

- **Criterion 3 will very likely fail.** It needs own − none and shared − none each above 0.5 on the report mazes. At the pilot, with stronger trails, own − none was +0.07 and shared − none +0.83 on 64 mazes. At the winner the follower's rate is 4.17 against a no-trail rate near 3.3. Expect the "weak signal" or "inconclusive" branch. Those §6 rows still say "then the fallback", which contradicts item 7's "there is no fallback". Reconcile them now.
- **The widening is spent on a foreseeable null.** The winner sits on three edges, so `b2_widening` produces 36 settings, each with its own gradient measurement. Every one lies in a direction where Stage B's rows show the rate falling: higher μ, higher λ, lower d₀. That is roughly one GPU-hour to confirm the same winner.
- **The cap is a choice between the signal and the modules, and the draft should say so.** Keeping 5% at 0.35 is defensible: E's K_D is 31.6 at 0.35 and 28.0 at 0.5, so the registered threshold of 30 really does bind there, and S3r3's module A falls to zero at 1.0. But it buys qualification at the cost of the trail effect. The alternative is a looser cap, justified by the K_D curve and labelled post hoc, which my earlier review offered as option 2. Either is acceptable. What is not acceptable is running without stating which was chosen and why, and what it is expected to select.

Smaller points, each a one-line fix:
- **Trail effect.** Fine as a gate. The no-trail run is the same for every setting by construction, so also record that `stage-b2`'s shared rates equal Stage B's rows exactly. That is a free GPU check that the exposure fix left shared trajectories unchanged, which no test currently covers.
- **Widening.** The gradient share is scale-invariant in d₀, as Stage B's identical rows at both d₀ show. Read it from Stage B's row for d₀-only widened settings instead of re-measuring. At μ 0.04 only λ 0.08 is live, since m is 0.0408. Add d₀ to the tie-break, smaller first, or ties resolve by dictionary order.
- **Criterion 4.** The probe's difference step is 0.001, so a 25th percentile below that gives one nose a negative input. Floor the percentile levels at 0.001. Say the quantiles come from the chosen variant's colony, as the code does. Replace "by the cap they are at most 5%" with "the seed's own share above 0.35 is reported": the cap is measured on the follower, and the seed's distribution is measured separately in `cmd_report`. State in advance that S3r3's module A read 29.3 at 0.35 in the diagnosis, below the required 30, so S3r3 is at risk of failing criterion 4 at any level near 0.35.
- **The fixed wording.** It asserts a positive result that holds at one setting and reverses at another. Fix two branches: "the slope exists physically; the follower did not use it facing away at any setting or on the reference slope; facing the source its reading was X at the chosen setting". Keep the E3b-1 sentence.

## 3. Before `stage-b2` runs

- **D178 does not exist.** It is cited in the plan, the code, the tests and the review note, but `DECISIONS.md` ends at D177. Write it, with both reviews archived, before the run.
- **Commit and push first.** The smoke ran on a dirty tree at 85bdffc. Rule 2 applies to the amendment and the code that executes it.
- **Record a compute projection now, not only before Stage C.** My estimate for `stage-b2` as drafted is about 1.1 GPU-hours: 24 reruns with the nose recorder, 36 widened settings with gradients, the no-trail run and nine polarity runs at the winner. That leaves about 1.15 hours for the recheck, Stage C, the report and the timing, which are the stages with neural updates. Trimming the widening's gradient re-measurement helps. If the projection is tight, state now a rule for skipping widening directions where Stage B's rows already show the rate falling, rather than deciding it after the cap clock bites.
- **The record's `resolved_config` still shows the pilot constants and 1 200 ticks.** Say in the record that it is the frame's base config, as my earlier review asked.

The code itself is sound: `require_recheck_passed` is tested, the toward start is tested against the previous route cell with bends present, the exposure fix is tested on the CPU, `polarity_readings` and `synthetic_slope` exist and ran in the smoke, and the smoke's `stage-b2.json` contains a chosen setting, the reported polarity block and the label.