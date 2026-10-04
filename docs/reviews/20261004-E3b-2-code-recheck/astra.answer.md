**Fix before `project`.** At `bf8d54e`, switching, vectorised tally equivalence, middle-half counters, `--out` refusal, pinned hashes, lesion units and benchmark progress records check out. The joint trail bootstrap is correct. **32 selected read-only tests passed**, but independent examples expose two reporting blockers.

The claimed cap-stop reporting improvement also remains ineffective: [the report](D:/Claude/random/wormWars/scripts/e3b2.py:871) still enters [the wrapper’s exhausted-cap refusal](D:/Claude/random/wormWars/scripts/e2.py:596). That previously nonblocking limitation remains.

Remaining blocking fixes:

1. **Preserve both trail-split intervals.** [Line 641](D:/Claude/random/wormWars/scripts/e3b2.py:641) overwrites `t_interval()`’s `ci95` with the bootstrap interval. With run allocations `[1, 3]` constant across mazes, the output retains only `[2, 2]`, losing the run-level interval `[-10.706, 14.706]`. Store the bootstrap under a separate key, as `schedules_of()` does.

2. **Exclude undefined equal-weight bootstrap draws.** [Lines starting at 749](D:/Claude/random/wormWars/scripts/e3b2.py:749) replace zero goal denominators with 1, fabricating zero agreement. Perfect agreement on two mazes containing different goals produces point estimate `1` but interval `[0.5, 1]`. Use a joint mask requiring positive decided counts for both goals; explicitly handle no valid draws. Add regression tests for both defects before binding the commit.