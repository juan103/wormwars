**The registered gate passed, and I found no unreported execution deviation. RESULTS.md needs a few reporting corrections and narrower claims about 04a.** I checked HEAD `20e98aa`, recomputed the gate statistics from the saved counts and events, and made no changes or simulation runs.

1. **The run followed the registration, on the available evidence.**

   The local remote-tracking reflog records the binding push at **17:38:17 UTC**, before the guarded smoke stages and the formal pilot marker at **17:38:55**. It records the freeze push at **17:44:43**, before the gate marker at **17:44:53**. These are local push records, not independently obtained server timestamps.

   The guarded smoke pair completed at `eb0b781`, with all **16 gate arms**, on smoke worlds **0–15**. Its experimental outcome was “not passed”; that is compatible with successfully exercising the guards and pipeline.

   I verified that:

   - The guarded code, configuration files, requirements and registration are unchanged between binding, pilot, gate and HEAD.
   - The recorded environments and connectome hashes match.
   - Every tuned winner is the **first maximum in its registered grid**, including the separate low-gain grid. S-const wins the navigator selection.
   - Coverage selects **σ=6, flagged**, exactly by the fallback rule.
   - The freeze’s LF-normalised hash matches the gate.
   - Pilot, tuning and gate IDs match their registered offsets and sizes.
   - Accounting matches the registered measurement shapes, all **1,836 tuning/oracle evaluations**, and **16 × 1,024 gate episodes**. There is one recorded formal pilot and one formal gate, both completed.
   - The budget was comfortably respected: **353.814 accounted seconds**, approximately **0.0983 hours**, against eight hours.

   I found no evidence of an extra formal attempt. Records and exclusive markers cannot prove that no unlogged execution ever occurred, but everything available is consistent.

   One archival improvement: the binding-commit guarded smoke evidence is currently local under `runs/e1-smoke/`, rather than committed alongside the earlier development records.

2. **The statistical numbers check out; the timing sentence mixes clocks.**

   Independently recomputing from `gate_events.npz` reproduces every arm’s counts and secondary measures exactly. The events also satisfy target pairing, separation, wall clearance, arrival radius, activation timing and continuity between legs.

   Recomputing the registered bootstrap reproduces all five lower bounds exactly:

   | Comparison | Lower bound |
   |---|---:|
   | Constant | 8.193359375 |
   | Random walk | 8.373046875 |
   | Wall-follower | 7.96875 |
   | K | 7.681640625 |
   | Cue contrast | 4.2880859375 |

   Reliability is exactly **1,023/1,024**. All displayed performance means, ratios, secondary measures and pilot measurements agree with the artifacts at the stated rounding. The pilot measurements are verified against `freeze.json`; their underlying generation-0 scores and coverage samples were not saved for independent reconstruction.

   **“E1 positive control: passed” is the exact registered wording.**

   Correct these reporting details:

   - [RESULTS.md:22](D:/Claude/random/wormWars/experiments/E1-navigation/RESULTS.md:22) uses **316 s** from pilot accounting but **36 s** from the gate’s internal timer. Consistent accounting gives **316.230 s + 37.584 s = 353.814 s**. Consistent internal timers give **315.326 s + 36.222 s**. Use the accounting figures for the compute claim. D100 repeats this inconsistency.
   - [RESULTS.md:122](D:/Claude/random/wormWars/experiments/E1-navigation/RESULTS.md:122) incorrectly calls the **0.94** comparator blind. That is **K, which reads scent level**. The best tested blind baseline is wall-following at **0.6484**. Write “all four gating baselines, including K” or use **0.65**.
   - Complete M-avg’s winner description with **fall threshold = 0**.
   - Describe **0.35** as the peak **goal-cue input current**. It is not the maximum across all sensory channels; the reported own-body collision current already exceeds it.

