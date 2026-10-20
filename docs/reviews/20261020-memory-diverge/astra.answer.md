I would keep several mechanisms alive simultaneously. The early decay and the nearly flat late tail may have different causes: the [committed curve](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/report.json:5869) approaches roughly 0.09 around ticks 150–300.

I checked the dynamics, samplers, probe, statistics and both results files. I ran no analyses or experiments. The checks below are proposals. For new simulations, I mean small exploratory CPU panels using [brain.py](/D:/Claude/random/wormWars/wormwars/brain.py) and [twin.py](/D:/Claude/random/wormWars/wormwars/exp03/twin.py), with fresh CPU draws and cached null graphs—not attempts to reproduce the GPU genomes from their seeds. These are intended as screens within an hour, not benchmarked runtime promises.

1. **Feedback almost pays the leak — control engineering**

   **Claim:** N2 more often assembles feedback loops whose reinforcement nearly balances leakage and gap damping. Differences therefore contract slowly, without requiring distinct stable states.

   **Prediction:** The slowest modes of the actual brain update lie closer to neutral stability, and the food histories excite those modes.

   **Cheapest kill:** Linearize `Brain.step` at several held-input states in a small panel. Test whether its modes predict the observed difference trajectory. If N2’s excited modes are no slower, discard this fixed-mode explanation.

   **Why it matters:** It would give a compact quantitative mechanism: anatomical wiring changes the distribution of effective relaxation times.

2. **Gap junctions miss the memory pattern — electrical common-mode rejection**

   **Claim:** N2’s history difference tends to put gap-connected neurons at similar *differences between histories*. Gap junctions then have little difference to equalize. Shuffled gaps more often connect neurons carrying opposing traces and erase them.

   **Prediction:** For the same overall history separation, N2 has smaller gap dissipation, measured by  
   \(\sum_{i<j}G_{ij}(\delta v_i-\delta v_j)^2\).

   **Cheapest kill:** Record both voltage trajectories through `twin.history` and calculate this quantity, normalized by squared separation. If N2’s trace is not unusually protected from gap dissipation, this explanation fails.

   **Why it matters:** It directly connects the relaxation result to the gaps-off result. Chemical feedback would still have to counter ordinary leakage.

3. **The two wiring layers fit together — reaction–diffusion and multiplex networks**

   **Claim:** N2’s chemical wiring generates patterns that its electrical wiring happens to spare. The useful property belongs to their arrangement together, beyond either layer’s individual graph statistics.

   **Prediction:** Combining N2 chemicals with shuffled gaps—or shuffled chemicals with N2 gaps—disrupts persistence more than expected from changing either layer independently.

   **Cheapest kill:** Make a small chemical-layer × gap-layer factorial using cached graphs, `Connectome.with_masks` and `BrainSpec.from_connectome`. Measure retention as well as response. No special interaction for the N2/N2 combination would kill the strong version.

   **Why it matters:** The relevant anatomical feature could be a relationship between layers that none of the five ensembles preserves.

4. **A long pipeline — chromatography and process engineering**

   **Claim:** Old input is still travelling through a sequence of ordinary leaky stages. N2’s output receives yesterday’s signal later; individual neurons need not retain it unusually long.

   **Prediction:** A brief food perturbation produces a later, broader turn response, with activity differences progressing through intermediate neurons.

   **Cheapest kill:** Around the final held input, apply a one-tick food pulse using `_current` and `Brain.step`; record individual neurons and turn output. If N2 has no additional delivery delay or temporal spreading, reject the pipeline account.

   **Why it matters:** It distinguishes storage from transport delay and could suggest a simple feedforward circuit that reproduces the effect.

5. **Passing the baton — transient growth in fluid mechanics**

   **Claim:** N2 transfers a fading difference between directions in state space, amplifying the next direction before the previous one dies. Every individual mode can be stable while their combination lasts surprisingly long.

   **Prediction:** Some perturbations grow temporarily or peak late; ordinary eigenvalue decay estimates substantially underpredict persistence.

   **Cheapest kill:** For a few trajectories, compare the actual linearized propagator acting on the history difference with an eigenvalue-only prediction. If there is no appreciable transient amplification or transfer in the excited directions, drop this account.

   **Why it matters:** It would explain long traces without near-neutral eigenvalues or attractors.

6. **Shared paths survive random signs — wave interference**

   **Claim:** N2 contains unusually many consequential routes that reuse the same chemical edges. Their random signs are therefore correlated. In squared responses, pairs of walks survive sign averaging when every signed edge appears an even total number of times.

   **Prediction:** N2 has an excess of long-lag response variance even in a linear surrogate with matched neuron slopes. Particular arrangements of overlapping loops matter more than the total reciprocal-pair count.

   **Cheapest kill:** Use `Genome.random`, `Genome.dense` and cached graphs to estimate sign-averaged squared impulse responses with common slopes and time constants. If no normalized long-lag excess survives, kill this linear path-interference version.

   **Why it matters:** It offers a structural explanation for reproducibility across random signs, rather than relying on biologically meaningful excitation and inhibition.

