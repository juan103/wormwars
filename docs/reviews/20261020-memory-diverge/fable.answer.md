Three things I checked in the files shape the ideas below, so I state them first.

- **N2's curve is a floor, not a slow slope.** In `report.json` the share is flat at about 0.09 from tick 150 to tick 300, while every ensemble keeps sliding, to 0.0008 for SH and 0.009 for SH-recip. The share is a mean over genomes, so a few non-decaying genomes with large differences can hold that floor up. 03m's Q1 already found N2's numerator concentrated in a minority.
- **The eight turn read-out neurons were never deleted.** 03m's lesion screen excluded them, so loops among SMD and RMD themselves are untested.
- **The stimulus bank's food level was never varied.** All three studies used the same level, 0.2234 in `pilot.json`.

Also useful: `mc_report.py` loads the per-genome difference curve from the local arrays, so most checks below need no GPU.

## The ideas

**1. It is a mixture, not a slow mode.** Statistics, Simpson's paradox.
Claim: N2's typical brain relaxes like a shuffle's. N2 simply has ten times as many bistable brains, and they carry large differences, so the mean curve sags toward a floor.
Seen if true: the median per-genome retention curve of N2 lands on the ensembles' median curves, and removing the 43 long-lived genomes removes most of N2's lead at tick 30.
Check: from `runs/p4mc/arrays/N2__long.npz` and one null graph's long array, compute the per-genome share curve, then the median across genomes, and the mean with the 43 excluded. Seconds.
Why: it decides whether the question is "why are N2's brains slower" or "why does N2 produce more latches". Everything downstream depends on that.

**2. Autapses as a leak reducer.** Control theory, self-feedback.
Claim: N2 has 38 chemical autapses; ordinary shuffles about 15. Half draw a positive sign, and each positive autapse cuts that neuron's effective leak from 1 plus g to 1 plus g minus W, stretching its time constant.
Seen if true: retention tracks the number and weight of positive autapses, per null graph and per N2 genome.
Check: list the autapse neurons and EM sections from the cache's chemical diagonal. Across the 640 local graphs, Spearman of autapse count and summed autapse weight against each graph's tick-30 share in `measurements.json`. Then regenerate N2's 2048 genomes on the CPU with `Genome.random` and 03mc's salt, and correlate per-genome positive-autapse weight with retention. Minutes.
Why: it would be the simplest possible story, and a single term in the equation.

**3. Heavy reciprocal loops.** Electronics, the latch.
Claim: N2 has 669 reciprocal chemical pairs, shuffles about 126, and SH-recip keeps the count but permutes the weights off them. A positive-product 2-loop whose gain approaches the product of the leaks creates a near-zero eigenvalue. N2's reciprocal pairs may carry much heavier weights than a random pair.
Seen if true: the summed product of anatomical weights on reciprocal pairs is far above that of the 256 Q-C permutations, and across those permutations it predicts the committed per-permutation P4.
Check: regenerate the 256 permutations' magnitudes with `_apply_magnitude_mode` and the seeds in `measurements.json`, compute the loop-weight sum, correlate with the P4 values in `report.json` Q-C. Seconds.
Why: it explains why SH-recip is the slowest ensemble and still far from N2.

**4. A slow neuron on the only road.** Reliability engineering, series versus parallel systems.
Claim: in N2 the food signal reaches the turn neurons through a few strong stations, AIY, AIZ, RIA. Whatever time constant those neurons draw sets the retention. A shuffle spreads the signal across many weak paths, so the fast ones dominate the average.
Seen if true: in N2, per-genome retention at tick 30 is predicted by the taus of AIY, AIZ, RIA and the turn neurons. In a shuffle, the same regression explains nothing.
Check: regenerate the genomes as in idea 2, regress per-genome retention on those taus, compare R² with a null graph. Minutes.
Why: it makes the RIA and AIY proportional cuts a direct consequence rather than a coincidence.

**5. Equipotential gap junctions.** Electrical engineering, no current flows through a wire between equal potentials.
Claim: N2's gap junctions join neurons whose states are correlated, left-right homologs and neighbours along the same pathway. They carry little current, so they dissipate little. A shuffle's gap junctions join unrelated neurons and act as a true extra leak. That is why switching them off frees the nulls much more than N2.
Seen if true: gap current per unit conductance at the holds' end is much lower in N2 than in any ensemble.
Check: a CPU rerun of the 100-tick hold with `Brain.step` on 256 genomes for N2 and each ensemble, then the sum of G times the absolute voltage difference over the sum of G. Five minutes. A no-simulation proxy first: the share of N2's gap weight on pairs from `configs/mirror_pairs.yaml` against a shuffle's.
Why: it is the only idea here that predicts the sign and the size of the gap-junction result directly.

