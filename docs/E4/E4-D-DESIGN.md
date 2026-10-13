# E4-D: a task where transfer is necessary (design v2.3)

**Status:** v2.3, after both reviews of v1 (D249) and of v2 (both "revise", narrowly; the trial and §3 hold;
`docs/reviews/20261012-E4-D-design*/`, D250), v2.2's weights (D258), and v2.3 after both reviews of the code (D260).
Nothing has been played.
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

**What v2.1 changes** (both reviewers of v2): the inherited 5-tick start cue is off; the start-cell rule is
operational, and its skip count and the scent width are fixed on a scouting block by declared rules; an oracle
ceiling; shuffling becomes an exact invariance test and reversal a mapping check; nose-origin uses B's four signed
edges; the selection's denominator, the bootstrap and the manifests are frozen; first entries are latched per wey;
§3's argument is stated structurally.

## 1. The trial

- **The maze:** E4's family (6 × 6 island mazes, k_r = 0, E3d's construction), unchanged. Its two carved goal sites
  are the two **candidates**; there is no A goal in a trial. The candidates are an unordered pair, in a canonical
  order (the lower cell index first), and the **assignment** is one bit: which candidate is real.
- **The start:** one wey (a colony of 1), placed at a **start cell** chosen from the maze alone (§2), with a heading
  from its own stream. Nothing about the start depends on the assignment.
- **Mode B from the first substep:** the latch neuron starts at v_q = −1, set in the initial state as E3a's
  `probe.latch_state` does (not clamped, so the latch is free afterwards). The gate reads v_q before the first
  substep, so g_A = 0 and A's motor edges carry no current from the first substep. E-G's latch holds it: from −1 (or
  −0.2) with no input, q settles at −1.9 and stays negative over 600 ticks (a CPU check, 2026-10-12). A check on
  every trial: q is negative at every substep until the trial ends, read directly (the switch log assumed a start
  in mode A; in a trial it starts in B).
- **What each module senses:**
  - **B's noses** read the sum of both candidates' scents, the same field under either assignment;
  - **A's noses** read the real candidate's scent alone: the cue, an engineered input, declared as such (both
    reviewers accepted it, with the narrower conclusion in §5).
  - **The relays** (at_a, at_b) read nothing in a trial, so no contact can switch the latch, and **the start cue is
    off**: the shuttle's inherited cue forces at_b = 1 for the first 5 ticks (`shuttle_cue_ticks`,
    `maze_world.py:376`), which drives Q positive through E3_RB and would open A's gate while A reads the cue (both).
  - **The world's goal is pinned** at B in a trial, so `goal_left`/`goal_right`, deposition and the visit bookkeeping
    do not depend on the assignment. E-G does not read `goal_*`; a test enumerates E-G's input channels and asserts
    that the assignment reaches only E3_A_NL and E3_A_NR.
- **The end:** the first entry into either candidate's goal block (real or decoy), latched per wey (its candidate
  and tick; later events ignored), or H_t ticks (neither). Worlds keep stepping in a batch after their trial ends;
  their later events are masked, and the batch's composition is unchanged.
- **No peers, no trails:** a colony of 1, access "none" (which suppresses trail sensing), crowding and pheromones
  off, as E4's configuration has them. A test asserts each.
- **Both assignments** are played for every maze and start, from bitwise-identical initial states.

## 2. Placement and the cue's range

- **Units:** maze cells (c × c) and grid cells (the 4c + 1 grid the scent is computed on); one maze cell is 4 grid
  cells. The scent is a Gaussian of path distance in grid cells, σ = 3, truncated at 9 in E4's world.
