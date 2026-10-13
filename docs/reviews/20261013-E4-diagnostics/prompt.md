You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Consultation: E4's diagnostics. The mutation load is the module biases' alone. What should E4's training be?

You are consulting on the WormWars repository (your working directory), read-only. You advised "diagnose before
choosing" (`docs/reviews/20261013-E4-pilot-1/`). The diagnostics ran: read `experiments/E4-two-minds/diagnostics.json`,
D253-D254 in `DECISIONS.md`, `scripts/e4_diagnose.py`, `wormwars/e4/arms.py` (`scales`, `class_scales`) and the E-G
module (`wormwars/e3/organism.py`, `engineered_gated`; `wormwars/e4s/comparator.py`).

**Results in one paragraph** (generation 1, children only, paired on 8 mazes, 4 seeds): breeding with all scales at
0 reproduces E-G exactly (no defect). E-G makes 4.03 on these mazes. Children at X0's factor 0.25: 1.97; 0.10: 3.11;
0.05: 3.60. By class at 0.25: weights only 4.14, τ only 4.16, gated edges only 4.13, one parameter per child 4.04;
**biases only 1.98**; module A alone 2.80, module B alone 2.80. E + W2 (ungated) on the same 6 × 6 mazes loses as
much (3.66 → 2.00); on 5 × 5 trees both organisms lose about a third (E-G 6.59 → 4.38, E + W2 6.52 → 4.34). The
saved final X0 populations (generation 99) on 64 validation mazes: E-G 7.63, no strain above it (best 6.16-7.08).

**My reading, as claims to attack:**
1. The comparators weigh tiny left-right scent differences, so a bias offset of order 0.01 on a module's noses or
   comparators shifts the balance point and ruins steering. The load is a property of the comparator module (shared
   by E and E-G), not of the gate or the arena.
2. A cross-link weight w on a slot whose source has mean activity m adds w·m to its target's drive: a bias-like
   offset. That explains why every cross-link factor above 0.25 costs (D250), and it means random cross-links mostly
   unbalance comparators. Evolution can then only recruit links in combinations whose tonic parts cancel.
3. **Proposed design changes, pilot-informed:** (a) the module biases mutate at a much smaller factor (for example
   0.01-0.02 of bias_sigma, or are frozen), with weights and τ kept at T-F's 0.25; (b) the load bound defined on
   children, relative to X0's own generation-1 children; (c) the cross-links either kept as 32 free slots (and the
   tonic-offset cost reported as part of the finding), or tied in mirror pairs (A_NL→B_CL with A_NR→B_CR, and so
   on) so that their tonic parts cancel by construction.

**What I want:**
1. Is reading 1 right, and does reading 2 follow? What check (CPU, or minutes of GPU) would confirm reading 2 directly?
2. Which of (a), (b), (c) do you endorse, with which values? Should the bias factor be chosen by a rule on a fresh
   block (like the cross-link factor), and what rule?
3. Is tying the cross-links in mirror pairs a design detail or a change of E4's question? Same for freezing the
   biases.
4. Given 3.0 + 0.7 GPU-hours spent (the pilot's attempt 1 and the diagnostics) and 30 in all: what is the next
   pilot, and what must the owner decide?

**The answer I want:** a recommendation first, then numbered points. Terse; do not restate the results.