7. **Rare islands refuse to relax — disordered materials**

   **Claim:** N2 contains weakly connected pockets that occasionally become strongly self-reinforcing under random signs. Different genomes activate different pockets, so pooled single-neuron deletions miss the common mechanism.

   **Prediction:** The slowest genomes have localized history differences or slow modes, but their locations vary between genomes.

   **Cheapest kill:** Record spatial differences and mode localization in a CPU panel, then inspect its slowest members. If their traces remain broadly spread and no small region carries disproportionate persistence, reject the localized-island version. Use `brain.py`, `twin.py` and the anatomical masks.

   **Why it matters:** It could reconcile reproducible population statistics with the absence of one universally necessary storage neuron.

8. **The surviving minority dominates the average — actuarial survival mixtures**

   **Claim:** N2 couples strong responses to long-lived genomes more often. Its aggregate curve slows partly because those genomes increasingly dominate the remaining signal.

   **Prediction:** The genomes contributing most to the mean change over time; amplitude-matched, per-genome comparisons show a smaller difference than the published aggregate.

   **Cheapest kill:** Use the existing `diff` arrays in [N2__long.npz](/D:/Claude/random/wormWars/runs/p4mc/arrays/N2__long.npz) and matching null files. Compare eligible genomes within starting-amplitude bins and remove the largest late contributors. If the retention shift remains broad across bins and quantiles, mixture weighting alone fails.

   **Why it matters:** It identifies whether the target mechanism is typical relaxation, rare persistence, or the association between persistence and response strength. This concerns the retention curve, separately from earlier P4 trimming.

9. **The microphones face the slow modes — acoustics and observability**

   **Claim:** N2 need not preserve more history throughout its whole state. Its chosen turn neurons may simply receive a larger projection of whatever slow differences exist.

   **Prediction:** N2’s advantage is large in the specified turn read-out but smaller in full-state distance and most alternative read-outs.

   **Cheapest kill:** During small `twin.history` runs, record full-state separation and a bank of matched random read-outs. Use the turn weights in [interface.yaml](/D:/Claude/random/wormWars/configs/interface.yaml). If the advantage is equally strong across state directions, reject read-out alignment as the main explanation.

   **Why it matters:** It would locate the special property in anatomy plus interface, and explain why response pathways and apparent memory are difficult to separate.

10. **Saturation disconnects the brakes — enzyme inhibition and feedback control**

   **Claim:** N2’s heavy anatomical edges push particular neurons into saturation, suppressing outgoing chemical pathways that would otherwise restore the state. The network loses some braking action while retaining reinforcing paths.

   **Prediction:** Low tanh slopes occur preferentially at sources whose unsaturated influence would accelerate convergence.

   **Cheapest kill:** From paired trajectories, reconstruct the state-dependent gains between voltage differences and tanh differences. Test whether suppressed pathways actually remove restoring influence. If they mainly suppress reinforcement instead, this proposed mechanism has the wrong direction. Use `Brain.step` and `twin.history`.

   **Why it matters:** It turns weight placement into a specific nonlinear mechanism. This concerns recurrent tanh; the pre-tanh read-out check leaves it intact.

11. **Random slow neurons land on bottlenecks — transport through disordered media**

   **Claim:** N2 offers more strategically important bottlenecks. Randomly assigning a large time constant to one of them delays an entire route, whereas a slow neuron in a shuffled graph is more easily bypassed.

   **Prediction:** Persistence depends on *where* the large time constants land, and N2 loses much of its advantage when all neurons receive the same time constant.

   **Cheapest kill:** With signs and biases paired, replace `Genome.tau` by a common value, then permute the original time constants among neurons. If retention is insensitive to both interventions, reject this bottleneck lottery.

   **Why it matters:** Identical time-constant distributions could still produce systematically different network timescales.

12. **A ghost traps the trajectory — chemical reaction kinetics**

   **Claim:** Some N2 brains pass near a dynamical bottleneck left by an almost-created or almost-destroyed equilibrium. They linger there without needing a genuinely stable alternative state.

   **Prediction:** A trajectory spends a long interval moving very slowly through a particular region, then escapes. Small changes in final food level produce large changes in escape time.

   **Cheapest kill:** Sweep a few nearby final food levels using `twin.history`, recording state speed. Smooth, modest changes in lifetime with no localized slowdown would kill this bottleneck account for the observed window.

   **Why it matters:** It could explain apparently settled differences that eventually vanish, without treating a short settling test as proof of stability.

