**I recommend a staged intervention study, led by edge count × total weight at fixed location, with smaller tests of weight shape and degree allocation.** Do not make a regression on spectral summaries the primary result, and leave relocation for a separate stage.

I checked the M4d arm records, construction code, classifier, synthesis and D365. The reported class counts agree. Three qualifications matter:

- M4d establishes effects of **packages of properties**, not separate contributions from count, weight and degrees.
- D randomizes the off-diagonal edges; its eight autapses remain at N2’s original positions and weights. The code explicitly enforces this. “260 edges, weight 2347” refers to the off-diagonal block. [Construction code](D:/Claude/random/wormWars/scripts/memory_m4/m4d.py:231)
- The small overlap between switching genomes is not surprising given the rare outcomes. Under independence, T and P would share approximately \(64×69/10240=0.43\) genomes; they share one. This demonstrates little preservation of the observed switch identities, but does not by itself demonstrate unusually strong antagonism between the arms.

**1. The estimand**

My proposed reader-facing sentence is:

> On the same 30 head neurons, does distributing a fixed amount of connection weight over more edges change how often two food histories reach different stable states, and how does that compare with increasing the weight or changing its distribution and degree allocation?

That is narrower than “which property causes memory,” and achievable.

Define the target as the average probability of **history-accessible separate stable states**, across fresh hosts, block constructions and random genomes, under the existing food probe. Include read-out-silent states and retain the denominator of every drawn genome.

Priority:

1. **Count and total weight, including their interaction.**
2. **Weight shape and degree allocation**, under explicitly specified constructions.
3. **Whether a summary predicts across different constructions.**
4. **Location and neuron-count size.**

Holding 30 neurons fixed studies edge density, not block size measured in neurons. Also, this measures the whole embedded network’s response. It does not establish that the block independently stores the state.

The proposed factorial is not well-defined as written: an exact weight multiset has a fixed cardinality, and N2’s exact degree sequence fixes the edge count at 260. Those cannot be crossed freely with the host’s edge count.

**2. A concrete eight-arm first stage**

For host \(h\), let \(E_h\) and \(S_h\) be its own off-diagonal C3 edge count and summed anatomical weight.

Use the following arms:

| Arm | Off-diagonal block | Purpose |
|---|---|---|
| I | Intact host | Baseline |
| U_LL | \(E_h\) random edges, total weight \(S_h\), equal magnitudes | Low-count, low-weight reference |
| U_LH | Same support as U_LL, total weight 2347 | Increase weight at low count |
| U_HL | 260 random edges, total weight \(S_h\), equal magnitudes | Increase count at low weight |
| U_HH | Same support as U_HL, total weight 2347 | Complete the factorial |
| W | U_HH’s support, N2’s 260 off-diagonal weights randomly assigned | Uniform versus N2-shaped magnitudes |
| K | N2’s labeled in/out-degree sequence, randomized wiring and globally permuted N2 weights | Degree-allocation intervention |
| T | Complete original N2 block | Fresh replication of the M4d transplant package |

**I through K retain the host’s original autapses.** T carries N2’s autapses and is a package-level benchmark; its comparisons are not clean tests of wiring or autapses.

Construction details that I would require:

- Couple the low-count support as a uniformly selected subset of the high-count support. This preserves the desired uniform marginals while improving pairing.
- Share support across weight interventions, and signs by ordered neuron pair across all arms.
- In K, globally shuffle weights after constructing the topology. Do not preserve N2’s out-strengths as M4d’s R did.
- Match K’s reciprocal-pair count to its paired W construction, with feasibility and sampler behavior checked before outcome runs.
- Freeze exterior signed weights, gap junctions, biases and time constants. Keep M4d’s intact-host normalization and bitwise sham check. Re-running `Genome.random` independently on each changed graph would spoil the intervention. [Paired construction](D:/Claude/random/wormWars/scripts/memory_m4/m4d.py:370)
- Verify achieved weights after clamping. Intended totals are insufficient if clipping changes them.

The two primary contrasts should be:

\[
\Delta_{\text{weight}}=p(U_{HH})-p(U_{HL}),\qquad
\Delta_{\text{count}}=p(U_{HH})-p(U_{LH}).
\]

