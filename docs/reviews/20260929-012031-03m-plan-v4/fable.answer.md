**Verdict: revise, narrowly.** Must-fix 1 is fixed. Must-fix 2 is done except for one branch: the smoke cannot reach the lesions' follow-up, and the test the plan claims for that boundary does not exist.

I ran nothing and could not run `git diff`. I read `p4m.py`, `tests/test_p4m.py` and `PLAN.md` at HEAD (the tree is clean at `e818ff0`), the committed JSON and the smoke records.

## v3 must-fixes

| Must-fix | Status | Evidence |
|---|---|---|
| 1. SH-recip rank (mine) | **Fixed** | `PLAN.md:79-87` matches `tails.json`: numerator 124 of 128, response all but one, overlap exceptions 0, 2, 2, 3, 4, six of 640 after removal |
| 2. Smoke on this code (mine) | **Partly** | All five commands completed, and the commit followed 18 s after the last one. The follow-up never ran (below) |
| Retention at cap boundaries (Astra) | **Partly** | Weights, decay and the main lesion sweep are fixed and tested. The follow-up checkpoint exists (`p4m.py:753-760`) but is untested |
| Graph rebuild under the cap (Astra) | **Fixed** | `p4m.py:349-353`, tested with a mocked rebuild; the default category counts its time |

## Must-fix

**The lesions' follow-up has never been executed, in a test or a smoke.**
- Smoke truncates to `entries[:6]` (`p4m.py:694-695`), which is the empty deletion plus five pairs. With no single deletion, `top` is empty and the follow-up loop never runs.
- The smoke output confirms it: `runs/p4m-smoke/lesions.json:308` has `"follow_up_by_synapse_type": {}`, and there is no `lesions-follow-up-per-genome.npz`.
- `PLAN.md:217-218` says "Each boundary has a test that stops there". There are four tests: weights, decay, the main sweep and graphs. None covers the follow-up.
- This is the risk I named in v3. A crash there keeps the sweep's rows and arrays, but `lesions.json` is not written, and a 1.4 h rerun does not fit the cap.
- I found no defect reading that path; it is simply unexercised.

**Fix:**
1. Let the smoke entries include singles, for example `entries[:3]` plus the first three singles. The existing stop test still holds.
2. Add a test that stops inside the follow-up and checks the partial JSON and the follow-up arrays.
3. Rerun the lesions smoke at the clean commit and confirm the follow-up is non-empty.

## Suggestions

- **`tails.json` was not regenerated.** It still records `"runs/exp03/measures (local)"` and a dirty `0916f41` stamp, so "Q1b's actual input directory recorded" is true of the code only. Regenerate both Q1 files at the final commit.
- **The graphs smoke rebuilt nothing** (0.005 s), because the ten graphs already existed. The real rebuild last ran in an earlier smoke, at roughly 15 s per graph, which agrees with the plan's 0.3 h.
- **The decay stop test calls the real `ensure_graphs`.** On a fresh clone it rebuilds ten graphs into `runs/exp03/graphs`, outside `tmp_path`, and is not marked slow. Mock it as the graphs test does.
- **03m still has no `DECISIONS.md` entry or README.** Both are needed before anything reaches main.

Graphs, synapses, weights and decay are ready as they stand; only lesions waits on the fix. I do not need another round if it is made as described.

**03m plan: revise**