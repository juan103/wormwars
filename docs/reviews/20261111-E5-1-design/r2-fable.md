**Verdict: fix then proceed.** No redesign is needed. Draft 2 introduces three problems that must be fixed, and it leaves the interval choice open in a way its own check cannot settle. A third full round is not needed; these can be checked at the pre-registration review.

I ran nothing and have no shell, so I could not run `git show ae959a8`. I compared draft 2 against my archived review and §12.

## My round-1 must-fixes

- **M1 (mixed world): met.** One gap: §7.2's CPU-against-CUDA score check is "per setting". Add the mixed world at the training shape; only the composition check touches it now.
- **M2 (gains): met.** "G0 is also measured at each graph's calibrated gains (minutes)" does not say which strains or worlds.
- **M3 (the host may add little): partly met.** A0 and the lesion exist, but the reading against the anchor is one sentence for one branch, with an undefined comparison (item 1).
- **M4 (B's start): met.**
- **M5 (pilot rules): partly met.** δ, counts and generations are fixed without the contrast. The replacement stop rule still almost cannot fire (item 3).
- **M6 (O1's rules): met.** "The latent between-graph SD" needs its estimator, and what is reported when it comes out at zero (Δ over it is then undefined).

Three of Astra's items also fall short:
- **Astra 6:** the simulation has normal scores, one run SD for both arms, and no failed runs or graphs.
- **Astra 7:** the composition check uses genomes that mostly do not score.
- **Astra 16:** D389 is still cited, and `DECISIONS.md` still ends at D388.

## New must-fix

**1. A0's reading does not follow from A0's construction.**
> "If neither G-N2 nor G-SHr exceeds A0, 'the host's wiring adds nothing measurable to the graft under this design, and O1 compares how much each host interferes.'"

- "Exceeds" has no statistic, interval or rule for 8 runs against 32 and 80.
- Only one branch is written. There is no sentence for both arms exceeding A0, or for one.
- A0 starts from `carrier_genome` at forward 1.0 and turn 0.2, E4s-0's qualified carrier. It scores 3.01 on the suite before any evolution, above E4s-1's champions at 2.85. G-N2 starts from 32 random hosts.
- So A0 differs from G-N2 in two things at least: no host weights and a hand-qualified start. "Neither exceeds A0" at 500 generations can be the head start alone. This is partly my fault: I recommended the carrier start.
- Minimum fix:
  - define the comparison (difference of arm means, 90% interval);
  - write all three branches;
  - reword to what it shows: neither host, evolved from random backgrounds, exceeded the wiring-free carrier evolved for the same budget;
  - rest the wiring claim on the lesion.
- Recommended: add a like-for-like anchor of 8 runs (2 batches, about 1 to 2 hours): G-N2's own `embedded_population` draw with host weights zeroed and pinned.
- Also state whether A0's generation 0 is 32 identical copies, and that "host-to-host weights" covers gap junctions (`g`) as well as `w`, in the mask and in the lesion.

**2. §6 removes units for a failure that good hunters cause.**
> "A technical failure (a crash, a non-finite state, a ledger outside tolerance, a target sequence exhausted) reruns the batch once from its seed on the same code. A second failure removes the batch's unit"

- Exhaustion happens when a hunter uses all 64 centres (`config.py:168`, `hunt.py:279`), through captures and skipped entries. It is caused by scoring well and is deterministic, so the rerun repeats it and the removal drops a unit for its performance.
- `_capture` clamps silently (`nxt.clamp_max(K - 1)`); the error is raised only in `hunt_events()`. A GA rollout that reads `captures` alone would train on a prey respawning at the last centre.
- Fix:
  - exhaustion is a design error: stop and amend, never remove a unit;
  - the GA rollout checks `_overflow` every rollout;
  - §7 reports the highest sequence index reached, and the pre-registration requires headroom (I suggest at most half of K).
- Raising K looks prefix-stable in `_build_targets`, since centres are drawn in order. Test it.
- A non-finite state on one graph may be a property of that graph. Register a bound: recompute O1's label with removed units set to the arm's lowest and highest completed values, and say if it changes.
- "On the same code" covers the rerun only. Say what happens to completed batches when the failure is a bug.

**3. The pilot's stop rule passes under pure noise.**
> "Stop if, in fewer than 3 of the 4 populations, at least one strain's module-only `mean` contrast has a 90% interval above 0"

- Each population has 32 strains, each tested one-sided at 5%. With no signal, a population passes with probability 1 − 0.95³² = 0.81, and 3 of 4 pass with probability 0.83. This treats strains as independent, so it is approximate.
- Fix: pick each population's 3 elites on its actual 8-world training batch, then test their contrast on the 256 fresh worlds. That has no multiplicity and tests what selection would use. Alternatively keep the rule at a Bonferroni level.
- The signal probably exists: M run 0's generation-0 contrast on Task N was 1.72. The gate should still be able to fail.

**4. The interval is not chosen, and the Welch check cannot choose it well.**
> "finds the Welch interval's coverage nearer 90% over the whole grid"

- Under normal scores the result is foregone: Welch is near nominal there. The bootstrap's 86 to 90% is the usual small-sample shortfall of a percentile interval at 20 and 32 units.
- "Nearer over the whole grid" is not a criterion: it does not say mean or worst cell.
- The cases that matter are not simulated. A few SH-route graphs where L1 does not work would give 20 skewed graph means.
- Recommended: register Welch on the 32 run scores and 20 graph means now. It needs no resample count or seed. Report the percentile bootstrap beside it.
- Rerun the simulation with unequal run SDs, 10 to 30% dead graphs, and the minimum complete set (28 runs, 18 graphs). Report worst-cell coverage for both intervals.

## Should-fix

5. **The CUDA gates are equivalence tests of unknown power.**
   - "Pass if the 90% paired interval of CUDA − CPU lies within ±0.10 for each" depends on σd, the SD of the per-world paired difference, which nobody has measured.
   - On 1 024 worlds with no true difference, one interval passes with probability 0.88 at σd = 1.0, 0.37 at 1.5, and never above 1.95. All 25 must pass.
   - Measure σd on a separate block first, then size the worlds by a stated rule.
6. **The composition check is nearly vacuous.**
   - Its "16 + 16 genomes" are generation-0 genomes near the floor. Use the 16 E4s-1 C champions and pilot-evolved null champions.
   - Step 2 needs "a scoring grafted SH-route genome", which does not exist until step 5.
   - The formal suite is 512 worlds per setting and the check uses 1 024. State the formal evaluation's composition (mixed or per setting) and validation's, and check those.
7. **N2's batches are a free placebo.** On the null side a graph is also a batch. Report N2's between-batch SD over its 8 batches with the same estimator.
8. **§7 no longer leaks the evolved contrast.** What remains:
   - steps 4 and 5 put generation-0 numbers for both sides next to each other;
   - the owner's cap is set afterwards, and it decides cut (4), 20 graphs or 16.
   - Fix the cap from the bench before steps 4 to 6 are read, and name the four graphs that would go.
9. **500 generations is acceptable** as a budget-conditional endpoint, which the companion sentences state. But "shows whether the gap is still closing" has no statistic. Register one, for example the change in validation Δ from generation 300 to 500 with its interval and a fixed sentence. Report C's generation by arm.
10. **Weighted fitness: no bias, but say the cost.** One static world carries a third of the weight. With equal per-world variance, that is 59% of the fitness noise, and 1.5 times the variance of an unweighted mean.
11. **The equivalence sentence undersells.** "No difference … was found" reads like the inconclusive one. The rule shows that a difference of 0.25 or more is excluded in either direction.
12. **Arm P.** Permuting weights over N2's edges may break SH-route's caps on direct food-to-read-out weight. Report N2perm4 to 6 against the caps. I did not find N2perm's builder, so this is unchecked.
13. **Seeds and ids are clean:** no other `.py` or `.md` uses the 985-million block or the 1 51x 000 seeds. Still missing:
    - the world seed for training, validation and evaluation;
    - which 2 pilot graphs evolve;
    - the explicit admission list ("proportionally" is not one);
    - records keyed by arm, since B run i shares G-N2 run i's seed.
14. **`stats.label` returns "inconclusive" for NaN inputs.** Refuse non-finite values, with a test.

## Numbers checked

| Claim | Source | Result |
|---|---|---|
| Simulation table, all four rows; 38%, 78%, 64%; coverage 86 to 90%; 10 to 14% | `design-power.json`, `power-log.txt` | Correct |
| Suite scale 2.85, SD 0.23, 3.01, 0.76, 0.11 | `design-power.json` | Correct |
| E4s-1's curve 2.22, 6.86, 7.08; 95% by 500 | `eval-training.json`, 16 M runs summed by hand | Correct (2.224, 6.860, 7.079; 95.5%) |
| 03r gains: N2 2.08, SH-route median 2.95, N2perm 2.92 to 3.07 | `supplement.json` | Correct |
| E1's 3.04 s and 4.68 s; 3.35 s per generation; 0.47 h | `freeze.json` | Correct |
| Cost rows and totals; 2.58 M, 3.03 M, 393 216; 28 to 40 h | arithmetic | Correct |
| "about 0.8 M" for lesions, bridges, O0, references | my tally | Holds only without the lesion: on the suite it adds 1.29 M episodes |
| Graph names 1020000 to 1020019, 1020020, 1020023 | 03r manifests | Present (1020021 and 1020022 not checked) |
| Sabotage and first failure | `runs/e5-1/` | Sabotage is a real assertion failure; the first failure is an import error |

Not rechecked this round: E4s-1's batch times and the motionless hunter's 0.21 to 0.26.

## Before a pre-registration

Settle items 1 to 4, the world seed, the admission list, the lesion's worlds, the evaluation composition, and D389.