Report the corresponding low-level contrasts and the interaction. Do not average away an interaction and announce one universal “density effect.”

W−U_HH tests replacing equal magnitudes with N2’s weight distribution at fixed support and sum. It does not isolate a single concentration statistic.

K−W tests **N2’s labeled degree constraints under exchangeable weight assignment**. It does not isolate degree heterogeneity from which named neurons receive high degrees, or from the strength variation that degrees induce. A later label-permutation arm is needed for that distinction.

I would defer the four-level gain sweep, reciprocity manipulations, autapse manipulations and gap transplants. If T works but the host-diagonal constructions do not, the next stage must address the diagonal and its interactions.

**3. Synthetic blocks**

Yes, include constructions that do not inherit N2’s off-diagonal edges or weight distribution. The four U arms already do that.

They ask whether random wiring with equal magnitudes can produce an effect at the tested counts and weight budgets. That is a useful generic test, conditional on these hosts and their retained diagonals.

I would defer synthetic heavy-tailed weights and synthetic heterogeneous degree sequences to stage two. There, compare:

- equal magnitudes;
- N2-shaped magnitudes;
- a pre-specified bounded synthetic broad distribution;

and, separately, approximately homogeneous versus synthetic heterogeneous degree allocations.

A synthetic distribution that changes total weight, maximum weight and concentration simultaneously would reproduce the present confounding. Conversely, failure of equal-weight blocks would not establish that N2’s particular weights are necessary.

**4. Unresolved genomes**

**A longer classifier pass is essential, but “increase the horizon” needs a precise implementation.** M2 already uses up to 20,000 ticks of continuation after the 2,000-tick endpoint. Its oscillation procedure then examines roots from the continued orbit; it does not simply reclassify both histories at that later endpoint. [Classifier implementation](D:/Claude/random/wormWars/scripts/memory_m2/pilot.py:307)

I propose this fixed protocol:

1. Classify every genome at 2,000 ticks using the existing rules.
2. For **every arm’s unresolved and persistent-oscillation genomes**, continue both histories from their saved 2,000-tick states to a total hold time of 22,000 ticks.
3. Reapply the root, stability and reaching rules at that endpoint, using correctly shifted observation windows and retaining the original write amplitude. Keep the existing 20,000-tick certification cap.
4. Apply the same later check to a preselected 1% audit sample of initially resolved genomes. Unexpected class changes trigger the specified validity response.
5. Preserve both classifications and their transition table.

Include persistent oscillations because their classification is explicitly finite-horizon evidence; they should not silently become permanent non-switches in an eventual-state claim.

This requires a validated horizon-aware wrapper. Merely changing `FOLLOW` or `CAP` is insufficient: the current code has fixed tail-window assumptions. That new behavior needs failing tests and equivalence checks against the unchanged 2,000-tick path.

For the final estimand, retain partial-identification bounds:

\[
p_{\text{separate}}\in
\left[\frac{n_{\text{separate}}}{N},
\frac{n_{\text{separate}}+n_{\text{unresolved}}}{N}\right].
\]

Do not discard unresolved genomes, assume they resemble resolved ones, or combine them with switches. Report oscillation and unresolved rates separately. Increased coupling need not monotonically increase switching; other random recurrent-network models show transitions into sustained irregular dynamics as gain rises, although that is not a prediction for this particular network. [Sompolinsky, Crisanti and Sommers](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.61.259)

**5. Replication, reading and margin**

Use **hosts as the outer replication unit**, but replicate the block construction within each host:

- Ten fresh hosts, two per ensemble.
- Two independent block draws per host.
- 512 fresh genomes per draw, paired across arms.
- Thus 1,024 genomes per host and arm.

Average the two draws within each host before the primary host-level analysis. Report both draws. They improve sampling of the construction distribution; they do not create twenty independent hosts.

Use paired risk differences as primary. Give multiplicity-adjusted intervals for the two primary contrasts; treat the other contrasts as secondary estimates. Calibrate the interval procedure before running against sparse counts, heterogeneous hosts, block variation, nearly disjoint switching genomes and residual unresolved outcomes. Do not assume M4d’s bootstrap/t-interval procedure automatically transfers.

