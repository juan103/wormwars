## 1. Verdict: proceed to pre-registration

Three pins must be carried into it (items 3a–3c below); none needs a new design round. I ran nothing: the numbers below are hand calculations from `Brain.step`'s update rule, `module.json`, `config.py` and the committed JSON.

## 2. v2.2 items

All are resolved. I rechecked these against files:

- **Geometry:** the JSON matches the design (acceptance minimum 0.1177, median 0.178; 16 373 of 8 801 215; scent 0.02857, which the noses receive as 0.0100; 6.6% at 14 cells).
- **Antisymmetry:** `module.json` has the comparator-to-turn edges at exactly ±3, with nose-to-comparator at ±3 and equal τ, so tied draws give CL ≡ CR and a zero offset.
- **Budget:** the ten batches took 4 876–5 151 s; Stage 2's 1.7 h follows (1.39 h × 1.2).
- **Hold reference, classes, release floor, validation parity, census ordering, S2-b's first outcome:** done as mapped.

Two are resolved for the engineered organism but not for every champion, and both are covered in items 3a and 3b: the settling window, and the two-tick stimulus.

## 3. New problems in v2.3

**a. The 20-tick windows are tuned to τ_q = 1 (must pin).** τ_q evolves over [0.5, 20].
- A bistable champion relaxes at about 0.83/τ_q per tick. At τ_q of about 4–6, a champion that does switch is still settling at tick 20.
- Its reference is then mid-transient, so "within 10% of the reference" fails a real latch. This is v2.2's defect again, for slow champions.
- "Settable within 20 ticks" has the same problem.
- Fix: compare q at the end with the champion's fixed point only, and scale both windows with the champion's τ_q (for example max(20, 10 τ_q)).

**b. The two-tick level can contradict "working" (must pin).** A champion whose visits last 4–6 ticks in the world can alternate correctly and pass the clamp assays, yet fail "settable" or the release test.
- At τ_q ≥ 5 with drive 3, I estimate a two-tick level moves q by about 1.5, not enough to cross from 1.9.
- It would be reported as "working, no memory" or "working, not a latch".
- Fix: use the champion's own median level duration at confirmed visits on the test worlds as the stimulus, and report the two-tick result beside it. Otherwise, register the wording for a working champion that fails at two ticks.
- Also run the release test on "bistable, not a latch" champions, descriptively; as written, their retention goes unmeasured.

**c. Zero turn offset holds at generation 0 and for one generation only (must state).** `p_mutate` is 1.0, so every child gets independent noise on all four biases and all four gate edges.
- A CL/CR mismatch δ gives a turn offset of about 5.9 δ (2 tanh(b_t + 3δ)).
- The bias noise alone (0.05 × √2) gives an sd of about 0.42 per module, before the gate edges add more. That is against a carrier turn of 0.2 and a clip at 1.
- So most generation-1 children carry offsets of the size Astra's 83.5% described. Only the 3 elites keep the balance.
- The route to the gate also needs each pair's biases to move about 38 sigmas while staying matched to about 0.03.
- This is a legitimate design choice, but the text reads as if the balance problem is solved. Say it, log the offsets per generation, and add "with untied mutation at 1×" to the 0-of-8 wording.

**d. The initial distribution contains no working selector (wording).** With |gate| ≤ 0.5 and |w_qq| ≤ 0.5, q is monostable and the gate swings a comparator's operating point by about 1 at most (gain ratio about 0.4).
- The random-sampling arm (1.7 h) and the GA-distribution census are therefore near-certain zeros.
- S2-b's "evolution better" then means "better than its own starting distribution". Register that reading, or draw random sampling from the tied uniform-over-bounds distribution.

**e. "Exactly" open loop is true as dynamics, not bitwise.** q, RA and RB form a closed subsystem driven only by the levels in Stages 2 and 3, so the claim holds. Under rule 6, do not claim bit equality across batch compositions. It does not hold for B-task, where edges into q are free; the classes rightly exclude it.

**f. The component tests at m = 0.005 pass trivially.** The noses are linear there, so K_D is flat at about 35.6 below m = 0.05. The extension is harmless, but it does not qualify far starts; the Stage 1 gate and the clamp assays do that. Say so.

**g. Spawn caps:** sound. The script still omits the world's clip, which is inert here.

## 4. What the pre-registration must pin

- **Settling and switching windows** as functions of τ_q, and the hold's q reference (3a).
- **The level duration** for the settable and release tests, and the wording when a working champion fails them (3b).
- **Which signal "a level for goal X" means:** `at_` of the other source, by task semantics and not by q's sign, so that mirrored champions are tested correctly.
- **The fixed-point count:** the root-finding method and tolerance near the fold.
- **Monostable clamp values when a goal phase never occurs** on the test worlds (no median exists); the design covers only medians that differ by less than 0.1.
- **The 0-of-8 and S2-b wordings** from 3c and 3d.
- **B-task's initial draws** for the 121 internal and 32 output edges. If the output edges are not drawn antisymmetric, its generation 0 has offsets and the tie is moot.
- **Carried from v2.2 and still open:** the geometric maximum, the blind policies' settings, B-shared's wiring, the world-block spans, and the reset test's timing and pass rule.