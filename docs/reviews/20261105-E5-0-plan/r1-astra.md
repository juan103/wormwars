**Verdict: fix then proceed.** The basic task is workable, but draft 1 has several gaps that could change the interpretation after seeing results. I checked the scope, both archived reviews, `world.py`, E1’s configuration/controllers, and the relevant equivalence contract. No files were changed.

1. **Scope fidelity: mostly faithful, with three substantive omissions.**

   The controls, frozen whole-brain reuse, captures-only scoring, accounting and separation from E5-1 are consistent with the accepted scope. Deferring the prey-graft check until H3 is appropriate.

   However, the scope explicitly requires **reliability for a reused hunter to qualify**; §6 drops that requirement. Cue dependence also becomes optional outside two settings, and the route check no longer establishes loop completion. Those need fixing or explicit narrowing of the claims. [Accepted qualification rule](D:/Claude/random/wormWars/docs/E5/SCOPE.md:218)

2. **Task mechanics: head-centred scent is acceptable; the ledger needs a correction.**

   Using `pos` for both scent and reach is a reasonable, declared design choice. It gives a straightforward ghost correspondence with Task N. Keeping the same anchor for ghost, reach and bite also makes their comparison interpretable. It does mean the scent directs pursuit toward the armoured head; that is part of this task’s geometry.

   **D − R = 6.5 is defensible.** Your triangle-inequality argument is correct for a static reach target. However, this is a **second change from the scope**, which required D from the hunter. Mark it explicitly. Once candidates can be skipped, replace “life k at centre k” with a separate life index and sequence index; log the accepted sequence index.

   **The stated removal booking is incomplete for ghost/reach.** A living prey still has energy when replaced:

   | Capture rule | Book as removed | Book as respawned |
   |---|---|---|
   | Ghost/reach | Remaining prey energy + body mass | E_prey + body mass |
   | Bite | Corpse body mass | E_prey + body mass |

   For bite, the lost energy and transfer inefficiency are already handled by combat. Booking only removed body mass while booking fresh energy as respawned would break the ghost/reach ledger. T0’s `1e-5` is a **relative error against starting total energy**, not an absolute tolerance. [Combat and reaping](D:/Claude/random/wormWars/wormwars/world.py:1141), [ledger definition](D:/Claude/random/wormWars/wormwars/world.py:1290)

   Pinning through `_resolve_move`, removing corpses, replacing prey within the tick, and horizon-only `done()` are sound. Specify combat stage 0 for ghost/reach, one capture maximum per tick, next-life activation at `tick + 1`, and refresh geometry/body state after respawn. Preserve the hunter’s state.

   Finally, the oracle is a **privileged pursuit reference**, not a ceiling. Its success demonstrates feasibility; its failure does not establish geometric impossibility. E1 already documents that its navigator sometimes beats the oracle. [E1 correction](D:/Claude/random/wormWars/experiments/E1-navigation/RESULTS.md:173)

3. **Calibration: not yet fixed enough.**

   **E_prey:** the proposed controller does not maintain the stated contact geometry. E1’s oracle always steers toward the target/head; starting beside the midpoint does not make the ensuing contact a sustained flank bite. Nor does multiplying a median damage rate establish a ten-tick kill time under changing contact.

   Define a controlled contact fixture or explicit contact-holding policy, including orientations and offsets. Prevent energy capping or death during damage measurement: `_combat()` caps recorded damage at remaining energy. Define the statistic precisely—preferably each world’s damage over 20 contact ticks divided by 20, then the median across worlds—and stop calibration if contact is insufficient or the reference damage is zero. Subsequently measure actual kill times at the selected energy. [Oracle implementation](D:/Claude/random/wormWars/wormwars/e1/controllers.py), [damage cap](D:/Claude/random/wormWars/wormwars/world.py:1182)

   **Routes:** mean speed and a displacement-window check do not establish waypoint traversal. Add ordered waypoint visitation and loop completion, with a separate sufficiently long check at low speeds: at nominal `s = 0.1`, 300 ticks provide only 10.5 cells of travel. Also specify the closing edge’s spacing, initial heading/next waypoint, and what “starting phase” means when waypoint 0 is always the spawn. Make calibration changes global across speeds, and specify **stop for route-controller revision** if gain 4 plus spacing 8 still fails.

   **H2b:** the movers are reasonable. State normal innovations, initial random-walk state and turn clamping explicitly, and report stalls as well as realised speed. “Scripted prey read nothing” is inaccurate: the wall-follower reads collisions. Hunter-only masking must preserve that input.

   **Tuning:** §3 tunes three settings; §§5–6 promise tuning for every setting. Choose one. Either tune each evaluated setting, or freeze an explicit mapping from those three parameter sets to every condition and call the remaining evaluations transfers. Include H1-reach and H2b’s wall-follower explicitly. Also resolve E1’s wall-follower grid’s **own-body reference level**, because its thresholds are offsets from that measured value. [Grid construction](D:/Claude/random/wormWars/scripts/e1.py:374)