**The margin should reflect scientific importance, not be obtained by multiplying the observed baseline.** M4d’s 0.004 was one-quarter of N2’s excess over reference hosts. Updating the baseline from 0.12% to 0.039% changes that calculation from approximately 0.0040 to 0.0042—not to one-third of 0.004. [Original margin](D:/Claude/random/wormWars/docs/memory/M4D-PLAN.md:161)

For this property screen, I suggest **0.001 absolute probability**, one additional switching genome per thousand, as a provisional meaningful-effect benchmark. That is a new scientific choice, not a consequence of the baseline correction. Report estimates and uncertainty around it; do not promise this screen can establish equivalence at that margin.

For scale: with two rates around 0.6%, 10,240 genomes per arm and approximately independent switch identities, the binomial-only standard error of their difference is about **0.00108**. Host and block heterogeneity can add uncertainty. This is a screen for substantial effects, not a reliable exclusion of every effect near 0.001.

I oppose a summary regression as primary. Eight arm constructions provide little independent variation for separating correlated summaries, and genome counts do not create additional independently manipulated block types.

Spectral quantities can be diagnostics, but specify the matrix. The actual stability calculation includes signed weights, saturation derivatives, gaps, leak and time constants—not just the anatomical block. Root stability is also part of the outcome definition, making a root-spectrum “explanation” potentially circular. [Implemented Jacobian](D:/Claude/random/wormWars/scripts/memory_m2/equilibria.py:40)

To claim that one summary explains the rates, require prediction of held-out construction families and deliberately matched-summary comparisons. An insignificant residual arm coefficient is insufficient.

**6. Cost and cap**

The eight-arm design contains:

\[
10\times2\times512\times8=81{,}920
\]

genome–arm evaluations: **80 standard panel-equivalents**.

The actual M4d records total 90,532 seconds for 70 panels, averaging **1,293 seconds**, rather than 1,100. That projects to **28.7 hours** before the new follow-up procedure and setup. [Recorded timing](D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:54)

My proposal is:

- Approximately 29 hours for initial classifications.
- Provisionally 8–12 hours for later classification and its audit.
- Additional allowance for construction and verification.
- **48 CPU-hour cumulative cap**, with a benchmark required before freezing that allocation.

The follow-up allowance is uncertain. A small fraction of genomes can consume disproportionate wall time through serial oscillation checks and difficult root calculations.

Run balanced host/draw blocks, without outcome-dependent extension. If the required protocol cannot finish under the cap, report it as incomplete; do not quietly drop expensive arms or unresolved cases.

This first stage does **not** require a GPU. A study powered for small equivalence margins or several location and size factors may need substantially more compute, and then the owner’s GPU decision becomes relevant.

**7. Consequences for M5**

Results should change M5 as follows:

- **Total weight dominates:** match achieved effective weight budgets carefully.
- **Weight shape matters:** match the distribution or its demonstrably relevant features, not merely its sum.
- **Degree allocation matters:** include degree-matched controls and separate labeled allocation from degree heterogeneity.
- **A summary predicts across independent constructions:** add a control matched on that summary.
- **Unsettled dynamics dominate:** carry the longer classification protocol and a separate dynamics outcome into M5.
- **Strong host variation:** increase host replication rather than only genomes per host.

However, matching a spectral summary can remove a mechanism through which exact wiring acts. M5 must distinguish the **total advantage of N2’s wiring** from its **residual advantage beyond a chosen summary**. Those are different questions.

No ordinary outcome of this exploratory screen makes M5 scientifically unnecessary. Generic blocks working does not show that N2’s wiring adds nothing; a null property contrast does not establish equivalence. A convincing fresh-data exclusion of a scientifically relevant wiring advantage would essentially perform M5’s job already. Otherwise, abandoning it would be a decision about priorities.

My concerns, ranked, are:

1. **Unresolved and finite-horizon classifications are comparable in size to the effects.**
2. **Calling coupled interventions separate property effects.**
3. **Insufficient replication of block constructions and host heterogeneity.**
4. **Treating predictive summaries as causal explanations or equivalence evidence.**
5. **Expanding into location, neuron-count size and many gain levels before the first distinctions are resolved.**