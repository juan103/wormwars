You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a proposed roadmap change in WormWars, an open-science project that evolves brains
on the C. elegans connectome. The repository is your working directory; read `AGENTS.md` for its
rules and `ROADMAP.md` for the current roadmap.

**What to review:** `docs/E4s/ROADMAP-PROPOSAL.md` (commit on the `roadmap` branch).

**Background you may need:**
- E2d's results: `experiments/E2d-taskn-diagnosis/RESULTS.md` (the "non-stereo plateau").
- The literature review behind the proposal, archived verbatim: `docs/reviews/20261001-literature-review/`
  (`opus.review.md`, `astra.review.md`, `prompt.md`, `README.md`). Neither review has been verified by
  the project; the proposal relies on some of their claims.
- The earlier E4s designs and their reviews: `docs/E4s/DESIGN.md` (working copy is design v3,
  uncommitted), `docs/reviews/20260930-014518-E4s-design/`, `docs/reviews/20260930-020427-E4s-design-v2/`,
  and D139-D142 in `DECISIONS.md` (D142 is in the working copy).
- E1's scripted controllers and gain curve: `experiments/E1-*/RESULTS.md`; the gain probe:
  `experiments/E4s-stereo-module/development-records/gain-probe.json`.
- The owner chose option (a): keep bilateral left/right scent as an explicit game-design choice.

**Please answer:**
1. A verdict: "adopt", "adopt with changes" or "rethink".
2. Must-fix items (numbered, each with the section and the change).
3. Your answers to the proposal's six questions.
4. Any claim from the literature review that the proposal relies on and that you believe is wrong or
   needs checking before it is used (say what you checked).

Be concrete and brief. You are read-only: do not edit files.
