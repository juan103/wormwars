# E5-1's code and E5-1a's driver, round 2

Your round-1 answers are in `docs/reviews/20261111-E5-1a-code/r1-astra.md` and `r1-fable.md` (both "fix then run").
I took every fix; `docs/E5/E5-1-DESIGN.md` §14.1 (new, at the end) lists them, with the corrections of what §14 and my
smoke summary got wrong. Still uncommitted in the working tree.

The main changes:
- `scripts/e5_1a.py` is rewritten around one comparison (`compare`, `counts_by_task`, `required_worlds`, `judged`,
  `stratified`). Every per-world comparison (CPU against CUDA, ghost against Task N on CUDA, batch shapes against one
  strain × 512) takes its SD from 512 SD-block worlds per hunter. It uses the largest required count, judges mixed
  worlds by the score-weighted stratified interval, has every genome play every world, holds at most 1 024 worlds per
  play, and records the precision reached.
- The bench adds a scoring (B-construction) batch. The projection gives low and high totals and recomputes every cut
  from what it removes (`projection`).
- `cap` is bound to the bench and refuses a cap that nothing fits. Every play checks E5-1a's cap; hand-stepped worlds
  check the ledger, the overflow and finiteness.
- `wormwars/e5/play.py`: a non-finite state raises (test seen failing first: `runs/e5-1/finite-first-fail.txt`).
  `tests/test_e5_arms.py`: the GA is pinned to E2's.
- The old-against-new smoke now runs the real worktree at 7d25460 (`runs/e5-1a-smoke/equivalence.json`: 1 045 arrays
  identical, 530 captures, 64 smoke worlds at 40 ticks). Every stage ran again at smoke size, CPU and CUDA, including
  the cap refusal.
- The sabotage log now has 28 cases, all caught (`runs/e5-1/sabotage_log.txt`). The whole CPU suite is still running.

Read-only; keep it short. Are your round-1 fixes done correctly? Anything new that would make an E5-1a stage wrong?
Verdict: run (equivalence, graphs, cuda, bench, then stop for the owner's cap), or fix first (list).
