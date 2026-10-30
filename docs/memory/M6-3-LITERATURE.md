# M6, option 3: what the real worm shows about history in its head-steering circuit — a bounded literature check

*Draft 2, 2026-10-30, after one review round. Astra 6 and Fable 5.1 both said "fix then publish". Every fix was
checked against the sources and taken; the two points that did not hold are noted under "Corrections from review".
Draft 1, the prompts and the reviews are in [`docs/reviews/20261030-m6-3-scope/`](../reviews/20261030-m6-3-scope/).

The scope is [`M6-3-SCOPE.md`](M6-3-SCOPE.md), draft 2, written after a blind first round with both consultants. The
owner chose option 3 of [`M6-OPTIONS.md`](M6-OPTIONS.md), "with consultation with Fable and Astra". No compute. This
is not a deep research and not a test of the model. Every claim carries the level at which its source was read.*

## How this was done

**Sources.** 44 sources, collected in three ways:
- Claude's own searches: Europe PMC, the Consensus index and web search, 2026-10-30;
- the two consultants' blind lists, merged;
- five sources the round-2 reviewers added.

**Retrieval.** Each source was fetched through public interfaces only:
- Europe PMC's search, for metadata and abstracts;
- its full-text service, for open-access texts;
- NCBI's E-utilities, for the PMC open-access and author-manuscript copies;
- two preprint pages, through a page fetch.

Pages behind a bot check were not worked around. 30 full texts were retrieved, plus one preprint read through a
page fetch.

**Reading.**
- Claude read these itself: the two Lockery pieces, Hendricks 2012, Ouellette 2018, Dunn 2025's summary, results on
  single-neuron stimulation and discussion, Liu J 2022's RMD passage, and parts of Nicoletti 2019 and Kaplan 2020.
- Three reading agents (Claude subagents, working only on the downloaded texts) read the other full texts against
  fixed questions. They returned verbatim quotes.

**Quote checks.**
- **The agents' 386 quotes** were all found by exact string match, one after a reading agent corrected it.
- **Every quoted passage in this report** was checked the same way, against the local texts and abstracts
  (`reading/check_report.py`).
- **An exact match verifies the transcription, not the context** (Astra). Two context errors in draft 1 are among
  the corrections below.
- **Where the records are.** The source list, the quote lists, the scripts and Claude's log are in
  [`docs/reviews/20261030-m6-3-scope/reading/`](../reviews/20261030-m6-3-scope/reading/). The full texts are not
  committed.

**Levels:**
- **full text:** the full text was retrieved and the passages cited were read; it does not mean every page was read;
- **abstract:** only the abstract was read;
- **secondary:** known only through another source;
- **not found:** a bounded search found nothing.

## In short

1. **A two-state membrane property in one head-steering neuron: yes, RMD. Its mechanism is open.**
   - **What was recorded.** In situ, a brief positive current pulse or a puff of glutamate moved RMD into a
     depolarisation "stable for at least 1 min", which a brief negative pulse ended. That makes "two stable resting
     potentials, one near −70 mV and one near −35 mV", and shifts also occurred spontaneously.
   - **Sources.** All of this comes from Lockery & Goodman's 2009 commentary (full text) describing Mellem et al.
     2008, which was read only at abstract level ("their potential state appears to be bistable"). It rests on one
     primary report. No later RMD recording was found (searches below).
   - **Mechanism.** A conductance model reproduces the two states through intrinsic currents, the T-type channel
     CCA-1 and the leak (Nicoletti et al. 2019, full text, a fitted model). A rate model on the connectome proposes
     instead a circuit contribution, the RMDL–RMDR excitatory loop (Liu J et al. 2022, full text). The experiments do
     not exclude synaptic contributions (Astra), and Lockery & Goodman left that question open.
   - **Function.** That the state stores "the sign of the most recent synaptic input" was a hypothesis. In 2009
     Lockery & Goodman wrote that "almost nothing is known" of plateau functions in the worm.
