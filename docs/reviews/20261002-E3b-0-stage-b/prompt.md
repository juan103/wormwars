You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing an exploratory stage of a research project (WormWars, this repository; branch `roadmap`). Read files to check claims; you cannot edit anything. Please answer in English, concisely, with a clear verdict.

## Context

E3b-0 is the exploratory feasibility stage before a confirmatory experiment (E3b-1) on colonies of simulated worms ("weys") shuttling between two sources A and B in tree mazes, laying linear per-wey trails. Its plan is agreed at v3: `docs/E3/E3b-0-PLAN.md` (you reviewed v1 and v2; reviews under `docs/reviews/20261002-E3b-0-plan*`). Decisions: `DECISIONS.md` D175-D177. The runner is `scripts/e3b0.py`; engine `wormwars/e3/maze_world.py`; controls `wormwars/e3/maze_controls.py`; drivers `wormwars/e3/maze_runs.py`.

## What happened

- **Stage A** (record `experiments/E3-ab-organism/E3b-0/stage-a.json`) chose c = 5, H = 2 400 (the four H = 1 200 candidates failed only on the follower's median legs).
- **Stage B** (record `stage-b.json`, per-setting arrays `stage-b-*.npz`) evaluated the 24 live trail settings. **None passed.** For every setting:
  - polarity (plan §3b: pass(real) − max(pass(none), pass(route-permuted))) was between −0.06 and +0.02, against ≥ 0.3; the follower reached A from the mid-route start, facing away from A, in only 2-9% of mazes even on the real trail;
  - the nose range (share of on-route goal-channel nose inputs in [0.005, 0.35]) was 0.26-0.46 against ≥ 0.9, with 2-43% above 0.35;
  - the gradient share passed everywhere (0.80-0.94 at age 1 leg, 1 and 8 contributors).
- The plan's branch (§6) for "Stage B, no setting passes" is: the fallback (Panait-Luke-style, nonlinear trails); the peer controls redesigned and reviewed before E3b-1. It also says "Stage B only: controller failures never change the trail rule" (Astra).

## A diagnosis, run afterwards on the CPU (exploratory)

`scripts/e3b0_diagnose.py` → `experiments/E3-ab-organism/E3b-0/development-records/stage-b-diagnosis.json`, on selection mazes 0-63 (the same ones Stage B used), at the pilot constants and at Stage B's highest-rate setting (μ 0.005, λ 0.02, δ 0.05, d₀ 0.571):
- the scripted follower's later-leg rate (legs per 1 000 ticks after each wey's first visit), colony of 8, 95% paired bootstrap over mazes: shared − none **+2.85 [1.83, 3.92]**, own − none +1.09 [0.39, 1.92], shared − own **+1.75 [0.93, 2.64]** at the best-rate setting; at the pilot, shared − none +0.83 [0.09, 1.72], own − none +0.08 [−0.55, 0.74];
- polarity by start heading (reach A within 2× the oracle's time), best-rate setting: facing away (registered) real 0.05 / none 0.02 / permuted 0.09; facing toward A 0.61 / 0.47 / 0.45; uniform heading 0.41 / 0.28 / 0.33;
- nose inputs on route: about 22% exactly 0, 14% because the nose is occluded (a wall between head and nose zeroes it, plan §1d); unoccluded, about 40% in range.

The follower (plan §3a) steers by 32 (L − R) on its goal channel's two noses, with no temporal comparison and no memory beyond its goal.

## A claim to attack (Claude's, not settled)

"Stage B failed on two qualification tests that this controller cannot pass by construction, not on the trails: a bilateral, memoryless follower facing away along a corridor gets no left-right difference from a longitudinal slope, so it cannot turn around; and the 90% range target is unreachable when occluded noses read 0 and colony trails stack. The trails are usable (shared − none +2.85 legs per 1 000 ticks, and a peer effect). So instead of the nonlinear fallback, amend the plan (v3, Amendment 1, labelled as decided after seeing Stage B's data):
1. polarity becomes reported, at all three headings, not a selection condition; the gradient share (≥ 0.8) stays as the physical polarity check;
2. the nose range becomes reported (with occluded and zero noses apart), not a selection condition; criterion 4's component tests at the levels actually met, including the low ones, carry the requirement;
3. Stage B's rule is reapplied to its recorded rows (λ > m, gradient), choosing the highest later-leg rate; the winner (μ 0.005) is on the grid's edge, so the one widening (μ 0.0025) runs, as a new stage reading Stage B's record;
4. everything downstream (the recheck, Stage C, the report on untouched report mazes 1000-1255) runs as planned, and the results say plainly that the rule was changed after seeing data."

## Questions

1. Is the diagnosis right? Check the code and data. In particular: is the polarity failure really structural (the follower), or could it reflect a bug or a bad test setup (e.g. the start, the 2× oracle limit of about 78 ticks, the trail's age)?
2. Should E3b-0 take the plan's fallback (nonlinear trails) or the amendment above, or something else? Consider "controller failures never change the trail rule".
3. If the amendment: what would you change in it? Is choosing by the follower's later-leg rate (shared) still the right rule, or should it be the trail effect (shared − none), or something else? Is there a selection-bias problem in choosing on the selection mazes that the diagnosis also used?
4. Anything else that must be fixed before the rerun.

Give a verdict: "amend and continue", "take the fallback", or "stop and redesign", with reasons.
