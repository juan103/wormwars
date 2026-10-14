You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Review request: the evolutionary E4-D's pre-registration, draft 1 (WormWars), before binding

You are reviewing, read-only, in the WormWars repository (your working directory). You reviewed the design
(`docs/E4/E4-D-EVO-DESIGN.md` v2.1; D265-D266) and the pilot code (D268). The pilot ran (D269-D270): every one of 20
runs recruited the transfer (champions 0.68-0.96 real-first against E-G's 0.49), the slot factor is 0.25 by the
declared rule, and F was kept by the owner's rule.

**Review:**
- `experiments/E4-two-minds/E4-D-evo/PREREGISTRATION.md` (draft 1);
- the registered rule, `wormwars/e4/evo_stats.py`, and its tests, `tests/test_e4d_evo_stats.py`;
- the power analysis, `scripts/e4d_evo_power.py` → `experiments/E4-two-minds/E4-D-evo/power.json` (it calibrates on
  the pilot's local per-maze files, and records the calibration it used);
- for reference: the pilot's records (`precheck.json`, `screen.json`, `f.json`), `scripts/e4d_evo.py`,
  `wormwars/e4/evo_trial.py`, `wormwars/e4/trial.py`, DECISIONS D265-D270.

**What I want:**
1. Is the confirmatory question, estimand and five-state rule registered exactly and unambiguously, as design v2.1 §6
   and the owner's δ = 0.15 require? Does `evo_stats` implement it (the bounds, the states' order and edges, the
   sign-flip p)? Tests that would pass with a broken rule?
2. The power analysis: does it simulate the whole registered rule (final-population selection, finite blocks,
   heterogeneous success) credibly? Are the scenarios (homogeneous, mixture, spread; maze overdispersion σ 0 and 1)
   and the calibration from the pilot reasonable? Is the target (80% at a mean gain of 0.25, keeping your 0.10 spacing
   above the owner's δ = 0.15; 0.20 reported beside) and the resulting R right? Anything that would make it
   optimistic?
3. The design choices fixed post-pilot (§11): W = 8, G = 100, R, F with 4 runs as secondary, S's condition and its
   R, the `check` stage (the control plus a bitwise replay of the pilot's first 10 generations).
4. Anything missing for the formal stage code to be written test-first from this text alone: blocks and their
   independence, the pre-flight, seeds, the cue controls, eligibility and the rerun rule, the cap, the order of
   stages, what refuses.
5. Wording: do the outcome labels and §7.2's joint L/S readings claim more than the design supports?

**The answer I want:** a verdict ("bind as is", "bind after these fixes", or "revise"), then numbered findings with
severity, section or file:line, and the fix. Terse.
