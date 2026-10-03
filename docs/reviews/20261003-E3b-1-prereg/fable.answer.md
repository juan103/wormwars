**Verdict: bind after fixes.** The pre-registration carries design v2 and pins 2 through 11 faithfully. Pin 1 is not carried, and a handful of rules need one sentence each to be computable without a post-hoc choice. None changes the design, so no further round is needed if the fixes below go in as written.

## What I checked and confirmed

- **Hashes.** All nine fixed inputs match at HEAD (95800aa) and in the worktree. Table in §2 is correct.
- **Budget.** From timing.json (0.056528 s per tick at 4,096 worlds, H 2,400): T-A 4.711, T-F 5.653, N 3.533, R 1.178, total 15.07; validation 1.206; total 17.49; with training × 1.25, 21.26. §10 is right to its rounding.
- **Gate formula.** Matches `scripts/e3b1_power.py` exactly: SE = √(s_A²/8 + s_F²/8)/2, Satterthwaite df, one-sided p. The three labels are exhaustive and unambiguous.
- **Read points against `wormwars/e04a/evolve.py`.** `generations=125` runs indices 0 to 124, and breeding is skipped at the last index, so `rec.final` is the population evaluated at index 124. §6 is correct. The index-124 snapshot for T-F needs the new hook, which §5 and §11 register. The checkpoint champion (`RunRecord.champion_index`) is correctly declared unused.
- **Mutable set.** Matches `_grafted` and `stage3_scales` (edges with a grafted end; nodes except the relays) plus the new W2 freeze. `reflex()` has two neurons with eight output edges each, so "16 output edges" is complete.
- **Degraded start.** `organism.no_latch` exists: comparator biases and gate edges at 0 on E's mask, as §2 says.
- **Replay rule.** `maze_runs.replay_donors` is "from 1000 up, advanced until A or B differs", matching §6 at episode 0.
- **Secondary tests, roster, Holm, "not read", reruns, cuts order.** All as pinned in "v2, as confirmed" items 4, 5, 9, 10 and the design §6.
- **Equivalence reference.** The 84ff98a reference exists (E3b-0 RESULTS, development-records).

## Fixes before binding

1. **Pin 1 is missing: there is no power section.** The prereg lists power.json as an input but states no MDE, no false-positive rate, and not the scope caveat. Add a short section: MDE 0.19 at CV 0.282, 0.21 with unequal spreads, 0.27 at CV 0.40; false positives 4.4 to 5.3% in every scenario; the caveat that 0.282 was simulated as the SD of d at every effect, and if the CV holds at the tuned mean the MDE is nearer 0.22 to 0.23. Scope the pooled-t and sign-flip 5.0 to 5.5% and the shifted-null 0.28 to 0.31 to CV 0.282. §7's "10% reference" otherwise has nothing registered to refer to.
2. **The admission formula contradicts pin 11.** §9 applies × 1.25 to the remaining non-training stages and not to the training stage being admitted, while the planned-total rule and pin 11 put the reserve on training only. Write one formula and use it in both places. I recommend: hours spent + the stage's projection × 1.25 + remaining non-training projections ≤ 22.
3. **Champion validation's access mode is unstated.** N's champions can be picked under "none" or "shared", and this changes the N against T-A reading. Pin it as each arm's training access (N under "none", the others under shared), at episode 0.
4. **Three denominators and conditions are implicit.** State that S-gen's paired difference is under shared trails; that S-peer's denominator is the seed's first-B time of later discoverers under "own", as a mean over the test block; and that the descriptors (seed − W2 alone) and (follower − seed) are under shared.
5. **Cut 3 moves a read point.** If T-F is cut to 250 generations, say the final read is index 249 and S-gen pairs 249 against 124.
6. **Learning-curve count.** `evolve_batch` also checkpoints at generation 0, so the curve has 200 points, not 176, and costs about 0.24 GPU-hours rather than 0.21. Trivial, but rule 5.
7. **"Its own t interval"** for each schedule's mean d: say two-sided 95%.

## Noted, not required

- The design's "S-trail secondary measure: the later-leg rate" is carried only as a general measure, not beside S-trail. Fine as descriptive, but say so if you want to keep the design's framing.
- The replay coefficient now comes from the calibration block rather than E3b-0's selection block. That is a stated departure in effect; adding it to §12 would be cleaner.