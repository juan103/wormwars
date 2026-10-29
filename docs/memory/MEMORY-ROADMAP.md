# Why does N2's history difference decay more slowly? A roadmap

*Draft 2.1, 20 October 2026. Written by Claude as the master of ceremonies of a three-round brainstorm. Draft 1
(archived in `docs/reviews/20261020-memory-select/`) was reviewed by Astra 6 and Fable 5.1, who both said "revise".
Draft 2 took their corrections, and both agreed to it with small fixes, which draft 2.1 makes. The rounds, the
selection and the review are archived in `docs/reviews/20261020-memory-{diverge,build,select}/`. A living plan, not a
pre-registration. Everything under "What the ceremony found" is exploratory.*

## The question

03mc found that N2's random brains keep 0.436 of their history difference 30 ticks after the ramp, against null
ensemble medians of 0.255 to 0.291 (Q-D, registered). The owner asked why, and wanted to answer it with a
different kind of ceremony: first a blind, divergent round ("a bit of crazy ones"), then building on each other's
ideas, then a critical, honest selection.

## How the ceremony ran

| Round | What happened | Who |
|---|---|---|
| 1, diverge, blind | 5 sources, about 60 ideas, written without seeing each other | the owner (ring attractors, waves trapped in loops, transplanting), a ChatGPT roadmap the owner supplied, Claude (13), Fable 5.1 (17), Astra 6 (18) |
| 2, build | Families, hybrids, new ideas, and the cheap experiments that would split the families. Fable grouped them in 13 families, Astra in 16; the selection used Fable's. | Fable, Astra |
| Between 2 and 3 | 7 batches of cheap CPU checks, chosen from round 2's experiments, plus analyses of 03mc's arrays (`scripts/memory_spikes/`, outputs in `runs/memory-spikes/`) | Claude |
| 3, select | A verdict for every family. Astra advocated the dynamical families and Fable the structural ones. Both prosecuted Claude's leading reading. Each proposed a roadmap and one crazy idea. Claude wrote its own selection before reading theirs. | Fable, Astra, Claude |
| After 3 | Batch 8 checked both crazy ideas and the join that both had asked for. Then both reviewed draft 1 of this roadmap. | Claude; Fable, Astra |

## What the ceremony found (exploratory)

**Where the numbers come from.**
- Some analyses use 03mc's own committed records and local arrays: the median ranks, the amplitude correlations, the structural regressions and the settled census (`check_mixture.txt`, `check_structure.txt`, `settled_census.json`).
- Everything else uses fresh CPU panels of random genomes, mostly with one graph per null ensemble.
- Graphs within an ensemble differ a lot, and N2's own share moves between panels: 0.469, 0.396 and 0.504 on three panels. Treat single comparisons as leads.

1. **The typical N2 brain is not shown to forget more slowly.**
   - **N2's median per-genome retention is ordinary relative to graph variability:** 17 to 46 of 128 graphs per ensemble are at or above it.
   - **The tick-30 voltage-norm retention has similar observed medians** in N2 and two nulls: 0.197 against 0.192 and 0.200. No equivalence test was run, and these are tick-30 ratios, not fitted decay rates.
   - **What is extreme is the registered, amplitude-weighted share.** N2's upper quartile of per-genome retention is high (0.558; 0 to 3 of 128 graphs per ensemble reach it), and the largest tick-30 contributors carry an unusual part of the signal. These two selections overlap, but how much has not been measured.
   - **The amplitude-retention association is weaker in N2:** −0.13, against −0.39 to −0.42. It is negative in both, and a Pearson correlation of log amplitude against a ratio that contains the amplitude is a crude measure of it.
   - Astra's wording is the accurate one: **N2 retains a larger amplitude-weighted fraction of its turn-history signal.**

   *Corrected 2026-10-20 (M1, D350; [`M1-RESULTS.md`](M1-RESULTS.md)). "What is extreme is the registered,
   amplitude-weighted share" is misleading. On 03mc's arrays the exact decomposition, eligible share = E[r] +
   Cov(a, r)/E[a], shows N2's unweighted mean per-genome retention to be extreme too (0.586, against ensemble medians of
   0.370 to 0.412; none of the 640 graphs reaches it), and the amplitude weighting lowers N2's share (covariance term
   −0.152, against medians of −0.111 to −0.128). N2's retention is above the median graph's in every amplitude stratum
   with common support, and its largest contributors carry much of the lead. "The typical N2 brain is not shown to
   forget more slowly" still holds for the median genome. The "weaker amplitude-retention association" above is a
   Pearson correlation of log a against r; it does not carry over to the exact covariance term, which is more negative
   in N2.*
