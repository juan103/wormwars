The ideas fit together at four levels: **what carries the difference, what anatomy supports it, how food and turning access it, and how averaging over genomes makes it appear.** Several mechanisms could operate in the same brain. The tick-30 advantage and the late plateau could also have different explanations.

I read the repository files and ran no analyses or experiments. The checks establish:

- N2’s reported retention is approximately **0.097 at tick 150 and 0.090 at tick 300**; the ensemble median curves continue falling. Those observations leave several possible interpretations of the late tail. [Committed curves](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/report.json:5869)
- The deletion screen excluded the eight turn neurons. [03m results](/D:/Claude/random/wormWars/experiments/03m-p4-mechanism/RESULTS.md:110)
- These P4 probes reuse one **final** food level, approximately 0.22338, with the prescribed preparatory levels and ramps around it. [Bank](/D:/Claude/random/wormWars/experiments/03-generation0/pilot.json:2), [03mc protocol](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/PREREGISTRATION.md:48)
- The published retention is a **ratio of means**, \(\sum_g|d_g(t)|/\sum_g|d_g(0)|\). This makes starting amplitude part of the explanation. [Calculation](/D:/Claude/random/wormWars/scripts/p4mc.py:545)
- All five null samplers preserve each neuron’s chemical in-degree, out-degree and gap degree. This makes the **arrangement of degrees, weights, loops and pathways** the relevant development of the degree-based ideas. [Samplers](/D:/Claude/random/wormWars/wormwars/exp03/samplers.py:1)

**1. Families: all five sources**

Below, O means owner, C Claude, F Fable, A Astra, and R the ChatGPT roadmap. Numbers refer to their numbered ideas. Families overlap where an idea supplies both a dynamical mechanism and an anatomical location.

| Family | Ideas belonging here | Shared mechanism or useful distinction |
|---|---|---|
| **Intrinsic clocks placed at bottlenecks** | C1–2; F4; A11; R’s ordinary low-pass persistence and \(\tau\) controls | Slow neurons matter because of where they sit, how strongly they couple, and whether signals can bypass them. |
| **Feedback replenishes leakage** | O2; C4; F2–3, F7; A1; R’s slow eigenmodes and reciprocal/hub feedback | Autapses, reciprocal pairs and longer loops are different scales of the same proposal: reinforcement nearly balances loss. |
| **Nonlinear wells, thresholds and ghosts** | C4, C13; F7, F11, F15; A12, A15; R’s multistability and bifurcation analysis | The histories occupy different wells, pass near a slow bottleneck, or approach a threshold. **Motor-neuron storage** is a specific anatomical branch: F11 and A15. |
| **Weakly coupled reservoirs and rare islands** | C5, C7, C12; F8, F16; A7; R’s localized hub/module modes | A compartment stores a slowly exchanging trace. The pharynx is a named candidate; different genomes could activate different compartments. |
| **Transport delay and nonnormal propagation** | C11; F9–10; A4–5; R’s sequential and nonnormal memory | A cascade is a concrete implementation of a moving trace. More general nonnormal dynamics transfer the trace between spatial directions. |
| **Electrical protection and coordination between wiring layers** | C3; F5; A2–3; R’s gap-Laplacian alignment | Chemical dynamics write patterns that gap junctions weakly damp. The chemical–gap relationship can matter beyond either layer alone. |
| **Saturation changes the effective circuit** | C1, C11, C13; F6, F14; A10, A13; R’s state-dependent operators | Saturation can remove restoring feedback, isolate compartments, expose intrinsic clocks, hide voltage differences or change routes over time. These are distinct branches under one mechanism. |
| **Readout alignment and accessibility** | A9; R’s write–retain–read decomposition, balanced modes and alternative readouts | A trace can be unusually writable by food, readable by turning, or both, without being unusually persistent in every state direction. |
| **Population mixtures and amplitude weighting** | F1; A8; C5’s pooled broad-timescale interpretation; R’s regime census | A broad shift, more persistent genomes, stronger persistent genomes, and changing contributors to the mean are separate population explanations. |
| **Oscillations, circulating waves and spatial echoes** | O2; F12–13; A14; R’s phase memory | History can survive as phase or position along a travelling pattern. The ventral-cord transmission-line proposal is a spatial branch. |
| **Continuous memory coordinates** | O1; A18; R’s line/slow manifolds | A ring coordinate, line coordinate or approximately conserved weighted sum carries history. A ring of possible stationary states and a circulating oscillation remain separate branches. |
| **Aging and hierarchical relaxation** | C5–6; A16 | Preparation changes which timescales or configurations the system occupies. This can connect broad relaxation spectra to waiting-time dependence. |
| **Correlated paths under random signs** | A6; connected to O2 and R’s walk analysis | Overlapping routes share sign variables. Their joint contribution can survive averaging over random genomes. |
| **Bilateral symmetry sectors** | F17 | Symmetry organizes which patterns are driven, coupled, damped and observed. This deserves its own family because the input and readout select particular symmetry sectors. |
| **Winnerless sequential dynamics** | A17 | History records position among successive temporary winners. Keep this separately identifiable from smooth propagation and ordinary periodic motion. |
| **Near-chaotic persistence** | R’s near-chaotic regime | History survives through irregular separation dynamics, potentially with strong sensitivity to perturbations. |

