# Bringing `main` up to date with D366-D378 (round 1)

The owner asked to publish the M6-3 literature report "as Astra and Fable recommended" (your round-2 verdicts:
fix then publish; the fixed draft 2 is committed on `roadmap` as D378). `main` is 13 commits behind `roadmap`
(D367-D378). As in D342, D348 and D365, `main` would fast-forward to `roadmap`, one commit on `main` removes the
working-branch banner, and `roadmap` fast-forwards back and restores it. No history is rewritten.

Before the merge, the main-facing summaries were updated (uncommitted; the diff is `r1-diff.patch` in this folder):
- `ROADMAP.md`: a dated 30 October status entry (M4e, M5, M6-0, M6-3 and the owner's order for what follows) and a
  note under "The thread worth following";
- `README.md`: the banner and the memory row of "Experiments at a glance" (M1-M6).

The owner's order for what follows (2026-10-30): a quick check of whether the switches' states outlast the input
(food returned to baseline after the ramp), then a test of whether the champions' fading history effect matters for
foraging, then stop.

Read-only; proportionate, as in `docs/reviews/20261025-main-sync/`:
1. Does every number and reading in the new text match its results file (`docs/memory/M4E-RESULTS.md`,
   `M5-POWER-RESULTS.md`, `M6-0-RESULTS.md`, `M6-3-LITERATURE.md`, `SYNTHESIS.md`) and its fixed wording?
2. Anything overstated, missing or misleading for a reader of `main`?
3. Anything on `roadmap` since D366 that should not go to `main`?
4. Verdict: merge, fix first (list), or hold.
