**Verdict: fix first.** The five numbered fixes from my previous review are correctly implemented. Two additional fixes remain incomplete:

1. **The scripts guard exempts executable changes beyond the binding values.** [scripts/e3d.py:140](D:/Claude/random/wormWars/scripts/e3d.py:140) removes every line containing either binding key before comparing files. I reproduced a valid Python mutation that moves the binding line below the other registry entries and appends `"H": 60`. `require_bound()` accepts it with the existing binding commit and design hash. Normalize only the two binding string values; compare everything else, including additional entries on those lines. Add this negative case.

2. **The projection still understates the required budget.** [scripts/e3d.py:499](D:/Claude/random/wormWars/scripts/e3d.py:499) counts completed attempts but omits the current project stage. I exercised the production body with 360 seconds elapsed: it reserved only 0.25 h, instead of 0.35 h. A projected 2.70 h plan is therefore admitted despite totaling 3.05 h with those overheads. Use `ctx.cap.spent_hours()` plus elapsed time from `ctx.cap.t_start`, then add the g-e allowance. Also include record compression/writing in the timing: projection calls `play` without `save_as`, whereas formal conditions save compressed artifacts. Otherwise admission can select a plan that exhausts the cap before completing its required blocks.

The other fixes check out:

| Fix | Finding |
|---|---|
| Fresh g-e comparison | Requires a fresh record, exit status 0, and `identical=True`; stale/failure cases pass. |
| Per-condition records | Verified **106 existing smoke artifacts**, including hashes. All saved arrays and summaries reconstruct exactly from saved cells; maze, strain, wey and visit identities survive. |
| Per-goal scent split | Correctly groups A/B arrival shares by each goal’s flag, separately and pooled. |
| Bootstrap | Both omitted quantities now use the paired resamples. |
| Numerical reporting | Tree maze 30200 now reports **9 candidates**; zero-mean predictions evaluate the inequalities directly. |
| Contact/config/qualification | The class counting, label tie, island-to-tree reset, circulation and ray-test changes are correct. |
| E3c test | Appropriate: it checks the recorded freeze against Git. E3c’s formal guard still refuses the two modified engine files. |
| Binding/correction | Hash matches; `4886ba9..c86f281` changes only the binding value. The dated wording correction is appropriate. |

Validation: **81 pytest tests passed**; the remaining stale-record test passed using an in-memory filesystem substitute. The full CPU equivalence comparison matched the committed `40bd50f` reference exactly across all four rollouts and both configuration hashes.

No files changed and no GPU work ran.