The clearest cases of the same idea in different clothes are:

- **C12 and F16:** the pharyngeal echo chamber.
- **C6 and A16:** aging through preparation-dependent dynamics.
- **F12 and A14:** history-dependent oscillation phase.
- **F9 and A4:** transport through a cascade.
- **F11 and A15:** storage in or tightly around the turn neurons; F11 specifies mutual inhibition.
- **C3, F5, A2 and R’s gap-alignment proposal:** electrical protection. Their measurements emphasize different things—within-trajectory voltages versus the *difference between histories*.
- **F1 and A8:** population mixtures, with A8 additionally emphasizing the association between response amplitude and persistence.

Several other entries are **methods that connect families**:

- O3’s transplantation, C10’s regional morphing and R’s graph surgery test structural transferability.
- C8’s reversal tests direction dependence; C9’s noise-response comparison connects spontaneous fluctuations with driven relaxation.
- R’s instrumentation, numerical refinement, full-state geometry, operator analysis, differential currents and adjoints provide a common measurement language.
- R’s prior-level, slope, equal-integral/order and random-input assays distinguish memory content. Noise tests examine robustness; erasure, transplantation and rescue examine causation; fresh confirmation and delayed tasks examine generalization and utility.

**2. Hybrids across sources**

**A. A motor latch protected by electrical common modes**  
*F11 + C3/A2 + R’s write–retain–read decomposition.*

Suppose a dorsal-versus-ventral difference lives in the turn circuit, while left and right homologs carry similar differences. Gap coupling between homologs could spare that pattern. RIA and AIY could write or amplify it.

This combines storage location, electrical protection and sensory access into one circuit hypothesis. It predicts a trace that is left–right common but dorsal–ventral differential, with low gap dissipation. Motor-state erasure and delayed rebuilding would distinguish a local store from continuing delivery by upstream neurons.

**B. A reservoir whose entrance closes after writing**  
*C7 + F6 + R’s phase-specific interventions.*

A weakly coupled compartment receives the food history while a connecting hub is responsive. Later saturation suppresses the hub’s outgoing influence, reducing exchange and preserving what entered. Subsequent movement out of saturation exposes the trace again.

The new element is a **write-dependent change in insulation**. The same connection can be important during writing and comparatively unimportant during maintenance. Prediction: access currents peak early, compartment separation persists later, and intervention effects depend strongly on timing.

**C. Imperfect rings produce both fading traces and a persistent minority**  
*O1 + A7 + F1.*

An approximately continuous memory coordinate could be distorted differently by each random genome. Some realizations allow slow drift; others develop preferred positions that pin the coordinate. Different anatomical patches might support the coordinate in different genomes.

