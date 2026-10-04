You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Design review: E3c, the assembly comparison (v1 draft)

You are reviewing a design in the WormWars repository (your working directory). You may read any file.

## Context

The owner chose E3c next, then E4, with 30 GPU-hours each (`DECISIONS.md` D198). E3c is ROADMAP §E3's
"assembly comparison". The relevant record:
- **E3a** (`experiments/E3-ab-organism/E3a/RESULTS.md`): the open-arena shuttle. It includes S2, the
  selector evolved from a near-ungated start, and B-task, a dense controller from scratch.
- **E3b-1** (`E3b-1/RESULTS.md`): the maze gate, "better".
- **E3b-2** (`E3b-2/RESULTS.md`): the tuned organisms still use the selector.
- **D159:** the owner's ceilings.

**The draft:** `docs/E3/E3c-DESIGN.md` (v1).
- **The arms:** five, with matched training effort. P-joint reuses E3b-1's T-A champions.
- **Two questions:** Q1, structure (S-mod against S-dense), and Q2, reuse (P-joint against S-mod).
- **A cost accounting.**
- **A feasibility pilot first.**
- **§9** lists the decisions it wants attacked.

## The question

**Is this the right E3c design for the roadmap's assembly comparison, within 30 GPU-hours? What should change
before a pre-registration is written?**

Please address §9's nine points, and anything else you find, especially:
- whether the comparisons answer what the roadmap asks ("first-use cost including pretraining, cumulative
  reuse cost; one loss on first use does not settle the value of modularity");
- **confounds in the matching:**
  - capacity, inputs and task conditioning;
  - the frozen W2 and the relays;
  - reusing E3b-1's champions (different code commit, validation block, selection);
- whether S-mod and S-dense from random weights are likely to be informative in mazes at this budget, and
  whether the pilot and its criterion handle that;
- the cost accounting for hand-built modules;
- what the registered tests should be.

Please end with a verdict: "go to pre-registration" (with changes), or "revise" (with what instead).
