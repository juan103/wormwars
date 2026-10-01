# WormWars literature review: stereo steering, connectome-constrained evolution, ring attractors and module grafting

Your non-stereo plateau is most likely caused by how your brains are parameterised and how the sensors are encoded, not only by weak search: a left–right difference of about 0.01 has to be amplified roughly 250-fold to steer well, but your weight cap (|w| ≤ 3) and tanh saturation limit a short sensory-to-motor path to about 3–9×, which matches the measured open-loop stereo gain of about 0.1 [INFERENCE]. The published connectome chemotaxis models that work (Izquierdo & Lockery 2010; Izquierdo & Beer 2013) never used bilateral comparison. They used temporal-derivative ON/OFF sensors and weight ranges of ±15, and their code is public [READ]. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890) [jneurosci](https://www.jneurosci.org/content/30/39/12908)

## TL;DR
- **Fix the interface before building a ring.** Normalise or differentiate the sensor input (use ON/OFF derivative cells, as Izquierdo & Lockery 2010 did, or feed a pre-computed L−R), widen the weight or gain range, and make the parameters mirror-symmetric. A 2–4-neuron crossed-inhibition steerer should then be enough for a single Gaussian source. The ring is probably unnecessary for this task [INFERENCE, supported by the Louis et al. 2008 and Wystrach et al. 2016 findings that bilateral comparison is not required for larval taxis].
- **Reuse now:** the Izquierdo/Beer klinotaxis model and its parameter ranges; the Izquierdo & Beer 2013 connectome-pruning recipe (ASE→SMB, path length 3, ≥2 contacts, leaving AIY/AIZ); the Goulard et al. 2021 Python central-complex model (8-EPG ring, PEN shift gain K = 0.75, PFL3 steering); the Noorman et al. 2024 MIT-licensed MATLAB small-ring code; and the Adden et al. 2022 silkmoth flip-flop steering model for your E3 latch.
- **Novelty:** we found no prior work that grafts a designed stereo or ring module onto the full 302-neuron connectome and then lets evolution act on the whole brain. E4s is novel. The fly literature does, however, predict that small hand-tuned rings are fragile to parameter noise (Noorman et al. 2024), so expect Gaussian mutation to erode the ring unless you protect it [INFERENCE].

## Reuse now (ranked by development time saved)

1. **Izquierdo & Lockery 2010 and Izquierdo & Beer 2013 klinotaxis models.** J Neurosci 30:12908, https://doi.org/10.1523/JNEUROSCI.2606-10.2010; PLoS Comput Biol 9:e1002890, https://doi.org/10.1371/journal.pcbi.1002890.
   - *What to take:*
     - the sensor encoding: ON and OFF cells that report "an approximation of the time derivative of salt concentration" [READ]; [jneurosci](https://www.jneurosci.org/content/30/39/12908)
     - symmetric dorsal/ventral parameters [READ]; [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890) [jneurosci](https://www.jneurosci.org/content/30/39/12908)
     - the evolution settings: 60 individuals, 300 generations, 100 runs, parameters encoded in [−1, 1] and mapped linearly to τ ∈ [1, 3], biases and weights ∈ [−15, 15], gap conductance g ∈ [0, 15], with an oscillator period T = 4.2 s [READ, Methods; the equations are rendered as images and the symbol mapping was not verified character by character]; [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890) [elifesciences](https://elifesciences.org/articles/104456)
     - the task set-up: start 4.5 cm from the peak, 500 s assays, fitness = mean chemotaxis index over 50 assays, trained on conical gradients and tested on Gaussian ones [READ]. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890) [elifesciences](https://elifesciences.org/articles/104456)
   - *Saves:* redesigning the sensor front-end and the parameter ranges, and gives you a benchmark to compare against.
   - *Code:* github.com/edizquierdo (klinotaxis-information-flow, RoyalSociety2018, CE_locomotion). [github](https://github.com/edizquierdo) The C++ repositories CE_locomotion and RoyalSociety2018 have **no LICENSE file**, so ask the author before reusing them [SECONDARY, repository listing]. [github +3](https://github.com/edizquierdo/CE_locomotion)
2. **The Izquierdo & Beer 2013 connectome-pruning recipe** (ideal for E4 minimal circuits) [READ]. [elifesciences](https://elifesciences.org/articles/104456)
   - Mine all paths from the chemosensory set to the neck-motor set (RIV, RIM, RMG, RMF, RMH, RMD, RME, SMB, SMD, URA). [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
   - Keep only the paths that are "fully connected" (every sensor can reach every motor), at the minimum path length that allows this. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
   - Restricting to ASE→SMB at path length 3 leaves "23 (7.61%) neurons and 276 (3.78%) chemical synapses and gap junctions". [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
   - Adding a contact threshold of ≥2 leaves only the interneurons AIY and AIZ. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
   - Izquierdo's site also lists a "Minimal *C. elegans* connectome circuit search [Mathematica]" tool [SECONDARY]. [github](https://edizquierdo.github.io/)
3. **Goulard et al. 2021, central-complex steering model**, PLoS Comput Biol 17:e1009383, https://doi.org/10.1371/journal.pcbi.1009383; code at github.com/RomanGoulard/ModelCX_code-data (licence not checked) [READ, sections 2.1–2.6]. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009383)
   - Python 3.6, simple rate units that are linear and clipped to [0, 1] or [−1, 0]. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009383)
   - 8 EPGs with global inhibition standing in for Δ7 ("direct inhibition from each EPG to all the other EPGs"), EPG–PEG recurrence for persistence, and 16 PENs. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009383)
   - Angular velocity enters as a binary signal "modulated by a fixed gain (K = 0.75)" to PEN1–8 or PEN9–16 (eq. 2). [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009383)
   - Two PFL3 sets with connectome-derived weights normalised to [0, 1] (eq. 3). Steering = left–right PFL3 difference plus Gaussian noise σ = 10°, clipped to [−2.5, 2.5]° per step (eq. 4). The agent moves at 0.25 length units per step. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009383)
   - Equations 2–4 are published as images and we could not transcribe their exact symbols, so take them from the PDF or the code.
4. **Noorman et al. 2024, small ring attractors**, Nat Neurosci 27:2207–2217, https://doi.org/10.1038/s41593-024-01766-5; code HermundstadLab/DiscreteRingAttractor v1.0, https://doi.org/10.5281/zenodo.12789923 (MATLAB, MIT, v1.0 dated July 2024) [READ, introduction; code licence SECONDARY]. [github +2](https://github.com/HermundstadLab)
   - The key result is analytic: "even very small networks can be tuned to maintain continuous internal representations, but this comes at the cost of sensitivity to noise and variations in tuning" [ABSTRACT]. [nature](https://www.nature.com/articles/s41593-024-01766-5)
5. **Adden, Stewart, Webb & Heinze 2022, flip-flop steering**, Neural Comput 34(11):2205–2231, https://doi.org/10.1162/neco_a_01540; code github.com/stanleyheinze/insect_steering (Nengo; licence not checked) [ABSTRACT]. [ed](https://www.research.ed.ac.uk/en/publications/a-neural-model-for-insect-steering-applied-to-olfaction-and-path-/) [researchgate](https://www.researchgate.net/publication/343896200_A_neural_model_for_insect_steering_applied_to_olfaction_and_path_integration)
   - An inhibitory local interneuron plus a bistable descending "flip-flop" neuron, each driven by the ipsilateral sensor, steers towards a pheromone plume source. [biorxiv](https://www.biorxiv.org/content/10.1101/2020.08.25.266247v1) [doi](https://dx.doi.org/10.1162/neco_a_01540)
   - It also steers correctly when driven by the Stone et al. 2017 path-integration output. [nih](https://pmc.ncbi.nlm.nih.gov/articles/PMC7613704/) [doi](https://dx.doi.org/10.1162/neco_a_01540)
   - This is a ready-made set-reset steering primitive for E3.
6. **Wystrach, Lagogiannis & Webb 2016**, eLife 5:e15504, https://doi.org/10.7554/eLife.15504; MATLAB and Mathematica code on ModelDB, accession 206356 [ABSTRACT]. [yale](https://senselab.med.yale.edu/ModelDB/ShowModel.cshtml?model=206356) [elifesciences](https://elifesciences.org/articles/15504)
   - Taxis from "direct sensory modulation of continuous lateral oscillations", needing no action selection and no bilateral comparison. [elifesciences](https://elifesciences.org/articles/15504)
   - A cheap klinotaxis alternative that fits your SMD/RMD head-sweep motors.
7. **Neuroevolution libraries** [SECONDARY, repository metadata]:
   - pycma (BSD-3-Clause, release r4.4.3 in February 2026); [github](https://github.com/conda-forge/cma-feedstock) [zenodo](https://zenodo.org/records/18763699)
   - evosax (Apache-2.0, JAX); [github](https://github.com/RobertTLange/evosax)
   - EvoTorch (Apache-2.0, updated May 2026); [github](https://github.com/nnaisense)
   - neat-python (BSD-3-Clause, v2.0.1). [github](https://github.com/CodeReclaimers/neat-python/releases) [github](https://github.com/RobertNiklasBock/neat-python-fast)
   - Moving from truncation-selection GA to CMA-ES costs about an afternoon, and CMA-ES adapts per-parameter step sizes, which matters when a few gains must grow by orders of magnitude [INFERENCE].

## Our plan versus prior work

We read the public README: it states "Weys get separate left and right food readings, so foraging can be solved by comparing the two sides. A real worm cannot do that: *C. elegans* chemotaxis samples concentration over time while moving." [github](https://github.com/juan103/wormwars) The README also records that Experiment 01 ran with the chemical synapses reversed and was rerun as 01b. [github](https://github.com/juan103/wormwars) We could not retrieve ROADMAP.md, DECISIONS.md or docs/E4s/DESIGN.md (fetch errors), so the design details below come from your brief.

| Plan element | Status | Prior work / verdict |
|---|---|---|
| Evolving a CTRNN on the full 302-neuron connectome for chemotaxis | Partly done | Izquierdo & Beer 2013 evolved a pruned connectome subcircuit (ASE, AIY, AIZ, SMB); BAAIWorm (Zhao et al. 2024) is a biophysical closed-loop model with zig-zag chemotaxis. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890) [nature](https://www.nature.com/articles/s43588-024-00738-w) We found no full-302 evolved rate model for chemotaxis [INFERENCE from the search] |
| Stereo (L−R) steering on the worm connectome | Biologically implausible, no precedent found | The amphids are "only 8 μm apart" (Pierce-Shimomura et al. 1999, citing Ward et al. 1975) [SECONDARY]; WormBook states the worm "does not sense a spatial gradient over its body to decide which way to turn" [SECONDARY] | [nih](https://www.ncbi.nlm.nih.gov/books/NBK19746/) [jneurosci](https://www.jneurosci.org/content/19/21/9557)
| Plateau at mean-only behaviour | Known class of failure | The bootstrap problem and deception in evolutionary robotics (Mouret & Doncieux 2009) [SECONDARY]; our scaling argument suggests a gain ceiling in your case [INFERENCE] | [archive](https://scholar.archive.org/search?q=Overcoming+the+bootstrap+problem+in+evolutionary+robotics+using+behavioral+diversity.)
| Hand-built stereo module (2 noses + readout) | Done many times outside worms | Braitenberg-style vehicles; Beer & Gallagher 1992 evolved CTRNN chemotaxis controllers [ABSTRACT]; Gaudry et al. 2013 describe the fly mechanism [ABSTRACT] | [sagepub](https://journals.sagepub.com/doi/10.1177/105971239200100105) [nature](https://www.nature.com/articles/nature11747)
| Ring attractor anchored by a bilateral odour signal | Wind version done in the fly; odour-anchored ring not found | Okubo et al. 2020: the fly compass is tied to wind direction, which is computed from both antennae [ABSTRACT/SECONDARY] | [sciencedirect](https://www.sciencedirect.com/science/article/pii/S0896627320304761) [researchgate](https://www.researchgate.net/profile/Tatsuo-Okubo)
| Grafting the module into the connectome, then evolving the whole | Novel as far as we found | The closest analogue is advice splicing in NEAT (Yong et al. 2006), where "advice eventually becomes incorporated into the network" [ABSTRACT] | [aaai](https://cdn.aaai.org/ojs/18753/18753-52-22424-1-10-20210929.pdf)
| E3: two navigation modules + set-reset latch | Components exist | Flip-flop steering (Adden et al. 2022); evolved action switching (Agmon & Beer 2014, Adaptive Behavior 22(1)) [SECONDARY] | [acm](https://dl.acm.org/doi/abs/10.1177/1059712313511649) [biorxiv](https://www.biorxiv.org/content/10.1101/2020.08.25.266247v1)
| E4: gluing and pruning to a minimal circuit | Pruning method exists | Izquierdo & Beer 2013 path-length and contact-number pruning [READ]; [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890) lesion-attribution methods (Keinan et al. 2004 and others) not verified here |

## 1. Evolved or trained controllers on the *C. elegans* connectome for chemotaxis

- **Izquierdo & Lockery 2010**, J Neurosci, https://doi.org/10.1523/JNEUROSCI.2606-10.2010 [READ, abstract and methods up to the architecture section]. [jneurosci](https://www.jneurosci.org/content/30/39/12908)
  - The model has an ON–OFF chemosensory pair, dorsal and ventral neck motor neurons with self-connections, muscles, and a sinusoidal oscillator. Weights, biases and time constants are symmetric across the dorsoventral midline. [jneurosci](https://www.jneurosci.org/content/30/39/12908)
  - A GA found that this minimal network "is sufficient to generate realistic klinotaxis behavior". A dynamical-systems analysis of 77 evolved networks revealed a state-dependent mechanism. [jneurosci](https://www.jneurosci.org/content/30/39/12908) [jneurosci](https://www.jneurosci.org/content/30/39/12908)
  - Evolution used conical gradients, and the sensor averaging windows N and M were "constrained to be <4.2 s". [jneurosci](https://www.jneurosci.org/content/30/39/12908)
- **Izquierdo & Beer 2013**, PLoS Comput Biol, https://doi.org/10.1371/journal.pcbi.1002890 [READ].
  - Circuit: ASE → AIY/AIZ → SMB, obtained by pruning the connectome. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890) [elifesciences](https://elifesciences.org/articles/104456)
  - Of 100 GA runs, "17 failed to produce networks capable of efficient chemotaxis (chemotaxis index lower than 0.5)", and 27 networks reached CI ≥ 0.75, averaging 0.87 in longer assays. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
  - Networks evolved on conical gradients generalised to Gaussian gradients (Table 1). [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
  - The fitness function "does not specifically reward klinotaxis", yet klinotaxis emerged: turning bias grew linearly with the gradient component normal to the direction of travel. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
  - The paper is inconsistent about symmetry. The Results say the interneurons are not constrained to be left/right symmetric, while the Figure 2 caption says all parameters were symmetric across the dorso-ventral midline [READ]. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
  - *Lesson for you:* a GA with a population of 60 worked because the sensory encoding made the relevant signal (dC/dt) large and the ranges allowed large gains.
- **Izquierdo, Williams & Beer 2015**, PLoS ONE 10:e0140397, https://doi.org/10.1371/journal.pone.0140397 — an information-flow analysis of the same ensemble [ABSTRACT]. [plos](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0140397) Code: edizquierdo/klinotaxis-information-flow (C++; licence not checked). [github](https://github.com/edizquierdo)
- **Olivares, Izquierdo & Beer 2021**, Front Comput Neurosci 15:572339, https://doi.org/10.3389/fncom.2021.572339 — evolved neuromechanical forward locomotion, implemented in C++ [ABSTRACT]. [frontiersin](https://www.frontiersin.org/journals/computational-neuroscience/articles/10.3389/fncom.2021.572339/xml) The code is at github.com/edizquierdo/MultipleNetworkOscillator according to the bioRxiv version [SECONDARY]. [biorxiv](https://www.biorxiv.org/content/10.1101/710566v2) [biorxiv](https://www.biorxiv.org/content/10.1101/710566v3.full) Izquierdo & Beer 2018 (Phil Trans R Soc B 373:20170374) state that their model was "solved by Euler integration with a 1 ms step", with code at github.com/edizquierdo/RoyalSociety2018 [SECONDARY]. [github](https://github.com/edizquierdo/RoyalSociety2018) [royalsocietypublishing](https://royalsocietypublishing.org/rstb/article/373/1758/20170374/42157/From-head-to-tail-a-neuromechanical-model-of)
- **BAAIWorm, Zhao et al. 2024**, Nat Comput Sci 4:978–990, https://doi.org/10.1038/s43588-024-00738-w (open access, CC BY-NC-ND article) [ABSTRACT]. [nature](https://www.nature.com/articles/s43588-024-00738-w)
  - It couples a biophysically detailed neural network to a 3D body; "Through the closed-loop interaction between the two submodels, BAAIWorm reproduced the realistic zigzag movement toward attractors." [nature](https://www.nature.com/articles/s43588-024-00738-w)
  - The paper states: "In our current model, we modeled 136 neurons rather than all 302 neurons, and the only behavior considered was zigzag locomotion". The State of Brain Emulation Report 2025 (arXiv 2510.15745, preprint) adds that these are "multicompartmental models with sub-2μm compartments, incorporating 14 types of ion channels", and lists "expanding to the complete 300-neuron network" as a remaining challenge [SECONDARY]. So BAAIWorm is not a full-302 model.
  - Code: github.com/Jessie940611/BAAIWorm, Apache-2.0 according to its README [SECONDARY]. [github](https://github.com/Jessie940611/BAAIWorm) [github](https://github.com/openworm/MetaWorm) It is a heavy biophysical model and a poor fit for GA inner loops [INFERENCE].
- **Other connectome klinotaxis models:**
  - Chen, Feng, Su, Su & Wang 2022, Sci Rep 12, "Neural model generating klinotaxis behavior accompanied by a random walk based on C. elegans connectome", https://doi.org/10.1038/s41598-022-06988-w [ABSTRACT]. They incorporate "the all-or-none depolarization characteristic of ASEL neuron" and report that when the network is evolved, "klinotaxis emerged spontaneously". Their evolved models fell into "Motif 2" of Izquierdo & Lockery's two motifs [SECONDARY].
  - Hironaka & Sumi 2025, eLife 14:RP104456 (https://elifesciences.org/articles/104456), a model of salt-concentration-memory chemotaxis, uses the Izquierdo & Beer 2013 connectome constraints and parameters: start distance 4.5 cm, speed 0.022 cm/s, oscillator period 4.2 s, time step 0.1 s [SECONDARY].
  - arXiv 2504.18073 (preprint) integrates connectomics, dynamics and biomechanics [ABSTRACT]. [arxiv](https://arxiv.org/pdf/2504.18073)
- **OpenWorm c302**: Python, MIT [SECONDARY]. [github](https://github.com/openworm/c302) Chemotaxis tasks were not verified.

## 2. Stereo (tropotaxis) versus temporal (klinotaxis) steering

- **Can *C. elegans* compare its two sides?** Probably not for chemotaxis.
  - Pierce-Shimomura, Morse & Lockery 1999 (J Neurosci 19:9557, https://doi.org/10.1523/JNEUROSCI.19-21-09557.1999) write that orienting on the concentration difference between the amphids "is unlikely because the amphids are only 8 μm apart (Ward et al., 1975)". They also note that the phasmids are not needed for chemotaxis (Ward 1973) [SECONDARY; we did not open Ward et al. 1975]. [jneurosci](https://www.jneurosci.org/content/19/21/9557)
  - WormBook (Bargmann, "Chemosensation in *C. elegans*", https://www.ncbi.nlm.nih.gov/books/NBK19746/) says turn direction during pirouettes is random, "indicating that *C. elegans* does not sense a spatial gradient over its body" [SECONDARY]. [nih](https://www.ncbi.nlm.nih.gov/books/NBK19746/)
  - Single study caveat: the 8 μm figure is quoted secondhand.
- **Circuits for klinotaxis and weathervaning.**
  - ASE is functionally asymmetric: "the left neuron is an on-cell, whereas the right neuron is an off-cell" (Thiele, Faumont & Lockery 2009, J Neurosci 29:11904) [ABSTRACT]. [jneurosci](https://www.jneurosci.org/content/29/38/11904)
  - AIZ (Iino & Yoshida 2009) and AIY (Kocabas et al. 2012) are implicated in klinotaxis [SECONDARY, via Izquierdo & Beer 2013]. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
  - SMB sets the amplitude of head sweeps (Gray et al. 2005) [SECONDARY]. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
  - Kocabas et al. 2012 (Nature, https://doi.org/10.1038/nature11431) showed that "a single pair of interneurons is technically sufficient" to drive worms up virtual optical gradients [ABSTRACT]. [nature](https://www.nature.com/articles/nature11431)
  - We did not verify the RIA/SMD weathervaning papers (Liu 2018, Ouellette 2018, Matsumoto 2024), which remain leads.
  - **Design implication:** your mapping (left scent → ASEL, right scent → ASER) mixes body side with ON/OFF polarity. Evolution may be receiving a signal that the connectome's ASE wiring expects to be temporal and ON/OFF rather than spatial [INFERENCE].
- **Has any connectome-constrained model evolved bilateral steering?** We found none. All the connectome klinotaxis models above use single-point temporal sampling [INFERENCE from the literature searched].
- **Is the plateau known?** The general phenomenon is: evolution settles on a local optimum that uses the easy signal (mean concentration, a kinesis-like behaviour) and cannot bootstrap the weak one. This is the "bootstrap problem" and "deception" (Mouret & Doncieux 2009, IEEE CEC, pp. 1161–1168) [SECONDARY]. [archive](https://scholar.archive.org/search?q=Overcoming+the+bootstrap+problem+in+evolutionary+robotics+using+behavioral+diversity.) We found no paper that reports specifically ignoring a small bilateral difference.
  - **Why it happens in your case** [INFERENCE]:
    - The L−R difference is 0.004–0.017 while the common level is 0.02–0.35, so the common-mode signal is 10–50 times larger.
    - The scripted steerer needs k ≈ 256.
    - With |w| ≤ 3 per synapse and tanh slope ≤ 1, a 1–2-synapse path gives at most a gain of 3–9 before saturation. Your measured gain of 0.1 is at the scale this ceiling predicts, and any high-gain path would saturate on the common mode first.
  - **Known remedies:**
    - Mouret & Doncieux group them as staged evolution, environmental complexification, fitness shaping and behavioural decomposition [SECONDARY, via a PPSN 2012 paper]. [polytechnique](http://www.cmap.polytechnique.fr/~nikolaus.hansen/proceedings/2012/PPSN/papers/7492/74920052.pdf)
    - Behavioural-diversity and novelty objectives are another option [SECONDARY]. [loria](https://members.loria.fr/jbmouret/evolution.html)
    - Evolving under the biological constraints worked for Izquierdo & Beer: derivative sensors, symmetric parameters and ±15 ranges [READ]. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
  - **Concrete fixes to test** [INFERENCE]:
    1. Encode the sensors as log-concentration or divisively normalised values, (L−R)/(L+R).
    2. Add an evolvable input gain, or raise |w| to about 15.
    3. Enforce left/right mirror symmetry, so a crossed pathway only has to evolve once.
    4. Shape the curriculum: start with steep gradients and wide sensor spacing, then anneal.
    5. Seed with the scripted steerer.

## 3. Minimal stereo-steering circuits

- **Evolved CTRNN chemotaxis:** Beer & Gallagher 1992, Adaptive Behavior 1(1):91–122, https://doi.org/10.1177/105971239200100105. They evolved "a chemotaxis controller that switches between different strategies depending on environmental conditions" [ABSTRACT]. [sagepub](https://journals.sagepub.com/doi/10.1177/105971239200100105) The later small-CTRNN theory is Beer 1995, "On the dynamics of small continuous-time recurrent neural networks", Adaptive Behavior 3(4):469–509 [SECONDARY]. [google](https://scholar.google.com/citations?user=F_J8QyAAAAAJ&hl=en)
- **Fly lateralisation:** Gaudry et al. 2013, Nature 493:424–428, https://doi.org/10.1038/nature11747. Each olfactory receptor neuron spike releases "approximately 40% more neurotransmitter" onto ipsilateral than onto contralateral projection neurons, so the asymmetry in odour input is amplified at the first synapse [ABSTRACT]. [harvard](https://wilson.hms.harvard.edu/sites/g/files/omnuum8421/files/wilson-lab/files/gaudrywilson2013.pdf) [repec](https://ideas.repec.org/a/nat/nature/v493y2013i7432d10.1038_nature11747.html) *Lesson:* biology adds lateral gain at the first synapse rather than downstream [INFERENCE].
- **Larvae:**
  - Louis et al. 2008 (Nat Neurosci 11:187–199, https://doi.org/10.1038/nn2031) found that bilateral input "improves chemotaxis, it is not required" [SECONDARY, via Davies, Louis & Webb 2015, PLoS Comput Biol, https://doi.org/10.1371/journal.pcbi.1004606]. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1004606) A commentary adds that dual inputs mainly improve signal-to-noise (PMID 18394176) [ABSTRACT]. [nih](https://pubmed.ncbi.nlm.nih.gov/18394176/)
  - Gomez-Marin, Stephens & Louis 2011 (Nat Commun, https://doi.org/10.1038/ncomms1455): stereo-olfaction "is not required for larvae to control the onset of turning", but bilateral input improves turning [SECONDARY]. [nature](https://www.nature.com/articles/ncomms1455)
  - Wystrach et al. 2016: taxis without bilateral comparison [ABSTRACT]. [elifesciences](https://elifesciences.org/articles/15504)
- **Silkmoth flip-flop:** the Adden et al. 2022 model (see Reuse now) [ABSTRACT]. [biorxiv](https://www.biorxiv.org/content/10.1101/2020.08.25.266247v1) The original physiology papers (Kanzaki, Mishima, Iwano, Olberg 1983) were not verified here.
- **Braitenberg analyses** (Rañó and others), **cricket phonotaxis** (Webb & Scutt 2000) and **mammalian stereo olfaction** (Rajan et al. 2006; Catania 2013) were not verified in this pass. Treat them as leads.
- **Does a 2–4-neuron circuit suffice?** Yes, very likely, for a single smooth Gaussian source: two sensory units with crossed inhibition (common-mode rejection) feeding two turning units is a Braitenberg vehicle-3 arrangement [INFERENCE]. Your scripted k·(L−R) steerer already shows the task needs no memory. The ring adds nothing unless the scent is intermittent or occluded.

## 4. Ring attractors as portable rate models

- **Goulard et al. 2021** [READ]: parameters as in Reuse now.
  - The EB model follows Pisokas, Heinze & Webb 2020 (eLife 9:e53985) [SECONDARY]: "Four neuron types interact to create a ring attractor, three forming the excitatory part of the circuit, EPGs, PEGs and PENs, and one contributing inhibition, Delta7." [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009383)
  - The weights "have been set to optimize the tracking of the heading even in darkness". [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009383) The numerical weight values are in the equations and the code, not the text.
  - Steering uses a PFL3 left–right difference (eq. 4). Shifting the EPG→PFL3 weight profile by one or two columns produces menotaxis at an offset (Fig 5C). [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009383) This is directly usable as your L/R readout onto SMD/RMD.
- **Stone et al. 2017**, Curr Biol 27:3069–3085, https://doi.org/10.1016/j.cub.2017.08.052 [SECONDARY/ABSTRACT]. [researchgate](https://www.researchgate.net/publication/320254232_An_Anatomically_Constrained_Model_for_Path_Integration_in_the_Bee_Brain) [cell](https://www.cell.com/current-biology/fulltext/S0960-9822%2817%2931090-4) It uses "a simple firing rate model" with sigmoid parameters a and b "control[ling] the slope and offset"; "All connection weight matrices and other model parameters can be seen in Figure S5." [researchgate](https://www.researchgate.net/publication/320254232_An_Anatomically_Constrained_Model_for_Path_Integration_in_the_Bee_Brain) The code (InsectRobotics/path-integration, Python/Jupyter) showed no LICENSE file in our check, which was unconfirmed [SECONDARY]. [github](https://github.com/InsectRobotics/path-integration)
- **Noorman et al. 2024** [READ, introduction]: small rings can be continuous, but only if finely tuned. There are two side rings for clockwise and anticlockwise shifts driven by angular velocity (Fig 1a). [nature](https://www.nature.com/articles/s41593-024-01766-5)
- **Kakaria & de Bivort 2017**, Front Behav Neurosci 11:8, https://doi.org/10.3389/fnbeh.2017.00008 [ABSTRACT]: ring dynamics "emerged under a wide variety of parameter configurations, even including non-spiking leaky-integrator implementations", which suggests robustness comes from topology rather than fine detail. [frontiersin](https://www.frontiersin.org/articles/10.3389/fnbeh.2017.00008/text) This is in tension with Noorman's point about fine tuning. The two claims concern different things, discrete bump stability versus continuity, so both can hold.
- **P-EN shifters:** in Goulard, a binary angular-velocity input × K = 0.75 goes to one half of the PENs [READ]. Noorman describes "shift neurons … jointly tuned to orientation and angular velocity" [READ]. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009383) [nature](https://www.nature.com/articles/s41593-024-01766-5)
- **Bilateral-cue anchoring:** Okubo et al. 2020, Neuron 107:924–940, https://doi.org/10.1016/j.neuron.2020.06.022. "Shifting the wind rightward rotates the compass as if the fly were turning leftward", and "wind direction can only be deduced by combining information from both antennae" [ABSTRACT/SECONDARY]. [sciencedirect](https://www.sciencedirect.com/science/article/pii/S0896627320304761) [researchgate](https://www.researchgate.net/profile/Tatsuo-Okubo) Basnak et al. 2025 (Nat Neurosci 28:1729–1740) extend this to multimodal cue learning [SECONDARY]. [annualreviews](https://www.annualreviews.org/content/journals/10.1146/annurev-neuro-112723-062711)
- **Heading-to-steering:** "Transforming a head direction signal into a goal-oriented steering command", Nature 2024, https://doi.org/10.1038/s41586-024-07039-2. [nature](https://www.nature.com/articles/s41586-024-07039-2) Crossref lists the authors as Westeinde, Kellogg, Dawson, Lu, Hamburg, Midler et al. (Nature 626:819–826, 2024), not Mussells Pires as in your lead list; the abstract states "PFL3R cells are recruited when the fly is oriented to the left of its goal, and their activity drives rightward turning; the reverse is true for PFL3L" [ABSTRACT].
- **Does egocentric odour-direction memory help?** It helps in intermittent plumes and after losing the cue, not in smooth gradients. Goulard's CX memory supports persistence "when the visual cues disappear" [READ]. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009383) Infotaxis and RNN plume agents (Vergassola 2007; Singh 2023) were not verified here. For your continuous Gaussian task we expect little benefit [INFERENCE].

## 5. Seeding or grafting designed modules

- **NEAT advice:** Yong, Stanley, Miikkulainen & Karpov 2006, AIIDE, https://ojs.aaai.org/index.php/AIIDE/article/view/18753 [ABSTRACT]. Advice is converted into network structure and spliced into NERO agents, which "makes learning faster even when the tasks change and novel ways of making use of the advice are required". [researchgate](https://www.researchgate.net/publication/221309216_Grammar-Guided_Neural_Architecture_Evolution) The PDF notes that when the task conflicts with the advice, the advice is gradually reshaped and "eventually becomes incorporated into the network" [ABSTRACT]. [aaai](https://cdn.aaai.org/ojs/18753/18753-52-22424-1-10-20210929.pdf) So a seeded module that is useful tends to be kept but modified, and one that conflicts with the task is rewritten.
- **Incremental evolution and bootstrapping:** Mouret & Doncieux 2008 and 2009 [SECONDARY]. [scholarpedia](http://www.scholarpedia.org/article/Evolutionary_Robotics)
- **Not verified this pass:** module duplication, modularity through connection cost (Clune et al. 2013), catastrophic forgetting (Ellefsen et al. 2015), and progressive networks and PathNet. Treat them as leads.
- **Our prediction for E4s** [INFERENCE]:
  - Under uniform Gaussian mutation, a finely tuned ring will drift (Noorman's sensitivity result).
  - A simple crossed-inhibition stereo module is likely to be kept if it raises fitness right away.
  - Freezing the module, or giving it a lower mutation σ, is the cheapest control. Run "frozen", "free" and "free with scaled σ" arms.

## 6. Modular organisms with latches or flip-flops

- **Designed latch:** the Adden et al. 2022 flip-flop descending neuron [ABSTRACT]. [biorxiv](https://www.biorxiv.org/content/10.1101/2020.08.25.266247v1)
- **Evolved bistability and sequencing:**
  - Yamauchi & Beer 1994, Adaptive Behavior 2:219–246, https://doi.org/10.1177/105971239400200301 [SECONDARY]; [wiley](https://onlinelibrary.wiley.com/doi/10.1111/tops.12686)
  - Agmon & Beer 2014, "The evolution and analysis of action switching in embodied agents", Adaptive Behavior 22(1). It shows transient sensorimotor modes "in which a subset of the available sensors and effectors become engaged while others are ignored" [ABSTRACT]. [acm](https://dl.acm.org/doi/abs/10.1177/1059712313511649) This is a warning that evolved switches may not be clean latches.
- **Not verified:** Brooks, Maes, Gurney/Prescott basal-ganglia selection, and the *C. elegans* persistent-state papers (Flavell 2013; Gordus 2015).

## 7. Finding minimal circuits by pruning or lesioning

- **Structural pruning before evolution:** Izquierdo & Beer 2013 [READ], see Reuse now.
  - *Pitfall:* the contact threshold is an assumption ("better-connected paths are more likely to have stronger interactions"). [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
  - The authors note that the real circuit lies between the minimal and maximal networks. [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1002890)
- **Functional lesioning after evolution:** the multi-perturbation Shapley value (Keinan et al. 2004) and related methods were not verified here.
  - *Pitfall* [INFERENCE]: removing neurons one at a time, in a fixed order, misses redundancy and compensation.
  - Instead, re-evolve briefly after each cut, and test pairs of lesions.

## 8. Software

| Tool | Licence | Maintenance | Use |
|---|---|---|---|
| edizquierdo/CE_locomotion, RoyalSociety2018 | **No LICENSE file** | 9 and 2 commits, no releases | C++ CTRNN and evolution reference [github](https://github.com/edizquierdo/CE_locomotion) [github](https://github.com/edizquierdo/RoyalSociety2018) | [github](https://github.com/edizquierdo/CE_locomotion)
| Jessie940611/BAAIWorm | Apache-2.0 (per README) | Paper Dec 2024; forked to openworm | Biophysical baseline [github](https://github.com/Jessie940611/BAAIWorm) [github](https://github.com/openworm/MetaWorm) |
| openworm/c302 | MIT | Active organisation | NeuroML connectome [github](https://github.com/openworm/c302) |
| RomanGoulard/ModelCX_code-data | Not checked | Code accompanying the 2021 paper | Ring + PFL3 steering (Python) | [plos](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009383)
| HermundstadLab/DiscreteRingAttractor | MIT | v1.0, July 2024 | Small-ring theory (MATLAB) [github](https://github.com/HermundstadLab) [zenodo](https://zenodo.org/records/12789923) | [nature](https://www.nature.com/articles/s41593-024-01766-5)
| stanleyheinze/insect_steering | Not checked | 2020–2022 | Flip-flop steering (Nengo) | [researchgate](https://www.researchgate.net/publication/343896200_A_neural_model_for_insect_steering_applied_to_olfaction_and_path_integration)
| InsectRobotics/path-integration | No LICENSE seen (unconfirmed) | — | Stone 2017 CX model [github](https://github.com/InsectRobotics/path-integration) |
| pycma | BSD-3-Clause | r4.4.3, February 2026 | CMA-ES [github](https://github.com/conda-forge/cma-feedstock) [zenodo](https://zenodo.org/records/18763699) |
| evosax | Apache-2.0 | v0.2.0, March 2025 | JAX evolution strategies on GPU [github](https://github.com/RobertTLange/evosax) [github](https://github.com/RobertTLange/evosax/releases) |
| EvoTorch | Apache-2.0 | Updated May 2026 | PyTorch evolution strategies on GPU [github](https://github.com/nnaisense) |
| neat-python | BSD-3-Clause | v2.0.1 (Python 3.12+) | NEAT seeding [github](https://github.com/CodeReclaimers/neat-python/releases) [github](https://github.com/RobertNiklasBock/neat-python-fast) |

The licence and maintenance data come from repository metadata [SECONDARY]. Verify them before you redistribute anything.

## Caveats
- Many leads from the brief (Braitenberg formal analyses, silkmoth physiology, Keinan MSA, Clune modularity, the RIA/SMD weathervaning papers) were not verified in this pass and are not cited as findings.
- Most sources were read only as abstracts or secondhand. The [READ] sources are Izquierdo & Beer 2013, Izquierdo & Lockery 2010 (in part), Goulard et al. 2021 (sections 2.1–2.6) and Noorman et al. 2024 (introduction).
- The Goulard and Izquierdo equations are published as images, so we give equation numbers and parameter values but not transcribed formulas.
- Single studies: Gaudry et al. 2013 (the 40% figure), Okubo et al. 2020, Noorman et al. 2024 and Kakaria & de Bivort 2017 are each single studies. The arXiv and bioRxiv items are preprints.

## Open questions (you would have to test these yourselves)
1. Is the plateau a gain or parameterisation ceiling or a search failure? Re-run with |w| ≤ 15 or an input-gain gene, and with normalised (L−R)/(L+R) sensors.
2. Does moving from the ASEL/ASER mapping to symmetric AWC/AWA-only inputs change what evolution finds?
3. Does evolution on the full connectome discover klinotaxis (temporal derivative) if the stereo cue is removed, as Izquierdo & Beer found on a pruned circuit?
4. Is a grafted crossed-inhibition steerer kept, and is a grafted ring kept, under free versus protected mutation?
5. Does an odour-direction ring improve scores only when the scent is intermittent or occluded? Test this with a patchy source.
6. In E3, do evolved selectors converge to clean bistable latches, or to transient modes as in Agmon & Beer 2014?