This gives one route from a broad relaxation advantage to a small persistent tail. Prediction: intermediate histories populate a smooth curve in some genomes but cluster near preferred positions in others. Perturbations along that curve relax differently from perturbations across it.

**D. A cascade of electrically protected compartments**  
*A4 + C3 + F13.*

The stages of a long pipeline could be gap-coupled groups. Chemical connections move the trace between groups, while electrical coupling rapidly equalizes differences within each group.

Here the trace travels through a sequence of comparatively protected common modes. Prediction: low within-group variation accompanies a moving between-group peak. Breaking a bridge changes delivery time; disrupting within-group organization changes protection. These effects can be separated from changing a single neuron’s clock.

**E. Overlapping paths couple response strength to persistence**  
*A6 + F1/A8 + R’s controllability–observability analysis.*

The same arrangement of overlapping paths might make a random sign realization both easy to excite and slow to forget. N2 would then gain twice: more useful long-lived realizations and more weight assigned to those realizations by the published statistic.

The new prediction concerns **covariance**, not just a slow mode or a rare class. A sign-randomized surrogate should reproduce an association between initial amplitude and later normalized retention. Measure absolute responses alongside squared responses so that the surrogate connects directly to Q-D.

**F. Preparation moves brains toward a dynamical bottleneck**  
*C6 + A12 + F15.*

Waiting longer could bring the histories closer to a slow region whose location depends on final food level. Apparent aging would then interact with operating point: strong preparation dependence near particular levels, weaker dependence elsewhere.

Prediction: a waiting-time × food-level map contains concentrated bands of long residence times, accompanied by localized low state speed. A more broadly distributed waiting-time effect would instead support hierarchical relaxation across many configurations.

**3. Additional ideas sparked by the synthesis**

**A. The measured difference survives because its components cancel less**

The eight motor contributions might decay at ordinary rates while their sum behaves differently. Define

\[
z_i(t)=c_i\,[\tanh v_i^\uparrow(t)-\tanh v_i^\downarrow(t)],
\]

\[
L(t)=\sum_i|z_i(t)|,\qquad
\kappa(t)=\frac{|\sum_i z_i(t)|}{L(t)}.
\]

Then \(|d(t)|=\kappa(t)L(t)\).

N2 could preserve coherence between the contributions, while null brains develop stronger cancellation. Alternatively, decreasing cancellation could compensate for decaying components.

This turns readout alignment into a concrete mechanism involving the **relative signs and timing of eight signals**. Recording those signals separates component persistence from cancellation immediately.

**B. Large traces enter a different contraction regime**

Normalization removes a constant gain factor, but nonlinear contraction can depend on separation size. N2 might write larger differences that spend longer in a slowly contracting region.

At the ramp end, preserve the midpoint \(m\) and replace the pair with

\[
v^\uparrow_\alpha=m+\alpha\delta v/2,\qquad
v^\downarrow_\alpha=m-\alpha\delta v/2.
\]

Varying \(\alpha\) asks whether the same brain and operating region retain large separations differently from small ones. Smooth amplitude dependence supports a finite-amplitude contraction mechanism; a sharp transition suggests basin or threshold structure; similar normalized curves support an approximately linear carrier.

**C. Corrective feedback arrives late**

Combine the pipeline idea with the restoring-feedback idea: N2’s trace might persist because the feedback that removes it takes longer to return.

Partition a local linear model into observed neurons \(x\) and hidden neurons \(z\). Eliminating \(z\) produces a feedback kernel

\[
K(s)=A_{xz}e^{A_{zz}s}A_{zx}.
\]

This measures the sign and delay of feedback returning through the hidden network. The mechanistic question becomes whether N2 has a later restoring component, a longer reinforcing component, or both.

That could explain a shoulder followed by faster decay without requiring one identifiable storage compartment. It also predicts different effects from cutting the outbound and return portions of a pathway.

**4. A few cheap measurements that separate families**