2. **History steering a later turn: yes. In the most directly relevant study checked, the authors place the memory in
   oscillation phase.**
   - **What was shown.** Optogenetic AWA stimulation, timed to head bends during forward crawling, biases the
     direction of the turn that ends the next reversal (Dunn et al. 2025, full text). AWA is one of the model's food
     inputs.
   - **Where the authors place the memory.** In tetramisole-paralysed worms (fictive behaviour), the turn about 30
     to 90 s later could be biased. The authors find the memory "held in the relative phase of the distributed
     oscillations of two groups of many neurons". They name SMDD, SMDV, RIA and RIV as "headswing complex neurons",
     and RMDD and RMDV among the neurons in both groups.
   - **Single neurons.** Stimulating any of "five different neuron classes/subcompartments within the headswing
     complex" ended reversals "yet do not bias turn direction". The authors leave open "other intermediate carriers
     of the memory trace", single neurons included, and which neurons are necessary.
   - **Against the model:** the model's present probe has no head oscillation, so it does not assay this mechanism.
3. **The other history effects found have different physiological substrates from the model's, though some overlap
   in kind.**
   - **What they are.** Several are held in the sensory neurons (AWA desensitises over seconds to hours; AWC is a
     biphasic filter). Several are held in command and modulatory states lasting seconds to tens of minutes. One is
     a food memory that changes reversal-driven reorientations for 10 to 20 minutes after food is removed.
   - **Where they overlap with the model.** Their circuit motifs (mutual inhibition, gap junctions, positive
     feedback) are of kinds a rate network can express (Astra). What the model lacks is their physiology:
     neuromodulators, intrinsic currents and sensory transduction.
   - **A contrast, outside the scope.** ASER's salt set point, held over hours, is plasticity.
4. **RIA: an integrator of sensory and motor signals. No source checked shows it holding a state, and none excludes
   it.**
   - **What the sources show.** Its axon's two compartments follow each head bend, driven by SMD. Its whole-axon
     sensory responses are transient. A proposed gate and routing mechanism places its sensory input under head
     posture and routes its output dorsally or ventrally (Hendricks 2012, Ouellette 2018, Liu 2018, full texts).
   - **In Dunn 2025.** Its nuclear calcium was not a strong correlate of either oscillating group. The authors
     expected its axonal compartments to be, and RIA features improved their decoding of the turn.
   - **For the model.** This neither supports nor rules out a storage role. The model's RIA result, vulnerability
     to a cut, gets no further support from it.
5. **Structure: the evidence is mixed on how far anatomy predicts function.**
   - **Against.** 6% of the neuron pairs measured in immobilised worms met a stringent criterion for a functional
     connection, and anatomy-based predictions agreed poorly with the measurements (Randi 2023, full text).
   - **For.** A dynamical model fitted with weights only on anatomical edges captured causal interactions "82% as
     well as the reproducibility of the perturbation data", far better than shuffled connectomes (Creamer et al.,
     bioRxiv 2024, abstract).
   - **Wiring varies between individuals.** About 43% of connections differ between isogenic animals, but these
     carry 16% of chemical synapses, and the interneuron circuits are largely stable (Witvliet 2021, full text).
6. **Model precedents: history-independent multistability on the connectome is known in rate and conductance
   models.**
   - **Kunert-Graf et al. 2017 (full text):** a fixed point and a limit cycle coexist under the same constant input,
     reached from different initial conditions.
   - **Liu J et al. 2022 (full text):** a rate model gives the structural conditions for multiple fixed points, and
     notes that a state is kept when "external input terminates".
   - **The model's probe holds the final food level throughout** (Astra, Fable), so its switches are also attractors
     under constant input.
   - **What the thread adds** is a protocol, not a known novelty: the basin chosen by a specified sensory history,
     the rate of such genomes over random weights, and the dependence on the head core's block. Whether that is new
     would need a proper novelty search.

