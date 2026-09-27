Task N is a reasonable basis for v2, but **v1 does not yet distinguish target-directed navigation from effective search, and its E3 transfer assumptions need correction**. I checked the files on `roadmap`; I ran no experiments and changed nothing.

**Must change**

1. **Require evidence that target information improves arrival, not just that arrivals occur.** Moving the target removes the reward for remaining at one food patch. It does not prevent broad circling, wall-following or arena coverage from collecting hits.

   Include tuned K explicitly in the baseline gate, alongside tuned movement baselines. Add a paired evaluation with the **scored target unchanged but its scent spatially displaced**, using the existing mirrored-food probe or an equivalent declared displacement. Require a meaningful performance loss when scent ceases to locate the target. Apply this to the evolved primitive as well as the scripted control.

   Do not require stereo specifically: temporal navigation is acceptable. Likewise, a foraging-derived policy that reliably follows the currently relevant cue to moved destinations qualifies as a navigation primitive. The distinction is functional, not the controller’s name.

2. **Specify the actual target-mode mechanics before piloting.** Several inherited behaviours could change the experiment substantially:

   - **Radius and strength:** the existing map builder scales patch radius by `sqrt(headcount/20)` and mass by `headcount/20`. With one wey, a configured radius of 1.5 becomes approximately **0.335**, unless target mode bypasses that scaling. Such a small rasterised patch can even miss all cell centres. Specify physical radius, source mass/amplitude, sensing scale and clipping. See [world.py:364](D:/Claude/random/wormWars/wormwars/world.py:364).
   - **Scent coverage:** this Gaussian is truncated at three sigma. Sigma 2 means a kernel extending six cells on each axis, not a weak signal throughout the arena. Some starts will have no target information. Measure zero-signal coverage and input saturation in the pilot; stronger amplitude cannot repair a region where the field is exactly zero. See [world.py:56](D:/Claude/random/wormWars/wormwars/world.py:56).
   - **Energy mechanics:** removing energy from the score does not disable eating, source depletion, movement costs or death. Explicitly disable consumption and drains for this task, keeping the wey alive for the full horizon. Preserve target-field mass during relocation or account for its changes in the energy ledger.
   - **Score plumbing:** `tune_batched` obtains its objective through `rollout_brain`, whose `_play` currently hard-codes `foraging_score`. A target mode in `World` alone is insufficient. Scripted tuning and evolution must both receive the target count. See [rollout.py:55](D:/Claude/random/wormWars/wormwars/evo/rollout.py:55).

3. **Replace the proposed gate with a pilot-calibrated, fully specified decision rule.** I would not accept 2×, 1.5× and 150 ticks as justified thresholds yet.

   A large ratio against an almost-zero baseline can describe an unusable navigator. Require both an absolute reliability floor and a practically meaningful improvement over baselines. In particular, report the fractions of episodes reaching **at least one and at least two targets**; the latter tests relocation within an episode.

   “Median time to reach” must include failures appropriately. A median over successful arrivals alone can reward a controller that succeeds rarely. Use first-arrival success plus a censored time analysis, or the simpler mean of `min(first-arrival time, horizon)`. Report subsequent-leg times separately.

   Use pilot/tuning worlds to choose task parameters, controller settings, margins and sample sizes; then freeze them before final evaluation. Select S versus M on tuning data, or account explicitly for selecting the winner on hold-out data. Specify a ratio of aggregate means if retaining ratios, including treatment of zero denominators. “Excluding 1.5” should mean **the lower confidence bound exceeds 1.5**.

   Finally, give 04a its own numerical gate and run count. Worlds quantify uncertainty for a fixed controller; independent evolution runs quantify repeatability of evolving one. Individual arrivals are not independent replicates.

4. **Define target pairing by event index, not merely “a per-world keyed RNG.”** Controllers reach targets at different ticks and at different positions. If rejection sampling measures D from the current head, or “free” excludes its current body, identical random candidates can produce different target sequences.

   The simplest reproducible design is a target sequence determined by `(evaluation seed, world id, target index)`, with separation measured between successive target centres and clearance determined by static geometry. Define initial-target separation from the shared spawn separately. If head-relative placement is preferred, acknowledge that common random candidates do not imply identical destinations.

   Also, world IDs alone do not identify layouts: the current generator uses **both `run_seed` and `world_id`**. Baselines and champions must share both. See [world.py:161](D:/Claude/random/wormWars/wormwars/world.py:161).

5. **Preserve the learned input mapping when moving to E3.** I disagree with “food for A, pheromone channel for B” if that means injecting B into different neurons in the copied module.

   Food currently enters AWA/AWC/ASE; ally pheromone enters ASK and enemy pheromone enters ADL. A frozen copy trained through the first mapping is not validated through the others. See [interface.yaml:19](D:/Claude/random/wormWars/configs/interface.yaml:19).

   Keep one canonical left/right **goal-cue input** at the existing food neurons. In E3, route A-related observations into those inputs of copy A and B-related observations into the same inputs of copy B. World-level A/B identity and visit confirmation remain distinct. This is a design commitment now; it does not require building the assembly layer now.

