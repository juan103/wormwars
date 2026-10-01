**Verdict: fix (text).** The recorded qualification and design-trigger decisions hold. Several interpretations overreach.

Reviewed `roadmap` at `7eac620`. There is no README inside `E4s-0`; I reviewed the [parent README](D:/Claude/random/wormWars/experiments/E4s-stereo-module/README.md). No files changed.

I independently reproduced all sweep bootstrap intervals and classifications, qualification intervals, population classifications and selection indices, and robustness shares from the counts. Key results check out: L1 **5.176758**, lower bound **5.098608**; **16/16** selected G0 bests “uses”; robustness shares **0.920896, 0.776119, 0**; compute **0.226257 hours**.

1. **“Small k adds at most +0.08 … (one champion +0.19)” is false.**  
   [README:32](D:/Claude/random/wormWars/experiments/E4s-stereo-module/README.md:32), `sweep.json`: at k=1, `e2 es run00` gains **0.267578**, and `e2 extension run04` gains **0.208984**. The quoted range describes **first improving k**, where **23** champions gain 0.017578–0.080078 and one gains 0.191406. Correct that restriction in the README and the “24 … and one” wording in RESULTS. “Only large gains pay” also overstates this: small gains sometimes pay modestly.

2. **The sweep summaries mix ranges and aggregation.**  
   [RESULTS:56](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/RESULTS.md:56), `sweep.json`: “The median champion’s score” is actually the **median across champions separately at each k**, not one champion’s trajectory. README’s “k=2–16 … median … 0.69–0.83” omits **1.568359 at k=2**; that narrower range applies to k=4,8,16. Replace “k≥32 helps all” with **“the tested k=32,64,256 help all.”**

3. **“Shrinks at every stage” is not supported as written.**  
   [RESULTS:20](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/RESULTS.md:20), README:35, `attenuation.json`: the table pools absolute gains across **champion–neuron observations**, rather than first producing one value per champion. Even those pooled medians rise slightly from RIA to motor neurons at m=0.08: **0.073396 → 0.073954**. Individual champions need not decline stage by stage. Say **“pooled median differential responses are generally smaller in the downstream groups”**; this does not establish serial attenuation through a recurrent circuit. Also, sensory |K_C| at m=0.02 is **0.814838**, rounding to **0.81**, not 0.82.

4. **The mutation conclusions exceed the measurements.**  
   [RESULTS:176](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/RESULTS.md:176): “the valley … predicts that free mutation … will not keep a strong gain” contradicts the plan’s explicit limitation. The sweep never measures weight mutations. Likewise, “destroys the module” and README’s “survives … but not at 1×” convert **one-generation carrier scores** into functional or evolutionary survival claims.  
   `robustness.json`: at 1×, **195/256** children score zero, but **61** score above zero, **39** retain at least half, and **7** exceed the parent. At 0.25×, **78/256** score zero and **134/256** retain at least half. Report those distributions and the medians; leave survival under selection to E4s-1. No mutant differential-gain or “uses” measurement establishes destroyed computation.

5. **The bounds explanation states an unmeasured counterfactual.**  
   [RESULTS:108](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/RESULTS.md:108): “half of each perturbation … is removed” should be **“outward proposals are clipped, occurring with probability approximately one-half per bounded parameter.”** `Genome.mutate` does not halve each perturbation. “Better than … an interior point” was not tested. Say clamping changes the effective mutation distribution and limits generalization to interior parameter settings.

6. **“The graft does not work on this background” hides the most informative result.**  
   [RESULTS:146](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/RESULTS.md:146), repeated at 175: `populations.json` classifies 04a run 2 **“unclear,”** with these paired results:

   | Module input | Mean score |
   |---|---:|
   | Real | 0.885742 |
   | Mean-only | 2.643555 |
   | Swapped | 0.019531 |

   Re-derived real-minus-mean: **−1.757813**, 95% CI **[−1.819336, −1.697266]**. Real-minus-swapped: **+0.866211**, CI **[0.834961, 0.897461]**. Correct to **“fails ‘uses’; real differential input substantially reduces performance relative to module mean-only input.”** This paired comparison is more informative than the historical, different-world E2d comparison. The average right-turn command does not establish the mechanism.

7. **“On 64 worlds most are expected to be unclear or no-benefit” supplies an unsupported explanation.**  
   [RESULTS:134](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/RESULTS.md:134), `populations.json`: limited precision can produce “unclear”; “no material benefit” requires both intervals *inside* the equivalence band. **398/512** backgrounds score zero with real input; **294** score zero under all three probes. Report the observed categories and pervasive inactivity without attributing both categories to sample size.

8. **“Reached 90% within 3 ticks” has an indexing error.**  
   [RESULTS:116](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/RESULTS.md:116): `ladder.json` records `t90=3`, but `diagnostics.settle` returns a **zero-based trace index**, and `open_loop_dynamics` records after each update. That is the **fourth post-change update**. Correct the text and document the indexing convention.

9. **“Every number below comes from … this folder” is incorrect.**  
   [RESULTS:8](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/RESULTS.md:8): 0.098 comes from `development-records/gain-probe.json`; 2.64 from E2d’s `part-b.json`; 8.51 from E1’s `freeze.json`. These values check out. Cite them explicitly, and describe **8.511719 as the best tuned score at k=256 on 256 E1 tuning worlds**, not a paired benchmark.

10. **The README overpromises reproduction.**  
    [README:58](D:/Claude/random/wormWars/experiments/E4s-stereo-module/README.md:58): same GPU, environment and composition are insufficient for the repository’s exactness claim without `replay_mode()`. The E4s-0 execution path does not enable it; registration guards do not enable determinism. Remove the implied exact-repeat guarantee. Also, the “Reproduce it” commands reject an ordinary current checkout because its completed records already exist (`scripts/e2.py:587`). Document an isolated reproduction procedure, or label these as the original execution commands.

For **E4s-1**, retain random N2 and the 0.25× factor: both follow the stated rules. Add these implications:

- Treat C2 as a **harmful host–graft interaction**, reporting signed probe effects alongside its categorical outcome. Do not preassign a negative outcome from “unclear.”
- Track **turn offset and differential gain separately**. Zero navigation score need not mean lost amplification; asymmetric mutations could instead introduce a large turning offset. That is a hypothesis to test.
- Report mutation-score distributions and effective clipping, not just medians. The carrier assay does not establish robustness while the host—including motor neurons—also evolves.
- In R, all 20 chosen edge magnitudes are **3**, so magnitude permutation does nothing: this comparator’s random control varies **signs only**. State that explicitly.
- Preserve fresh requalification and the pending CUDA-state and inert-graft gates; these results do not discharge them.