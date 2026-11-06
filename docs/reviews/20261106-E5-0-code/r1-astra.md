**Verdict: fix then run.** The core world mechanics mostly match draft 2, but the calibration, cap, and stage guards have concrete defects. I would fix these before formal stages.

1. **E_prey is measured incorrectly because of float32 rounding.**  
   [`HuntWorld._combat`](D:/Claude/random/wormWars/wormwars/e5/hunt.py:232) subtracts the prey’s before/after energies. Near `1e6`, float32 spacing is `0.0625`; converting those energies to double afterward cannot recover the lost precision.

   I reproduced the held fixture on the same eight smoke worlds. The event log reports rates of `0.125` or `0.0625`; combat’s `last_damage_taken` reports `0.137500003` or `0.076388888`. Consequently, the intended statistic gives **E_prey = 1.37500003, not 1.25**.

   Accumulate combat’s attributed/capped damage directly in float64, and use that for calibration and maximum-tick damage. Recheck the predicted range: this fixture can include head damage alongside both flank points.

2. **The eight-hour cap does not count the current invocation.**  
   [`cap()`](D:/Claude/random/wormWars/scripts/e5_0.py:114) constructs a new `CapClock` every time. Calls such as `cap().check()` therefore compare previous attempts plus essentially zero elapsed time. The current attempt enters the accounting file only when it finishes.

   I verified this with a simulated clock: a persistent clock rejects nine elapsed hours; the runner’s fresh-clock pattern accepts them. Create one clock per invocation and retain it. Also resolve `--out` consistently: accounting honors it, while this driver’s cap/results paths remain unchanged.

3. **Benchmarking comes after the expensive work it is supposed to budget.**  
   [`stage_bench`](D:/Claude/random/wormWars/scripts/e5_0.py:536) requires `calibration.json`, while calibration performs the complete per-setting tuning. This contradicts §8’s benchmark-first requirement and prevents the speed cut from saving calibration work.

   Make the benchmark runnable before full tuning, project calibration as well as evaluation/probes, and apply the declared cuts before doing the affected work. Separately, the [reference subprocesses](D:/Claude/random/wormWars/scripts/e5_0.py:408) never export/merge their compute counters. Their elapsed time is covered by the parent, but their worlds, ticks, and neural updates are missing.

4. **Required failure conditions are recorded, not enforced.**  
   [`run_scripted`](D:/Claude/random/wormWars/scripts/e5_0.py:528) records attack-disabled captures/damage without rejecting nonzero values. The reader also merely reports them. In an in-memory check, the actual reader accepted eight attack-disabled captures and nonzero damage.

   Likewise, `check_ledger_every_tick` remains **False** in the operational configuration. Results contain the final ledger residual, and neither runner nor reader rejects excessive or nonfinite errors. Enable per-tick tracking for HuntWorld runs and enforce the `1e-5` limit. Make nonzero attack-disabled captures or damage stop the stage immediately.

5. **Equivalence and resume records are insufficiently bound to the code being evaluated.**  
   [`stage_equivalence`](D:/Claude/random/wormWars/scripts/e5_0.py:404) trusts an existing reference worktree without checking its HEAD or cleanliness. A modified reference could therefore produce a false old-versus-new pass. The existing worktree currently has the correct HEAD; this is a missing guard, not evidence that your recorded comparison used the wrong engine.

   [`stage_evaluate`](D:/Claude/random/wormWars/scripts/e5_0.py:615) accepts `equivalence.json["passed"]` without checking that it covers the current code/environment. `--resume` additionally bypasses the clean/pushed guard; completed outputs are reused by filename. Validate prior-stage provenance, calibration completion, run configuration and output compatibility before reuse.

   Trace coverage also falls short of §4: the ghost traces cover only three hunters under `real`; the old/new traces omit the oracle. Add the promised coverage.

6. **The route check tests three marginal proportions instead of the joint criterion.**  
   [`route_check`](D:/Claude/random/wormWars/scripts/e5_0.py:285) accepts when each condition separately passes in 95% of worlds. The plan requires 95% of worlds to satisfy **all three**.

   For example, three disjoint failure groups of three worlds each give every marginal `61/64 = 95.31%`, but only `55/64 = 85.94%` pass jointly. Gate on `(ok_speed & ok_lap & ok_ref).mean()`. Keep the separate proportions as diagnostics.

7. **Required observations are discarded before saving, and some readings diverge from §6.**  
   [`run_neural`](D:/Claude/random/wormWars/scripts/e5_0.py:498) and `run_scripted` retain only part of `HuntResult`. The saved smoke arrays contain captures, capture ticks, contact counts and bearings. Activation ticks, first-contact ticks, attributed damage, hunter paths and complete prey paths are lost; bite-energy gains are also discarded. Neural runs omit the promised prey-speed/wall-refusal reporting. Preserve these before the formal runs, because they cannot be recovered from the saved counts.

   [`stage_read`](D:/Claude/random/wormWars/scripts/e5_0.py:763) also applies solvability/qualification readings to H1-ghost, although §6 excludes that bridge setting. The threshold-free contrasts contain point estimates only; add paired bootstrap intervals under the stated interval convention. The planned `evaluation.json` and `probes.json` summaries are not produced.

On the other requested points:

- **Mechanics:** head-centred truncated scent, post-move reach, bite capture, zero prey attack, replacement without pellets, D−R selection, sequence-indexed events, prey-policy reset and horizon termination look consistent. The body field is refreshed at tick end. The body probe retains combat’s body-point sampling while removing the prey’s collision-field contribution.
- **Hooks:** yes, by inspection they are no-ops for existing tasks. The spawn default returns the original swarm count; the food-field predicate is unchanged; `attack_scale=None` skips multiplication. I found no conflicting overrides elsewhere.
- **Statistics:** the bootstrap correctly shares resampled worlds and recomputes the maximum baseline mean inside each resample, including for ratios. Qualification/failure inequalities match the plan. Falls-off uses increasing tested speeds and retains subsequent readings, including recoveries.
- **One smaller probe discrepancy:** `constant` also injects the scent-derived constant into the prey’s food channels. I measured prey food input changing from zero to `0.12154`. Current scripted prey ignore food, so this does not change their behavior, but “prey observations unchanged” is false. Restrict that replacement to the hunter.

I independently compared the archived 64 arrays: identical. Those reference files contain **512 worlds and eight traced worlds**, despite residing in the smoke directory. I also directly ran all eleven E5 test cases successfully. Those tests substantiate the world mechanics; they do not catch the driver failures above. No files were changed.