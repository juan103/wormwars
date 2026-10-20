**My selection is the amplitude-weighted tail, supported by a head circuit, with the dynamical mechanism still unresolved.** Batch 7 makes that circuit the best structural lead. It does not yet establish an autonomous memory store, or show whether its advantage comes from maintenance, amplification, or access to otherwise ordinary slow dynamics.

As the dynamical advocate, I would prioritize **localized feedback near instability in a minority of genomes**, then **finite-amplitude saturation and read-out alignment**. I would demote global slow modes, global non-normality, and triangle counts. I would not kill time-constant interactions or probe dependence on the checks performed.

I inspected the earlier proposals, spike scripts, saved outputs, brain update and registered probe. I ran no analyses or experiments.

**The family verdicts use “dead” for the specified explanation of this result—not for every conceivable version of the idea.**

| Family | Verdict and evidence | Cheapest remaining kill-check |
|---|---|---|
| **1. Feedback pays the leak; slow modes; ring/line attractors** | **Alive, narrowed to relevant modes and the tail.** Similar median spectral radii weaken a population-wide eigenvalue shift. But N2 has 5.1% with midpoint radius above one, versus 0–0.8%; global maxima need not describe food-excited, turn-visible modes. Exact ring/line attractors remain unsupported. [Batch 3](</D:/Claude/random/wormWars/runs/memory-spikes/batch3.json>) | On genomes carrying most of the late numerator, test whether excited, observable slow/expanding modes predict separation and whether selective disruption removes it. Ordinary contraction in those directions, with the advantage explained entirely by projection, kills the slow-mode account. A continuum of initial histories collapsing to isolated endpoints kills a continuous attractor interpretation. |
| **2. Chains and transient growth** | **Wounded.** N2 is not globally more non-normal by Henrici. Nevertheless, the frozen model predicts ten-tick **full-state growth in 7.4%** of N2 genomes, against 0–0.4% in these nulls. That is an unresolved lead, not evidence specifically for non-normal growth: unstable modes could produce it. Reversal retaining tick-30 share does not exclude short cascades. [Batch 3](</D:/Claude/random/wormWars/runs/memory-spikes/batch3.json>) | Examine actual history-direction propagation in stable genomes and a short pulse response. No excess delayed delivery, directional transfer or transient amplification among the important contributors kills this explanation of the lead. |
| **3. Reservoirs and return; trapped waves** | **Wounded.** The pharyngeal reservoir is **dead as an explanation of tick 30**: its erasure changes essentially nothing. A reservoir within the head remains possible. Neither a localized residual nor many loops demonstrates circulation. [Batch 4](</D:/Claude/random/wormWars/runs/memory-spikes/batch4.json>) | Record contributors every tick and erase candidate compartments after writing. No persistent compartment feeding the output kills reservoir-and-return; no recurring spatial progression kills trapped-wave versions. |
| **4. Switched routes and sequences** | **Wounded, not tested decisively.** Frozen forecasts correlate with retention, but the calculation is not a calibrated forecast of the actual observable. Endpoint localization cannot detect intervening handoffs. [Batch 3 code](</D:/Claude/random/wormWars/scripts/memory_spikes/batch3.py:47>) | Compare frozen gains with ordered, time-varying gains using the correct read-out, then predict independent perturbations. If frozen gains explain the weighted tail and interventions equally well, changing routes are unnecessary. |
| **5. Saturation reshapes the circuit** | **Alive.** Strong localization, amplitude dependence and weaker read-out slopes make this credible. Weak marginal bias correlations do not test it. The pre-tanh result in 03mc concerns P4, not a complete pre-tanh relaxation curve. [03mc results](</D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md>) | Scale separation around a fixed midpoint and compare voltage, activity and output decay. If normalized retention is amplitude-independent and fixed gains explain the effect, finite-amplitude saturation loses its case. Specifically, “saturation removes restoring feedback” dies if the suppressed paths predominantly reinforce separation. |
| **6. Gap geometry and layer matching** | **Wounded as the primary explanation; alive as a modifier.** N2 chemicals retain much of the effect with shuffled gaps and improve with gaps absent. A necessary special N2/N2 pairing is poorly supported. But gaps penalize this SH graph much more strongly, so differential damping remains plausible. [Batch 1](</D:/Claude/random/wormWars/runs/memory-spikes/batch1.json>) | Branch identical ramp-end states with original, shuffled and absent gaps. No distinctive maintenance effect or trace-specific gap damping across several hosts kills the protection account. Whole-probe interventions currently mix writing with maintenance. |
| **7. Time-constant lottery** | **Wounded, unfairly declared finished.** Batch 4 tests one-neuron marginal rank correlations, not interactions between clocks and random feedback. It does not perform the proposed equal-tau or tau-permutation interventions. [Code](</D:/Claude/random/wormWars/scripts/memory_spikes/batch4.py:80>) | Hold signs and biases fixed; permute taus and homogenize them at several sensible common values. Persistence of the N2 advantage under these changes kills heterogeneous clock placement as its explanation. |
| **8. Mixtures and heavy tails** | **Alive; strongest descriptive finding.** The top 5% carry 55.4% of the tick-30 numerator. But N2’s upper quartile also shifts, so “only a handful of bistable brains” is too narrow. [Mixture output](</D:/Claude/random/wormWars/runs/memory-spikes/check_mixture.txt>) | Existing-array decomposition by starting amplitude, retention quantile and late contribution. A broad matched-amplitude shift would kill a **weighting-only** account. A discrete latch-mixture account dies if contributors form a continuous distribution of fading responses without distinct dynamical classes. |
| **9. Read-out geometry; read-out as store** | **Alive for geometry; the eight-neuron store is strongly wounded.** Turn erasure largely rebuilds; removing mutual chemical edges leaves substantial retention. Alternative read-outs weaken the specialness, while full-state medians are ordinary. This favors access to a larger circuit. [Batches 1](</D:/Claude/random/wormWars/runs/memory-spikes/batch1.json>), [6](</D:/Claude/random/wormWars/runs/memory-spikes/batch6.json>) | Decompose activity-norm retention from projection onto turn, especially in numerator-dominating genomes. If excess state persistence accounts for the advantage and projection contributes little, read-out geometry is not the main mechanism. |
| **10. Phase memory** | **Wounded, still possible in a minority.** Nothing supplied establishes repeated trajectories or phase offsets. Settled late genomes cannot all be explained this way; moving contributors might be. | Every-tick full-state recording of late contributors, followed by time-shift alignment. Absence of recurring trajectories, or separation persisting after appropriate phase alignment, kills phase-only memory. |
| **11. Preparation and aging** | **Dead as the leading warm-up artifact over the tested range.** Moving from 100 to 400 warm-up ticks barely changes retention; 25 ticks changes it moderately. This looks more like preparation approaching a reproducible regime than continuing aging. [Batch 1](</D:/Claude/random/wormWars/runs/memory-spikes/batch1.json>) | Rescue would require systematic waiting-time dependence in the important contributors that the aggregate hides. I would not spend the next compute budget here. |
| **12. Probe regime** | **Wounded, not dead.** Food scaling weakens the claim that one accidentally chosen food level explains everything. It does not test pulse-written versus hold-written history, different ramp durations, or different input directions. [Batch 1 code](</D:/Claude/random/wormWars/scripts/memory_spikes/batch1.py>) | A matched-amplitude pulse pair around a shared prepared state. Robust transfer to pulses and another input direction kills the narrow hold/ramp-specific account. Failure would materially narrow the finding. |
| **13. Bilateral sectors** | **Wounded and largely untested.** Bilateral head participation is compatible with it; SH-mirror’s failure shows preserved anatomy alone is insufficient. Independent signs, taus and biases prevent assuming exact symmetry sectors. | Decompose relevant trajectories into bilateral common/difference components and measure cross-sector coupling. No unusual concentration or protection in the predicted sector kills that version. Do not infer sectors from neuron names alone. |

