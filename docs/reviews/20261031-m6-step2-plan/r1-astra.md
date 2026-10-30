**Verdict: agree with fixes.** The bounded experiment is defensible, and the main design corrections were adopted. I would fix the items below before running it; another design round is unnecessary.

The archived and working plan copies are identical. I verified the 102 T1 champions, 72 T0 champions, and 30/24 blocks against the records. The full-network rescaling is implemented correctly: `Genome.cat` retains the scaled configuration, and `Brain` reads it. My constant-input check on the disclosed champion was bitwise exact at all five k values. No clamping occurs.

`score_run` uses the intended worlds, seeds and score axes. `probe_one` correctly writes the two states at k = 1, continues those same states under each arm, and sums absolute read-out separation over ticks 1–100. The control comparison uses the specified common denominator. The primary averaging correctly computes within-run ratios, averages mappings within blocks, then weights blocks equally.

The required fixes are:

1. **Match mappings in the T1–T0 comparison.**  
   [The reader](/D:/Claude/random/wormWars/scripts/memory_m6/step2_read.py:188) pairs graph/run blocks correctly, but averages different mapping sets: T1 has M0, R1, R2 **and MS** in the 24 shared blocks; T0 has only M0, R1 and R2. This follows the plan’s literal block averaging, but confounds the intended task comparison with mapping composition.

   A 50% drop confined to MS would produce a −12.5 percentage-point T1–T0 difference even if every matched mapping were unchanged. For this secondary, pair T1 and T0 within graph/run/**mapping**, restrict to M0/R1/R2, then average within blocks. Keep all 102 champions in the T1 primary.

2. **Fix Spearman’s ranks and the resample count.**  
   [`argsort().argsort()`](/D:/Claude/random/wormWars/scripts/memory_m6/step2_read.py:93) assigns distinct ranks to tied observations. Bootstrap resampling creates ties even when the original observations are distinct. I reproduced `rho = 1` for `[1,1,2]` against `[1,2,3]`; proper Spearman gives approximately `0.866`. Constant input also incorrectly returns `1`.

   Use average ranks or `scipy.stats.spearmanr`, handle undefined correlations explicitly, and use the promised 10,000 resamples. `association` currently uses only 1,000.

3. **Make incompleteness and failed checks govern the entire reading.**  
   [Validation](/D:/Claude/random/wormWars/scripts/memory_m6/step2_read.py:119) silently excludes missing arms. Using the existing fixture entirely in memory, I removed k = 0.25 and k = 4 from 15 of 16 probe runs: validation still passed, and the reader issued the affirmative primary wording.

   Check required genomes, labels, arms and fields before analysis; require the intended 32 finite world scores and consistent means. Missing required measurements must make the reading inconclusive. Report zero continuation denominators explicitly instead of silently changing the validation population.

   Also, [failed consistency or validation](/D:/Claude/random/wormWars/scripts/memory_m6/step2_read.py:206) replaces only `words.primary`. The output still says “The reduction exceeded…” for both controls, and retains affirmative wording under `primary.words`. Keep descriptive numbers, but gate **all interpretive conclusions** consistently.

4. **Resolve the mixed batch composition in secondary comparisons.**  
   [The scheduled batches](/D:/Claude/random/wormWars/scripts/memory_m6/step2.py:152) put T1 k = 1 in a three-strain batch, while k = 0.5, k = 2 and the interior arm run alone. Thus those paired comparisons change both the intervention and composition. The primary and control comparisons retain composition correctly.

   Either use matching compositions or add a predetermined rollout equivalence check for the actual one-versus-three-strain compositions. The batch test currently checks the schedule, not numerical equivalence. I found equality in a short CPU brain check, so I am **not claiming demonstrated score contamination**; the full comparison remains unchecked.

5. **Correct the runtime forecast and retain partial work.**  
   [The forecast](/D:/Claude/random/wormWars/scripts/memory_m6/step2.py:184) multiplies the first three T1 runs’ average cost by all 174 runs, treating cheaper T0 runs as T1 runs. Using the plan’s own estimates, it projects approximately  
   `170 / 102 × 174 = 290 minutes`, exceeding the 255-minute forecast threshold, although the stated total is 222 minutes.

   Forecast T1, T0 and probe work separately, including time already spent. Check the cap inside the probe’s arm loop, as promised. Save completed run records incrementally: currently a stop discards the entire unfinished stage’s measurements while still consuming its budget.

6. **Complete the promised reporting and the omitted design fix.**  
   [The reader](/D:/Claude/random/wormWars/scripts/memory_m6/step2_read.py:164) does not produce the promised absolute-change summaries beside the ratios. Its control intact means are genome-weighted, whereas the effect summaries are block-weighted. Add clearly labelled, consistently weighted baseline and absolute-change summaries.

   Validation reports aggregate proportions but no individual failures. Add their identities, explicit known-switch/previously-seen flags, and the prespecified fading-only sensitivity analysis requested in the design review. That last analysis needs no new simulation. Consequently, “every fix is taken” is currently inaccurate.

   Clarify that the primary percentage is the **mean within-champion relative change**, not the percentage change in a pooled mean score.

7. **Soften three interpretation claims.**  
   - The interior arm preserves boundary **time constants**, not boundary responses: recurrent inputs change, and boundary neurons also receive finer numerical integration. Say “the drop also occurred without directly changing sensory and motor time constants.” It cannot rule out sensory/motor response explanations outright.
   - Exact rescaling does not guarantee that a finite-window integrated separation decreases for every nonlinear trajectory. The population validation criterion is reasonable, but its success is empirical; “shrinks by construction” is too strong.
   - Single-nose sensing makes temporal comparison plausible. It does not establish that this foraging score requires it, or that a fourfold speedup must impair performance. Present the expected drop as a prior expectation.

**What to cut:** control-genome probes are the clearest saving. The reader uses only champion probes; the control probes have no specified analysis. Either name their purpose now or omit them. The k = 1 full probe and continuation also duplicate the same trajectory and can share computation. I would add no further intervention arms.

I reproduced the five reader tests using in-memory fixtures and demonstrated the failures above without changing files. The archived 15/15 sabotage result does not cover these cases. Add targeted tests for missing arms, gated wordings, tied ranks, unequal mapping sets, and the actual `score_run`/`probe_one` paths. The disclosed timing and smoke observations are appropriately labelled exploratory; I found no basis to allege an additional undisclosed post hoc choice.