**6. Saturation-induced percolation.** Statistical physics, bond percolation.
Claim: the chemical term is gated by the presynaptic tanh slope. N2's heavy weights saturate its hubs, so the hubs' outgoing edges vanish from the linearised dynamics. The effective network fragments into weakly coupled pieces, and small pieces with few live inputs hold state for long. A shuffle's hubs are less saturated, its effective graph stays an expander, and everything relaxes fast. The read-out slope of 0.44 against 0.73 is a visible corner of this.
Seen if true: at the holds' end, N2 has a far larger fraction of chemical edges with presynaptic slope below 0.1, and the live subgraph's largest strongly connected component is smaller.
Check: the same CPU rerun as idea 5, then per-neuron slope, an effective edge mask, and component sizes. Ten minutes.
Why: it ties the slope finding, the weight-placement finding and the gap-junction finding into one object.

**7. Edge of bistability.** Physics, critical slowing down at a saddle-node.
Claim: the slow decay and the 2.2 percent of latching brains are two faces of one distribution. N2's leading Jacobian eigenvalue sits closer to zero than a shuffle's, and crosses it ten times as often.
Seen if true: the distribution of the rightmost real part is shifted toward zero for N2, and the fraction above zero matches the latching fraction per graph.
Check: with no simulation, build J equals diag of 1 over tau times the sum of minus I minus diag g, W transposed and G, at v equals 0, from `Genome.dense`, for 2048 genomes on N2 and on five null graphs. Eigenvalues of a 302 matrix take about 20 ms, so a few minutes. Then repeat at the hold state from idea 5's rerun.
Why: a shifted eigenvalue distribution is a mechanism in the ordinary sense, and it is quantitative.

**8. Metastability from modules.** Network science and Markov chain mixing.
Claim: N2 has modules, head ganglia, cord, tail, pharynx, joined by few edges. Weakly coupled modules give eigenvalues near zero whose eigenvectors are localised on a module. Degree-preserving shuffles are expanders with a spectral gap. SH-mirror and SH-recip keep more structure and do decay more slowly, which fits.
Seen if true: N2's slowest eigenvectors have low participation ratios and sit on an anatomical module. Across the 640 null graphs, modularity predicts the tick-30 share.
Check: the eigenvectors from idea 7 plus a participation ratio. Per-graph Newman modularity on the local graph files against `measurements.json`. Minutes.
Why: it would say the effect is generic to any biological graph, not a worm fact.

**9. Group delay of a cascade.** Signal processing.
Claim: a chain of leaky integrators lags its input by the sum of the stage time constants, and a rising-versus-falling ramp difference persists for that lag. N2's strong feed-forward chain gives both a large response and a long lag. The shoulder in N2's curve, 0.887 at tick 5 against 0.78 for SH, is the lag.
Seen if true: per genome, numerator size and tick-30 retention are positively correlated in N2 and uncorrelated in shuffles, because the same path sets both.
Check: the local per-genome arrays hold both quantities. Seconds.
Why: it would make the proportional RIA and AIY cuts expected, since removing a stage shortens the chain and shrinks the signal together.

**10. Non-normal transient growth.** Fluid dynamics, pseudospectra.
Claim: a feed-forward hierarchy gives a strongly non-normal Jacobian. Differences can grow before they decay even when every eigenvalue is stable, and the transient outlives the spectral prediction. Shuffles are closer to normal.
Seen if true: N2's Jacobians have a larger Henrici departure from normality, and more N2 genomes show the difference at tick 5 above tick 0.
Check: Henrici's number from the matrices in idea 7, and the per-genome growth fraction from the local arrays. Minutes.
Why: it would mean eigenvalues alone can never explain the curve, which changes what any mechanism study must measure.

**11. A mutual-inhibition memory in the read-out itself.** Neuroscience, the Machens-Brody integrator.
Claim: the dorsal and ventral turn neurons, SMDD against SMDV and RMDD against RMDV, are reciprocally connected in the worm. With both signs negative, one draw in four, a heavy reciprocal pair is a latch or a line attractor, and the probe reads exactly the dorsal-minus-ventral mode it stores. The lesion screen never touched these neurons.
Seen if true: per-genome retention depends on the sign pattern of the edges among the eight turn neurons. Zeroing those edges removes the floor and the latching genomes.
Check: read those edges and weights from the cache. Regenerate the genomes, group retention by sign pattern. Then a CPU rerun of 2048 N2 genomes with the chemical edges among the eight turn neurons zeroed through `Genome.with_params`. Two minutes.
Why: the memory would sit where it is read, which is both the strongest and the most embarrassing possible answer.

