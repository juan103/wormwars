You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Code review request: E4's code, parts 1 and 2a (WormWars), before a GPU pilot

You are reviewing code in the WormWars repository (your working directory), read-only. WormWars runs CTRNN brains
on the C. elegans connectome in a maze-shuttle game. E4 asks whether two grafted navigation modules (A and B, one
active at a time, selected by a latch neuron Q) come to use information crossing between them, through 32
optional cross-link synapses, under evolution.

**Read first:** `docs/E4/E4-DESIGN.md` (design v3, agreed by both reviewers in an earlier round) and the decision
entries D245 and D246 at the end of `DECISIONS.md`.

**The code under review** (part 1 committed at c60eac7; part 2a in the working tree, not yet committed):
- `wormwars/brain.py`: `Brain.gate_outputs` (part 1) and a new `Brain.substep_hook` (called with each substep's
  end-state; unset, nothing is called).
- `wormwars/e3/organism.py` (`engineered_gated`, `cross_links`, `motor_edges`, `gate_spec`),
  `wormwars/e3/maze_organisms.py` (the optional `gate`), `wormwars/e4/organism.py`.
- `wormwars/e4/arms.py`: the X0 and X+ mutation masks, the frozen selector, E4's `assert_frozen`, `cut`,
  `mean_substitute`.
- `wormwars/e4/train.py`: the gated `rollout_fn` and evaluation brains.
- `wormwars/e4/means.py`: P1-info's source means.
- `wormwars/e4/lineage.py`: champion lineages recovered by replaying `breed`.
- `wormwars/e4/scale_rule.py`: the cross-link scale rule.
- `wormwars/e4/stats.py`: the exact sign-flip test, the t interval, P1 states, P2 labels, the joint table.
- `wormwars/e4/evaluate.py`: link subsets, condition genomes, batched play, the latch-switch count.
- `scripts/e4.py`: the pilot runner (exploratory; on E2's stage frame `scripts/e2.py`).
- Tests: `tests/test_e4_gate.py`, `test_e4_organism.py`, `test_e4_arms.py`, `test_e4_train.py`,
  `test_e4_means.py`, `test_e4_lineage.py`, `test_e4_scale_rule.py`, `test_e4_stats.py`, `test_e4_evaluate.py`.

**What I want from you:**
1. **Correctness bugs** that would make the pilot's numbers wrong or the formal run's readings wrong: file, line,
   the failure scenario. Check especially:
   - that the output gate is applied in every rollout of training and of evaluation (`gated_rollout`,
     `gated_brain`, `evaluate.play`, `means.source_means`), and nowhere is an ungated brain played for E-G;
   - `mean_substitute`: the formula b'_j = b_j + Σ_{i→j} w_ij · mean(tanh v_i), the source means' averaging
     (every substep end-state, wey and maze), and that nothing clamps the substituted bias. Note that the means
     are taken with substep end-states, while the chemical term inside a substep uses the state at its start;
     is that difference material?
   - the lineage replay: that the peeked parents are the ones `breed` uses (`wormwars/evo/evolve.py:67`);
   - the pairing across arms (same run seed → same training mazes and same mutation noise on shared parameters),
     given that the arms now train as two separate `evolve_batch` calls;
   - the sign conventions in `stats.py` (d = intact − intervention; "positive" means cutting hurts) and
     `p1_state` / `p2_label` against design v3 §2.
2. **Whether the tests can fail** for the right reasons (rule 9: tests fail before they pass; a check that
   cannot fail gets a sabotage). Name any test that would pass with a broken implementation.
3. **Two findings of mine, stated as claims to attack:**
   - **(a) Design v3's joint table is incomplete.** It omits, for example, P1-cut equivalent with P1-info
     positive, P1-cut positive with P1-info negative, P1 not evaluable, X0 beyond X+, the null row with E4-D's
     control failed, and the row order when P2 is not evaluable but P1 is positive. `stats.joint` keeps the
     design's rows D1-D8, puts P1's acute rows first, and adds rows P1-P8 labelled "proposed". Are the proposed
     rows and the precedence sound? What would you change?
   - **(b) The scale rule cannot meet its reach criterion at the registered mutation sigma.** With w_sigma 0.08
     and w_max 3, a neutral slot's reach P(|w| ≥ 1) is 0.21 at factor 1.0 after 100 lineage mutations and 0.47
     after 300 (D246 has the numbers; `scale_rule.py` reproduces them). So the fallback, "the smallest factor
     meeting the load bound", would choose 0.25, where a slot barely moves, and X+ would be close to X0 by
     construction. Is this right? What should the pre-registration do: the largest factor meeting the load
     bound, larger candidates (2, 4), or something else?
4. **The rulings in D246:** X+ refuses to build without its factor; P2's "no relevant difference" needs only the
   interval inside the smaller margin even when the exact test rejects; the arms train as two batches; the pilot
   trains X+ at 0.5. Accept or reject each, with a reason.
5. **The pilot's measurements** (`scripts/e4.py` docstring, design §6): is anything the power analysis or the
   pre-registration will need missing from what the pilot records? Is anything recorded that is wasted cost?

**The answer I want:** a verdict ("ready for the pilot", "fix first", or "revise"), then numbered findings, each
with a severity (critical / important / minor), file:line, and the fix. Be specific and terse. Do not restate the
design.
