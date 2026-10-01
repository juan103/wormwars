## Reuse now

1. **[READ] Start with the released Hironaka–Sumi worm chemotaxis baseline.** The [MIT-licensed repository](https://github.com/118-Oganesson/c_elegans_chemotaxis) contains a Rust simulator, genetic algorithm, configuration files, evolved genes and Python analysis. It implements a small ASE–AIY–AIZ–SMB circuit using temporal sensing. **[INFERENCE]** This saves reconstructing a successful worm model from equations and gives you a positive control for sensory preprocessing, steering and evolution. It is not a stereo controller.

2. **[READ] Reuse small steering circuits before building the ring.** [Rañó’s Braitenberg analysis](https://doi.org/10.1109/ICRA.2012.6224583) provides the sensor–motor mathematics. [Adden et al.](https://doi.org/10.1162/neco_a_01540) built a four-unit insect steering model and connected it to an existing navigation network; [their code is public](https://github.com/stanleyheinze/insect_steering), although I found no explicit code licence. **[INFERENCE]** These save designing the first comparator and, particularly, the experiments for calibrating its interface with another circuit.

3. **[READ] Use ENOMAD as the closest released large-connectome optimization comparison.** The published implementation includes a 300-neuron model and chemotaxis benchmark. Both the [optimizer](https://github.com/dsb-lab/ENOMAD) and [archived paper implementation](https://doi.org/10.5281/zenodo.17591250) are MIT-licensed. **[INFERENCE]** Take its search procedure and benchmark controls, rather than interpreting it as an already-solved stereo worm: its sensory interface differs substantially from yours.

4. **[READ] If you need a ring, begin with Noorman’s implementation.** [DiscreteRingAttractor](https://github.com/HermundstadLab/DiscreteRingAttractor), also [archived on Zenodo](https://doi.org/10.5281/zenodo.12789923), is MIT-licensed MATLAB code with explicit rate dynamics, parameter construction and small-ring failure analyses. **[INFERENCE]** It saves deriving and debugging a minimal ring, including the easily missed problem of a persistent bump that cannot move under weak angular input.

5. **[READ] Take empirical steering tests from Matsumoto et al.** Their [released dataset and model code](https://doi.org/10.6084/m9.figshare.23583705), under CC BY 4.0, accompany experiments on phase-dependent salt steering. **[INFERENCE]** The phase-response measurements and compact motor model are more immediately useful to WormWars than importing an entire biomechanical simulator.

6. **[READ] Reuse existing environments to test whether memory earns its cost.** [chemoxrl](https://github.com/kirkegaardlab/chemoxrl) supplies spatial-versus-temporal chemotaxis models and trained weights; [plumetracknets](https://github.com/BruntonUWBio/plumetracknets) supplies changing-wind plume tasks and recurrent policies. Both are MIT-licensed. **[INFERENCE]** These save building the harder environments and baselines needed to distinguish useful memory from extra recurrent capacity.

7. **[READ] Reuse mutation and module-selection machinery selectively.** [Safe Mutations](https://github.com/uber-research/safemutations) supplies MIT-licensed output-preserving perturbation methods. [MM-NEAT](https://github.com/schrum2/MM-NEAT) supplies module duplication, designed-versus-evolved selection and module-usage analysis. **[INFERENCE]** Port those mechanisms into your existing experiment framework before replacing the whole optimizer.

**[INFERENCE] My main recommendation is to split E4s into two questions: first, whether a seeded comparator can establish useful stereo control through your motor interface; second, whether directional memory improves that controller. The literature supports both kinds of machinery, but does not establish that a ring remedies weak differential sensitivity.**

**[READ] Review scope.** I inspected the public WormWars repository at commit [`df50f6a`](https://github.com/juan103/wormwars/tree/df50f6a5433d3079888aa661b88c2e769b139fc7), including README, ROADMAP, DECISIONS and the relevant experiment reports. `docs/E4s/DESIGN.md` was absent from that snapshot, so the E4s description below follows your supplied brief. Software availability and licences were checked on **30 September 2026**. I inspected implementations but did not install or reproduce the cited simulators.

**Evidence tags:** `[READ]` means full-text evidence or directly inspected repository material; `[ABSTRACT]` means abstract only; `[SECONDARY]` means a claim obtained through a review or another source’s citation; `[INFERENCE]` means my analysis or proposed experiment. Tags apply to the whole associated paragraph or table entry. **Each research paper discussed below is a single study, not an independent replication; preprints and reviews are marked explicitly.**

## Our plan versus prior work

| WormWars component | What already exists | Assessment |
|---|---|---|
| **E4s: small bilateral steering module** | [READ] Braitenberg controllers, evolved bilateral sensor–motor maps and insect steering circuits already implement this general computation. [Rañó](https://doi.org/10.1109/ICRA.2012.6224583); [Simões et al.](https://doi.org/10.1038/s41467-021-22322-w). | [INFERENCE] The comparator itself is established. Its successful implementation within your signal, weight and motor-interface constraints remains an experiment. |
| **E4s: add a ring and update it during turns** | [READ] Portable heading rings, angular-velocity shifters and navigation-memory models exist. [Noorman](https://doi.org/10.1038/s41593-024-01766-5); [Goulard](https://doi.org/10.1371/journal.pcbi.1009383); [Sun](https://doi.org/10.7554/eLife.73077). | [INFERENCE] The combination is established at the architectural level. A benefit in your continuously available, relocating Gaussian field is unproven. |
| **E4s: graft, then observe retention or erosion** | [READ] Incremental evolution, controller seeding, circuit grafting and co-adaptive neural augmentation have precedents. [Tomko–Harvey](https://users.sussex.ac.uk/~inmanh/do-not-disturb.pdf); [Adden](https://doi.org/10.1162/neco_a_01540); [Bryan et al.](https://doi.org/10.1088/1741-2552/accaa9). | [INFERENCE] I found no matching experiment that freely evolves a stereo graft inside your kind of worm mask and distinguishes retention, bypass, redundancy and transfer into the host. That is a defensible research gap; modular neuroevolution itself is not new. |
| **E3: two policies plus a persistent selector** | [READ] Neural hysteresis, SR latches and designed/evolved module arbitration have been built. [Hülse–Pasemann](https://doi.org/10.1007/3-540-46084-5_127); [Spaeth et al.](https://doi.org/10.1371/journal.pone.0240267); [MM-NEAT](https://doi.org/10.1162/evco_a_00181). | [INFERENCE] Reuse the selector concepts. The A/B shuttle, trails and subsequent consolidation form your specific experimental combination, not a first demonstration of a neural latch. |
| **E4: assemble modules, evolve integration** | [READ] Olivares et al. evolved a unit, replicated it into a body and continued optimization. NMODE assembled independently evolved controllers. [Olivares](https://doi.org/10.3389/fncom.2021.572339); [NMODE—preprint](https://arxiv.org/abs/1701.05121). | [INFERENCE] Assembly and joint optimization are precedented. Demonstrating that computation moves across initially separate connectomes requires additional causal tests. |
| **E4: prune to a minimal circuit** | [READ] Lesion studies already demonstrate misleading single-neuron rankings and rescue by additional lesions. [Fakhar–Hilgetag](https://doi.org/10.1371/journal.pcbi.1010250). | [INFERENCE] Greedy pruning is useful, but its result is an order-dependent circuit irreducible under your test—not necessarily the globally smallest circuit. |

## 1. Evolved or trained C. elegans chemotaxis controllers

### What was actually optimized

| Study | Model and retained circuitry | Optimization, task and reported result |
|---|---|---|
| **[READ] Izquierdo & Lockery 2010** | Four units: temporal ON/OFF sensors and dorsal/ventral motor units. Polysynaptic pathways are compressed; this is not a literal four-cell connectome subgraph. An imposed oscillator supplies head motion. | Eight-parameter GA; population 10, 100 generations, 100 runs. Seventy-seven runs achieved training fitness ≥0.75. Table 1 reports chemotaxis indices approximately 0.88 in cones and 0.87 in Gaussians. Take the phase-gating mechanism and embodiment controls. [Paper](https://doi.org/10.1523/JNEUROSCI.2606-10.2010). |
| **[READ] Izquierdo & Beer 2013** | Ten cells: ASE L/R, AIY L/R, AIZ L/R and four SMB cells. Retains short ASE→SMB anatomical paths, removes weakly supported contacts, and includes AIY/AIZ electrical coupling. Graded neurons with logistic outputs; connection strengths/signs are optimized. | Twenty parameters; GA population 60, 300 generations, 100 runs. Twenty-seven runs reached fitness ≥0.75. Table 1 gives indices 0.875 in cones and 0.871 in Gaussians. The mechanism is temporal input interacting with head-sweep phase. [Paper](https://doi.org/10.1371/journal.pcbi.1002890). |
| **[READ] Chen et al. 2022** | ASE, twelve interneuron pairs and four SMB cells; conductance-based chemical and electrical connections. ASEL has stochastic all-or-none responses; ASER has graded responses. | GA optimizes 463 parameters; population 300, up to 1,000 generations. Of 300 evolved models, 108 passed the authors’ performance/reliability criteria. Table 1 reports mean indices about 0.753/0.749 in cone/Gaussian fields. A subsequent noisy-synapse stage adds random walking. [Paper](https://doi.org/10.1038/s41598-022-06988-w). |
| **[READ] Hironaka & Sumi 2025 — reviewed preprint, v3** | Extends the ten-cell model, constraining AIY→AIZ to inhibition; 22 optimized parameters. Temporal sensory filtering includes an explicit gain of 100. | GA population 60, 300 generations, 100 searches. A selected constrained model achieves CI 0.877. Changing ASER→AIY sign switches preference in the model; this is a proposed mechanism, not an A/B latch. [Reviewed preprint](https://elifesciences.org/reviewed-preprints/104456v3); [MIT implementation](https://github.com/118-Oganesson/c_elegans_chemotaxis). |
| **[READ] Chen, Yu & Xue 2023: CENN** | **469 model nodes**, including neurons, muscles and other cells; 4,869 chemical and 1,433 electrical connections, plus proprioceptive feedback. Single-compartment graded dynamics; ASE inputs encode temporal concentration change. | BPTT/Adam imitation of a PID controller, using 6,000 recorded sequences. Table 2 reports random-start CI 0.72±0.34, versus 0.65±0.33 for the teacher. Take the teacher-to-connectome training pipeline and ablation procedure. [Paper](https://doi.org/10.3390/math11112442); [code](https://github.com/zhongyuchen/digital-twin-c-elegans), with no explicit licence found. |
| **[READ] Zhao et al. 2024: BAAIWorm** | **136 neurons**, multicompartment morphology and channel models, connected to a 96-muscle body. This is not a freely evolved 302-cell rate network. | Gradient-based fitting of neural correlation data and a separately fitted motor readout. Chemotaxis uses the time derivative of head concentration. Take the neural-data fitting, morphology or body stack if needed. [Paper](https://doi.org/10.1038/s43588-024-00738-w); [Apache-2.0 code](https://github.com/Jessie940611/BAAIWorm); [data](https://doi.org/10.5281/zenodo.13951773). |
| **[READ] Churchland & Garcia-Ojalvo: ENOMAD, published online 2025, issue 2026** | **300 neurons**, excluding CAN, with 3,682 connections; discrete leaky integrate-and-fire dynamics and muscle control. Gap edges become independently optimized directed weights. | Global evolutionary search plus derivative-free NOMAD local optimization. Published version includes Gaussian chemotaxis, but sensory activation is triggered inside a food-radius boundary, rather than supplied as two analogue nose readings. Eq. 1 uses leak **λ=0.98**. [Paper](https://doi.org/10.1016/j.isci.2025.114436); [MIT paper archive](https://doi.org/10.5281/zenodo.17591250). |
| **[READ] Olivares, Izquierdo & Beer 2021** | Anatomical ventral-cord neuromechanical circuit with repeated units and 44 shared parameters. | **Locomotion, not chemotaxis.** First evolve an isolated rhythmic unit; then embed repeated copies in the body and continue evolution. Of 160 runs, 104 achieved baseline locomotion and 15 passed further biological tests. Take the staged assembly protocol and supplementary parameters. [Paper](https://doi.org/10.3389/fncom.2021.572339). |

**[INFERENCE] The chemotaxis indices above are not comparable to WormWars’ targets per episode. Nor are these interchangeable optimization problems: derivative preprocessing, imposed oscillation, proprioception, parameter bounds and embodiment all change what evolution must discover.**

**[READ] Code provenance matters for the classic models.** [`CE_orientation`](https://github.com/edizquierdo/CE_orientation) is useful author code, but its current source includes fully recurrent interneuron connectivity and sensory-weight settings that differ from the 2013 paper. I found no licence in its tree. [`CE_locomotion`](https://github.com/edizquierdo/CE_locomotion) also exists, but I did not establish an exact licensed reproduction of the Olivares paper. For an executable small chemotaxis reference, the newer Hironaka repository is clearer.

### A recent, closely related failure—and its limits

**[READ] Lee 2026 — unreviewed preprint.** A fixed, atlas-fitted c302 network is controlled by an **external** evolved policy that injects currents into selected neurons. Command/steering stimulation supports chemotaxis; sensory-only stimulation performs near chance. One training seed remains in a reversal-only local optimum. Adding bilateral log-concentration information improves open-ground navigation and directional bending. However, the model includes an engineered motor layer, and the adaptive weights are outside the connectome. [Preprint DOI](https://doi.org/10.64898/2026.09.06.749731); [full author draft](https://github.com/kairess/worm-whisperer/blob/main/docs/PAPER_DRAFT.md).

**[INFERENCE] This is relevant evidence that sensory access, motor repertoire and optimization traps can dominate a connectome experiment. It is not a replication of your plateau, and it does not demonstrate that evolving weights on the 302-cell mask discovers stereo subtraction.**

### Equations worth taking

**[READ] Izquierdo & Beer 2013, Eqs. 2–3**, for graded interneurons:

\[
\tau_i\frac{dy_i}{dt}
=-y_i+\sum_jw_{ji}\sigma(y_j+\theta_j)
+\sum_kg_{ki}(y_k-y_i)+I_i,
\qquad
\sigma(x)=\frac{1}{1+e^{-x}}.
\]

**[READ] Their Eq. 5** gives the reduced dorsal/ventral motor readout:

\[
\varphi=\frac{d\mu}{dt}
=w_{NMJ}\left[\sigma(y_D+\theta)-\sigma(y_V+\theta)\right].
\]

**[READ] Their Methods allow chemical weights and biases in \([-15,15]\)**—substantially broader than your stated bounds. These equations and that range were checked in the [full paper](https://doi.org/10.1371/journal.pcbi.1002890).

**[READ] Hironaka & Sumi, Appendix 1, Eq. A1**, explicitly amplifies the difference between recent and preceding concentration averages. With the dummy integration variable renamed \(s\):

\[
z=
\frac{100}{N}\int_{t-N}^{t}C(s)\,ds
-
\frac{100}{M}\int_{t-(N+M)}^{t-N}C(s)\,ds.
\]

**[READ] Eqs. A2–A3** rectify this into ON/OFF signals:
\[
z_{ON}=\max(z,0),\qquad z_{OFF}=\max(-z,0).
\]

**[READ] Appendix Tables 2 and 4** specify \(\tau=0.1\,s\), oscillator period \(4.2\,s\), and representative values \(N=0.4907\,s\), \(M=0.7618\,s\), \(w_{OSC}=2.9655\), \(w_{NMJ}=2.7969\). The full champion is in Table 4 and the released genes. [Source](https://elifesciences.org/reviewed-preprints/104456v3).

**[INFERENCE] The reusable lesson is preprocessing plus a calibrated motor interface. These numbers cannot be transplanted unchanged into tanh neurons measured in ticks.**

## 2. Stereo versus temporal steering

### Can the worm compare its two sides?

**[SECONDARY] The frequently cited amphid-pore separation is approximately 10 μm.** This comes from [Lockery’s 2011 review](https://doi.org/10.1016/j.conb.2011.06.009), which cites [Ward et al. 1975](https://doi.org/10.1002/cne.901600305). I read the review, but did not directly verify that measurement in the original anatomical paper. Treat it as an approximate anatomical statement, not a measured distribution with a known error bar.

**[READ] The more consequential issue is the steering axis.** On agar, the worm lies on a lateral side and bends dorsoventrally. ASEL and ASER occupy approximately the same position along that steering axis. Matsumoto et al. explicitly use this geometry to explain why salt-gradient steering requires temporal sensory information combined with movement. [PNAS 2024](https://doi.org/10.1073/pnas.2310735121).

**[INFERENCE] Therefore, “left” and “right” neuron names do not make ASEL/R equivalent to your game’s horizontally separated noses. The evidence does not justify the unrestricted statement that worms cannot compare spatial signals at all. It does justify saying that the standard salt-klinotaxis mechanism is not ordinary simultaneous amphid tropotaxis.**

### Which circuits implement steering?

- **[READ] AIY–AIZ–SMB/RME:** Kocabas et al. used phase-dependent AIY stimulation to control gradual curving, while symmetric stimulation affected reversal frequency. Sampling a virtual gradient at the nose worked; a gradient experienced at the AIY soma failed because of its displaced sampling position and resulting delay. This is a strong reason to audit sensing location and timing. [Nature 2012](https://doi.org/10.1038/nature11431).

- **[READ] ASER/AIZ–SMBD in salt navigation:** Matsumoto et al. measured phase-dependent responses of SMBD to salt decreases. Responses during ventral bending counteracted that bend. RIA was dispensable for the salt-klinotaxis conditions tested. Their compact model includes assumptions—for example, a symmetric SMBV response that was not directly detected. [Paper](https://doi.org/10.1073/pnas.2310735121); [data and model](https://doi.org/10.6084/m9.figshare.23583705).

- **[READ] RIA–SMD in odour-guided head orientation:** Ouellette et al. describe sensory signals interacting with motor-related calcium in separate dorsal and ventral RIA axonal compartments. RIA output biases the appropriate motor compartment; blocking its release impairs head orientation toward an odour stream. Their “gate-and-switch” is head-phase-dependent routing, not an SR memory latch. [eNeuro 2018](https://doi.org/10.1523/ENEURO.0121-18.2018).

- **[ABSTRACT] Complementary navigation strategies:** Iino & Yoshida report complementary pirouette and weathervane mechanisms, with ASE/AIZ involvement. I verified the abstract rather than the full original article. Its [erratum](https://pmc.ncbi.nlm.nih.gov/articles/PMC6665697/) corrects gradient and distance units, relevant if importing numerical settings. [Original DOI](https://doi.org/10.1523/JNEUROSCI.3633-08.2009).

**[INFERENCE] A single scalar rate state for RIA cannot directly reproduce its compartment-specific computations. More generally, retaining neuron names and anatomical edges does not automatically retain the sensorimotor computations implemented by those cells.**

### Has a constrained worm model learned bilateral steering?

**[READ] In the broad sense, the Lee preprint supplies bilateral information to an evolved controller acting through a fixed worm network.** The classic Izquierdo models instead use temporal ON/OFF information, despite containing anatomically left/right cells. [Lee](https://doi.org/10.64898/2026.09.06.749731); [Izquierdo–Beer](https://doi.org/10.1371/journal.pcbi.1002890).

**[INFERENCE] For your narrower question—learning simultaneous analogue nose comparison by adapting the internal weights of a worm-connectome-constrained controller—I did not find a verified matching demonstration. This is a bounded negative search result, not proof that none exists.**

### Is your plateau known?

**[READ] Your own report supports a slightly more precise description than “zero stereo”: all 47 champions fail the positive stereo-use criterion; 43 show no material benefit and four show small benefits.** A weak scripted stereo controller can pass the diagnostic while scoring near the plateau. [WormWars E2d report](https://github.com/juan103/wormwars/blob/df50f6a5433d3079888aa661b88c2e769b139fc7/experiments/E2d-taskn-diagnosis/RESULTS.md).

**[INFERENCE] I found no paper establishing this particular small-difference plateau as a named or universal phenomenon. The literature supplies relevant mechanisms and counterexamples, rather than a diagnosis of your runs.**

**[READ] Two concrete prior failures matter.** Izquierdo & Lockery trained in conical fields partly to avoid exploiting Gaussian relationships between local steepness and source distance; they also prevented a simulator shortcut involving translation without appropriate undulation. These were explicit model-design problems. [2010 paper](https://doi.org/10.1523/JNEUROSCI.2606-10.2010).

**[INFERENCE] In your fixed Gaussian world, exploiting mean concentration is a valid strategy. It becomes a shortcut relative to a broader scientific claim about gradient navigation. Changing field amplitude and width independently is therefore an informative generalization test, not automatically a required correction to your task.**

**[READ] Alonso & Kirkegaard trained spatial, temporal and combined chemotaxis policies under sensory noise.** Their PPO-trained networks shifted between useful spatial and temporal integration as sensor geometry and signal quality changed. Their Eq. 6 preprocesses counts as \(m_i=\log(M_i+1)\). This establishes a successful comparative framework, not the same evolutionary failure. [PNAS Nexus 2024](https://doi.org/10.1093/pnasnexus/pgae235).

**[INFERENCE] The most informative remedies to test are:**

1. **Gain:** add a calibrated residual stereo term to an existing champion and sweep its strength. This measures whether weak stereo contributions help immediately or require crossing a performance valley.
2. **Preprocessing:** compare raw \(L,R\) against explicit mean/difference channels, recording that this supplies the subtraction externally.
3. **Geometry curriculum:** begin with wider sensor separation, then return to the original separation; evaluate only on the original geometry for the final comparison.
4. **Teacher seeding:** fit a controller to the successful scripted policy before free evolution. Success establishes an attainable solution; failed fitting does not prove unattainability.
5. **Noise:** use realistic, separately controlled common and independent noise. Added noise can overwhelm the small difference; amplification after the noise does not improve its signal-to-noise ratio.
6. **Shaping:** reward the intended directional response or component task. Generic proximity shaping may further reward the existing mean-based solution.

### One structural issue already identified in your repository

**[READ] WormWars DECISIONS distinguishes two cases:** exact left/right-equivariant parameters combined with a left/right-even dorsal-minus-ventral readout can force \(u(L,R)=u(R,L)\); a symmetric mask with independently initialized weights does not enforce that equality. [DECISIONS, D050–D051](https://github.com/juan103/wormwars/blob/df50f6a5433d3079888aa661b88c2e769b139fc7/DECISIONS.md).

**[INFERENCE] Preserve that distinction when designing the graft. Symmetry inside a comparator can help cancel common input, but its output must be mapped explicitly to opposite turning commands. Graph symmetry alone does not explain the observed plateau.**

## 3. Minimal stereo-steering circuits

### Braitenberg models: what is already sufficient

**[READ] Rañó derives a leading-order planar model in Eqs. 4–6:**

\[
\dot x=F(S(\mathbf{x}))\cos\theta,\qquad
\dot y=F(S(\mathbf{x}))\sin\theta,
\]

\[
\dot\theta
=\mp\frac{\delta}{d}\nabla F(S(\mathbf{x}))\cdot\mathbf e_p,
\qquad
\mathbf e_p=(-\sin\theta,\cos\theta).
\]

**[READ] Here \(\delta\) is sensor separation and \(d\) is wheel separation; the sign depends on crossed versus uncrossed wiring.** The analysis also shows why qualitative “attraction” is not a guarantee of source capture: field shape and response law affect equilibria and trajectories. [ICRA 2012 paper](https://doi.org/10.1109/ICRA.2012.6224583); [full author PDF](https://pure.ulster.ac.uk/ws/files/11403431/rano11model-final.pdf).

**[INFERENCE] A ring is unnecessary for computing a signed lateral gradient and steering on it. Two sensor–motor pathways, with zero to a few intervening units, suffice algorithmically. That does not prove that a two-to-four-cell graft achieves your required gain through the existing host under every weight bound.**

### A useful evolved bilateral motor map

**[READ] Simões et al. evolved Braitenberg-like vehicles for fly heat avoidance. Their Eqs. 15–16 are:**

\[
v_L=h(s_L)w_{LL}+h(s_R)w_{LR}+v_0+\gamma,
\]
\[
v_R=h(s_L)w_{RL}+h(s_R)w_{RR}+v_0-\gamma.
\]

**[READ] The symmetric model uses ipsilateral weight \(w_I\) and contralateral weight \(w_C\).** The selected model’s Methods values include \(w_I=29.1\,\mathrm{mm/s}\), \(w_C=-22.5\,\mathrm{mm/s}\), \(v_0=5\,\mathrm{mm/s}\); model antenna separation is \(300\,\mu m\). Evolution used NSGA-II through DEAP. This is thermotaxis, not worm chemotaxis; the complete research code was stated as available on request. [Nature Communications 2021](https://doi.org/10.1038/s41467-021-22322-w).

**[INFERENCE] Subtracting the two motor equations cancels the common sensory contribution when the weights are matched. Reuse that cancellation structure; do not import its dimensional gains into WormWars.**

### Insects detect small bilateral differences

**[READ] Gaudry et al. found that walking flies could respond to a 5% asymmetry in total olfactory-receptor input during a 50-ms optogenetic stimulus.** Bilaterally projecting receptor neurons released approximately 40% more transmitter ipsilaterally, producing asymmetric downstream responses. [Nature 2013](https://doi.org/10.1038/nature11747).

**[INFERENCE] This is evidence that small fractional bilateral signals can guide an animal. It supplies neither a universal minimum gain nor evidence that the worm’s paired amphids perform the same computation.**

### Four-unit moth steering—and a grafting failure worth copying

**[READ] Adden et al. use one flip-flop unit and one PBN unit on each side.** PBN inhibits the opposite flip-flop. Their rate model is not just four ordinary neurons: Eq. 3 includes previous activity,

\[
r_t=\frac{1}{1+\exp[-a(J+r_{t-1}+\epsilon)-b]},
\]

and explicit switching rules use thresholds \(r>0.8\), input \(>0.5\), and opposing changes of \(0.5\).

**[READ] Connecting this steering module to Stone’s navigation model produced angular artifacts.** Jointly remapping input \([0.5,1]\) to \([0,1]\) improved success from 0.70 to 0.78 for the rate model and 0.57 to 0.92 for the spiking model; gain or bias changes alone did not suffice. [Paper, Fig. 6](https://doi.org/10.1162/neco_a_01540).

**[INFERENCE] This directly supports calibrating the host–graft interface before interpreting evolutionary retention. It also cautions against describing a procedural toggle as an emergent tanh attractor.**

### A minimal WormWars comparator to test

**[INFERENCE—proposed circuit, not a quoted published model]**

\[
\tau_s\dot x_L=-x_L+a(L-R),\qquad
\tau_s\dot x_R=-x_R+a(R-L),
\]
\[
u=b+b_m\left[\tanh(x_L)-\tanh(x_R)\right].
\]

**[INFERENCE] With matched channels its steady output is**
\[
u=b+2b_m\tanh[a(L-R)],
\]
**so local differential gain is \(2ab_m\), with exact cancellation of common input in this idealized circuit.** This is an appropriate two-unit positive control. Reaching your scripted gain may require input/output scaling or a larger circuit; it is not established merely by writing these equations.

**[INFERENCE] Measure common-mode rejection directly.** Define \(m=(L+R)/2\), \(d=L-R\), and measure \(K_D=\partial u/\partial d\), \(K_C=\partial u/\partial m\). The useful condition is \(|K_Cm|\ll|K_Dd|\) over your actual joint distribution of observations—not a universal gain or decibel target borrowed from insects.

**[INFERENCE] Two additional mechanisms deserve isolated tests:**

- Near-critical recurrence can amplify a signal while slowing it:  
  \(\tau\dot x=-(1-r)x+ad\) has gain \(a/(1-r)\) and effective time constant \(\tau/(1-r)\).
- For two otherwise identical passive cells joined by a symmetric gap conductance, their voltage difference satisfies  
  \(\tau\dot{\Delta v}=-(1+2g)\Delta v+(I_L-I_R)\).  
  Thus electrical coupling can suppress the difference in this simple case; the full chemical network may counteract it.

## 4. Ring attractors as portable rate models

### Noorman et al. 2024: best minimal reference

**[READ] Noorman’s Eq. 1 is**

\[
\tau\dot h_j
=-h_j+\frac1N\sum_k
\left[W^{sym}_{jk}+v_{in}W^{asym}_{jk}\right]\phi(h_k)+c_{ff},
\]

\[
W^{sym}_{jk}=J_I+J_E\cos(\theta_j-\theta_k),\qquad
W^{asym}_{jk}=\sin(\theta_j-\theta_k),\qquad
\phi(x)=\max(0,x).
\]

**[READ] Checked settings:** Methods specify \(\tau=0.1\,s\), \(c_{ff}=1\). Figure 2 uses \(N=6\), with tuned \(J_E\in\{12,4,2.4\}\). \(J_I\) is constructed numerically to enforce a minimum bump amplitude, rather than supplied as one universal constant. [Paper](https://doi.org/10.1038/s41593-024-01766-5).

**[READ] A source-code construction for one setting is**
```matlab
JI = computeJI(4, 0.2, 1, 2*pi*(0:99)/100, 6);
```
**[READ] Use the released [`computeJI.m`](https://github.com/HermundstadLab/DiscreteRingAttractor/blob/main/auxFunctions/computeJI.m) and [`dynSys.m`](https://github.com/HermundstadLab/DiscreteRingAttractor/blob/main/auxFunctions/dynSys.m).** I did not substitute an invented numerical \(J_I\).

**[READ] The study shows that small untuned rings can pin activity to discrete directions and fail to integrate weak velocity inputs.** Precisely tuned networks can support continuous representations with very few units.

**[INFERENCE] A persistent bump is therefore an insufficient acceptance test. Measure drift, velocity gain, dead zones and recovery after cue loss. Replacing ReLU with tanh changes the model and requires revalidation.**

### Goulard et al. 2021: explicit P-EN-style shifting

**[READ] This is the visual-landmark paper, *A unified mechanism for innate and learned visual landmark guidance in the insect central complex*. Its Eq. 2, checked against the equation image, is**

\[
\begin{aligned}
EPG_i(t)&=VU_i(t)+1.0\,PEG_{i|i+8}(t-1)
+2.5\,PEN_{i-1|i+9}(t-1)
-0.2\sum_jEPG_j(t),\\
PEG_{i|i+8}(t)&=1.0\,EPG_i(t-1),\\
PEN_i(t)&=0.75\,EPG_i(t-1)+0.75\,Nod_L(t),\\
PEN_{i+8}(t)&=0.75\,EPG_i(t-1)+0.75\,Nod_R(t).
\end{aligned}
\]

**[READ] The vertical bar is the paper’s notation for bilateral copies; the inhibition sum excludes the current EPG.** The model uses discrete, clipped rate updates and binary nodulus signals. Note the printed same-time inhibition term. [Paper](https://doi.org/10.1371/journal.pcbi.1009383); [Python code](https://github.com/RomanGoulard/ModelCX_code-data).

**[INFERENCE] Reuse its shifted recurrence and maintenance topology. Its panoramic visual input mapping does not solve the problem of estimating a complete direction from two chemical samples. Do not silently turn these discrete updates into a continuous-time equation.**

### Stone et al. 2017: heading plus home-vector memory

**[READ] Stone’s STAR Methods give unnumbered rate equations**

\[
r=\frac{1}{1+e^{-(aI-b)}},\qquad I_j=\sum_iw_{ij}r_i,
\]

and TB1 recurrence

\[
w_{ij}=\frac{\cos(\theta_i-\theta_j)-1}{2},
\]
\[
I_{TB1,j}^{(t)}
=(1-c)r_{CL1,j}^{(t)}
+c\sum_{i=1}^{8}W_{ij}r_{TB1,i}^{(t-1)},\qquad c=0.33.
\]

**[READ] Its unnumbered CPU4 memory update is**

\[
I_{CPU4}^{(t)}
=I_{CPU4}^{(t-1)}
+h\left(r_{TN2}^{(t)}-r_{TB1}^{(t)}-k\right),
\quad h=0.0025,\quad k=0.1.
\]

**[READ] Memory starts at 0.5 and is clipped to \([0,1]\); the model uses eight TB1 and sixteen CPU4 cells.** Heading is supplied by compass inputs; this is not itself the fly P-EN velocity-integrator implementation. [Paper](https://doi.org/10.1016/j.cub.2017.08.052); [code](https://github.com/InsectRobotics/path-integration).

**[INFERENCE] This is useful when E3 needs an actual home vector, but excessive machinery for instantaneous Gaussian stereo steering.**

### Kakaria & de Bivort 2017: a tanh variant, with a code mismatch

**[READ] Besides its spiking model, the paper gives this unnumbered leaky-integrator equation:**

\[
\frac{dV_i}{dt}
=\frac1{C_m}\left[
\frac{V_0-V_i}{R_m}+I_{in}
+I_{max}\sum_{j=1}^{60}M_{ji}\tanh\!\left(20(V_j-V_0)\right)
\right].
\]

**[READ] Paper values include** \(C_m=0.002\,\mu F\), \(R_m=10\,M\Omega\), \(V_0=-52\,mV\), \(dt=10^{-4}\,s\). [Paper](https://doi.org/10.3389/fnbeh.2017.00008).

**[READ] Released [`flyLI.m`](https://lab.debivort.org/protocerebral-bridge-ring-attractor-model/flyLI.m) instead uses** tanh slope 100, \(C_m=2\times10^{-8}F\), \(R_m=10^6\Omega\), and \(I_{max}=2.5\times10^{-10}A\). Both electrical parameter pairs give \(R_mC_m=0.02\,s\), but their individual scalings differ.

**[INFERENCE] Choose a coherent paper or code implementation; combining their defaults is not a faithful reproduction.**

### Angular-velocity shifting: biological evidence

**[READ] Green et al. provide causal evidence for P-EN-mediated heading updates.** Left/right P-EN activity tracks turning; shifted feedback to E-PG supports directional movement of the heading representation. Blocking P-EN transmission impairs tracking in darkness, and stimulation shifts E-PG activity. [Nature 2017](https://doi.org/10.1038/nature22343).

**[INFERENCE] For an egocentric remembered bearing, body rotation and represented direction have opposite signs. Test that coordinate convention independently before evaluating navigation. Near a source, translation changes bearing too; angular-velocity compensation alone is incomplete.**

### Wind anchoring is demonstrated; chemical-bearing anchoring is a different problem

**[READ] Okubo et al. found a WED→LAL→ellipsoid-body pathway that combines the two antennae’s displacements with opposing signs.** Bilateral excitation/inhibition partly cancels wind-intensity changes, and wind direction anchors the E-PG compass representation. [Neuron 2020](https://doi.org/10.1016/j.neuron.2020.06.022).

**[INFERENCE] This is a useful biological common-mode-rejection motif and a genuine bilateral cue anchoring a ring. Mechanical antennal deflection contains directional information that two scalar odour concentrations do not necessarily provide.**

**[INFERENCE] In your Gaussian field, two noses determine a lateral component but do not generally resolve full bearing.** For equal noses separated by \(\delta\), Gaussian width \(\sigma\), and source displacement \(r_\perp\) along the sensor baseline,

\[
\log\frac{L}{R}=\frac{\delta r_\perp}{\sigma^2}.
\]

**[INFERENCE] Forward-versus-backward ambiguity remains without more information. A ring initialized from \(\operatorname{sign}(L-R)\) should not be interpreted as an accurate 360° source-direction estimate. Active sampling, history or another cue must supply the missing information.**

### When does memory help odour navigation?

**[READ] Sun, Yue & Mangan combine chemotaxis, odour-gated anemotaxis, path integration, switches and remembered directions.** Their demonstrations include recovery after displacement and backtracking. Chemotaxis uses temporal concentration changes and an independently available global compass; the proposed fan-shaped-body ring is a modelling hypothesis. [eLife 2021](https://doi.org/10.7554/eLife.73077); [code](https://github.com/XuelongSun/insectNavigationCX).

**[READ] Singh et al. trained recurrent agents using one odour measurement and egocentric wind.** RNN advantages over finite-history feedforward policies were strongest in changing-wind conditions. Much of the learned integration operated over short timescales. This supports memory in intermittent, nonstationary plume tracking, but does not isolate a ring as the necessary mechanism. [Nature Machine Intelligence 2023](https://doi.org/10.1038/s42256-022-00599-w).

**[INFERENCE] The clean E4s memory tests are odour outages, changing wind, displacement and delayed observations. Target relocation also creates a cost for stale memory, so reset or confidence decay belongs in the experiment.**

## 5. Seeding and grafting modules into evolving networks

### What the literature supports

- **[READ] NEAT protects structural innovations, but original NEAT is not a designed-graft experiment.** It starts minimally and adds structure. Its add-node mutation replaces a connection with two connections, assigning upstream weight 1 and downstream the previous weight. [Stanley & Miikkulainen 2002](https://doi.org/10.1162/106365602320169811).  
  **[INFERENCE]** With a sigmoid inserted, that operation is not exactly function-preserving: \(wx\) becomes \(w\sigma(x)\). Seeding a designed controller does not require switching to NEAT.

- **[READ] Working controller seeds can improve neuroevolution.** Koppejan & Whiteson compared helicopter policies initialized from scratch with policies initialized from a robust baseline. Seeded engineered multilayer policies performed best in their comparison; topology search did not outperform the designed architecture. [2011 study](https://doi.org/10.1007/s12065-011-0066-z).  
  **[INFERENCE]** Reuse the seeded-versus-random comparison, not a claim that evolution preserves the seed’s internal mechanism.

- **[READ] Initial interface disturbance matters.** Tomko & Harvey added neurons to evolving tanh networks and compared new weights of zero, small Gaussian values with SD 0.1, and large values in \([-10,10]\). Large additions could undermine the benefit of incremental evolution; zero was not universally best. [Full conference paper](https://users.sussex.ac.uk/~inmanh/do-not-disturb.pdf).  
  **[INFERENCE]** Initialize *additional* host–graft connections at zero or small values while preserving the functioning module and its intended motor connection.

- **[READ] Modular assembly has direct precedents.** NMODE combines separately evolved recurrent controllers through explicit module interfaces. Its demonstrated leg-controller assembly is relevant to E4, but mutations are constrained by module boundaries. [2017 preprint](https://arxiv.org/abs/1701.05121); [code](https://github.com/kzahedi/NMODE).  
  **[INFERENCE]** Such boundaries facilitate assembly but can prevent the cross-module reorganization you want to study.

### Protecting a graft

**[READ] Safe Mutations changes perturbation size according to behavioural-output sensitivity.** Its Eq. 1 is

\[
Divergence(\delta;w)
=\frac1I\sum_i\sum_k
\left[
NN(X_i;w)_k-NN(X_i;w+\delta)_k
\right]^2.
\]

**[READ] SM-R estimates this through output comparisons; SM-G uses derivatives. Recurrent tasks were included in the experiments.** [Lehman et al. 2018](https://doi.org/10.1145/3205455.3205473); [MIT code](https://github.com/uber-research/safemutations).

**[INFERENCE] For WormWars, replay complete input histories with controlled initial neural states. A static sensor-vector archive does not capture CTRNN state dependence. A smaller graft mutation rate is a simpler comparison, but I found no validated “correct” multiplier for your case.**

**[READ] PathNet evolves pathways while training weights by gradients; after one task it freezes the successful pathway for subsequent tasks.** [2017 preprint](https://arxiv.org/abs/1701.08734).

**[INFERENCE] This supports a frozen-graft control. Retention by freezing is protection by construction, which must be distinguished from spontaneous retention under free mutation.**

### Neural prostheses and co-adaptation

**[READ] Bryan, Jiang & Rao connect an artificial recurrent co-processor to a damaged cortical grasping model.** They compare fixed and co-adapting hosts; training uses gradients through an emulator, not a GA. [Published study](https://doi.org/10.1088/1741-2552/accaa9); [full author version](https://arxiv.org/abs/2210.11478); [code](https://github.com/mmattb/coproc-poc).

**[INFERENCE] Reuse their fixed-host versus adapting-host distinction. The study is an augmentation precedent, not evidence that a worm host absorbs a graft’s computation after the graft is removed.**

### Forgetting: an important distinction

**[READ] Ellefsen, Mouret & Clune evolved networks that subsequently learned within their lifetimes using neuromodulated plasticity.** Connection-cost selection promoted modularity and better retention of alternating food associations; excessive cost pressure worsened solutions. [PLoS Computational Biology 2015](https://doi.org/10.1371/journal.pcbi.1004128); [archive](https://doi.org/10.5061/dryad.s38n5).

**[INFERENCE] This supports explicit retention tests and restrained pruning pressure. It is not a direct experiment on successive fixed GA champions erasing a graft. I did not verify a NEAT-only study establishing your precise form of catastrophic forgetting.**

### Distinguishing the possible outcomes of E4s

**[INFERENCE] Run the same functioning seed under frozen, reduced, uniform and sensitivity-controlled graft mutation. Partition host, graft and interface parameters, and measure these outcomes separately:**

| Outcome | Evidence needed |
|---|---|
| **Retention** | [INFERENCE] The graft retains its input–output function and remains causally useful. Parameter similarity alone is insufficient. |
| **Erosion** | [INFERENCE] Its stereo function deteriorates; determine whether performance also falls or another strategy compensates. |
| **Bypass** | [INFERENCE] The graft still works when isolated, but the evolved organism no longer uses it. |
| **Redundancy** | [INFERENCE] Either host or graft can sustain the relevant function after the other is removed. |
| **Transfer into the host** | [INFERENCE] Post-evolution host-only performance and stereo diagnostics improve relative to the original host; removing the graft leaves the transferred computation, not merely a temporal fallback. |

## 6. Modular organisms switched by a latch

### Rate-model memory is already available

**[READ] Hülse & Pasemann analyse a tanh neuron with positive self-feedback.** Their Eq. 2 gives fixed points,

\[
x^*=\theta+w_s\tanh(x^*),
\]

and Eq. 3 gives the saddle-node condition,

\[
w_s\tanh'(x)=1.
\]

**[READ] Their Eq. 4 gives hysteresis width**

\[
\Delta^*=
\left|
\ln\frac{1+\alpha}{1-\alpha}-2w_s\alpha
\right|,
\qquad
\alpha=\sqrt{1-\frac1{w_s}},\quad w_s>1.
\]

**[READ] Their evolved robot controller includes weights exceeding your ±3 bound.** Take the analysis rather than copying those controller values. The published model is discrete-time. [2002 paper](https://doi.org/10.1007/3-540-46084-5_127).

**[INFERENCE—continuous-time candidate, not their published parameter set]** An isolated extra cell compatible with your scalar bounds is

\[
\tau_q\dot q=-q+2\tanh(q)+S-R,\qquad \tau_q=1\text{ tick}.
\]

**[INFERENCE] At zero input it has stable states \(q\approx\pm1.915\).** Sustained unit set/reset inputs can switch it. From the opposite settled state, a unit pulse needs approximately \(3.08\tau_q\) to cross zero; four ticks is a reasonable isolated-cell test pulse. A one-tick pulse is insufficient. Simultaneous equal inputs cancel; initialize away from the unstable state \(q=0\). This remains a proposed component requiring validation in your actual integrator and interface.

### Explicit SR implementations

**[READ] Spaeth et al. construct a three-spiking-neuron SR latch:** two excitatory neurons sustain the active state, and an inhibitory neuron resets it. Four such modules controlled a physical flexible crawling robot. [PLoS ONE 2020](https://doi.org/10.1371/journal.pone.0240267); [supplementary Julia notebook](https://doi.org/10.1371/journal.pone.0240267.s001).

**[INFERENCE] Reuse its topology and persistence/reset tests. Its active state is a spiking limit cycle, so its parameters are not portable CTRNN latch values.**

### Designed versus evolved selectors

**[READ] MM-NEAT compares human-defined task selection with evolved preference neurons.** The highest preference chooses a policy module; hidden computation can be shared. Module duplication initially preserves policy connections, but extra modules can remain unused. [Schrum & Miikkulainen 2016](https://doi.org/10.1162/evco_a_00181).

**[INFERENCE] For E3, compare three selectors: your fixed SR rule, an evolved selector with explicit state, and preference-based arbitration. Keep both navigation modules identical at the start. Log module usage and both proposed motor commands, since a high shuttle score can conceal one unused module or persistent conflict.**

**[INFERENCE] Specify inactive-module semantics before evolving: continue updating, freeze its state, or reset on activation. Also define repeated arrival pulses, simultaneous set/reset, destination-boundary hysteresis and initial mode. Moth flip-flops and RIA “switches” should not be cited as exact implementations of your arrival-triggered A/B memory.**

## 7. Finding minimal circuits by pruning and lesioning

**[READ] Fakhar & Hilgetag analyse a NEAT-evolved Space Invaders controller with 19 neurons and 51 connections.** Single-lesion rankings differ from multi-perturbation Shapley estimates; removing an additional component can rescue a damaging lesion, and a neuron’s importance can differ from the importance of its self-loop. [PLoS Computational Biology 2022](https://doi.org/10.1371/journal.pcbi.1010250); [analysis/data repository](https://github.com/kuffmode/ANNLesionAnalysis).

**[INFERENCE] Consequently, a one-neuron-at-a-time pass is a good search heuristic, but a weak standalone account of circuit function. Use the following protocol:**

1. **Define preserved function.** Require both behavioural performance and the stereo/latch property you care about. Otherwise pruning may preserve score by reverting to the mean-only strategy.
2. **Separate acute lesions from reoptimization.** Report immediate performance, performance after retraining, and the smallest successful circuit found.
3. **Recompute after each deletion.** Importance changes with the remaining circuit. Repeat several deletion orders.
4. **Test interactions selectively.** Screen pairs or small groups around interfaces and apparently dispensable units; use sampled coalitions if feasible.
5. **Use paired held-out episodes.** Include both goals, rare latch transitions, relocation, initial orientations and sensory ranges.
6. **Define the physical lesion.** Removing a neuron and all its edges differs from clamping its voltage while retaining gap junctions. A clamped gap-connected cell can become a current sink.
7. **Retest dynamics.** A pruned ring may still show a bump while losing mobility; a pruned latch may hold state while losing reliable switching.

**[INFERENCE] The appropriate claim is “smallest circuit found under this task distribution, tolerance and lesion/retraining procedure.” A successful controller on one narrow assay is not automatically a minimal biological circuit.**

## 8. Software, licences and maintenance

**[READ] The dates below are observed repository activity, not guarantees of support or successful installation. “No licence found” means I did not identify an explicit code licence in the inspected material; an article’s licence was not automatically assigned to its repository.**

### Worm and chemotaxis software

| Software | Licence and observed activity | What to take |
|---|---|---|
| [Hironaka chemotaxis](https://github.com/118-Oganesson/c_elegans_chemotaxis) | [READ] MIT; activity September 2025. | [INFERENCE] Best small executable worm baseline: simulator, GA, saved genes, configuration and plots. |
| [Matsumoto model/data](https://doi.org/10.6084/m9.figshare.23583705) | [READ] CC BY 4.0; research archive with model and figure code. | [INFERENCE] Empirical phase-response data and compact steering model. |
| [CE_orientation](https://github.com/edizquierdo/CE_orientation) | [READ] No licence found; last push June 2022. Current source differs from the classic paper. | [INFERENCE] Historical CTRNN/chemotaxis implementation and analysis reference. |
| [CENN digital twin](https://github.com/zhongyuchen/digital-twin-c-elegans) | [READ] No explicit licence found; last commit May 2025. | [INFERENCE] MuJoCo body, teacher-data generation and connectome imitation learning. |
| [BAAIWorm](https://github.com/Jessie940611/BAAIWorm) | [READ] Apache-2.0 at root; last push June 2026. Ubuntu/CUDA/OptiX-oriented stack. | [INFERENCE] Morphology, electrophysiology, fitting and body simulation when biological detail is the aim. |
| [ENOMAD](https://github.com/dsb-lab/ENOMAD) and [paper archive](https://doi.org/10.5281/zenodo.17591250) | [READ] Both explicitly MIT; optimizer last push December 2025; archived implementation v2.0. | [INFERENCE] Hybrid global/local optimization and a large-connectome benchmark. |
| [OpenWorm/c302](https://github.com/openworm/c302) | [READ] MIT; last push August 2026. | [INFERENCE] NeuroML generation, named-cell/connectivity handling and simulator cross-checks. It is a modelling framework, not a verified trained chemotaxis policy. |
| [chemoxrl](https://github.com/kirkegaardlab/chemoxrl) | [READ] MIT; last commit October 2023. | [INFERENCE] Spatial/temporal information ablations, noisy sensing, training code and weights. |
| [plumetracknets](https://github.com/BruntonUWBio/plumetracknets) | [READ] MIT; last commit June 2025. | [INFERENCE] Plume environments, recurrent-policy baselines and behavioural analysis. |

### Rings and insect navigation

| Software | Licence and observed activity | What to take |
|---|---|---|
| [DiscreteRingAttractor](https://github.com/HermundstadLab/DiscreteRingAttractor) | [READ] MIT; last push July 2024; archived release available. | [INFERENCE] Minimal ring dynamics, parameter construction and pinning/mobility tests. |
| [Goulard ModelCX](https://github.com/RomanGoulard/ModelCX_code-data) | [READ] No licence found; last push July 2021; Python 3.6/OpenGL-era code. | [INFERENCE] Shifted recurrent topology and visual-heading experiments. |
| [Stone path-integration](https://github.com/InsectRobotics/path-integration) | [READ] No licence found; last push August 2017; historical Python code. | [INFERENCE] `cx_rate.py`, heading/home-vector circuitry and steering comparator. |
| [Adden insect_steering](https://github.com/stanleyheinze/insect_steering) | [READ] No licence found; last push January 2020. Current files include additional states beyond the minimal paper circuit. | [INFERENCE] Graft-interface and steering experiments; reconcile code version with paper before reproduction. |
| [Sun insectNavigationCX](https://github.com/XuelongSun/insectNavigationCX) | [READ] No licence detected; last push March 2024. | [INFERENCE] Combined odour/wind/navigation tasks, switches and memory tests. |
| [Kakaria companion archive](https://lab.debivort.org/protocerebral-bridge-ring-attractor-model/) | [READ] Licence not stated on inspected page; MATLAB 2016a-era material. | [INFERENCE] Connectivity, bump diagnostics and perturbation experiments; resolve paper/code scaling first. |
| [pompy](https://github.com/InsectRobotics/pompy) | [READ] MIT; last push November 2018. | [INFERENCE] Existing plume simulation if you introduce intermittent odour tasks. |

### CTRNN, evolution and analysis libraries

| Software | Licence and observed activity | What to take |
|---|---|---|
| [NEAT-Python](https://github.com/CodeReclaimers/neat-python) | [READ] BSD-3-Clause; last push May 2026. Current README describes v2.1, evolved time constants and CTRNN fixes. | [INFERENCE] CTRNN reference, checkpoints and topology-evolution comparison. Your gap-current semantics still require explicit implementation. |
| [DEAP](https://github.com/DEAP/deap) | [READ] LGPL-3.0; last push April 2026. | [INFERENCE] Custom-genome evolution, multiobjective selection, genealogy and parallel evaluation. |
| [EvoTorch](https://github.com/nnaisense/evotorch) | [READ] Apache-2.0; last push September 2026. | [INFERENCE] Batched tensor evolution and distributed evaluation if simulation throughput warrants a port. |
| [Safe Mutations](https://github.com/uber-research/safemutations) | [READ] MIT; last push April 2018. | [INFERENCE] Research implementation of sensitivity-controlled perturbations. |
| [MM-NEAT](https://github.com/schrum2/MM-NEAT) | [READ] BSD-style core with separately licensed dependencies; last push May 2026. | [INFERENCE] Module duplication, selectors and usage logging. |
| [NMODE](https://github.com/kzahedi/NMODE) | [READ] No licence identified; last push October 2018. | [INFERENCE] Module interfaces and assembly protocol. Its discrete update is not a CTRNN kernel. |
| [ANNLesionAnalysis](https://github.com/kuffmode/ANNLesionAnalysis) | [READ] No licence identified; last push December 2023. | [INFERENCE] Lesion coalitions and contribution analysis. |
| [Neural co-processor](https://github.com/mmattb/coproc-poc) | [READ] No licence identified; last push May 2023. | [INFERENCE] Fixed-host/co-adaptive-host experimental design. |
| [worm-whisperer](https://github.com/kairess/worm-whisperer) | [READ] Code/data use PolyForm Noncommercial 1.0.0; manuscript/docs use CC BY-NC 4.0; activity September 2026. | [INFERENCE] Recent negative-result and interface experiments; not a permissively licensed substitute for your codebase. |

**[INFERENCE] I would keep WormWars’ present simulator and experiment records, import a small number of verified components, and reproduce each component independently before connecting it to the host. Changing simulator, optimizer, sensor representation and architecture together would obscure which intervention escapes the plateau.**

## Open questions

1. **[INFERENCE] Can your existing mask, bounds and readout represent the successful stereo policy?** Teacher fitting and targeted circuit construction can establish existence. Unsuccessful evolutionary search cannot establish impossibility.

2. **[INFERENCE] Where is differential information lost?** Measure gain and common-mode sensitivity successively at sensory cells, candidate interneurons and motor readouts, with state and input history controlled.

3. **[INFERENCE] Is the plateau a selection problem or a circuit problem?** A residual-gain sweep around an existing champion can reveal whether incremental stereo improvements are rewarded before launching another large search.

4. **[INFERENCE] Does a two-to-four-unit graft suffice under the actual host interface?** Test a frozen comparator first, then compare it with a capacity-matched random graft and the ring.

5. **[INFERENCE] What observation anchors a complete odour bearing?** Two concentration samples alone leave ambiguity. Specify what active sampling or additional measurement resolves it.

6. **[INFERENCE] Does memory improve the present task at all?** Compare matched-gain controllers with and without memory across continuous cues, outages and target relocation; measure stale-memory costs as well as benefits.

7. **[INFERENCE] Does evolution preserve a computation, or merely preserve score?** Track stereo diagnostics and causal dependence alongside task performance. Weight drift, retained neurons and high fitness are individually insufficient.

8. **[INFERENCE] Can the host acquire the graft’s function?** Compare host-only performance before and after joint evolution, including left/right swaps and common-mode sweeps, to exclude a temporal fallback.

9. **[INFERENCE] Does E3 need two independent navigation modules?** A shared navigator with a persistent goal/context bit may solve the shuttle task. That is an important baseline for claims about merging organisms.

10. **[INFERENCE] How contingent is the final minimal circuit?** Repeat pruning across seeds, deletion orders and task distributions. Multiple small circuits with the same score may implement different mechanisms.
