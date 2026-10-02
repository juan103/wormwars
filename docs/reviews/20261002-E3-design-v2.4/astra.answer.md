**Verdict: proceed to pre-registration.** I checked `roadmap` at `79234c9`, AGENTS.md, both v2.3 reviews, D162 and the relevant engine code. The remaining problems can be settled in pre-registration.

**v2.3 items:** The frozen-state probe, equilibrium preparation, scaled windows, operational memory wording, mutation-balance qualification, carrier-offset correction, pulse-to-goal mapping, bitwise qualification and low-level component-test caveat are resolved. Random sampling’s replacement distribution is specified. Four items remain incomplete:

- **Calibration and stimulus contradictions:** [lines 408–414](D:/Claude/random/wormWars/docs/E3/DESIGN.md:408) still prescribe a two-tick setting stimulus and **test-world** phase medians, contradicting the new calibration protocol. Make calibration medians and champion-specific durations authoritative.
- **Fixed-point counting is not resolved correctly.** [Merging two nearby roots](D:/Claude/random/wormWars/docs/E3/DESIGN.md:309) can turn three roots into **two**, which neither class accepts. I calculated an allowed example: `w=2`, `b=0.5328398943`, roots approximately `−0.881712`, `−0.881035`, `2.506407`; the first pair merges. Strict sign-change detection also misses the engineered system’s exact grid root at zero. Handle exact zeros, tangencies and stability explicitly.
- **B-task’s output amplitudes remain unspecified.** [Antisymmetry](D:/Claude/random/wormWars/docs/E3/DESIGN.md:458) fixes signs, not the sampling distribution. “Stage 2’s draws” does not resolve this because Stage 2 freezes those outputs.
- **The descriptive release test for bistable non-latches** now exists, but “start at q’s computed equilibrium” does not identify which equilibrium.

**New issues and new pre-registration pins:**

- **B-task’s balance is stronger than stated.** If the incoming comparator columns, biases and τ are identical, CL and CR remain identical for *every* sensory input. Antisymmetric outputs then cancel completely: generation 0 is sensory-blind at the motors, not merely balanced at equal nose levels. Explicitly accept this starting condition or specify a different symmetry. Include self/cross edges in the construction.
- **Random sampling has a different structural prior.** Its tied draws have nine independent coordinates; GA mutation explores thirteen. The comparison is valid as specified, but its wording must identify both the different distributions and the permanent tying in random sampling. It does not isolate the search algorithm.
- **Assay details newly needed:** define stimulus-duration rounding, pooling across A/B, censored visits and the no-confirmed-visits case; choose the starting equilibrium(s) for the added bistable release assay. Restore the probe’s `m=0.05`, which disappeared in this revision.
- **Window interpretation:** `max(20,10τ_q)` is an acceptable operational deadline, not a guarantee of settling near a bifurcation. The revised operational wording accommodates that.

The calibration-world separation and holding `(q, RA, RB)` during gain readout address the previous substantive objections. None of the points above requires another design round before drafting the pre-registration.