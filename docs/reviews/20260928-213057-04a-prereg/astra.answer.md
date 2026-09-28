**Revise before binding.** Most design elements requested by the E1 reviewers are present, but several guards do not implement the registration, the smoke isolation is broken, and the success-rate wording overclaims what 6/12 establishes.

I inspected draft commit `b38c7cc`, the requested code, tests, reviews and context, plus the saved smoke accounting and projection JSON. I did not execute tests or simulations or modify files.

**Must-fix items:**

1. **Smoke training uses the formal training range.**  
   [`use_smoke()`](/D:/Claude/random/wormWars/scripts/e04a.py:600) changes sizes, validation IDs and hold-out IDs, but never changes `REGISTERED["train_ids"]`. [`cmd_train()`](/D:/Claude/random/wormWars/scripts/e04a.py:246) passes that registered range directly to evolution. Therefore, the current smoke command trains on IDs in **997,000,000–997,999,999**.

   This also requires a disclosure correction. The saved accounting records show completed CPU smoke training for both batches, including actual simulated worlds. Those commands ran dirty code, so their accounting alone cannot establish the historical IDs. Nevertheless, the blanket statement that no training-range worlds have been touched is currently unsupported.

   Fix the smoke range and add a command-level assertion on the **actual IDs passed to the simulator**. Audit the earlier exposure, preserve its evidence, and disclose it; reserve a fresh training range if the old exposure cannot be reconstructed. I found no corresponding validation or hold-out range leak.

2. **The command-test fixture can delete real development records.**  
   In [`tests/test_e04a_commands.py:70`](/D:/Claude/random/wormWars/tests/test_e04a_commands.py:70), the fixture calls `use_smoke()` **before** redirecting `EXP` and `OUT` to `tmp_path`. That function first selects the real `runs/e04a-smoke/` directory and unlinks training records, evaluation records and start markers.

   Isolate the filesystem before any cleanup, and test that repository smoke artifacts remain untouched. This directly contradicts the draft’s claim that these command tests operate in a scratch folder.

3. **The projection is not a gate.**  
   [`cmd_project()`](/D:/Claude/random/wormWars/scripts/e04a.py:282) writes `within_limit`, but:
   
   - training never reads or requires it;
   - an over-budget projection merely prints `OVER`;
   - projection has no exclusive marker, cap checks or not-completed handling;
   - formal projection length can be changed through `--generations`, despite the registered six generations;
   - training does not establish that the projection used the same guarded code and environment.

   Require a completed, passing projection with matching code, configuration and environment before batch A. Apply the declared once-only and cap rules to projection, or explicitly register different rules. Test missing, failed, over-limit and mismatched projections through the command entry points.

4. **The supposedly frozen E1 inputs are outside the guards.**  
   [`GUARDED`](/D:/Claude/random/wormWars/scripts/e04a.py:51) excludes both `experiments/E1-navigation/freeze.json` and `gate.json`. Evaluation reads the former directly, without checking its committed state or hash. `task_config()` compares against the latter’s current contents.

   Consequently, changing the frozen baseline parameters can pass the existing formal guards. Pin and verify these inputs, include them in the clean-tree and same-code checks, and record their hashes. A configuration hash compared against a mutable reference is not sufficient freezing.

5. **“At least as often as not” is not established by 6/12.**  
   The statement in [§6](/D:/Claude/random/wormWars/experiments/04a-navigation-primitive/PREREGISTRATION.md:179) turns an observed-share criterion into a population claim.

   Keep **6/12 as a prespecified operational benchmark**, but say that it means at least half of these registered runs passed. It does not establish that a new run succeeds with probability at least 0.5. Even with ideal independent, perfectly classified Bernoulli outcomes, a one-sided exact 5% test against \(p\leq0.5\) requires **10/12**, not 6/12. Shared evaluation worlds introduce another distinction between success on this benchmark and success across newly sampled benchmarks.

6. **Clarify what the cue criterion establishes.**  
   The mirrored contrast establishes sensitivity to misleading cue location. It does not necessarily establish an advantage over the champion’s own cue-free behavior.

   A champion scoring 3 under both real and constant probes, but 0 under the mirror, could pass every registered rule given sufficiently weak baselines and generation 0. The mirror harms it; the real cue has not improved its count over the constant probe.

   Either make a paired real-versus-own-constant comparison gating, with its margin fixed now, or narrow “because of the cue” to the precise reflected-cue criterion. The existing constant arm already supplies the necessary measurement.

   Also carry forward Fable’s explicitly requested **grid-edge limitation**: these are comparisons against the frozen tested baselines, some potentially under-tuned—not against the best possible simple movement policies.

7. **Supply the required engine-equivalence evidence and correct the testing description.**  
   The new per-strain-ID test compares two paths through the **new** implementation. It is not the previous-engine comparison required by AGENTS.md rule 7. I did not find an archived before/after check for these changes.

   Provide that comparison with its tolerance declared beforehand, using nonformal worlds. Add direct tests of the geometric progress formula and reset after relocation: the existing bounds tests would accept many incorrect progress functions. The draft should also disclose that command tests use `smoke=True, guarded=False`; they do not exercise the formal guards’ wiring.

On the remaining design questions:

