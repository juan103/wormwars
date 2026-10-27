**Verdict: revise.** I agree with one primary contrast, simulation of the actual reading procedure, and pre-registration of M5. I do **not** agree that the proposed resolved-genome outcome answers the original question, or that the present assumptions can yet support a definitive host requirement.

I checked both results documents, both readings files, the relevant panel records, and the construction and reading code. I reproduced the variance decomposition and panel costs. I ran no experiments and changed no files.

My points, ranked:

1. **The resolved-genome proposal changes the estimand; it does not remove classification uncertainty.**

   Your original question concerns the share of **all sampled genomes** that have separate states. Your proposed primary estimates the difference between two arm-specific conditional shares:
   \[
   P(S_T\mid R_T)-P(S_{K^*}\mid R_{K^*}),
   \]
   where \(R\) means resolved. The two denominators can select different kinds of genomes. This is the problem with conditioning on an outcome affected by the intervention. [Frangakis and Rubin](https://pmc.ncbi.nlm.nih.gov/articles/PMC4137767/) discuss the general distinction.

   Let \(u_a\) be the unresolved fraction, \(q_a\) the separate-states fraction among resolved genomes, and \(r_a\) the unknown separate-states fraction among unresolved genomes. Then the full-population rate is
   \[
   p_a=(1-u_a)q_a+u_ar_a.
   \]
   Reporting \(u_T-u_{K^*}\) does not identify \(r_T-r_{K^*}\). **Even identical unresolved rates can conceal selection bias as large as the target.** For example, with both true rates at 0.006 and both unresolved rates at 0.004, taking \(r_T=0\) and \(r_{K^*}=0.5\) produces a resolved-only advantage of approximately 0.002 despite zero full-population advantage.

   In M4e, changing to your per-host resolved denominators barely changes the estimate: **0.0019531 becomes 0.0019536**. That numerical similarity does not validate the interpretation.

   My preference is to retain the all-genome estimand, with a fixed classification protocol and a predeclared allowance for remaining classification uncertainty. A longer pass belongs in a separately agreed feasibility pilot, with its horizon, stopping rule and cost measured before the formal design. More hosts cannot overcome a persistent identification interval crossing zero.

   If that is unaffordable, a defensible narrower primary is **“fraction of all sampled genomes confirmed as separate states by the specified protocol.”** Keep the full denominator, report unresolved rates and bounds, and word the conclusion accordingly. Resolved-only is also a legitimate conditional description, but I would not make it the primary answer to the owner’s original question.

2. **The audit must bound error below the effect you want to detect, and its failure branch must enter the simulation.**

   Your arithmetic is right: zero transitions among 1,500 audited fading genomes gives a one-sided 95% upper bound of **0.001995** under the binomial calculation. But an undetected transition rate almost equal to the entire 0.002 target is insufficient validation for a 0.002-scale scientific claim.

   First choose an allowable classification-error contribution, separately from the detectable effect. For illustration, bounding an arm’s transition rate below **0.0005** requires **5,990** zero-transition audits at individual one-sided 95% confidence; simultaneously bounding both arms at 95% by Bonferroni requires **7,376 per arm**. These are illustrative error budgets, not my proposed mandatory audit sizes. They show why “audit sized for the target” needs a more precise definition.

   The current implementation also has a consequential branch: **one audited fading-to-separate transition anywhere discards the second pass globally and uses first-pass classes**. See [m4e_read.py](/D:/Claude/random/wormWars/scripts/memory_m4/m4e_read.py:268). At a transition probability of only 0.0005, a 1,500-case audit has approximately a **53%** chance of detecting at least one transition.

   Therefore simulate first-to-second-pass transitions, audit selection, detection, fallback or further classification, and budget exhaustion. Merely generating final unresolved counts misses this branch. I would reconsider reverting to the shorter horizon after discovering its missed switches; an explicit further-classification or inconclusive outcome is easier to interpret.

   A third pass may be more valuable than more hosts **for reducing identification uncertainty**. Its resolution yield and cost are unknown, so the present records cannot establish that allocation choice.

3. **K* is a reasonable primary control, but “keeps everything else” is wrong. Define the weighted null precisely.**

   I favour your K* over the historical package K **if the intended question is weighted wiring beyond the specified constraints**. Match the actual labelled diagonal entries, with the same paired genome signs—not merely eight autapses—and match exactly 75 reciprocal pairs.

   Feasibility is established in a limited but useful sense: all ten M4d Rr constructions retained 75 reciprocal pairs and completed 5,200 accepted swaps. [The committed construction records](/D:/Claude/random/wormWars/runs/memory-m4d/blocks-summary.json) confirm this. Starting from N2 and preserving reciprocity during rewiring is preferable to assuming M4e’s greedy matcher will reach 75.

   However, [M4e’s K construction](/D:/Claude/random/wormWars/scripts/memory_m4/m4e.py:212) **globally permutes the off-diagonal weights**. It does not retain N2’s labelled strengths or each source neuron’s collection of outgoing weights. [M4d’s Rr construction](/D:/Claude/random/wormWars/scripts/memory_m4/m4d.py:196) does retain those outgoing weights while changing their targets.

   Thus:
   - **T − K*** tests N2’s weighted arrangement beyond labelled degrees, global weight multiset, diagonal and total reciprocity.
   - **T − Rr** asks a narrower question that additionally conditions on each source’s outgoing weight collection.

   I would accept the first as primary, with that wording. Neither isolates unweighted edge positions from weight placement.

   Also specify the sampling distribution. Completing 5,200 accepted swaps demonstrates movement, not mixing or uniform sampling. The current fixed-accepted-swap algorithm should not automatically be called uniform; if uniformity is intended, rejected proposals and chain reachability require attention. Otherwise explicitly define an algorithm-generated null and check chain-length sensitivity and retained similarity to N2.

   **Whether K* materially changes S3 is presently unknown.** No existing K* sample answers that. Measure its S3 distribution and rejection acceptance in the agreed construction pilot. Keep the S3-conditioned contrast secondary, with its own variance assessment and no causal-mediation interpretation.

4. **The variance model needs paired outcomes, fixed ensemble strata, and structural differences between T and the controls.**

   My recomputation from the panels gives:

   | Contrast | Mean | SD of estimated host contrasts | Separate states in both paired arms |
   |---|---:|---:|---:|
   | M4e T − K | 0.001953 | 0.005466 | 0 |
   | M4d T − R | 0.001172 | 0.003530 | 1 |
   | M4d T − Rr | 0.003125 | 0.003313 | 1 |

   Sources: [M4e panels](/D:/Claude/random/wormWars/runs/memory-m4e/arms), [M4d panels](/D:/Claude/random/wormWars/runs/memory-m4d/arms). The M4e decomposition reproduces **50.85% host, 7.73% draw and 41.42% genome sampling**.

   Separate binomial margins plus “shared panels” do not specify genome-level dependence. Use a joint outcome model—at minimum separate/unresolved/other in each arm—or an equivalent explicit coupling. For fully resolved binary outcomes, the paired genome contribution depends on
   \[
   \operatorname{Var}(Y_T-Y_K)
   =p_T+p_K-2p_{11}-(p_T-p_K)^2.
   \]
   The observed overlap gives no basis for assuming a large pairing benefit.

   Treat the five named ensembles as **fixed sampling strata**, unless you explicitly want inference to a population of additional ensemble definitions. Define the target as, for example, an equally weighted mean across these five ensembles, allocate equally, and bootstrap hosts within ensembles. Include ensemble-specific baseline and contrast behaviour in the simulations.

   T has no randomly drawn block. With fresh genome panels, its draw-to-draw sampling noise should not automatically receive an additional block-draw variance component. K* does have block-draw variation.

   Ten hosts and two draws cannot reliably identify a rich GLMM with all proposed interactions and covariances. I would start with a parsimonious contrast model and transparent sensitivity ranges. Retain boundary estimates and fitting failures in uncertainty reporting; do not silently drop bootstrap refits that fail.

   Include **T − Rr**, not only T − R, as historical information. But none is exchangeable with K*, and M4d lacks M4e’s longer classification pass. Historical data support provisional scenarios; a K* pilot is needed before calling the result a calibrated M5 sample size.

5. **0.002 at 80% is acceptable as a planning specification, but not as an expected K* effect or the only useful answer.**

   I would retain **0.002**, alongside **0.001**, rather than require 0.001 as the sole target. There is no statistical reason that my earlier 0.001 benchmark must become the owner’s minimum worthwhile effect. The scientific rationale should be explicit: detecting an increase of two genomes per thousand is worth this experiment.

   The historical contrasts do not bracket K*’s unknown effect. Their role is to inform plausible rates and variability.

   Fix the confidence level now. With a **two-sided 95% interval**, “lower bound above zero” has a nominal directional false-positive rate of **2.5% at zero**, not 5%. A one-sided 5% test is another defensible choice, but a different design.

   Keep your spread scenarios, with these changes:

   - Distinguish a constant effect in every host from an effect drawn uniformly across hosts.
   - For sparse response, randomly draw responder hosts with probability 0.2; do not force exactly one responder in every five sampled hosts.
   - Add response confined to one ensemble, and positive/negative host effects whose population mean is zero.
   - Add switch-enriched unresolved genomes in **K*** as well as T. T-only enrichment mainly tests attenuation; control-arm enrichment can create false “raises.”
   - Calibrate effects on the **marginal probability scale of the chosen estimand**, after random effects and resolution selection. A logit coefficient is not a risk difference.

   Extend the host grid beyond 100 for the 0.001 target and high-variance scenarios. The earlier idealized calculation was approximately **61 hosts at 0.002 and 237 at 0.001**, before classification complications; balanced allocations round these upward. Those remain orientation, not M5 requirements. [Archived calculation](/D:/Claude/random/wormWars/docs/reviews/20261027-m4e-results/r1-astra.md:87).

   Report Monte Carlo uncertainty and uncertainty from fitting the historical data separately. Do not select the first noisy grid cell whose estimated power happens to exceed 80%. Specify the precision and selection rule in advance; simulation uncertainty is a substantive reporting requirement. [Morris, White and Crowther](https://doi.org/10.1002/sim.8086).

   Finally, report both **fewest hosts** and **lowest estimated cost** among qualifying allocations. These need not coincide. A uniform-response minimum can be reported, but must be labelled conditional on that scenario.

6. **Two implementation details would otherwise make “simulate the whole procedure” misleading or infeasible.**

   First, the existing guard applies **only to exclusion at 0.004**, not to “raises.” [m4e_read.py](/D:/Claude/random/wormWars/scripts/memory_m4/m4e_read.py:69). Preserve that distinction. Adding a maximum-host veto to the primary would be a new rule whose behaviour can worsen as more hosts are sampled.

   Second, the current envelope enumerates **all \(2^H\) corners**. [m4e_read.py](/D:/Claude/random/wormWars/scripts/memory_m4/m4e_read.py:56). That cannot be carried into simulations at 60–100 hosts. Agree on a scalable, demonstrably conservative replacement, or a justified optimization method. If the envelope is only descriptive sensitivity, it need not be computed inside every power replicate. Validate any replacement against exhaustive small-host examples.

   Your proposed tests and sabotage check should specifically cover these branches, pairing, marginal effect calibration, and informative unresolved outcomes—not merely whether the simulator reproduces its own inputs.

7. **The cost estimate is a sound historical baseline, but incomplete for the proposed design.**

   T and K together took **10.479 hours across ten hosts**, or **1.048 hours per host** for two draws of 512 genomes, including the existing second pass. That gives approximately **62.9 hours for 60 hosts** and **104.8 hours for 100**.

   Those estimates exclude a larger audit, a third pass, K* construction changes, and additional control arms. A fresh S3-conditioned arm costs another set of panels; a fresh historical-K arm also costs compute. Reusing the published package contrast for continuity does not.

   Model classification cost separately from genome count because difficult trajectories drive variable costs. Report cap-exhaustion probabilities as well as average time. GPU feasibility requires its own benchmark and the repository’s equivalence check.

8. **Yes to pre-registration, and yes to reviewing the power output before M5’s plan is finalized.**

   The power calculation is exploratory design work; it does not need its own confirmatory pre-registration. It should have a dated agreed specification, versioned code, input provenance, tests and committed outputs.

   I recommend this sequence: agree on the revised estimand and classifier policy; agree on any construction/classification pilot; produce and review the power report; then freeze, commit and push M5’s pre-registration before the formal run. Keep pilot outcomes separate from formal outcomes unless their inclusion is explicitly accommodated in the design.

   The next review should assess whether the implemented simulator actually represents the agreed experiment, whether its false-“raises” behaviour is acceptable, and how strongly the recommended allocation depends on uncertain K* and classification assumptions. **Until those are settled, “about 60 hosts” is a conditional reference calculation, not an answer to the owner’s feasibility question.**