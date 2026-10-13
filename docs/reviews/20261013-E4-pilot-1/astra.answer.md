**Choose A first: reduce inherited mutation, retain independently scaled cross-links, and run a short, bounded pilot. Reject C for now. Keep B as an explicitly narrower fallback—not an equivalent replacement for E4.**

1. **The load is real; “the GA does not move off E-G” is too strong.** The [summary](D:/Claude/random/wormWars/experiments/E4-two-minds/pilot-attempt1-summary.json) supports destructive mutation and no visible training-score improvement. But 22–57 mutation events establish genetic movement, and those are whole-genome mutation events, not individual parameter changes. All strains within a run share each generation’s eight mazes; changing maze difficulty and choosing the maximum obscure performance trends. Also, generation-0’s 6.23 and the load assay’s 1.94 use different maze blocks: their subtraction is not a paired load estimate.

   **Cheap check:** take each saved final population’s three elites plus its final training winner; screen them on 32 common fresh pilot mazes, select one per run, then compare those four against E-G on a separate 128-maze block. Report per-run paired differences and maze-level uncertainty, averaging weys within mazes. This should take a few GPU minutes; it assesses those candidates, not every possible champion. Evaluating all final populations on 64 validation mazes would cost roughly eight minutes at proportional throughput, plus independent evaluation. The driver computed checkpoint validation scores but did not preserve them in the partial record.

   Crucially, **X0 improvement is not required for meaningful P1 or P2**. X+ could discover useful links while X0 remains at a local optimum. Recruitment is functional under §2, not inferred from weight size or X0’s learning curve.

2. **Use A without automatically relaxing the load bound.** Screen inherited factors **0.05 and 0.10**, retaining 0.25 as the load reference. Keep `p_mutate=1` initially: that changes one thing. The recorded masks contain 56 mutable inherited parameters; sparse mutation is a reasonable later alternative, but the current global `p_mutate` also thins cross-link mutations and changes their reach calculation.

   Measure E-G, X0 offspring and X+ offspring on identical mazes. Report offspring separately from unchanged elites. Reconsider the bound using competent offspring and intervention sensitivity; dividing by X0’s current catastrophic load would merely permit more damage. A preserves the original scientific comparison, with conclusions conditional on the revised optimizer.

   **B changes the question** to whether links alone can improve fixed modules. Moreover, if every other parameter is frozen, cutting all links returns exactly E-G: **P2 and P1-cut become the same performance contrast**, rather than complementary evidence. P1-info remains useful, but coadaptation is excluded.

   **C has no demonstrated payoff.** More elites may preserve competence while reducing exploration; larger populations buy more expensive draws from the same damaging proposal. Neither addresses the first problem. Changing the seed changes the population to which conclusions apply.

3. **Next pilot: about 2–2.5 additional hours, with a hard stop.**
   
   - First perform the saved-candidate check above and a paired generation-1 screen of inherited factors 0.05/0.10/0.25. Include a zero-mutation breeding check to exclude clamp or implementation effects.
   - Run **two seeds per weaker setting, X0 only, population 32, W=8, G=20**. Together this is approximately **19 minutes**, assuming proportional throughput. Choose using offspring retention and independent candidate performance, not population mean alone.
   - Run the chosen setting in **both arms, four paired runs, population 32, W=8, G=50**: approximately **93 minutes**, plus assays. Select the cross-link scale from the revised load screen.
   - Measure common-block candidate-minus-E-G curves; offspring-minus-parent effects; W=8 ranking stability against a larger block; competence; paired P2 differences; and intact/cut/mean-substitution effects with maze variability. Save populations, RNG states, selection records and validation scores every ten generations.

   This is a feasibility pilot, not a four-run significance test. Extend training only if independent performance or functional recruitment is still developing. Flat X0 alone is not a stop criterion. The formal budget needs revision: **eight runs per arm × 300 generations already projects to 18.7 training hours**, before final assays.

4. **Owner decision:** weaker mutation and its calibration are design amendments within the existing question; freezing modules, changing the seed, or replacing P2’s meaning are scientific-direction choices. Publish the amendments before formal work and retain attempt 1.

   There is also a concrete budget issue: D251’s 4.5-hour pilot allowance **includes** the approximately three hours already spent. This proposed follow-up exceeds that cumulative allowance, although it fits within E4’s 30 hours. The owner must explicitly approve that revised pilot allocation; approval to rerun the unchanged design does not establish it.