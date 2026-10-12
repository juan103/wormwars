# E4-D: a task where transfer is necessary (design v2)

**Status:** v2, after both reviews of v1 (Fable: "go to v2 with these changes"; Astra: "revise";
`docs/reviews/20261012-E4-D-design/`, D249). No code, no compute yet.
- **Its purpose** (E4 design v3 §7): to read a null in E4's main task. E4-D is a task where information must cross
  from A to B, with a hand-configured positive control that shows whether the architecture can carry it.
- **Its order:** the positive control's feasibility check (CPU, exploratory engineering) runs before E4's formal
  run. A formal E4-D run, if any, has its own pre-registration; its ceiling is the owner's to set (asked
  2026-10-12: "decide later").

**What changed from v1** (both reviewers): v1 used repeated shuttle legs with a persistent decoy. Repeated legs leak
the assignment (contact with the real B through the relays and the latch, history, and the one-tick lag between the
world's goal and the latch's sign, D247), so "chance" had no bound, and the cue was out of scent range at the choice.
v2 replaces them with **fresh single-choice trials**, each in mode B from its first substep, scored at the first
candidate entered, and played under both assignments from identical starts.

## 1. The trial

- **The maze:** E4's family (6 × 6 island mazes, k_r = 0, E3d's construction), unchanged. Its two carved goal sites
  are the two **candidates**; there is no A goal in a trial. The candidates are an unordered pair, in a canonical
  order (the lower cell index first), and the **assignment** is one bit: which candidate is real.
- **The start:** one wey (a colony of 1), placed at a **start cell** chosen from the maze alone (§2), with a heading
  from its own stream. Nothing about the start depends on the assignment.
- **Mode B from the first substep:** the latch neuron starts at v_q = −1 (E3a's probe sets the latch state the same
  way), so g_A = 0 and A's motor edges carry no current from the first substep. E-G's latch holds it: from −1 (or
  −0.2) with no input, q settles at −1.9 and stays negative over 600 ticks (a CPU check, 2026-10-12). A check on
  every trial: q stays negative until the trial ends (the switch log, D247).
- **What each module senses:**
  - **B's noses** read the sum of both candidates' scents, the same field under either assignment;
  - **A's noses** read the real candidate's scent alone: the cue, an engineered input, declared as such (both
    reviewers accepted it, with the narrower conclusion in §5).
  - **The relays** (at_a, at_b) read nothing in a trial, so no contact can switch the latch.
- **The end:** the first entry into either candidate's goal block (real or decoy), or H_t ticks (neither).
- **No peers, no trails:** a colony of 1, access "none" (which suppresses trail sensing), crowding and pheromones
  off, as E4's configuration has them. A test asserts each.
- **Both assignments** are played for every maze and start, from bitwise-identical initial states.

## 2. Placement and the cue's range

