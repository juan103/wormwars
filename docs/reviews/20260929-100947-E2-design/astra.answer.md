I would revise v1. The central problems are the incomplete compute accounting, a random-search rule that discards most of its work, and an ES specification that could produce an uninformative failure. N2-only, raw-count fitness and a conservative preference for retaining the GA are reasonable choices.

I checked the design against the roadmap, corrected 04a results, evolution and genome code, E1’s throughput records, and the ENOMAD paper and authors’ code. I did not execute project code or modify files.

The following are **must-changes**.

1. **Define one complete budget, including how tuning is amortized.**

   The [256,000-episode figure](D:/Claude/random/wormWars/docs/E2/DESIGN.md:48) covers training selection alone. With 04a’s 41 checkpoints and one final evaluation, the corresponding total is already:

   `256,000 + 41 × 256 + 1,024 = 267,520 episodes/run`

   That excludes tuning, probes, replays and projection work. Checkpoint frequency is confirmed in the [04a implementation](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:153).

   The tuning allocation is also ambiguous. Six 100-generation pilots cost **153,600 training episodes**. Charged once against three runs’ combined 768,000-episode allowance, they leave **800 training generations per formal run**. Charged separately to each run, they leave **400**. Those are substantially different comparisons; both calculations still omit evaluation overhead.

   My preference is a **method-level allowance**, with tuning charged once and the remainder divided equally among fresh formal runs. Publish a ledger covering training, tuning selection, validation, final evaluation and diagnostics, with shared controls identified separately. Count ticks and actual neural updates, including padding.

   Keeping inherited GA settings without new tuning is acceptable for an engineering decision about replacing an incumbent. Describe this as **equal additional E2 work**, not equal historical development effort.

2. **Repair the random-search champion rule.**

   As written, random sampling nominates only the best genome of the checkpoint generation. Unlike the GA, it carries no information from intervening generations.

   Under 04a’s schedule, only **41 × 32 = 1,312 of 32,000 random genomes** can influence the final champion. The other 95.9% are discarded without affecting anything. That is not a useful equal-budget random-search floor.

   Retain candidates from every sampling batch. One inexpensive option is to retain the best screening candidate since the previous checkpoint, then validate that candidate. A fixed shortlist with budgeted reevaluation is another. Fresh proposals remain independent random samples; retaining good observations does not turn them into adaptive proposals.

   The [GA’s implementation](D:/Claude/random/wormWars/wormwars/evo/evolve.py:73) explicitly preserves elites, so applying identical checkpoint wording does not give the two methods equivalent opportunities.

