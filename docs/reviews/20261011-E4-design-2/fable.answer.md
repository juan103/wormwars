**Verdict: revise, but narrowly.** The architecture is now sound: the output gate, ungated comparators, frozen selector, 32 slots on one connectome, seed-paired runs and E4-D's ordering all hold up against the code. What still breaks is the reading layer. Four points would make a result wrong or unreadable as written, and all four are fixable on paper, with no GPU.

## 1. Were my required changes taken?

Yes, all eleven. The leak was measured before anything else and the decision recorded (D243). The clamp is gone and §4 reads per-mode leg durations. The shared connectome with slots at 0 and the exactness test are there. The subsets are correctly 16 sensory and 16 comparator links by source (my v1 count of 8 comparator links was wrong; v2's is right). The matched within-module cut is dropped rather than kept descriptive, which is better. P1 is primary with P2's minimum detectable effect stated, pairing is in, the gating check and the gene-duplication measure are in, E4-D is separate, and §9's facts check against E3c's ledger: the three new arms cost 16.85 h over 20 runs, which is the 0.84 h per run the design cites.

## 2. The new choices

**The output gate** is sound and closes the isolation gap completely. I checked the routes: the 8 module neurons have no outputs except the 32 comparator-to-motor edges, `graft_connectome` adds no gap junctions, Q receives only RA, RB and itself, and the worm block is silent and frozen. Gating those 32 edges leaves the inactive module no path to behaviour in X0. The leak script measures what it says. E-G's active module is numerically the seed's at rest, since the gate bias was chosen as minus two tanh of Q's fixed point, so re-qualification should pass. Two specification gaps, not blockers: the gate at q = 0 (the state starts at zero in `wormwars/brain.py:403`, so under "g_A = 1 while q > 0" the first substeps are B mode, harmlessly, since every comparator is also at zero), and "Q's 13 parameters" is ambiguous. `samplers.SELECTOR` at `wormwars/e3/samplers.py:30` counts the four comparator biases among its 13; the other natural set of 13 is Q's five, the four gate edges pinned at 0, and the relays' four. Say which, and give the mutable count per arm.

**Ungated comparators:** yes. Both kinds of information exist only because of this, and it costs nothing but the re-qualification.

**P1 by cut and mean substitution as primary:** right choice, with one defect that would inflate it (item 3 below) and one wording risk (item 4).

**The joint table:** not yet usable (item 1).

**The scale rule:** its aim is right, but it collides with Branch A and ignores the GA's elite copying (item 2).

**E4-D's ordering:** sound. A hand-built organism on the CPU is exploratory engineering; label it so, and note that E4-D's "own ceiling" needs the owner's word, since D198's 30 hours were E4's.

## 3. What to change

1. **The joint table does not match the statistics it is built on.** P2 has three outcomes under E3c's dual margin: beyond, no relevant difference, unclear. The table has only "positive" and "none". At the stated power (1.26 visits detectable at 8 runs against a margin near 0.67), "no relevant difference" is almost unreachable, so row 4 would read an "unclear" P2 as "no useful transfer evolved". Row 6 lets a failed E4-D positive control void a positive P1 and P2, when it can only void nulls. P1-cut appears nowhere, so "P1-cut positive, P1-info none" (a tonic mechanism) is filed as "mechanism unresolved". A negative P1-info (cutting helps) and failed competence have no row. Map all three P2 labels, both P1 readings, competence, and the sign of P1-info.

2. **Branch A's criterion is incompatible with the scale rule.** The rule picks the factor at which a neutral slot reaches |w| ≥ 1 within G generations. At that factor a neutral slot's final SD is near 0.8, and the 95% band for "every one of 32 slots inside" is about ±2.4, close to w_max 3. A functionally recruited link at |w| 1.5 sits inside it, so Branch A fires and a true P1-info is thrown away as "not read". The band is also miscomputed with k = G: `breed` copies elites unmutated (`wormwars/evo/evolve.py:77-90`), so a champion's lineage has fewer than G mutation events, and the pilot's X+ slots are under selection, not neutral. Define "recruited" functionally: the per-champion P1-cut effect outside the evaluation-noise band measured in the pilot. Keep |w| descriptive. Give the scale rule its quantile and compute drift from the lineage's recorded mutation count.

3. **Mean substitution runs into b_max.** The edit adds up to four links' mean drive to a target's bias, each up to 3 in magnitude, on top of an evolved bias already within ±2. `Genome.clamp_` clips biases at 2 (`wormwars/brain.py:252`, `wormwars/config.py:40`). A clipped substitution leaves a tonic residue inside "intact minus mean-substituted", a false positive for information. Declare that the substituted genome is built without `clamp_` (the brain reads `genome.bias` unclamped, so it runs), or show it never clips. Also fix: all 32 substituted jointly, the unconditional mean over ticks, weys and validation mazes of the intact champion, since a mode-conditional mean is not expressible as a genome edit.

4. **"Transferred information" can be the module's own signal looped back.** In X+, B's noses receive links from A, so A_CL ← B_NL ← A_NL is a two-hop delayed copy of A's own nose, a cheap temporal derivative evolution can find. P1-info would be positive with nothing of B's crossing. Pre-register the directional read from §4 as the qualifier: links into the active module cut against links out of it, on per-mode leg durations. Word the confirmatory claim as "the time-varying signal crossing the module boundary is used" unless the directional read supports "the other module's information".

## 4. Smaller fixes for the pre-registration

- Define P2's "paired interval" (t-based or inverted sign-flip).
- The 0.6 h per run at H 1 800 scales E3c's time by horizon only; the 6 × 6 arena has 1.4 times the cells. The pilot replaces it anyway.
- The sensory and comparator subsets are nearly redundant in content (a comparator is a saturated difference of the two noses). Read them separately as planned, but do not interpret a difference between them as "raw versus computed".

With 1 to 4 folded in, v3 can go straight to the pre-registration without another design round.