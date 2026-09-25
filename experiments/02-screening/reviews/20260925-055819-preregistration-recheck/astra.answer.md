1. **FIXED** — [analysis.py:352](/D:/Claude/random/wormWars/wormwars/exp02/analysis.py:352) converts the anchor flag to native `bool`; [test_exp02_report.py:71](/D:/Claude/random/wormWars/tests/test_exp02_report.py:71) now verifies plain JSON serialization.

2. **FIXED** — [analysis.py:235](/D:/Claude/random/wormWars/wormwars/exp02/analysis.py:235) removes the inconsistent equivalence branch, matching [PREREGISTRATION.md:89](/D:/Claude/random/wormWars/experiments/02-screening/PREREGISTRATION.md:89).

3. **NOT FIXED** — [report.py:69](/D:/Claude/random/wormWars/wormwars/exp02/report.py:69) checks SH names, not required run indices or registered seeds. Removing **all SH run-0 records still produces `complete=True`, `supported`**, contrary to [PREREGISTRATION.md:95](/D:/Claude/random/wormWars/experiments/02-screening/PREREGISTRATION.md:95). Also, [report.py:155](/D:/Claude/random/wormWars/wormwars/exp02/report.py:155) calculates capability before validation: a 63-score vector crashes instead of withholding. Reproduced both.

4. **NOT FIXED** — [scripts/exp02.py:479](/D:/Claude/random/wormWars/scripts/exp02.py:479) resets measured step costs on resume; [line 551](/D:/Claude/random/wormWars/scripts/exp02.py:551) retries previously dropped steps. Reproduced a resume taking accounted time from **90 to 150 seconds under a 100-second cap**. Furthermore, [line 573](/D:/Claude/random/wormWars/scripts/exp02.py:573) prints unassessed (`None`) tripwires as **“ok”**, violating §6.

5. **FIXED** — [report.py:129](/D:/Claude/random/wormWars/wormwars/exp02/report.py:129) bootstraps run-averaged world differences; [PREREGISTRATION.md:107](/D:/Claude/random/wormWars/experiments/02-screening/PREREGISTRATION.md:107) explicitly limits interpretation to detection counts.

6. **FIXED** — [analysis.py:146](/D:/Claude/random/wormWars/wormwars/exp02/analysis.py:146) and [PREREGISTRATION.md:140](/D:/Claude/random/wormWars/experiments/02-screening/PREREGISTRATION.md:140) consistently specify 90% of fitted improvement.

7. **FIXED** — [analysis.py:125](/D:/Claude/random/wormWars/wormwars/exp02/analysis.py:125) uses group sizes and the unbalanced ANOVA correction; [test_exp02_analysis.py:231](/D:/Claude/random/wormWars/tests/test_exp02_analysis.py:231) covers mixed replication.

8. **NOT FIXED** — Minor remaining contradiction: [PREREGISTRATION.md:175](/D:/Claude/random/wormWars/experiments/02-screening/PREREGISTRATION.md:175) still specifies **16 behaviour worlds**, whereas §5 and [scripts/exp02.py:561](/D:/Claude/random/wormWars/scripts/exp02.py:561) specify four. Valence scope and integrator units are corrected.

9. **FIXED** — The [original numbered review](/D:/Claude/random/wormWars/experiments/02-screening/reviews/20260925-045005-go-no-go/astra.answer.md:1) is archived; [PREREGISTRATION.md:22](/D:/Claude/random/wormWars/experiments/02-screening/PREREGISTRATION.md:22) discloses both N2 numbers.

**NEW blockers:** None additional identified. Points **3 and 4 remain run blockers**.