3. **Specify the ES as an actual algorithm, especially its geometry and flat-reward behavior.**

   Scaling by GA mutation sizes is a defensible starting point. It is not sufficient specification. Resolve:

   - **Encoding and bounds.** State the exact transform, for example  
     `z = (w/0.08, g/0.04, log(τ)/0.15, bias/0.05)`, including any offsets. The existing bounds are `w ∈ [−3,3]`, `g ∈ [0,2]`, `τ ∈ [0.5,20]`, and `bias ∈ [−2,2]`. Specify how candidates and the updated mean are projected or decoded. [Genome clamping and mutation](D:/Claude/random/wormWars/wormwars/brain.py:246).
   - **Clamping and antithetic sampling.** Clipped candidates need not remain symmetric around the decoded mean, particularly for small gap conductances. This does not automatically invalidate a Gaussian estimator applied through a fixed decoder, but it changes the search distribution. Preserve the original perturbations in the estimator and record clipping rates. Prevent or explicitly handle a mean drifting far outside the feasible region.
   - **Weight decay.** “0.005” is not portable across parameterizations. Decay toward zero in the transform above favors `g = 0` and `τ = 1`, as well as small weights and biases. Specify the regularized coordinates, reference point, normalization, and whether this is an Adam gradient penalty or decoupled decay. Drop the unexplained default or justify it against an option with no decay.
   - **Reward ties.** Raw counts averaged over eight worlds will tie frequently. Require equal utilities for equal rewards. The original [OpenAI implementation](https://raw.githubusercontent.com/openai/evolution-strategies-starter/master/es_distributed/es.py) assigns distinct ordinal ranks even to equal values; copying that behavior can manufacture a fitness gradient on an entirely flat batch. Test that constant rewards give zero fitness-gradient contribution.
   - **Update and randomness.** Fix gradient normalization, sign, Adam settings, noise schedule, and evaluation-before/after-update timing. Use the same worlds for the two members of each antithetic pair, preferably all candidates in a generation.

   Initialization also needs a decision. A single draw from `Genome.random` is not equivalent to averaging 32 draws—the latter cancels chemical signs and changes the prior. Nor does one starting basin provide the GA’s initial diversity. Specify whether ES uses one draw, a budgeted initial screening pool, or registered restarts.

   This matters because [04a found 78–97% of generation-zero genomes scored zero on all training worlds](D:/Claude/random/wormWars/experiments/04a-navigation-primitive/RESULTS.md:173). A small perturbation cloud around one inactive controller could remain uninformative. Record zero-reward batches and distinguish “this ES configuration failed” from “ES is unsuitable.”

4. **Freeze evaluation compositions, seed separation and candidate selection.**

   The hold-out arrangement is broadly sensible: common fresh worlds, champions fixed beforehand, and the same final composition for every method. Complete it by specifying:

   - separate tuning-training, tuning-selection, formal-training, validation and final-test streams;
   - committed champion hashes and frozen hyperparameters before final evaluation;
   - exact `(strains, worlds, weys)` compositions and chunking for every stage;
   - whether ES nominates its mean only, and the corresponding rule for ARS.

   “Batched as in 04a where the method allows” leaves too much open. The repository explicitly limits exactness to fixed compositions; single-strain padding does not establish composition independence. [Reproducibility rules](D:/Claude/random/wormWars/docs/REPRODUCIBILITY.md:46).

   Evaluating the ES mean is a legitimate choice, but it compares the methods’ declared output procedures, not necessarily their best encountered genomes. Do not switch to best sampled offspring after seeing results. Register a composition-sensitivity check on development worlds if methods require different numerical paths.

5. **Correct the runtime projection.**

   The proposed **1.6 seconds for three batched runs is unsupported** by E1’s measurements. The committed record gives approximately:

   | Runs batched | Seconds per training rollout |
   |---|---:|
   | 1 | 2.32–2.34 |
   | 4 | 3.03–3.05 |
   | 8 | 4.67–4.69 |

   See [E1’s throughput record](D:/Claude/random/wormWars/experiments/E1-navigation/freeze.json:493).

   Three runs contain 768 strain-episodes; 1.6 seconds implies **480 episodes/second**, exceeding even the measured eight-run throughput of 438. That speed might conceivably be measured, but it cannot be claimed from this curve.

   Measure the intended training, tuning and checkpoint shapes, including optimizer and recording overhead. Five hours may still suffice; the current evidence does not establish it. Decide ARS inclusion from timing and a fixed allocation **before inspecting comparative performance**, and specify the outcome if the cap prevents completion.

6. **Make the decision rule operationally complete and limit its interpretation.**

   A 0.5-target improvement is a defensible practical threshold. With three runs, the worst-versus-median condition is a conservative policy preference, **not evidence of a reliable population advantage**. One unlucky run—or a negligible difference at the boundary—can decide everything.

   Specify what happens when multiple methods qualify, whether random sampling can qualify, ties, numerical failures and incomplete runs. Retain all registered runs in the reporting; no replacing unsuccessful seeds.

   Also change “random sampling within 0.5 means the GA adds little” to an explicitly descriptive statement about the observed runs. Three runs do not establish equivalence. The 1,024 worlds improve measurement of each champion; they do not create additional optimizer replicates.

   Using the final suite to select an optimizer is appropriate here. It does mean the selected winner’s score is subject to selection optimism; E3 must evaluate on new worlds.

7. **State the limited connection to E3.**

   E2 measures acquisition from random initialization. [E3 starts with validated modules, then evolves a selector and jointly fine-tunes](D:/Claude/random/wormWars/ROADMAP.md:169). Those differ in initialization, parameter space and objective. Their optimizer rankings need not agree.

   E2 can choose a **provisional default for E3**, but cannot validate superiority for those later stages. If a stronger claim is intended, include a small matched comparison starting from existing champions. Otherwise retain the narrow screen and state the transfer uncertainty.

   Also specify whether E2 may replace the navigation module itself. If so, a higher count alone does not inherit 04a’s evidence about cue dependence and reliability; the replacement needs the relevant checks.

8. **Correct and qualify the ENOMAD summary.**

   The broad description is fair: hybrid evolutionary/local search, anatomical initialization, 512-member ES baseline, and a reported 20-minute comparison. “Leaky integrate-and-fire” is correct for the **journal version**; arXiv v1 instead describes no leak. Cite the version used. The ES’s 0.01 noise value is a floor, not necessarily its attained final value. [Published paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12803941/), [arXiv v1](https://arxiv.org/html/2508.09618v1).

   **“All positive” is wrong:** the authors’ `V2_FINAL` [loader negates GABA connection counts](https://raw.githubusercontent.com/dsb-lab/C_Elegans_Training/V2_FINAL/celega/Non_Biased_Dynamic_C/util/read_from_xls.py).

   “A working controller” also overstates the starting performance: the paper describes poor untrained food collection. Its important prior is a parameterization near useful solutions. Add two differences: their rewards include shaping, and their deterministic task setup differs from E2’s changing world samples. Generations are not evaluation counts, especially with nested NOMAD calls. [Published methods and results](https://pmc.ncbi.nlm.nih.gov/articles/PMC12803941/).

My **suggestions and answers to the six questions** are:

1. **Use OpenAI-ES as the single additional optimizer.** Sep-CMA-ES is also defensible and scales linearly in its diagonal representation; dimensionality does not rule it out. ARS need not be required. Spend spare budget on replication and a competent ES configuration first. Sixteen directions for 5,404 parameters is a weakly supported choice; consider a larger population with correspondingly fewer updates under the same total work.

2. **Charge tuning once to the method’s total**, while reporting it separately as a ledger category. Reporting it without charging would contradict the roadmap. State that formal replicates are conditional on one selected hyperparameter setting.

3. **Drop shaping for this screen.** That removes a training-objective choice and is supported as feasible by 04a. Four unshaped runs do not show shaping is generally harmful or unnecessary for every optimizer. Avoid that broader claim.

4. **Keep the 0.5 threshold; prefer six runs if the corrected projection permits it.** Three are acceptable for a deliberately coarse switch/no-switch decision. More runs are more useful than adding ARS. If increasing the run count, reconsider using the minimum: the worst of six is a stricter statistic than the worst of three.

5. **Do not require an ENOMAD hybrid now.** Keeping E2 small is sufficient justification. “We have no working prior” is not a sound general reason to defer it: 04a has now supplied competent, though weak, controllers that could seed local refinement.

6. **Improve tuning replication before expanding the grid.** Six configurations with one short trajectory each can select a lucky start. Prefer fewer settings evaluated on multiple paired initialization/world schedules. Fix the selection score and tie rule. The [04a corrections](D:/Claude/random/wormWars/experiments/04a-navigation-primitive/RESULTS.md:132) show why 100 generations should not be assumed to reveal eventual performance.

**E2 design: revise**