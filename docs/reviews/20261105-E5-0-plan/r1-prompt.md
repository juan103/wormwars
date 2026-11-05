# E5-0's plan, draft 1 (round 1)

The owner said "go ahead" with E5-0 (2026-11-05), the CPU feasibility check of stage 05's Task H that
`docs/E5/SCOPE.md` (draft 2, D385; your reviews in `docs/reviews/20261104-E5-scope/`) describes. Please review
`docs/E5/E5-0-PLAN.md` (draft 1). No code exists yet; it is being written alongside this review, so the plan's
mechanics can still change.

Read-only; please keep it proportionate.
1. **Faithful to the scope and your round-1 fixes?** Anything from your scope review left out or got wrong?
2. **Task H's mechanics (§2):** is centring the scent and reach rule on the prey's position (its head point) rather
   than its mid point acceptable, for the ghost's bit-exact equivalence? Pellet removal, respawn at D - R from the
   hunter, the pin, the ledger, `done()`: sound? Check against `wormwars/world.py`.
3. **Calibration (§3):** E_prey from the flank median, the route follower and its check, H2b's movers, the tuning
   settings. Sound and fixed enough?
4. **Equivalence (§4):** right checks and tolerances? Is reusing E1's gate worlds for an engine check acceptable?
5. **Decision rules (§6):** are the numbers right (0.80 reliability, 0.5 margin, 0.5 too-easy ratio, 0.25 flag), and
   is anything ambiguous enough to be argued after the data?
6. **Cost (§8):** is the drop order sensible?
7. Your verdict: agree, fix then proceed (list the fixes), or revise.
