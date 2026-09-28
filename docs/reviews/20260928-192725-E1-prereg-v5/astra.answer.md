Checked `roadmap` HEAD `0e13e49`. All four v4 must-fix points are resolved:

- **Analysis interruption:** the handler now covers analysis and the final cap check; stopped records contain no rule verdict. [scripts/e1.py:655](D:/Claude/random/wormWars/scripts/e1.py:655)
- **Checkpoint retention:** temporary-file writing followed by atomic replacement preserves the previous checkpoint during an interrupted write. [scripts/e1.py:575](D:/Claude/random/wormWars/scripts/e1.py:575)
- **Budget wording:** rollout overruns affect completion; only final output writing is excluded. [PREREGISTRATION.md:224](D:/Claude/random/wormWars/experiments/E1-navigation/PREREGISTRATION.md:224)
- **Output-only comparison test:** the real Git fixture accepts committed outputs and rejects changed code. [tests/test_e1_commands.py:267](D:/Claude/random/wormWars/tests/test_e1_commands.py:267)

No new must-fix defect found that would invalidate a result or make a registered statement false.

Validation: 30 non-writing tests and 13 command cases passed, with command filesystem operations redirected to memory. Three additional injections—`gate_rules` failure, `secondary` failure, and last-arm overrun—retained all 16 arms and produced the correct incomplete outcome. The temporary-repository test was inspected, not executed; I did not rerun the full suite. No files changed.

E1 pre-registration: ready to bind