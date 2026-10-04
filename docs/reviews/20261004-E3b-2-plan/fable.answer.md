I have everything I need. Here is the review.

**Bottom line:** the plan's partitions are correct against the code, and the budget is comfortable. Two lesions do not test what they claim, the latch recorder's threshold is wrong for champions with a nonzero latch bias, and the plan omits the one lesion that most directly separates the two mechanisms the decision cares about. Verdict at the end: go with changes.

**1. The partitions.** I checked them against `tuning.scales` and the modules. The mutable set is 47 edges (8 nose→comparator, 32 comparator→turn, Q→Q, RA→Q, RB→Q, 4 Q→comparator) plus τ and bias of 9 neurons (A's 4, B's 4, Q). Both partitions sum to 65 and cover every mutable parameter once, with nothing frozen included. The planned coverage test is still worth writing. On the cuts:
- Placing the comparator biases with gating is right for the seed, where bias −1.914 is the off state. It is a dual-role parameter in a champion: a bias near 0 also sets the comparators' resting activity, which times 16 output edges is a constant turn push. State this in §4, and add a free descriptive (see 6): the effective comparator bias under each latch state, bias + gate weight × tanh(q state), per champion.
- The relays' frozen parameters and the reflex cannot carry gain, so they belong in no attribution group. Correct to leave them out. A reflex lesion would likely strand every organism on walls and tell you nothing; its omission from D193's sketch should be stated in the plan.
- Comparator τ in sensing and comparator bias in gating splits one neuron across groups. Acceptable, but say so.

**2. The attribution method.** Groups of this size are the right unit; parameter-level reversions would cost about 65 chunks. The off-path worry is real but modest here: every champion's latch states sit near ±1.5 to ±2.5, so seed gates on a champion latch still roughly cancel. Still, add two guards:
- Report every hybrid's absolute score beside the seed and the W2-alone reference on the fresh block. Any hybrid below W2 alone is off-path and should be flagged where its Shapley contribution is discussed.
- Do not report per-champion shares for T-A. Its gains are +0.03 to +0.13 and a 256-maze hybrid mean has sampling noise of roughly the same size, so shares become ratios of small noisy numbers. Report Shapley values in the seed-mean units of d with maze-paired intervals, and shares only at the schedule level as sum of Shapley values over sum of gains. §8's fixed wording should say this.
- Reversion and transplant are the right companions and are the interpretable endpoints. Lead with them; the Shapley value is the average over the interior.
- The seed appears 16 times in A, once per champion's chunk, in the same composition. Use that as a free exactness check: the 16 seed score vectors must be bitwise equal.

**3. The lesions.** Two problems.
- "Latch frozen" by cutting the relay edges does not hold q at its start. The brain starts at zero, and the start cue reaches q only through RB→Q, which the lesion cuts. So q follows its own dynamics from 0, where the drift is set by b_q. From `evaluate.json`: 7 champions have b_q > 0 and settle at their A state, 9 have b_q < 0 and settle at B, and the seed has b_q = 0 exactly and stays at 0 for ever, which puts both comparators at −1.914 and silences both modules. The same lesion means three different things. Replace it with two lesions: relay edges cut and q started at the champion's own A state, and the same at its B state, using `StartedBrain`. Test that q stays within a tolerance of the state for the horizon. These clamps are the cleanest "selector removed" test, because everything else runs at the champion's own operating point.
- "Gate cut" is well defined as an operation, but on the seed it means "both modules off" (biases at −1.914 with nothing cancelling them), close to W2 alone. On a champion whose biases drifted toward 0 it means "both modules on". Keep it, but state the per-organism reading using the effective-bias descriptive above.
- Lesion 5, both outputs silenced, disconnects every grafted neuron except W2 from the worm. It is one organism for all 17, not 17. Run it once as the W2-alone reference, and say so.
- Add a "noses silenced" lesion: the 8 nose→comparator edges at 0. E3b-1 found saturated baseline turns for T-F finals 2, 3 and 7, which suggests a strategy of latch-state-dependent turn bias rather than stereo following. This lesion separates "uses stereo input" from "uses only the latch state", which is exactly what E4's information-crossing premise needs. Cost: about 2 chunks per trail condition.

**4. The latch recorder.** The mechanics are feasible from the hook: `world.v`, `world.goal` and `world.has_visited` give q, goal and first-visit per wey. Three fixes:
- sign(q) is the wrong split. Every champion has b_q ≠ 0, so its two states are asymmetric. Use the unstable middle root of the champion's own latch (from `latch.roots`) as the threshold.
- "|q| below the probe's separation threshold" is ill-defined. `MIN_SEPARATION` is a distance between the two stable states, not a band around 0. Define undecided as the middle third of the interval between the two states, or similar, and say so.
- Agreement alone hides a lag. The relays read the position after the previous tick's move, and q needs a few ticks to cross, so even the seed will miss some ticks after every visit. Report the seed as the reference, and add two per-visit measures: ticks from a confirmed visit until q crosses the threshold toward the new goal, and the share of legs where it never crosses before the next visit. Those answer "does the latch switch in the maze" more directly than a tick share. Reporting both codings is right; also check each champion's RA→Q and RB→Q signs, which define its intended coding for free.

**5. The mazes and the inputs.** Block 7000-7255 at seed 1 180 000 is disjoint from every block I can find: E3b-0's 0-255, 1000-1255, 2000-2255; E3b-1's 4000-4127, 4500-4627, 5000-5255, 6000-6255, training 10 000 000+, projection 9500-9755, and the trace's 9900-9902. The smoke range "9600 and up" overlaps E3b-1's projection ids 9500-9755. Not results, but pick 9800-9899 to keep the ranges clean. Reading `runs/e3b1/genomes` is read-only; have the runner refuse to write anywhere under `runs/e3b1` and write only to its own folder. The test block stays closed. Good.

**6. The reporting rules.** They avoid verdicts. Missing, in rough order of value to the decision:
- A short, explicitly non-binding "how the owner would read this" paragraph: if the selector's side share, the clamp costs and D's flip rate are all small, the engineered selector is not in use and both E3's assembly comparison and E4 lose their premise. Writing it now prevents reading it after the fact.
- N's 4 champions in C and D only, about 3 chunks. They say whether tuning without trail sensing also abandoned the selector. R's can stay out.
- The "none" condition for attribution is not needed; C covers it.
- Later-leg rate and median legs for the clamp and noses lesions, so a gain is not read from a one-leg colony.
- Free genome-level descriptives in E: relay→latch edge signs, gate edges, effective comparator bias per latch state, and the resting turn per latch state computed from the genome rather than only from the probe.
- Commit the full 16-hybrid and 8-hybrid tables per champion.

**7. Compute and drop order.** The projection is about 39 chunks; my additions bring it to about 48, under 2 GPU-hours against a cap of 5. Flip the drop order. B's selector share is the single most decision-relevant number, so drop C's "none" first, then halve the fresh block for B, and drop B last.

**Verdict: go with changes.**
1. Replace "latch frozen" with the two clamps at the champion's own states; test that q holds.
2. Add the "noses silenced" lesion.
3. Run lesion 5 once as the W2 reference.
4. Recorder: unstable-root threshold, a defined undecided band, flip latency and never-flipped share, the seed as reference.
5. Report Shapley values in d units with maze-paired intervals; shares at schedule level only; flag hybrids below W2 alone.
6. Add N's 4 champions to C and D; add the non-binding reading paragraph and the free genome descriptives.
7. Smoke ids to 9800-9899; runner refuses to write under `runs/e3b1`; flip the drop order.