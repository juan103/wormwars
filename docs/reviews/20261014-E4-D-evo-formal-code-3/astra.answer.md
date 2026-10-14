**Run it.** Reviewed `5237304`. All four findings from my second review are resolved; no new blocking findings.

1. **Resolved — Medium, amendment preservation.** [scripts/e4d_evo_formal.py:250](/D:/Claude/random/wormWars/scripts/e4d_evo_formal.py:250): prefix checks now cover the bound, formal, predecessor and first-attempt commits. Integrated in-memory probes rejected altered formal/predecessor text. No further fix.

2. **Resolved — Medium, interrupted rerun provenance.** [scripts/e4d_evo_formal.py:241](/D:/Claude/random/wormWars/scripts/e4d_evo_formal.py:241): archived-marker fallback works; changed environments and reruns lacking both markers are refused. The frame’s ordering makes this effective before restarting. No further fix.

3. **Resolved — Medium, incomplete observations.** [wormwars/e4/evo_formal.py:155](/D:/Claude/random/wormWars/wormwars/e4/evo_formal.py:155): finite, bounded validation shares, binary counts and exactly one outcome per assignment are enforced. The new malformed-observation test passes, including the binary double-outcome/missing-outcome case. No further fix.

4. **Resolved — Low, wording and smoke metadata.** [PREREGISTRATION.md:499](/D:/Claude/random/wormWars/experiments/E4-two-minds/E4-D-evo/PREREGISTRATION.md:499) correctly distinguishes the 300-tick tests from smokes and clarifies the training range. [scripts/e4d_evo_formal.py:764](/D:/Claude/random/wormWars/scripts/e4d_evo_formal.py:764) records the smoke’s actual blocks. No further fix.

I ran targeted read-only probes and four reporting tests; I did not rerun the full suite or GPU stages.

Yes: record `5237304ffce8251de30a635f27432800db7b091c` using the specified formal-commit line, commit and push that append, then run `check` after the owner’s word.