- **Shaping: the bound is correct, and \(c=0.5\) is defensible.**  
  I checked [`World.final_progress()`](/D:/Claude/random/wormWars/wormwars/world.py:560), target advancement, and [`fitness()`](/D:/Claude/random/wormWars/wormwars/e04a/evolve.py:52). The implemented formula is
  \[
  p=\operatorname{clip}\!\left(\frac{d_0-d_T}{\max(d_0,10^{-6})},0,1\right),
  \qquad F=\operatorname{mean}(N+0.5p).
  \]
  Distances are to the current target’s centre, from the leg’s actual starting head position and final head position. Relocation resets that start. There is no accumulated approach or relocation bonus.

  Within one episode, finishing another target cannot lose overall score merely by resetting progress: the arrival adds 1 and removes at most 0.5. Parking therefore cannot exploit an unbounded reward or make refusing an immediately available arrival preferable.

  **However, the bound is per episode, not per eight-world evaluation.** A zero-arrival policy with mean progress 0.9 scores 0.45; one arrival across eight worlds with zero terminal progress scores 0.125. Parking, orbiting or moving toward generally favorable locations can thus beat rare arrivals during training. This is a real optimization risk, not a broken bound. Raw-count validation and hold-out prevent such behavior alone from passing. I would retain 0.5 as a fixed heuristic and avoid claiming policy invariance or immunity to local optima.

- **Batching: I found no algorithmic coupling between runs.**  
  I checked initialization, per-run generators, training-ID construction, population slicing, `breed()`, genome copying, rollout ID flattening and world-to-strain assignment. Selection and mutation use only each run’s population and fitness. Brain matrix operations are batched by strain, without cross-strain mixing.

  Runs remain appropriate replication units. The fake-simulator independence test supports the optimizer wiring; it does **not** establish CUDA equivalence between solo and batched execution. The composition declarations and default-mode replay qualification are appropriate. Shared validation and hold-out worlds make inference conditional on shared benchmark samples; do not treat the resulting pass decisions as independent evidence about world-sampling uncertainty.

- **Champion and generation-0 baseline: acceptable for the stated comparison.**  
  The code implements 41 checkpoints—0, 25, …, 975, 999—and `np.argmax` selects the first validation maximum. Generation 0 is the training-fitness winner among its 32 initial genomes. Validation and hold-out use raw counts, and champion/baseline hashes are checked before hold-out evaluation.

  This measures improvement over the registered starting checkpoint. It does not isolate mutation’s benefit from the benefit of searching and selecting among many candidates; a compute-matched random-search comparison would answer that different question.

  **64 validation worlds are usable, but their adequacy for stable ranking is unproven.** Selecting among 41 checkpoints creates optimistic validation maxima and potentially noisy champion choices. Independent hold-out preserves interpretability. Increasing validation to 128–256 worlds is a suggestion if the revised projection supports it, not a prerequisite. Change “never used for selection” to “never used for breeding”; they plainly select the champion.

- **Thresholds and multiplicity: retain the navigation thresholds; specify the inferential claim.**  
  The reliability requirement, four baseline margins, mirrored contrast and generation-0 margin are implemented as written. I see no reason to require beating unrestricted S-const or reaching an arbitrary fraction of its score. That would change the question from evolving navigation to approaching a strong scripted controller.

  Within a run, requiring every component to pass is an intersection criterion; a blanket correction for those component tests is unnecessary. Across runs, however, the reported 95% bounds are **marginal**, not simultaneous. “At least six genuinely qualifying controllers” or “any selected passing module is certified at 95%” needs a separate multiple-testing formulation. Merely declaring an operational 6/12 benchmark does not automatically require Bonferroni over 16 runs. State this distinction explicitly.

- **Budget: plausible computationally; evolutionary sufficiency is unknown.**  
  The training calculation is correct: **4,096,000 strain-world episodes**, with 2,000 batch generations at 4.749 seconds giving 9,498 seconds. The local projection JSON supports the reported timing, but it is untracked and records dirty development code. Commit that evidence.

  The projection does not exercise checkpoint serialization through `on_checkpoint`, and its median largely excludes checkpoint generations. The separate checkpoint allowance and roughly 2.2-fold total margin make the six-hour cap plausible, but the guarded projection must actually enforce the decision.

  Nothing in E1 establishes that 1,000 generations suffice for this optimizer. This is a legitimate fixed-budget experiment. Failure means **this procedure did not meet the criterion within this budget**, not that N2 cannot evolve navigation.

**Additional suggestions, not binding blockers:**

- Prioritize tests for cap hits during evaluation and after analysis, training crashes before the first checkpoint, interrupts, generation-0 hash mismatches, and checkpoint-write failures. These are materially less covered than the draft suggests.
- Check validation scores for non-finite values before champion selection. The explicit finite check currently covers training only.
- Avoid leaving module files marked `passed` when the final cap check subsequently makes evaluation “not completed”; modules are currently saved before that check.
- Align the documented artifact paths with the runner: candidates are per-run files under `genomes/`, and final populations go under `runs/e04a/`.
- Make nonmonotone gain-curve handling agree between prose and code. The prose uses the endpoint at \(k=8192\); `equivalent_k()` uses the maximum over the curve for its upper-range classification.
- Selecting the E3 module by highest hold-out mean is an additional selection step. Its reported winning mean is selection-biased; assess downstream performance on fresh E3 data.

**04a pre-registration: revise**