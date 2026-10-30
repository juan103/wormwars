# M6, option 3: what the real worm shows about history in its head-steering circuit — a bounded literature check

*Draft 1, 2026-10-30, before review. Scope: [`M6-3-SCOPE.md`](M6-3-SCOPE.md), draft 2, after one blind round with
Astra 6 and Fable 5.1 ([`docs/reviews/20261030-m6-3-scope/`](../reviews/20261030-m6-3-scope/)). The owner chose
option 3 of [`M6-OPTIONS.md`](M6-OPTIONS.md), "with consultation with Fable and Astra". No compute. This is not a deep
research and not a test of the model. Every claim carries the level at which its source was read.*

## How this was done

**Sources.** 39 sources, collected in two ways:
- Claude's own searches: Europe PMC, the Consensus index and web search, 2026-10-30;
- the two consultants' blind lists, merged.

**Retrieval.** Each source was fetched through public interfaces only:
- Europe PMC's search, for metadata and abstracts;
- its full-text service, for open-access texts;
- NCBI's E-utilities, for the PMC open-access and author-manuscript copies.

Pages behind a bot check were not worked around. 29 full texts came through.

**Reading.**
- Claude read these itself: the two Lockery pieces, Hendricks 2012, Ouellette 2018, the key passages of Dunn 2025,
  and parts of Nicoletti 2019 and Kaplan 2020.
- Three reading agents (Claude subagents, working only on the downloaded texts) read the other full texts against
  fixed questions. They returned verbatim quotes with line numbers.
- **Every quote was checked against its file by exact string match:** 386 quotes, all found, one after
  a reading agent corrected it.
- The source list, the quote lists, the scripts and Claude's log are in
  [`docs/reviews/20261030-m6-3-scope/reading/`](../reviews/20261030-m6-3-scope/reading/). The full texts are not
  committed.

**Levels:**
- **full text:** read;
- **abstract:** only the abstract was read;
- **secondary:** known only through another source;
- **not found:** a bounded search found nothing.

Not every passage of a full-text source was read: the level says what was available, and the quotes say what was
used.

## In short

1. **Two stable states in a single head-steering neuron: yes, RMD, with an intrinsic mechanism.**
   - **What was recorded.** In situ, a brief current pulse or a puff of glutamate moves RMD from about −70 mV to a
     plateau near −35 mV. The plateau lasts at least a minute, and a brief negative pulse ends it. Shifts also occur
     spontaneously (Lockery & Goodman 2009, full text, describing Mellem et al. 2008, abstract).
   - **The mechanism** is a regenerative Na⁺ and Ca²⁺ current; a conductance model puts it in the T-type channel
     CCA-1 and the leak (Nicoletti et al. 2019, full text).
   - **Its role is a hypothesis.** Lockery & Goodman proposed that such a state "stores the sign of the most recent
     synaptic input", and wrote that "almost nothing is known" of its function in the worm.
   - **Against the model:** this is the closest biological match to the model's switch in form, and the furthest in
     mechanism. The model has no intrinsic conductances; its switches come from recurrent saturating synapses.
2. **History steering a later turn: yes. In the one study that shows it, the memory is phase in oscillations, not a
   held level.**
   - **What was shown.** AWA stimulation, timed to head bends during forward crawling, biases the direction of the
     turn that ends the next reversal, tens of seconds later (Dunn et al. 2025, full text). AWA is one of the model's
     food inputs.
   - **Where the memory is.** In paralysed worms, the authors find the memory "held in the relative phase of the
     distributed oscillations of two groups of many neurons". The headswing group includes SMD, RMD, RIA and RIV.
   - **No single neuron carries it.** Stimulating SMD, RIA or RIV alone ended reversals but "did not bias the
     subsequent TURN direction".
   - **Against the model:** the model's probe has no head oscillation, so this mechanism has no counterpart in it.
3. **The other history effects found sit outside the model's mechanism.**
   - **In the sensory neurons:** AWA desensitises; AWC is a biphasic filter; ASER holds a salt set point over hours
     (Larsch 2015, Kato 2014, Luo 2014, full texts).
   - **In command and modulatory states:** these last seconds to tens of minutes, held by RIM's synapses, by mutual
     inhibition among command neurons, or by serotonin and PDF (Sordillo 2021, Roberts 2016, Flavell 2013, Ji 2021,
     full texts).
   - **In a fading food memory:** after food is removed, it fades over 10 to 20 minutes (López-Cruz 2019, full text).
     It changes reversal-driven reorientations, not turns made during forward movement.