**12. The sustain pedal.** Music, acoustics.
Claim: some of the surviving difference is two trajectories oscillating at the same frequency out of phase. That never decays, and it is counted by the absolute difference.
Seen if true: among N2's 17 long-lived unsettled genomes, the signed difference changes sign across the recorded ticks.
Check: the signed per-genome difference and the settling ranges in the local arrays. Seconds.
Why: it would split the floor into latches and oscillators, which need different follow-ups.

**13. The ventral cord as a reflecting transmission line.** Electrical engineering, the telegraph equation. *Probably wrong, remarkable if true.*
Claim: the cord motor neurons form a chain with nearest-neighbour gap junctions. A perturbation diffuses down the chain, reflects from the tail, and returns to the head circuit hundreds of ticks later. Shuffles rewire the chain into an expander, and diffusion time collapses.
Seen if true: a travelling peak of per-neuron difference moves down the cord between ticks 10 and 100, and the head's share rises again afterwards.
Check: a CPU rerun on 256 N2 genomes recording per-neuron absolute difference by region, then `Brain.cut_gap` on all cord-to-cord gap junctions and compare the tail past tick 100. Ten minutes.
Why: a memory held in the body's wiring rather than the head would be a new kind of claim.

**14. Remanence in deep saturation.** Magnetism, hidden hysteresis. *Probably wrong, remarkable if true.*
Claim: a difference stored far out on the tanh rail is invisible downstream but persists at the neuron's own tau, and reappears when the common drive relaxes. N2's saturated hubs hide more of it.
Seen if true: non-monotone per-genome curves, a later tick exceeding an earlier one, are more common in N2 than in the ensembles.
Check: the local per-genome arrays. Seconds. Then a rerun recording the pre-tanh difference over time, which `twin.history` records only at the ramp's end.
Why: the probe would be underestimating N2's history, not overestimating it.

**15. The bank's level sits at N2's bifurcation.** Nonlinear dynamics, early-warning signals. *Probably wrong, remarkable if true.*
Claim: the one food level ever used happens to put many N2 brains near a saddle-node, where relaxation is critically slow. The effect is real but specific to that level.
Seen if true: N2's tick-30 share changes strongly when the food level is halved or doubled, while the ensembles' barely move.
Check: `twin.history` on the CPU, 256 genomes for N2 and four nulls, at 0.5, 1 and 2 times the bank's level. Ten minutes.
Why: three replications with one bank cannot exclude it, and it would turn a finding into a warning.

**16. The pharyngeal echo chamber.** Architectural acoustics, coupled rooms. *Probably wrong, remarkable if true.*
Claim: the 20 pharyngeal neurons are an almost isolated module joined to the rest mainly by the RIP-I1 gap bridge. They receive a faint copy of the history, hold it because nothing drains them, and leak it back.
Seen if true: at tick 300 the pharynx holds far more than its 7 percent share of the total difference.
Check: the per-neuron rerun from idea 13, then `Brain.cut_gap` on the bridge and zeroed pharynx-to-soma chemical edges. Ten minutes.
Why: a reverberation chamber in a random brain would be a striking use of anatomy.

**17. Common-mode gain doubling from mirror symmetry.** Circuit theory, differential amplifiers. *Probably wrong.*
Claim: the probe feeds equal input left and right and reads a left-right mean. In a mirror-symmetric graph the common mode sees the sum of an edge and its image, doubling effective loop gains and pushing them toward the leak. Random per-neuron draws break the symmetry, but only partly.
Seen if true: per-genome retention rises with the fraction of mirror-paired edges whose sign draws agree.
Check: regenerate the genomes, score symmetry per genome with `configs/mirror_pairs.yaml`, correlate with retention. Minutes.
Why: it would explain why SH-mirror sits between SH and N2, and it predicts a cheap intervention, symmetric draws.

## The three I would give a real chance

- **Idea 1, the mixture.** It costs nothing and it reframes every other idea. If N2's median brain is ordinary, the question becomes why N2 makes ten times as many latches, and ideas 3, 7 and 11 are the candidates.
- **Ideas 6 and 7 together, saturation percolation and the eigenvalue shift.** One CPU rerun and one eigenvalue pass test both. They are the only ideas that connect the slope, the weight placement, the gap junctions and the latching fraction with a single measurable object.
- **Idea 11, the latch in the read-out.** The lesion screen's one blind spot is exactly the eight neurons the probe reads, and the kill test takes two minutes on the CPU.

Runner-up: idea 5, because it is the only one that predicts the gap-junction result's direction and size rather than accommodating it.