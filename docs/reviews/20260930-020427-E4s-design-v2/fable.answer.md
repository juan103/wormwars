# Verdict: **proceed to pre-registration**

This is conditional on the must-fix items below going into the pre-registration draft. None changes the arms, the structure of the outcomes or the engine plan, so I do not ask for a design v3. I ran nothing; everything is from reading the code and records.

## 1. Are the v1 must-fixes resolved?

**Resolved:** Fable 1, 2, 3, 5, 6, 7, 8, 9, 11, 12 and Astra 1, 3, 4, 6, 8.

**Partly resolved:**
- **Fable 4 / Astra 7 (outcomes):** the classes are now exclusive and read on F, but see must-fix 5 and 6.
- **Astra 2 (bearing):** the wording is fixed, but the calibration target still treats ψ as a bearing (suggestion 1).
- **Astra 5 (probe extension):** the two new measures are confounded (must-fix 8).
- **Fable 10 (tolerances):** declared, but the score-level check is nearly vacuous (must-fix 9).

## Must-fix

1. **Stage A, G3: persistence contradicts the shifters.** G3 runs "on the carrier", which has a turn bias. At turn 0.2 the heading changes 3.4° per tick, or 69° in 20 ticks. Calibrated shifters must then move the bump about 1.5 columns, but persistence requires it to stay within one. Run persistence with the turn command at zero, or measure it in heading-corrected coordinates.
2. **Stage A, A0 to A1: qualification is undefined and favours latches.**
   - The component checks depend on a and φ, which are tuned later in A1. Apply the checks at each candidate's own values, as a filter inside A1's selection.
   - "Correct side" is tested from a zero start only. Add a carried-state reversal: scent present, δ reversed, the bump crosses within a fixed number of ticks. The differential input (about 0.03) is far below a persistent bump's own drive.
   - "Best 20 by bump contrast" selects the deepest attractors. Take all qualified rings, or a stratified sample.
3. **Stage A, A0: "no spontaneous bump" cannot fail.** A symmetric ring from an exact zero state stays symmetric, even when unstable. Use a seeded perturbation of about 10⁻³, a fixed duration, and a sabotage check.
4. **Modules and Budget: counts.** M1 is 14 neurons, not 30 (32 − 16 − 2). The budget factor is (334/302)² ≈ 1.22, not 332. Define M1 exactly.
5. **O1: the classes are not exclusive.** The interval follows E2d, which bootstraps the mean; the threshold is on the median. Nine runs at +0.55 and seven at −0.2 read both "supports" and "does not support". Use one statistic and ordered rules.
6. **O2: "kept" is a low bar.** A run that falls from 8 to 3 with a contrast of 0.8 is still "kept"; v1's "partly eroded" was dropped without a note. Add that class, or register a retention ratio against Stage A's frozen controller. Also say that if the graft works at generation 0, O1 is close to a manipulation check.
7. **Generation-0 measurement: the trigger is ambiguous.** Pin it as a count (for example, fewer than 9 of 16 runs), pin "best" by which score, and give its worlds their own id range.
8. **What is known 3, and D141: two probe claims are unsupported.** The transient and reversal measures have no unchanged-input control, so they measure drift.
   - For E2 GA run 0 at common level 0.02, the zero-start values are 0.1601 (δ = +0.01) and 0.1619 (δ = −0.01), and the carried reversal ends at 0.1398.
   - Its gain of −0.089 predicts a change of 0.0018.
   - "138 of 141 respond" and "not a latch" need a control run, or a dated correction. The small-signal gain is sound, since both arms share timing.
9. **Engine 5: the score-level check is nearly vacuous.** Random genomes score 0.031 (E1), so ±0.05 can barely fail on 32 of the 33 genomes. Add evolved champions, for example 04a's 16.
10. **Budget: Stage A is underestimated.** A1 is up to 20 × 3⁷ = 43 740 configurations, or 5.6 M episodes on 128 worlds, against 2.05 M for E2's whole GA training.
    - At the recorded rates (434 to 1 027 episodes per second) that is 1.5 to 3.6 h before the 1.22 factor.
    - The re-score adds 1.1 M episodes.
    - My estimate for Stage A is 2.5 to 5.5 h, not 1 h, and 18 to 21 h in total. The 30 h cap holds; the per-stage caps must change.

## 2. Suggestions

1. **Shifter check.** At full turn the bump must move one column per 2.6 ticks, which a ring at τ = 3 cannot do. Add τ = 0.5, pin how bump position is measured, and pre-state a fallback if no gain passes (for example, M1 becomes the module).
2. **Ring against gain cascade.** M2 has more stages than M0, so it can win on feedforward gain alone. Add a Stage A control: the ring with w_e = w_i = 0.
3. **Reaching the gate.** I estimate M0's feedforward gain at k of about 11 to 18, so G1 is marginal for it. M2 has enough gain, but four low-pass stages add lag. I expect the joint G1 and G3 pass to be the main risk.
4. **Nose weights.** Allow unrectified cosine weights as a grid option; they cancel part of the common mode, and Dale is off.
5. **A0 inputs.** Add δ = ±0.004 and common level 0.35 (the peak).
6. **Mutation fallback.** 0.125× is adopted unmeasured; measure it too. On the carrier, mutate module-owned parameters only. The module has no gap junctions, so "g 0.01" is moot.
7. **O1 sensitivity.** Report it without pairs whose B3 start scores zero, as E2's run 2 did.
8. **Hash check.** Also compare the old and new engine in the same session, in case the environment has drifted.

## 3. What the pre-registration must pin

- The complete module: every weight, τ and bias for the noses, Δ, shifters, relays and readout, and which weight is the "shifter gain".
- M0's w_d grid.
- The module definition file and its hash, plus a freeze record pushed after tuning and before the gate.
- All world-id ranges and seeds, including the robustness worlds, and which B1 runs pair with B2.
- The interval method for E2d's criterion and the bootstrap settings.
- How "not read" runs count in 12 of 16, and the rerun rule.
- O2's wording in the integration case ("eroded" becomes "not integrated").
- Which genomes the CUDA state tolerance applies to, and what happens if a champion fails it.
- The synapse-direction test, which is not yet in `tests/test_graft.py`.
- The roadmap amendment, which is not yet in `ROADMAP.md`.

## Checked and found correct

- **Carrier arithmetic:** forward is 2·tanh(b_f) and turn is 2·tanh(b_t) (`world.py:742-752`, gains 4 and 2).
- **Signs:** dorsal is turn-plus and positive is left; the shifter direction is right for positive θ as left.
- **M2's count:** 32 neurons.
- **Binomial:** 12 of 16 gives p = 0.0384.
- **E2's hashes:** 8 000 per-generation hashes are committed in `train-ga.json`, and E2d's replay reproduced generations 0 to 25.
- **E1's figures:** 5.63, 4.23, 8.78, 8.85 and 0.031 match its `RESULTS.md`.
- **Probe summary:** 0.098, 0.68, 0.032, 138 of 141 and 4.8% match `gain-probe.json`, written at a clean commit.
- **Engine claims:** `evolve_batch` and `mutate` are as the design says; a scale of ones or zero behaves as claimed in IEEE arithmetic.
- **Graft code:** `seeded_genome` copies the worm block exactly, and B3's pinned zero edges keep B1's spec and noise shapes.
- **Stage B's time:** 8 batches × 1.35 h × 1.22 is about 13 h.
- **Hygiene test:** it keys on 302 and known labels, as the design says.