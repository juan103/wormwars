I would revise this before freezing it. The fraction spends too much on remap breadth and too little on establishing what behaviour the task actually rewards. I checked the implementation and queried the cached connectome directly; I did not reproduce the GPU timings.

Points 1–11 are ranked roughly by expected damage.

1. **MAJOR — T1 can succeed without temporal food sensing. The proposed diagnostic does not establish otherwise.**

   Copying food concentration to both sides removes one source of spatial information. It leaves stereo pheromone, hazard and collision inputs intact. Pheromone is deposited continuously, including by the animal sensing it, so the environment itself stores movement history. These mechanisms are explicit in [world.py](D:/Claude/random/wormWars/wormwars/world.py:436).

   Even with those channels removed, a memoryless controller can potentially forage by moving quickly at low concentration and slowing or turning at high concentration. Failure of one proportional controller establishes only that that controller failed.

   **Detection:** the current diagnostic and behavioural replay are insufficient. Add a reasonably optimised memoryless controller with the same observations and motor limits as the memory controller. Evaluate champions with food input removed, replaced by a constant, and replaced by a distribution-matched unrelated signal; separately remove pheromone input/deposition. A short neural-state-reset evaluation is useful supporting evidence, although resetting state also disrupts ordinary signal propagation.

   Do not call T1 memory-demanding unless success demonstrably depends on informative food history, rather than merely surviving these baseline comparisons.

2. **MAJOR — “Foraging fitness” mixes food acquisition, corpse recycling, hazard avoidance and energy conservation.**

   Food sensing reads **FOOD + PELLET**. Eating consumes both. Death converts body mass into pellets. Fitness is surviving energy divided by starting energy; body mass is excluded from that denominator. With the defaults, initial body mass is half the starting energy budget. This is a substantial alternative resource, and the energy ledger correctly treats it as conserved—it will not flag corpse recycling as an exploit. See [eating](D:/Claude/random/wormWars/wormwars/world.py:606), [death](D:/Claude/random/wormWars/wormwars/world.py:733) and [fitness](D:/Claude/random/wormWars/wormwars/evo/rollout.py:40).

   Food also has finite spatial support and is biased toward the arena centre. Exploration, wall responses and patch retention may matter more than gradient following.

   **Detection:** add separate accounting for plant-food intake, pellet intake, hazard losses and movement costs. Replay representative champions with corpse nutrition disabled and with hazards disabled. Report these as interventions, not replacements for the primary score. “Time on food” alone cannot distinguish these mechanisms.

3. **MAJOR — The matched-remap specification is impossible as written, and the routing match is incomplete.**

   Three disjoint triples require **nine pairs**. The stated pool contains **eight**.

   Direct checks of the cached graph also found:

   | Pair | Relevant connection |
   |---|---|
   | AWC | AWCL directly connects to AVAL and SMDVL, both anatomical weight 1 |
   | ASJ | ASJL has a direct gap junction to SMDDR |
   | ASG | ASGL has a direct gap junction to SMDDR |
   | IL2 | Both neurons have direct chemical connections to the forward read-out |
   | AWB | Both neurons have direct chemical connections to the forward read-out |

   Thus “the food neurons are two hops away” is approximately descriptive, not literally true for every neuron. More importantly, ASJ/ASG acquire a one-hop locomotor route when gap junctions count.

   **Detection:** publish the actual six-neuron sets and matching table before running. Separate forward and turn read-outs, chemical and gap routes, and left/right asymmetry. Include connection strengths: one weak anatomical edge and sixteen strong edges should not be treated as equivalent shortcuts. The proposed input-drive probe helps, but should measure time-dependent responses to both common-mode and differential input, not one scalar magnitude.

4. **MAJOR — Equal mean absolute motor commands do not equalise locomotor opportunity.**

   Forward commands are clipped, reverse movement is multiplied by `reverse_fraction = 0.4`, and crowding modifies actual displacement. Equal `mean(abs(forward))` can therefore coexist with different speed, exploration and energy expenditure. Equal absolute turning can mean persistent circling or alternating turns, with very different consequences. See [motor read-out](D:/Claude/random/wormWars/wormwars/world.py:492).

   Sensor-silent calibration also measures autonomous dynamics driven by random biases, not responsiveness to food. Its estimation error becomes a fixed graph-specific intervention shared across every cell.

   **Detection:** validate calibration on independent random genomes; report signed command distributions, clipping frequency, actual displacement and temporal persistence. Check both deviation from the absolute target and differences between graphs. Add a modest gain-perturbation replay and examine whether the **interaction** changes.

   The 10% threshold currently has no demonstrated relationship to acceptable score distortion. It could comfortably exceed the effect being investigated.

