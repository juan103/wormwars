# E4-D: a task where transfer is necessary (design v1)

**Status:** v1, for review by both. No code, no compute.
- **Its purpose** (E4 design v3 §7): to read a null in E4's main task. If information crossing from A to B is never
  useful there, a null in P1 or P2 says little; E4-D is a task where it must cross, with a hand-configured positive
  control that shows the architecture can carry it.
- **Its order:** E4-D's positive-control feasibility check (CPU, exploratory engineering) runs before E4's formal
  run. Its own formal run, if any, has its own pre-registration.
- **Its ceiling needs the owner's word** (Fable): D198's 30 GPU-hours are E4's. The feasibility check is CPU only.

## 1. The task: a decoy B that only A can tell apart

Astra's randomised B-mode choice (E4 v3 §7), built on the maze shuttle's own scent channels.

- **The maze:** E4's family (6 × 6 island mazes, k_r = 0), with three dead ends marked: A, the real B, and a decoy
  B′. Per episode, which of the two B candidates is real is drawn at random (the cue), independently of the walls.
- **The shuttle:** as now, a visit at A switches the wey's goal to B, and a visit at the real B switches it back.
  Entering the decoy's dead end does nothing: no visit, no switch. So a wrong choice costs time, and timely
  completion is what is scored (visits per wey in H).
- **What each module senses:**
  - **in mode A** (goal A): both modules as now. A's noses read A's scent; B's noses read the B channel, which in
    E4-D is the sum of both candidates' scents.
  - **in mode B** (goal B): **B's noses read the sum of both candidates' scents,** so B cannot tell them apart by
    its own senses. **A's noses read the real B's scent alone**: the cue. A's motor output is off in mode B (the
    output gate), so the cue reaches the motors only through the cross-links.
- **Environmental paths are excluded:** no trails (access "none"), so peers' trails cannot mark the real B. The
  decoy and the real B are placed so that neither is systematically nearer (§2).

## 2. Placement

- A, B and B′ are three dead ends with A's path distance to B and to B′ within one cell of each other, and B and
  B′ at least 3 cells apart (so that the first branch point between them is a real choice). Mazes without such a
  triple are redrawn, by a stream keyed by the id, as E3b-1's infeasible-maze redraw.
- The draw of the real one is from its own stream [run seed, maze id, episode, a new key].
- **Open:** whether to require the B/B′ branch point to lie on the route from A, so that every B-leg meets the
  choice; and the minimum separation.

## 3. Controls and checks (the feasibility check, CPU)

- **X0 is invariant to the cue, exactly:** with the cross-links at 0 and A's motor edges gated off in mode B, A's
  activity cannot reach the motors in mode B. A test: swapping which candidate is real in A's channel only (cue
  reversal) leaves X0's trajectories bitwise unchanged, while swapping the walls' real B changes them.
- **The hand-configured X+ positive control:** E-G with cross-links copying A's comparator signals into B's
  comparators with the steering sign (for example A_CL → B_CL and A_CR → B_CR at a fixed weight, chosen on a
  calibration block). It must reach the real B first on clearly more B-legs than X0, and make more visits.
- **Its controls:** cue reversal (A told the decoy: the control should go to the decoy), cue shuffling (A's
  channel from an unrelated episode: no gain over X0), and cross-link removal (back to X0).
- **The readout:** per B-leg, which candidate is entered first (real, decoy, neither by H); and visits per wey.
  Chance for X0 is about one half on first entries, if the placement is symmetric (§2).
- **Success of the feasibility check,** declared before it is run: the control's real-first share exceeds X0's by
  at least 0.2 on a 64-maze block, its visits exceed X0's, cue reversal sends it to the decoy more often than to
  the real B, and X0's invariance test passes. A hand-configured success shows architectural feasibility, not
  evolutionary discoverability (E4 v3 §7).

## 4. The engine work

- **A world variant:** the maze world with a third marked dead end, the per-episode draw, the switch in A's nose
  channel during mode B, and the decoy's no-visit rule. It is a flag that is off for every earlier experiment.
- **Rule 7:** with the flag off, E3d's full-rollout comparison is identical, CPU and GPU.
- **The tests,** each seen failing first: the channel switch by mode, the decoy's no-visit rule, the placement
  constraint and its redraw, X0's invariance (bitwise), and a sabotage (the cue fed to B's noses breaks X0's
  invariance).

## 5. What E4-D does not decide

- Whether evolution finds the transfer: that is a formal E4-D run, with its own pre-registration and ceiling.
- Whether E4's main task uses transfer: that is E4's P1 and P2.
- **How E4 reads it** (E4 v3 §2): a failed positive control voids only E4's null rows. A working control lets a
  null in E4 be read as "no practically relevant benefit detected by the registered interventions", never as
  "transfer is impossible".

## 6. Questions for the reviewers

1. Is the decoy-B task a fair "transfer necessary" task? Can B solve it by its own senses or history, or through
   the latch, with the cross-links at 0?
2. Is the mode-dependent switch of A's channel acceptable as an engineered cue, declared as such, or should the
   cue be a separate input that A alone receives?
3. The placement constraints (§2): enough to make the choice real and the chance level one half?
4. The feasibility criteria (§3): right thresholds and block size?
5. Anything that makes X0's exact invariance fail in this engine? **Checked on E-G's module:** A's only edges to
   neurons outside the module are its 16 comparator → motor edges (to RMD and SMD), exactly the gated set, and the
   module has no gap junctions and no edges to Q, the relays or the carrier's other neurons. So in mode B nothing
   of A reaches the body in X0; the test in §3 confirms it on rollouts.
