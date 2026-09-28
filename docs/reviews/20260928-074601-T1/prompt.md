You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a plan in the WormWars repository (your working directory). It is a research codebase: evolved spiking-free rate brains wired by the C. elegans connectome, simulated in batched PyTorch worlds on one GPU (RTX 5080, Windows, torch 2.12 + CUDA 13.0). The owner has delegated the roadmap; decisions go ahead when both reviewers (you and one other model) agree.

Read `docs/foundations/T1.md` (plan v1, committed on branch `roadmap`). Context you may check:
- `ROADMAP.md` (section "T1: throughput, profile first"),
- `docs/foundations/T0.md` (especially the 2026-09-28 amendment about single-strain chunks on CUDA) and `docs/foundations/T0_gpu.json`,
- `docs/REPRODUCIBILITY.md`, `DECISIONS.md` D081-D085,
- `wormwars/brain.py` (`Brain.step`), `wormwars/evo/rollout.py`, `wormwars/evo/evolve.py`, `wormwars/world.py`,
- `docs/E1/DESIGN.md` (the next experiment).

The §1-§2 numbers came from throwaway scripts; I can share them if needed. They are exploratory, and T1.1 is meant to regenerate them from a committed script.

Please answer:
1. Is the profile's reading correct, and is anything important unmeasured (for example the world's share, host-device syncs, or evaluation paths the plan misses)?
2. Are the §2 decisions sound: which levers are adopted, deferred or rejected, and why?
3. Is the §3 equivalence contract right? Class E at zero tolerance; class N declared but not adopted. Are the class N thresholds sensible, or should they not be declared now?
4. T1.2: is brain-level padding of single-strain batches, behind a default-on switch, the right D082 decision? Consider the alternatives: padding in `rollout`, a guard or warning only, or default-off. Consider its effect on reproducing published results, and whether the test design can fail.
5. T1.3: is "build multi-run batching only if 04a's or E2's budget needs it" right, given the roadmap's tripwire ("no new infrastructure beyond T0, T1 and minimal module save/load until the minimal A/B organism runs")?
6. Is T1.4's gate a real gate, or trivially satisfied? Should T1 close on these conditions?

Finish with one line: "T1 plan: approve", "T1 plan: approve with changes" (list them), or "T1 plan: revise" (list the must-fix items). Be concrete; cite files and lines.
