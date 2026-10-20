Built on all five sources after re-reading 03mc's results, the brain update, the probe, the samplers and the report's curves. Two things I checked change what round 1 said, so they come first.

- **The 03mc genomes exist only on CUDA.** Their seeds feed a generator created on the run's device, and CPU and CUDA streams differ for the same seed. Fable's round-1 line that they can be regenerated on the CPU with the same salt is wrong. Regenerating them is seconds on the GPU, which is under the owner's word. A fresh CPU panel of 2048 genomes plus the full probe is a few minutes, and that is the right tool whenever an analysis needs genome values beside curves.
- **The gap layer carries no per-genome randomness.** G is identical across every genome of a graph. Only chemical signs, time constants and biases vary between genomes. Several experiments below rest on that asymmetry.

Confirmed from the files: N2's share sits near 0.09 from tick 150 to 300 and even rises slightly from tick 220 to 290, while every ensemble's median keeps falling. 03m's screen excluded the eight turn neurons. The registered share is a ratio of means over genomes, so it weights genomes by amplitude. The single-food-level fact I did not recheck this round.

## Families

| Family | Members | Same idea in different clothes |
|---|---|---|
| **1. Feedback nearly pays the leak.** A loop or self-loop whose gain approaches the leak gives a near-zero eigenvalue, a neutral direction at the limit, a fold just past it. | Astra 1, 12, 18; ChatGPT's slow-eigenmode and line-attractor rows; Owner 1; Claude 4; Fable 2, 3, 7, 15, 17; Astra 6 as the structural form | Astra 1 is ChatGPT's slow eigenmode. Owner's ring attractor, ChatGPT's line attractor and Astra 18's conserved quantity are one object, a neutral direction. Claude 4, Fable 7, Astra 12 and Fable 15 are one idea at four distances from the fold, Fable 15 being its stimulus-level version. Fable 2, Fable 3 and Astra 6 nest: an autapse is a one-cycle, a reciprocal pair a two-cycle, Astra's even-multiplicity walks the general case. Fable 17 is Astra 6 restricted to mirror pairs. |
| **2. Chains and transient growth.** No slow eigenvalue; the trace travels or grows before it dies. | Astra 4, 5; Fable 9, 10; Claude 11; ChatGPT's nonnormal row | Fable 9 is Astra 4. Fable 10, Astra 5 and ChatGPT's row are one idea. |
| **3. Reservoir and return.** The trace is parked off the main road and leaks back. | Owner 2; Claude 7, 12; Fable 13, 16 | Claude 12 is Fable 16. Owner 2 is the general form, Fable 13 the cord version, Claude 7 the two-compartment abstraction. |
| **4. Sequences and switched routes.** Nonlinear cousins of 2 and 3. | Astra 13, 17; ChatGPT's sequential row | Astra 17 is Astra 13 with the handoffs made discrete. |
| **5. Saturation reshapes the effective graph.** | Claude 1, 13; Fable 6, 14; Astra 10 | Claude 1 is Fable 6. Astra 10 is the signed version. Claude 13 and Fable 14 are the hysteretic versions. |
| **6. Gap geometry.** | Claude 3; Fable 5; Astra 2, 3; ChatGPT §5D | Claude 3, Fable 5, Astra 2 and ChatGPT §5D are one idea: a gap cluster's common mode is undamped. Astra 3 generalises it to how the two layers are arranged. |
| **7. Time-constant lottery on topology.** | Claude 2; Fable 4; Astra 11; ChatGPT §5B | Fable 4 is Astra 11. Claude 2 is the low-degree variant. |
| **8. Mixture and heavy tails.** The mean curve is a superposition. | Fable 1, 8; Astra 7, 8; Claude 5; ChatGPT's tail panel | Fable 1 is Astra 8. Claude 5 is the same superposition inside one genome. Astra 7 and Fable 8 say where the tail's members live. |
| **9. Read-out geometry, and the read-out as the store.** | Astra 9, 15; Fable 11; ChatGPT's readout row | Astra 9 is ChatGPT's row. Fable 11 is Astra 15. |
| **10. Phase memory.** | Fable 12; Astra 14; ChatGPT's phase row | One idea. |
| **11. Preparation and non-stationarity.** | Claude 6; Astra 16; 03m's unsettled holds | One idea. |
| **12. The probe's regime.** About what is measured, not a mechanism. | Claude 9; ChatGPT M1 | |
| **13. Toolbox.** | Owner 3; ChatGPT M0, M2, M4, M5, §4, §5E; Claude 8, 10 | Owner's transplanting is ChatGPT's M5 and §5E. |

