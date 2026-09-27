# E1 design v2: confirmation review

I ran nothing. I read v2, D077 and both v1 reviews, and checked v2's claims in `world.py`, `fields.py`, `rollout.py`, `scripted.py` and `configs/interface.yaml`. The numbers below are hand calculations.

## Are my v1 points resolved?

| v1 point | Status |
|---|---|
| Must 1: odour does not reach the wey | **Partly.** The pilot and the σ grid are adopted, but the σ selection rule is wrong as worded (issue 1). |
| Must 2: energy physics | Resolved, except the ledger claim needs a mechanism (issue 3). |
| Must 3: gate statistics | Resolved. |
| Must 4: baselines | Resolved. |
| Must 5: 04a gate | Structure resolved. Numbers and run count are deferred to the freeze, which is acceptable if the freeze contains them. |
| Should-change and minor points | All resolved. The line-source probe is optional, which is fine. |

Code claims in v2 that I confirmed:
- The blur truncates at `ceil(3σ)` (`world.py:59`).
- Headcount scaling is at `world.py:369-372`.
- `_play` hard-codes `foraging_score` (`rollout.py:71`).
- `ScriptedBrain` reads only the food inputs (`scripted.py:27-28`).
- With `eat_rate` 0 and zero drain, nothing is eaten and nothing dies.
- The wey's own body stays below the crowding threshold, so there is no self-resistance.

## Wrong or new in v2

1. **The σ rule can pick a σ that leaves most legs starting blind.**
   - The rule tests a start at the *minimum* separation D, which is the best case, not the typical one.
   - With centres at least 3 cells from the walls, they lie in a 16×16 region. If D = 8, legs run from 8 to about 22 cells.
   - At σ = 3 the support is about 10.5 cells, so the rule passes. Only about 40% of legs start inside it; at σ = 4 about 78%, and at σ = 6 nearly all.
   - "Inside the scent" also needs a floor. The support edge is about 1% of peak on an axis and about 1e-4 diagonally, which steers nothing at k ≤ 32.
   - **Fix:** define the rule over the actual leg starts (previous centre to next centre). They are controller-independent, so this is computable without a rollout. Pick the smallest σ where a declared share of legs start above a declared usable-signal floor, or add a maximum separation.

2. **D has no value and no owner.** v2 uses D three times but never sets it or lists it among the pilot's choices. State which.

3. **"The ledger stays balanced by construction" is not yet true.**
   - `total_energy` sums the FOOD channel (`world.py:939`).
   - A blob with a set peak amplitude A has a rasterised mass that changes with sub-cell position, so each relocation would show as a ledger error.
   - **Fix:** snap target centres to cell centres, so every blob is identical. Alternatively, keep the target out of `fields[FOOD]` and add it only in `_sensed_food`.

4. **The `mirrored` probe works for rule 3, but describe it correctly.**
   - It reads the field at the point reflection of each sample point (`world.py:538-540`). That is a consistent decoy source at the reflected target, so it also works for M-avg.
   - The reflection is about (11.5, 11.5), not the arena centre (12, 12).
   - The displacement is twice the target's distance from that point. About 5% of targets get a decoy within 4 cells, and under 1% within R.
   - The navigator will park at the decoy, so its count can fall *below* the blind level, not "toward" it. Word the threshold accordingly.
   - I would also report the `constant` probe, non-gating, as this controller's own blind level.

5. **S-const's behaviour with no signal is unspecified.** `StereoProportional` has no constant turn, so with zero signal it goes straight, slides along a wall and jams in a corner. Define S-const as `StereoKinesis` with slow = fast and the turn in the grid, including 0.

6. **The implementation scope omits the oracle.** It needs position, heading and target, which is privileged plumbing. Keep it outside `ScriptedBrain`'s observation path.

7. **Smaller points for the freeze:**
   - Name the interval method for rule 2 and whether the bound is one-sided.
   - State which S is gated: the tuned S or the k ≤ 32 S.
   - Cap any shaping below one arrival per episode.
   - Make the freeze a committed file whose hash the gate run records.
   - The wall-follower's thresholds must sit above the own-body baseline in the collision readings.

## Readiness

Issues 1 to 3 are text edits, and only 3 and 6 touch the code scope. Nothing here is irreversible before the freeze, so another design round is not needed. The freeze document is what deserves the next review.

Make the edits for issues 1 to 3 before the pilot runs. Per v2's own order, T0's GPU items and T1 still come first.

E1 v2: ready to implement