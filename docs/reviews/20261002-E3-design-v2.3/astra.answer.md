**Verdict: revise.** The remaining repairs concern the memory assays and test-world separation. The engineered organism itself passes the checks I ran.

I checked `roadmap` at `9dc604e`, both reviews, D161, the code and training records. I reproduced the geometry JSON and reconstructed the proposed organism in memory for CPU `Brain.step` checks. No files changed.

**1. Resolution of the v2.2 items**

Resolved at design level: hold-reference timing; bistability versus controllability; two-tick setting stimulus; release-test gain floor; balanced initialization; mutation-distance/null wording; B’s spawn cap; sensory scaling and lower component levels; equal final validation; deferred census testing; S2-b’s missing outcome and four-pair qualification; indistinguishable medians; B-task’s gaps, relays and reduced-budget comparator; reserve/minimum-budget rules; and classification scope.

**Two items remain incompletely resolved:** the snapshot \(K_D\) measurement and the monostable release assay’s starting state. Missing goal-phase medians also remain unspecified.

**2. Remaining problems and numerical checks**

- **The revised hold works.** After opposite two-tick pulses, the engineered q reaches ±3.05328, settles to ±1.91501045 after 20 unforced ticks, and remains unchanged through the next 580 ticks in my CPU check.

- **Open-loop retention is valid, but the gain probe is still ambiguous.** For Stage 2/3, \((q,RA,RB)\) forms an autonomous subsystem once external levels are zero. Preserve all three states, including relay decay, and its dynamics can be reproduced open loop. This does **not** make the copied-state gain measurement instantaneous: the referenced component protocol includes 50 ticks of preconditioning. If q evolves during those ticks, the release assay measures retention beyond \(D\), not at \(D\). Explicitly hold the saved q during the gain readout, or define a finite-duration response and include that duration in the retention criterion. Bitwise equivalence still needs the repository’s composition-specific checks. [Assay specification](D:/Claude/random/wormWars/docs/E3/DESIGN.md:242)

- **“Resting state (100 ticks with no levels)” is false in general.** For allowed monostable parameters \(w_{qq}=0.99,\ b_q=0.01,\ \tau_q=20\), `Brain.step` gives **q = 0.04865** after 100 ticks from zero; the fixed point is **0.28209**. Initialize at the computed equilibrium with resting relays, or explicitly define a 100-tick preparation from a specified state and stop calling it equilibrium. [Release setup](D:/Claude/random/wormWars/docs/E3/DESIGN.md:269)

- **The memory classes now separate structure and control correctly.** They remain operational classes under the chosen pulse, settling deadline and delay. “No memory” should mean failure of this assay, not absence of every usable transient memory. Near-degenerate roots and missing phase medians need deterministic handling.

- **Balanced initialization works relative to the carrier.** Equal comparator inputs cancel the modules’ added turn. Total settled turn is **0.2**, not zero; my 100 sampled selectors reproduced that within float32 rounding. Qualify “zero turn offset” accordingly. [Initialization](D:/Claude/random/wormWars/docs/E3/DESIGN.md:291)

- **Both caps and the expanded component grid check out.** Geometry reproduction gives minimum acceptance **11.77%**, median **17.7975%**. The reported 0.0100 is scaled **head** scent, not an actual bilateral nose minimum; a separate interpolation sample reached about **0.00706**, still above 0.005. Across the specified component grid, active \(K_D\) was **31.60–35.63**, inactive **0.0595–0.0675**. Startup passed at tick 10; recovery exceeded 99.99% of settled gain ten ticks after the pulse.

The measured training batches also support the budget’s approximate scale: **1.3545–1.4308 hours** each.

**3. What pre-registration must pin**

- The corrected probe/preparation protocols; setting tolerance; pulse-to-goal mapping; \(D\)’s leg population, censoring and rounding; reset timing/pass criterion; and missing-median/root-boundary handling.
- **Separate Stage 1 calibration worlds from final test worlds.** Deriving \(D\) from “Stage 1’s test worlds” before training conflicts with keeping test worlds untouched until all champions freeze. Census deferral fixes only the census issue. [Conflicting requirements](D:/Claude/random/wormWars/docs/E3/DESIGN.md:328)
- Exact control/B-shared genomes, the complete B-task initialization—including output weights and comparator time constants—and Stage 3 mutation masks and champion selection.
- Selection-world allocation and random-stream sharing across arms; gate denominators/geometric maximum; bootstrap settings; and identities of retained runs under reductions.