4. **RIA: an integrator, not shown to store anything.** The texts checked show it doing four things:
   - its axon's two compartments follow each head bend, driven by SMD (corollary discharge);
   - its sensory responses are transient;
   - its sensory input is gated by head posture;
   - its output is routed dorsally or ventrally (Hendricks 2012, Ouellette 2018, Liu 2018, full texts).

   No persistent RIA state was found in the sources checked. Its nuclear calcium was not a strong correlate of either
   oscillating group in Dunn 2025. This fits the model's own reading of RIA, vulnerability rather than storage, and
   gives it no further support.
5. **Structure: the model's anatomical head core is not a functional unit by default.**
   - **Anatomy predicts poorly.** Only 6% of measured neuron pairs in the head are functionally connected, and
     predictions from anatomy agree poorly with measurement (Randi 2023, full text).
   - **Wiring varies.** About 43% of connections vary between isogenic animals (Witvliet 2021, full text).
   - **Gap junctions are remodelled with state** (Bhattacharya 2019, full text).
6. **Model precedent: multistability on the connectome is known, under sustained input.** A whole-connectome model
   with identical neurons shows bistability and transients of about 10 s that come from connectivity alone
   (Kunert-Graf et al. 2017, full text). A state that outlasts a transient input is not reported there. The model's
   history switch may still be new in that respect; the check cannot say that it is.

**What this does not show:** that the worm lacks a history switch of the model's kind. It is "not found in the
sources checked", not a negative finding.

## 1. Persistent or multiple states in the head-steering and command neurons

| Claim | Source (level) | Preparation, measure | History, duration | Open |
|---|---|---|---|---|
| RMD has two stable resting potentials, ~−70 and ~−35 mV; a positive pulse or glutamate starts a plateau "stable for at least 1 min", a negative pulse ends it; spontaneous shifts | Lockery & Goodman 2009 N&V, full text; Mellem et al. 2008, abstract ("These neurons resembled Schmitt triggers, as their potential state appears to be bistable") | in situ whole-cell current clamp (dissected) | current injection, not sensory history; ≥ 1 min | "almost nothing is known" of function; whether the plateau is intrinsic or partly synaptic (L&G question 2) |
| The initial transients are graded regenerative potentials, not action potentials; "approximately half of these events were followed by a stable plateau potential"; "the first demonstration of plateau potentials in a C. elegans neuron" | Lockery, Goodman & Faumont 2009, full text | as above | — | terminology dispute; the plateau itself is accepted |
| A conductance model reproduces two stable equilibria (−70, −47 mV) switched by transient current; removing CCA-1 removes the depolarised state | Nicoletti et al. 2019, full text | single-compartment model fitted to Mellem's current clamp | — | "other parameter sets could be identified" |
| AVA shows two quasi-stable potentials (−17 and −32 mV); a flip-flop of reciprocal inhibition between forward and reverse command neurons predicts search | Roberts et al. 2016, full text | patch clamp of AVA/AVB, behaviour, model | seconds | "premature to conclude that the biological system functions as assumed" |
| RIM stabilises reversals when depolarised (glutamate, tyramine) and forward runs when hyperpolarised (gap junctions): "behavioral inertia". The word "bistable" is not used | Sordillo & Bargmann 2021, full text | behaviour, AVA imaging, cell-specific manipulations | local search over ~15 min | innexin contributions |
| AIB–RIV electrical feedforward excitation and AIB/RIB inhibition implement a winner-take-all between reversal and turn modules; forward and backward modules as two attractors | Wang et al. 2020, full text | imaging (moving, immobilised), optogenetics, mutants | escape, seconds | inhibitory feedback mechanism |
| SMD switches between high- and low-activity states with the forward/reverse command cycle (~0.05 Hz); AIB is "crucial for switching"; head-casts ~1 Hz | Kaplan et al. 2020, full text | whole-brain imaging, immobilised and moving; hisCl | cycle of ~20 s; persists without movement | — |
| SMD "maintain[s] bending states"; bistability inferred from behavioural phase space and a model, not recorded | Li et al. 2026 (bioRxiv version), full text via fetch extraction; Curr Biol abstract | behaviour, ablations, model | head-bend time scale | no direct recording |
| AIY's forward-run representation is a corollary discharge needing RIM; positive feedback sustains forward runs | Ji et al. 2021 (eLife 10:e68848), full text | imaging, ablations, thermotaxis | runs; cooling periods 7–30 s | "We do not fully understand the synaptic mechanism by which CD reaches AIY" |
| Roaming and dwelling last minutes (dwelling τ = 482 s); serotonin and PDF initiate and extend them; mutual inhibition between the two modulatory systems underlies their persistence | Flavell et al. 2013; Ji et al. 2021 (eLife 10:e62889), full texts | freely moving imaging, mutants, optogenetics | minutes to tens of minutes | the neurons driving short states without 5-HT or PDF |

