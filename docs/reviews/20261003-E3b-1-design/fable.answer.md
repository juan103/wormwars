I've finished reading the design, the E3b-0 results, power and timing records, the Stage 3 tuning code, the lockstep evolve loop and the maze world's trail-access code. Writing the review now.

## Verdict: proceed to the pre-registration, with fixes

The design is sound in outline. The pooled gate is defensible, the compute arithmetic reproduces, and the power figures match `power.json`. Several things are ambiguous or missing and would make the result hard to interpret if left to the pre-registration to improvise.

## Checks against files

**Compute (§5).** From `timing.json`, 0.0565 s per tick at 4,096 worlds gives 1.38e-5 s per world-tick. I reproduce the table:

| Item | Episodes | GPU-h |
|---|---|---|
| T-A: 8 × 125 × 32 × 16 | 512,000 | 4.71 |
| T-F: 8 × 300 × 32 × 8 | 614,400 | 5.65 |
| N: 6 × 125 × 32 × 16 | 384,000 | 3.53 |
| Validation: 30 × 4 × 128 | 15,360 | 0.14 |

Training 13.9, with reserve 17.4. Correct. Two caveats the retiming must settle: the figures assume each arm runs as one lockstep batch (T-A at 4,096 worlds matches the timed composition exactly; T-F at 2,048 and N at 3,072 will be less efficient per world), and the test evaluation of 31 organisms × 256 mazes cannot be one batch (4,096 worlds took 1.2 GB), so declare the chunking.

**Power (§2).** `power.json` `fine`: 12 runs at CV 0.282 gives MDE 0.22 (normal) and 0.20 (empirical) under the t-test. 16 runs gives 0.19 and 0.18 at CV 0.282, and 0.18 and 0.17 at CV 0.267. The design's "0.17-0.19 at a CV of 0.282" is slightly off: 0.17 belongs to CV 0.267. Trivial, but rule 5.

**A gap in the power file.** The gate requires the exact sign-flip test to agree, but the `fine` block has no sign-flip entry for 16 runs (the script skipped it: 65,536 patterns). Add it before the pre-registration; it is cheap to compute in chunks.

**What the MDE means in visits.** 0.18-0.19 of the seed's 5.78 is about 1.0-1.1 visits per wey. That is the size of E's entire contribution over the blind wall-follower W2 (+1.09). The gate is powered to detect a tuning gain as large as E's own design contribution, not a modest refinement. The pre-registration should say this plainly, because it governs how "unclear" is read.

## The open questions

**1. Pooled gate: yes, keep it, with wording fixed.** Under the null "neither schedule improves on the seed", each difference is symmetric about zero and the sign-flip test is exact regardless of between-arm heterogeneity; the t-test is adequate at n = 16. What pooling tests is the average effect over the two schedules, so register the claim as "tuning, under the two schedules run" with no attribution, and report each arm's 8 differences with intervals beside it. T-A alone at 8 runs (MDE 0.27-0.28) would be a worse gate. Sign-flip agreement is the right guard; keep it. Also define "worse" symmetrically (mirror t and mirror sign-flip) and state that the two one-sided tests make 10% total.

**2. Margin: none in the test.** A shifted null at 0.10 of the seed's mean would cut power for a true 0.25 effect to roughly that of a 0.15 effect (0.65-0.74 at 16 runs). Instead register the one-sided 95% lower bound of the mean difference and an interpretation scale fixed in advance: the gain in units of E's contribution over W2 (1.09) and of the seed-follower gap (11.6). The v2 sketch also promised "a minimum repeated-journey criterion"; either register one (for example the champion's median legs per wey at least 2, the seed's being 3.56) as a sanity condition or drop it explicitly.

**3. Champion rule: ambiguous as written, and not what the code records.** `evolve_batch` logs only the generation-best genome's fitness and checkpoints only the argmax genome; there is no per-genome fitness history, and most genomes in a final population have one generation's score (`wormwars/e04a/evolve.py:149-177`). "Top 4 by their last 5 generations' training fitness" therefore has no defined meaning for non-elites. Register instead: the generation-best genome of each of the last 5 generations before the read point (121-125, 296-300), each scored on the 128 validation mazes; champion by best validation mean, ties to the earlier generation. With 8 training mazes per genome the training best has a standard error near 26% of the mean (between-maze CV 0.74), so the 128-maze validation (about 6.5%) carries the selection. Two read points are adequate. Add a cheap honest learning curve: validate the generation-best on the 128 mazes every 25 generations (roughly 0.05 GPU-h in all). It removes the winner's curse from the training curves and partly stands in for a positive control.

**4. N as "none": correct.** In `wormwars/e3/maze_world.py:276-313`, "none" leaves both sensed components at zero while deposit continues, so every wey's behaviour is identical to deposit-off. State one consequence: under N the trail-sensing edges of E drift without selection, so an N champion "with trails on" has a random trail response. That is what makes it a control.

**5. S-trail: visits per wey as primary.** It decomposes the gate exactly: (T on − seed on) = (T off − seed off) + [(T on − T off) − (seed on − seed off)], locomotion gain plus trail-use gain. Register that decomposition. The later-leg rate stays secondary for continuity with E3b-0.

**6. Missing.** No separate positive-control arm: T against the seed with trails off, plus the learning curve, already tells whether the GA improves anything. Memory assays at D = 141 are descriptive and low priority. The deposit-off arm is covered by N.

## Must fix before the pre-registration

- **Maze ID blocks.** Training, validation (128) and test (256) blocks are not named. They must be disjoint from each other and from E3b-0's selection block. The test block should not be the report block 1000-1255: the seed's numbers and the +1.09 reading that shaped this design were taken there. Use the reserved fresh block or a new one, and recompute the seed on it.
- **The check at generation 125.** State that it is read-only: T-F runs to 300 whatever it shows, and no compute is reallocated. Otherwise the gate's composition depends on data.
- **The frozen set needs its own mask and assertion.** `stage3_scales` mutates every grafted edge and node except the relays' τ and bias (`wormwars/e3/samplers.py:128-140`), which would include W2's neurons and edges. The pre-registration should name the new mask and an end-of-run assertion in the style of E3a's `assertions`.
- **The cut order deviates from the E3b-0 plan's registered one** (generations, then worlds, then horizon). v1 cuts N to 4 runs first, then T-F to 250 generations. Allowed, since N is already descriptive, but say so openly.
- **Small statements to add:** the initial population is 32 copies of the seed, as in E3a's Stage 3; the seed's test scores are recomputed in E3b-1, not carried from E3b-0; what happens to the labels if the observed run-level CV exceeds 0.282 ("unclear" is then read as underpowered, which §4 already gestures at).