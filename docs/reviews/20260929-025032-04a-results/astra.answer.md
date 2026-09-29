**The registered verdict “04a: passed” is supported. I would fix the reporting before main; I found no reason to rerun the experiment or change its verdict.**

**Must-fixes**

1. **Correct the training-curve summary.** [RESULTS.md:89](/D:/Claude/random/wormWars/experiments/04a-navigation-primitive/RESULTS.md:89) says validation means reached “about 1.5–2.1 by generation 100” and stayed “within about 1.5–2.9 afterwards.” That is not an accurate range.

   In `train-B.json`, generation-100 validation means are **0.73828125 for run 9** and **0.5078125 for run 11**. Run 11 falls to **0.49609375 at generation 125**. Across all runs, **56 of 576 checkpoints after generation 100** are below 1.5.

   Suggested replacement: “At generation 100, 14 of 16 runs scored approximately 1.5–2.1; runs 9 and 11 scored 0.74 and 0.51. Subsequent checkpoint means ranged from 0.50 to 2.86, mostly within 1.5–2.9. Selected champions came from generations 175–950.” The pilot describes the eventual performance scale, but not every run’s learning trajectory.

2. **Disclose the small commit-level departure and distinguish execution from record commits.** The registration explicitly calls for the guarded smoke run **on the binding commit**. The smoke record instead names **`9531aaf`**, the binding commit plus the projection records. Its introductory description also incorrectly calls this “the binding commit.”

   This is harmless to the scientific comparison: the diff contains only records. Nevertheless, [RESULTS.md:107](/D:/Claude/random/wormWars/experiments/04a-navigation-primitive/RESULTS.md:107), “No deviation from the registration,” needs that qualification. Also clarify [D110](/D:/Claude/random/wormWars/DECISIONS.md:3344): the formal projection **ran at `e3d68be`**; its record was **committed at `9531aaf`**. Currently D110 mixes that record commit with execution commits for the later stages.

3. **Restrict the reliability conclusion to passing champions.** [RESULTS.md:80](/D:/Claude/random/wormWars/experiments/04a-navigation-primitive/RESULTS.md:80) describes navigating “reliably” and then says “The champions do.” Four champions failed precisely that criterion. Say **“The 12 passing champions do; all 16 passed the cue and improvement comparisons.”**

Under the repository’s correction rule, add a dated correction quoting these existing statements and explaining the changes. Leave the bound registration unchanged.

**Registration and numerical checks**

The formal execution is consistent with the registration:

- Execution commits are projection **`e3d68be`**, A **`7ec22bb`**, B **`75307a3`**, evaluation **`2b9ed94`**. Guarded files are unchanged across them. The local remote-tracking reflog records each required push before the corresponding start marker.
- All four stages record matching Python, NumPy, PyTorch, CUDA, GPU and connectome hashes. Configuration and E1-input hashes agree. The guards check committed predecessor records, loaded brain configuration, champion/baseline hashes and regenerated initial-population membership before evaluation.
- Run seeds **1105000–1105015**, world seed **1100001**, shaping assignments, training and validation ranges, hold-out range, and registered compositions match.
- All 16 runs contain **1,000 generations and 41 checkpoints**. I checked every checkpoint’s mean against its count sum, its hash against the corresponding generation log, and every champion against the **earliest maximum validation checkpoint**. All agree. Generation-0 baselines select checkpoint zero.
- `run_rules` implements the registered inequalities correctly: reliability **≥80%**; baseline, constant-probe and generation-0 lower bounds **>0.5**; mirrored contrast lower bound **≥0**.

I recomputed all **82 arm means** from their 1,024 counts, all reliability counts and paired contrast means. They agree with `evaluation.json` and the results table.

The shaped passing runs are **0, 2, 3, 4, 6, 7, 9, 10**; all four unshaped runs pass. The recorded non-reliability bounds support every corresponding pass:

| Quantity | Checked value |
|---|---:|
| Minimum baseline lower bound | 1.0302734375 |
| Mirrored-contrast lower bounds | 0.802734375–1.31787109375 |
| Real-minus-constant lower bounds | 1.7265625–2.697265625 |
| Minimum generation-0 lower bound | 1.2197265625 |
| Exact passing-share lower bound | 0.3908623018 |
| Accounted time | 10,476.266 seconds = 2.910074 hours |

I independently checked the binomial-tail identity for the share bound and the log-interpolated equivalent gains. The latter range is **3.5313–6.8503**. Oracle fractions are **22.5025–31.8619%**, correctly rounded to 23–32%. The listed controls differ from E1’s gate by at most **0.0546875**, so “within 0.06” is correct.

**Interpretation and suggestions**

- **The narrow-count explanation is fair.** For example, run 0 has only two zero-target episodes, 554 two-target episodes and 259 three-target episodes; **848/1024** reach at least two despite a mean of **2.1514**. Means near two can pass this rule. They do not necessarily pass: runs 8 and 11 illustrate that.
- **Cue-following is a fair behavioral conclusion.** The mirrored and constant interventions strongly reduce performance, and mirrored endpoints are closer to the decoy in **96.68–99.80%** of episodes. This does not identify bilateral comparison, temporal sensing or a neural steering mechanism. In the README, replace “go to the decoy” with the measured endpoint statement: median final decoy distances are **2.35–4.10**, so the statistic is not a decoy-arrival rate.
- **“Slow navigators” is supported.** The recorded finished-leg efficiencies and durations match the quoted ranges and support poor task efficiency. They do not directly measure low movement speed. The performance-equivalent-gain caveat is appropriate.
- **“Shaping was not needed here” is defensible.** Four unshaped successes demonstrate that this procedure can succeed without shaping. They do not establish equal success probabilities or no benefit from shaping. RESULTS makes that distinction; carry its **“descriptive, four runs”** qualification into the README’s “did as well.”
- **Run 2 is the correct E3 module under the registered selection rule**, despite run 12 being best overall. Its module hash matches its training champion hash. The hold-out selection caveat and requirement for fresh E3 worlds are appropriate; 04a does not establish E3 performance.
- Drop **“narrowly”** from the README’s failures: run 5 achieved 719 qualifying episodes against the required 820.
- Label the README commands as a **smoke check**, and add an actual replication procedure. Also label **304 seconds** as evaluation time **through the verdict**; the subsequent replay work is included in the 2.91-hour total.

**Scope:** I inspected the registration, results, README, D110, named JSON records, start markers, relevant implementation, commit history and local push reflog. I inspected the NPZ’s inventory—821 members, 43,811,891 bytes—but did **not** independently recompute its event-derived metrics. I checked their JSON values and defining code. I did not rerun bootstraps, simulations, tests or genome replays, and changed nothing.

**04a results: fix**