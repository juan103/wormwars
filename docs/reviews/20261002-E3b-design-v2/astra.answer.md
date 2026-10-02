**1. Verdict: proceed to E3b-0’s plan.** I checked `roadmap` at `0e33f23`, both v1 reviews, D172, the literature sources and the relevant engine code. The remaining problems can be fixed in the plan. This approves feasibility work, not E3b-1.

**2. The v1 items are mostly addressed, but “every point resolved” is too strong.**

| Status | Items |
|---|---|
| Resolved at design level | Identical seed/arm mechanics; +2.36 correction; restricted interpretation of selector-search failure; 2×2 evaluation; raw-entry and round-trip measures; removal of body-mediated peer signals; spawn distribution; geometry and independent arena size; exact per-wey fields and peers-only control; trees; evidence-based reflex choice and its baseline. |
| Appropriately assigned to E3b-0 gates | Budget and memory; exploration from empty fields; trail polarity/persistence; scent support and neural qualification; per-wey scoring/configuration changes; task-off equivalence and memory-assay recalibration. These are requirements, not demonstrated resolutions. |
| Partially resolved | Replay’s information content; sensing/movement shortcuts around walls; causal interpretation of discovery-order times; literature precision. Details below. |

**3. Literature: mostly fair readings, with several qualifications.**

- **Jackson is overstated.** “A pheromone trail alone carries no direction in real ants” changes absence of prior evidence into a universal biological claim. The paper reports no prior evidence of detecting polarity from pheromone alone and demonstrates geometry-based orientation in Pharaoh’s ants. Correct that sentence in the literature note, design and D172. [Jackson et al.](https://www.nature.com/articles/nature03105)
- **“Their comparisons rest on single runs” is too broad.** Jimenez-Romero appears to report one evolutionary trajectory per pheromone condition, but also reports **100 evaluation trials**. Say exactly that; do not extend the criticism to unverified AntFarm. [Paper, §3.1](https://arxiv.org/html/2212.08484v2)
- **Panait–Luke’s adjustment reading is correct.** Its accessible full text specifies topping up toward the neighbouring maximum minus a constant. That supports the proposed fallback’s motivation, not an unconditional guarantee that an unspecified adaptation will produce navigable gradients. [Author-hosted paper](https://cs.gmu.edu/~lpanait/papers/panait04ant.pdf)
- **Czaczkes 2013’s “alternating” means left–right turns at successive bifurcations**, not alternating destination goals. The quoted result is fair; make that distinction explicit. [Paper](https://journals.biologists.com/jeb/article/216/2/188/11672/Ant-foraging-on-complex-trails-route-learning-and)

The summaries of [Dodoková](https://link.springer.com/article/10.1007/s11721-024-00237-8), [Czaczkes 2024](https://epub.uni-regensburg.de/59034/1/s00040-024-00995-y.pdf), [Salman](https://www.nature.com/articles/s44172-024-00175-7) and [StarLogo](https://web.mit.edu/mitstep/starlogo/samples/ants.htm) are fair within their stated scope. The explicit refusal to claim novelty is appropriate.

**4. Remaining and new problems in v2:**

- **Wall isolation is incomplete.** Masked diffusion does not prevent sensory leakage. Current noses project beyond the head and use unrestricted bilinear interpolation. With a head at `x=3.99`, a wall occupying `[4,5)`, and the existing forward offset `0.6`, the nose at `4.59` already interpolates signal from the far-side cell centred at `5.5`. This is more than the declared wall repulsion. Specify occlusion or explicitly permit and measure it; also test sliding for corner shortcuts. [Sampling geometry](D:/Claude/random/wormWars/wormwars/world.py:732), [interpolation](D:/Claude/random/wormWars/wormwars/fields.py:26)
- **Different replay endpoints do not guarantee irrelevant trails.** Donor and recipient routes can share long segments with helpful gradients. Measure overlap and scripted usefulness across the evaluation distribution. Scrambling should explicitly replace **only peer contributions**, preserving live own trails. Matching total field mass alone does not match exposure at the noses.
- **Discovery order is descriptive, not itself causal evidence.** Compare the same colony/maze assignments across interventions, retaining censored failures. Also, peers need not become redundant after one round trip: own trails can evaporate. Keep later-trip effects.
- **Exit criteria overinterpret positive controls.** A scripted follower’s effect establishes measurement sensitivity, not power over independently evolved runs. Its advantage over the seed establishes behavioural headroom, not an accessible evolutionary improvement. Furthermore, for a follower using its goal’s channel, own-only cannot improve first discovery of that goal: its corresponding trail does not yet exist. Apply `shared > own > none` to an explicitly suitable endpoint, such as repeated-trip performance.
- **The 2×2 is useful but needs separate readings.** Improvement over the seed, dependence on trails, adaptation to trail availability, and benefit from peers are different claims. Prespecify their contrasts and outcome wording.
- **The polarity inequality needs its assumptions.** `λ > μ` describes the simplified single-pass calculation using exponential rates. If evaporation is a fractional loss `μ`, the threshold is `λ > −log(1−μ)`. Neither version guarantees sourceward gradients under revisits, stationary deposition, diffusion and superposition.

**5. E3b-0’s plan must pin:**

- A **bounded candidate search**, selection rule, fallback trigger and stopping rule within three GPU-hours; report failed settings too.
- Maze generator and independent random streams; endpoint/spawn eligibility and distances; visit regions; horizon; colony size; movement, corner and sensing rules. The oracle must respect turning as well as speed limits.
- Exact deposit/visit/timer update order; diffusion operator and rate conventions; zero-field behaviour; scent support, scaling and saturation checks. Empty fields necessarily include readings below `0.005`; qualification must cover that regime.
- Scripted exploration and sensory access, including wall inputs/reflexes; donor selection and timing; scrambling; quantitative thresholds for the six exit criteria. Revalidate attribution and peer isolation if the fallback makes deposition depend on shared concentrations.
- Raw versus confirmed discoveries, round-trip definition, `k`, censoring, paired contrasts and inference hierarchy: **independent evolutionary runs for E3b-1**, with maze/colony evaluations nested within them.
- Reference commit and equivalence tolerances declared before changes; failing/sabotage tests; actual-composition timing and peak memory; complete workload accounting and reserve. E3b-1’s power calculation must state its run-level variance assumptions and minimum detectable effects.