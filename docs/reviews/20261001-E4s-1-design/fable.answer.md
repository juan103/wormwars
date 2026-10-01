## Verdict: revise

The arms, seeds and budget are sound, so this is one text round, not a rethink. The must-fixes are in the readings. I checked the files named below; nothing was run.

## Must-fix

1. **O1 is not a manipulation check (Outcomes, O1).** M's generation-0 bests score a median of 2.06, and N after 1 000 generations should reach the plateau (2.19 across the 47 champions). M − N ≥ 0.5 therefore needs M to climb, which is the open question. Delete "close to a manipulation check: the graft works at generation 0"; the claim is inherited from the roadmap and E4s-0 has overtaken it.

2. **C2 is "unclear" in all 8 runs by construction (O2).** With E4s-0's numbers (real − mean lower bound −1.82), `classify` in `scripts/e2d.py` returns "unclear" for its G0, and all 32 copies are identical. Give C2 its own reading from signed effects (harmful, neutral or uses, at G0 and F), outside the table.

3. **R is often a harmful graft, not a neutral one (arms, O1b).** Random signs on the four nose edges make each comparator common-mode with probability ½, so many draws inject a scent-driven turn offset. M − R > 0 can then mean "R is worse than nothing".
   - Register R − N beside it, descriptively.
   - Record each draw's open-loop K_D and K_C at G0.
   - Word the claim as "designed signs against random signs".
   - Replace "cannot repair itself" with a measurement of R's final edge signs and magnitudes. The step is 0.02 per generation (`w_sigma` 0.08 × 0.25), so flips are unlikely but shrinkage under selection is not excluded.

4. **"Retained" says nothing about score (O2, and E3's swap rule).** A run can be D and Mc at about 2 targets. Under the roadmap's rule, 12 of 16 "retained" would then swap a genome scoring about 2 into E3 in place of the carrier's 5.18. Read the arm jointly with O2b, and add a score condition to the swap (for example O2b ≥ 0.9).

5. **Mc is tested only on the carrier at turn +0.2 (Measures).** A module that co-adapted to a host with a negative offset can become asymmetric and fail there while still competent. Test Mc at both +0.2 and −0.2 and take either, and report its carrier score as a share of L1's. The "uses" bar of 0.5 is weak against 5.18.

6. **The turn offset is measured confounded with steering (Measures).** The closed-loop mean turn command includes the module's response. Measure it also with d = 0 (module "mean" plus the world's mean probe), and keep the saturation share. Fix K_D's operating point at E4s-0's levels (0.02, 0.08, 0.25).

7. **"On 04a run 2 (turn −0.28) the graft was harmful" implies a cause (What E4s-0 changes).** RESULTS.md says the bias is not attributed, and the −0.28 was measured with the graft on. The comparator is symmetric, so the sign should not matter if the world is mirror-symmetric (I did not check that). Reword it.

8. **Gate 1's "about 1%" is wrong (Gates).** It treats 5.18 as the true mean. With the estimate's own error (SE about 0.04, pass needs a fresh mean of about 5.08 or more), a chance fail is about 4-5%. State that, and what "diagnosis" allows.

9. **Gate 3 is nearly vacuous for the 32 random genomes (Gates).** 398 of 512 random backgrounds score 0, so ±0.05 passes trivially. Use genomes that score, such as generation-0 bests from non-E4s-1 seeds. Also test N's actual construction (edges present, weight 0), not only `without_outputs`.

10. **Unpinned details.**
    - C2's run seeds are not given.
    - `module_scales` pins the host at 0; E4s-1 needs host 1× with module f×, a new function missing from "New".
    - State that arms sharing a seed share training worlds and mutation draws (`breed_seed`, `train_ids`): good pairing, but say so.
    - Add end-of-run assertions: N's 16 edges exactly 0, and F0's module bit-identical to L1.
    - "Batches of 8" against "M 1-8 with N 1-8": say this is two batches.

11. **O1's rules have no reversed case.** An upper bound below 0 (M worse) currently reads "does not support". Add "reversed".

**Should-fix:** "acquired" will mostly reflect which founder the 8 worlds picked (about 2.6 users per population), not acquisition. Report the population's user count at G0.

**Checked and fine:**
- The run count is 80 in 10 batches.
- The along-training generations are all checkpoints.
- The E2 hash gate passed (D144).
- The episode arithmetic holds (about 3.1 M, or 1.0-1.9 h).
- 24 h is a reasonable cap.
- The 1.35 h per batch I saw only in E2d's plan, not in a compute record.

## The four questions

1. **Ready?** Not yet; the items above. No new arm is needed.
2. **Turn offset:** record it, do not control it. A registered turn bias would change the hash-frozen module, give the graft a search function, and break N's comparability. Recording is enough if it is measured as in item 6, with a pre-stated descriptive split of M − N and class by G0 |offset|.
3. **S and the run count:** keep S. It is cheap, and with F0 it brackets the load explanation for "lost". Sixteen runs are adequate only for large effects: if M's outcomes are bimodal (SD about 1.3), the 90% half-width is about 0.55, so power is roughly 90% at a true effect of 1.0 and under 50% at 0.5. That is my rough arithmetic; state the limit in the design.
4. **Class table:** the order is logically fine, but not the reading. Fix C2 (item 2), Mc (item 5) and the score-blind "retained" (item 4). 12 of 16 is acceptable once "unclear" counts are reported.