**I recommend option 2: one bounded validation of 6 × 6, k_r = 0, at 1,800 ticks.** Claude’s reason for dismissing it is not supported by the saved trajectories. Option 4 remains defensible, but I would not relax G1b before testing this concrete alternative.

I checked HEAD at `6bc3bfc`, the committed records and implementation. I also analysed the saved trajectories after verifying their SHA256 hashes against the committed manifests. I changed no files and ran no simulations.

**The shorter horizon has more support than the recommendation acknowledges.**

I screened horizons {1,600, 1,800, 2,000, 2,100, 2,200, 2,400} at all three k_r values. For each trajectory, I counted `0 ≤ visit_tick < H`, recomputed colony means and B_max over **every played blind member**, and applied the existing gate. The 2,400-tick counts reproduced the committed records. These are new exploratory calculations from the files identified in [calibrate.json](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3d/calibrate.json), using the definitions in [e3d_gate.py](D:/Claude/random/wormWars/wormwars/e3/e3d_gate.py:40).

At **k_r = 0**:

| Horizon | B_max | Shared follower | Follower/oracle | Seed median legs | Failed criteria |
|---:|---:|---:|---:|---:|---|
| 1,600 | 1.579 | 10.054 | 0.358 | 3.875 | None |
| **1,800** | **1.761** | **11.630** | **0.367** | **4.625** | **None** |
| 2,000 | 1.960 | 13.261 | 0.376 | 5.313 | None |
| 2,100 | 2.063 | 14.051 | 0.379 | 5.625 | G1b |
| 2,200 | 2.154 | 14.881 | 0.383 | 6.063 | G1b |
| 2,400 | 2.337 | 16.531 | 0.389 | 6.813 | G1b |

At 1,800 ticks, the seed scores 6.457 visits, G1a is 0.151, and the oracle’s visited share remains 1.0. All criteria also pass on the truncated point estimates at k_r = 2 and 4.

**This is not a new validation pass and does not change E3d’s verdict.** It is evidence for selecting a candidate for fresh validation. Using the repository’s paired bootstrap:

- B_max at 1,800: **1.761 [1.656, 1.872]**.
- Follower/oracle: **0.367 [0.308, 0.428]**.

G2a remains uncertain. Shortening does reduce the ratio, as Claude anticipated, but it does **not** make the screened point estimate fail. I prefer 1,800 over 2,000 because the latter leaves only 0.040 visits below G1b; its B_max interval crosses 2.0. I am not claiming 1,800 is optimal.

**The next validation should be a fixed attempt, not another search.**

Bind 6 × 6, k_r = 0, H = 1,800, unchanged signal dynamics and thresholds, a declared blind family, and fresh calibration and confirmation blocks. Using the existing 128/256 block sizes is reasonable. Require all six criteria, the oracle precondition and feasibility floor; retain the original distinction between point-estimate acceptance and reported uncertainty. If it fails, report that and stop this sequence of horizon adjustments.

The incremental cost looks modest. E3d’s calibration took 2,459 seconds for three 128-maze blocks. A single-setting 128 + 256 design has the same number of maze episodes per controller; scaling by 1,800/2,400 gives roughly **0.51 GPU-hours for that existing control workload**, before extra confirmation conditions, checks and reporting. This is an extrapolation, not a measured projection. Use the runner’s projection and a fixed ceiling, such as the previous three-hour ceiling. The runner and registration work also cost time.

A declared exploratory selection followed by untouched validation is an appropriate response to forking paths. **Changing the acceptance claim after observing failure is itself a design fork**; option 4 does not escape that issue merely by avoiding another run.

**How I weigh the other options:**

