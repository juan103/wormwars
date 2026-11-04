**Verdict: fix then proceed with E5-0.** The owner’s ladder is sensible, and a construction experiment is a reasonable interpretation of stage 05. The main fixes are to separate navigation transfer from capture, preserve the reused organisms’ actual interfaces, and define measurable gates before evaluation.

H1–H3 are preparation for the roadmap gate. Fresh world IDs in the same empty arena test new placements, not new map geometry. H4 must explicitly require competent moving prey on held-out obstacle maps. Likewise, energy off is a useful simplification, but “food other than prey limited is then trivially true” sidesteps the intended resource constraint. Call that part deferred. [Roadmap](/D:/Claude/random/wormWars/ROADMAP.md:655)

**Recommendations for §7, questions 1–5**

1. **Scent: start with the Gaussian on the hunter’s food channels.** This gives the cleanest transfer test. Use E1’s frozen settings, including its chosen σ, rather than `WorldConfig` defaults. Make the hunter’s signal exclude the prey’s food and corpse pellets.

   Treat pheromone tracking as a separate later condition. Feeding ADL is not a substitute that existing food navigators can be expected to use. Task N also disables pheromone deposition and sensing, so this alternative requires configuration changes.

2. **Capture: keep reach, then bite, but describe reach as a navigation bridge.** A living target is not *exactly* Task N: its body contributes collision input and crowding forces. `Stationary` commands zero motion; the world can still apply crowding displacement. Verify or explicitly pin H1’s prey position. [Movement code](/D:/Claude/random/wormWars/wormwars/world.py:1015)

   Calibrate bite damage first in controlled contact geometries—different orientations and offsets—then evaluate free pursuit. One energy value cannot guarantee a fixed kill time across orientations because armor, sampling and attack overlap change damage. Choose a reference duration, such as ten ticks in a specified sustained-contact configuration, and report the variation.

   For E5-0, use respawn without edible corpses, disable prey starvation and healing, and require hunter-attributed damage for a bite capture. Account explicitly for energy and body mass introduced or removed at respawn. Energy-on predation can follow later.

3. **H2: use 0.25, 0.5 and 0.75 as candidate speed rungs, not guaranteed-solvable rungs.** Express these against a fixed physical maximum, shared across hunters; also report realized speeds. Limited turning, initial separation, route geometry and the 300-tick horizon matter.

   Vary waypoint layouts, starting phase, direction and orientation by episode. Keep each route deterministic once drawn. Verify that the route controller actually completes its route at the commanded speed without wall stalls or impossible turns.

4. **H3: begin with a small, qualified suite of intact frozen organisms.** Include native-interface 02 T0/T1 champions and whole E4s-1 navigators; use E2/04a navigators as additional weaker or behaviorally different examples. Add E3 organisms when their required task signals and maze setting are supported. “Previously evolved” does not establish competent prey: qualify movement and task performance independently of how easily the candidate hunter catches them.

   Keep prey non-attacking initially. Mask novel enemy/damage inputs in the transfer condition, then expose them in a separately named interaction condition. Unmasked exposure is acceptable as an experiment, but it is not preserved behavior and does not establish learned evasion.

   There is a larger omission than ADL/ASH: **T1 used mono food sensing, T0 stereo; both used food blur and a reduced food sensing scale.** 02 also used graph-specific motor gains and sometimes remapped interfaces. The current world shares sensing settings and motor gains across swarms. Preserving these prey requires role-specific handling or an explicitly documented change of conditions. [02 task configuration](/D:/Claude/random/wormWars/wormwars/exp02/grid.py:48)

5. **Inert graft: structurally sound, with two qualifications.** Equal neuron count/order is needed; identical connectivity masks are not. Graft each prey’s original graph—including its null graph—rather than placing all prey on the hunter’s N2 connectivity.

   Also replace “behaves exactly as before” with a declared equivalence criterion. The existing test explicitly permits rounding differences: `1e-5` over 100 CPU neural steps. Test the selected artifacts over the intended horizon and composition, including behavioral outcomes. `Module.without_outputs` is appropriate; E4s-1 also already has a construction retaining output edges at zero weight. [Existing test](/D:/Claude/random/wormWars/tests/test_graft.py:105), [E4s-1 constructions](/D:/Claude/random/wormWars/wormwars/e4s/arms.py:1)

**Reuse and factual corrections**

The basic world, attack accounting, scripts and common-neuron-count limitation are described substantially correctly. The local genome collections named for 02, E2, 04a and E4s-1 exist. However:

