**Verdict: fix then publish.** The M6 numbers and credits check out. The remaining fixes concern scope and wording; no further run is needed. The archived `draft5.md` is byte-identical to `SYNTHESIS.md`.

I would make these four fixes:

1. **Update the claims presented as applying throughout.** The [genome definition](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:83) says “generation 0, never evolved”; the [limits](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:418) say “every result” concerns the ramp, other inputs are untested, and interventions are on N2. These no longer describe the whole synthesis: M6 includes evolved champions, changed input banks, input removal, and foraging interventions across graph families. The annotation about evolved brains addresses only part of this. Add an explicit dated scope correction, preserving the earlier wording as historical.

2. **Restore the literature pointer’s attribution and bounded scope.** [“The worm’s best-described turn memory is held in oscillation phase”](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:502) is stronger than the report. It introduces an unsupported ranking and states the proposed carrier as established fact. Use: “In the most directly relevant study checked, Dunn et al. place the turn memory in distributed oscillation phase, which this probe does not assay.” Section 7 already handles this correctly.

3. **Keep input dependence tied to the tested histories.** At [section 7’s two-kinds interpretation](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:342), change “needing the food input to keep two states” to “whose two tested histories merged when food input was removed.” The [results explicitly retain the possibility of other input-free attractors](/D:/Claude/random/wormWars/docs/memory/M6-OUTLAST-RESULTS.md:131). The synthesis should retain that qualification.

4. **Make the T0 lesson unambiguous.** [“Showed it was not specific to the single-nose task”](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:476) is defensible if it means that losses also occurred in T0, but invites the stronger interpretation previously rejected in review. Say exactly that: “The T0 champions showed that losses also occurred in the stereo task.” Keep the nearby distinction between no detected difference and established equivalence.

The numerical audit agrees with the results files and committed records:

| Item | Checked |
|---|---|
| M6-0 | 1/102 champion switches versus 5/408 drift; 101 fading; family medians 39–46.5 ticks; approximately sixfold starting amplitude |
| Literature | 44 sources, 30 retrieved full texts |
| Step 1 | 55 held under Z, 54 returned overall, 112 faded, 111 of those returned to the rising-start state; held-status agreement 163/169 |
| Step 2 | −24.5%, −7.5%, −12.7%, −35.1%; interior arm −6.0%; matched T1−T0 −2.8 percentage points, interval −6.1 to +0.4; validation ratio 0.233 |
| Compute | 0.96, 0.20 and 3.64 hours; M6 totals 4.80 hours before display rounding; cumulative total 117.23 |

Two useful numerical clarifications: the −0.015 switch contrast is **averaged over 30 blocks**, with unresolved drift genomes counted as non-switches, rather than the pooled count difference. Also, the 54 recoveries are **53 held genomes plus the unresolved genome**, not 54 of the 55 that held.

On the prohibited claims: section 7 avoids them. It leaves foraging benefit open, rejects a tuned-optimum inference, retains the warm-up hazard and non-equivalence caveat, and does not locate the cost in sensory/motor neurons. It makes no dose-response claim, behavioural-use inference from persistence, or biological-validation claim. Both “exceeded” comparisons remain beside the floor caveat; the table also flags it. M6 is explicitly exploratory.

**The M6 credit allocation matches D376–D383.** I found no attribution requiring correction.

**The stop is faithful to D379.** It preserves M5’s preparation and the unresolved scientific questions without scheduling more work. The roughly 100× reset cost is traceable to the design note; describe it as a rough estimate, with no implication that paying that cost would necessarily isolate memory cleanly.