6. **Do not import T0’s score tolerance unchanged.** T0’s provisional `1e-4` bound concerns the continuous foraging score at specified configurations. For an integer arrival count, that bound requires exact equality. A tiny trajectory difference near a reach boundary can change an event and subsequently the entire target schedule.

   Declare E1-specific replay checks for counts and event sequences/times. Prefer same-device deterministic replay for saved-module evidence, retaining the code version and execution mode. CPU replay does not promise exact reproduction of a historical CUDA run. See [T0.md:123](D:/Claude/random/wormWars/docs/foundations/T0.md:123).

**Should change**

1. **Correct and strengthen the controls.** The proposed families are appropriate, but their descriptions are wrong:

   - K has **constant turning**, not random turns.
   - M compares with the **previous tick**, not a running average.
   - S adds stereo steering to a constant turn and uses a two-level speed rule.

   These are explicit in [scripted.py:82](D:/Claude/random/wormWars/wormwars/exp02/scripted.py:82). An exponential running average would be a new variant.

   Retune for arrival, allowing constant-speed stereo steering; slowing near food was useful for consumption and need not help reaching a destination. Use M’s average of the same stereo observations for a clean comparison.

   The existing `Straight` never turns at walls, and `ScriptedBrain` passes policies only food readings. A wall-reactive baseline needs access to the declared collision inputs—not privileged coordinates. Give all relevant controls comparable access.

   Tune random-walk persistence and circle speed/curvature on tuning worlds. Matching S’s average speed and turn rate alone does not produce a strong search baseline; one historical “typical curvature” is also too narrow. Replaying a small prespecified set of frozen 02 champions would be a useful additional check, not a required new experiment.

2. **Do not interpret failure of both scripts as proof of inadequate sensors or body.** S and M can fail because their exploration or wall handling is poor, particularly outside the finite scent footprint. First check implementation, signal availability, constant-speed steering and search behaviour. Redesign sensing only after diagnosing that failure. Conversely, one valid scripted navigator passing is sufficient to establish attainability; both need not pass.

3. **State the limited E3 claim.** E1 validates approach to a localised source. E3 requires following distributed, decaying trails through branching mazes. A controller that climbs a radial concentration hill may fail on a trail ridge, at a junction, or against a wall.

   The current map builder supplies a boundary wall, and the food blur does not respect internal wall occlusion. New world IDs therefore do not demonstrate generalisation across maze structures. Declare what walls will block, and put a small bent-trail/junction check at the start of E3 integration. Do not build a maze framework now.

   Preserve controller state across target relocations in E1. Otherwise the reset becomes hidden assistance. E3’s inactive-module state rule remains an explicit integration decision.

4. **Keep the pilot and implementation small but complete.** Pilot signal coverage, baseline strength, first/second-arrival reliability and the fraction of initial genomes receiving zero fitness. A scripted success does not establish that sparse counts provide enough selection pressure.

   Count pilot/tuning compute using T0’s existing accounting. Measure throughput on Task N itself. Use a fixed event record containing controller/run identity, world, target index/position, activation tick, reach tick and leg distance; retain unfinished legs for timing analysis. Target sequencing, score selection, replay and batch/chunk invariance warrant targeted checks. A general event framework does not.

**Minor**

- “02b found … steering weakly by side” reintroduces the causal interpretation that its corrected report explicitly rejects. Write “turn commands covaried with food side.” See [02b RESULTS.md:18](D:/Claude/random/wormWars/experiments/02b-champion-analysis/RESULTS.md:18).
- One wey removes **inter-animal** crowding. Its own body still contributes to the body field and collision observations; those inputs are not necessarily zero.
- Distinguish experiment 02’s task **T0/T1** from foundation milestones **T0/T1**.
- Defer Bridge 1 unless effectively free. A module registry, general channel router, reusable task framework or broad topology study would violate the intended restraint of the [roadmap tripwire](D:/Claude/random/wormWars/ROADMAP.md:62).

**Answers to open questions 1–6**

| Question | Answer |
|---|---|
| **1. One wey?** | Yes. Establish individual navigation first. Introduce peer obstruction during E3 integration. |
| **2. Food or new channel?** | Reuse food neurons as the canonical goal-cue interface. Route each goal into the corresponding copy’s identical inputs. |
| **3. Count or first-arrival time?** | Count primary, with absolute repeated-arrival reliability. First-arrival success and failure-aware latency are secondary. |
| **4. Thresholds?** | Pilot first, freeze before final hold-out evaluation. Include absolute performance, baseline improvement and cue dependence. |
| **5. Meaning of moved?** | Relocation after arrival is sufficient and fits stationary A/B destinations. Pursuit during approach adds unnecessary scope. |
| **6. E3 relevance?** | Useful as a local cue-following primitive, provided input mapping and state semantics transfer. It does not establish trail following, maze navigation or colony robustness. |

E1 design: proceed to v2