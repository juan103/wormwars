## Verdict: proceed to pre-registration

No third design round is needed. The arms, gates and readings are now sound; what remains can be fixed as pins in the pre-registration text. I read the design, both v1 reviews, D148, E4s-0's records and the relevant code; nothing was run.

## 1. Are the v1 must-fixes resolved?

All of Fable's 11 and Astra's 7 are resolved in substance. Checks I made:

- **Power table:** it agrees with my own normal-approximation arithmetic for the exact rules (for example SD 1.3, effect 0.5 gives about 47%; SD 2.0, effect 1.0 gives about 65%).
- **Pairing:** `train_ids` and `breed_seed` depend only on the run seed (`wormwars/e04a/evolve.py:63-74`), so the claim holds. `evolve_batch` refuses duplicate seeds within a batch, and the ten-batch order respects that.
- **Edge counts:** L1 has 4 nose edges and 16 output edges, 20 in all (`wormwars/e4s/comparator.py:49-51`).
- **Ids and seeds:** the 942 M world block and the 1 160 000 seed block do not collide with E4s-0's 940 M and 1 150 000-1 151 000 (`scripts/e4s0.py:65-81`).
- **E3's rule:** the dated amendment is in `ROADMAP-PROPOSAL.md:338-341`.

Two are resolved only partly:

- **Power (both reviewers; rule 5).** I found no committed script or record for the simulation; the numbers appear only in the design and D148. It also assumes normal differences, while E4s-0 gives reason to expect bimodal outcomes. Commit the script and add one bimodal scenario.
- **Gate 3 (Fable 9).** It may still be weak for half its genomes. With bias 0, L1's output is exactly 0 when both noses get the mean, so N's construction is equivalent to the "module mean" probe. All 16 of E4s-0's generation-0 bests "use" the module, so their hosts alone score well below 2.06, possibly near 0. `populations.json` holds the per-world counts under each probe: compute their mean-probe means and keep only genomes that score. The 04a champions are fine.

A smaller point: the "1.35 h per batch" is still traceable only to E2d's `PLAN.md:318`, not to a compute record. The projection stage covers the risk, but call it planned, not measured, or cite the record.

## 2. New problems in v2

1. **O1c's M-against-N contrast is confounded at generation 0.** M and N share a population but not a G0 best: M's is picked with the graft live, N's without. The difference of climbs equals (F_M − F_N) − (G0_M − G0_N), and the second term is the graft's immediate benefit. A negative climb difference is therefore expected even if M ends higher. State this in advance, and report G0_M − G0_N beside it.
2. **"Does not support" covers a significantly positive small effect.** A lower bound above 0 with an upper bound below 0.5 gets that label. Word it as "does not support an effect of at least 0.5", or add a "small positive" case.
3. **Two unadjusted tests each give a false "supports" in 5-8% of simulations at zero effect.** The family rate is therefore about 10-15%. Say that number, not only "no adjustment".
4. **Gate 3 is a conjunction of 32 strict tests with no stated basis for ±0.05.** If closed-loop trajectories diverge in a few worlds, a chance stop is possible. Either justify the tolerance from E4s-0's data or state what a narrow failure means.

None of these changes an arm or a measure.

## 3. What the pre-registration must pin

- **Analysis constants:**
  - the bootstrap seed;
  - the interval level for every class (D, H, Mc, C2's "harmful");
  - that H and Mc use E2d's `classify` thresholds unchanged.
- **O2b and E3:**
  - whether "at least 0.9" is the point estimate or a bound;
  - that the chosen genome is F, as the proposal says, not C.
- **Worlds for the 256-world probes:** the final populations and the G0 user count have no block assigned.
- **The turn-offset split:** which m level defines the G0 offset, and from which arm's G0.
- **Open-loop probe:** tick count, settling window, start state, and whether module neurons are driven.
- **Gate 2:**
  - how 48 genomes fill each shape;
  - how the input histories are generated and seeded;
  - that only the 302 host neurons are compared;
  - the basis for 10⁻⁴.
- **Gate 3:** the exact genome list by sha256, after the check above.
- **R's draw:** the generator, the order of the 20 edges, no rejection of draws, and the draws' hashes recorded before training.
- **`arm_scales`:**
  - that τ and bias of module neurons take the module factor;
  - that N's nose edges mutate harmlessly;
  - how bound clipping interacts with the pin.
- **Failures:**
  - what happens to a pair if a run or batch stops (a non-finite score raises and stops the batch);
  - whether reruns are allowed;
  - the minimum number of pairs for O1;
  - what is reported if the cap hits before batches 7-10.
- **Mc transplant:** exactly which parameters move, and that the carrier's turn-neuron biases are the carrier's, not the host's.
- **Outcome wording:** all four O1 labels in full, including O1b's "designed against random signs" caveat, and the O1c sentence from item 1.