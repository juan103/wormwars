## 1. Verdict: proceed to pre-registration, with four must-fixes carried into it

All four are text fixes and none needs a new design round. The first is a real defect: as written, the engineered organism fails its own hold test. I ran nothing; the numbers below are hand estimates, or read from the design and committed files.

## 2. v2.1 items

All are resolved in substance. I rechecked these against files:

- **Budget:** the ten batches took 4 876–5 151 s (1.354–1.431 h). The scalings (1.2×, 2.0×, 3.2×) and the 13.4 h sum check out.
- **Geometry:** the JSON matches the design's numbers. The script omits the world's clip to [1.2, 22.8], which is inert here (spawn extent 1.35–22.69).
- **No-latch control, clamp values, S2-b's ordering, reductions reaching the minimum, the −0.2197 correction:** done as mapped.

Two are resolved only in part, both covered in §3: the hold timing (Astra) and the "start near the ungated pair" claim.

## 3. New problems in v2.2

1. **The hold test's reference is taken mid-transient (must fix).** The hold starts as the head leaves the source, and q must stay "within 10% of its value at the start of the hold".
   - At that moment q is still switching: about ∓0.22 after a one-tick level, and up to about ∓4.9 after a longer stay, by the design's own cue numbers. It then settles at ∓1.915.
   - So the engineered organism fails, and every bistable champion lands in "bistable, fails hold".
   - Fix: take the reference after a settling window (20 ticks, by the design's cue numbers), or compare tick 600 against the champion's own fixed point.
   - The tick indexing also needs pinning. If "first tick after the head leaves" suppresses the last delayed level, a one-tick visit never switches the latch (Astra's v2.1 point, still open).
   - K_D "at tick 600" in a closed-loop episode is undefined. Say it is an open-loop probe from the snapshotted state. Give the inactive K_D an absolute or ratio limit; "within 20%" of about 0.06 is noise.

2. **The clamp-to-B assay meets an uncapped B (must fix).** The Euclidean cap is on A only.
   - By the script's own counts, about 11% of uncapped draws put a source more than 16 from the spawn (8.80M against 7.85M accepted). B's share given the cap on A is not computed, but it is likely similar.
   - In those worlds B's scent at the spawn is below the qualified m = 0.02, down to about 0.0006. The 90% first-entry threshold for "clamped to B" is therefore at risk for reasons unrelated to memory.
   - Fix: restrict that assay's denominator to worlds with |B − spawn| ≤ 16, or draw assay worlds with both capped. State how worlds with no entry count. Have the script report B's scent too.

3. **"A run starts close to the no-latch control" is not true of a typical draw (must fix the claim or the distribution).** The four comparator biases are untied, N(0, 0.5²).
   - A CL/CR mismatch δ acts like a nose difference of about δ/6 (`module.json`: nose→comparator ±3). The mismatch's sd is about 0.7, so the equivalent nose difference is about 0.12, at or above the largest real gradient signal.
   - Generation 0 is thus an ungated pair with large random turn offsets.
   - Fix: either draw the comparator biases much tighter (near the mutation scale, 0.05), or reword the claim and report generation 0's K_D and turn offsets from the census.
   - The target is also far in mutation units (`w_sigma` 0.08, `bias_sigma` 0.05): the gate biases are about 38 sigmas away, and w_aq and w_bq about 30. That is reachable in 300 generations only under steady selection. The 0-of-8 wording should name "300 generations at these sigmas" as well as the distribution.

4. **"Bistable" reachability is tested by the wrong stimulus (must fix).** A static hysteresis sweep passes a champion with τ_q = 20 that a real 1–3 tick visit never switches.
   - Fix: define reachability by the release test's two-tick level, from each stable state.
   - Once item 1 is fixed, the hold test is near-tautological for a bistable q, because the selector has no other inputs. Say it is a consistency check.
   - The release test needs its starting state pinned for monostable champions.

5. **The other points you asked about are sound.**
   - **No-latch control and q-zero ablation:** correct as built.
   - **B-task:** free parameters are now countable (121 + 18 + 32 = 171) and the reading is acceptable as descriptive. Under reduction step 1 it has 300 generations and should be read against Stage 2's champions, not Stage 3's.
   - **Geometry script:** correct, but its minimum scent is a tautology of the rule (it cannot fail). The acceptance rate is the real check.
   - **Reduction order:** sensible, and it reaches the minimum. With 4 pairs, S2-b's bootstrap is close to a range and should be labelled descriptive.

## 4. What the pre-registration must pin

- **Hold test:** the settling window, tick indexing, the open-loop K_D protocol and the inactive limit (item 1).
- **Clamp assays:** the denominator, and how no-entry worlds count (item 2).
- **The selector's comparator-bias distribution,** and the reachability stimulus (items 3 and 4).
- **Which genomes the GA validates at the final checkpoint.** Random sampling validates its top 32; the GA should validate its final 32 too, or S2-b compares unequal selection.
- **Census ordering.** Qualifiers get "the full check on the test worlds", yet the test worlds are untouched until champions are chosen. Run that check after all champions are frozen.
- **S2-b when neither arm has a working selector.** "As good" must read as "neither found one".
- **B-task:** whether gap conductances are free, its champion rule, and its comparator under reduction step 1.
- **The reduction trigger:** the margin against the cap, and what happens if the minimum still exceeds it.
- **Scope of the classes:** Stage 2 champions only, or Stage 3's as well.