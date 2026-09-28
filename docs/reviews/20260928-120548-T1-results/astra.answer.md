**T1 should not close under T1.4 as currently written.** The failures are disclosed honestly, but the narrowed wording overreaches the evidence, and there are defects in the checker and missing promised checks.

I reviewed `roadmap` at `c25ffb4`. The JSON confirms, in each mode, 188/188 switch-off matches, 112/114 “multi-strain” matches, and 66/74 single-strain matches. It also confirms 388 unchanged hold-out records—24,832 individual scores. I could not rerun Python tests: this environment has no accessible Python installation.

1. **Handling: honest reporting, but not satisfaction of the original contract.**

   Recording the general claim as failed is correct. Correcting the singleton-remainder classification is also legitimate: that changes which reference an output should be compared against; it does not turn a numerical failure into class N.

   However, the replacement claim is a **post hoc finding**, not a pass of the original class E test. Adoption therefore needs an explicit, dated change to the acceptance decision.

   The wording needs tightening:

   - “At least 20 rows” implies an established threshold. The rollout evidence supports particular cases at **20, 160, 320 and 1,280 rows**, with particular strain counts, configurations and endpoints. It does not establish every larger size or every combination of those dimensions.
   - “Below 20 rows, results depend on the batch’s strain count whatever padding does” is too broad. It contradicts the reported eight-row diagnostic.
   - [REPRODUCIBILITY.md:49](D:/Claude/random/wormWars/docs/REPRODUCIBILITY.md:49) says only singleton batches differed at eight rows; [T1.md:358](D:/Claude/random/wormWars/docs/foundations/T1.md:358) says **none** differed. These cannot both describe the same check.
   - I found no committed script/output for the expanded raw `bmm` sweep, the reduction-threshold diagnostic, or the separate remainder rerun. The committed equivalence script tests no eight-row brain case or eight-row proxy rollout. The reported **153 differences** are present for singleton-versus-32 proxy comparisons; the supplied summaries do not independently establish the stated **two-versus-32** comparison.

   Commit those diagnostics with provenance, or label the unsupported details as provisional. A raw `bmm` match also cannot establish whole-rollout equivalence.

2. **Decision 1: retain brain-level padding; favor default-on for future work under an explicitly amended policy.**

   I would retain this mechanism. It fixes demonstrated cases, covers direct brain callers, preserves the tested legacy path, and has straightforward accounting.

   But describe it as **a mitigation with measured scope**, not general composition independence. Keeping it default-on despite failures outside that scope is a new engineering acceptance decision; my earlier conditional approval did not authorize calling the failed test passed.

   I would not add rollout duplication or row padding now. Neither follows automatically from this diagnosis, and each needs its own declared comparison. Measure the final padding-enabled E1 configuration: the committed profile predates padding.

3. **Decision 2: the composition amendment is directionally right, but needs precision.**

   Write composition as a **tuple**, `(strains per chunk, rows per strain, worlds per chunk)`, rather than a product. Equal products do not imply equivalent shapes. Record actual remainder chunks and distinguish the logical singleton from its effective two-strain neural batch.

   Keep the surrounding conditions explicit: same configuration, inputs, device, numerical settings and software environment. “Equality across compositions only for the comparisons tested” is defensible; “≥20 rows and ≥16 worlds” is not an established universal rule.

   Also clarify the reduction diagnosis: these are **per-world spatial sums evaluated in differently sized world batches**, not sums across worlds. See [rollout.py:66](D:/Claude/random/wormWars/wormwars/evo/rollout.py:66).

4. **Decision 3: reasonable provisional guidance, not an equivalence guarantee.**

   Use **20 checkpoint worlds as a candidate configuration**, then test the actual Task N implementation and its actual endpoints. “Any number ≥20 is safe” is unsupported.

   Alternatively, accepting composition-specific results is scientifically workable if each evaluation protocol fixes and records its composition consistently across conditions.

   Neither choice establishes equality between eight-world training and twenty-world checkpoints: those have different rows per strain, a comparison the original contract expressly excluded. The eight-row raw multiplication finding does not validate larger multi-run batches end to end.