**Reading:**
- **Persistent states are well documented in the worm's command and modulatory circuits.** They are held by
  identified circuit motifs (mutual inhibition, gap junctions, positive feedback) and by neuromodulators.
- **Among the head-steering read-out neurons,** a recorded two-state membrane property exists in RMD, and it is
  intrinsic.
- **SMD's states in the sources checked follow the command cycle or the head bend.** None is set by a food history.

## 2. History changing later steering or turning

| Claim | Source (level) | Preparation | History; matched later? | Time scale | Open |
|---|---|---|---|---|---|
| Posture-timed AWA stimulation during forward crawling biases the post-reversal turn; memory "held in the relative phase" of a headswing complex (SMD, RMD, RIA, RIV, SAA…) and a command complex | Dunn et al. 2025, full text | behaviour (closed loop); whole-brain imaging in tetramisole-paralysed worms (fictive) | stimulation withheld after reversal onset; compared with unstimulated control | turn ~30–90 s later | "other intermediate carriers of the memory trace"; which neurons are necessary |
| SMDD/SMDV, RIA (nrV, nrD), RIV stimulation during fictive reversals ends reversals but does not bias turn direction | Dunn et al. 2025, full text | as above | — | — | — |
| Turning sequences: SAAV anticipates turn direction; RIM tyramine coordinates the sequence; gradient integrated over "a couple head swings" | Kramer et al. 2026, full text | freely moving whole-brain imaging; optogenetics; tdc-1 | no matched-history design | reorientation 10–20 s after veering | roles of SMB and RIV |
| Prior food concentration (45 min) changes reversal-driven reorientations during local search; fades to global search over 10–20 min; turns during forward movement unaffected | López-Cruz et al. 2019, full text | behaviour; imaging; mutants | yes (same food-free plate) | minutes | "the nature of the additional clock is unknown" |
| AWA is "concentration- and history-dependent", integrating at low and desensitising at high concentration; AIA compresses that history | Larsch et al. 2015, full text | imaging in microfluidics; behaviour | odour pulse histories | seconds to hours | electrophysiology of AWA |
| AWC and ASH are near-linear biphasic filters (AWC sign change after 10–12 s) | Kato et al. 2014, full text | imaging, immobilised | odour sequences | seconds | adaptation beyond ~60 s |
| ASER encodes gradient and salt set point, cell-autonomously; downstream AIB, AIY, AVA encode movement, not memory | Luo et al. 2014, full text | imaging, behaviour | growth salt (hours) | hours | causality of ASER patterns |
| AWC-ON adapts its threshold to odour history; EGL-4 sets the timescale | Levy & Bargmann 2020, abstract | — | — | — | — |

**Reading:**
- **The worm's documented history effects on turning are held in several places:** the sensory neurons, oscillation
  phase across distributed neurons, modulators and command states.
- **In no source checked is a food history held as a persistent level in the head-steering neurons.**
- **The model's fading effect resembles, in form, the sensory and local-search memories that fade.** It does not
  resemble the phase-based memory, which has no counterpart in an open-loop probe.

## 3. RIA

- **Its compartments track head bends.** "the single RIA axon is partitioned into distinct domains, and calcium
  dynamics within these domains spatially represent, or encode, head movement". This is driven by SMD through GAR-3
  and persists in paralysed animals; the soma shows no prominent calcium response (Hendricks et al. 2012, full text).
- **Its sensory responses are transient.** "global RIA axonal activity is transiently suppressed by IAA presentation
  and activated by its removal" (Hendricks 2012).
- **Its sensory input is gated by head orientation, and its output is routed.** The "switch" routes output to dorsal
  or ventral motor neurons. RIA is involved in responses to asymmetric stimuli "but not the temporal integration
  that underlies the biased random walk strategy" (Ouellette et al. 2018, full text).
