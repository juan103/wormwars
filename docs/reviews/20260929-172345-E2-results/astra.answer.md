**fix** — text corrections before publishing. The registered decision is correct; I found no reason to rerun or rework E2.

**Must-fix items**

1. **Correct three numerical details.**
   - [RESULTS.md:71](D:/Claude/random/wormWars/experiments/E2-optimizer-screen/RESULTS.md:71): GA validation at generation 100 is **1.5048828125 → 1.50**, not 1.51.
   - [RESULTS.md:165](D:/Claude/random/wormWars/experiments/E2-optimizer-screen/RESULTS.md:165): accounting gives **16,630.450494 seconds → 16,630**, not 16,631. The stated 4.62 hours remains correct.
   - [DECISIONS.md:3677](D:/Claude/random/wormWars/DECISIONS.md:3677): the formal projection started at **10:34:39 UTC**. Either start the chain at 10:34 or label 10:38 as the pilot’s start. The 4.74-hour total includes projection.

2. **Qualify the cue claims** — [RESULTS.md:59](D:/Claude/random/wormWars/experiments/E2-optimizer-screen/RESULTS.md:59), also §3’s “never found a cue-follower.” Similar aggregate means do not establish that run 2’s count “does not depend on the cue at all.” Its real-versus-mirrored counts differ on **75/1,024 worlds**, and real-versus-constant on **51**. Say its champion showed **little aggregate performance advantage from the real cue**. Only the selected champion received these probes; “never found” overstates what was measured.

3. **Correct the floor interpretation** — [RESULTS.md:173](D:/Claude/random/wormWars/experiments/E2-optimizer-screen/RESULTS.md:173). “1,000 generations of either optimizer add little” misstates the formal ES budget: **623 generations**, including generation 0. Also, the floor is a registered diagnostic trigger, not an equivalence finding. The observed gains over random sampling were **0.3562 for GA and 0.4808 for ES**—approximately **22% and 30%**. State those gains and the trigger without declaring them negligible.

4. **Narrow the extension’s causal interpretation** — [RESULTS.md:124](D:/Claude/random/wormWars/experiments/E2-optimizer-screen/RESULTS.md:124). The extension supports further improvement with additional work. It does not establish that the tuning charge caused the “keep GA” outcome: even afterward, ES–GA is **0.370483**, below 0.5. Suggested wording: “The ES improved beyond its formal allowance; the extended comparison still falls short of the registered mean margin and uses more charged work.”

Record these as dated corrections quoting the original statements, as AGENTS.md requires.

**Suggestions**

- Quantify run 2’s influence without excluding it: it contributes **+0.152466** to the overall ES–GA mean difference; the other seven paired differences average **−0.031808**. Reliability is central to the observed comparison.
- Clarify §6 as “every **formal** method’s mean”: the extension’s 2.331 exceeds M-avg’s 2.199. Scripted controls demonstrate task headroom, not an attainable ceiling for this bounded neural implementation. Similar scores also do not establish similar navigation mechanisms.
- Explain selection optimism beyond the extension’s 42 checkpoints: distinguish validation selection from selecting methods or standout champions after inspecting hold-out results. Retain the registration’s eight-run, procedure-level limitation.

For the diagnosis, I would prioritize:

- **Noise and candidate nomination:** reevaluate fixed genomes and perturbation pairs on independent eight-world blocks and larger reference sets. Measure rank stability, zero/tied fitness and antithetic-pair discrimination. Compare the GA’s current-generation nominee, random sampling’s best-since-checkpoint nominee and ES’s mean; close champion validation/hold-out scores do not establish reliable training rankings.
- **Saturation:** inspect trajectories and sensor-to-motor responses of strong random champions, successful optimized champions and GA run 2. Test weak steering gain, ineffective differential sensing, motor saturation and wall behavior directly.
- **Budget:** preregister additional matched-work comparisons with fresh evaluation worlds and fixed checkpoint opportunities. Include smaller σ values because the pilot selected its grid boundary; keep tuning costs explicit.

**What I checked and found correct**

Independent recomputation from all hold-out counts gives:

| Quantity | Recomputed |
|---|---:|
| GA mean | 1.960937500 |
| ES mean | 2.085571289 |
| Random mean | 1.604736328 |
| GA median | 2.130859375 |
| ES champions strictly above median | 5 |
| ES − GA | +0.124633789 |
| Random − GA | −0.356201172 |

Both replacement criteria fail; the floor fires. The quoted outcome and floor exactly match §8, and README’s status and decision summary are accurate.

I also checked all checkpoint validation counts and champion choices, pilot totals and selection, pairing hashes, random candidate nominations, extension sources, SDs, oracle fractions, probe ranges, flat generations, clipping and episode counts. The reported checkpoint ranges use the full series, not subsamples. The remaining numerical summaries check out, including **37.74%** extra charged extension work and **4.739344 hours** overall.

Per-stage accounting matches differences between committed ledger versions. Records show one completed attempt per stage, and guarded code/configuration are unchanged from the binding commit. No files were modified.