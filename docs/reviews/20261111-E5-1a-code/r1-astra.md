**Verdict: fix then run.** The core implementation looks consistent with the design. The driver still has checks that can pass incorrectly and budget logic that needs correction.

The file changed during this review. The latest `composition_rows` fixes the omitted-genome and duplicate-observation problems I initially found; my in-memory check now covers all 16 champions on 512 distinct worlds each.

The remaining fixes are:

1. **The state-level check accepts NaNs and omits champions at two shapes.** In [state_level](/D:/Claude/random/wormWars/scripts/e5_1a.py:600), `max(m, float(...))` silently retains `m` when the new value is NaN. I injected all-NaN states: the function returned `worst: 0.0, passed: True`. Check finiteness explicitly. Also, selecting `range(S)` tests only champions 0–3 at validation shape and 0–7 at suite shape. Iterate over groups so all 16 receive every promised check.

2. **The CUDA/composition statistics do not enforce the promised precision or consistently test the weighted score.** [paired_check](/D:/Claude/random/wormWars/scripts/e5_1a.py:537) pools SD across strains, then tests strains individually. I reproduced a passing check with a **0.042 half-width**, exceeding 0.03. `worlds_for` also silently caps an insufficient sample at 8,192. Size each comparison separately—or use the largest required size—and explicitly handle insufficient precision.

   The dedicated training-shape check pools differences across champions and settings, without SD-based sizing. Mixed comparisons use a plain mean, allowing cancellation that the actual fitness weights do not permit: slot differences `[1,-1,-1,-1,-1,1,1,1]` average zero but have weighted mean **0.467**. Test the weighted objective per genome, with the appropriate stratified variance.

3. **Some world-level CUDA checks bypass their stated safeguards.** [trajectories](/D:/Claude/random/wormWars/scripts/e5_1a.py:559) and [respawn_distances](/D:/Claude/random/wormWars/scripts/e5_1a.py:574) never inspect the accumulated ledger residual or call the overflow-checking `hunt_events()`. Setting `check_ledger_every_tick=True` only collects residuals; it does not reject them. Respawn checks also pass with zero respawns.

   Additionally, the motionless hunter still has its body and default attack enabled under the bite rule. That is not §7’s motionless **ghost** hunter; prey can encounter it and respawn. Implement the intended isolated-path check or explicitly amend that requirement.

4. **The cap and stage gates are incomplete.** The new `play()` cap check helps, but [bench_batch](/D:/Claude/random/wormWars/scripts/e5_1a.py:735) does not pass `check=cap().check`; reference children, graph rebuilding and direct world/state loops also bypass it. Constructing `CapClock` does not enforce anything.

   More importantly, [stage_cap](/D:/Claude/random/wormWars/scripts/e5_1a.py:841) writes `cut_level: null` when nothing fits, while [guard](/D:/Claude/random/wormWars/scripts/e5_1a.py:121) checks only that `cap.json` exists. Later stages therefore proceed after “does not fit.” Require a finite positive cap, an admissible configuration, and a cap record bound to the current benchmark. Require explicit successful prerequisite status rather than accepting missing status fields.

5. **The cut projection contains a substantial arithmetic error.** [Line 826](/D:/Claude/random/wormWars/scripts/e5_1a.py:826) subtracts `16 × 2 × 8 × 512 × 17` evaluation episodes when removing four graphs. The suite contribution for those 16 runs is `16 × 2 × 512 × 17`: **278,528**, not **2,228,224**. Batch width does not multiply the episode count again.

   Recompute each cut from its remaining evaluation items. Currently B/P cuts retain their evaluation allowance, while the graph cut removes an excessive amount. Clarify whether the owner’s cap includes already-spent E5-1a time, which is reported separately but excluded from the projected total. The admission policy should also explicitly reflect the owner’s decision to retain B.

6. **Correct the equivalence evidence and smoke isolation.** [The smoke branch](/D:/Claude/random/wormWars/scripts/e5_1a.py:288) passes `ROOT` as both engines. The recorded 1,045 identical arrays therefore establish current-versus-current repeatability, not equivalence with `7d25460`.

   The child reference script receives no smoke settings: it runs 300 ticks on IDs beginning **985,800,000**, inside E5-1’s check block. Thus “40 ticks, outside every E5-1 block” is also incorrect for this portion. Label that evidence accurately and obtain the genuine old/new comparison. I independently verified that the separate **68 E5-0 arrays are identical**.

On the underlying implementation, I found no substantive error in the training mixture, integer weights, validation weighting, world blocks, seed mapping, A0/A0r masks, host lesion, or P’s ungrafted-host permutation followed by L1 embedding. The route cache retains the old sampler’s inputs and random stream; lazy filling is acceptable. The overflow and ledger checks in `TaskHRollout` are present.

By inspection, `weights=None`, scalar pins and shared world IDs preserve their previous execution paths. Exempting `init_*` configuration fields is appropriate: those fields control initialization, not execution. The compatibility guard deliberately changes rejection behavior. I would not claim compatibility with **every** existing caller until the whole-suite run finishes; its log was still incomplete.

**§14’s numerical choices are generally acceptable without changing the seeds, mutation scales, signal threshold or sample counts**, subject to the precision fixes above. Two textual/implementation mismatches also need resolving:

- The reference script covers **19 settings**, not 18.
- `evolve_batch(generations=500)` checkpoints generation **499** as well as 475. The design calls 475 “the last checkpoint.” Freeze the intended candidate set and closing-gap endpoint explicitly before formal registration.

Finally, §9 is not wholly implemented yet: the formal readers and diagnostics—including O0’s calibrated evaluations and P’s direct-routing comparison—remain outstanding. That need not block E5-1a, but they need review before the formal run.

This review was read-only. I reproduced the false passes with in-memory substitutes and inspected the saved arrays. The supplied sabotage log reports a clean 44-test run; I stopped my additional CPU test rerun after about ten minutes without a completed result. No GPU stage was rerun.