For the owner’s loops specifically: **global triangle-count sufficiency is effectively dead; particular weighted feedback arrangements remain alive.** Raising triangle counts failed, while core-preserving graphs retained the effect with null-level counts. That is stronger evidence than the extrapolated regression.

**The strongest dynamical lead needs a narrower interpretation than “N2 has more unstable brains.”**

Batch 3 evaluates the Jacobian at the **midpoint between histories**, which need not lie on either trajectory. A radius above one there could indicate a separating saddle between two contracting trajectories. It does not establish ongoing instability, chaos, or even growth along the observed difference.

Furthermore, its forecast uses \(c^\top\delta v\), whereas observed turning uses \(c^\top[\tanh(v^\uparrow)-\tanh(v^\downarrow)]\). Their denominators differ too. Spearman correlations of 0.50–0.74 show useful ordering, not accurate prediction of the weighted signal. The missing connection is whether the radius-above-one genomes, the linearly growing genomes and the large late contributors are actually the same genomes. [Calculation](</D:/Claude/random/wormWars/scripts/memory_spikes/batch3.py:47>)

That join is more valuable than another graph-level spectral summary.

**Claude’s leading reading survives, but several sentences should be weakened.**

1. **“The typical genome forgets alike” is a reasonable description of medians, not an equivalence result.** N2’s median is ordinary relative to graph variability, but its 75th percentile is 0.558 versus ensemble medians of 0.403–0.448, with only 0–3 graphs per ensemble reaching it. The upper distribution differs before one reaches the most extreme 5%. Also, batch 4 measures voltage norms; batch 6 measures activity norms after tanh. Both support an ordinary median, but they are different observables. [Mixture output](</D:/Claude/random/wormWars/runs/memory-spikes/check_mixture.txt>), [batch 6 transformation](</D:/Claude/random/wormWars/scripts/memory_spikes/batch6.py:51>)

