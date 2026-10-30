**Verdict: fix then publish.** The broad conclusion survives: the sources establish several forms of history dependence, but do not establish the model’s particular food-history switch in the worm. Draft 1 overstates some mechanisms, overinterprets negative results, and suggests novelty on an unreliable distinction.

I checked the scope, both first-round reviews, report, reading records and relevant probe code. The two report copies are identical; the records contain 39 sources, 29 full-text retrievals and 386 quote entries. I did **not** independently repeat all 386 exact-match checks. I inspected original full-text passages for nine of the eleven requested sources; my independent checks of Lockery & Goodman’s News & Views and Ouellette relied on substantial search-indexed original-text excerpts because direct access was blocked.

The required fixes are these.

1. **RMD: the recorded plateau is supported; an exclusively intrinsic mechanism is not established.**  
   This affects [the summary](D:/Claude/random/wormWars/docs/memory/M6-3-LITERATURE.md:43), §1’s reading, §7 and the closing.

   Lockery & Goodman explicitly leave open whether synaptic interactions contribute to plateau maintenance. The report acknowledges this in its table, then repeatedly declares the mechanism intrinsic. Nicoletti demonstrates a sufficient intrinsic mechanism **in a fitted model**; its CCA-1 removal is an *in silico* intervention, not experimental identification of the biological maintenance mechanism. Keep those evidential levels separate. [Lockery & Goodman](https://pmc.ncbi.nlm.nih.gov/articles/PMC3951993/), [Nicoletti et al.](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0218738).

   Suggested wording: “RMD exhibits prolonged, resettable plateau potentials. A conductance model reproduces this through intrinsic currents, but the experiments discussed here do not exclude synaptic contributions.”

   The correspondence is represented correctly: it disputes the initial transient’s classification as an action potential while accepting the plateau observation. [Lockery, Goodman & Faumont](https://pmc.ncbi.nlm.nih.gov/articles/PMC3951996/).

   **The scope itself needs a dated correction:** its guard at line 81 already assumes the mechanism is intrinsic. Also date “almost nothing is known” explicitly to 2009.

2. **Dunn: remove “No single neuron carries it,” and correct the RIA interpretation.**  
   [Lines 53–79](D:/Claude/random/wormWars/docs/memory/M6-3-LITERATURE.md:53) and §3 go beyond the evidence.

   Failure of the tested stimulations to bias turn direction does not exclude single-neuron storage. The authors explicitly allow additional neuronal or molecular carriers and leave maintenance necessity unresolved.

   The RIA quotation loses consequential context: immediately after reporting weak **nuclear** correlation, Dunn anticipates strong correlations in RIA’s axonal compartments. Figure 3J also reports improved decoding with individual-neuron features including RIA. Therefore, “It did not track the memory” and “not tracking Dunn’s memory” should go. Neither storage nor its absence follows.

   Describe distributed relative-phase memory as the authors’ supported interpretation, without excluding other carriers. Replace “the one study that shows it” with “the most directly relevant study checked.” Attribute the 30–90-second interval specifically to fictive-turn experiments. [Dunn et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC12829590/).

   Finally, **open loop does not mean incapable of internal oscillation**. Say the present nonoscillatory probe does not assay this mechanism. Hendricks’ compartmental findings and persistence during paralysis are accurately represented. [Hendricks et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC3393794/).

3. **The anatomy section needs qualification and its omitted counterweight.**  
   At [lines 81–83](D:/Claude/random/wormWars/docs/memory/M6-3-LITERATURE.md:81), replace “Only 6% … are functionally connected” with “6% met the study’s stringent detection criterion, q < 0.05.” Randi measures effective propagation through potentially multiple paths. Failure to meet that threshold does not establish disconnection; the paper separately tests evidence for non-connection. Its poor agreement concerns the anatomy-based models evaluated there. [Randi et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC10632145/).

   Leaving Creamer unchecked while repeatedly concluding “anatomy predicts function poorly” produces an avoidably one-sided reading. The explicitly nominated preprint reports substantially better prediction using fitted connectome-constrained dynamics, with shuffled connectivity performing worse. Its indexed abstract is sufficient to require acknowledging the counterpoint; pin the version and reading level. This does not establish C3 as a functional module. [Creamer, Leifer & Pillow, v4](https://www.biorxiv.org/content/10.1101/2024.09.22.614271v4).

   Witvliet’s 43% figure is correctly quoted, but retain the accompanying **16% of chemical synapses** and developmental sampling context in the summary. Delete the suggestion that this could “swamp” sub-percent model effects: connection variability and changes in switch prevalence are different quantities, with no demonstrated conversion between them. [Witvliet et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC8756380/).

4. **Remove the proposed novelty distinction based on input termination.**  
   [Section 5](D:/Claude/random/wormWars/docs/memory/M6-3-LITERATURE.md:187) correctly reports Kunert-Graf’s multistability and long transients. Specify that its highlighted bistability is between a fixed point and a limit cycle. [Kunert-Graf et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC5468412/).

   But your own probe also maintains an external input: `follow()` applies the common final food level throughout the observation period. What ends is the difference between the histories, not all input. [Probe implementation](D:/Claude/random/wormWars/scripts/memory_m1/common.py:183).

   The defensible distinction is that Kunert-Graf demonstrates different attractors from different initial conditions under matched constant drive, whereas this project demonstrates selection through specified input histories. That is a protocol distinction, not yet novelty.

   There is also a directly relevant missing precedent: **Liu et al. 2022**, which develops attractor-based switching in connectome-derived circuits and explicitly discusses maintenance after external input terminates. It also proposes a circuit contribution to RMD plateaus. These are modeling interpretations, not new electrophysiological confirmation. Add it and remove “possibly new” pending a proper novelty search. [Liu et al.](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2022.808824/full).

5. **Preserve the distinction between observations and mechanistic interpretations throughout the readings.**  
   “The other history effects found sit outside the model’s mechanism” is too sweeping. Recurrent feedback, inhibition, electrical coupling and fading dynamics have conceptual overlap with mechanisms available to this model. Missing physiological implementation does not establish wholly different dynamical mechanisms.

   Sordillo’s description of RIM stabilizing opposite locomotor states through different outputs is supported. However, its approximately 15-minute local-search interval is **not** the duration of one maintained RIM state. [Sordillo & Bargmann](https://elifesciences.org/articles/67723).

   López-Cruz supports food-history-dependent reorientation under a common subsequent food-free environment. Qualify “fades”: population behavior changes gradually, but many individuals exhibit abrupt transitions. This is not evidence that each worm contains a smoothly decaying scalar memory. The reported distinction between reversal-associated reorientations and forward-movement turns is supported. [López-Cruz et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC9161785/).

   Ouellette’s “switch” is correctly distinguished from a memory switch. Nevertheless, label the output-routing account a **proposed mechanism**: the discussion identifies unresolved postsynaptic effects. Similarly, do not upgrade Roberts’ modeled reciprocal inhibition to a fully identified maintenance mechanism in §1’s reading. [Ouellette et al.](https://www.eneuro.org/content/5/6/ENEURO.0121-18.2018).

6. **Repair the reading-level and search-record descriptions.**  
   “Full text: read” conflicts with the later statement that this level indicates availability. Use “full text retrieved; relevant passages read” where appropriate, and distinguish direct experimental evidence from secondary reporting. Mellem’s detailed plateau measurements are secondary through Lockery & Goodman in this review.

   The records also need small, concrete repairs:

   - `sources.json` records known-title/DOI retrieval queries, not the broader discovery searches needed to interpret absence claims.
   - `quotes-states-history.txt` has source keys and quotations but no source line numbers, despite the general description.
   - Li’s separately retrieved preprint needs an explicit version/URL entry alongside the batch sources.

   Exact matching verifies transcription. It does not verify context or entailment; the Dunn examples demonstrate that limitation.

For **gaps**, my bounded additional search did not identify a later independent RMD electrophysiology study that settles intrinsic versus circuit maintenance or establishes food-history storage. That is a limited search result, not evidence that none exists. The gap should be recorded as searched, with queries, rather than left “not searched.”

Two additions deserve priority over widening the review indiscriminately: Liu 2022 and Creamer above. There is also material already in the reading records that deserves brief treatment: **Atanas 2023’s recent-action encoding**, with its explicit distinction between decoding past behavior and establishing causal memory use. That would restore some of the scope’s promised emphasis on fading effects. Dunn’s Figure 5L also contains sustained SMDV calcium associated with subsequent turn identity; acknowledge it without calling it a history-set stable equilibrium.

The guards are therefore only partly applied. The routing meaning of “switch” and the prohibition on tick-to-second calibration are preserved. The intrinsic-bistability guard needs correction; the RIA section overinterprets negative evidence; and the summary’s categorical language exceeds the bounded absence claim used elsewhere.

**The closing is underinclusive.** Adding an RMD plateau and designing a phase-sensitive task are possible new projects, but the literature does not compel either. A plateau could be represented phenomenologically without a detailed conductance model, and adding an oscillation alone would not reproduce a memory task.

**My recommendation to the owner is to publish the corrected review and close the switch-focused branch for now.** M6-0 found fading effects in 101 of 102 generation-39 champions. If the owner continues the existing memory thread, the more direct next question is whether those fading states causally contribute to behavior, using the existing champions and validated interventions. A biologically motivated phase-sensitive navigation task could follow as a separately scoped project. I would not add RMD plateaus merely to create a closer resemblance to one literature observation.