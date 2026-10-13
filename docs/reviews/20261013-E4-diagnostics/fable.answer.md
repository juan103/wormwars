Files read: the diagnostics, D250-D254, the arms, the module and comparator code, the L1 module file and the mutation kernel. Answer follows.

**Recommendation.** Scale the eight module biases down by a rule on a fresh block, with 0.02 as the expected winner. Keep weights and τ at 0.25. Keep the 32 slots free. Redefine the load bound on children against X0's children. Do not tie the slots and do not freeze the biases. Run a 20-minute generation-1 screen first, then rerun the pilot as designed at the chosen factors. The owner must approve a second pilot allowance and decide the formal run's size, which the pilot's timing now shows exceeds the ceiling at 300 generations.

**1. Reading 1 is right, and the code gives it a number.** The module's open-loop gain from a nose bias to each turn neuron is 18: nose to both comparators at 3 each side, push-pull, then 3 onto the motors. From a comparator bias it is 6. The carrier's rest-turn bias is atanh(0.2), about 0.2. So one nose-bias step at σ 0.0125 moves each turn neuron by 0.225, more than the rest turn itself. The diagnostics also show the cost is linear in σ:

| bias σ | loss in children, visits |
|---|---|
| 0.0025 | 0.4 |
| 0.005 | 0.9 |
| 0.0125 | 2.05 |

Linear loss means no safe threshold, only a smaller step. The one-parameter-per-child result fits this within noise, since a single hit costs about 0.7 and only 13% of children get one. A cheap test of the gain argument: split "biases only" into nose biases and comparator biases at 0.25. Prediction, stated before running: noses cost about three times what comparators cost.

**2. Reading 2 does not follow, and the diagnostics already argue against it.** The nose-to-comparator weights are the within-module twin of a nose cross-link: a step δ on NL→CL adds δ·mean(tanh NL), the same tonic term a cross-link would add. "Weights only at 0.25" includes those eight edges and costs nothing; the children end above E-G. So tonic parts at σ 0.02 are harmless at the magnitude a cross-link would have. The likelier cost of a cross-link is its fluctuating part: A's left-right scent difference, the gradient to the wrong goal, injected into B's steering while B is active. The direct test, two conditions and about 3 GPU-minutes: cross-links only at 0.25 with the inherited parameters frozen, versus the same children after mean substitution, which keeps the tonic part and cuts the fluctuating part. If the substituted twin is at E-G and the children are not, the cost is cross-talk, not offset. The function `mean_substitute` in `wormwars/e4/arms.py` already does the edit. D250's cross-link costs are void either way, since they were measured on a floor the biases had already halved.

**3. On (a), (b), (c).**
- **(a) Yes, by rule.** Candidates 0.05, 0.02, 0.01, with 0 as the fallback. Choose the largest whose children, with w and τ at 0.25, are within 0.25 visits of the frozen-bias children, paired on the same four seeds, on a fresh 8-maze block. Linear extrapolation says 0.05 fails and 0.02 passes. A small factor beats freezing: compensating a recruited link's tonic part needs bias mobility of about w·m, and σ 0.001 drifts 0.007 over fifty mutations, which is enough.
- **(b) Yes.** X+'s children within 0.25 visits of X0's children, same block, same seeds. Run the bias ladder first, then the cross-link load at the chosen bias factor, in that order.
- **(c) Keep 32 free slots.** The mirror pairing also has its physics backwards. A_NL→B_CL tied with A_NR→B_CR cancels the common-mode input and maximises A's left-right difference into B's comparator, which is the cross-talk term, not the tonic one. For comparator sources the tonic part does not cancel at all, since tanh(A_CL) has a nonzero mean whenever the worm turns one way on average. Report the cross-link cost as part of the finding.

**4. Detail or question.** A smaller bias factor applied identically to both arms is a training detail, and §6 already promises a pilot-informed specification before the formal run. Record it as a decision and in the pre-registration as pilot-informed. Tying the slots is a change of question: it hands evolution the sharing circuit the experiment asks whether it will find. If the owner wants it, it is a third arm with its own claim. Freezing the biases is a detail, but a bad one for the reason in 3(a).

**5. One consequence for the scale rule.** The functional unit of a cross-link is w times an activity of order 0.1, and the diagnostics place a noticeable effect near w·m of 0.001 to 0.01. The reach criterion of |w| at least 1 is fifty to a hundred times that, and no candidate will meet it at the pilot's lineage counts of 22 to 57 mutations. The rule will always fall to its load-bound fallback. Say so in the pilot-informed spec, and read recruitment by the cut, which P1 already does.

**6. The next pilot, in two stages.**
- **Stage A, about 20 GPU-minutes, exploratory.** Generation 1 on a fresh block, four seeds: the nose/comparator bias split at 0.25; the bias ladder; cross-links only at 0.25, 0.5 and 1.0 with their mean-substituted twins; the full X+ load at the chosen bias factor. This fixes both factors by rule and settles reading 2.
- **Stage B, about 3.3 GPU-hours.** The pilot as designed, both arms at the chosen factors, four paired runs of 100 generations, populations saved at every checkpoint. Report per generation the children's mean, the elites' mean, and the elite's score on the validation block. The best of eight training mazes is noise with a per-maze SD of 3.7, which is how attempt 1's elites drifted below E-G: lucky children displaced the unmutated E-G.

**7. What the owner must decide.**
- A second pilot allowance of about 4 GPU-hours. Spent so far 3.7 of 30, with 0.8 left in the first pilot's 4.5.
- Whether the bias factor is a detail, as I argue, or a direction change.
- The formal run's size. Attempt 1 measured about 15 seconds per generation per run. Eight runs per arm at 300 generations is about 20 GPU-hours before E4-D, over the ceiling. Choose fewer generations, fewer runs, or a larger ceiling before the pilot-informed spec is written.
- Nothing else. Mirror pairs and frozen biases should not be on the table.