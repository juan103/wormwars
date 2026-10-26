**Verdict: revise.** Keep the factorial, fresh hosts, two block draws and paired risk differences. I checked both reviews, M4d’s arm records and the classifier.

1. **The joining observation is overstated; I would drop U_HX.** At fixed summed magnitude, the off-diagonal contribution to S2 is \(S_1^2/E\), so it falls exactly. **S3 need not fall for every paired support draw.** Moreover, predicting Δ_count < 0 requires switching probability to increase monotonically with the summary; stronger coupling can instead produce unsettled dynamics. This contrast tests a prediction of a specified summary model, not which summary governs the mechanism.

   U_HX is useful but secondary. Its projected **3.59 hours** would be better reserved for classification checks. Nine arms’ initial cost is indeed **32.33 hours**.

2. **Fresh hosts: agree.** Losing pairing with M4d is acceptable. Fresh hosts and genomes provide a cleaner prospective test after the R > D observation. Keep Stage 0 descriptive and prevent it from changing the primary specification. Also, S3 is a spectral proxy, **not an exact expected signed spectral radius**; the isolated block’s eigenvalues do not determine the embedded network’s stability. The [implemented Jacobian](D:/Claude/random/wormWars/scripts/memory_m2/equilibria.py:40) includes saturation, gaps and leak.

3. **Two margins: acceptable, with two reporting fields.** Report direction beyond ±0.001 separately from exclusion beyond ±0.004: an interval such as [0.0015, 0.0030] supports both “raises” and “excludes effects of magnitude ≥0.004.”

   Specify simultaneous coverage: **95% intervals each give a Bonferroni guarantee of 90% jointly; use 97.5% each for 95% jointly.** Coverage simulation needs a predetermined failure response, especially for exclusions. M4d’s [coverage exercise](D:/Claude/random/wormWars/docs/memory/M4D-PLAN.md:144) already showed severe failure under sparse host responses; taking the bootstrap/t hull does not fix that.

4. **22,000 ticks: agree as a finite-horizon endpoint. Audit: revise.** Preserve the original write amplitude, shift every observation window, and retain the additional 20,000-tick certification cap. The existing [classifier](D:/Claude/random/wormWars/scripts/memory_m2/pilot.py:363) cannot simply be given a longer trajectory unchanged.

   **256 cases with 99% agreement is too permissive:** it allows two changes, and even zero changes gives a one-sided 95% upper bound of approximately **1.16%** on the change rate—larger than either margin. Audit all initially separate-state cases plus an arm/host-stratified fading sample. Prespecify that any switch/non-switch transition suspends the mixed-horizon reading pending broader validation. Size the fading audit against an explicit tolerated transition rate; 256 is a smoke check, not validation at 0.001. Fix the fallback in advance: original classifications with bounds, or unresolved—not whichever horizon reads better.

5. **Essential remaining details:**
   
   - Fit the descriptive dose curve on **U arms**, then assess W and K against it. Fitting W/K into their own reference curve weakens the proposed collapse check. Specify treatment of all-zero counts and non-finite slopes.
   - Freeze K’s feasibility, mixing checks and failure policy before outcomes. Subthreshold autapses can still matter through recurrent interactions; retaining host autapses is defensible, but T remains a package comparison.
   - Correct the historical wording: [D364](D:/Claude/random/wormWars/DECISIONS.md:11674) literally said “do not draft M4e,” not merely its smaller-block stage. [D365](D:/Claude/random/wormWars/DECISIONS.md:11682) subsequently authorizes the dense-block study.
   - Keep location, neuron-count size and further synthetic distributions deferred. Agree that this screen does not make M5 unnecessary.