- **Steering arises from the asymmetry between its compartments.** Sensory input suppresses the motor signal in its
  two domains, and that asymmetry biases steering. Experience (6 h of PA14 training) changes the integration "upstream
  of RIA" (Liu et al. 2018, full text).
- **Silencing it removes no motor link checked.** Silencing or blocking RIA left the relationship between SMD and
  head bending unchanged (Kaplan 2020, full text). RIA "appears to be not directly involved in action selection or
  the control of movement kinematics" (Huo et al. 2024, full text).
- **It did not track the memory in Dunn 2025.** "The RIA nuclear calcium signal did not emerge as a strong correlate
  to either complex"; stimulating RIA ended reversals without biasing the turn (Dunn 2025).

**Reading:** an integrator of sensory and motor signals on the time scale of a head bend. No source checked reports
it holding a state. The model's finding, that its switches are vulnerable to cutting RIA's edges, is consistent with
RIA's central wiring position. The literature gives it no further support as a storage site, and the scope's guard
against RIA confirmation bias applies.

## 4. Structure

- **Function departs from anatomy.**
  - Only "1,310 of the 23,433 measured neuron pairs, or 6%" are functionally connected.
  - There is "fairly poor agreement between anatomy-based model predictions and our measurements".
  - Fitting weights and signs on the anatomical edges improves agreement, but "overall agreement remained poor".
  - Some signalling is extrasynaptic (Randi et al. 2023, full text; immobilised animals). RIA and SMD are not
    discussed.
- **Hubs predict brain-wide correlations.** Non-local connectivity features and hub neurons predict functional
  relations, and inhibiting hubs disrupts brain-wide correlations (Uzel et al. 2022, abstract).
- **The anatomical rich club is 11 neurons** (Towlson et al. 2013, abstract), described as locomotor interneurons.
  Whether RIA is among them was not checked.
- **Wiring varies between individuals.**
  - "About 43% of all cell-cell connections – accounting for 16% of all chemical synapses – are not conserved between
    isogenic animals".
  - Interneuron circuits are "largely stable", and motor neurons are the least variable.
  - Modulatory neurons' outputs are the most variable. That class includes CEP and RIC, both in C3 (Witvliet et al.
    2021, full text; chemical synapses only).
- **Gap junctions change with state.** In dauers, innexin expression changes in 86 of 118 neuron classes; AIB gains
  inx-6 in dauer and in L1 diapause (Bhattacharya et al. 2019, full text).

**Reading:**
- **The model's C3 is an anatomical object.** The literature gives no reason to treat its density as a functional
  module, and some reason for caution: anatomy predicts function poorly.
- **Wiring differences between worms may exceed the model's effects.** The worm's own wiring varies at a level that
  could swamp the sub-percent wiring effects M4d and M5 chased. That says nothing about whether the dense core matters
  in the model.

## 5. Model precedents

- **Kunert-Graf et al. 2017 (full text):**
  - **The model:** the whole connectome with single-compartment conductance neurons, all identical except for
    connectivity and sign.
  - **What it found:** connectivity alone gives multistability. For example, "at about 1.7 × 10⁴ the system becomes
    bistable with the addition of a new fixed point" under constant PLM and ASK input. Transients run "much slower (on
    the order of seconds to tens of seconds) than any intrinsic neuronal timescales".
  - **Limits:** the bistability is under sustained input, and a state persisting after the input ends is not reported.
    The authors note that "there is no theoretical guarantee that we find all possible states of the system".
- **Izquierdo & Beer 2013 (full text):**
  - **The model:** evolved passive-node circuits on a minimal klinotaxis path (ASE → AIY → AIZ → SMB), with an
    imposed head oscillation.
  - **What it found:** state dependence. Motor-neuron bistability was rare and tied to strong self-connections.
    Transients lasted about one head sweep.
  - **Limits:** no RIA, SMD or RMD.

**Reading:**
- **Multistability and long transients in connectome models are known,** under sustained input.
- **A history-set state that outlasts its input,** found in random genomes on the full wiring, was not found in
  these two precedents. That makes it possibly new among connectome models, a claim that would need a wider search
  before it is made.

## 6. The model against the worm

