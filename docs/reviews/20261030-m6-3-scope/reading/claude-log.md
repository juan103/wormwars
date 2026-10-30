# Source log (M6-3), Claude's own check

Levels: full text / abstract / snippet / secondary (via another source) / wrong.

## RMD bistability
- Mellem, Brockie, Madsen, Maricq 2008, Nat Neurosci 11:865-867, doi 10.1038/nn.2131, PMID 18587393, PMC2697921.
  PMC blocked (reCAPTCHA); Europe PMC fullTextXML 500. Level so far: SNIPPET (search result quotes: "These neurons
  resemble Schmitt triggers because their potential state appears to be bistable"; "54 of 98 RMD action
  potentials"; Ca2+ dependent; never in AVA, n=10). Also SECONDARY via Nicoletti 2019: RMD "regenerative plateau
  potentials ... with a bistable resting potential [13]"; "absence of full repolarization" in whole-cell recordings;
  depolarized post-stimulus state disappears in cca-1 ("as shown by experiments [13]").
- Nicoletti et al. 2019, PLoS ONE, doi 10.1371/journal.pone.0218738, PMC6602206. FULL TEXT (Europe PMC XML).
  Conductance model fitted to Mellem's current clamp; two stable equilibria (~-70 and -47 mV) without input,
  switched by transient current; CCA-1 (T-type) and leak set the bistable range. Cites Lockery & Goodman 2009 [58]
  for "the plateau potential and the bistability ensure robustness and resilience to noise by storing the sign of
  the most recent input" (that phrasing is Nicoletti's paraphrase of [58]; [58] itself not yet read).
- Lockery & Goodman 2009, "The quest for action potentials in C. elegans hits a plateau", Nat Neurosci 12:377-378,
  doi 10.1038/nn0409-377. NOT YET READ.
- Critique: "First report of action potentials in a C. elegans neuron is premature", Nat Neurosci 12:366 (2009),
  and Mellem et al. reply (nn0409-366). NOT YET READ.

## RIA
- Hendricks, Ha, Maffey, Zhang 2012, Nature (compartmentalized calcium, head movement). ABSTRACT (Consensus).
- Hendricks & Zhang 2013, Worm (review). ABSTRACT.
- Ouellette et al. 2018, eNeuro, gate-and-switch. ABSTRACT. "a switch that routes RIA synaptic output to dorsal
  or ventral head motor neurons" (a routing switch tied to head orientation, not a history memory).

## SMD / head motor circuit
- Kaplan, Salazar Thula, Khoss, Zimmer 2020, Neuron 105:562, PMC7014571. Downloaded (Europe PMC); to read.
- Li et al. 2026 Curr Biol (bioRxiv 2024.11.18.624064): "RMD contributes to head casts, SMD sustains bending
  states". ABSTRACT.
- Huo et al. 2024 PNAS: SAA; RIM "an integrating neuron that helps maintain a behavioral state". ABSTRACT.
- Sakata & Shingai 2004, Network: model of head swing. ABSTRACT.

## Updates
- Mellem 2008: now ABSTRACT (Europe PMC): "certain neurons in C. elegans fire regenerative action potentials. These
  neurons resembled Schmitt triggers, as their potential state appears to be bistable. Transitions between up and
  down states could be triggered by application of the neurotransmitter glutamate or brief current pulses."
  Abstract does not name RMD; RMD named in snippets and in Nicoletti 2019 (secondary). Full text: PMC copy behind a
  bot check; E-utilities: publisher forbids XML. NOT read in full.
- Lockery & Goodman 2009 N&V (PMID 19322241, PMC3951993): ABSTRACT: "plateau potentials introduces the possibility
  of digital neural codes"; noise from single channels makes classical APs unworkable. Full text not available.
- Lockery, Goodman, Faumont 2009 correspondence "First report of action potentials in a C. elegans neuron is
  premature" (PMID 19322234): TITLE ONLY (no abstract). Content not verifiable. Mellem reply (same issue): not read.
- Hendricks et al. 2012 Nature 487:99 (PMC3393794): FULL TEXT (E-utilities, OA). RIA's axon compartments track
  ventral/dorsal head bends, driven by SMDV/SMDD (cholinergic, GAR-3, intracellular stores), persist in
  levamisole-paralysed animals; glutamate-dependent synchronous (whole-axon) responses to odour: IAA-off evokes
  influx then efflux, IAA-on efflux then influx (transient); compartmental activity is corollary discharge;
  gar-3 mutants: deeper head bends. No persistent or bistable state reported.
- Ouellette et al. 2018 eNeuro (PMC6325537): downloaded FULL TEXT; to read.
- Kaplan et al. 2020 Neuron (PMC7014571): FULL TEXT. Nested hierarchy: ~0.05 Hz brain-wide cycle drives forward/
  reverse; SMD oscillators drive head casts within forward state (SMDD/V antagonistic), persist in immobilised
  animals (intrinsic); SMD peaks at reverse-to-forward transitions; AIB/RIM candidates for switching SMD pattern.
- Luo et al. 2014 Neuron 82:1115 (PMID 24908490): ABSTRACT. Salt set-point memory encoded in ASER temporal activity;
  interneurons downstream encode movement decisions.
- Gordus et al. 2015 Cell: ABSTRACT. AIB response depends on AIB-RIM-AVA network state at stimulus time.
- Lopez-Cruz et al. 2019 Neuron: ABSTRACT. Local search after food removal, "multimodal, distributed short-term food
  memory", decays to global search over several minutes; glutamatergic sensory neurons + MGL-1 on integrating
  neurons.
- Ouellette et al. 2018 eNeuro (PMC6325537): FULL TEXT. "Gate and switch": sensory responses in RIA gated by head
  orientation; "switch" = differential mCa2+ between RIA's nerve-ring compartments routing output dorsal/ventral.
  Odour removal during a head bend triggers rapid contralateral head withdrawal within ~2 s, RIA-dependent. Not a
  history memory; the word "switch" means routing.
- Liu H et al. 2018 Neuron 97:390 (PMID 29290549): ABSTRACT. Sensory-evoked (cholinergic, ACh-gated channel) and
  motor (muscarinic) signals converge on RIA's two axonal domains; asymmetric outputs bias trajectory (steering);
  "Experience alters the sensorimotor integration".
- Kato S et al. 2014 Neuron 81:616: ABSTRACT. AWC tracks odour fluctuations with subsecond precision; ASH integrates
  over seconds; linear biphasic filters.
- Iino & Yoshida 2009 J Neurosci 29:5370: ABSTRACT. Weathervane (gradual curving) and pirouette mechanisms; ASE, AIZ.
- Kato et al. 2015 Cell 163:656: ABSTRACT. Brain-wide cyclic state maps to motor command sequence.
- Flavell et al. 2013 Cell 154:1023: ABSTRACT. Long-lasting roaming/dwelling states set by serotonin (MOD-1) and PDF;
  "slow temporal dynamics of this neuromodulatory circuit supplement fast motor circuits".
- Liu Q et al. 2018 Cell 175:57: ABSTRACT. AWA fires calcium all-or-none action potentials (EGL-19, SHK-1); natural
  odours likely induce AWA spiking. (AWA is one of the model's food inputs.)
- Li P et al. bioRxiv 2024.11.18.624064 (Curr Biol 2026): FULL TEXT via fetch extraction (first 100k chars). Abstract
  "SMD maintain bending states" (Consensus abstract text said "sustains"). Bistability of SMD inferred from behaviour
  phase-space ("two nearly symmetrical clusters, suggesting bistable dynamics"), not recorded; RMD "bistable ...
  according to electrophysiological measurements" citing prior work; model with hysteresis. No direct persistent
  activity recording.

## After round 1 (2026-10-30 evening)
- Batch (batch.py, Europe PMC search + fullTextXML / NCBI efetch OA subset; searched 2026-10-30): 39 sources,
  full text for 29 (sources.json). Author manuscripts (NIHMS) come through efetch.
- Lockery, Goodman, Faumont 2009 correspondence: FULL TEXT (efetch). RMD events are "graded regenerative
  potentials", not action potentials; "approximately half of these events were followed by a stable plateau
  potential"; "This is the first demonstration of plateau potentials in a C. elegans neuron"; plateau potentials
  occur spontaneously; recorded "in situ".
- Lockery & Goodman 2009 N&V: FULL TEXT (efetch). "A brief pulse of positive current in an RMD neuron (or a puff of
  glutamate) elicited a depolarization of more than 30 mV that was stable for at least 1 min ... could be
  terminated by a brief pulse of negative current. Thus, RMD has two stable resting potentials, one near -70 mV and
  one near -35 mV." Spontaneous shifts observed. Na+ and Ca2+ current. Hypothesis: "plateau potentials might support
  a digital coding scheme in which neuronal state (depolarized or hyperpolarized) stores the sign of the most recent
  synaptic input." "almost nothing is known about either function [pattern generation, short-term memory] in C.
  elegans". Open: whether plateau is intrinsic or partly synaptic.
- Mellem 2008 itself: still ABSTRACT only. Its details reach us through Lockery & Goodman (secondary, but by experts
  who reviewed the data).
- Consultant-only sources: Astra-only: Dunn 2025, Ji 2021, Goodman 1998, Yeon 2018 (also Fable), Kramer 2026 (also
  Fable). Fable-only: Sordillo 2021, Roberts 2016, Wang 2020, Alkema 2005, Pirri 2009, Kagawa-Nagamura 2018, Chen
  2024, Levy 2020, Larsch 2015, Ji 2019, Atanas 2023, Kunert-Graf 2017, Izquierdo & Beer 2013, Randi 2023, Dvali 2024,
  Creamer 2025, Uzel 2022, Witvliet 2021, Shen 2016, Huo 2024 (also Claude). Both: Mellem, Lockery 2009 corr,
  Hendricks 2012, Liu 2018, Ouellette 2018, Kato 2014, Gordus 2015, Lopez-Cruz 2019 (Astra) ...

## Round 2 checks (2026-10-30, late)
- Dunn 2025: tetramisole 5 mM in methods (Fable's doubt did not hold); RIA sentence continues "though based on prior
  studies, we would expect that RIA subcompartment calcium dynamics ... would exhibit strong negative and positive
  correlations" (Astra right); "Inclusion of several individual headswing neuron features (SMDD, SMDV, RIA) improves
  prediction accuracy"; discussion "five different neuron classes/subcompartments within the headswing complex can
  terminate reversals yet do not bias turn direction"; SMDV "prolonged and sustained depolarization for ventral but
  not dorsal TURNs" (figure legend).
- Larsch 2015: "in a five hour experiment" (Fable's "minutes" did not hold). Roberts 2016 L47 legend: AVA trace.
- Lopez-Cruz 2019: "51% of animals appeared to have a single abrupt transition"; forward-movement reorientations
  similar between local and global search (time-independent), not tested against food history.
- Lockery & Goodman N&V: "suggest that RMD plateau potentials depend on a current carried mainly by Na+ and Ca2+
  ions".
- Liu J et al. 2022 Front Neurosci (PMC9085386), full text: rate model on connectome; "as long as the state is in the
  domain when external input terminates"; RMD plateau "may also be explained by multiple fixed points", RMDL-RMDR
  excitatory synapses.
- Creamer, Leifer, Pillow bioRxiv 10.1101/2024.09.22.614271: abstract (82%; shuffled connectome much lower).
- Cecere et al. bioRxiv 2021.04.09.439242 v2: abstract via page fetch; SMDD/SMDV clusters named; SMD timing not in
  abstract.
- Li et al. bioRxiv 2024.11.18.624064 abstract (Europe PMC): "SMD sustains bending states"; "RMD subgroups displayed
  unique calcium dynamics correlated with rapid head movements and slow transitions between behavior states".
- Nicoletti 2024 PLoS ONE: abstract ("bistable responses" among measured neurons; models AIY, RIM, AVA, VA, VB, VD).
- Discovery searches for later RMD electrophysiology (Europe PMC): (ABSTRACT:"RMD" OR TITLE:"RMD") AND
  (ABSTRACT:"patch" OR ABSTRACT:"current clamp" OR ABSTRACT:"electrophysiolog*" OR ABSTRACT:"plateau") AND
  ("elegans") -> 0; ("plateau potential" OR "plateau potentials") AND "elegans" -> 86, RMD items only Nicoletti 2019,
  Liu J 2022, Lockery 2009 x2. Earlier: web search "C. elegans RMD neurons calcium imaging head movement plateau up
  state in vivo" -> nothing on RMD.
- Discovery searches before the batch (round 1): Consensus "RIA interneuron compartmentalized calcium head bending
  C. elegans"; web "Mellem Brockie Madsen Maricq 2008 ..."; web "SMD neurons C. elegans head bending persistent
  calcium Kaplan ..."; Europe PMC RMD and RIA memory queries (see q.py runs above).
- check_report.py: 50 quoted passages in draft 2, all found; sabotage (one quote altered) caught.
