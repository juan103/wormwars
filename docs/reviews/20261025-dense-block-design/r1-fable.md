**Short answer:** the study should be a dose-response, not another ladder. Candidates (a) and (b) are not alternatives: (b) is the only way to get (a) with the power this CPU affords. Candidate (c) is a different question and should wait. One free step comes first: M4d's own records can choose the dose variable before anything is run.

## Why a ladder will fail again, and what to do instead

M4d's best-resolved secondary contrast, R against D, was a difference of 28 genomes over 10 hosts, and it was robust only on counted genomes. A factorial of properties at this scale gives a dozen such contrasts, each with the same precision, each with unresolved genomes as large as the effect. A dose-response reads one slope across all arms, which uses every panel for one estimate, and it tells M5 what to match.

The mechanism makes a dose variable natural. Signs are drawn per genome, so the anatomy fixes only the magnitude profile of the block. In this tanh network, two stable states under the final input need a real eigenvalue of the effective coupling above 1, and a complex pair above 1 gives an oscillation. That fits what M4d saw: the switch genomes differ almost completely between arms because the signs decide which genome crosses, while the block's structure sets the rate of crossing. It also explains why the not-settled genomes gather in T and T+G. Three sign-invariant block summaries follow, and they make different predictions:

| Summary | What it is | Rises with |
|---|---|---|
| S1 | summed scaled magnitude | count, gain |
| S2 | summed squared scaled magnitude | count, gain squared, weight concentration |
| S3 | square root of the spectral radius of the matrix of squared magnitudes | S2, and concentration of edges on hub rows and columns |

S3 is the expected spectral radius of the signed block over random signs. R, Rr, P and T share S1 and S2 exactly, so M4d's R over D can only be an S3 effect or noise. The per-genome version is the signed block's largest real eigenvalue, computable before any simulation.

I checked the scale. N2 has 3,709 chemical edges of total weight 20,965, so a scaled magnitude is 0.0354 times the anatomical weight. N2's eight C3 autapses weigh 1 to 11 sections, so their scaled magnitudes are at most 0.39, far below the isolated-neuron threshold of 1. They cannot seed bistability alone, so autapses do not deserve a factor, only one cheap arm. The heaviest C3 edges I saw in the local blocks file weigh 57, which scales to about 2.0, so a global gain above 1.4 would hit the engine's clamp of 3.0. The gain route must stop at 1.4 and the plan must compute the true maximum.

**Stage 0, free and exploratory, before the plan is fixed.** Compute S1, S2 and S3 for every M4d block and the per-genome largest real eigenvalue for all 71,680 M4d genomes, then relate them to the committed classes. Fix the selection rule before looking: the per-genome predictor with the highest AUC for separate states pooled over arms becomes the dose variable, and its block-level counterpart the arm summary. Also compute S3 for M4d's R blocks against T's. If R's S3 sits below T's, part of M4d's T over R was a built-in coupling advantage, which matters for M5 directly. Everything here is after the data; the prospective test is the stage below.

## The proposal, question by question

**1. Estimand**, in one sentence for `main`: in fresh null graphs, random brains hold a food history as two stable states more often the stronger the head-core block's recurrent coupling, whether that strength comes from more edges, heavier edges, or edges concentrated on a few neurons; and N2's own degree pattern adds nothing beyond it, or adds a stated amount. Priority: (b) first, (a) answered through it, (c) deferred to a second stage.

**2. Arms**, all on C3's neurons with M4d's paired construction and hosts' exteriors, N2's eight autapses kept except where named. New blocks only; I, D, R and T are already measured on the same genomes.

| Arm | Block | Route | Separates |
|---|---|---|---|
| D×0.5 | M4d's D, gain 0.5 | weights | S1 from S2: same S1 as D130, S2 half of it |
| D×0.71 | gain 1/√2 | weights | same S2 as D130, S1 higher |
| D×1.4 | gain 1.4, below the clamp | weights | top of the range |
| D130 | random half of N2's multiset, random positions | size | with D×0.5 |
| D390 | 260 plus 130 resampled from the multiset | size | with D×1.4: same S1, lower S2 |
| H | 260 edges, N2's multiset, a degree sequence more concentrated than N2's by one fixed rule | degrees | S3 from S2 at fixed S1 and S2 |
| Dc | D's positions, N2's multiset raised to a fixed power and renormalised to the same sum | weight concentration | S2 and S3 from S1 at fixed count |
| D0 | M4d's D without autapses | autapses | closes that share |

Essential: D×0.5, D×1.4, D130, D390 and H. Useful: Dc, D×0.71, D0. Reciprocity gets no arm: with independent signs, reciprocal pairs carry nothing in the signed matrix's expectation, and Rr below R was one draw per host. Gap junctions wait too.