- **The start domain:** free grid cells. d₀ and d₁ are the shortest-path distances (grid cells, 4-neighbour BFS on
  the free grid, the scent's own metric) to the two candidates' goal blocks.
- **The start cell:** a cell qualifies if |d₀ − d₁| ≤ 4 (one maze cell; the resulting bias toward the nearer
  candidate is declared, and irrelevant to §3's exactness), and if its paths **separate** within 4 steps: from the
  cell, the sets of neighbours that lower d₀ and that lower d₁ become disjoint after at most 4 common downhill steps
  (each step to the lowest-index neighbour lowering both). Among qualifying cells, the one maximising min(d₀, d₁);
  ties to the row-major lowest. The heading is drawn from the trial's own stream [maze seed, maze id, a new key].
- **The scent width:** E4-D's scent has no truncation and width σ_D, a declared difference from E4's world. σ_D is
  chosen on the scouting block from {3, 6, 9, 12}: the smallest at which the **oracle** (§4) makes a real-first share
  over all trials ≥ 0.75 and X0's entry rate (real or decoy before H_t) is ≥ 0.75.
- **The scouting block:** 32 mazes, disjoint from every other block. It fixes σ_D, measures the start rule's skip
  count, and reports the scaled, occluded nose readings at the start for each candidate, their sum and their
  left–right differences, under both assignments (Astra: a wide field does not guarantee a lateral reading). It is
  never used again. Mazes without a qualifying start are skipped in order; if more than 25% of the scouting block is
  skipped, the rule is revised as a new version before anything else is played.
- **Frozen before the calibration block:** σ_D, the start rule, every block's id manifest, the heading stream and
  the skip limit. Nothing seen on the calibration or evaluation blocks may change them.

## 3. The chance level, exactly

X0 (cross-links at 0) is invariant to the assignment, **structurally** (Fable). In the step (`brain.py`), A's only
contributions to non-A neurons are products with exact zeros: its gated motor entries while g_A = 0, and the
zero-weight slots. Grafted neurons have no gap entries (`graft.py`). A finite value times zero adds exactly zero to
any partial sum, whatever the reduction order. Every other input (B's sum channel, formed in canonical order; the
relays; the walls, start and heading) is the same under both assignments. So X0's trajectory is the same under both
assignments, it enters the same candidate first in both, and that candidate is real in exactly one. **X0's
real-first share of entries is exactly 0.5,** whatever the geometry (Astra), provided at least one entry occurs
(otherwise it is undefined, and reported as such). Its decoy-first count equals its real-first count; "neither" is
the rest.

**The test:** the bitwise identity of every non-A injected current, motor command, position and non-A neuron's
state through the trial, under both assignments, within one batch composition (D082). Sabotages, each shown to be
detected on a fixture where the cue is informative: the cue fed to B's noses; a direct leak from A to a motor;
assignment-dependent relay current injected before the entry.

## 4. The positive control and the feasibility check

- **The control:** E-G with cross-links copying A's steering signal into B, at one weight w, set directly in the
  genome (not through the mutation clamp; w = 3 is w_max). Two wirings, both declared now:
  - **comparator-origin:** A_CL → B_CL and A_CR → B_CR, at +w;
  - **nose-origin:** B's own four signed nose → comparator edges, from A's noses (`e4s/comparator.py:49`):
    A_NL → B_CL +w, A_NL → B_CR −w, A_NR → B_CR +w, A_NR → B_CL −w (both).

  The candidate weights: 0.5, 1, 2, 3. **Selection** on the calibration block by the real-first share over **all**
  trials (entries and "neither"); ties to the smaller w, then comparator-origin. Every candidate's calibration
  result is recorded.
- **The oracle ceiling** (Fable): E-G with B's noses reading the real candidate alone and no cross-links, on every
  block. It separates "the slots cannot carry the signal" from "B cannot do the trial on this field", and it fixes
  σ_D on the scouting block (§2).
- **The blocks:** scouting 32 mazes (§2), calibration 32, evaluation 64, each played under both assignments. Seeded,
  their id manifests frozen before calibration, disjoint from each other and from every E4 block. H_t = 600 ticks.
- **The controls on the evaluation block:**
  - **cue reversal** (A told the decoy): a mapping check, not independent evidence (Astra: with both assignments
    paired it reproduces the normal trajectories with the labels exchanged). Criterion: the control's decoy-first
    count under reversal equals its real-first count without it;
  - **the cue held fixed** (Fable; it replaces shuffling, whose criterion could not fail): the control with A's cue
    set to one candidate whatever the assignment is bitwise invariant to the assignment (a test);
  - **cue removal** (A's noses read zero): reported, with no criterion;
  - **cross-link removal:** bitwise identical to X0 (a test).

  Entry counts are reported for every condition.
- **Success,** all of:
  - the control's real-first share over all trials ≥ 0.75;
  - its maze-level bound above 0.5: per maze, the mean of its two trials' real-first indicators; then a one-sided
    95% percentile bootstrap over mazes (10 000 resamples, seed 20 261 013), its lower bound;
  - X0's invariance test and the mapping checks.

  The oracle's real-first share over all trials is reported beside.
- **A failure** is read with the oracle beside it: a failed control with a working oracle is "the slots, as
  configured, did not carry the signal"; a failed control with a failed oracle is "the task is infeasible", and v3
  changes the task. Either way E4's null rows stay unread. Any change after a failure is a new version with a fresh
  evaluation block; every attempt is logged. The final configuration and its outcome are committed before E4's
  formal run, since the outcome enters E4's joint table (E4 v3 §2).
- **Compute:** the check runs under `wormwars.accounting`, on the CPU.

**Amendment, v2.2 (2026-10-13, before anything was played; D258):** the candidate weights become 0.05, 0.1, 0.25, 0.5,
1, 2 and 3 (Fable, after E4's stage A, D256-D257): the smallest weight that carries the signal is the prior for whether
evolution can discover it, since random cross-link steps of about 0.02 already break B in E4's main task. The selection
rule and its ties are unchanged.

**Amendment, v2.3 (2026-10-13, before anything was played; D260, after both reviews of the code):**
- **Distances are to the goal blocks** (as §2 says), by a BFS from every free cell of a block; the code had used the
  blocks' centres (Astra).
- **"Outside both goal blocks"** (d₀, d₁ > 0) is declared as part of the start rule; the code had an undeclared
  min(d₀, d₁) > 2 (both).
- **Each genome plays alone in its batch** (2n worlds of one strain), so every comparison of §3 and §4 is within one
  composition (both: the reversal check had crossed compositions).
- **The latch is checked in every trial,** at every substep until the world's first entry, and enters the verdict.
- **The verdict reads the integrity checks first** (X0's invariance, the reversal mapping, the cue held fixed,
  cross-link removal, the latch): a failure voids the result; only then is a performance failure read with the oracle
  (both).
- **The invariance checks compare every tick's** position, heading and random projections of the non-A neurons'
  states, bitwise, not only the endpoints (both).
- **The oracle is played on the calibration block too** (§4: "on every block").
- **Rule 7 holds by construction:** E4-D's trial world is a subclass of the maze world, and no engine file changed
  (`wormwars/e4/trial.py` is new; `wormwars/brain.py`, `wormwars/world.py` and `wormwars/e3/maze_world.py` are
  untouched by E4-D), so §6's flag-off comparison is not run (Fable accepted; Astra asked that it be run or amended
  openly: this is the amendment).
- **Simultaneous entries** into both candidates cannot happen (disjoint blocks, one head); the code's tie-break is
  never used. The bootstrap's quantile is NumPy's default (linear).
- **The inherited ledgers** of the maze world (visits, the goal's switch before it is re-pinned, deposits) keep
  running in a trial; only the first-entry record is read (Astra).

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
  candidate), the relays silent, the start cue off, the goal pinned, the untruncated scent at σ_D, first-entry
  latching and masking, and the oracle's mapping (B: the real candidate).
- **Rule 7:** with the flag off, the full-rollout comparison against the previous engine at tolerance zero, CPU and
  GPU: E3d's tree-family reference and E4's gated island rollouts under shared and no trails (Astra), with the
  compositions declared.
- **Tests,** each seen failing first: the channel mapping under both assignments, and the enumeration of E-G's
  input channels; the relays silent and the start cue off (a sabotage: with the cue on, q turns positive within 5
  ticks); q negative at every substep; first-entry latching, an entry on the last tick, "neither" at H_t, and masking
  after the end; the start rule (distances, separation, ties) and the skips; the assignment changing neither walls,
  start nor heading; X0's bitwise invariance with the sabotages of §3; the control with the cue fixed; every peer and
  trail path off. The previous-engine commit and the comparison compositions for rule 7 are declared before the
  comparison.

## 7. Next

v2.1 takes every finding of both reviews of v2, which agreed that the trial and §3 hold. The feasibility code is
written test-first next and reviewed by both with the code, before the scouting block is played.
