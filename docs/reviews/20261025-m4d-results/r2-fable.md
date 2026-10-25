**Verdict: fix then publish.** Two sentences are wrong or misleading, both descended from my own round 1 review, and both are one-line fixes. Nothing touches a table, an interval or the reading. With those two fixed I would say agree.

**What I checked.** Every number in draft 2 against `readings.json`, `tables.txt`, `blocks-summary.json`, `hosts.json`, `companion.json`, the attempt and compute records and the run log. The regenerated `tables.txt` matches the records, and its new every-failure reason counts reproduce from the T panels' reason strings (37 unconfirmed candidates, 38 unstable or marginal roots, 12 Newton failures, 7 around a stable root). The single-host variant in the per-end paragraph is reachable: with SH-mirror-2041001 at its all-for-T end and every other host at its low end, the t upper bound is about 0.003 and the guard fires. The accounting code records cleanliness of the three code directories at the start and the commit at the end, as the draft now says. All of round 1's findings from both reviewers are in the text.

**Must fix.**

1. **The timing sentence is false as written.** Draft line 57 says the two slowest panels "are also those with the most unresolved genomes (12 and 10)". The panel with the most unresolved genomes is SH-recip-2051000's P, with 13, and it took 1653 s. The two slowest panels are two of the three with the most. My round 1 review stated this wrongly; I am the source. Say "two of the three panels with the most unresolved genomes (12 and 10; the third, with 13, took 1653 s)". The hedge about shared CPU stands either way, and SH-recip-2051000's I panel (0 unresolved, 1815 s) shows the sharing directly.

2. **"The interval spans about half the whole transplant effect"** (line 177) is misleading. The T − P interval runs from −0.0035 to +0.0025, a width of 0.006, which equals the whole transplant effect of 0.0059. Each end is about half of it. Also my round 1 phrasing. Say "reaches about half the transplant effect on either side" or "is as wide as the whole transplant effect".

**Nits, take or leave.**

- Line 54: the sixty fast panels ran 790 to 1624 s, not "to 1650". The cutoff sits oddly close to the 1653 s of the slow group.
- Line 215: "the controls match their references" rests on 6 of 282 in N2. "Are consistent with" is what that count supports.
- Line 245 says a resolution could only move the reading between the second reading and "Unresolved". The reading section also names the single-host variant. Make the two agree.
- Line 235: "about 5% power at δ = m" is true by construction, since a 90% interval's lower bound exceeds a true effect of exactly m about 5% of the time. Adding "by construction" or citing the 0.015 case (98 to 100%) would say more.
- Line 69 credits `verify_run` with matching each arm graph to its recorded hash. In the code, `verify_run` computes the hash and the reader's `validate` does the match. The next clause already covers it, so merge them.
- Reproduce, check path: `sha256sum` is not on the tested Windows platform without Git Bash. Since `m4d_tables.py` now stops on a mismatch, that step is the check, and the manual line can be dropped or given a PowerShell alternative. Also, `m4d.py hosts blocks` runs inside the accounting wrapper, so it appends an attempt to the local compute record. That record is gitignored and the committed copy is the run's, but a reader comparing the two should know.
- The tables script's sha-mismatch stop is new behaviour with no test in `tests/test_memory_m4d.py`. Rule 9 would ask for one. Not a blocker for the results document.

**Not verified by me.** I have no shell in this session, so I could not confirm that `coverage.json` is in commit 6553a98. The plan text in that commit carries the simulation's numbers, which is what matters.