You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Review of a screening-experiment design. The main aim: find the failure modes nobody has thought of yet.

## Context

The working directory is the WormWars repository. Read `experiments/02-screening/DESIGN.md`: a
12-GPU-hour fraction of a larger experiment, drafted after your earlier advice. Background is in
`experiments/01b-direction-corrected/RESULTS.md`, `DECISIONS.md` D031-D033,
`configs/interface.yaml`, `wormwars/calibration.py`, `wormwars/world.py` (sensors, hazards,
pheromone deposition), `wormwars/brain.py` and `wormwars/evo/`.

The project owner's instruction for this stage: spend 12 hours to discover what we are not seeing,
rather than find it after 150.

Two things were measured after your earlier advice, and they change it:
- **The integrator is nearly free.** 8, 16 and 32 substeps cost 3.9, 4.2 and 4.9 s per generation
  on the RTX 5080, because the world simulation dominates. The design uses 32.
- **Matching wrong mappings on degree and hop distance leaves a small pool.** In the true signal
  direction, the food neurons AWA/AWC/ASE are 2 hops from the motor read-out with almost no direct
  edges, while nearly every other bilateral sensory pair outside the interface is 1 hop, many with
  10-16 direct edges to the read-out command interneurons. The matched candidates are ASI, ASJ, ASG,
  IL2D, IL2V, IL2, AWB and PLN, mostly other amphid chemosensory neurons.

The design also argues that a reversed-valence hazard task is uninformative here: synapse signs are
not fixed (random-sign initialisation, sign-free mutation), so approach and avoidance are nearly
symmetric, except through gap junctions. A cheap valence probe tests this.

## What I want

1. **Failure modes not yet on the radar.** This matters most. Think about the simulator, the
   evolution loop, calibration, the tasks, the remapping, the statistics, and how a result could
   look meaningful while being an artefact. For each, say how the screening would detect it; if
   it would not, say what probe to add. Rank them by expected damage.
2. **Is the fraction well chosen?** Does it answer the three stated jobs within 12 hours? What
   would you swap in or out at the same cost?
3. **Are the tripwires and their thresholds right?** Is any missing, any threshold arbitrary in a
   way that matters, or any consequence wrong?
4. **Is anything in the design factually wrong** about the code or the connectome? Check against
   the files.

Numbered points, each marked MAJOR or MINOR. Be concrete; check the code where you can. End with
the one failure mode you most expect to bite.
