I have what I need: the amendment, both diagnosis records, the diagnose-4 script, the stage-b2 record, the runner's stage-b3 code, the probe and the tests. Writing the review now.

**Verdict: confirm with fixes, no further round.** The diagnostics support the amendment's main conclusion. Two things should change before `stage-b3` runs: the cap should be measured on the seed rather than on the follower, and the threshold's provenance should be the registered rule, not E's own number.

## 1. Do the diagnostics support the conclusion?

**Yes, for E with W2.** The record `diagnosis-4-seeds.json` shows paired effects on all 256 selection mazes, and both intervals exclude zero.

| E + W2 | No trail | Best setting | Medium setting |
|---|---|---|---|
| Later-leg rate | 1.77 | 3.04 (+1.27 [1.01, 1.53]) | 2.30 (+0.53 [0.34, 0.75]) |
| Legs median per wey | 1.63 | 4.06 | 1.94 |
| Share of own inputs above 0.35 | | 0.207 | 0.041 |
| 95th percentile of own inputs | | 0.955 | 0.302 |

The amendment reads these correctly. One thing it omits matters for Stage C: criterion 2 requires a legs median of at least 2.0, and E + W2 sits at 1.94 at the medium setting. The weaker the trail setting, the closer E gets to that floor. The drafted follower-side cap pushes the choice toward weaker settings, so this risk should be stated in the expectations and, better, avoided (see question 2).

**W0, W1 and S3r3 failing is plausible, not a bug, with one cheap check advised.** E + W0 and E + W1 make 0.26 and 0.43 visits per wey against 3.70 for W2. A carrier with a resting turn and no one-sided reflex has no mechanism for progress along a corridor, so this fits. S3r3 + W2 is the odd row: 0.34 first visits per wey yet exactly zero later legs in all three conditions, 6 144 wey-episodes. A champion tuned in an open arena with a partial gate, plus W2's resting turn of 0.4, circling at the source it just visited is a plausible mechanism, and the genome hash is verified against the record. Still, before the report says "S3r3 fails every variant", look at one S3r3 + W2 trajectory on the CPU. That costs nothing and does not block `stage-b3`.

**The follower decomposition supports "gain times difference", with one wording caution.** The clean evidence is the symmetric-occlusion variant (+3.42 against +2.85 for the standard follower, so occlusion asymmetry is not the source) and gain 128 at a quarter of d₀ (+3.02, the gain-times-level invariance). The gain-0 row is not a clean "switch only" measurement: its own no-trail baseline is 1.08 against 3.33 for the standard follower, because the scent near the sources triggers the steering branch even without trails, and with gain 0 that branch is reflex only. So that row shows that losing W2's exploration near sources is harmful, not that the switch contributes nothing. The amendment's table should say so. The "inputs about twice the seed's" claim holds: 95th percentiles of 1.995 against 0.955 at the best setting and 0.692 against 0.302 at the medium one, a ratio of 2.1 to 2.3.

## 2. Is 1.0 defensible, and should the seed qualify the setting?

**The level is defensible.** K_D is a small-signal gain at a fixed difference of 0.001 (`probe.py`, D = 1e-3). On a linear trail the nose difference at a place scales with the level, so the response to a relative difference is K_D times level. E's curve stays above its 0.35 value through 1.0 (15.0) and drops below it by 1.5 (9.7), so 1.0 is inside the measured range and the last grid point before the fall. The extended one-nose checks up to 1.0 are the right large-signal complement.

**Fix the threshold's provenance.** The runner uses 11.06, E's own measured value. The registered rule is K_D ≥ 30 at levels up to 0.35, which is K_D × level ≥ 10.5 at 0.35. Use 10.5. It is seed-independent, it is the registered rule's translation rather than a number read off E, and it changes nothing for E (15.0 passes, 9.7 fails either way). Also correct the sentence "S3r3's module A is 0 at 1.0, so no seed is qualified above 1.0": S3r3 simply fails criterion 4 at the 1.0 boundary, which is always in the level list.

**Measure the cap on the seed, not the follower.** This is my main recommendation. The cap exists to protect the seed's modules, and the follower's exposure runs about 2.1 to 2.3 times the seed's. A follower-side cap at 1.0 is therefore a seed-side cap near 0.45, which is the same mistake Amendment 1 made, at a different level. From the stage-b2 quantiles, the drafted rule would select μ 0.005, λ 0.02, δ 0.15, d₀ 0.2855 (rate 6.01, follower effect +2.07, 95th percentile exactly 1.0, so borderline) or else μ 0.01, λ 0.02, δ 0.05, d₀ 0.2855 (5.81, +1.87). E's effect there is untested and probably between +0.5 and +1.0, with the legs median near the 2.0 floor. A seed-measured cap instead admits the best-rate setting, where E's effect (+1.27) and legs median (4.06) are already measured: E + W2's 95th percentile there is 0.955, so its share above 1.0 is under 5% by construction.

The variant circularity is manageable:

- In `stage-b3`, measure the cap on E + W2's own shared colony with the nose recorder, at each live setting, instead of rerunning the follower. W2 is the only variant that moves, and its exposure is the highest of the three measured (W0 0.62, W1 0.13, W2 0.955 at the best setting), so it is the conservative choice. The ranking stays the follower's rate from Stage B's record, the gradient stays from Stage B's rows, and the trail-effect gate stays from `stage-b2`'s rows (that record is already hash-pinned in the runner). The follower's share above 1.0 becomes a reported number.
- The report's existing seed-side cap, with the chosen seed and variant, remains the verification. Add one rule: if that check fails, Stage C and the report rerun once at the next-ranked qualifying setting, rather than ending in a redesign.

The cost is the same as the drafted rerun: 24 seed runs at about 30 s. With the best-rate setting as the likely winner, the widening fires in two directions (μ down to 0.0025 and d₀ up to 1.142, since the rate rises toward both edges), about 30 settings with 18 new shapes needing gradient runs, roughly 0.3 to 0.4 GPU-hours. Everything else then needs about 0.8. That fits the 1.93 left, with little slack. If you keep the drafted follower-side rule instead, say in the expectations that the winner is probably μ 0.005, λ 0.02, δ 0.15, d₀ 0.2855, that the μ widening will fire (12 settings with fresh gradients, not in the "about 0.2" estimate), and that E + W2 may fail criterion 2's legs floor there.

## 3. Fixes before the run

- **The cap on the seed** (above), or at least the two added expectations if you keep the follower-side cap.
- **Threshold 10.5** in `REGISTERED["stage_b3"]["relative_min"]`, and the plan's criterion 4 text to match, with the test at `tests/test_e3b0_runner.py:163` updated.
- **D179 does not exist.** The script's docstring, the stage label and the runner's comments cite D179, but `DECISIONS.md` ends at D178. Write it before the run, since the record is labelled with it.
- **The gain-0 wording** in the amendment's follower table, as in question 1.
- **Budget the widening** explicitly in the compute projection. The compute record confirms 1.07 of 3 GPU-hours used (3 865 s).
- **The S3r3 + W2 trajectory check** before the report, exploratory and on the CPU.

Nothing else in the amendment needs to change. The stage-b2 reuse guard, the widening rule and the polarity reporting carry over as written.