4. **Equivalence: the proposed checks are useful, but distinguish their purposes.**

   Reusing E1’s gate worlds for an engine regression check is acceptable. It does not constitute a fresh navigator claim.

   Require zero tolerance for the same-platform CPU ghost comparison at matched batch compositions. Alongside counts/events, compare hunter positions, headings, inputs and neural states on a small diagnostic set. Exercise the scent probes too.

   **Bind an independent pre-change engine reference.** Comparing HuntWorld with `navigate` after both inherit changed hooks can miss a shared regression. Passing existing tests helps, but does not replace the old-versus-new comparison required by T1. Include a multi-swarm combat case because the attack hook affects that path. [Equivalence contract](D:/Claude/random/wormWars/docs/foundations/T1.md:109)

   The CPU–CUDA gate check is a historical compatibility target, not engine equivalence. The proposed 0.05/99% thresholds are permissible prospective targets, but **integer scores do not justify expecting 99% identity**: small trajectory changes can change an arrival tick or count. If this check fails, compare unchanged Task N on CPU with the CUDA record to identify whether the discrepancy predates Task H.

5. **Decision rules: the numerical choices are acceptable; the definitions need tightening.**

   I accept **0.80 reliability, a >0.5 capture margin, 0.5 for “too easy”, and 0.25 as a warning** for this exploratory feasibility check. These are design choices, not uniquely correct numbers. The 0.5 ratio is a reasonable compromise between the earlier proposals.

   Required fixes:

   - Restore the **0.80 reliability lower bound for each qualifying reused hunter**.
   - Run the constant-scent probe wherever full qualification is claimed, or label unprobed outcomes “capture-performance criterion met; cue dependence untested.” Avoid changing the meaning of “qualifies” at `s = 0.5`.
   - Define “best baseline” inside the bootstrap. A clear implementation uses shared resampled worlds and recomputes the maximum baseline mean in each resample, for both differences and ratios.
   - State that lower/upper bounds use the 5th/95th percentiles. Specify whether the 0.25 warning uses the point estimate; define zero-denominator handling.
   - Distinguish demonstrated failure of reliability, baseline advantage and cue dependence. The present “demonstrated failure” rule covers only advantage.
   - Report the **first failed tested speed**, with any later recovery visible. It is not an established monotonic cutoff.

   “Solvable” and “too easy” can both hold under these rules; make that explicit rather than treating them as mutually exclusive outcomes.

6. **Cost: benchmark first is right; revise the pruning details.**

   The neural count is **80**, not 81. Four tuned controls plus four frozen references, oracle and stationary make **10 scripted evaluations** unless some are explicitly deduplicated. That gives approximately **1.20 million evaluation/probe episodes**, before calibration and equivalence. The three stated E1 tuning grids add 93,504 episodes if all combinations are evaluated on 64 worlds.

   Thinning speeds is reasonable, but retain **1.0**, the shared-speed endpoint. I would reduce generation-0 coverage early and prefer reducing evaluation worlds to 256 **before filtering moving-prey evaluations by H1-bite success**. Static failure does not imply moving-prey failure; this selection could omit informative transfers. If retained, describe it as a selected-subset survey, with no full-family fall-off claim.

   Step 3’s savings are unknown at benchmark time. Budget conservatively or define a staged budget decision. Specify the clock—elapsed CPU-run hours or summed core-hours—coverage across attempts, and the outcome if all reductions still exceed eight hours.

One factual correction: **“outside every earlier range” is false**. 04a abandoned a range beginning at 997,000,000 after a smoke run touched 24 IDs. The different run seed means these are different worlds, so this is not itself contamination; correct the wording and freeze the exact IDs used. [04a record](D:/Claude/random/wormWars/scripts/e04a.py:79)