**What this does not show:** that the worm lacks a history switch of the model's kind. It is "not found in the
sources checked", not a negative finding.

## 1. Persistent or multiple states in the head-steering and command neurons

| Claim | Source (level) | Preparation, measure | History, duration | Open |
|---|---|---|---|---|
| RMD: a positive pulse or glutamate starts a depolarisation "stable for at least 1 min", ended by a negative pulse; "two stable resting potentials"; spontaneous shifts; depends on "a current carried mainly by Na+ and Ca2+ ions" (their "suggest") | Lockery & Goodman 2009 N&V, full text, describing Mellem et al. 2008 (abstract) | in situ whole-cell current clamp | current injection, not sensory history; ≥ 1 min | intrinsic or partly synaptic; no replication found |
| The initial transients are graded regenerative potentials, not action potentials; "approximately half of these events were followed by a stable plateau potential"; "the first demonstration of plateau potentials in a C. elegans neuron" | Lockery, Goodman & Faumont 2009, full text | as above | — | terminology dispute; the plateau itself is accepted |
| A conductance model has two stable equilibria (−70, −47 mV) switched by transient current; removing CCA-1 in silico removes the depolarised state | Nicoletti et al. 2019, full text | single-compartment model fitted to Mellem's current clamp | — | "other parameter sets could be identified"; an in-silico knockout, not an experiment |
| The RMD plateau "may also be explained by multiple fixed points" of the RMD network (RMDL–RMDR excitatory synapses) | Liu J et al. 2022, full text | rate model on the connectome | — | a modelling interpretation |
| AVA shows "two stable membrane potentials with rapid transitions between them" (−17 and −32 mV in the trace shown); a model with reciprocal inhibition between forward and reverse command pools predicts search behaviour, and AVA–AVB inhibition was measured | Roberts et al. 2016, full text | patch clamp of AVA/AVB, behaviour, model | seconds | "premature to conclude that the biological system functions as assumed" |
| RIM stabilises reversals when depolarised (glutamate, tyramine) and forward runs when hyperpolarised (gap junctions), "behavioral inertia"; the word "bistable" is not used | Sordillo & Bargmann 2021, full text | behaviour, AVA imaging, cell-specific manipulations | single reversals and runs; the ~15 min is the local-search period, not one RIM state | innexin contributions |
| AIB–RIV electrical feedforward excitation and AIB/RIB inhibition implement a winner-take-all between reversal and turn modules | Wang et al. 2020, full text | imaging (moving, immobilised), optogenetics, mutants | escape, seconds | inhibitory feedback mechanism |
| SMD switches between high- and low-activity states with the forward/reverse command cycle (~0.05 Hz), AIB "crucial for switching"; head-casts ~1 Hz; persists without movement | Kaplan et al. 2020, full text | whole-brain imaging, immobilised and moving; hisCl | cycle of ~20 s | — |
| SMD "sustains bending states" (published and bioRxiv abstracts; the full-text page read has "maintain"), with bistability inferred from behaviour and a model, not recorded; RMD subgroups show calcium dynamics correlated with "slow transitions between behavior states" (bioRxiv abstract; not found in the part of the full text read) | Li et al. 2026 / bioRxiv 2024.11.18.624064, abstract and full text via a page fetch | behaviour, ablations, model | head-bend time scale | no direct recording |
| AIY's forward-run representation is a corollary discharge needing RIM; positive feedback sustains forward runs | Ji et al. 2021, eLife 10:e68848, full text | imaging, ablations, thermotaxis | runs; cooling periods 7–30 s | the synaptic route of the corollary discharge |
| Roaming and dwelling last minutes (dwelling τ = 482 s); serotonin and PDF initiate and extend them; mutual inhibition between the two systems underlies their persistence | Flavell et al. 2013; Ji et al. 2021, eLife 10:e62889, full texts | freely moving imaging, mutants, optogenetics | minutes to tens of minutes | the neurons driving short states without 5-HT or PDF |