5. **Decision 4: T1.4 has not passed. Closure requires an explicit amended gate.**

   The record should say approximately:

   > T1.2 failed its original class E acceptance test. Legacy preservation passed for the measured outputs, and 388 historical hold-out records reproduced. Padding achieved equality for a specified subset of comparisons. Retaining it is a post hoc engineering decision under a dated amendment; it does not retroactively satisfy the original gate.

   Two promised checks remain missing: **starting food** and **published capability probes**. The published-effect routine checks hold-outs only, although [T1.md:247](D:/Claude/random/wormWars/docs/foundations/T1.md:247) requires both.

   After addressing the defects and evidence gaps below, engineering closure through an amended criterion is reasonable. It should authorize the bounded E1 pilot and leave the measured experiment-budget gate with E1.

   The §2 choices remain reasonable. Qualify the profiling record, though: `short_run` is measured once; concurrency reports one aggregate timing per process configuration; lever timings discard the ranges returned by `_timed`. “Five repeats with median and range” does not describe every reported measurement.

6. **Code and test findings.**

   **The core padding implementation looks sound by inspection.** Broadcasting the per-strain terms, duplicating the state and matrices, applying silencing, invalidating the cache in `cut_gap`, and counting the duplicate work are consistent. I found no concrete arithmetic defect there.

   The following need attention:

   - **The remainder fix is ineffective against the existing reference.** `run_cases()` now emits the marker, but [run_mode():289](D:/Claude/random/wormWars/scripts/t1_equivalence.py:289) reads descriptions from the old `reference.json` and discards both new descriptions. That reference lacks `remainder_of_one` for `random256x8/chunk3`. Infer the remainder from `strains` and `per_chunk` during classification, and test using the old metadata. Preserve the original result and append the corrected comparison.

   - **Starting food is omitted.** [FIELDS:62](D:/Claude/random/wormWars/scripts/t1_equivalence.py:62) excludes `food_start`. Moreover, normal `rollout()` does not populate that field, although `_play()` calculates it. Adding the field name alone will not fix coverage.

   - **The equality checker accepts invalid results.** [_eq():192](D:/Claude/random/wormWars/scripts/t1_equivalence.py:192) treats matching NaNs as equal and also accepts matching infinities. Require finite values and matching dtypes, with sabotage tests. If retaining the literal “bit-equality” wording, distinguish it from numeric equality, which also equates positive and negative zero. I am not claiming the existing outputs contain nonfinite values; the checker cannot establish their absence.

   - **Legacy loading has an override hole.** In [load_genome():211](D:/Claude/random/wormWars/wormwars/evo/genomes.py:211), missing metadata becomes off only when constructing the config from storage. A caller supplying a current `BrainConfig()` can silently enable padding for an old file. The inspected historical entry points generally avoid this, but the blanket loader claim is false. Preserve the stored setting or require an explicit padding override; test this supplied-config case.

   - **Subprocess compute is not persisted.** The equivalence script’s `--in-replay` branch bypasses `run_script`; the profile’s `--worker` branch does likewise. Their process-local ledgers are discarded, and the parent does not merge them. Parent elapsed time does not recover missing world/neural counts. Record and aggregate child accounting.

   - **The published mean-change statistic is misleading.** [Line 326](D:/Claude/random/wormWars/scripts/t1_equivalence.py:326) subtracts a float32 mean from a float64 mean reconstructed from JSON. Consequently the artifact reports a nonzero maximum mean change despite every individual score matching. Compute differences in a common dtype before averaging. This does not invalidate the per-world equality results.

   Finally, update the implementation comments that still promise population equality unconditionally, and the test module’s claim that CPU padding cannot change results. Keep the historical plan text intact and append its correction.

T1: not yet — fix the checker and accounting defects, complete starting-food and published-probe checks, archive the diagnostic/rerun evidence, narrow the claims, and explicitly amend the failed closure gate.