5. **MAJOR — The convergence tripwire is backwards, and the existing evolution logs cannot cleanly diagnose convergence.**

   “Fewer than 80% still improving → raise generations” extends converged runs while potentially leaving universally improving runs at 40.

   There is a second problem: training worlds change each generation, and the logged best is selected on only eight worlds. The final champion is likewise chosen on the final training batch. Consequently, apparent progress combines learning, map difficulty and selection noise. The final held-out score remains valid for the selected champion, but graph differences may partly reflect sensitivity to this noisy selection procedure. See [evolve.py](D:/Claude/random/wormWars/wormwars/evo/evolve.py:121).

   **Detection:** evaluate prespecified checkpoints on one common diagnostic world suite, separate from the final test suite. Rescore a few checkpoint populations on a larger independent suite and measure rank stability and elite overlap. Extend prespecified runs to 80 generations.

   Raise the full budget when meaningful improvement remains plausible, or when the ranking changes with additional training—not according to the fraction of noisy slopes above zero.

6. **MAJOR — A saved champion can silently be replayed under the wrong experimental condition.**

   [load_genome](D:/Claude/random/wormWars/wormwars/evo/genomes.py:150) checks the graph label and array dimensions. It does **not** check the actual edge identities/order. Two different shuffles labelled `SH1` with identical edge counts pass those checks.

   Saved genomes also do not contain the interface mapping, and [write_bundle](D:/Claude/random/wormWars/wormwars/evo/bundle.py:93) does not automatically record it. That becomes dangerous once nine conditions differ partly through interface configuration.

   **Detection:** require an exact manifest containing graph/edge-order hashes, resolved interface, sensing mode, gains, full configuration and seed schedule. Add an in-memory versus saved-and-reloaded rollout comparison for every condition type. Deliberately loading the wrong mapping or same-labelled wrong graph should fail.

   None of the behavioural tripwires reliably detects this.

7. **MAJOR — The uniform-magnitude generation-0 probe does not isolate anatomical strengths.**

   Initial chemical magnitudes scale with anatomy, but mutation adds noise with a fixed absolute standard deviation. Thus anatomical magnitude controls both initial dynamics and how easily a connection changes sign or relative strength. That can affect evolution long after generation 0. Gap magnitudes are anatomical too. See [initialisation and mutation](D:/Claude/random/wormWars/wormwars/brain.py:131).

   Uniform magnitudes additionally change the magnitude distribution and potentially invalidate gains calibrated under anatomical initialisation.

   **Detection:** retain the cheap uniform probe, but add within-mask magnitude permutations that preserve the distribution, with chemical and gap manipulations distinguished. Use paired biases, time constants and signs. A small number of evolved strength-control runs would be more informative than another full remap.

   The design correctly limits its claim to wiring plus strengths. It should not subsequently interpret the generation-0 decomposition as separating their contributions to evolvability.

8. **MAJOR — The numerical tripwire can pass while the reported interaction changes substantially.**

   Five percentage points of normalised fitness per champion is not necessarily small. An interaction combines four signed components. Opposing errors can move that interaction by almost twenty percentage points while every individual component remains below the proposed threshold.

   Final-champion checks also miss numerical changes in which mutants get selected.

   **Detection:** compare the primary contrasts and interaction at 32 versus 128 substeps, using paired worlds. Refine a few checkpoint populations to check selection-rank stability. Include repeated 32-versus-32 evaluations to establish the contribution of CUDA nondeterminism.

   Keep 32 substeps given the measured cost. However, brain refinement does not test nearest-cell eating, collision or field-deposition artefacts. A small grid-alignment sensitivity probe would address a different numerical failure mode that the current design misses.

9. **MAJOR — Four graphs can support rough planning, but the proposed allocation rule uses the wrong variance unless specified more carefully.**

   The relevant variance is the variance of **within-graph mapping contrasts**, not simply raw fitness between graphs. Large additive graph differences can cancel almost completely in the interaction. Conversely, graph-by-mapping variation can dominate despite modest variation in overall graph means.

   Two runs per graph separate components only very noisily. Reusing the graphs across cells is useful, but it does not create additional independent graphs.

   **Detection:** estimate variance components for the actual planned contrasts and report broad planning ranges, including leave-one-graph-out sensitivity. Preserve each run’s whole task/mapping vector during resampling. If seeds are shared across graphs, account for that crossed seed structure rather than automatically nesting seeds inside graphs.

   Also report the task contrast **`I(T1) − I(T0)`** explicitly. Two separate interaction estimates do not directly answer whether the interface effect is stronger under the proposed worm-like condition.