I would organize these around one shared recording, then reuse it. Existing-array work examines the measured genomes. CPU simulations would use fresh, paired exploratory draws on cached graphs; they should not be described as recreating the original GPU genomes from their seeds.

For CPU work, a small panel across N2 and the five ensembles, followed by interventions on a handful of representatives, is an approximately hour-scale **budget proposal**, not a benchmarked runtime.

**Measurement 1: Decompose the published curve by prevalence, amplitude and persistence.**  
*Existing arrays; seconds per graph.*

For genomes with adequate starting signal, let \(a_g=|d_g(0)|\) and \(r_g(t)=|d_g(t)|/a_g\). Within that subset,

\[
R(t)=\mathbb E[r(t)]
+\frac{\operatorname{Cov}(a,r(t))}{\mathbb E[a]}.
\]

Keep the small-start group separately accounted for. Also partition the original numerator into contributions from persistent, settled-with-separation, and other genomes, retaining the original denominator.

Outcomes would favour:

- **A broad shift in per-genome quantiles:** mechanisms affecting ordinary genomes—clocks, feedback, transport or electrical protection.
- **Similar bulk curves but a different persistent fraction:** rare islands, latches, ghosts or oscillatory minorities.
- **A large amplitude–persistence covariance:** hybrid E and write/read alignment.
- **Different groups dominating tick 30 and tick 300:** separate early and late mechanisms.

Signed reversals and rebounds can nominate candidates for subsequent full-state recording. The saved sampling interval limits what they establish about oscillations.

**Measurement 2: Record the state, its movement, and its projection onto turning.**  
*One shared CPU recording.*

Record both \(v(t)\) and \(\tanh v(t)\), state speed, the eight motor contributions, spatial participation and

\[
\frac{\sum_{i<j}G_{ij}(\delta v_i-\delta v_j)^2}
{\|\delta v\|^2}.
\]

Compare gap damping with matched perturbation directions in the same brain, as well as across graphs.

Outcomes would favour:

- **Persistent full-state separation in a nearly fixed direction:** feedback, intrinsic clocks, reservoirs or a slow manifold.
- **A moving localized peak:** transport, switching routes or spatial echoes.
- **Ordinary state decay but persistent readout projection:** accessibility or cancellation.
- **Low gap damping specifically along the history trace:** electrical protection and coordination between layers.
- **Localized late differences with varying locations between genomes:** rare islands.
- **Late trajectories aligned by a time shift:** phase memory.
- **Long dwells with abrupt recurring handoffs:** the winnerless carousel.

This recording can also expose a persistent voltage trace whose activity difference is compressed by saturation.

**Measurement 3: Compare frozen dynamics, changing dynamics and separation size.**  
*Reuse that recording; a few short CPU branches.*

For the two histories, use the finite-difference tanh slope

\[
s_i(t)=
\frac{\tanh v_i^\uparrow-\tanh v_i^\downarrow}
{v_i^\uparrow-v_i^\downarrow},
\]

with the derivative as the coincident-state limit. Combined with the actual semi-implicit update in [Brain.step](/D:/Claude/random/wormWars/wormwars/brain.py:434), these slopes give an exact difference-propagation operator along the recorded pair.

Compare frozen or averaged operators against later trajectories and independent small perturbations. Add the midpoint-preserving \(\alpha\) intervention above.

Outcomes would favour:

- **A frozen operator with a readable, excited slow mode:** near-balanced feedback or a fixed reservoir.
- **Delayed response and rotating directions despite faster modal decay:** nonnormal transport.
- **Strong dependence on the ordered gain sequence:** saturation-driven route switching.
- **Strong dependence on separation size:** finite-amplitude retention or basin structure.
- **A shared approximately conserved weighted sum across independent perturbations:** A18’s collective variable.

Exact reconstruction of the recorded pair is an arithmetic check; prediction of independent perturbations supplies the explanatory evidence.

**Measurement 4: Cross preparation duration with final operating level.**  
*A small CPU factorial.*

