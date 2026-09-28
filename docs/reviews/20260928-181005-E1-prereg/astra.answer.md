**Revise before binding.** The core task matches the design, but the cue-use inference and several enforcement/reporting claims need correction.

I checked `roadmap` HEAD `f83bd1941153e7b71b481d7334669926633f30f4`, the requested files, the earlier reviews, and T1 §7. All **25 supplied tests pass**. Additional checks used existing test fixtures or synthetic counts. I ran no pilot or gate and changed no files.

1. **Implementation versus design**

The main mechanics match:

- The target enters sensing, never the FOOD energy field; energy costs, eating, hazards and pheromones are disabled.
- Target sequences use a separate stream keyed by seed and world identity, respect separation and clearance, and remain paired across controllers.
- Arrival advances the target without resetting controller state.
- Rollouts select arrival count as fitness.
- Ordinary scripted controls receive declared sensor currents; only the oracle receives position, heading and target coordinates.

See [task.py:31](D:/Claude/random/wormWars/wormwars/e1/task.py:31), [world.py:479](D:/Claude/random/wormWars/wormwars/world.py:479), [world.py:635](D:/Claude/random/wormWars/wormwars/world.py:635), [rollout.py:75](D:/Claude/random/wormWars/wormwars/evo/rollout.py:75), and [controllers.py:92](D:/Claude/random/wormWars/wormwars/e1/controllers.py:92).

There are definite reporting defects:

- **Path efficiency is wrong.** [e1.py:305](D:/Claude/random/wormWars/scripts/e1.py:305) uses the previous target centre as the leg’s start. The head actually starts wherever it entered the previous goal disc, and the next leg also ends before reaching the centre. In the existing four-world oracle fixture, **15 of 20 subsequent completed legs have “efficiency” above 1**, reaching 1.074. Record actual head positions and define the numerator explicitly: either endpoint displacement, or shortest distance from the starting head to the destination disc.
- **The event table is discarded.** The world and rollout construct it correctly, including unfinished legs, but [e1.py:377](D:/Claude/random/wormWars/scripts/e1.py:377) saves only summaries and counts. Persist the gate events with controller labels, world IDs and target indices. Default CUDA replay is not a substitute for retaining the original observations.
- **“Constant probe for every controller” is not implemented literally.** The enumeration at [e1.py:351](D:/Claude/random/wormWars/scripts/e1.py:351) omits the unselected navigator and the small-gain variant’s constant probe. Implement the promised reporting or explicitly narrow its scope before binding.

2. **Registered numbers and statistical rules**

The numerical choices are defensible operational criteria, although their feasibility is unproven:

- `A=1`, peak cue current `0.35`, `R=1.5`, `D=8`, and clearance 3 are coherent. Consecutive discs are disjoint.
- The σ candidates, 5% floor, 90% share and flagged fallback form a complete mechanical rule. The floor measures concentration availability at prescribed reference points; it does **not** establish usable steering gradients.
- The grids and tie-breaking are explicit. Selecting between S-const and M-avg on tuning data is appropriate. Reporting the unrestricted and small-gain S variants distinguishes task attainability from plausible neural gain.
- Reliability means **at least 820 of 1,024 episodes** reach two targets. That is a clear sample criterion, not a confidence statement that population reliability exceeds 80%.
- A 0.5-target baseline margin and paired world bootstrap are reasonable. Worlds are the correct resampling unit. Requiring every component to pass supports the intersection argument against a multiplicity adjustment.
- The eight-hour cap is a reasonable resource decision; successful completion within it remains to be measured.

**The cue bound needs fixing.** [e1.py:370](D:/Claude/random/wormWars/scripts/e1.py:370) bootstraps `real − mirrored` but compares its bound with half the **observed** real mean held fixed. That is the written algorithm, but it is not a calibrated 95% lower bound for the claimed proportional effect.

For a 50% drop, bootstrap the paired contrast

`0.5 × real_count − mirrored_count`

and require its lower bound to be nonnegative. This accounts for uncertainty and covariance in both quantities. On synthetic paired counts alternating `real={2,6}`, with `mirrored=real−2`, the current rule passes; the correct contrast’s lower bound is **−0.05078125**. The distinction is substantive.

Fixing A, R, D, margins and sample sizes now is a legitimate tightening of the earlier design, which allowed pilot calibration. It increases the chance of an inconclusive gate, but does not invalidate a pass. I would not reopen these choices merely to improve the likelihood of passing.

3. **Pre-registration disclosure and σ**