- **7 × 7, longer horizon:** lower priority. The required increase in follower/oracle is indeed about 2.1–2.5-fold, and the oracle also gains time. The records show reduced later-leg rates as well as delayed discovery, so extra time is not an established remedy. Cost rises with horizon.
- **7 × 7, stronger signal:** plausible, but less targeted by present evidence. The scent-reach split does not identify the cause. Also, extending the cutoff alone leaves the Gaussian tail below the scripted follower’s detection threshold; a useful change may require changing σ, gain or threshold. Trail persistence changes another part of the task and needs fresh qualification. See [E3d’s scent definition](D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:110).
- **Option 4 at 6 × 6:** acceptable as a new, narrower task-design decision. Its advantage is existing separation between the tested navigators and blind controls. Its disadvantage is accepting substantial blind success without confirmation.
- **Stop general maze validation:** reasonable if the owner prioritises E4’s causal question. An alternative is to make E4’s private-information diagnostic primary and the shuttle secondary—for example, a balanced cue available only to A that determines a consequential choice made by B. That addresses whether information must cross more directly than further adjustments to general coverage.

**Whether using option 2 or option 4, E4 needs more than scores above the random walk.**

The proposed requirement to “clear the blind references” is insufficient for useful transfer. Two independently operating navigators can beat blind controls without sharing useful information. I would require:

1. **Separate task competence from transfer.** Demonstrate navigation and repeated shuttling, then test a prespecified benefit attributable to cross-links. The cross-link effect itself need not exceed 2.3 visits; that historical score is neither an effect-size threshold nor a universal blind ceiling.

2. **Remeasure references on E4’s test mazes.** Freeze controller definitions, not their historical scores. Retain a declared blind family and test E4 champions with their noses removed. If claiming that adapted coverage cannot compete, include an island-trained blind arm; E3c champions evolved on trees do not establish that.

3. **Use matched training and causal interventions.** Compare independently evolved runs with and without cross-links, plus acute cuts, information scrambling, sham interventions and suitably matched within-module disruption. Count evolutionary runs as replicates for training comparisons; do not treat colony members as independent runs.

4. **Make the information requirement explicit.** Include the roadmap’s diagnostic where A receives information B needs. Validate a working transfer control and an information-unavailable control. Prespecify outcomes distinguishing useful transfer, nonspecific disruption, failed navigation and inadequate precision.

5. **Account for shared trails and alternative routes.** At k_r = 0, the scripted follower falls from 16.53 to 2.93 without trails, against B_max = 2.34. The large advantage concerns scent **and trail** navigation. Own/peer or replay controls, or a diagnostic that prevents the private cue entering trails, are needed to distinguish neural transfer from environmental information paths. [E3d results](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3d/RESULTS.md:162)

There is also a concrete implementation issue: [the roadmap](D:/Claude/random/wormWars/ROADMAP.md:414) assumes the inactive module’s motor output is switched off. **The current seed does not implement an exact disconnection:** it suppresses comparator responses through saturation while retaining motor connections. [organism.py](D:/Claude/random/wormWars/wormwars/e3/organism.py:72) E4 must implement or otherwise establish the required isolation. Even with exact motor gating, a lesion applied earlier can change B’s later starting position and trails; phase-specific interventions from matched states are needed for the claimed inference.

**k_r = 0 is a sensible default, not an established optimum.** It preserves the most maze structure, following the original rationale. Its historical blind score is slightly lower, but these records do not establish superiority over k_r = 2. Freeze it for that structural reason rather than claiming it won a comparison. [Selection rule](D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:201)

Finally, the factual qualifications to Claude’s claim are:

- The approximately **7× follower and 4× seed** figures are correct for shared-trail calibration. “Wall-following is defeated” needs the qualifier **for the tested controllers and starts**.
- G1b is a chosen threshold, but exceeding it reflects substantive behaviour: at k_r = 0, **40.5%** of the best walk’s weys complete a round trip. Relaxing it changes the claim, not merely presentation.
- The shorter-horizon dismissal is unsupported and now has contrary exploratory evidence.
- E3e’s wording that the trail-free follower is “at or below” the walk is literally wrong at k_r = 0 and 2: **1.554 > 1.495**, and **1.520 > 1.513**. The defensible interpretation is near parity with no demonstrated reliable advantage; my paired bootstrap intervals for those differences cross zero. [E3e comparison](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3e/RESULTS.md:145)