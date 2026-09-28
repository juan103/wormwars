Checked `roadmap` HEAD `a84d30f`. The pinned-environment/source-hash fix is resolved. The clock boundary and output-overhead exclusion are now explicit. Remaining must-fixes:

1. **Interruption handling remains incomplete.** [scripts/e1.py:653](D:/Claude/random/wormWars/scripts/e1.py:653) catches exceptions only during the arm loop. Injecting `RuntimeError` into `gate_rules` or `secondary` completed all 16 arms but produced **no `gate.json` or fixed stopped wording**. The checkpoint survived. Extend handling through analysis to implement [PREREGISTRATION.md:189](D:/Claude/random/wormWars/experiments/E1-navigation/PREREGISTRATION.md:189).

2. **Checkpoint replacement can destroy previously retained observations.** [scripts/e1.py:576](D:/Claude/random/wormWars/scripts/e1.py:576) overwrites the sole checkpoint directly. NumPy opens it with `w+b`; termination during that write leaves a truncated archive, losing earlier completed arms. This contradicts the killed-process guarantee at [PREREGISTRATION.md:239](D:/Claude/random/wormWars/experiments/E1-navigation/PREREGISTRATION.md:239). Use atomic replacement or separate arm files, and define retention during an interrupted checkpoint.

3. **The new budget wording contradicts enforcement.** [PREREGISTRATION.md:218](D:/Claude/random/wormWars/experiments/E1-navigation/PREREGISTRATION.md:218) says an in-flight rollout’s overrun cannot change the decision. It does: injecting an overrun during the last arm yields “not completed” at [scripts/e1.py:667](D:/Claude/random/wormWars/scripts/e1.py:667). Restrict the decision exclusion to final output writing; retain the post-rollout cap enforcement.

4. **The requested output-only code-comparison test is still missing.** [tests/test_e1_script.py:210](D:/Claude/random/wormWars/tests/test_e1_script.py:210) returns an unconditional empty diff. It does not exercise an output-only change. I added `freeze.json` to `GUARDED` in memory—the test still passed, although that would reject the required freeze-only commit. Add an argument-sensitive Git fixture or a temporary-repository test.

Validation: 30 non-writing tests passed; all eight command tests passed with filesystem operations redirected to memory. Failure reproductions also used memory only. No files changed or registered worlds were evaluated.

E1 pre-registration: revise