3. **The main interpretation is fair, with limits that should be explicit.**

   **Bang-bang:** justified as a description of the control law. The winner applies `clip(8192 × (left − right), −1, 1)`, saturating when the current difference exceeds approximately **0.000122** in magnitude. The actual fraction of saturated commands was not measured. Its success establishes solvability with a very sensitive scripted controller, not comparable sensitivity in an evolved N2 brain.

   **Mirrored decoy:** the collapse from **8.6797 to 0.0283**, together with the constant-probe result and unchanged blind baselines, strongly supports dependence on correctly located cue information. But the mirror supplies a misleading destination. The below-blind score does not quantify the contribution of information under simple cue removal, establish a general navigation mechanism, or demonstrate robustness to misleading cues. The mirrored arm’s apparently respectable finished-leg efficiency comes from only **29 arrivals**; it is strongly conditioned on rare successes.

   **σ=6:** the flag is correctly disclosed and does not invalidate the gate. Coverage was **1,124/1,280 prescribed leg starts**, leaving **156 below the reporting floor**. Below 5% does not mean zero signal or inability to steer. These samples use the spawn and previous target centres, not every controller’s actual relocation position. High gain can exploit signals below that floor.

   **Low-gain target:** **5.6152 targets, 63.88% of the oracle count**, is a useful scripted reference for 04a. Calling it demonstrably “realistic” for N2 goes beyond the evidence. There is no measured mapping from recurrent N2 dynamics to this scalar steering gain. Also, the low-gain winner has constant turn **0.2**, versus **0** for the unrestricted winner: this is a comparison between separately tuned policies, not a pure gain ablation.

   **Generation 0:** the zero share is **190/256 genomes**, across 64 worlds each, in the specified composition. This supports concern about sparse selection signals and triggers the design’s planned shaping provision. It does **not prove that unshaped evolution cannot work**. Replace “selection will need” with “this meets the design’s condition for bounded shaping,” including in D100.

   Likewise, M-avg’s result concerns this tuned one-step-memory family. It does not establish that temporal comparison generally underperforms stereo sensing. The oracle is a privileged reference policy, not a proven mathematical optimum.

4. **04a’s registration must make the following concrete.**

   **Shaping:** specify the exact fractional-progress formula, normalisation, handling of relocation and negative progress, and an episode-level bound below one arrival. Prevent repeated progress or relocation from accumulating an uncapped bonus. Record it separately and remove it from every benchmark and gate score.

   **Budget:** use the measured *aggregate* rollout rates, not 438 per run. For 32 genomes × eight worlds:

   | Runs batched | Aggregate episodes/s | Seconds per generation batch |
   |---|---:|---:|
   | 1 | 109.84 | 2.331 |
   | 4 | 336.14 | 3.046 |
   | 8 | 437.96 | 4.676 |

   For illustration, eight runs of 1,000 generations would require approximately **1.30 hours of these rollouts** when batched eight together. That excludes optimizer work, shaping overhead, validation, final probes, saving and failures. Commit the full budget calculation, explicit cap and stopping rules before running.

   **Composition:** fix training, validation, generation-0 comparison and final-evaluation compositions separately. The throughput measurements used `(32,8,1)`, `(128,8,1)` and `(256,8,1)`; the generation-0 result used `(256,64,1)`. Neither transfers an exactness claim across compositions. Preserve single-strain padding and specify replay checks. Batched evolutionary runs need separate optimizer state and random streams.

   **Gain and evaluation:** freeze sensing scale, neural input gain, motor gains, parameter bounds and any calibration procedure. Keep both scripted gain references; do not treat 5.62 as established N2 capability. Reserve 04a’s hold-out worlds, fix champion selection before their use, retain reliability/baseline/cue criteria plus a generation-0 comparison, and define the required share of independent evolutionary runs passing. Runs—not worlds or arrivals—are the replication unit.

Apply corrections through the repository’s dated correction process; the registered gate verdict itself does not change.

E1 results: fix (must-fix: consistent compute timing; correct K’s classification; qualify N2 attainability and shaping necessity; complete M-avg parameters and label the cue-current bound).