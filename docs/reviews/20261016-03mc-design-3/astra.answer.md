**revise** — narrow corrections to the validation contract and numerical wording. I found no reason to change the hypotheses, sample sizes, or primary tests.

1. **The settling gate does not enforce the stated limit.**  
   [DESIGN.md:355](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:355) permits at most two genomes per graph to change any label. [p4mc_equivalence.py:100](/D:/Claude/random/wormWars/scripts/p4mc_equivalence.py:100) instead checks each label’s count separately.

   I reproduced a counterexample using the actual functions: two genomes change “settled,” two different genomes change “remaining,” and none changes “both.” **Four genomes are affected, but `judge()` passes.**

   **Fix:** count the union of genomes with any changed label and require that count ≤2; add this counterexample as a regression test. The recorded run’s zero changes remain valid.

2. **The new tick-comparison claim is still too strong.**  
   [DESIGN.md:436](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:436) and [DECISIONS.md:8832](/D:/Claude/random/wormWars/DECISIONS.md:8832) say ticks 20–40 are within simulation error. [power.json:174](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/power.json:174) gives **0.8306, 0.8464, 0.8482**, respectively.

   With 5,000 independent simulated studies per tick, the tick-30-minus-20 difference is **2.15 Monte Carlo standard errors**; tick-40-minus-20 is **2.40**. The blanket claim is not supported merely by quoting approximately ±0.01 uncertainty.

   **Fix:** report the three estimates, say ticks 30 and 40 are nearly tied and tick 20 is slightly lower, and retain the disclosed rationale for choosing tick 30. No endpoint change is needed.

3. **One tolerance-margin statement needs a rounding correction.**  
   [DESIGN.md:353](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:353) still says “at least 4.5 times.” The recorded worst per-genome tick-30 deviation is \(2.23484435\times10^{-5}\), giving \(10^{-4}/\text{deviation}=4.4746\).

   **Fix:** write “about 4.5 times.” This is a numerical wording issue, not evidence that the tolerance is inadequate.

4. **The substantive equivalence findings from v2 are fixed, apart from finding 1 above.**  
   [p4mc_equivalence.py:143](/D:/Claude/random/wormWars/scripts/p4mc_equivalence.py:143) now checks aggregate retention, pre-tanh arrays and terms, and genome-level settling labels. I independently recomputed the JSON’s maxima and pass flags across **24 graphs and three conditions**. The quoted retention error **4.0678×10⁻⁷**, pre-tanh aggregate error **2.1302×10⁻⁷**, zero label changes, counts **26/171/37**, and **0.2401-hour** duration agree.

   The worst graph is correctly named. The new [pre-tanh reference test:130](/D:/Claude/random/wormWars/tests/test_exp03_twin.py:130) passed and caught an in-memory sign-reversal sabotage. **No further design fix requested.**

5. **The power-model findings from v2 are fixed.**  
   [power.py:160](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/power.py:160) preserves joint N2 uncertainty and batch-0 sharing; it adds regression posterior uncertainty, simulated Q-C, and the stated Student-t sensitivity.

   I reproduced **the entire `power.json` exactly**, including input hashes, with input arrays cached and the output write intercepted in memory. The quoted probability tables, correlations, regression quantities, and tick estimates agree with the artifact. The remaining problem is their interpretation in finding 2. **No further model change requested.**

6. **The other v2 findings are addressed at design level.**  
   The control contrast and intersection-union claim, batch-0 controls, tie-break, degree rationale, interval specifications, known-SE qualification, Q-D failure wording, dirty-tree disclosures, build-overrun qualification, and D286 corrections are present. **No additional design blocker found.** Enforcement by the unfinished runner remains for the planned code review.

All **20 targeted CPU tests passed**. I made no file changes and ran no GPU work. I did not independently regenerate the GPU equivalence measurements or complete the separate formal-run implementation review.