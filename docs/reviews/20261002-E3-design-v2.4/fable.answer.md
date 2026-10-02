## 1. Verdict: proceed to pre-registration

Nothing left needs a new design round. I ran nothing: I read v2.4, both v2.3 reviews, D162 and `config.py`; the numbers below are hand estimates.

## 2. v2.3 items

All are resolved at design level. I checked each row of "Changes from v2.3" against the text, and the bounds against `config.py` (`w_max` 3, `b_max` 2, τ 0.5–20). Blocks 944M–948M appear nowhere in the repository outside the design and `DECISIONS.md`.

Two leftovers, both text:

- **Calibration is half-applied.** Line 412 still takes a monostable champion's median q "on the test worlds", while lines 272 and 413 say calibration worlds. It must be calibration throughout.
- **Astra's nose-level point is half-applied.** Lines 84, 92 and 194 still say the noses receive 0.0100 at the cap distance. That is the scaled head scent; the lowest bilateral nose reading is about 0.007, as line 202 says. It is harmless, since 0.005 is tested.

## 3. New problems in v2.4

None changes an outcome if pinned.

**a. The Stage 0 and Stage 1 gates name no world block.**
- They run before training. If they use 946M, the test worlds are touched before any champion is frozen, which is the conflict Astra raised for D.
- Run the gates on 948M or 947M. Read 946M only after the freeze, for the engineered organism's mean in "working".

**b. The tolerances are relative to q\*.**
- "Within 10% of the fixed point" is ill-scaled for a weak or asymmetric latch, where one stable state can sit near 0.
- Define it against the separation of the two stable states, or add an absolute floor.
- "Within W" should mean "at the end of W". The engineered q overshoots to ∓3.05 before settling.

**c. W = 10·τ_q does not cover a near-fold latch.**
- The relaxation rate is (1 − w_qq·sech²q\*)/τ_q. At w_qq of about 1.1 it is about 0.13/τ_q, so a real but weak latch is still settling at W and fails "settable".
- This is acceptable as an operational class, because the hold now compares with the fixed point after 580 ticks. The registered wording for "bistable, not a latch" should say it includes slow settling.

**d. The champion's own stimulus is undefined in two cases.**
- A champion may have no confirmed visit on the calibration worlds. The classes apply to non-working champions too, so this will occur. Give a fallback of 2 ticks.
- A level may be cut off by the episode's end. Exclude it, as censored legs are.
- Also say which level is measured: the visited source's `at_X`, from the confirmed entry to the exit.

**e. The probe is sound.**
- With q held, holding RA and RB changes nothing in Stages 1–3, since the relays feed only q.
- "Measured after the start cue" is now moot for the probe. Say the probe replaces the cue with the held state.

**f. Random sampling's distribution is no longer a near-certain zero, but its hit rate is unknown.**
- My rough estimate is 10⁻⁴ to 10⁻³ per draw, which gives about 1–10 hits in 9 600 draws and 0–1 in the 1 024-draw census. I could be off by a factor of ten either way.
- The census can therefore read 0 while the search finds one. S2-c's wording must not read a census zero as "the distribution holds none".
- The engineered w_aq and w_bq sit on the bound of U[−3, 3]. Weaker drives may not switch q on a 1–3 tick level at larger τ_q, so the working region may be thin. Report the census's hit rate with an interval.
- S2-b's asymmetry (a local start against a global blind search) is stated in the reading. That is enough.

**g. B-task's draws are sound in principle but underspecified.**
- The tie covers each comparator pair's edges "from every other neuron". That leaves out the self-loops and the CL↔CR pair. It needs CL→CL = CR→CR and CL→CR = CR→CL, or generation 0 has offsets.
- With NL and NR tied into both comparators, CL ≡ CR for any input. Generation 0 then has zero K_D, and every genome behaves as the carrier's circle. It is consistent with "no offset", but it means B-task starts from no navigation at all, while Stage 2 starts from two working modules. Say so in its reading.
- Not given: the output edges' range, and the distribution of τ for the 8 non-q free neurons.

**h. The reset test's "q is set"** should say a one-time write, not a clamp. It should also say which state a monostable champion uses.

## 4. New pins for the pre-registration

- The world block for the Stage 0 and Stage 1 gates (a).
- The tolerance definition and "at the end of W" (b).
- The stimulus fallback, censoring and which level is measured (d).
- Line 412 corrected to calibration worlds, with a dated note.
- S2-c's wording for a zero census from random sampling's distribution, and an interval on the hit rate (f).
- B-task's self and mutual comparator edges, output range and τ draws; the zero-K_D start named in its reading (g).
- The reset write (h).
- Which Stage 3 runs are kept under reduction step 3. Random sampling's are named (runs 0–3); Stage 3's are not.