2. **A minority of brains may be multistable, in N2 and in some nulls.** This is batch 8 (512 genomes, seed 7500, follow 300) read against 03mc's committed census.
   - **Expansion at the midpoint.** In 21 of 512 N2 genomes, the one-tick Jacobian has spectral radius above 1 at the midpoint between the two histories' ramp-end states. Only 6 of 512 have a radius above 1 at a history's own ramp-end state. Their overlap with the 21 was not recorded.
   - **The settled genomes.** 8 N2 genomes meet the script's "settled" rule: a start difference of at least 10⁻³, more than 10% of it left at tick 300, and a change between ticks 250 and 300 of less than 2% of the start difference. All 8 are among the 21, and none of the 8 has an own-state radius above 1.
   - **None of these states was verified as a fixed point.** The ramp-end states and their midpoint are still relaxing, so the pattern is *consistent with* a separating saddle between two stable states. It does not establish one. The rule is also weaker than 03mc's, which checks the full state over the last ten ticks.
   - **Share of the signal:** the 21 carry 39% of the eligible genomes' tick-30 numerator, and the 8 settled genomes 25%.
   - **The leading eigenvector at the midpoint concentrates on the head core.** Over the 21 genomes it puts 92% of its mass on the 30-neuron head core and 67% on RMD and SMD. N2's other genomes already put 43% and 24% there, and the core list was chosen by start difference, so part of this restates how the core was chosen. It also says nothing about how strongly the histories excite this mode.
   - **No oscillatory enrichment.** 2 of the 21 leading eigenvalues are complex, against 15% of N2's other genomes. Fable's prediction of oscillatory instability is not observed; its other half, an eigenvector on RMD and SMD, held.
   - **The nulls also settle with separation.**
     - In 03mc's committed census, N2 has 26 settled genomes with separation left, of 1977 eligible. That is high but not unique: 3 to 7 of 128 graphs per ensemble reach it, and single null graphs reach 28 to 126.
     - Within every ensemble, graphs with more settled genomes have a higher tick-30 share (Spearman 0.36 to 0.48; `settled_census.json`).
     - In batch 8, SH-class-2030000 has 9 midpoint-expanding and 6 settled genomes, and a share of 0.483 against N2's 0.504; SH-2010000 has none.
     - So settling is associated with a high share in general (an association, not a demonstrated cause). N2 is enriched in it without being unique. What sets N2 apart may be where its settling happens, or its weight in the signal, or something else.
3. **The structure that matters looks like a head core, not triangle counts.**
   - **Raising three shuffles to N2's triangle counts did not recover N2-level retention** (batch 2). The values moved both ways, for example 0.353 to 0.264 and 0.234 to 0.282.
   - **N2's core keeps the lead in a mostly shuffled graph, conditionally** (batch 7; three graphs per arm, each on two panels):
     - with 73% of N2's off-diagonal chemical edges shuffled and the head core's 199 internal edges frozen, the mean is 0.482, at null-level triangle counts;
     - freezing a hub set with about as many internal edges (202) gives 0.343;
     - every arm keeps N2's whole gap layer, its autapses and about 27% of its original chemical edges;
     - so this is conditional preservation, not standalone sufficiency.
   - **Dissolving the core costs part of the lead:** 140 swaps, which remove 70% of the core's internal edges and add boundary edges, give 0.363; scrambling the periphery as much gives 0.454.
   - **The core's members:** RIA, RIM, RIB, AIB, AIZ, AIY, RMD, SMD, SMB, SIA, SIB, AVE, and some of the AWC and AWA sensory neurons.