## Hybrids and new ideas

**Hybrids.**

1. **Gap-assisted latch.** Astra 3 with Fable 3 and the Q-A result. A gap junction sitting on a reciprocal chemical pair adds to the loop gain when the pair drew two positive signs and subtracts when it drew two negative ones. N2 puts its gap junctions on such pairs; every ensemble shuffles the two layers independently. Developed in the last section.

2. **The draws are 2048 free lesions.** Fable 4's regression, Fable 11's sign grouping and ChatGPT's M4 decomposition, applied at the level of the random draw. Regress each genome's tick-30 share on its 302 time constants, on its 302 biases, and on its 5404 edge signs, three sparse regressions per graph, for N2 and three nulls. Which block explains N2's spread names the family, and which neurons or edges it picks names the circuit, with no deletion run. Because G never varies, family 6 predicts a large between-graph effect and an empty within-graph regression. That emptiness is itself a signature.

3. **A sign-free variance propagator.** Astra 6, Fable 7 and ChatGPT's hub row. With independent random signs, the mean absolute difference over genomes is a second-moment quantity. In an annealed approximation its growth is governed by the entrywise square of the linearised propagator, where signs vanish, while the leak and the gap layer enter coherently because they carry no sign. The Perron root of that nonnegative matrix is a zero-simulation per-graph statistic, and its Perron vector names the neurons. It also says why the layers differ in kind: chemical synapses act on the variance of the trace across genomes, gap junctions on its mean.

4. **Saturation as a lens on gap geometry over time.** Fable 6, Astra 2 and Astra 13. On one set of paired CPU trajectories, compute at every tenth tick the live chemical subgraph, its largest component, and Astra 2's gap dissipation per unit separation. If the trace retreats into the common modes of gap clusters that sit inside small live components, families 5 and 6 are one mechanism, and the late floor is where the retreat ends.

5. **Tail dissection in one pass.** Fable 1, 12, 14 and Astra 15. Classify each of N2's 43 long-lived genomes by four binary marks from the local arrays: settled or moving, signed difference changing sign or not, late tick above an earlier tick or not, pre-tanh read-out saturated or not. Then rerun only those 43 on the CPU with the edges among the eight turn neurons zeroed. Each class maps to a family: moving and sign-changing is 10, settled and monotone is 1 or 9, late rises are 3 or 5.

6. **Reversal as a structure test.** Claude 8 with Fable 3 and Astra 6. Autapses, reciprocal pairs and even-multiplicity walks are invariant under transposing the chemical matrix; chains, the sensor-to-motor route and the read-out's fan-in are not. So the reversed N2's retention share, not its response, is the quantity to compare. Survival points to families 1 and 6, loss to 2, 3 and 9.

7. **A trace older than the ramp.** Claude 6 and Astra 16 with 03m's finding that no hold settles in 100 ticks. The slowest single-neuron leak is 20 ticks, so a 100-tick hold is five e-folds for a lone neuron, but a network slow mode can be slower. Part of the tick-0 difference may be the two rows' unfinished relaxation from the zero start, written before the ramp. Vary the warm-up; if N2's curve moves and the nulls' do not, some of the "history" predates the history.

**New ideas.**