- E1’s **8.68 and 98.7%** are correct. E4s-1’s **7.14** is the mean of the M arm’s final brains, not every evolved grafted brain. Reuse the **whole brain**: the selected run 10’s module scored zero on both carriers. [E4s-1 results](/D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-1/RESULTS.md:115)
- “E2’s and 04a’s champions: 2.0–2.8” is a typical-performance description, not their full range: E2 includes a failed GA champion at 0.75 and an extended-ES champion around 2.9.
- `make_frozen_suite` creates random-weight opponents, not competent evolved prey. Reuse the hall-of-fame and scheduling machinery, not its suite definition or energy-difference scoring unchanged. [Coevolution code](/D:/Claude/random/wormWars/wormwars/evo/coevolve.py)
- Useful omissions are **M-avg/K controls**, E1’s cue interventions and event/statistical machinery, and the **designed L1 comparator on its carrier** as a neural positive control.
- E3’s maze geometry, collision and sensing routines are reusable, but `MazeWorld` currently requires one swarm. H4 is an adaptation project, not simply selecting island maps. [MazeWorld](/D:/Claude/random/wormWars/wormwars/e3/maze_world.py:201)

Two Task N details need redesign. Its sequence guarantees separation between consecutive **target centers**, not D from the hunter’s actual position. Moving prey make that distinction larger. Its unfinished-leg progress also assumes a stationary target; do not copy that tie-break into pursuit unchanged. For E5-0, rank by captures and log distance separately. [Target machinery](/D:/Claude/random/wormWars/wormwars/world.py:523)

**E5-0 controls and decision rule**

The proposed controls are insufficient. Add:

- A **stationary hunter**, directly measuring captures caused by prey approaching.
- A privileged pursuit/contact controller, distinguishing geometrical feasibility from failure of E1’s particular steering policy.
- Hunter-only constant-cue and bilateral-mean interventions on the same frozen hunters. Keep prey observations unchanged.
- An attack-disabled check: bite captures must be zero.
- Separately tuned blind baselines. The wall-follower is blind to scent, but its collision input includes prey bodies; it is not wholly blind to prey.

Do not require E1’s navigator to catch every slower prey. That assertion is wrong for finite-horizon pursuit. Preserve it as a transfer reference; an adapted controller using declared observations can establish task solvability.

A proportionate rule I would adopt is **64 calibration worlds, then 512 fresh paired evaluation worlds per frozen condition**, reserving the eventual roadmap test suite entirely. Freeze settings and controller choices after calibration. Proposed thresholds—not empirical facts—are:

| Reading | Fixed rule |
|---|---|
| **Solvable** | The observation-limited positive control has a one-sided 95% lower bound above 80% for at least one capture within 300 ticks. |
| **Useful separation from accidents** | Its paired mean capture advantage over every tuned blind control has a 95% lower bound above 0.5 captures/episode. |
| **Too easy for testing pursuit** | A blind control’s mean is demonstrably at least 80% of the positive control’s mean. An interval crossing that boundary is inconclusive. |
| **Reused hunter qualifies** | It meets the reliability and blind-control margins; its intact cue also beats its constant-cue condition. |
| **Falls off** | Report the first failed rung **within each speed series**, distinguishing demonstrated failure from uncertainty. Do not assume H2b/H3 are monotonically harder. |

Bootstrap paired differences over independent worlds/routes, not individual captures. Report each frozen genome separately before summarizing a family. Separate calibration from evaluation, as D262 did.

**Principal risks**

D026’s lesson is stronger than “make hunting pay”: **damage can occur because the other animal approaches, and metrics can encode their own apparent success.** With non-attacking prey, unanswered-damage share is essentially guaranteed by design. It cannot demonstrate tactics. Capture superiority over stationary/blind controls and dependence on informative cues are the relevant evidence. [D026](/D:/Claude/random/wormWars/DECISIONS.md:316)

E2d supports an operational non-stereo plateau, not proof of a particular temporal algorithm or an immutable architectural ceiling. Moving sources may disrupt whatever strategy those brains use. Measure that transfer; do not assume more optimization will fix it. [Corrected interpretation](/D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/RESULTS.md:249)

E4’s fragility argues for testing mutations around the actual chosen hunter before authorizing E5-1. Bias-only perturbations roughly halved E-G’s score on one diagnostic block; that does not establish the same sensitivity in E4s-1. Preserve frozen references and test inherited function during adaptation. [E4 diagnostics](/D:/Claude/random/wormWars/experiments/E4-two-minds/RESULTS.md:58)

**Cost**

“One to a few CPU hours” is possible, but currently unsupported. E4s-0 recorded approximately 306 episodes/s for one GPU composition, with substantially different rates for others. Benchmark scripted and neural hunters separately with combat, intended batches and event logging. Enumerate genomes × conditions × probes × worlds before estimating hours. [Timing record](/D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/project.json:383)

The E5-1 analogy has a definite error: **16.61 GPU-hours covered 80 runs, not 16.** Correct it; it does not yet justify a 5–20-hour forecast.

Proceed after fixing the observation contract, capture/respawn semantics, equivalence wording, controls and thresholds, and cost accounting. No evolution is needed to resolve these questions.