4. **Weakened, each for the specific version tested.**

   | Idea | What the checks found |
   |---|---|
   | a numerical artefact | 16 substeps against the baseline 32 give very similar aggregate retention. That does not rule out numerical effects on the rare classes in finding 2. |
   | warm-up length, food level | The N2-SH lead holds from 25 to 400 ticks of warm-up and from half to twice the food level. Pulses, other ramp durations and other input directions are untested. |
   | a time-constant lottery | Single-neuron correlations of tau or bias with retention are small: at most 0.10 in N2, and 0.12 in SH-class. Interactions, tau permutation and equal taus are untested (Astra). *Annotated 2026-10-20 (M1): with equal taus the lead survives (92% of the intact lead); the permutation diagnostic correlates 0.30 to 0.43 in N2 and the nulls alike.* |
   | a pharyngeal reservoir | The pharynx keeps its own difference longest, but erasing it does not change the tick-30 read-out. |
   | a network-wide slow mode, or transient growth | Spectra and non-normality are as in the nulls. *Annotated 2026-10-20 (M1): at the genome level, under the frozen ramp-end Jacobian, 4.8% of N2's eligible genomes grow transiently with radius below 1 and carry 30% of the tick-30 numerator, against 0 to 0.6% (and at most 4.8% of the numerator) in the five null graphs sampled. The transient-growth kill is not rejected; one graph per ensemble is a small reference.* |
   | the eight read-out neurons as the store | Erased, the signal regrows to about 82% from outside the eight. Where outside is not isolated. |
   | gap junctions | The chemical layer carries most of the effect, and turning gaps off lengthens memory in N2 and in the one SH graph tested. Their different penalties (0.07 for N2, 0.19 for SH) could still contribute to the gap between graphs. |
   | triangle counts as such | Not sufficient; loops in particular weighted arrangements are untested. |