**Reading:**
- **Persistent states are documented in the worm's command and modulatory circuits.** They are attributed to circuit
  motifs (mutual inhibition, gap junctions, positive feedback), some only modelled, and to neuromodulators.
- **Among the head-steering read-out neurons,** RMD has a recorded two-state membrane property, from one report,
  whose mechanism is open.
- **SMD's states, in the sources checked,** follow the command cycle or the head bend. None is set by a food history.

## 2. History changing later steering or turning

| Claim | Source (level) | Preparation | History; matched later? | Time scale | Open |
|---|---|---|---|---|---|
| Posture-timed AWA stimulation during forward crawling biases the post-reversal turn; the authors place the memory in the relative phase of a headswing complex and a command complex | Dunn et al. 2025, full text | closed-loop behaviour; whole-brain imaging in tetramisole-paralysed worms (fictive) | stimulation withheld after reversal onset; compared with unstimulated control | fictive turns ~30–90 s later | other carriers; which neurons are necessary |
| Stimulating SMDD, SMDV, RIA (nrV, nrD) or RIV during fictive reversals ends reversals but does not bias turn direction; after RIA stimulation, SMDV shows "prolonged and sustained depolarization for ventral but not dorsal TURNs" | Dunn et al. 2025, full text | as above | — | — | not a test of necessity |
| Turning sequences: SAAV anticipates turn direction; RIM tyramine coordinates the sequence; the gradient is integrated over "a couple head swings"; RMDD, not RMDV, inverts its phase between forward and reverse movement | Kramer et al. 2026, full text | freely moving whole-brain imaging; optogenetics; tdc-1 | no matched-history design | reorientation 10–20 s after veering | roles of SMB and RIV |
| Some neurons integrate the animal's recent velocity over tens of seconds (RIC, in C3, among them); a decoder reads past velocity 20 s back, but current activity does not predict future velocity or head bending | Atanas et al. 2023, full text | freely moving whole-brain imaging | motor history, not food | half-decay 0.9–31.7 s | causal use not tested ("We did not distinguish whether a given neuron's encoding of behavior reflected the neuron causally driving behavior") |
| Prior food concentration (45 min) changes reversal-driven reorientations during local search, under the same food-free test conditions; the population moves to global search over 10–20 min, while 51% of individuals show a single abrupt transition | López-Cruz et al. 2019, full text | behaviour; imaging; mutants | yes | minutes | "the nature of the additional clock is unknown" |
| The network state of AIB, RIM and AVA at odour arrival gates AIB's response (state gates input, the reverse direction from the model's probe) | Gordus et al. 2015, abstract | — | — | — | — |
| AWA is "concentration- and history-dependent", integrating at low and desensitising at high concentration; responses fall over ~300 pulses in a five-hour experiment; AIA compresses that history | Larsch et al. 2015, full text | imaging in microfluidics; behaviour | odour pulse histories | seconds to hours | electrophysiology of AWA |
| AWC and ASH are near-linear biphasic filters (AWC sign change after 10–12 s) | Kato et al. 2014, full text | imaging, immobilised | odour sequences | seconds | adaptation beyond ~60 s |
| ASER encodes gradient and salt set point cell-autonomously; downstream AIB, AIY, AVA encode movement, not memory (plasticity; a contrast outside the scope) | Luo et al. 2014, full text | imaging, behaviour | growth salt (hours) | hours | causality of ASER patterns |
| AWC-ON adapts its threshold to odour history; EGL-4 sets the timescale | Levy & Bargmann 2020, abstract | — | — | — | — |
| Whole-brain imaging under bacterial stimuli: clusters for AVA, RME, SMDD, SMDV; network states in which AVA and RME clusters are "largely unperturbed by or receptive to" bacterial input | Cecere et al., bioRxiv 2021.04.09.439242 v2, abstract | restrained, whole-brain imaging | food onset and removal | not in the abstract | the SMD timing Fable recalled was not verified |