**3. Synthetic arms.** Yes, but only H and Dc, each derived from N2's multiset by one named transformation. N2's numbers are a single point on the degree axis and on the concentration axis, and only synthetic blocks extend those axes. Fully synthetic weight laws with free parameters should wait: too many choices to fix honestly.

**4. Unresolved genomes**, fixed in advance:
- Every unresolved genome in every arm gets a second pass: the float32 probe continued from its recorded tick-2000 state for 8,000 more ticks, then the same classifier. Its class after the pass is its class.
- A validity check: 256 resolved genomes sampled across arms get the same pass and must keep their class in 99% or more. Otherwise the pass is reported, not used.
- Genomes still unresolved count as not separate states and bound the reading by M4d's envelope.
- "Not settled" (oscillation plus still unresolved) is a secondary outcome with its own slope, because the complex-pair counterpart of the switch is itself a prediction.

Cost: about an hour. Counting unresolved genomes as switches in the estimand would mix the two regimes; do not.

**5. Reading.** Hosts as the unit, as in M4d. Primary: per host, a Poisson regression of the switch count on the log of the chosen summary over the six dose arms, giving one slope per host; the reading is the mean slope with the hull of the host bootstrap and the Student-t interval, with a coverage simulation before the run. "Dose-response" if the lower bound is above zero. Secondary, the collapse test: for H, R and Dc, each host's deviation of the observed count from what its own curve predicts at that arm's summary, averaged over hosts. "Carried by the summary" if the interval lies within a margin of 0.004 either side, "beyond it" if the lower bound exceeds the margin, otherwise unresolved. The margin is M4d's, and the plan should say plainly that smaller deviations are not detectable with ten hosts. The base rate matters only for the floor, which I already gives. A random-effects regression across hosts adds assumptions and nothing else.

**6. Cost.** Reuse M4d's ten hosts and their panels. At M4d's rate:

| Item | Panels | Hours |
|---|---|---|
| 8 new arms × 10 hosts | 80 | 24.4 |
| second pass and check | | about 1 |
| stage 0 | | minutes |
| cap | | 32 |

Fixed now as stage 1b and run only if the slope reads positive: five fresh hosts, one per ensemble, with I, D, the four essential dose arms and H, about 35 panels and 11 hours. No GPU is needed. Reuse pairs every new arm with seven arms already measured on the same genomes, and the fresh hosts guard against the fact that these ten hosts produced the R over D observation that motivated the design.

**7. Feeding M5.**
- If the slope holds and the routes collapse, M5's rewired control must match N2's block on the summary, not just on degrees and out-strengths. That is a one-line tolerance in the swap chain, and the power calculation gets a concrete null: the expected T over R is the summary difference times the slope.
- If the per-genome predictor explains the switch at the genome level and T's genomes show no residual over D's and R's, M5 is unnecessary as a host-level test. The wiring question is then answered with about 300 switches instead of 12-genome host differences. If T shows a residual, M5 runs with the predictor as a pre-specified covariate and its power calculation uses the residual's size.
- If there is no dose-response across a threefold range of the summary, the density account is wrong, and M5's wiring test becomes the interesting one, with D and R against I as its controls.

## Concerns, ranked

1. **Another ladder reproduces M4d's indeterminacy.** The dose design and stage 0 are the fix. If the session prefers the factorial, it should state up front that most cells will read unresolved.
2. **Stage 0 chooses the summary on M4d's data.** The prospective tests, the slope and the collapse, are new contrasts, and stage 1b's fresh hosts cover the shared D260 point. Say all of this in the plan.
3. **The clamp.** Gain above 1.4 clamps the heaviest edges; the plan must compute N2's maximum C3 edge weight and report clamped entries, expected zero at 1.4.
4. **The second pass is a new horizon.** M2 validated the classifier at 2,000 ticks only. The resolved-genome check above is the minimum; without it the pass should not change any count.
5. **One block draw per host and arm.** P's spread of 1 to 19 across hosts shows a draw matters as much as a host. The host bootstrap covers it only because draws are independent across hosts. H's construction must be one fixed rule so the draw is its only randomness, and no single host is read.
6. **The paired construction divides by the intact spec's mean.** That keeps the exterior unchanged when a synthetic block changes the total; the code does this now and the plan must say it and keep the sham check at D260.
7. **Location is not tested.** C3 carries the sensors and the read-out, so the finding's wording must say "on the head core's neurons". A dense block elsewhere is stage 2, and the classifier's full-state roots already give the independent observation it needs.
8. **"Unstable or marginal root" dominates T's unresolved genomes.** That may be a real third regime near a saddle. Keep it inside the not-settled secondary outcome rather than folding it into either class.