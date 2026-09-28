**Revise, narrowly.** The v3 code fixes are present, but one explicitly requested retention test is missing.

| V3 must-fix | Assessment |
|---|---|
| Retain completed work | Implemented: weights save after each design; decay saves before gaps-off and retains its arrays; main lesions flush in `finally`; follow-ups checkpoint after each deletion. |
| Correct SH-recip rank | Fixed. “Above 124 of 128” matches `tails.json`; the added response rank and tail exceptions also match. |
| Cap graph rebuilding | Fixed. `cmd_graphs` checks the cumulative clock before each graph; completed files survive, and accounting export remains in the outer `finally`. |

**Remaining must-fix: test follow-up retention with nonempty follow-ups.** The additions in [test_p4m.py](/D:/Claude/random/wormWars-p4/tests/test_p4m.py:180) cover weights, decay, main lesions and graph rebuilding. None reaches the new [follow-up callback](/D:/Claude/random/wormWars-p4/scripts/p4m.py:753).

The successful smoke run does not cover it either: [smoke truncation](/D:/Claude/random/wormWars-p4/scripts/p4m.py:694) selects intact plus five bilateral pairs, leaving no eligible singles. Consequently, [lesions.json](/D:/Claude/random/wormWars-p4/runs/p4m-smoke/lesions.json:308) contains `"follow_up_by_synapse_type": {}`, and no follow-up NPZ exists. The plan’s [“Each boundary has a test” claim](/D:/Claude/random/wormWars-p4/experiments/03m-p4-mechanism/PLAN.md:217) is therefore incorrect.

Add a mocked case with eligible singles that stops after a completed follow-up and verifies its partial summary and both per-genome arrays survive. Ideally stop within the gap pass, also checking retention of the preceding chemical pass. This completes v3’s existing requirement.

I found no other new implementation defect in the diff by inspection. I did not execute tests or simulations.

**03m plan: revise**