2. **“Large differences forget less” needs qualification.** The reported correlation is Pearson correlation between **log starting amplitude and a ratio containing that amplitude in its denominator**. It remains negative in N2. The result establishes a weaker negative association than in nulls, not a positive relationship, and it does not quantify the covariance term governing the registered statistic. Conditional amplitude-bin analysis is needed.

3. **Erasing the largest initial differences is not specific evidence of a store.** It removes the most signal. Its larger effect than residual-selected erasure strengthens this objection. Holding the denominator at the intact start is appropriate for measuring lost output, but that quantity is not the decay rate of the remaining trace. Equal-neuron-count random controls do not match erased norm, immediate output loss, or downstream influence. Held-out genomes reduce selection overfitting; they do not remove this mechanistic ambiguity. [Batch 6](</D:/Claude/random/wormWars/scripts/memory_spikes/batch6.py:73>)

4. **Batch 7 establishes conditional preservation, not standalone sufficiency.** Every arm retains N2’s whole gap layer and all chemical autapses. About 27% of original off-diagonal chemical edges remain in the large shuffles. The comparison against hub freezing is meaningful, but “the internal core wiring is enough in an otherwise shuffled graph” should explicitly name that retained background. [Construction](</D:/Claude/random/wormWars/scripts/memory_spikes/batch7.py:29>)

5. **There are two additional implementation qualifications.** “Frozen” protects existing internal edges but does not forbid new internal edges, so it does not freeze the entire induced subgraph exactly. Also, genomes are regenerated from each graph’s edge enumeration: matching seeds do **not** preserve signs on every retained edge. These remain legitimate random-genome comparisons, but they are not surgical interventions on identical signed brains. [Rewiring](</D:/Claude/random/wormWars/scripts/memory_spikes/batch7.py:36>), [genome generation](</D:/Claude/random/wormWars/wormwars/brain.py:214>)

6. **Dissolution simultaneously weakens recurrence and increases exchange with the surroundings.** Each swap removes an internal core edge and an external edge and creates two boundary-crossing edges. The control scrambles external edges without that boundary change. Reduced retention could therefore reflect loss of internal feedback, increased leakage/interference, altered writing, or changed routes to turning. These are distinguishable mechanisms. [Dissolution](</D:/Claude/random/wormWars/scripts/memory_spikes/batch7.py:59>)

7. **“Triangles matter through the core” is not established mediation.** The evidence says total counts are neither an adequate explanation nor a sufficient transplant target. Core density, weight placement, reciprocity, boundary structure and electrical overlap remain bundled. Also, the quoted extrapolation and interval are absent from the saved `check_structure.txt` I read, although the current script contains code to produce them. In any event, a pooled, weak fit extrapolated beyond the null range cannot identify causation.

A concrete competing explanation is **a strongly written, highly observable head circuit with ordinary contraction in most genomes and occasional nonlinear separation**. It predicts that matching initial state separation and output projection will remove much of the apparent advantage. A genuine maintenance mechanism predicts an advantage after those are controlled.

Another is **protection from external interference**, rather than special internal loops. It predicts sensitivity to core-boundary rewiring even when internal recurrence is fixed. Batch 7 does not separate those accounts.

**The registered measure remains well posed. The roadmap should split the questions.**

For \(a_g=|d_g(0)|>0\) and \(r_g(t)=|d_g(t)|/a_g\),

\[
R(t)=\frac{\sum_g a_g r_g(t)}{\sum_g a_g}
=\mathbb E[r_g(t)]
+\frac{\operatorname{Cov}(a_g,r_g(t))}{\mathbb E[a_g]}.
\]

The equality applies to a consistently defined population; excluded small-start genomes need their numerator and denominator contributions reported separately.

This gives three distinct targets:

- **Typical-genome retention:** evidence that ordinary random realizations retain a larger fraction of their signal. Current evidence is weak for a distinctive median and stronger for the upper distribution.
- **Amplitude-weighted retention:** evidence that anatomy puts more late output into realizations carrying substantial signal. This is the registered finding and remains scientifically meaningful.
- **Maintenance of internal separation:** evidence about dynamical retention, separated from writing and observation.

For activity difference \(\delta a=\tanh v^\uparrow-\tanh v^\downarrow\), define
\[
q(t)=\frac{|c^\top\delta a(t)|}{\|c\|\,\|\delta a(t)\|}.
\]
Then, where defined,
\[
\frac{|d(t)|}{|d(0)|}
=
\frac{\|\delta a(t)\|}{\|\delta a(0)\|}
\frac{q(t)}{q(0)}.
\]

