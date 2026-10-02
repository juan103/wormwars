## 1. Verdict

**Proceed to E3b-0's plan.** Nothing in v2 makes E3b-0 uninformative or infeasible in a way the plan cannot fix. I ran nothing; the engine claims come from reading `world.py`, `fields.py`, `config.py` and `wormwars/e3/`, and the maze arithmetic below is my own rough estimate.

## 2. v1 items

All are resolved except these three, which are partial and fixable in the plan:

- **Seed exploration is gated, not designed.** Exit criterion 2 catches a failure, but v2 never says what "maze-ready" adds besides the reflex.
  - The carrier turns at 0.2 × `max_turn` = 0.06 rad/tick, a circle of radius about 5.8 cells.
  - With per-axis sliding in 3-wide corridors, the heading keeps rotating, so the wey oscillates within roughly ±6 cells. That is not exploration.
  - I expect criterion 2 to fail on first contact. The plan must say what may be added (labelled, frozen, given to every arm and baseline) and how many iterations the 3 hours allow.
- **The wall-follower criterion merges two different requests.** I asked for the seed above the blind baselines; Astra asked for the wall follower's ceiling to be measured. Criterion 2 now requires the seed to beat the wall follower.
  - A wall follower solves any tree completely. At c = 5 its tour is about 2 × 24 edges × 4 cells ≈ 190 cells ≈ 550 ticks, so about 4 visits in 1 200 ticks.
  - Either size the maze so the tour exceeds the horizon (c = 8 gives about 1 440 ticks), or report the wall follower as a ceiling and not a bar.
- **Astra's inference-plan items** (seed artefact, mutation mask, untouched maze blocks) are only partly in the E3b-1 sketch. That deferral is acceptable.

## 3. The literature note

Mostly fair, and the verification levels are honest. I checked the Panait & Luke and Jackson quotes against memory only: they match the abstracts as I recall them. I could not check Czaczkes 2024/2013, Dodoková or Salman.

The overclaims:

- **"A trail alone carries no polarity in real ants"** (note item 2; design line 79). The quote is "previous research has found no evidence", from an abstract, about one species (Pharaoh's ants). That is absence of evidence. Soften to "no evidence found, per Jackson et al."
- **"Best at about 60 degrees"** — I recall the abstract giving a typical bifurcation angle of 50–60°, not an optimum. I am unsure; recheck the wording.
- **"Established practice"** rests on two abstracts, and the same table lists StarLogo as a one-pheromone counterexample. "Has precedent" is what the evidence supports.
- **"Their comparisons rest on single runs"** (item 4; repeated in D172 as fact). The quote "two distinct simulation runs" may only mean the two conditions were separate runs. The full text was read, so cite the replicate count, and do not extend the claim to AntFarm, which is unverified.
- **The fallback "gives a gradient by construction"** is not in the abstract. It rests on Astra's reading of the full paper. Astra gave a GMU PDF link in the v1 review; read that before the fallback is relied on.

## 4. New problems in v2

- **The fallback breaks the peer controls.** A top-up from neighbouring values is nonlinear in the field. Shared is then no longer the sum of per-wey fields, and "peers only = sum − own" is undefined. If the fallback is adopted, own-only and peers-only need redesign and a new review. The additive rule's linearity also needs no clamp anywhere on the fields.
- **The dynamic range is tight.** The field along a route is d₀·exp(−μ·age)·exp(−(λ−μ)·s). L1's window of 0.005–0.35 is 70×, about e^4.25. That window must hold route length, trail age, 1–8 summed contributors and the scent together. Over a 200-tick leg, (λ−μ) can be at most about 0.015 per tick, which is about 4% per cell along the route.
- **A lateral ridge is not polarity.** Stereo noses centre a wey on the trail, and a wey heading straight down-gradient gets no left-right difference. So "the gradient points to the source" (criterion 3) is necessary, not sufficient. Add a behavioural test: a follower or seed placed mid-trail facing the wrong way turns round.
- **Oracle sizing conflicts with exploration.** A maze where the oracle makes only 4–6 journeys is roughly c = 8, where a blind tour exceeds the horizon. Size by blind first-discovery time as well, for example at most a quarter of the horizon.
- **Trails on/off is not a peer contrast.** Own trails also give wall-centring (the declared bilinear effect) and self-route memory. The 2 × 2 reads "trail use"; peer claims come only from shared against own-only, peers-only and replay.
- **Replay with other A/B placements misleads.** Donor trails lead to wrong dead ends. Shared > replayed can be harm from replay, not benefit from peers. It must be read against own-only.
- **Criterion 6 powers the wrong contrast.** The scripted follower's peer effect says nothing about the gate (tuned against frozen seed). E3b-0 should also give the seed's between-maze variance and a minimum detectable effect for the gate, and run the seed under own-only (the controls list has only on and off).
- **"Below the scripted follower" should not be a pass/fail bar.** A seed at or above the follower is a finding. Define headroom against the oracle.
- **No failure branch.** v2 does not say what happens when an exit criterion fails.

## 5. What E3b-0's plan must pin

1. **Trail semantics:** which trail each goal state reads and deposits; the initial goal of every wey (all A through the cue ticks, or split); no clamp on the fields.
2. **A free sabotage test:** before a wey's first B visit, own-only and none must give identical trajectories, bitwise on CPU, because its own relevant trail is empty.
3. **The scripted follower:** bilateral instantaneous readings only, with no temporal comparison, and its exploration policy stated. Its "none" level and every peer gap depend on that policy.
4. **Maze sizing:** c, the A–B path range, the oracle's journeys, the wall-follower tour time and the blind first-discovery time, with the maze stream separate from the episode's.
5. **Constants:** the search grid for d₀, λ, μ and diffusion, with the range inequality above as a constraint, measured with 1 and 8 contributors and at old trail ages.
6. **Equivalence:** tolerances declared in advance. I would expect bitwise on CPU for Task N, foraging, E3a's shuttle and E4s-1's graft with every flag off.
7. **"Maze-ready":** the list of permitted additions, each labelled and frozen, with the carrier plus each addition reported as a baseline.
8. **Thresholds:** numbers for "above", "headroom" and the power criterion, fixed before the runs, with the colony as the unit.
9. **Donor replay:** run donors in lockstep. Stored fields are about 10 MB per world at 1 200 ticks. Count the cost under criterion 5.
10. **Failure branches and budget:** what each failed criterion triggers; the iteration limit inside 3 GPU-hours; timing at the real composition (4 096 worlds × 8 weys) with peak memory including diffusion's working buffers.
11. **Wording fixes:** the literature items in section 3, as dated corrections under rule 4.