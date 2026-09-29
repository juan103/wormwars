**I still recommend revision.** The main unresolved issue is equal-work accounting; the ES update and decision rule also remain incomplete. I checked v2, both archived reviews, the roadmap, 04a’s code and corrected results, and E1’s throughput record. I executed no project code or tests and changed no files.

**On the tuning-charge disagreement:** I prefer the method-level allowance with shorter formal ES runs. It directly implements the stated resource constraint.

Fable’s alternative is acceptable for a **budget-limited primary comparison**, provided the eligible prefix has exactly the same algorithm and checkpoint schedule as a truncated run, its champion is locked independently of later results, and the extension has a separate descriptive budget. All extension work must still appear in actual compute totals. Full-length ES runs plus tuning cannot be described as equal *total additional E2 work* merely because later checkpoints are ineligible.

The following previous requirements are addressed at the design level: random sampling retains intervening candidates; ES encoding, projection, initialization, tie utilities and weight decay are specified; tuning has replication; formal evaluation compositions and champion freezing are stated; E3’s interpretation is appropriately provisional; and equivalence/update tests are planned. The corrected 4.67-second throughput agrees with [E1’s record](D:/Claude/random/wormWars/experiments/E1-navigation/freeze.json:493).

My **must-changes** are:

1. **Correct the arithmetic and define an actual complete allowance.**  
   [The tuning section](D:/Claude/random/wormWars/docs/E2/DESIGN.md:98) does not support “about 780” formal generations:

   ```
   Pilot training: 15 × 200 × 256 = 768,000 episodes
   Remaining per formal run:
   (8 × 256,000 − 768,000) / 8 = 160,000 episodes
   Equivalent training generations: 160,000 / 256 = 625
   ```

   That excludes separately charged initialization screens and evaluation work. Moreover, 15 pilot runs assumes reusing the three trials at the selected σ and rate 0.3σ. Rerunning that setting in stage two gives 18 pilots and **550** formal generations before other charges. State the reuse rule.

   Listing validation, probes and diagnostics in a ledger does **not** resolve how they count toward equality. Pilot selection adds work; shorter formal runs have fewer checkpoints. These costs do not automatically cancel. Define the total per-method allowance, charge initialization and tuning selection, account for the evaluation schedule, identify shared controls, and state rounding or unused-budget rules.

   Freeze pilot batching/chunking too, and recompute the runtime projection from the resulting schedule. This remains an unresolved v1 must-change, contrary to the last section’s claim.

2. **Finish the ES update specification and strengthen the flat-batch test.**  
   [“Specified completely”](D:/Claude/random/wormWars/docs/E2/DESIGN.md:74) is premature. The gradient estimator’s normalization and ascent sign, Adam ε and bias correction, noise/rate schedules, and checkpoint timing relative to updates are still unstated. These were explicitly requested in v1.

   There is also an implementation trap: **zero gradient does not imply zero Adam movement after earlier nonzero gradients**, because momentum persists. Specify what an all-tied batch does to the mean, moments and optimizer step counter. Test a non-flat update followed by a flat batch; a flat function tested only from fresh optimizer state misses this failure.

   Reconcile generation counting with the inherited GA: [`evolve_batch`](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:127) evaluates generations 0–999, validates generation 0, and breeds only between evaluations. State where ES’s initial screen, first update and final checkpoint fall in the charged sequence.

3. **Make the decision rule internally consistent and complete.**  
   [The current rule](D:/Claude/random/wormWars/docs/E2/DESIGN.md:125) says “both challengers qualify” while prohibiting random sampling from being chosen. There is now only **one eligible challenger: ES**. Remove the obsolete multiple-challenger branch.

   Specify that an incomplete GA reference prevents a replacement decision; “an incomplete method cannot qualify” does not cover the missing baseline.

   Express the random-floor diagnostic trigger explicitly—for example, `random_mean ≥ GA_mean − 0.5`. “Within 0.5” could otherwise exclude random sampling beating GA by more than 0.5, which should also trigger diagnosis. State that this diagnostic requirement takes precedence over proceeding to E3, even if ES clears its switch threshold.

My **suggestions and minor corrections** are:

- Change “32 directions” to **16 independent directions, evaluated with both signs** at [line 91](D:/Claude/random/wormWars/docs/E2/DESIGN.md:91).
- The claimed dated roadmap amendment is absent: [ROADMAP.md still specifies three runs](D:/Claude/random/wormWars/ROADMAP.md:161). Add it before registration, or describe it as pending.
- Pair initialization and world schedules across pilot settings where feasible. Also report all-tied batch frequency alongside clipping rates.
- Treat the power statement as conditional on assumed ES variability. GA’s observed spread does not establish ES’s spread or failure rate.
- Adding probes permits assessment of cue dependence; it does not by itself make a higher count evidence of **better cue use**. Keep that interpretation conditional on their results.

The ENOMAD wording incorporates the requested corrections. I independently reconfirmed signed initialization in the [authors’ loader](https://raw.githubusercontent.com/dsb-lab/C_Elegans_Training/V2_FINAL/celega/Non_Biased_Dynamic_C/util/read_from_xls.py) and shaping in the [preprint](https://arxiv.org/html/2508.09618v1). The journal full text was inaccessible in this pass, so I have not independently reverified its version-specific numerical details.

**E2 design: revise**