That is the direct separation between state persistence and read-out alignment. Compare it **within the genomes carrying the weighted numerator**, not only through population medians.

I would describe the established result as **“N2 retains a larger amplitude-weighted fraction of its turn-history signal.”** “N2 brains decay more slowly” implies more than has been shown. Neither formulation establishes functional memory.

One further bookkeeping point: `trim43` removes the **43 largest tick-30 contributors**, not the 43 genomes classified as long-lived at tick 300. Those are different tests. [Code](</D:/Claude/random/wormWars/scripts/memory_spikes/check_mixture.py:21>)

**I would use this five-step roadmap. Costs below are planning estimates anchored to the saved timings, not new benchmarks.**

1. **Finish the population accounting on the original arrays.**  
   Decompose raw numerator and denominator, amplitude strata, retention quantiles, small-start contributions, and overlap between tick-30 and tick-300 contributors. Compare the actual long-lived class with late-contributor trimming. **Cost:** seconds to minutes of CPU; **exploratory**.  
   **Changes the plan:** a broad within-amplitude shift prioritizes contraction mechanisms; a concentrated contribution prioritizes the dynamical census of that tail. Different early and late contributors require separate explanations.

2. **Record a shared dynamical census across several null graphs.**  
   Save both voltage and activity trajectories, individual turn contributions, state speed and core/periphery separation. Use fresh CPU panels with several graphs per ensemble, then analyze representative large contributors and ordinary controls. Correct the forecast’s read-out; compare frozen operators, time-varying propagation and small independent perturbations. Continue selected cases long enough to distinguish fading traces, separated endpoints and oscillations. **Cost:** approximately 1–2 CPU hours for an initial panel; **exploratory**.  
   **Changes the plan:** if projection explains the excess, stop pursuing a general slow-state claim. If the important genomes have separated contracting endpoints, pursue basin structure; if trajectories align by phase, pursue oscillators; if fixed linear propagation works, avoid elaborate switching models.

3. **Separate writing, maintenance and reading in the identified circuit.**  
   Branch identical saved states. Erase candidate directions at multiple delays with controls matched for erased norm and immediate read-out effect. Test core-only versus periphery-only initial separation. Alter selected feedback or gaps only during maintenance, with all other signed weights held fixed. Include the inexpensive tau controls. Rescue a disrupted trace by reinjecting the proposed state coordinate. **Cost:** roughly 0.5–2 CPU hours; **exploratory**.  
   **Changes the plan:** loss confined to writing or reading revises “store” to access circuitry. Selective loss during maintenance, followed by rescue, justifies identifying a retained dynamical coordinate.

4. **Perform the owner’s transplant as a controlled block replacement.**  
   Start with independently generated hosts. Compare the original weighted core with internally rewired controls matched for internal degrees/density and boundary connections. Include the reverse intervention in N2. Explicitly vary whether N2 gaps and autapses accompany the block. Preserve parameters on unchanged edges and neurons. Measure absolute amplitudes, state retention and weighted read-out retention. Adding neurons through E4s is unnecessary at this stage. **Cost:** approximately 2–6 CPU hours for a modest host panel; **exploratory construction and screening**.  
   **Changes the plan:** transfer only with native boundary placement supports an accessible circuit, not a portable memory module. Transfer only with electrical structure supports a joint-layer mechanism. Equal transfer by internally randomized controls favors density/strength over particular wiring.

5. **Pre-register the narrow surviving mechanism and test fresh draws.**  
   Freeze the core/mode definition, principal contrast, effect threshold, graph sampling and wording before confirmation. Use enough independent hosts to estimate graph variability, fresh genomes, and one pulse-written history or independent read-out to delimit generality. Retain the registered ratio-of-means alongside the mechanistic endpoint. **Cost:** benchmark first; potentially several GPU hours or substantially longer on CPU. **Confirmatory: committed and pushed before running, under the repository’s rules.**  
   **Changes the plan:** failure of transfer or maintenance specificity rejects that mechanism even if the original Q-D effect replicates. Failure only on the new probe narrows its scope.

**The crazy idea that has gained plausibility is a small head circuit with several history-selectable states—a distorted, pinned relative of the owner’s continuous attractor.**

Most random sign realizations would contract normally; some would acquire a shallow bottleneck or several separated endpoints. That could jointly produce an ordinary median, a consequential tail, localized residuals, and an expanding midpoint between histories.

This is more plausible now than a literal ring attractor, but remains a hypothesis. The decisive observation would be several histories converging to different, perturbation-resistant endpoints under identical final input, with the relevant state organization transferring with the circuit. A ring or line would require the additional evidence of a continuous coordinate with restoring dynamics transverse to it. Neither loops nor a radius above one supplies that evidence.