**revise**

Against my round-1 findings:

1. **Stop wording: partly fixed.** The narrower rank-route interpretation is correct. Discordance still does not override the recommendation.
2. **Relief benefit versus sham damage: fixed.** Both level contrasts, shared-world intervals, and realised selection-bank counts are retained.
3. **Guards: partly fixed.** The completed 0.25 pilot and its immediate upstream hashes are checked before rollouts and record movement. Driver/input coverage is expanded, but creates the blocker below. Environment/connectome provenance is still recorded without comparison to the pilot.
4. **Undefined ratio: fixed.** Missing/nonfinite ratios now go to the owner.
5. **Accounting: fixed for completed runs.** Required ledgers and both completion overrun flags are present. Failed records still omit those flags.

Remaining findings:

- **High — the production guard rejects its own new script.** [e03h_amplitude.py:306](/D:/Claude/random/wormWars/scripts/e03h_amplitude.py:306) compares `P.CODE` against the binding commit. [P.CODE includes all of `scripts/`](/D:/Claude/random/wormWars/scripts/e03h.py:64), so committing this newly added script necessarily fails that comparison. Leaving it uncommitted fails the dirty check. Compare the reused implementation paths explicitly; retain this new script in the clean/pushed check. Smoke bypasses this guard.

- **Medium — discordant evidence still prints an affirmative recommendation.** [Guide branching:199](/D:/Claude/random/wormWars/scripts/e03h_amplitude.py:199) ignores `flags`; [console output:340](/D:/Claude/random/wormWars/scripts/e03h_amplitude.py:340) prints only the branch. Significant sham damage can therefore produce “a redesign round is supported” without its qualification. Make discordance override the branch and print its reasons.

- **Medium — provenance comparison remains missing.** [Preflight:305](/D:/Claude/random/wormWars/scripts/e03h_amplitude.py:305) checks package pins, but never compares the pilot’s GPU/CUDA/connectome provenance. Add the existing `require_same_env` check before computation.

- **Low — negative ratio bounds are reversed.** [ratio_range:171](/D:/Claude/random/wormWars/scripts/e03h_amplitude.py:171) returns `lo > hi` when the mean is negative. [Test:62](/D:/Claude/random/wormWars/tests/test_e03h_amplitude.py:62) explicitly permits this. Sort the endpoints and test a negative mean.

- **Low — 35% is not a general dependence bound.** [Docstring:43](/D:/Claude/random/wormWars/scripts/e03h_amplitude.py:43): approximately 35% is the independent-amplitudes result; arbitrary dependence permits approximately 38%. State the dependence assumption.

Fable’s saved level-decile, graph-name, and 0.25 reporting fixes are present. The saved CUDA smoke records completion in **42.8 seconds**. No experiments/tests rerun; no edits.