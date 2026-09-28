**Revise before binding.** The main scientific rules now match the implementation. Remaining blockers concern genome configuration integrity, reruns, failure recording, and the certainty claimed for reconstructed exposure.

I inspected the working files with HEAD pointing to `68f8aa3`, both archived v1 reviews, D104, the development records and surviving smoke accounting. I did not execute tests, simulations, hashes or numerical reconstructions.

**Must-fixes**

1. **The local-genome checks permit a change to the registered padding configuration.**

   [`check_genomes()`](/D:/Claude/random/wormWars/scripts/e04a.py:513) checks parameter hashes and regenerated generation-0 membership. But [`load_genome()`](/D:/Claude/random/wormWars/wormwars/evo/genomes.py:211) lets stored `pad_single_strain` override the supplied brain configuration. `genome_hash()` excludes that metadata, and `Brain` uses the loaded genome’s configuration.

   Consequently, changing only a candidates file’s metadata to disable padding leaves every parameter-hash check satisfied, including generation-0 membership, while changing the hold-out’s registered execution configuration. The recorded task-configuration hash still describes padding as enabled.

   **Fix:** reject loaded candidates whose effective brain configuration differs from the bound configuration, before the evaluation marker or any hold-out rollout. Add a test that changes only padding metadata, preserves parameter hashes, and requires rejection. Keeping genomes local is otherwise the correct remedy for the redistribution problem.

2. **The rerun implementation does not fulfill the registered rule.**

   Two concrete gaps:

   - [`cmd_project()`](/D:/Claude/random/wormWars/scripts/e04a.py:271) never handles `args.rerun`. A stopped projection writes `projection.json`; subsequent invocation refuses because that file exists, even with `--rerun`. Either implement its once-only retry or explicitly exempt projection from the general rule before binding.
   - [`cmd_train()`](/D:/Claude/random/wormWars/scripts/e04a.py:334) archives the JSON record, marker and partial JSON, but **does not archive the stopped attempt’s candidate genomes**. The rerun’s first checkpoint overwrites those files through `save_genomes()`. The preserved record can then reference genomes that no longer exist. Same seeds do not repair this, particularly when exact CUDA replay is explicitly unclaimed.

   **Fix:** archive the batch’s local candidates and any final populations alongside the stopped attempt, with an explicit path mapping. Keep these files local. Test preservation of their original hashes after retry, and rejection after a *second stopped attempt*. The existing retry test instead retries after completion, which exercises the completed-outcome refusal.

3. **Some advertised failure-recording guarantees remain false.**

   In [`_train_not_completed()`](/D:/Claude/random/wormWars/scripts/e04a.py:396), `save_genomes()` runs before the not-completed JSON is written. If checkpoint persistence caused the original exception and continues failing, the exception handler repeats that failure and never writes the stopped record. The marker then blocks ordinary execution, while `archive_attempt()` cannot operate without the record.

   Also, [`extras()`](/D:/Claude/random/wormWars/scripts/e04a.py:647) computes `decoy_capture` outside its exception handlers. An exception there preserves the already-written verdict, correctly, but produces no extras error record and prevents the remaining extras. That contradicts §7’s promise.

   **Fix:** make failure-record writing independent of another successful genome save, preserving the last durable checkpoints and recording persistence errors. Put decoy diagnostics under the same error-recording protection as replays and modules. Add targeted failure tests; neither case is covered now.

4. **Qualify and preserve the evidence behind “reconstructed exactly.”**

   The two surviving smoke ledgers support **48 selection episodes per batch and 1,920 selection ticks**, consistent with the stated settings. Both also say `code_dirty: true`; neither records world IDs. Matching those totals does not independently establish which IDs the historical process used.

   The [reconstruction](/D:/Claude/random/wormWars/experiments/04a-navigation-primitive/development-records/smoke-training-exposure.json) supplies a deterministic schedule and names the ledgers, but the original ledgers remain under an ignored `compute/` directory. I could inspect them locally; a fresh public checkout cannot obtain that corroboration from the reconstruction alone.

   **Fix:** preserve those two small ledgers in the development records and describe the IDs as reconstructed from the stated schedule/settings, consistent with accounting, with the dirty historical source and deleted direct records acknowledged. Distinguish exact reproduction of that schedule from direct verification of the historical IDs.

**Status of the v1 must-fixes**

