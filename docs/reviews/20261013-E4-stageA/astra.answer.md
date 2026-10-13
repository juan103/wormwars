**Recommend (ii), gated on E4-D feasibility—not an immediate evolutionary run. Publish ordinary-task E4 as exploratory, and retain the remaining GPU budget until there is a credible transfer task and search protocol.**

1. **Reading 1 overreaches.** Stage A establishes that random cross-links impose severe generation-1 load. It does **not** establish that useful transfer is absent or that evolved P1/P2 nulls follow “by construction.” Random perturbations can harm a circuit even when selected connections could help. Opposite-goal signals might support avoidance, navigation or feedback; their usefulness is unmeasured. Moreover, the noses receive **goal scent plus trails**, not goal scent alone ([world code](/D:/Claude/random/wormWars/wormwars/e3/maze_world.py:350)).

   D256 needs a dated correction: `sensory_cut` removes nose-origin links **from both modules**, targeting both noses and comparators. It does not isolate “A’s noses into B’s comparators” ([link definitions](/D:/Claude/random/wormwars/wormwars/e4/evaluate.py:104)). Mean substitution still performs far below E-G; centering does not rescue performance. Report **“large cross-link mutation load, with greater rescue from removing nose-origin links; mechanism unresolved.”** Cross-talk is plausible, not settled.

2. **Reading 2 is right about reconsideration, wrong about the rule’s stated intent.** My [previous recommendation](/D:/Claude/random/wormwars/docs/reviews/20261013-E4-diagnostics/astra.answer.md) explicitly required the **combined mask** to retain 95% of E-G. The implementation follows it. That was an overly restrictive criterion for choosing a bias scale when the frozen-bias baseline itself fails. I would revise it openly, preserving the failed outcome.

   Separate **incremental bias load against frozen-bias children** from **total offspring load against E-G**. The existing incremental criterion selects **0.02**, not 0.01. That selection remains exploratory and is not confirmed by block B, which tested frozen biases.

3. **No obvious implementation artefact explains the large cross-link cost; there are qualifications.**
   
   - Frozen biases are matched between X0 and X+. Cross-link-only children reproduce nearly the same collapse, so inherited mutation is not required. Freezing biases nevertheless restricts compensation during subsequent evolution.
   - Child comparisons use matching seeds and composition: **116 strains × 16 mazes × 8 weys**. E-G is evaluated as **one strain**. Before treating its exact deficit—or “all links cut = E-G”—as numerically established, replay replicated E-G/all-cut controls at the children’s composition.
   - The cross-link screen uses only block A. Block B confirms the inherited-load problem, **not cross-link generalisation**. Reported SEs cover four mutation seeds on fixed mazes, not uncertainty across maze samples.

4. **Ranking: (ii) > (iv) > (iii) > (i).**
   
   - **(ii):** Best question per further compute: can this evolutionary procedure discover useful transfer when the task requires it? A hand-wired feasibility pass establishes possibility, not discoverability.
   - **(iv):** A defensible completed exploratory study. It concludes mutation sensitivity, not failure of evolved sharing.
   - **(iii):** Potentially worthwhile for ordinary shuttling, but introduces another task-design problem. Prefer it only if preserving shuttling is scientifically essential.
   - **(i):** Still scientifically legitimate, but currently poor value. Smaller factors are not guaranteed to pass; approaching zero can satisfy load while making exploration ineffective. A nonsignificant result would often remain **inconclusive**, not “no benefit.”

5. **Concrete next steps and cost for (ii).**
   
   Correct D256 and archive stage A: **zero GPU**. Review the **already implemented** [E4-D runner](/D:/Claude/random/wormwars/scripts/e4d.py), trial code and tests; then run the declared CPU scout → calibration → evaluation, with its oracle, invariance checks and stopping rules: **zero GPU for feasibility**. Complete the required GPU engine-equivalence check separately; its cost is not established here.

   Only after feasibility passes, design a bounded evolutionary pilot with all 32 slots initially zero, fresh blocks, protected cue isolation and cut/cue controls. Set a **proposed one-GPU-hour pilot cap**, not a runtime prediction; use measured throughput to size it. A formal run needs new review, pre-registration, push and an explicit budget decision. E4-D’s ceiling is currently undecided; E4’s roughly **25.6 hours remaining are not automatically transferred**.

6. **Put this to the owner:**

   > “The calibration shows that random cross-links strongly damage the starting circuit; it does not show that evolved sharing cannot help. I recommend publishing ordinary-task E4 as exploratory and completing E4-D’s CPU feasibility check next. If that passes, we will propose a separately budgeted evolutionary test of discovering necessary transfer. Do you prefer that direction, or closing E4 now? I do not recommend committing approximately 20 GPU-hours to the present main task.”