- **Units:** maze cells (c × c) and grid cells (the 4c + 1 grid the scent is computed on); one maze cell is 4 grid
  cells. The scent is a Gaussian of path distance in grid cells, σ = 3, truncated at 9 (E4's world).
- **The scent is widened for E4-D,** a declared difference from E4's world (Fable): σ_D and reach_D are set so that
  at the start cell both candidates' scents and their lateral gradients are non-zero. Proposed: reach_D = the
  maze's largest path distance in grid cells, σ_D = 12. B's sum field then has a gradient toward both candidates,
  and A's cue a gradient toward the real one.
- **The start cell:** a free cell whose path distances (grid cells) to the two candidates differ by at most 2, and
  from which the two shortest paths separate within 4 grid cells, so the choice is made near the start (a decision
  junction, Astra). Among qualifying cells, the one farthest from both candidates; ties to the lowest index. Mazes
  with no qualifying cell are skipped in order (their count reported), never redrawn by the assignment.
- **Before anything is played,** the cue's lateral gradient at the start is computed for the evaluation block and
  reported (Fable).

## 3. The chance level, exactly

X0 (cross-links at 0) is invariant to the assignment: A's only edges leaving the module are its 16 comparator →
motor edges, exactly the gated set, and the gate is closed throughout the trial. B's input is the same under both
assignments. So X0's trajectory is bitwise the same under both assignments, it enters the same candidate first in
both, and that candidate is real in exactly one. **X0's real-first share over the trials that end in an entry is
exactly 0.5,** by construction, whatever the geometry (Astra). Its decoy-first share equals it; "neither" is the
rest. A test checks the bitwise identity of motor commands, positions and every non-A neuron's state through the
trial, within one batch composition (D082), with a sabotage (the cue fed to B's noses breaks it).

## 4. The positive control and the feasibility check

- **The control:** E-G with cross-links copying A's steering signal into B, at one weight w. Two wirings, both
  declared now: **comparator-origin** (A_CL → B_CL, A_CR → B_CR) and **nose-origin** (A_NL → B_CL, A_NR → B_CR, as
  B's own nose → comparator edges; Fable: B's saturating comparator may swamp a copied comparator signal). The
  candidate weights: 0.5, 1, 2, 3. The configuration (wiring and w) with the highest real-first share on the
  calibration block is chosen; ties to the smaller w, then comparator-origin.
- **The blocks:** calibration, 32 mazes; evaluation, 64 mazes; each played under both assignments (64 and 128
  trials). Seeded, disjoint from each other and from every E4 block. H_t = 600 ticks.
- **The controls on the evaluation block,** each with its pass criterion:
  - **cue reversal** (A told the decoy): the control's decoy-first share ≥ 0.75 of its entries;
  - **cue shuffling** (A's cue from an independent fair draw, within the same geometry): real-first share of
    entries within 0.5 ± 0.15;
  - **cue removal** (A's noses read zero): reported; no criterion (uninformative cross-link drive can still alter
    locomotion, Astra);
  - **cross-link removal:** bitwise identical to X0 (a test, not a behavioural check).
- **Success,** all of:
  - the control's real-first share over **all** trials (entries and "neither") ≥ 0.75;
  - its maze-level lower bound above 0.5: the per-maze mean over the two assignments, a one-sided 95% bootstrap
    bound by mazes (10 000 resamples, a fixed seed);
  - real-first share of entries exceeding X0's 0.5 by at least 0.25;
  - the reversal and shuffling criteria; X0's invariance test.
- **A failure** is reported. Any change after it is a new version (v3) with a fresh evaluation block; every attempt
  is logged. The final configuration and its outcome are committed before E4's formal run, since the outcome enters
  E4's joint table (E4 v3 §2).
- **Compute:** the check runs under `wormwars.accounting`, on the CPU.

## 5. What it shows, and what it does not

- **A pass shows:** the architecture, with the real interface, can carry an engineered A → B steering signal
  through the cross-link slots, so that B uses it.
- **It does not show:** that evolution finds the transfer (a formal E4-D run would ask); that E4's A has anything
  worth sending under its ordinary inputs (in a trial A becomes a navigator with an input E4's A never has); or that
  E4's interventions are sensitive enough (Fable, Astra).
- **In E4's reading:** a failed control voids only E4's null rows; a pass lets a null be read as "no practically
  relevant benefit detected by the registered interventions", never as "transfer is impossible".

## 6. The engine work and its tests (rule 7, rule 9)

- **A trial mode** for the maze world, a flag that is off for every earlier experiment: one wey, the candidates and
  the assignment, the start cell and heading, the latch's start state, the channel mapping (B: the sum; A: the real
  candidate), the relays silent, the widened scent, first-entry scoring and the end of the trial.
- **Rule 7:** with the flag off, the full-rollout comparison against the previous engine at tolerance zero, CPU and
  GPU: E3d's tree-family reference and E4's gated island rollouts under shared and no trails (Astra), with the
  compositions declared.
- **Tests,** each seen failing first: the channel mapping under both assignments; the relays silent; q negative
  through a trial; first-entry bookkeeping and "neither" at H_t; the start cell's rule and the skips; the assignment
  changing neither walls, start nor heading; X0's bitwise invariance, with the sabotages (the cue into B's noses; a
  direct leak from A to a motor; the relays reading the real candidate); every peer and trail path off.

## 7. Questions for the reviewers of v2

1. Does the single-choice trial close every path by which X0 could beat one half? Is §3's exactness argument right
   in this engine?
2. The widened scent (§2): acceptable as a declared difference, and are σ_D and the start-cell rule right?
3. The pass criteria (§4): tight enough, and is a 64-maze evaluation block with both assignments adequate for an
   engineering gate?
