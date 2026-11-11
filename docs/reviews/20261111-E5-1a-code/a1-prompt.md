# E5-1a, Amendment 1 (the state-level check), for review

E5-1a ran on `aa36440` after your two code reviews. Steps 1 and 2 passed. Step 3 (CUDA) stopped by its own rule on one
check, the open-loop state level; everything else passed. `docs/E5/E5-1-DESIGN.md` §14.3 (new, at the end) gives the
numbers, the diagnosis and a proposed amendment:
- the attempt-1 records are in `experiments/E5-hunter/E5-1/E5-1a/attempt-1/` (`cuda.json` has every check);
- the diagnosis script and its outputs are in `experiments/E5-hunter/E5-1/E5-1a/diagnosis/`;
- the amended code is `scripts/e5_1a.py`'s `state_level` (uncommitted; `git diff`);
- a sabotage is in `runs/e5-1/amend1-sabotage.txt`.

In short: CPU float32 and CUDA float32 are each 0.15 to 0.46 from a float64 reference for the evolved C champions
over 300 ticks, and 0.0025 to 0.011 from each other. The proposal is to judge CUDA against float64 relative to CPU
float32's own error (factor 1.5, plus 1e-4), with the criterion openly chosen after the failure, and to rerun steps 1
to 3 on the amended code.

Read-only; short. Is the diagnosis right, and is the amendment acceptable (factor, floor, what reruns)? Should anything
else change before the rerun? Verdict: amend and rerun, or other (say what).