**Keep the σ rule unchanged.** Adding σ=8 or lowering the share because of the observed 0.875 would be adaptation to those data. A flagged fallback was already an explicit outcome of the rule; it should remain one.

The disclosure identifies the exposure adequately, but two qualifications are necessary:

- [PREREGISTRATION.md:3](D:/Claude/random/wormWars/experiments/E1-navigation/PREREGISTRATION.md:3) claims publicity before “any registered measurement.” The debug calculation was the registered σ measurement on part of the registered pilot sample. Say instead that registration precedes the **formal pilot and gate, with the disclosed earlier calibration exposure**.
- I cannot independently verify that the rule predates the debug run. The runner and disclosure first appear together in `f83bd19`; committed history provides no earlier version proving that ordering. Retain the claim as an attributed development-history statement, or support it with a contemporaneous record.

Also, “the binding commit is the one that first contains this file together with `scripts/e1.py`” already identifies this draft commit. Specify how the reviewed version becomes binding and record the public push before the formal pilot.

Correcting statistical inference or implementation defects is a principled change unrelated to the σ result. Changing the coverage requirement to rescue that result is not.

4. **Gaming, silent failure and enforcement**

The protections are useful, but weaker than their descriptions.

- **Single-use is not enforced across interrupted or concurrent runs.** [e1.py:254](D:/Claude/random/wormWars/scripts/e1.py:254) and [e1.py:318](D:/Claude/random/wormWars/scripts/e1.py:318) check only completed output files. An interrupted gate can already have evaluated gate worlds and still be rerun. Use an exclusive, persistent stage-start record before evaluation, preserve failed attempts, and declare the technical-failure/resumption policy.
- **Committed does not mean mechanically valid.** [e1.py:320](D:/Claude/random/wormWars/scripts/e1.py:320) checks tracking, cleanliness and equality of `registered`. It does not validate the chosen σ, navigator, baseline parameters or tuning winners. A committed freeze containing altered derived choices passes those checks. Retain grid scores and validate selection, parameter membership and tie-breaking; validate σ against the recorded coverage rule.
- **Code/configuration can change after the pilot while `REGISTERED` stays identical.** The gate reconstructs configuration from current code. Compare the relevant code/configuration identity against the pilot, allowing the expected freeze-only commit, and record the resolved configuration.
- **“Clean tree” is overstated.** [e1.py:94](D:/Claude/random/wormWars/scripts/e1.py:94) checks only `wormwars`, `scripts` and `configs`; the registration itself can be dirty. Protect the registration and other declared inputs, or describe the narrower check accurately.
- **The declared execution environment is not enforced.** [e1.py:422](D:/Claude/random/wormWars/scripts/e1.py:422) permits CPU and automatically falls back to it. Formal runs should reject an execution mode inconsistent with the registration. Record runtime versions and data hashes alongside the commit.
- **The cap can be exceeded while producing a valid-looking result.** Checks occur before work units, with no final check before either output. The last rollout, oracle evaluation or bootstrap can cross the cap. Add bounded checking and a final budget decision; explicitly define any unavoidable in-flight overrun.
- **Smoke isolation currently works:** separate IDs, output paths and altered registered sizes prevent normal smoke runs from using formal E1 worlds.

The existing rule tests do not exercise these failure paths. Add refusal, interruption and cap-boundary tests before relying on the enforcement claims.

5. **T1 composition finding**

It matters, but it does **not** invalidate this gate.

Generation 0 really runs as **256 strains × 64 worlds × one wey**, in one chunk, and records that composition at [e1.py:195](D:/Claude/random/wormWars/scripts/e1.py:195). Its statistics and throughput apply to that composition; they do not establish equivalence to later evolution or checkpoint shapes.

Scripted controllers avoid neural `bmm`, and the gate’s paired arms share the declared single-strain, 1,024-world composition. Nevertheless, “no neural batch” does not prove general composition independence.

There is a separate, concrete batch dependence in [controllers.py:64](D:/Claude/random/wormWars/wormwars/e1/controllers.py:64): random-walk noise follows tensor shape and generator consumption, not world identity. In a direct check, identical first-world slots agree at tick 0 but differ from tick 1 when changing one strain to two. Key noise by world identity if chunk invariance/common noise is intended; otherwise document this as part of the execution composition.

Accept composition-specific results, retain matching gate arms, and test actual shapes before making cross-composition equality claims. Exact integer representation of counts is not a guarantee of repeatable trajectories.

E1 pre-registration: revise — must fix: cue inference; event retention and secondary reporting; freeze/configuration/environment validation; interruption-safe single-use enforcement; cap enforcement; binding and disclosure wording.