Use a few waiting times and nearby final food levels, keeping history amplitude controlled. On selected brains, add brief pulses and longer continuation.

Outcomes would favour:

- **Concentrated peaks in lifetime versus food level:** critical slowing, ghosts or threshold landscapes.
- **Preparation-dependent relaxation across a broad range:** aging or hierarchical reservoirs.
- **Preparation effects settling to a common curve:** relaxation toward a reproducible operating state.
- **Stable pulse-response delays across preparations:** a persistent transport architecture.
- **Multiple persistent endpoints under identical final input:** multistability or a continuous memory coordinate.
- **Persistent periodic trajectories with different timing:** oscillatory phase memory.

**Measurement 5: Interrupt maintenance after the histories have converged in input.**  
*A handful of representative CPU brains.*

At the ramp end and at a later time, erase the difference in the turn neurons, a candidate compartment, or a measured mode. Preserve the pair’s midpoint; compare equal-norm controls. Separately branch the same saved states with gaps switched off during maintenance.

Outcomes would favour:

- **Motor erasure causes lasting loss:** storage in or tightly around the output circuit.
- **The motor difference rebuilds:** upstream reservoirs or continuing delivery.
- **Compartment erasure causes a delayed loss at the output:** a remote reservoir or return pathway.
- **Maintenance-only gap changes alter state contraction:** direct electrical involvement in retention.
- **Different groups matter at different times:** a moving trace or changing access to a reservoir.
- **A small mode erasure matters more than anatomical group erasures:** a collective memory coordinate.

These interventions connect the families without requiring a full neuron-by-neuron screen.

**5. Taken further: Fable’s bilateral-symmetry idea**

I would develop **Fable 17** into a symmetry-resolved model of writing, storage and reading.

The interface makes this unusually concrete. The probe supplies equal food input to left and right sensory homologs. The turn readout averages left and right members within its dorsal and ventral groups. Thus both are symmetric under left–right exchange. The turn signal’s dorsal–ventral opposition is a separate distinction. [Interface](/D:/Claude/random/wormWars/configs/interface.yaml:21)

Let \(P\) exchange the curated bilateral partners and define

\[
Q_+=\frac{I+P}{2},\qquad Q_-=\frac{I-P}{2}.
\]

Every history difference separates into

\[
\delta v=\delta v_+ + \delta v_-,
\qquad \delta v_\pm=Q_\pm\delta v.
\]

Now there are two specific developments of Fable’s proposal.

**First: storage in the symmetric sector.** Food writes a bilateral common pattern, electrical coupling spares it, and the turn interface observes it. The anatomical arrangement would make the entire input–memory–output path occupy a favourable sector.

**Second: storage in a weakly accessible antisymmetric sector.** Random signs, biases, time constants and anatomical asymmetry couple the two sectors. Food could write into a hidden antisymmetric reservoir through that coupling, and the reservoir could leak back into the symmetric readout. This predicts that an intermediate amount of coupling might maximize *observable* delayed response.

The cheap measurement is to record the two sectors separately and decompose the effective operator into four blocks,

\[
K_{ab}=Q_aKQ_b,\qquad a,b\in\{+,-\}.
\]

Then use three matched small perturbations around the same food baseline: bilateral common, bilateral opposite, and unilateral. Read both symmetric and antisymmetric output combinations.

The outcomes have distinct interpretations:

- Persistent symmetric activity with low gap damping supports common-mode protection.
- Persistent antisymmetric activity with delayed symmetric output supports a hidden reservoir.
- Different decay rates between sectors support symmetry-selective dynamics.
- Similar state persistence but very different output visibility supports symmetry-selective access.

For a focused causal step, erase \(\delta v_+\) or \(\delta v_-\) after writing and observe whether the other sector rebuilds it. A linear surrogate can additionally vary only the coupling between sectors, keeping their internal operators fixed.

This also gives the owner’s transplantation idea a concrete target: transplant a circuit with **separately measurable input access, sector-specific persistence and output access**, then test whether the recipient acquires the predicted delay and symmetry dependence.