13. **The memory route changes as it fades — switched systems and robotics**

   **Claim:** As neurons enter and leave saturation, N2 changes which pathways carry the difference. A succession of temporary routes preserves history better than any one fixed network of effective gains.

   **Prediction:** The spatial trace changes, and the ordered sequence of effective updates predicts retention much better than frozen or averaged updates.

   **Cheapest kill:** Use `Brain.substep_hook` to record paired states and reconstruct difference propagation. Compare the actual sequence with gains frozen at the ramp end. If freezing reproduces the slow curve, the moving-route explanation is unnecessary.

   **Why it matters:** It would explain why static graph descriptors and one-time Jacobians fail, and why deleting one relay can leave alternatives.

14. **The histories disagree about the beat — music and oscillator synchronization**

   **Claim:** Some N2 brains approach the same oscillation with different phases. What persists is the timing difference, rather than separation between stationary states.

   **Prediction:** The two histories trace similar repeating trajectories; shifting one in time substantially removes their late separation.

   **Cheapest kill:** First inspect signed `diff` in the local arrays for oscillatory candidates. Then record every tick in a small CPU panel and test time-shift alignment of the full states. Failure to align kills a phase-only explanation.

   **Why it matters:** Persistent history could be encoded as timing. Absolute differences would conceal that distinction.

15. **The output neurons are themselves the store — digital latches**

   **Claim:** The eight turn neurons, or short loops tightly involving them, hold much of the trace. RIA and AIY mainly deliver or amplify signals reaching that store.

   **Prediction:** Erasing the difference specifically in the turn neurons destroys later separation more effectively than an equally sized intervention elsewhere.

   **Cheapest kill:** At the ramp end, set those eight neurons to the midpoint of their two history states, then resume the intact dynamics. Compare late absolute differences using the intact starting difference for normalization. If the original tail quickly rebuilds, reject a predominantly local output store. `twin.py` already identifies the neurons.

   **Why it matters:** It gives a concrete storage hypothesis for neurons excluded from the earlier deletion screen.

16. **The network ages like a glass — glass physics. Probably wrong, but remarkable if true.**

   **Claim:** N2’s nested feedback structures create a hierarchy of progressively harder-to-escape configurations. The 100-tick preparation changes how old the network is dynamically, not merely its starting voltage.

   **Prediction:** Relaxation depends systematically on preparation duration; curves may organize by elapsed time relative to waiting time. A brief perturbation may rejuvenate fast relaxation while leaving an older trace.

   **Cheapest kill:** Vary `warm` in `twin.history`, for example across 25, 100 and 400 ticks, holding the ramp and final input fixed. If normalized relaxation simply converges to one preparation-independent curve, kill the aging explanation over this range.

   **Why it matters:** Memory duration would be a property of the network’s preparation history, not a fixed clock.

17. **A winnerless carousel — ecology. Probably wrong, but remarkable if true.**

   **Claim:** N2 more often forms circuits in which one active group suppresses another, which suppresses another, eventually releasing the first. Trajectories linger near successive temporary winners.

   **Prediction:** Long quiet intervals alternate with abrupt handoffs among neuron groups. The two histories retain different positions in this sequence.

   **Cheapest kill:** Inspect full-state traces from the slowest members of a small CPU panel using `substep_hook`. If there are no ordered, recurring handoffs—only smooth contraction or stationary separation—the carousel account dies for those traces.

   **Why it matters:** The memory would be a position in a sequence, suggesting a route from random anatomical dynamics to temporal computation.

18. **An emergent conserved quantity — chemistry and conservation laws. Probably wrong, but remarkable if true.**

   **Claim:** Despite explicit leakage, chemical feedback in some N2 brains nearly conserves a weighted combination of neuronal differences across several operating states. Individual neurons change while that combination scarcely does.

   **Prediction:** One weighted sum, fitted early, predicts late separation and remains approximately conserved under independent small perturbations. Its weights need not be identical across genomes.

   **Cheapest kill:** Construct effective update matrices at several states from `brain.py`. Search for a shared approximately conserved direction, then validate it on independent perturbations and require a measurable connection to turn output. No unusually good shared direction relative to nulls would kill it.

   **Why it matters:** It would provide an explicit collective memory variable and a possible design principle for synthetic circuits.

The three I would give a real chance are **2, gap junctions missing the memory pattern; 6, shared paths surviving random signs; and 13, a changing route for memory**.

**2** has the clearest connection to an existing intervention result. **6** tackles the central puzzle of how anatomy can produce a repeatable effect despite randomized signs. **13** allows the mechanism to reside in the evolving pattern of effective connections, which could explain why neither individual deletions nor static structural constraints have isolated it.