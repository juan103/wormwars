I've finished reading the design, both v2 reviews, the geometry script, the E4s-1 batch records and the engine code; here is the review.

## 1. Verdict: revise

The engineered organism, the budget and the geometry are sound. Three Stage 1–2 definitions are wrong as written, though, and they change outcomes, so I would not carry them into a pre-registration. They are text fixes; nothing needs to run. I ran nothing; the latch check is a hand integration.

## 2. v2 items

All are resolved, with one caveat: the spawn-distance fix guarantees a non-zero scent, not a usable one (see the geometry point in §3).

- **Budget:** checks out. The ten batches took 4 876–5 151 s (1.35–1.43 h) at composition [256, 8, 1], 300 ticks and 1 000 generations.
  - Stage 2 is 1.2× the tick count of one batch, so about 1.7 h; Stage 3 is 2.0×, about 2.8 h; the table sums to 13.3 h.
  - E4s-1's validation was [8, 256, 1], champions only. Twelve validations at 600 ticks cost less than the forty at 300 already inside the measured rate.
- **Relays and w_aq/w_bq as genome edges:** resolved. A self-edge q→q is allowed by `graft_connectome` and `BrainSpec`.
- **Latch switching with relay lag:** my hand integration gives q of about −0.35 to −0.4 after one tick, consistent with the design's ∓0.43. The relay's decay keeps driving for about 0.8 tick afterwards, so the lag helps.
- **Dtypes, latency, component protocol, contribution definition, cue, S2-c, Stage 3:** resolved.

## 3. New or surviving problems

1. **The "no-latch control" is not what it says** (`docs/E3/DESIGN.md:190`). With q clamped to 0 and the comparator biases at −1.914, both modules sit at an offset of −1.914, where the slope is about 0.08. That is both modules roughly 92% off, not "both always on". The Stage 1 gate "beats the no-latch control" is then nearly free. A true both-on control needs comparator biases 0 and gate edges 0.

2. **The classification misfiles real latches.** The hold test requires |tanh q| ≥ 0.9 and the absolute component limits (K_D ≥ 30). Those are the engineered organism's numbers.
   - An evolved bistable selector with w_qq = 1.3 has tanh q* of about 0.7. It would be bistable, working, fail the hold test, and be classed "no memory".
   - For champions, the hold should be relative: q stays near its own fixed point, and its own gate function at tick 600 matches its pre-hold value.
   - The classes also need a fourth cell, "bistable but fails hold".
   - Three fixed points with the relays at rest does not show both states are reachable by the levels. The hysteresis sweep does, so it should be part of the criterion, not only reported.

3. **Clamp assays for champions are undefined.** "Clamped to ±1.915" means nothing for an evolved q with other fixed points, or for a monostable trace. Yet "working selector" and "slow trace" both depend on passing them. The clamp values should be the champion's own, for example its fixed points or its median q per goal phase.

4. **B-task has no registered reading.** It takes 4.5 h of 13.3 h, and S2-a, S2-b and S2-c never mention it. Either give it a reading or cut it to the first shrink step by default.
   - Its initial distribution (121 edges uniform over ±3) will saturate all 11 neurons, so it is likely a strawman.
   - It is unstated whether its τ, biases and the 40 output edges are free.

5. **The selector's initial distribution makes a null likely.** `w_max` is 3 and `b_max` is 2. My rough estimate of the working fraction under uniform-over-bounds initialisation is about 10⁻⁶ to 10⁻⁵. It needs four comparators each with b ≈ −w·tanh q* and |b| above about 1, plus bistability, both drive signs, and the cue's polarity.
   - The census of 1 024 will almost surely find none, which is fine for S2-c.
   - "0 of 8" is then a probable Stage 2 outcome, and it needs wording that says "not found in this budget from this distribution", not "cannot evolve".
   - The engineered w_aq and w_bq sit exactly on the bound (±3), so evolution cannot make the drive any stronger than the engineered one.

6. **The geometry script is correct but checks the wrong quantity.**
   - It omits the world's clip to [1.2, 22.8], which is inert at W = 24 (the spawn extent is 1.35–22.69). The JSON matches the design's numbers.
   - "Within 16 on both axes" allows a Euclidean distance up to about 22.6, where the scent is about 0.0008. That is 25 times below the lowest level the component tests qualify (m = 0.02, about 16.8 cells). A Euclidean cap of 16 on |A − spawn| would be better, and the script should report the scent at the spawn.
   - It samples A and B jointly; the world's sampler must do the same or the acceptance rates do not transfer.
   - "Every spawn" in the design means every one of the 2 000 sampled spawns.

## 4. What the pre-registration must pin

- **The no-latch control's construction:** biases and gate edges, per point 1.
- **Champion-relative hold and clamp definitions,** the four-way classification, and the hysteresis criterion.
- **B-task:** its reading and wording, its free parameters (τ, bias, output edges), and its initial distribution.
- **Stage 2 wording for 0 of 8,** and for the mirrored-polarity solutions, which count as working.
- **The initial population:** 32 independent draws per run, and whether the census shares the distribution's stream.
- **The source sampler:** joint or sequential redraw, and the Euclidean cap.
- **The champion-selection rule:** which validation checkpoint supplies the champion, and that the test worlds are untouched until then.
- **The owner's cap,** and the projection rule that triggers the shrink order.