1. **The integrator is on the gaps' side, and only for fast neurons.** The update is implicit in the leak and in the diagonal of the gap term, explicit in the off-diagonal. For a shift that is uniform across a gap cluster, the per-substep multiplier is one plus c times g over one plus c plus c times g, against one over one plus c for a lone neuron, where c is the substep over the time constant and g the summed conductance. The exact dynamics would damp the two identically. The excess is second order in c, so it is large for fast, heavily gap-coupled neurons and negligible for slow ones. Which neurons are heavily gap-coupled is anatomical in N2 and permuted in every null.

   | time constant, ticks | g | lone neuron, kept per tick | gap common mode, kept per tick |
   |---|---|---|---|
   | 0.5 | 1 | 0.17 | 0.23 |
   | 2 | 1 | 0.61 | 0.63 |
   | 20 | 1 | 0.95 | 0.95 |

   This is ChatGPT's M0 gate made specific, and it compounds with family 6. The check is a rerun at 16 and 32 substeps.

2. **The rich-club core.** Degree-preserving swaps keep each neuron's degree but destroy which degrees connect to which. The worm's published rich club, a densely interconnected set of command interneurons that I did not re-derive from the cache, is a small, heavily weighted core. A dense core of k neurons has a loop gain that grows with the square root of k, so near-neutral or unstable modes are far likelier there than anywhere in an expander. The core is redundant, so single and pair deletions miss it, which is what 03m saw. Prediction: deleting the whole core collapses retention, deleting as many degree-matched non-core neurons does not. This is Fable 8 inverted: not weakly coupled modules, one over-coupled module.

3. **Hold-written against pulse-written.** The two rows differ at tick 0 for two reasons: 100 ticks at different levels, and 10 ticks of different ramps. A second protocol starts both rows at the common level, gives one a brief upward excursion and the other a downward one, and returns both. If N2's lead survives the pulse pair, the mechanism transports or stores a kick, families 1 to 3. If it vanishes, the memory is of the operating point, families 5 and 6, and the "history" is a level.

4. **The next two nulls.** A sampler that keeps N2's reciprocal pairs and their anatomical weights, shuffling only the rest, separates Fable 3 from Astra 6 and from the rich club. A sampler that rewires the chemical layer and then re-seats the gap junctions on the new reciprocal pairs, matching N2's overlap count, tests Astra 3 without N2's particular neurons.

## Experiments that split the families, and one idea taken further

| Measurement | Cost | What each outcome favours |
|---|---|---|
| **E1. Reweight the curve.** Per-genome share curves for N2 and all 640 graphs under three weightings: ratio of means as registered, median of per-genome shares, mean with the top late contributors removed. Add the count of signed sign-flips and of late rises. | seconds, local arrays | Lead survives all three: the slowness is typical, families 1, 2, 5, 6, 7. Lead collapses under the median: family 8, then E5 to say what the tail is. Many sign-flips in the tail: 10. Late rises: 3 or 5. |
| **E2. Per-genome curve shape.** Fit each genome's 32 points to one exponential, two, a power law, and a constant floor; note early humps. | seconds, local arrays | One slower exponential in most genomes: 1 or 7. Early hump or shoulder: 2. Two rates with a long slow one in most genomes: 3 or 1 with two modes. Power law in single genomes: 8 within the genome. Floor: 1 at the fold or 9. |
| **E3. The free-lesion regression.** Hybrid 2, on a fresh CPU panel or the CUDA genomes. | minutes | Time constants of named neurons: 7, and the names say 9 or Fable 4's road. Signs of a few edges: 1, and the edges say autapse, reciprocal pair, or turn-neuron latch. Biases: 5. Nothing beyond the nulls: 2, 6 or 8. |
| **E4. Linearise at the hold state.** Leading eigenvalue real part, departure from normality, maximal transient gain, participation and anatomical localisation of the slow eigenvectors, fraction of edges with presynaptic slope under 0.1, and the linear forecast of the curve against the observed one. | minutes, CPU, 256 genomes per graph | Forecast fits with a slow eigenvalue: 1. Fits without one but with transient gain: 2. Fails: 4 or 5. Slow vectors on the core: the rich club. Slow vectors on small components with many dead edges: 5 and 6 together. |
| **E5. Substeps 8, 16, 32.** | minutes, CPU | N2's lead shrinks: new idea 1 is part of it and family 6 is partly numerical. Stable: the mechanism is in the continuous dynamics. |
| **E6. Layer factorial.** Chemical layer N2 or shuffled, times gap layer N2, shuffled or off; plus the per-genome ΔP4 already in the gaps array, grouped by the sign pattern on gap-overlapped reciprocal pairs. | minutes, CPU, plus seconds on the arrays once genomes exist | Interaction, and ΔP4 negative for the two-positive group: Astra 3 as developed below. Additive: gaps are a generic leak, and the story is chemical, families 1, 2, 5. |
| **E7. Warm 25, 100, 400, and the pulse pair.** | minutes, CPU | Curve moves with warm: 11 or hybrid 7. Lead survives the pulse pair: 1 to 3. Lead vanishes: 5 or 6. |
| **E8. Reversal.** | minutes, CPU | Share survives: 1 or 6. Share lost: 2, 3 or 9. |

