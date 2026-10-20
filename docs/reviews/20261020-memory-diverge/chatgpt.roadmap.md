# Roadmap: from P4 to a dynamical mechanism

Yes. This could become a particularly interesting part of WormWars—but I would **not start by following all synapses**. First identify the dynamical object carrying the history trace; then follow the synapses that create, preserve, and expose that object.

03mc already suggests that there may not be one single “memory place”:

- N2’s history difference relaxes more slowly.
- RIA and AIY strongly amplify the measured signal, but deleting them reduces the history numerator and ordinary response almost proportionally.
- Anatomical weight placement strongly increases response magnitude but does not fully explain normalized P4.
- Gap junctions change N2 and null-network dynamics differently. ([03mc results](https://github.com/juan103/wormwars/blob/main/experiments/03mc-p4-confirm/RESULTS.md))

That looks like a possible separation between **writing the trace, retaining it, and making it visible at the turn output**.

## 1. What does “memory” mean in 03mc?

The WormWars brain obeys a continuous leaky-rate equation of approximately this form:

\[
\tau_j\dot v_j =
-v_j+b_j+
\sum_i W_{ij}\tanh(v_i)+
\sum_iG_{ij}(v_i-v_j)+I_j.
\]

The synaptic weights do not change during a trial. There is no plasticity and no learned memory item. ([brain implementation](https://github.com/juan103/wormwars/blob/main/wormwars/brain.py))

Let the two histories be “rising” and “falling,” and define their internal-state difference as

\[
\delta v_t=v_t^{\uparrow}-v_t^{\downarrow}.
\]

Once both histories receive exactly the same current input, their future difference is determined entirely by the internal state:

\[
\delta v_{t+1}
=
F(v_t^{\uparrow},u)-F(v_t^{\downarrow},u).
\]

For nearby trajectories, this becomes approximately

\[
\delta v_{t+1}\approx J_t\delta v_t,
\]

where \(J_t\) is the local Jacobian of the recurrent dynamics. The turn-output difference is approximately

\[
\delta y_t\approx c_t^\top\delta v_t,
\]

where \(c_t\) describes how the turn readout observes the internal state.

That gives a precise mechanistic vocabulary:

- **The memory trace** is \(\delta v_t\): the difference in internal activity caused by the previous input.
- **The retention mechanism** is the recurrent state-transition operator \(J_t\).
- **The readout mechanism** is the projection \(c_t\) that makes part of that state difference visible as turning.
- **The synapses and time constants are the machine that creates the trace; the momentary activity state is what presently carries it.**

If the system has multiple attractors, the memory can instead be described as “which basin or fixed point the system occupies.” If it has sequential transient dynamics, the trace can move from one group of neurons to another. So asking “where does the memory live?” may have an answer like **“in a one-dimensional dynamical mode distributed over 40 neurons,”** rather than the name of one neuron.

Also, P4 is not yet a general measure of memory capacity. Its histories differ simultaneously in:

- their previous absolute food level;
- the sign of the recent slope;
- cumulative exposure over the preceding interval;
- the path taken through state space.

The present protocol therefore proves **path dependence**, but does not tell us which feature of the path is represented. The repository itself appropriately says that the confirmed interventions move the measured numbers but do not yet identify a mechanism. ([03mc results](https://github.com/juan103/wormwars/blob/main/experiments/03mc-p4-confirm/RESULTS.md))

---

## 2. The plausible mathematical mechanisms

These are the main dynamical patterns worth looking for.

| Candidate mechanism | What the activity would look like | Mathematical signature |
|---|---|---|
| **Ordinary low-pass persistence** | The same activity pattern simply fades | One or several exponential decays determined largely by \(\tau\) |
| **Slow recurrent eigenmode** | After a transient, the history difference settles onto one stable spatial pattern and decays slowly | A Jacobian eigenvalue close to 1 in discrete time, or close to 0 from below in continuous time |
| **Nonnormal or sequential memory** | The difference moves through a sequence of neurons or neuronal groups | No especially slow eigenvalue, but large finite-time singular values and an approximately feedforward Schur structure |
| **Discrete multistability** | Rising and falling histories settle into two genuinely different states | Two fixed points under the same final input; hysteresis and basin dependence |
| **Slow or line-attractor manifold** | A continuous coordinate of activity records previous input level | A family of fixed or extremely slow points with one approximately neutral direction |
| **Oscillatory phase memory** | Both histories approach the same oscillation, but at different phases | Complex modes or a stable limit cycle with persistent phase offset |
| **Near-chaotic persistence** | Tiny state differences persist or expand irregularly | Largest Lyapunov exponent close to or above zero; poor noise robustness |
| **Readout alignment** | The full state difference is not especially persistent, but it remains aligned with the turn readout | Ordinary \(\|\delta v\|\), exceptional \(c^\top\delta v\) |
| **Hub/reciprocity-induced broad timescales** | Some highly connected or reciprocally connected subnetworks are systematically slower | Slow modes localize on hubs or reciprocal structures; broad multi-exponential relaxation |

The distinction between slow eigenmodes and nonnormal transient dynamics is well established: near-critical eigenvalues generate genuine slowing, whereas nonnormal networks can propagate and amplify activity transiently even when all eigenvalues are safely stable. Schur decomposition is often more revealing than ordinary eigenvectors in the second case. ([Phys. Rev. E](https://link.aps.org/doi/10.1103/PhysRevE.86.011909))

Ganguli, Huh and Sompolinsky formalized the idea that a dynamical system can retain past inputs in its present state and showed how specially structured nonnormal networks can achieve long memory through a hidden feedforward architecture. ([PNAS](https://www.pnas.org/doi/10.1073/pnas.0804451105)) Continuous or approximate line attractors are another classical mechanism for storing an analog value. ([PNAS](https://www.pnas.org/doi/10.1073/pnas.93.23.13339))

A recent theoretical candidate is particularly relevant to WormWars: degree heterogeneity combined with partial reciprocity can generate effective self-coupling, localized slow hub modes, and a broad distribution of timescales. That paper does not directly establish anything about N2, but it gives you a concrete structural prediction to test. ([arXiv](https://arxiv.org/html/2603.04149v1))

---

## 3. The experimental sequence

### M0 — Instrument the complete dynamical system

Before interpreting modes, add a dedicated mechanism probe that records for both histories:

- the complete \(v(t)\) vector after every tick or substep;
- \(\tanh v(t)\);
- chemical and gap-junction currents;
- the raw and transformed turn outputs;
- the exact local Jacobian \(J_t=\partial F/\partial v\);
- sensor input and intrinsic drive separately.

Three tests should gate everything that follows:

1. Summed per-synapse currents must exactly reconstruct the total chemical and gap drive.
2. Automatic-differentiation Jacobians must agree with finite differences.
3. Representative slow genomes must retain the same qualitative dynamics with half and quarter time steps, and ideally in a small independently written CPU implementation or continuous-time solver.

The last test is important because a near-unit eigenvalue can be a real mechanism or a numerical integration artifact.

Use two panels:

- a **random unselected panel**, which estimates how common each mechanism is;
- an explicitly labeled **tail panel**, oversampling the unusually long-lived N2 genomes.

03mc found that 43 of 1,977 valid N2 genomes retained more than 10% of their initial difference at tick 300, and 26 met a settling criterion while still separated. But it explicitly did not claim stable states. That tail should be investigated separately from the typical N2 effect. ([03mc results](https://github.com/juan103/wormwars/blob/main/experiments/03mc-p4-confirm/RESULTS.md))

#### Gate

The full-state trajectories and their classifications remain stable under numerical refinement. Otherwise, stop and resolve the integration issue.

---

### M1 — Determine exactly what is remembered

The present rising/falling comparison needs to be expanded into a stimulus basis.

#### 1. Prior-level assay

Hold the network at several initial food levels and move all of them to the same final value. Ask whether the final state encodes the previous level continuously.

This distinguishes a graded trace from a binary rising-versus-falling effect.

#### 2. Slope assay

Construct trajectories with the same start, end and approximate integral, but different recent slopes. For example, one can overshoot and return while another undershoots and returns.

This asks whether the system remembers:

- the sign of the derivative;
- previous absolute level;
- or simply accumulated exposure.

#### 3. Equal-integral temporal-order assay

Give equal-area pulses at different times:

- early pulse versus late pulse;
- high-then-low versus low-then-high;
- two histories with the same start, end and integral but different ordering.

If the final state distinguishes order, this is richer than an ordinary scalar low-pass filter.

#### 4. Impulse and pseudorandom-input assay

Drive the food input with small pulses or a pseudorandom binary sequence around a fixed operating level. At every delay \(k\), train a cross-validated linear decoder to reconstruct \(u_{t-k}\) from the current full state:

\[
MC(k)=R^2\bigl(u_{t-k},\widehat u_{t-k}(v_t)\bigr).
\]

This produces a conventional **memory curve** rather than a single P4 number. Repeat the decoder using:

- the complete state;
- interneurons only;
- motor neurons only;
- the turn readout alone.

Dambre-style information-processing capacity can subsequently test nonlinear features such as products or functions of multiple past inputs, rather than only delayed scalar reconstruction. ([Scientific Reports](https://www.nature.com/articles/srep00514))

#### 5. Noise robustness

Repeat small-input memory curves with controlled process noise and initial-state noise. A mode that lasts for hundreds of deterministic ticks but has negligible signal-to-noise ratio may be dynamically interesting without being a robust memory substrate. Fisher Memory Curves were developed precisely to quantify how information about earlier inputs survives in a noisy dynamical state. ([PNAS](https://www.pnas.org/doi/10.1073/pnas.0804451105))

#### Gate

At the end of M1, you should be able to state something precise, such as:

> “N2 retains a fading estimate of the previous absolute food level.”

or:

> “N2 retains the temporal order of recent inputs beyond what can be explained by a one-pole low-pass filter.”

The result may simply be unusually slow low-pass filtering. That would still be a real and interpretable mechanism.

---

### M2 — Find the memory trace in state space

For every paired trajectory, calculate

\[
\delta v_t=v_t^{\uparrow}-v_t^{\downarrow}.
\]

Then separate two effects that P4 currently mixes:

\[
|\delta y_t|
\approx
\|c_t\|\,\|\delta v_t\|\,
|\cos\theta_t|,
\]

where \(\theta_t\) is the angle between the state difference and the readout direction.

This asks:

- Does N2 preserve a larger **full-state difference**, \(\|\delta v_t\|\)?
- Or does an ordinary state difference remain unusually well aligned with the turn output?
- Or both?

This distinction is essential. A turn readout can exhibit long history dependence even if the network as a whole does not contain unusually much decodable history.

#### Analyses

Use:

- neuron-by-time heatmaps of \(\delta v_i(t)\);
- singular-value decomposition of all difference trajectories;
- participation ratio to estimate effective dimensionality;
- dynamic mode decomposition to identify exponential or oscillatory components;
- principal angles between memory subspaces from different random genomes;
- projections by neuron class, degree, anatomical community and sensor-to-motor layer.

There are two especially informative outcomes:

**A common anatomical mode.** Across random N2 genomes, approximately the same neuronal subspace carries the trace. This would support a specific N2 circuit explanation.

**Different modes in different genomes.** N2 topology makes slow dynamics statistically more likely, but individual realizations use different neurons. In that case there may be no unique “memory circuit”; the mechanism is a graph-level propensity.

#### Gate

Decide whether the phenomenon is:

1. low-dimensional and anatomically repeatable;
2. low-dimensional but with different orientations across genomes;
3. genuinely high-dimensional;
4. principally readout alignment rather than full-state persistence.

Do not use “distributed memory” merely because single-neuron ablations failed. The repository already notes that redundancy, varying dependencies between genomes and exclusions from the deletion screen remain possible. ([03m results](https://github.com/juan103/wormwars/blob/main/experiments/03m-p4-mechanism/RESULTS.md))

---

### M3 — Classify the dynamical regime

Under the common final food input, search for fixed points and slow points using both history endpoints and many random initial states.

For each genome:

1. Solve \(F(v)-v=0\).
2. Minimize \(\|F(v)-v\|^2\) to find slow points even when no exact fixed point is nearby.
3. Continue the trajectories much longer than 300 ticks.
4. Calculate the local Jacobian at fixed or slow points.
5. Estimate the largest Lyapunov exponent.
6. Test for recurrent cycles and phase offsets.
7. Sweep final food level and recurrent gain to create a small bifurcation diagram.

Fixed- and slow-point analysis has been used to understand high-dimensional RNN mechanisms precisely because trajectories can often be explained by a relatively small collection of fixed points and their local linear dynamics. ([PubMed](https://pubmed.ncbi.nlm.nih.gov/23272922/))

#### Classification

Each genome should be assigned to one of these descriptive classes:

- common fixed point, rapid decay;
- common fixed point, one slow mode;
- common fixed point, multiple timescales;
- distinct fixed points or multistability;
- approximate slow manifold;
- stable oscillation with history-dependent phase;
- nonnormal transient sequence;
- irregular or chaotic dynamics;
- unresolved.

Then compare the **frequency of each class** between N2 and the null ensembles. The average N2 curve could otherwise hide a mixture—perhaps most genomes have moderately slow relaxation while a small tail is genuinely bistable.

#### Gate

A dominant dynamical family must explain both:

- the typical N2-versus-null shift;
- the exceptional long-lived tail, or why that tail is a distinct secondary phenomenon.

---

### M4 — Identify the writable, persistent and readable modes

This is the cleanest mathematical decomposition.

Around an operating state, write the linearized dynamics as

\[
\delta v_{t+1}=J\delta v_t+B\,\delta u_t,
\qquad
\delta y_t=C\delta v_t.
\]

Here:

- \(B\) describes how food input enters the sensory neurons;
- \(J\) determines how state differences evolve;
- \(C\) describes the turn readout.

The delay-\(k\) impulse response is

\[
h_k=CJ^kB.
\]

If \(J\) is diagonalizable,

\[
h_k=
\sum_m
\underbrace{(Cr_m)}_{\text{readability}}
\underbrace{(l_m^\top B)}_{\text{writability}}
\underbrace{\lambda_m^k}_{\text{persistence}}
\frac{1}{l_m^\top r_m}.
\]

This tells you exactly why a mode matters:

- food must be able to **write** it;
- it must **persist**;
- turning must be able to **read** it.

That decomposition gives a very attractive interpretation of the existing 03mc leads:

- the slower relaxation result points toward an unusual persistence factor;
- RIA, AIY and anatomical weight placement may contribute mainly to writability, readability or general gain;
- gap junctions may modify the persistence operator.

That is currently only a hypothesis, but it is directly testable.

#### Analyses

Compute:

- eigenvalues and left/right eigenvectors;
- Schur decomposition;
- singular values of \(J^k\);
- maximum finite-time transient gain;
- eigenvector condition numbers and pseudospectral sensitivity;
- modal participation ratios;
- the accuracy with which \(J^k\delta v_0\) predicts the observed nonlinear relaxation.

If one eigenvalue near 1 predicts the decay, the answer is slow recurrent feedback.

If eigenvalues are not especially slow but the propagator has large singular values and the activity pattern rotates through state space, the mechanism is nonnormal sequential memory.

If the linear prediction fails strongly, return to nonlinear attractors, saturation or trajectory-dependent Jacobians.

#### Balanced memory modes

Finite-horizon controllability and observability Gramians identify modes that are both reachable from food input and visible at the turn output:

\[
W_c=\sum_k J^kBB^\top(J^\top)^k,
\]

\[
W_o=\sum_k(J^\top)^kC^\top CJ^k.
\]

Balanced model reduction then ranks the state-space directions that matter for the input-output history response. This is a much stronger operational answer to “where does the memory live?” than ranking neurons by deletion: the answer may be one balanced mode distributed over many neurons. Controllability–observability balancing was developed to identify precisely these dynamically important input-output components. ([IEEE](https://ieeexplore.ieee.org/document/1102568))

#### Gate

A small set of modes should predict a declared fraction—perhaps 90%—of the observed history response and relaxation curve on held-out trajectories. If hundreds of modes are required, the eventual mechanism claim must remain high-dimensional.

---

### M5 — Causally erase, transplant and rescue the memory state

Permanent neuronal deletion is a blunt instrument. It simultaneously changes:

- how history is written;
- the network operating point;
- how it is retained;
- how it reaches the output.

Instead, intervene on the state after the two inputs have become identical.

#### Mode erasure

Let \(q\) be a candidate memory mode. At the ramp’s end, remove only the difference along \(q\):

\[
v^\uparrow
\leftarrow
v^\uparrow-q\,q^\top(v^\uparrow-v^\downarrow).
\]

If the future turn difference collapses while orthogonal perturbations of equal norm do not, the mode is necessary.

#### Mode transplantation

Insert the rising-history mode coordinate into the falling-history state, while leaving all orthogonal coordinates untouched.

If the future output moves toward the rising-history trajectory, the mode is sufficient to carry the relevant history information.

#### State transplantation by neuron group

Construct hybrid states:

\[
v^{\mathrm{hybrid}}_S
=
v^\uparrow_S,\qquad
v^{\mathrm{hybrid}}_{\neg S}
=
v^\downarrow_{\neg S}.
\]

Test RIA, AIY, AIZ, candidate interneuron groups and mode-derived sparse neuron sets. This asks whether the current states of those neurons are sufficient, rather than whether their permanent removal damages the entire system.

#### Phase-specific intervention

Turn a neuron, synapse class or gap junction off only during:

1. **writing:** before and during the ramp;
2. **maintenance:** after the inputs become identical;
3. **reading:** only during the last few output ticks.

This could settle the RIA/AIY question cleanly:

- If readout-only silencing reproduces most of their effect while maintenance-only silencing leaves the hidden-state trace intact, they are primarily conduits or amplifiers.
- If maintenance-only silencing selectively accelerates \(\|\delta v_t\|\) decay, they participate in retention.
- If write-only intervention prevents the mode from being initialized, they contribute to encoding.

Do the same temporal decomposition for gap junctions. “Gaps off for the entire experiment” cannot tell whether they alter encoding, retention or readout.

#### Rescue

After disrupting the candidate circuit, reinject the missing state-mode coordinate. If the history response returns, that is substantially stronger evidence than ablation alone.

#### Gate

You have localized a memory mode only when you can show:

- necessity through mode erasure;
- sufficiency through transplantation;
- specificity against matched control modes;
- preferably rescue after a structural intervention.

---

## 4. Following every synapse—the useful way

Yes, you can literally track every synapse. But there are two different quantities.

### Descriptive differential current

For a chemical synapse \(i\rightarrow j\),

\[
\Delta I^{\mathrm{chem}}_{i\to j}(t)
=
W_{ij}
\left[
\tanh v_i^\uparrow(t)-
\tanh v_i^\downarrow(t)
\right].
\]

For a gap junction between \(i\) and \(j\), its differential contribution into \(j\) is

\[
\Delta I^{\mathrm{gap}}_{i\leftrightarrow j\to j}(t)
=
G_{ij}
\left[
\delta v_i(t)-\delta v_j(t)
\right].
\]

An edge-by-time animation of those quantities could reveal recognizable patterns:

- repeated circulation around a feedback loop;
- a traveling wave through a chain;
- synchronization within a gap-junction community;
- activity moving from sensory neurons through interneurons toward the motor readout;
- a persistent hub-centered mode.

But current magnitude alone does not tell you whether an edge matters to the eventual output. Large currents may cancel.

### Causal downstream contribution

Start at the final turn output and propagate an adjoint sensitivity backward:

\[
\lambda_T=\nabla_{v_T}y_T,
\qquad
\lambda_t=J_t^\top\lambda_{t+1}.
\]

An edge’s differential current can then be weighted by the sensitivity of the future output to current entering its postsynaptic neuron. Integrated gradients between the two complete trajectories can provide a nonlinear counterpart.

For a time-invariant linearized system, the effect of every possible walk through an edge is already summarized by

\[
h_k=CJ^kB.
\]

The derivative with respect to a particular matrix element is

\[
\frac{\partial h_k}{\partial J_{ab}}
=
\sum_{r=0}^{k-1}
(CJ^{k-1-r})_a
(J^rB)_b.
\]

That expression effectively follows every length-\(k\) path passing through edge \(b\rightarrow a\), without explicitly enumerating an exponential number of paths.

### What to do with the edge ranking

Separate edges into three rankings:

- edges that write the memory mode;
- edges that maintain it;
- edges that expose it at the output.

Then perturb **groups**, not only individual edges:

- top-ranked edges;
- reciprocal pairs;
- short cycles;
- feedforward chains;
- chemical–gap hybrid motifs;
- matched random edges with the same weights, degrees and sensor/motor distance.

Single-edge deletion can miss a highly redundant mechanism. Test pairwise or group interactions and compare the combined effect with the sum of individual effects.

---

## 5. Test the structural origin in N2

Once you have a candidate dynamical mechanism, ask what fixed feature of N2 makes it more frequent.

### A. Spectral matching

Generate or select null graphs matched to N2 on:

- leading Jacobian eigenvalue;
- spectral radius;
- transient gain;
- degree distribution;
- reciprocity;
- input-output response magnitude.

Then ask which matching condition removes N2’s relaxation advantage.

For example:

- If spectral-radius matching removes it, N2 may simply sit closer to instability.
- If eigenvalues match but N2 still retains history, nonnormal geometry or input/output alignment is implicated.
- If transient-gain matching removes it, a hidden feedforward mechanism becomes likely.

### B. Time-constant controls

Because each neuron has an intrinsic \(\tau_j\), test:

- all \(\tau_j\) equal;
- the same \(\tau\) multiset randomly reassigned to neuron labels;
- \(\tau\) paired across N2 and null networks;
- \(\tau\) correlations with degree, mode participation and neuron class.

This separates topology-created timescales from lucky topology–\(\tau\) alignment.

### C. Reciprocity, degree and hubs

Measure whether slow-mode participation correlates with:

- in-degree and out-degree;
- reciprocal chemical connectivity;
- short directed cycles;
- hub status;
- community position;
- anatomical edge magnitude.

Then create targeted nulls that preserve everything except the leading candidate. Recent theory predicts that degree heterogeneity combined with partial symmetry can create effective self-feedback, broad timescales and hub-localized slow modes; WormWars can test whether anything resembling that mechanism appears in this very different small connectome model. ([arXiv](https://arxiv.org/html/2603.04149v1))

### D. Gap-junction geometry

Gap junctions contribute a diffusive Laplacian-like term. Such coupling generally damps differences across connected neurons, but it need not damp every mode equally.

A concrete hypothesis suggested by 03mc is:

> The N2 memory mode lies in a gap-junction subspace that is relatively weakly damped, whereas the history modes generated by shuffled chemical graphs align with gap-junction modes that are damped more strongly.

Test this by:

1. extracting the candidate memory mode \(q\);
2. measuring its one-step damping attributable specifically to the gap operator;
3. projecting \(q\) onto gap-Laplacian eigenmodes;
4. comparing this alignment across N2 and null graphs;
5. selectively rewiring gap edges while preserving gap degree;
6. turning gaps off only during maintenance.

That would explain the apparently paradoxical finding that removing gaps increases P4 everywhere but increases it much more in null networks. It would replace “gap junctions matter somehow” with a concrete mode-alignment mechanism.

### E. Graph surgery and transplantation

Once a structural motif or mode-supporting edge set has been identified:

- remove it from N2 with degree- and weight-matched replacement edges;
- insert it into matched null graphs;
- preserve total edge count and basic strength statistics;
- predict the direction and approximate size of the dynamical change before running it.

The strongest result would be bidirectional:

> Removal shortens the memory timescale in N2, and matched transplantation lengthens it in null graphs.

---

## 6. Orthogonal confirmation

After the exploratory mechanism work, freeze one narrow model and test it on fresh graphs and genomes.

A good confirmatory statement might be:

> N2’s elevated history persistence is caused by a food-writable and turn-readable nonnormal mode supported by a specific reciprocal-hub structure. Its predicted mode coordinate explains at least 80% of the delayed response, erasing that coordinate removes the effect, and transplanting the supporting structure increases persistence in matched null graphs.

Or perhaps:

> N2 has no special nonnormal chain; it instead has a larger probability of a single near-critical mode, and its gap-junction organization selectively spares that mode.

The confirmation should use:

- fresh N2 parameter draws;
- fresh null graphs;
- an independent implementation for at least the central calculation;
- new pulse or pseudorandom stimuli;
- a readout not used to discover the mechanism;
- one or two preregistered predictions, not another large exploratory family.

---

## 7. Functional memory comes last

Only after identifying a dynamical mechanism should you ask whether it is useful.

Build a task in which:

1. a cue is visible;
2. the cue disappears;
3. a delay follows;
4. behavior must depend on the earlier cue.

A delayed-choice maze or delayed alternation task would work. Include a zero-delay version that requires the same sensing and motor capabilities without memory.

Then intervene on the identified mode:

- mode intact;
- mode erased after cue removal;
- matched orthogonal mode erased;
- structural edges removed;
- rescue by reinjecting the mode.

A selective loss on the delayed task, but not the zero-delay control, would justify calling the phenomenon **functional memory**.

Until then, the safest description remains:

> **A fading internal trace of recent input history.**

---

## Recommended experiment packaging

I would package the work into four studies rather than dozens of tiny ones.

### 03md — Memory content and dynamical census  
*Exploratory.*

- Complete-state recorder and numerical validation.
- Orthogonal stimulus set.
- Full-state memory curves.
- State amplitude versus readout alignment.
- Fixed points, slow points, Jacobians, Schur modes and genome classification.

**Output:** one or two candidate mechanisms.

### 03me — Causal memory mode  
*Confirmatory on fresh draws.*

- Predeclared mode or subspace.
- Mode erasure and transplantation.
- Write/maintain/read interventions.
- RIA/AIY and gap-junction phase decomposition.
- Predicted relaxation curve from the mode.

**Output:** what dynamical object carries the history trace.

### 03mf — Synaptic and topological mechanism  
*Exploratory followed by a small confirmation.*

- Differential-current and adjoint maps.
- Edge and motif leverage.
- Spectral, reciprocity, hub and gap-alignment tests.
- Targeted removal, transplantation and rescue.

**Output:** why N2 topology makes the mode more likely.

### 03mg — Orthogonal and functional validation

- Independent implementation.
- Standard delayed-input memory curves.
- New stimuli and readouts.
- Delayed behavioral task with a matched memory-free control.

**Output:** whether the dynamical trace generalizes and whether it has behavioral value.

---

## My current best mechanistic framing

The existing results most naturally motivate—but do not yet establish—this decomposition:

\[
\boxed{
\text{food history}
\;\xrightarrow{\text{write}}\;
\text{persistent internal mode}
\;\xrightarrow{\text{RIA/AIY and motor routing}}\;
\text{turn difference}
}
\]

with gap junctions modifying the decay properties of the internal mode.

RIA and AIY are presently stronger candidates for **signal routing or amplification** than for the storage site, because their deletion scales the ordinary response and history numerator together. The weight-placement result may belong to the same gain pathway. The slower relaxation result is the strongest clue about the actual retention mechanism. ([03mc results](https://github.com/juan103/wormwars/blob/main/experiments/03mc-p4-confirm/RESULTS.md))

The single highest-value next experiment is therefore:

> **Record the complete paired state trajectories, decompose the turn difference into full-state persistence versus readout alignment, find fixed/slow points and exact Jacobian modes, and then erase and transplant the leading candidate mode.**

That experiment would tell you whether 03mc is about a slow eigenmode, a moving nonnormal trace, multistability, readout geometry—or something not yet anticipated. Only after that should the project descend to the individual-synapse level.
