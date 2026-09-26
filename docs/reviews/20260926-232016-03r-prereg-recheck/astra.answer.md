**Must-fix:**

1. **Withheld outcomes still lose the promised gate table.** [report.py:169](/D:/Claude/random/wormWars/wormwars/exp03/report.py:169) computes ensemble statistics only when *every* completeness condition passes. I reproduced an incomplete ensemble causing `P4: {}`; `replication_primary` then contains only the withholding reason and counts. [cmd_report:654](/D:/Claude/random/wormWars/scripts/exp03.py:654) also omits the side-by-side comparison. This contradicts §10’s “every outcome” commitment. Preserve available descriptive statistics and gates independently of verdict eligibility; mark genuinely unavailable quantities explicitly.

2. **Correct the pre-run disclosure and binding boundary.** [§1:41](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:41) says only structure was measured and no 03r brain has run. [D060:1482](/D:/Claude/random/wormWars/DECISIONS.md:1482) records an unsaved, end-to-end SH-1010000 measurement. Disclose that preflight measurement, which outputs were inspected, and its exclusion from the formal run. Clarify “first measurement” accordingly. This does not imply N2 was measured.

**Should-fix:**

- **Finish supplement validity/provenance handling.** [_quantiles:61](/D:/Claude/random/wormWars/experiments/03-generation0/supplement.py:61) excludes `None` but counts NaN/Inf as valid observations; I reproduced `n=3` with entirely NaN summaries from `[1, NaN, Inf]`. Filter nonfinite values. At line 90, `m.get("provenance")` also accepts measurements uniformly lacking provenance, unlike the main report. Reject missing provenance.
- **Soften the new threshold argument.** [§6:202](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:202) overclaims “close to a coin flip at any sample size” and “the only informative” test. Under the stated Jeffreys model, SH-route’s α/3 rank-pass probability is approximately **0.67 at 256**, approaching **0.77** as sample size increases. The single-signal choice remains defensible without those claims.

**Minor:** [§6:187](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:187) incorrectly generalizes that one failing ensemble makes every label “inconclusive.” A margin failure can coexist with other “distinctive” labels; a rank failure can produce “consistent” labels. The code handles these correctly.

The other v1 findings are resolved. The revised power table reproduces exactly. **14 report/verdict tests and 16 replication tests passed**; two filesystem-writing tests were skipped, and optional `dill` was disabled for read-only execution. Checked `roadmap` at `1785936`; no files changed.

**Verdict: not ready to bind until the two must-fix items are corrected.**