**Reading:**
- **Where the worm holds history.** The documented history effects on turning are held in the sensory neurons, in
  oscillation phase across distributed neurons (the authors' interpretation), in neurons integrating recent motor
  history, and in modulators and command states.
- **No food-history level in the head-steering neurons.** In no source checked is a food history held as a
  persistent level there. The nearest is SMDV's sustained depolarisation before ventral turns in Dunn 2025, which is
  not shown to be a history-set stable state.
- **Against the model.** The model's fading effect resembles, in form only, the sensory and integrating memories that
  fade. The phase-based memory is not assayed by the model's present probe.

## 3. RIA

- **Its compartments track head bends.** "the single RIA axon is partitioned into distinct domains, and calcium
  dynamics within these domains spatially represent, or encode, head movement". This is driven by SMD through GAR-3
  and persists in paralysed animals; the soma shows no prominent calcium response (Hendricks et al. 2012, full text).
- **Its whole-axon sensory responses are transient.** "global RIA axonal activity is transiently suppressed by IAA
  presentation and activated by its removal" (Hendricks 2012).
- **A proposed gate and routing mechanism.**
  - Sensory input is gated by head orientation, and output is routed: the "switch" routes output dorsally or
    ventrally. It is the authors' proposed mechanism, with the postsynaptic effects unresolved.
  - The results "are consistent with the hypothesis that RIA is involved in responses to asymmetrically presented
    stimuli but not the temporal integration that underlies the biased random walk strategy" (Ouellette et al. 2018,
    full text).
- **Steering arises from the asymmetry between its compartments.** Sensory input suppresses the motor signal in its
  two domains, and that asymmetry biases steering. Experience (6 h of PA14 training) changes the integration
  "upstream of RIA" (Liu et al. 2018, full text).
- **Silencing it removes no motor link checked.** Silencing or blocking RIA left the relationship between SMD and
  head bending unchanged (Kaplan 2020, full text). RIA "appears to be not directly involved in action selection or
  the control of movement kinematics" (Huo et al. 2024, full text).
