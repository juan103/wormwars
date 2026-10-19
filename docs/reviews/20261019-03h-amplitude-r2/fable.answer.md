**Verdict: revise.** Two fixes, both small, no further review round needed. The first blocks the run outright; the second makes the guide's one corroboration for "redesign" empty.

**My round-1 findings**

1. **Error rates and the ratio's range: correct and complete.** I re-derived them. The sample ratio times √3 is a non-central t with 2 degrees of freedom and non-centrality √3 times the true ratio. That gives about 19% for a true 0.8 reading 2 or above, 19 to 35% for the larger of two, and about 7% for a true 2 reading under 1. The chi-square range at `scripts/e03h_amplitude.py:165` reproduces b_power's bounds and D337's 0.17 to 1.3.
2. **Engine guard: the paths are right, but the guard now refuses the run.** See new finding 1.
3. **Pilot staleness before compute: fixed.** `P.read("pilot")` at line 307 runs before the clock, the record move and the recorded block. The pilot records directory is in the dirty check. Five upstream hashes are recorded.
4. **Float64 level decile: fixed**, by taking the pilot's own `decile_level` from the hash-checked arrays.
5. **Realised counts: kept**, per graph and condition.
6. **Graph names: present** in every readings block.
7. **CUDA smoke: present** and run.

Astra's items, from my side: the stop wording, the three selection-bank differences paired on S1's worlds, the undefined-ratio branch, the required ledgers and the end-of-run flags are all in place.

**New findings**

1. **The formal run will refuse at `scripts/e03h_amplitude.py:306`.** Severity: high for operability, though it fails safe before any GPU work and before the record moves. `P.CODE` contains the whole `scripts` directory. The amplitude script lives there and did not exist at the bound commit ff1fd31. Once committed, `git diff --name-only ff1fd31 HEAD -- scripts` lists it and the guard exits. Left uncommitted, `git status --porcelain -- scripts` shows it as untracked and the dirty check exits instead. The smoke runs and all nine tests skip this guard, so nothing has exercised it. Fix: pass the exclusion `:(exclude)scripts/e03h_amplitude.py` with `P.CODE`, or assert the diff equals exactly that one file. Also confirm with one git diff that nothing else under the code paths moved after ff1fd31. D337 added b_power.py under development-records, outside the guarded set, so I expect it is clean.

2. **The "grew faster than the SD" flag can never fire.** Severity: medium, because it is the corroboration the guide promises for the redesign branch. The condition at lines 193 to 196 is algebraically "the ratio rose from 0.25". The pilot's baseline ratio is 0.76 with a positive mean and SD, so any ratio of 2 or more satisfies it. The owner would read "no flag" as support when it is arithmetic. The test at `tests/test_e03h_amplitude.py:153` passes only because its fake has a stated ratio of 2.5 while its mean over SD is 0.67. The wording came from my round-1 review and was imprecise. A flag that can fire: the ratio is 2 or above but the mean shift's shared-world interval at that amplitude includes the 0.25 mean, or the between-graph SD shrank from 0.25. Rewrite the test with consistent fakes.

**Low, no fix required before running**

- A negative mean gives a range with lo above hi at line 171. Cosmetic.
- The docstring cites D338, which is not in DECISIONS.md yet. Write it in the same commit.
- The redesign branch string reads unconditional. That is fine once the flag above can fire.