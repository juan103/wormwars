I read the 01b results and pre-registration, D008, D028, D030 to D033, the interface config and loader, the calibration module, the genome initialisation, the roadmap draft and Astra's review. Findings below, checked against those files where a claim was checkable.

**1. Correct-vs-wrong mapping**

1. MAJOR. One wrong mapping is not a test, because for SH and RD "correct" is not a label with meaning. The right null is the distribution of fitness over many sensory mappings, and the claim is that N2's correct mapping sits in the upper tail of its own distribution while SH's "correct" mapping sits nowhere special in SH's. Pre-register the interaction: (correct minus mean-of-random) for N2 minus the same for SH. Four to six random mappings is the minimum to estimate the spread.

2. MAJOR. Random mappings must be matched on chemical out-degree of the injection neurons and on hop distance to the motor read-out neurons. The read-out is AVA/AVB/AVD/PVC, and in the real graph touch neurons ALM/AVM/PLM synapse onto exactly those cells. So "food into touch neurons" is shorter to the read-out than "food into ASE/AWA", and on a reflex task N2 may do better with the wrong mapping. That result would say nothing about specialisation. Compute the hop-distance and degree tables for every candidate set before the pre-registration, and choose wrong sets from real sensory neurons of other modalities that match ASE/AWA/AWC on both. Keep bilateral pairs, six injection channels and the same sensor gain. Vary only the task-relevant channels and leave the motor read-out fixed.

3. MAJOR. Calibration currently uses N2 as the reference, measured in a world with sensory feedback (`wormwars/calibration.py`). Every new mapping changes the random population's drive, so each cell needs its own gains, and the reference must not be N2-correct. Calibrate every graph-by-mapping cell to a fixed absolute target, or calibrate on a sensor-silent probe. 01b already reported that the residual favoured N2 over SH.

4. MINOR. The "correct" mapping is itself contestable. Hazard heat into AFD is a thermotaxis neuron, not a nociceptor; ASH or FLP is the defensible choice for noxious avoidance. Fix and cite each correct assignment before anything else, since the whole test rests on it.

5. MINOR. Initial weights are anatomical magnitudes with random sign (D028), so any generation-0 advantage mixes topology with anatomical weight magnitudes. Pre-register the generation-0 versus gain decomposition as primary this time, not exploratory.

**2. Tasks**

6. MAJOR. Use two tasks that keep the sensor set and read-out identical and differ only in the required behaviour. Worm-like: mono-nose chemotaxis (klinotaxis, needs a moment of memory) plus hazard avoidance, both things the animal does. Not worm-like: the same world with the valence reversed, food only inside hazard zones and hazard damage removed, so the network must approach what nociceptors report. The nociceptor-to-AVA pathway is a real topological asymmetry, so this is the sharpest contrast available with the existing sensors. Stereo foraging is not a worm behaviour and should not be the "worm-like" arm.

7. MAJOR. Diagnostic controllers before a task counts: a memoryless proportional controller (turn on left-minus-right, constant forward), a one-step-memory controller (turn when concentration drops), a reflex "reverse on hazard" controller with both signs, and an untrained population. Mono chemotaxis counts only if the memoryless controller scores at the untrained level and the memory controller near ceiling. Report each task's ceiling and floor and express scores on that range.

**3. Plasticity**

8. MAJOR. One rule: reward-modulated Hebbian with a handful of global coefficients evolved (rate, decay, bound). Skip pure Hebbian. Short-term plasticity is a second, cheaper column if budget allows. Feed the reward signal as an input channel in every column, plastic or not, so information access is matched. Matched parameters follow automatically if coefficients are global, and edge counts already match across graphs.

9. MAJOR. To avoid crediting plasticity for activity-based memory: run the fixed-weight column on every learning task, and on evolved plastic champions freeze the rule at test time and separately reset activity mid-episode. The drop under each ablation is the evidence. This is Astra's R04 and it still applies.

10. MAJOR. Weights that change within a lifetime raise the in-degree-weighted step gain that D032 already found under-resolved at 8 substeps. Fix the integrator (semi-implicit or 32 substeps) and re-validate on evolved genomes before any plastic run.

**4. Statistics and budget**

11. MAJOR. Pre-register the interaction in point 1 as the single primary contrast, hierarchical bootstrap with runs nested in graphs nested in mappings, Bonferroni over the number of tasks. Use the mean held-out score over the last five generations, not one generation. Smallest effect of interest: 0.10 of each task's floor-to-ceiling range, chosen because it is about the size of the N2 minus RD final effect in 01b when scaled.

12. MAJOR. Power is the problem. In 01b the N2 minus SH final-score interval had half-width about 0.09, dominated by between-graph variance (SH interval 0.16 wide, N2 0.08). An interaction of two such differences has roughly double the variance. Go to 10 SH graphs at 2 runs each and 20 N2 runs, and consider dropping RD except in the anchor cell, since SH is the control that matters and SH and RD never separated.

13. Budget, at 25 generations and current substeps, one cell is about 1 GPU-hour per 45 runs.

| design | cells | runs/cell | substeps | GPU-hours |
|---|---|---|---|---|
| 2 tasks × 5 mappings × 2 plasticity, N2+SH+RD | 20 | 45 | 8 | 20 |
| same, 32 substeps | 20 | 45 | 32 | 60 |
| same, 60 runs/cell, 32 substeps | 20 | 60 | 32 | 80 |
| recommended cut (point 15) | 10 | 60 | 32 | 40 |

**5. What would make it uninformative, and what to cut**

14. MAJOR. The grid fails if any of: tasks are solved by generation 0 or have no headroom; N2 stays the calibration reference; wrong mappings are unmatched on hops and degree; the interaction interval ends up plus or minus 0.15 and the answer is "no conclusion". The last is the likely outcome at 01b's replication level.

15. Cut first: the plasticity column, which is a separate question and can be experiment 03. Then RD. Then the third task. Keep two tasks, correct plus four matched random mappings, N2 and SH, more graphs than before.

**The one change:** replace "one correct versus one wrong mapping" with "correct versus a set of degree- and hop-matched random sensory mappings", pre-registering N2's percentile against SH's as the primary outcome. Without it, the touch-neuron shortcut to the command interneurons can produce either sign of result for reasons that have nothing to do with specialisation.