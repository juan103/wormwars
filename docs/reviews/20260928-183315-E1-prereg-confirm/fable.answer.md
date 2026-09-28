# E1 pre-registration v2: confirmation review

I ran nothing: no shell, so no test suite and no `git diff`. I read the files at HEAD, both v1 reviews, D095, the smoke records in `runs/e1-smoke/`, and git's refs and reflog. HEAD is `a6437be`; `origin/roadmap` is still at `857e0ce`, so nothing of E1 is public yet.

## 1. My six must-fix points

| # | Point | Status |
|---|---|---|
| 1 | LF freeze, normalised hash | Resolved (`scripts/e1.py:149-160`, tested). |
| 2 | Gate refuses code drift, an inconsistent freeze, non-CUDA | Resolved in code. `require_same_code_as_pilot` (`scripts/e1.py:427-431`) has no test. |
| 3 | Binding commit, pre-registration in the dirty check, pushed state | Resolved in code (`scripts/e1.py:52`, `122-132`). Only the CPU branch is tested (`tests/test_e1_script.py:139-141`); the dirty and unpushed branches are not. |
| 4 | §7, and world ids in the freeze and gate | Ids are recorded. §7 is still incomplete (section 3). |
| 5 | Cap and crash wording, gate start marker | Resolved. |
| 6 | Tests for the guards | Partly resolved. |

Also untested: the `CapReached` path in `cmd_gate`, `use_smoke`, and the own-body zero-sample refusal. So "its guards are tested" (`PREREGISTRATION.md:29`) and "each has a test" (`DECISIONS.md:2896`) overstate.

## 2. New defects

I found none that would invalidate a result. These are correct as written:
- **The cue rule** (`scripts/e1.py:472-475`) matches §4, and Astra's counter-example fails it as it should.
- **Leg endpoints** (`wormwars/world.py:515-517`, `546-556`): path efficiency is at most 1 by the triangle inequality, up to float32 rounding.
- **`secondary`** selects finished legs before any NaN can reach a median.
- **`use_smoke`** rebinds ids and paths before it deletes anything.
- **`validate_freeze`** and the gate's cap path behave as described.

Defects, all in robustness or wording:

| Where | Defect |
|---|---|
| `scripts/e1.py:360-363`, `499-501` | The start marker is written before the connectome loads and before any CUDA operation. A trivial failure then burns the stage, and for the gate that means a new registration. `require_formal` checks only `is_available()`. |
| `scripts/e1.py:367-374` | §5 says the cap is checked "before every rollout". Generation 0 and the twelve throughput rollouts have no check. It is immaterial to the budget, but the text is not true. |
| `.gitignore:70-74` | §5 says the compute record is committed. `runs/**/compute.json` and `experiments/*/compute.json` are ignored, and the runner writes nowhere else. |
| `scripts/e1.py:551-553` | The events file is written before `gate.json`. If that write fails, the outcome is lost and the gate worlds are spent. |
| `scripts/e1.py:535-539` | On a cap hit, the completed arms' counts are discarded. State that this is intended, or save them. |
| `scripts/e1.py:400-424` | The check does not confirm that the coverage rows are exactly the registered candidates, or that the freeze came from a clean tree. |

## 3. §7 and the offset

**§7 is accurate where I could check it, but it is not complete.** The compute records show two smoke runs before v1's commit, not one, both on a dirty tree at `de57ce4`:

| UTC | Attempt | Record |
|---|---|---|
| 16:07:23 | pilot | 52 + 1 000 worlds, matching §7's sizes |
| 16:07:29 | gate | failed, freeze not found, 0 worlds, as §7 says |
| 16:08:22 | pilot | 52 + 1 000 worlds |
| 16:08:27 | gate | **completed, 208 worlds under `final`** (13 arms × 16 worlds) |

§7 describes only the first pair. No record holds the second pair's world ids, so I cannot tell which it used. v1 was committed at 16:10:05, so the move off E1's ranges happened somewhere in that window. If the second run was still on E1's ranges, the first 16 gate worlds were evaluated, and "No gate world was ever evaluated" is false.

The rest is sound:
- the geometry holds (the 5% floor lies at 2.448 σ);
- the later smoke runs record ids 0-15;
- the debug run is disclosed as unrecorded.

**The offset is adequate and not data-driven.** Every touched index is below 32, worlds are keyed by splitmix64 of (run seed, world id), and no world at index 1 000 or above has been evaluated. It also covers gate indices 0-15 if the second run touched them.

## 4. Before the binding commit

**Must fix:**
1. §7: account for the 16:08 pilot and gate. State their ids and the basis for the statement. If the basis is recollection, say so, as the σ ordering does. Correct "twice" and the gate sentence if needed.
2. Add tests for `require_same_code_as_pilot` and for the dirty and unpushed branches of `require_formal`, or narrow the two "tested" claims. D095 needs a dated correction, not an edit.
3. Make §5 true: add the missing cap checks or reword, and name a path for the compute record that is not ignored.

**Recommended in the same revision:**
- Move a preflight (connectome, interface, one real CUDA operation) before both markers.
- Write `gate.json` before the events file.
- Commit the start markers with each stage's output.
- Run a smoke pilot and gate from a clean tree at the binding commit. The last smoke run was on a dirty tree at `f83bd19`, and the formal-only guards have never executed.

E1 pre-registration: revise (must-fix: complete §7 for the second smoke run and its gate; test the same-code and clean-and-pushed guards or narrow the claims; make §5's cap-check and compute-record statements true).