- **In Dunn 2025.** "The RIA nuclear calcium signal did not emerge as a strong correlate to either complex". The
  same sentence goes on to expect RIA's nrV and nrD compartments to correlate strongly. RIA features improved
  decoding ("Inclusion of several individual headswing neuron features (SMDD, SMDV, RIA) improves prediction
  accuracy"), and stimulating its compartments ended reversals without biasing the turn.

**Reading:** an integrator of sensory and motor signals on the time scale of a head bend, with a proposed routing
role. No source checked reports it holding a state, and no source tests whether it does. The model's finding, that
its switches are vulnerable to cutting RIA's edges, is consistent with RIA's central wiring position. The literature
gives it no further support as a storage site; the scope's guard against RIA confirmation bias applies.

## 4. Structure

- **Function and anatomy (Randi et al. 2023, full text; immobilised animals).**
  - "A total of 1,310 of the 23,433 measured neuron pairs, or 6%, pass our stringent criteria to be deemed
    functionally connected at q < 0.05". Failing that threshold is not proof of disconnection (Astra).
  - The anatomy-based models evaluated agreed poorly with the measurements. Fitting weights and signs on the
    anatomical edges improved agreement, but "overall agreement remained poor".
  - Some signalling is extrasynaptic. RIA and SMD are not discussed.
- **The counterweight (Creamer, Leifer & Pillow, bioRxiv 10.1101/2024.09.22.614271, abstract).** A connectome-
  constrained dynamical model fitted to the same kind of perturbation data "captured causal interactions between all
  pairs of neurons 82% as well as the reproducibility of the perturbation data themselves". Models fitted on
  shuffled connectomes did much worse.
- **Hubs (Uzel et al. 2022, abstract).** Non-local connectivity features and hub neurons predict functional
  relations, and inhibiting hubs disrupts brain-wide correlations.
- **The rich club (Towlson et al. 2013, abstract).** It is 11 neurons, "almost exclusively the interneurons of the
  locomotor circuits". Whether RIA is among them was not checked.
- **Variation between individuals (Witvliet et al. 2021, full text; chemical synapses only).**
  - "About 43% of all cell-cell connections – accounting for 16% of all chemical synapses – are not conserved between
    isogenic animals". Variable connections are mostly weak.
  - "the layout of interneuron circuits, the core decision-making architecture, is largely stable", and motor
    neurons are the least variable.
  - Modulatory neurons' outputs are the most variable. That class includes CEP and RIC, both in C3.
  - The study could not assess animal-to-animal variability at each age.
- **Gap junctions and state (Bhattacharya et al. 2019, full text).** In dauers, innexin expression changes in 86 of
  118 neuron classes; AIB gains inx-6 in dauer and in L1 diapause.

**Reading:**
- **On anatomy and function, the evidence is mixed.** Measured propagation departs from simple anatomical
  predictions. A fitted connectome-constrained model captures most of it, and the wiring matters there: shuffled
  connectomes do worse.
- **On C3.** Neither result makes the model's C3 a functional module; it remains an anatomical object.
- **On variation.** The worm's variable connections are mostly weak ones, while the strong, high-degree wiring a
  dense core relies on is the conserved part (Fable). No conversion from connection variability to switch prevalence
  exists, so nothing follows for the size of the model's effects (Astra).

## 5. Model precedents

- **Kunert-Graf et al. 2017 (full text):**
  - **The model:** the whole connectome with single-compartment conductance neurons, identical except for
    connectivity and sign.
  - **What it found:** connectivity alone gives multistability. Under constant PLM and ASK input, a fixed point and
    a limit cycle coexist ("at about 1.7 × 104 the system becomes bistable with the addition of a new fixed point").
    "The two trajectories plotted are in response to the same constant input amplitudes into PLM and ASK, and differ
    only by their initial conditions."
  - **Transients** are "much slower (on the order of seconds to tens of seconds) than any intrinsic neuronal
    timescales".
  - **Limit:** "there is no theoretical guarantee that we find all possible states of the system".
- **Liu J et al. 2022 (full text):**
  - **The model:** a nonlinear rate model on the connectome.
  - **What it found:** the structural condition for multiple fixed points, and a finite-state account of the command
    circuit's forward–reverse switching.
  - **Two points that bear on this thread.** States persist "when external input terminates" within a basin, and
    the RMD plateau may come from the RMD network's multiple fixed points.
- **Izquierdo & Beer 2013 (full text):**
  - **The model:** evolved passive-node circuits on a minimal klinotaxis path (ASE → AIY → AIZ → SMB), with an
    imposed head oscillation.
  - **What it found:** state dependence. Motor-neuron bistability was rare and tied to strong self-connections.
    Transients lasted about one head sweep.
  - **Limit:** no RIA, SMD or RMD.

**Reading:**
- **Multistability, long transients and their structural conditions in connectome models are known.**
- **The model's switches are of the same broad kind:** attractors under a constant held input. Its probe holds the
  final food level, so draft 1's "outlasts its input" distinction was wrong (Astra, Fable).
- **What differs is the protocol.** A specified sensory history selects the basin, the rate of such genomes is
  measured over random weights, and it depends on the head core's block. Whether any of this is new needs a proper
  novelty search; this check does not claim it.

## 6. The model against the worm

| Model feature | Closest worm evidence | Match |
|---|---|---|
| Rare switches: two stable states selected by a food ramp, under a held input, through recurrent saturating synapses | RMD's two stable potentials, set by current or glutamate, mechanism open (modelled as intrinsic, or as circuit); command-state flip-flops attributed to circuits | form yes; mechanism unresolved for RMD; the command circuits are not set by food history in the sources checked |
| Switches vulnerable at RIA | RIA integrates and, by a proposed mechanism, routes; no state shown or tested | no support beyond wiring position |
| Fading history effect in most genomes and evolved champions, tens of ticks | sensory adaptation and filters (seconds to hours); integration of recent motor history (tens of seconds); local-search memory (minutes) | form only; no time calibration |
| Evolved champions: larger, fading effect | no counterpart checked | — |
| Dense head core raises the switch rate | mixed evidence on anatomy and function; hubs matter for global dynamics | not addressed by the literature checked |
| Same food signal into AWA, AWC, ASE as leaky units | AWA history-dependent and spiking (Liu Q 2018, abstract); AWC biphasic; ASER set point | mismatch, by design |
| Probe without head oscillation | the worm's turn memory is placed by its authors in oscillation phase | not assayed by the present probe |

## 7. What would mislead, with the evidence now in hand

- **"Bistable".** RMD's states are modelled as intrinsic in one model and as circuit-based in another, and the
  experiments do not settle it. Dunn's "two core bistable groups" are command-state neurons. Neither is shown to be
  the model's mechanism.
- **"Switch".** Ouellette's switch is routing.
- **Signs and transmitters.** The model draws signs at random. Any comparison is topological only.
- **Lumping the read-out.** The model sums RMD with SMD. The worm separates them: RMD makes fast head casts and SMD
  slower bending (Li), and RMDD but not RMDV inverts its phase with movement direction (Kramer).
- **Time.** Worm effects run from about 1 s (head-casts) to tens of minutes (states). The model's ticks are
  uncalibrated.
- **Preparations differ.**
  - The RMD plateau was recorded in situ under current injection.
  - Dunn's memory mechanism comes from paralysed worms, with the behavioural effect in moving worms.
  - SMD calcium persists in immobilised worms in Kaplan and Hendricks, but was absent in paralysed unc-54 mutants in
    Yeon et al. 2018 (full text). Paralysis method matters.
- **Population against individual.** The model's percentages describe a weight ensemble; the worm is one parameter
  set with variable wiring.

## Coverage and gaps

- **Overlap of the blind lists (round 1).**
  - **Named by both:** Mellem 2008, the Lockery correspondence, Hendricks 2012, Liu 2018, Ouellette 2018, Yeon 2018,
    Kramer 2026, Kato 2014, Gordus 2015.
  - **Astra only:** Dunn 2025, López-Cruz 2019, Ji 2021 (eLife 10:e62889), Flavell 2013, Goodman 1998.
  - **Fable only:** Nicoletti 2019, Sordillo 2021, Roberts 2016, Wang 2020, Ji 2021 (eLife 10:e68848), Kaplan
    2020, Kato 2015, Atanas 2023, Kunert-Graf 2017, Izquierdo & Beer 2013, Randi 2023, Witvliet 2021, Uzel 2022,
    Huo 2024, Shen 2016, Chen 2024, Li 2026, Larsch 2015, Levy 2020, Luo 2014, Alkema 2005, and the tyramine and atlas
    papers. Gray 2005, Towlson 2013 and Bhattacharya 2019 came from memory.
  - **Neither consultant:** Lockery & Goodman's News & Views and Liu Q 2018. Claude's own searches also found several
    of the sources above independently.
- **Added in round 2:** Liu J 2022 and Creamer 2024 (Astra); Cecere 2021, Nicoletti 2024 and the Li bioRxiv
  abstract (Fable).
- **Abstract only:** Mellem 2008 (its full text is behind the bot check, and the publisher forbids XML), Kato 2015,
  Gordus 2015, Levy 2020, Uzel 2022, Towlson 2013, Goodman 1998, Liu Q 2018, Gray 2005, Alkema 2005, Creamer 2024,
  Cecere 2021, Nicoletti 2024.
- **Not checked:** Pirri 2009, Kagawa-Nagamura 2018, Dvali 2024 (named by Fable), and the Rusu 2021 preprint.
- **Later RMD electrophysiology: not found.**
  - **Claude's queries (Europe PMC, 2026-10-30):** `(ABSTRACT:"RMD" OR TITLE:"RMD") AND (ABSTRACT:"patch" OR
    ABSTRACT:"current clamp" OR ABSTRACT:"electrophysiolog*" OR ABSTRACT:"plateau") AND ("elegans")` gave 0 hits.
    `("plateau potential" OR "plateau potentials") AND "elegans"` gave 86 hits, of which the RMD items were
    Nicoletti 2019, Liu J 2022 and the two 2009 Lockery pieces.
  - **The reviewers' own bounded searches** found only models (Nicoletti 2020 and 2024; Naudin 2020 and 2022).
  - **A limited search result,** not evidence that none exists.
- **Retrieval queries.** `reading/sources.json` records the retrieval query for each known source. Claude's
  discovery searches are in `reading/claude-log.md`.
- **Name mismatch:** the eLife corollary-discharge paper (Ji et al.) is 2021, not 2019 as Fable's list implied.

## Corrections from review

Draft 1 was corrected on these points:
- **RMD.** Draft 1 called the mechanism intrinsic and the preparation "dissected"; both are now as above (Astra,
  Fable).
- **Dunn 2025.**
  - "No single neuron carries it" is removed (Astra).
  - The RIA sentence's context is restored, with the decoding result (Astra).
  - "The one study that shows it" now reads "the most directly relevant study checked" (Astra).
  - The 30–90 s is tied to fictive turns (Astra).
- **Kunert-Graf.** Draft 1's "outlasts its input" distinction is removed, because the model's probe holds the final
  input (Astra, Fable). Liu J 2022 is added (Astra).
- **Structure.** Randi's 6% is qualified, Creamer added, and Witvliet's 16% and stable core added. Draft 1's "could
  swamp the model's effects" is removed (Astra, Fable).
- **López-Cruz.** Draft 1 said "turns during forward movement unaffected" by food history. The source compares
  local and global search, not food histories (Fable). Individual transitions are often abrupt (Astra).
- **Other hedges and qualifiers.** Ouellette's hedge and the proposed status of its mechanism are restored (Astra,
  Fable). Sordillo's 15 minutes is the local-search period, not one state (Astra). Atanas, Gordus, Cecere and the
  missing guards are added (Fable, Astra).

Two review points did not hold on checking:
- **Dunn's preparation.** Dunn's methods use 5 mM tetramisole, so "tetramisole-paralysed" stands.
- **Larsch's time span.** It includes a five-hour pulse experiment, so "seconds to hours" stands.

## What this means for the thread

- **The literature does not show the model's switch in the worm.** It shows four things nearby:
  - a two-state membrane property in RMD, from one report, with its mechanism open;
  - persistent command and modulatory states;
  - neurons integrating recent motor history;
  - a turn memory that its authors place in oscillation phase across the head-steering neurons, which the present
    probe does not assay.
- **What the literature offers the model.** It gives no worm-side measurement the model's switch could be scored
  against.
- **Options raised in review, for the owner.** This report recommends none of them.
  - **Stop (option 4)**, folding this check into the synthesis as its biology section (Fable's recommendation).
  - **A causal test of the fading effects.** Ask whether the evolved champions' fading effects contribute to
    behaviour, using validated interventions (Astra's recommendation, if the thread continues).
  - **A cheap description, CPU minutes.** Return the food to baseline after the ramp in the already-classified switch
    genomes. Fable suggested it to see whether their states outlast the input.
  - **Larger changes.** An RMD plateau in the model, or a phase-sensitive task. Both are new projects that the
    literature does not compel. Astra advised against adding a plateau only to resemble one observation. Fable noted
    that neither direction has a worm-side target the model could be scored against.