5. **The reviewers' objections, and where the plan takes them up.**
   - **The core was selected on the result** (Fable). M3 defines a core from the anatomy alone.
   - **Writing, holding and reading are not separated** (both). M4 intervenes during the hold only.
   - **Persistence and alignment are not separated** (Astra). The output's retention factors into the persistence of the activity difference and its alignment with the turn read-out; M1 measures both in the genomes that carry the signal. *Annotated 2026-10-20 (M1): measured on all eligible genomes, a-weighted; the alignment part of N2's excess is negative, and persistence carries all of it (D2 does not fire).*
   - **Batch 3's linear forecast projects the voltage, not the tanh output** (Astra). M2 corrects the observable.
   - **Response amplitude is untested** (Fable, using Astra's round-2 design). M1 scales it. *Annotated 2026-10-20 (M1): scaled; D1 is inconclusive on its coverage condition, and most of the lead survives every amplitude match that could be made.* *Annotated again 2026-10-20 (M1 amendment 1, D352): with smaller k on N2, D1's conditions are met on the a basis and it does not fire: at matched amplitude across graphs, f = 1.01 and 1.03, so the within-strata lead survives whole.*
   - **Erasures conflate location with amount** (both). M4 matches controls for erased norm and immediate output effect.
   - **The spike rewirings are not 03's samplers** (Fable): they keep the parent's autapses and carry each weight with its edge. Genomes are drawn per graph, so the same seed does not give the same signed brain, and "frozen" protects the core's edges without forbidding new internal ones (Astra). M4 adds 03's conventions and paired genomes.
   - **Dissolution changes two things at once** (Astra): internal edges go and boundary edges come. M4 separates them.

## What the owner's ideas became

- **Ring attractors:** batch 8 and 03mc's census suggest that a minority of brains, in N2 and in the nulls, may hold the
  history in separate states: a discrete, pinned relative of a ring. Whether there are two states, several, or a
  continuum is untested, and that is M2's question.
- **Waves trapped in loops:** total triangle counts are not sufficient. Loops in particular arrangements inside the
  head core remain possible; M4 separates the core's wiring from its density.
- **Transplanting:** M4 screens it and M5 tests it. The core-frozen shuffle already worked as a first, conditional half-transplant.

## The roadmap

Steps M1 to M4 are exploratory and run on the CPU; M4 includes an exploratory transplant screen. M5 is the pre-registered test.
**Decision points:** M1's amplitude and alignment accounting, M2's share of the lead from settling, M4's
maintenance specificity, and M5's portability. A pivot needs its result replicated on a second panel or on several
graphs first. **Costs** are extrapolated from the spike timings, not benchmarked: about 2 minutes per 1024 genomes
with 100 ticks of follow-up, and about 6 minutes per 512 genomes with 300 ticks and three Jacobians.

**M1. Accounting, amplitude and the cheap kills** (CPU; seconds on 03mc's arrays, then about 2 hours without
Jacobians; exploratory).
- **Population accounting on 03mc's arrays** (Astra):
  - split the registered share into the mean per-genome retention plus cov(amplitude, retention) / mean amplitude, overall and within amplitude strata;
  - report the small-start genomes' numerator and denominator contributions separately;
  - measure the overlap of the tick-30 and tick-300 contributors;
  - trim the nulls' top contributors as N2's were;
  - use 03mc's settled census per genome as a proxy for settling.
- **Persistence against alignment** (Astra): in the genomes that carry the signal, split output retention into activity-norm retention times the change in alignment with the turn read-out.
- **Fresh panels:**
  - several randomly sampled graphs per ensemble, kept apart from deliberately selected high-retention and high-settling graphs, with graph-to-graph variability reported and not only panel errors;
  - the definition of settling fixed in advance: 03mc's full-state criterion, primary.
- **The amplitude arm:** scale the ramp-end difference by 0.25, 0.5 and 2 around the midpoint (Astra's round-2 design, pressed by Fable), reporting the actual state and output amplitudes. Amplitude dependence would not by itself mean that response size explains the lead, because the choice between basins can itself depend on amplitude. The comparison that matters is at matched amplitude across graphs.
- **The cheap kills from round 3, moved here because they cost seconds to minutes:**
  - complement erasure, of everything outside the core;
  - the gap dissipation ratio of the difference;
  - the left-right antisymmetric share;
  - the tau-permutation and equal-tau controls;
  - growers with radius below 1, and the forecast correlation without the radius-above-1 genomes (Fable).
- **M3's anatomy predictor runs here too** (minutes).
- **Changes the plan if:**
  - the lead vanishes at matched amplitude across graphs: the focus moves to the size of the response;
  - the alignment term carries the excess: the focus moves from a store to read-out geometry.

**M2. A validated dynamical census** (CPU; a small pilot first, then several graphs per ensemble; hours with Jacobians; exploratory; Astra steps 2 and 3, Fable step 2).
- **The pilot,** on the genomes that carry the signal and ordinary controls:
  - every-tick full-state recording;
  - late-window convergence by 03mc's criterion;
  - Jacobians at candidate equilibria, not at relaxing states;
  - return after small perturbations;
  - the linear forecast corrected to the tanh output;
  - representative classifications repeated at finer integration.
- **Classes:** several discrete states, fading, oscillating, and unresolved. Within the pilot, write a family of histories (ramp starts between 0.25 and 1.75 of the final level) and see whether end states cluster or form a continuum. A continuum of finite-time end states could also be slow fading. *Annotated 2026-10-20 (M2 pilot, D354; [`M2-PILOT-RESULTS.md`](M2-PILOT-RESULTS.md)): every check passed. From nine ramp starts, every "separate states" genome reaches exactly two stable roots, switching once, and every sampled fading genome one; no continuum was seen. M1's settling cohort consists of separate-states genomes (111 of 112), and no persistent oscillation was confirmed.*
- **Then the census:** 03mc's within-ensemble association between settling and share rests on the minority of graphs with any settled genomes (the median count is 0), so the census tests it rather than inheriting it. It covers randomly sampled graphs from each ensemble, the high-settling null graphs (81 to 126 settled genomes in 03mc), and batch 7's core-frozen and hub-frozen graphs. Do the core-frozen graphs keep N2's settling and its location, and do the hub-frozen graphs lose it?
- **The split:** how much of N2's excess over the nulls is settling, and how much is graded slower fading in large-amplitude genomes.
- **Changes the plan if:** settling explains little of the excess. The graded part then becomes the main target, with saturation and gap damping as its candidates. *Annotated 2026-10-21 (M2 census, D356; [`M2-CENSUS-RESULTS.md`](M2-CENSUS-RESULTS.md)): every check passed. At tick 30 the split's reading is "inconclusive" on both of N2's panels: separate states carry 0.47 (0.28 to 0.67) and 0.35 (0.14 to 0.55) of N2's mean lead over 30 reference graphs, fading 0.44 and 0.64. So the branch is not taken; "little" is excluded only at seed 7600. Descriptively, separate states enter by N2's having more of them, fading by retention (N2's fading genomes keep 0.38 and 0.40 at tick 30, the reference's median 0.27); at tick 300 separate states carry most of the lead. The core-frozen shuffles have 9, 17 and 26 separate-states genomes (N2: 15 and 13), located on the core as in N2, and its fading retention; the hub-frozen shuffles have fewer separate states (one of three keeps N2-level S(30)) and retention near the reference's. 03mc's within-ensemble association stays untested (six graphs per ensemble).*

**M3. A core defined without the result** (CPU, minutes for anatomy and existing arrays; exploratory; Fable step 3).
- **Define the core from the anatomy alone,** for example the turn read-out's two-step in-neighbourhood ranked by internal density, plus a write-read path measure. Correlate them within ensembles with the upper quartile, the settled count and the share across the 640 03mc graphs.
- **Inspect the top two to five graphs of each ensemble** by share and by settled count: what do they share with N2?
- **No veto** (Astra). A weak correlation rejects that predictor, not the existence of a structural handle, and it does not cancel a controlled transplant. Formulas chosen after looking at results are exploratory choices, so they are frozen before validation on graphs not yet used. *Annotated 2026-10-22 (D357; [`M3-NOTE.md`](M3-NOTE.md)): M3 closed as a completed screen. M1's part C defined and froze the predictors and the anatomy core C3 and found no strong within-ensemble association; against M2's census measures they add only weak to moderate associations over 30 graphs. N2 lies outside the nulls' range on every predictor, so within-ensemble variation cannot test N2's own density. C3 goes to M4.*

**M4. Write, hold, read; dissection; a transplant screen** (CPU, several hours; exploratory; Astra steps 3 and 4, Fable step 4).
- **Hold-only interventions on branched identical states:**
  - cut core edges, or switch gap junctions off, during the hold only;
  - erasures matched for erased norm and immediate output effect, at several delays;
  - re-injection of a proposed state coordinate, with a rescue that must persist through a later delay;
  - write-only and read-only comparisons, so a hold intervention that only blocks delivery is not mistaken for a store;
  - the internal separation measured throughout, and a common read-out condition restored before reading, so storage and delivery are told apart.
- **Paired genomes:** unchanged edges keep their signed parameters across rewired graphs.
- **Core dissection.** Core-frozen shuffles with one change each:
  - internal edges rewired within the core at fixed degrees;
  - internal weights permuted;
  - reciprocal pairs broken;
  - only the sensory half frozen, or only the motor half;
  - the boundary rewired with the internal edges fixed (Astra's "protection from interference" reading).

  All of these run under 03's sampler conventions as well as the spikes'.
- **A pulse-written history and another input direction,** to see how far the probe matters (Astra).
- **An exploratory transplant screen:**
  - exact block replacement into independently generated hosts;
  - with and without N2's gap junctions and autapses;
  - untouched parameters preserved;
  - placement away from the read-out with an independent way to observe the state.
- **Output:** the smallest successful structure among those tested. *Annotated 2026-10-24 (M4d plan, D363; [`M4D-PLAN.md`](M4D-PLAN.md)): chosen after M4c by consensus (Claude, Astra, Fable). Staged: all of C3's chemical block first, into ten fresh hosts (two per ensemble), against controls of its edge count, weights and autapses (random positions, rewired at fixed degrees with and without its reciprocal pairs, its edges with shuffled weights) and with N2's gap junctions; paired genomes, every genome classified with no eligibility floor, hosts as the unit. Smaller blocks and placement away from the read-out wait for a second stage, planned after this reading.* *Annotated 2026-10-25 (M4d results, D364; [`M4D-RESULTS.md`](M4D-RESULTS.md)): "Unresolved (the unresolved genomes decide it)". N2's C3 block raises the share of separate-states genomes over the intact host in all ten fresh hosts (counted 0.04% to 0.62%; robust over every assignment of the unresolved genomes), but its rewired copies at the same degrees reach 0.51%: on the counted genomes a wiring advantage of 0.004 is excluded, over the unresolved genomes it is not. No successful structure beyond the block's size, weights and degrees is shown, so the second stage is not drafted; the thread's direction goes to the owner.* *Annotated 2026-10-26 (M4e plan, D367; [`M4E-PLAN.md`](M4E-PLAN.md)): the owner chose a study of what a dense block carries (D365). M4e crosses the edge count and the total weight of equal-magnitude random blocks on C3's neurons in ten fresh hosts, with N2's weights (W), N2's labelled degrees (K) and N2's block (T) beside them, two block draws per host, and a second, longer classification of the genomes that matter; agreed with both reviewers in two design rounds and three rounds on the plan and code.* *Annotated 2026-10-27 (M4e results, D368; [`M4E-RESULTS.md`](M4E-RESULTS.md)): at equal magnitudes and N2's total weight, spreading the weight over N2's 260 edges lowers the share of separate-states genomes against the host's own edge count (Δ_count "lowers", its size unresolved by the unresolved genomes); raising the total weight at N2's count shows no effect of 0.004 or more (direction unresolved). The equal-magnitude blocks do not reproduce N2's block's effect; it arrives with N2's uneven weights (resolved), labelled degrees and exact wiring (both unresolved over the unresolved genomes). T − I replicates M4d in all ten fresh hosts. Next, the owner's third item: M5, after a power calculation.*
- **Changes the plan if:** no hold-only intervention beats its matched control. "Store" is then dropped for "access", and M5 tests portability of access rather than of a store. *Annotated 2026-10-22 (M4a plan, D357; [`M4A-PLAN.md`](M4A-PLAN.md)): on both reviewers' advice, a null from M4a is read as "not demonstrated", not as "access": it could reflect a short cut, redundant maintenance or the sampled controls.* *Annotated 2026-10-23 (M4a results, D358; [`M4A-RESULTS.md`](M4A-RESULTS.md)): the reading is "unresolved": C3's 30-tick cut costs more than every one of 30 sampled external cuts of equal size at the point estimate on both panels, but at seed 7600 the interval reaches the margin; the cut is also nearly four times stronger at once. Descriptively, it sends 26 of N2's 28 separate-states genomes into one basin from their roots, against 14% for the sampled cuts. Nothing is dropped for "access".* *Annotated 2026-10-23 (M4b results, D360; [`M4B-RESULTS.md`](M4B-RESULTS.md)): cutting the edges among a switch genome's 30 most-differing neurons erases 89% of N2's switches against 31% and 11% for exterior and outgoing controls, but across the selected graphs the effect is not shown (two of ten respond like N2): "unresolved". RIA's 26 to 29 C3-internal edges alone erase 20 and 17 of N2's 28 switches, a place of vulnerability to test next.* *Annotated 2026-10-23 (M4c plan, D361; [`M4C-PLAN.md`](M4C-PLAN.md)): RIA's C3-internal edges are the core's heaviest (560 and 503 against at most 217), so M4c tests them on fresh N2 genomes against three families of weight-matched edge sets.* *Annotated 2026-10-23 (M4c results, D362; [`M4C-RESULTS.md`](M4C-RESULTS.md)): positive: on 141 fresh N2 switch genomes, RIAR's and RIAL's C3-internal edges erase 0.72 and 0.58 of the switches, against 0.22 to 0.30 for every weight-matched family (all six lower bounds above 0.10). A place of vulnerability beyond its weight under these schemes, not evidence of storage; M5 is a candidate, for a decision.*

**M5. The transplant, pre-registered** (the owner's idea; the confirmatory run perhaps on the GPU, with the owner's word; Fable step 5, Astra step 5). *Annotated 2026-10-28 (M5's pilot, D369 and D371; [`M5-PILOT-PLAN.md`](M5-PILOT-PLAN.md), [`M5-PILOT-RESULTS.md`](M5-PILOT-RESULTS.md)): the owner asked for M5 to test N2's exact wiring after working out how many hosts it needs (D365). Agreed with both reviewers: T against M4d's rewired control Rr, the share of all genomes confirmed as separate states, 0.002 at 80% power, the host count from a simulation of the whole reading procedure. A pilot on M4e's hosts (none of its data enter M5) keeps the 22,000-tick protocol (none of 117 unresolved genomes resolved by 100,000 ticks), found no audit transition (0 of 1500 per arm), and puts T − Rr's spread close to genome sampling (SD 0.0034). Agreed after it: a sampled audit, and the calibrated qualifier as a protocol sensitivity with the logical bounds beside it. Next: the power script.* *Annotated 2026-10-28 (M5's power calculation, D372; [`M5-POWER-DESIGN.md`](M5-POWER-DESIGN.md), [`M5-POWER-RESULTS.md`](M5-POWER-RESULTS.md)): designed and reviewed with both reviewers in three rounds, then the script and its results in three more. Success is "raises" in all six readings; the audit is a fixed size; the reading adds the Welch t. The rule recommends C: 110 hosts first, up to 160, about 72 CPU hours at the pilot's spread and 91 at the core (A: 135 hosts, 92 hours). M5 can show more protocol-confirmed separate states, not the direction in underlying states. Next: the owner chooses the host count, then M5's plan and pre-registration.* *Annotated 2026-10-29 (D373): postponed by the owner for its cost against its benefit, not cancelled; the design, pilot and power calculation are kept, and resuming starts at the choice of host count.*
- **Hosts and controls:**
  - M4's structure goes into fresh, independently generated hosts from each ensemble's own sampler;
  - matched controls: a hub set and an internally rewired copy;
  - the reverse in N2;
  - a fresh-draw validation of the narrow maintenance claim that survives M4.
- **Fixed in advance,** committed and pushed:
  - the classification rules and eligibility floors;
  - the sampling units, graph and genome counts;
  - the primary contrasts, the uncertainty method and the exclusions;
  - equivalence margins for "the controls do not move";
  - the outcome wording.

  Thresholds are relative to each host's own baseline. Fable's draft thresholds were on the share and the *growth* fraction (from under 1% to at least 3% of genomes whose full-state difference grows over ten ticks), not on settling.
- **Cost:** benchmark first.
- **A failure** rejects portability under the tested embedding and assay. Whether the state was not written, not observed, or not kept is for the controls to say.

**M6. Then behaviour and biology** (not scheduled). *Annotated 2026-10-29 (D374): with M5 postponed (D373), the owner agreed to design M6's behaviour question next, first as an options note with rough costs and the likely size of each answer.*
- **Behaviour:** does a multistable brain use its states on the memory-task track? 03h's lessons apply: a relief through a channel the read-out can see, and a power rule fixed in advance.
- **Biology:** whether the real worm's RMD and SMD neurons show anything comparable is a literature question. It has to meet the project's literature standard before anything is designed on it.

## Contributions

- **The owner:** the question, the ceremony's format, and three of round 1's ideas:
  - ring attractors became M2's question;
  - trapped waves in loops survive in a narrower form;
  - transplanting became M4's screen and M5.

  They also supplied the ChatGPT roadmap, whose numerical check (M0) ran first.
- **Fable 5.1:**
  - in round 2, the discriminating experiments that most spikes came from;
  - in round 3:
    - the sampler-convention and substeps corrections;
    - pressing the amplitude objection;
    - the anatomy predictor (M3) and the core dissection (M4);
    - the oscillator idea, half observed: its eigenvector half held, its oscillation half did not;
    - the join that batch 8 ran (with Astra);
  - in the review, the 03mc settled census that reframed finding 2.
- **Astra 6:**
  - in round 2, the decomposition of the registered measure, the amplitude scaling around the midpoint, and the maintenance erasures that became batches 4 and 6;
  - in round 3:
    - the persistence-alignment factorisation;
    - the caution that the midpoint Jacobian *could* indicate a saddle;
    - the separation of write, hold and read;
    - the matched erasure controls;
    - the idea of several history-selectable states, which batch 8 and the census make more plausible without establishing it;
    - the bookkeeping catches;
  - in the review, the fixed-point and settling-rule objections.
- **Claude:** ran the ceremony, the eight spike batches and the census check, proposed the core reading, and wrote both drafts.