10. **MAJOR — Discarding pilot runs does not remove tuning leakage if pilot graph identities are reused.**

    Task tuning on SH1–SH4 followed by new runs on SH1–SH4 still tunes to the test graphs. New genomes and held-out worlds do not undo that.

    Likewise, dropping a mapping because its observed N2/SH results hit a floor can remove the very architectural limitation the experiment should discover.

    **Detection/prevention:** reserve distinct shuffle identities for pilots. Establish task feasibility with controllers before inspecting N2. Preserve failed cells in the report; changing the subsequent design should not retrospectively make them unusable observations.

    The current “N2 never touches tuning” rule does not fully cover either issue.

11. **MAJOR — The valence probe tests sensory encoding symmetry, not equivalence to a hazard-avoidance task.**

    The narrow mathematical argument is sound without gap coupling: flip the food-input neurons’ voltage coordinates, flip their biases, and transform incident chemical weights correspondingly. With symmetric initialisation and mutation, this preserves the distribution of possible motor behaviour.

    But negating food input while retaining food rewards is not the same intervention as replacing reward acquisition with damage avoidance. Hazard placement, exposure costs and resource depletion differ.

    Furthermore, a positive result with gaps present does not make the “no fixed signs” argument wrong; it demonstrates that its acknowledged exception matters. A null result from four runs is not evidence of practical symmetry.

    **Swap:** first use a paired, no-evolution transformation check with gaps removed, then restore gaps and measure the discrepancy. That directly tests the claimed mechanism cheaply. I would drop the evolved valence arm before dropping MS. If retained, specify a practical equivalence margin and test the N2–SH valence interaction, not just N2’s change.

12. **MAJOR — I would change the fraction at approximately the same cost.**

    My preferred allocation is:

    - Keep T0, T1, M0 and **two** feasible disjoint matched remaps.
    - Keep MS on T1: seven cells.
    - Use four N2 runs and six SH graphs × two runs per cell: **112 runs**.
    - Prespecify eight runs for continuation from 40 to 80 generations.
    - Replace evolved valence runs with the causal and numerical probes above.

    This is **120 forty-generation equivalents**, compared with 126 in the main grid alone. It sacrifices some precision on N2’s mean and remap breadth to improve graph sampling and convergence information.

    With these changes, the fraction can serve all three jobs: discover mechanisms, obtain rough sizing information, and produce a provisional interaction estimate. As written, job 1 is underfunded and job 2 lacks a credible convergence check. Dropping RD and retaining 32 substeps are reasonable.

13. **MINOR — The runtime arithmetic is plausible, but it is not yet an end-to-end budget.**

    The 8.9-hour main-grid calculation is correct under the stated per-generation measurement. However, existing `evolve()` performs repeated held-out evaluations and an extra final training evaluation; the calling script evaluates the champion again. Depending on invocation, a 40-generation run currently includes six or nine held-out evaluations inside evolution.

    The valence specification also says four N2 and four SH runs, while the budget says sixteen runs. Clarify whether fresh positive arms are included and how the SH runs are distributed across graphs.

    Benchmark a complete pilot run with the intended checkpoint, refinement, saving and scoring schedule. Predeclare balanced batches so hitting the cap does not selectively remove one condition.

14. **MINOR — Several remaining tripwires need operational definitions rather than qualitative wording.**

    - Scripted-controller scores are benchmarks, not demonstrated floors and ceilings. Evolved policies may exceed them. Report raw scores and do not clip normalised scores.
    - “Within 20%” needs a denominator and uncertainty interval. A ratio to a weak memory controller can be misleading.
    - Opposite remap signs near zero are expected under noise. Trigger additional remap sampling on meaningful heterogeneity, not sign disagreement alone.
    - “Far more” and “beyond noise” need prespecified estimands and margins.
    - Graph variance dominating does not justify eliminating run replication. Retain enough replication to continue measuring it.

    These thresholds should govern investigation and subsequent allocation, not mechanically classify effects as present or absent.

15. **MINOR — Two factual documentation details warrant correction, and one integration test is missing from the plan.**

    `configs/interface.yaml` says injection uses bounded `tanh(v)`. Actual sensor injection adds external current and clips that current; `tanh(v)` is used for chemical transmission and motor read-out.

    The shuffle documentation says anatomical weights travel with edges, but [graphs.py](D:/Claude/random/wormWars/wormwars/connectome/graphs.py:97) independently permutes those weights onto the shuffled edges. Global distributions are preserved; neuron-specific strengths are not.

    Add a neuron-relabeling invariance test: consistently permute graph, genome and interface, then require unchanged motor outputs and rollout scores. Alongside explicit food-channel injection tests, this is a cheap defence against another indexing/direction mistake that plausible-looking fitness would conceal.

The failure I most expect to bite is **T1 producing an apparent temporal-chemotaxis result through reactive patch retention and pheromone-mediated environmental memory, without relying on temporal food information in the intended way**.