| Item | What I found |
|---|---|
| Smoke training isolation | Fixed in code: `use_smoke()` rebinds training IDs; validation, hold-out and projection use smoke ranges. The command test examines actual simulator IDs. Historical disclosure still needs item 4 above. |
| Fixture deleting real records | Fixed: the fixture supplies `folder=tmp_path` before cleanup; the unlink-spy test checks confinement. |
| Projection enforcement | Implemented: batch A requires a completed, passing projection; formal execution checks commitment, code and environment. Projection has a marker, cap checks and fixed length. Retry gap remains. |
| Frozen E1 inputs | Fixed: both files are guarded, stage hashes are recorded, and evaluation explicitly compares them with batch A. |
| Success-rate overclaim | Fixed: operational 6/12 wording, Clopper–Pearson calculation and shared-world/marginal-bound qualifications are present. |
| Cue criterion and baseline limitation | Fixed: `run_rules()` implements real-minus-own-constant with strict lower bound `> 0.5`; the counterexample from v1 is tested. Grid-edge limitations are stated. |
| Engine equivalence and progress tests | Old/new comparison code and CPU/CUDA reports now exist. Direct geometric-progress, arrival-reset and fixed-composition independence tests are present. |
| Genome publication | Publication requirement removed; files stay local and generation-0 membership is checked. Effective configuration still needs item 1. |
| `require_committed` testing | A temporary-repository test now covers untracked, committed and modified files. |
| Text and development artifacts | Substantially addressed, with the remaining mismatches identified above. |

The formal projection rejection coverage is still thinner than v1 requested: the command tests do not exercise a failed projection or mismatched projection code/environment. The guarded smoke run also skips `require_committed()` by design. Static inspection shows the calls are wired correctly; that is different from having those rejection paths tested.

**Development records and the training-range remedy**

Moving training to `999,000,000–999,999,999` is reasonable and conservative. The code passes that range to the schedule generator, and the range test excludes the reconstructed IDs. It removes the need to rely on a perfectly reconstructed old exposure. It does not erase the development exposure or make pilot-informed choices independent of pilot data; §9 should retain that distinction.

The equivalence reports consistently record identical scores and event arrays on both devices. The script can compare separate source trees, and `5eaf339` precedes the 04a groundwork. I accept this as the reported comparison for those cases. Its provenance is limited: the comparison JSON hard-codes the reference commit and records neither source-tree hashes nor input-artifact hashes. The draft fairly acknowledges that the tolerance’s timing is not independently verifiable.

The pilot disclosure accurately summarizes the saved checkpoint means. Add explicitly that [`e04a_pilot.py`](/D:/Claude/random/wormWars/scripts/e04a_pilot.py:40) uses **the same run seeds as formal batch A**, hence the same initial populations under the stated initialization. The worlds differ. This is acceptable development exposure, but “batch A’s shape” understates that relationship.

**Keep 1,000 generations and 02’s optimizer.**

The pilot demonstrates early improvement followed by limited further improvement in checkpoint means. It does **not** establish the reliability distribution or identify a better optimizer setting.

The [pilot writer](/D:/Claude/random/wormWars/scripts/e04a_pilot.py:48) discards checkpoint per-world counts and saves their means. A mean near two can accompany either passing or failing reliability. On the formal 1,024-world sample, rule 1 requires 820 episodes with at least two arrivals, implying a minimum mean of `1.6015625`; a mean above that is insufficient to establish passage.

Therefore:

- Keep the thresholds, shaping coefficient, optimizer and generation count.
- Describe the plateau as a risk to success, without assigning a likely outcome from means alone.
- Treat 04a as the fixed-budget test of this procedure; use E2 to compare optimizer alternatives.
- Preserve per-world counts and reliability diagnostics in future development pilots. Formal training already records checkpoint counts.

Increasing generations or changing mutation scales now would be a hypothesis about fixing the plateau, unsupported by this pilot. The existing approximately 2.96-hour estimate fits the six-hour cap; my requested fixes add no material simulation work.

**Suggestions, not binding blockers**

- **Projection:** the formula implements the registered expression, but it is an estimate rather than a conservative bound. The final timed generation omits breeding, and projection omits the growing checkpoint-file writes used in formal training. Measure or explicitly budget those costs.
- **Equivalence tooling:** record actual source revisions, dirty states and artifact hashes; make an exact-comparison failure return a failing exit status. Currently `compare()` prints differences but exits successfully.
- **Tests:** add validation-only NaN rejection, the missing formal projection rejection cases, and evaluation-retry coverage. I cannot establish fail-before-pass history from the current test files.
- **Local artifacts:** keep durable backups. Committed hashes establish identity when files are available; they do not let outsiders replay unavailable champions. This limitation is acceptable under the redistribution restriction.
- **Cap wording:** clarify how the all-stage cap applies to extras after the verdict, since replay cap errors are recorded without changing that verdict.

I checked the requested runner functions, the full batching/evolution implementation, both 04a test files, the new end-of-file Task N tests, and the supporting rollout, progress, genome-loading, registration and accounting paths. The new rule 4 is implemented correctly and should remain.

**04a pre-registration: revise**