| Model feature | Closest worm evidence | Match |
|---|---|---|
| Rare switches: two stable states set by a food ramp, recurrent saturating synapses | RMD plateau, two stable potentials set by current or glutamate (intrinsic); command-state flip-flops (circuit) | form yes; mechanism no for RMD; the command circuits are circuit-based but are not set by food history in the sources checked |
| Switches vulnerable at RIA | RIA integrates and routes; not a store in any source checked; not tracking Dunn's memory | no support beyond wiring position |
| Fading history effect in most genomes and evolved champions, tens of ticks | sensory adaptation and filters (seconds); local-search memory fading over minutes | form only; no time calibration |
| Evolved champions: larger, fading effect | no counterpart checked | — |
| Dense head core raises the switch rate | anatomy predicts function poorly; hubs matter for global dynamics | not addressed by the literature checked |
| Same food signal into AWA, AWC, ASE as leaky units | AWA history-dependent and spiking (Liu Q 2018, abstract); AWC biphasic; ASER set point | mismatch, by design |
| Open-loop probe, no oscillation | the worm's turn memory is held in oscillation phase | the main mechanism found has no counterpart |

## 7. What would mislead, with the evidence now in hand

- **"Bistable".** RMD's bistability is intrinsic (Lockery & Goodman; Nicoletti). Dunn's "two core bistable groups"
  are command-state neurons. Neither is the model's mechanism.
- **"Switch".** Ouellette's switch is routing.
- **Time.** Worm effects run from about 1 s (head-casts) to tens of minutes (states); the model's ticks are
  uncalibrated.
- **Preparations differ.**
  - The RMD plateau was recorded in situ under current injection.
  - Dunn's memory mechanism comes from paralysed worms, with the behavioural effect in moving worms.
  - SMD calcium persists in immobilised worms in Kaplan and Hendricks, but was absent in paralysed unc-54 mutants in
    Yeon et al. 2018 (full text). Paralysis method matters.
- **Population against individual.** The model's percentages describe a weight ensemble; the worm is one parameter
  set with variable wiring.

## Coverage and gaps

- **Overlap of the blind lists.**
  - **Named by both:** Mellem 2008, the Lockery correspondence, Hendricks 2012, Liu 2018, Ouellette 2018, Yeon 2018,
    Kramer 2026, Kato 2014, Gordus 2015.
  - **Astra only:** Dunn 2025, López-Cruz 2019, Ji 2021 (eLife 10:e62889), Flavell 2013, Goodman 1998.
  - **Fable only:** Nicoletti 2019, Sordillo 2021, Roberts 2016, Wang 2020, Ji 2021 (eLife 10:e68848), Kaplan
    2020, Kato 2015, Atanas 2023, Kunert-Graf 2017, Izquierdo & Beer 2013, Randi 2023, Witvliet 2021, Uzel 2022,
    Huo 2024, Shen 2016, Chen 2024, Li 2026, Larsch 2015, Levy 2020, Luo 2014, Alkema 2005, and the tyramine and atlas
    papers. Gray 2005, Towlson 2013 and Bhattacharya 2019 came from memory.
  - **Neither consultant:** Lockery & Goodman's News & Views and Liu Q 2018. Claude's own searches also found several
    of the sources above independently.
- **Abstract only:** Mellem 2008 (its full text is behind the bot check, and the publisher forbids XML), Kato 2015,
  Gordus 2015, Levy 2020, Uzel 2022, Towlson 2013, Goodman 1998, Liu Q 2018, Gray 2005, Alkema 2005.
- **Not checked:** Pirri 2009, Kagawa-Nagamura 2018, Dvali 2024, Creamer 2025 (named by Fable).
- **Not searched:** RMD plateaus in later electrophysiology, beyond what Nicoletti and Li cite.
- **Search strings and dates** are in the archived source list.
- **Mismatch noted by a reading agent:** the eLife corollary-discharge paper (Ji et al.) is 2021, not 2019 as
  Fable's list implied.

## What this means for the thread

- **The literature does not show the model's switch in the worm.** It does show three things nearby:
  - a single-neuron two-state membrane property in RMD, intrinsic;
  - persistent command and modulatory states, held by circuits and neuromodulators;
  - a phase-based turn memory spread across the head-steering neurons, in oscillations the probe lacks.
- **Two directions follow, for the owner to weigh. Neither is recommended here.**
  - **Give RMD a plateau.** The nearest biological analogue would need intrinsic conductances in RMD. That is a
    model change and a new question.
  - **Probe with an oscillation.** The worm's demonstrated memory would need a closed-loop or oscillating probe.
    That is a change of task, close to option 2 or 5's behaviour question.
- **Stopping is also open** (option 4). The thread's results would then stand as facts about this model, and this
  check records where they sit against the worm.
