1. Original points. **D** below means `experiments/03-generation0/DESIGN.md`.

| # | Status | Evidence and remaining issue |
|---|---|---|
| 1 | **PARTLY** | [D:59](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:59): weighted caps cover all fitness mappings, but the proposed enforcement is flawed; see below. |
| 2 | **PARTLY** | [D:67](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:67): atomic orbit moves improve the specification, but introduce additional invariants and frozen gap edges. |
| 3 | **PARTLY** | [D:90](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:90): counts, retries, chains and turnover added. A plateau does not establish mixing; thresholds should reference each ensemble’s attainable plateau, not ordinary SH’s. |
| 4 | **ADDRESSED** | [D:79](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:79): five types and per-neuron partner-class profiles are correctly identified. Small-block feasibility remains an implementation check. |
| 5 | **PARTLY** | [D:31](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:31): readout correction is right. The predicted decrease under SH-mirror does **not** follow: symmetric support does not make independently weighted brains equivariant. |
| 6 | **PARTLY** | [D:24](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:24): appropriately narrowed claims and N2perm added; [D:198](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:198) reintroduces unjustified causal attribution. |
| 7 | **ADDRESSED** | [D:130](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:130): C becomes descriptive; constant-input control added and nonmonotone task deferred explicitly. |
| 8 | **PARTLY** | [D:135](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:135): silence, hazards and map ordering fixed; movement-cost/mortality policy remains implicit. “No graph has a mean valence” is still unsupported. |
| 9 | **ADDRESSED** | [D:167](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:167), [D:174](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:174), [D:202](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:202): duplicate removed, head-start secondary restored, margins use unselected pilots. |
| 10 | **PARTLY** | [D:166](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:166): normalization and shared bank added; denominator conventions, near-zero handling, aggregation windows and history decay remain unspecified. |
| 11 | **PARTLY** | [D:185](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:185): uncertainty and primary family added, but prediction-test calibration, Holm ordering and effect-threshold uncertainty remain wrong/incomplete. |
| 12 | **PARTLY** | [D:151](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:151): 16 worlds, pairing and graph unit fixed. Joint resampling across graphs using shared world indices is not specified. |
| 13 | **ADDRESSED** | [D:113](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:113): MR explicitly dropped pending its own design. |
| 14 | **ADDRESSED** | [timing.py:35](D:/Claude/random/wormWars/experiments/03-generation0/timing.py:35), [timing.json:23](D:/Claude/random/wormWars/experiments/03-generation0/timing.json:23): genuinely larger batches tested; plateau confirmed. “Compute-bound on dense products” still requires profiling. |
| 15 | **PARTLY** | [D:219](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:219): fitness arithmetic checks; calibration included. C, revised probes/history and constrained-graph calibration remain unbenchmarked. |
| 16 | **PARTLY** | [D:245](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:245): registration checklist improved and N2-rev descriptive. Nonfinite handling remains absent; structural acceptance thresholds are still frozen **after** ensemble construction. |

2. New flaws and consequences:

- **Routing:** [D:63](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:63) forbids adding direct edges while allowing their removal. That is irreversible attrition, not sampling graphs under a weighted cap. Also, individual weights ≤ cap do not guarantee their **sum** ≤ cap: AWCL currently has two weight-1 direct chemical edges and total cap 2. Specify reversible moves, joint weight allocation without replacement, and final aggregate/hop checks.

- **Mirror:** [D:69](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:69) preserves per-neuron degrees within orbit categories, not merely overall symmetry. Self-only swaps permanently freeze bilateral gap edges: I counted **46** in the cached graph, including AWAL–AWAR. Explicitly accept this stronger null or change the moves. Check orbit membership on the complete post-swap graph, including newly created self-images, overlaps and reverse proposals.

- **Holm/IUT:** [D:191](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:191) applies corrections in the wrong order for the global claim. Form \(p_j=\max_E p_{jE}\), **then Holm across four signals**. Separate Holm within each ensemble can produce approximately **18.5%** familywise error at nominal 5% when each signal has its sole true null in a different ensemble.

- **Prediction test:** [D:186](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:186): the stated \(t_{63}\) distribution requires assumptions not supplied; adding estimated N2 variance does not preserve exact calibration. Ensemble SD already includes measurement noise, and shared worlds introduce dependence. Ratio signals particularly need a justified distribution/error model. Rank resolution is not justification for parametric tails. Require uncertainty beyond the **effect margin**, not merely significance against zero plus a point-estimate threshold.

- **Attribution:** [D:198](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:198): three nonsignificant N2perm results cannot establish weight placement as the cause. Likewise, [D:131](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:131) preserves motor gains, **not realized drive**; constant input changes input statistics and neural dynamics as well as information.

- **Precision/order:** [D:207](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:207) requires N2’s SE during a shuffle-only pilot, contradicting [D:250](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:250). Also, with 64 SH graphs and equivalence margin \(0.25\,SD\), even zero N2 measurement error gives only about **26% compatibility power at exact equality** under an ideal normal model.

- **Budget:** 10.5 hours is a plausible estimate, not demonstrated feasibility. A rank-based Holm alternative needs at least **79 graphs/ensemble merely for resolution**, raising the same budget approximately to **12.8 hours**. [D:228](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:228) also retains the old 227-hour arithmetic: at exactly 2× throughput it is approximately **204 hours**, still over one week.

3. **Before implementing the affected components:** settle the sampler state spaces and reversible proposals; define P1/P4 numerically, including denominator failures; replace the verdict’s Holm ordering and specify its statistical model; remove the pilot’s dependence on N2 measurements.

Exact seeds, hashes, numeric tolerances, measured runtime and stopping rules can follow implementation, before registration. **Structural acceptance rules must precede final ensemble construction.** Generic infrastructure and shuffle-only feasibility work can start now.