**Taken further: Astra 3, the two wiring layers fit together.** Astra listed it outside the three given a real chance, and it is the one idea that explains why no ensemble reproduces N2 and why the gaps-off result has the sign it has.

- **The mechanism, in one block.** Take neurons a and b with a reciprocal chemical pair and a gap junction between them. The linearised two-by-two block has the leak plus g on its diagonal and, off the diagonal, each chemical weight times its presynaptic slope plus the gap conductance. Its slow eigenvalue moves toward zero as the product of the two off-diagonal entries approaches the square of the leak. When both signs are positive the gap adds to each entry and pushes the loop toward neutrality. When both are negative the gap subtracts from each and pulls it away. With mixed signs the pair oscillates and the gap slows the oscillation. So the same gap junction is a leak on every neuron and a loop-gain boost on one sign pattern in four.
- **Why it fits the whole of 03mc.** Switching gaps off removes a leak everywhere, so P4 rises everywhere. In N2 it also removes the boost from the two-positive latches, so N2 gains less. That is Q-A's direction and roughly its size. Under weight permutation the gap junctions stay on their pairs but the heavy chemical weights leave them, which is why permutation keeps about half of N2's excess. The equipotential version of family 6 cannot predict any sign dependence; this version predicts it.
- **A structural number first.** Count N2's gap pairs that coincide with a reciprocal chemical pair, and compare with the count under independent shuffling of the two layers, which is what every sampler does. Seconds on the cached connectome. If the overlap is not far above chance the idea loses most of its force before any simulation.
- **A per-genome prediction from arrays that already exist.** For each N2 genome, score the sign patterns on its gap-overlapped reciprocal pairs. The two-positive-rich genomes should have higher tick-30 shares and a negative change in P4 when gaps go off; the two-negative-rich ones the reverse. Both quantities are in the long and gaps arrays. Only the scores need the genomes.
- **Then the null that keeps the relationship.** New idea 4's second sampler re-seats the gap junctions on the shuffled graph's reciprocal pairs. If it matches N2's retention, the mechanism is the relationship between the layers and not N2's neurons. If it does not, the neurons matter and the rich club is the next suspect.
- **Then the transplant.** Owner 3 made concrete: move N2's gap-overlapped reciprocal motifs into a shuffled graph with degree-matched replacements elsewhere, and predict the direction of the retention change before running it. Removal from N2 should shorten its memory; insertion should lengthen the null's.
- **The compounding.** New idea 1 protects the common mode of fast, heavily gap-coupled neurons. A two-positive latch across a gap pair is a common mode of that pair. So the integrator helps precisely the motif this idea names, which is one more reason E5 belongs beside E6.