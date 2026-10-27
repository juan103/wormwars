# Review request: M4e's results, draft 3

Round 2: both of you said "fix then publish" (`r2-fable.md`, `r2-astra.md`). Draft 3 is
`docs/memory/M4E-RESULTS.md` (draft 2 archived as `draft2.md`). Read-only. Every round-2 finding was taken:
- Δ_count's envelope: the wrong mechanism removed; now "the second pass settled 20 of U_LH's and 2 of U_HH's
  unresolved genomes ... narrowed the envelope enough to clear zero", with Astra's per-arm recomputation (U_LH's alone
  −0.0001, U_HH's alone +0.0002) cited to the review archive.
- The reproduction statement split by reviewer (Astra regenerated and reproduced; Fable checked against the files).
- Threshold: "arm averages look threshold-like"; "consistent with Δ_weight's unresolved direction and small counted
  difference"; the S3 gap 0.96–1.26; the predictor neither confirms nor refutes a step (354 to 629 strong-arm genomes
  below 1.0, 0 to 3 switches; AUC 0.41–0.66); the "wrong shape" sentence removed.
- The host-dependent baseline, without locating its source (host autapses inside C3; per-host genome panels).
- In-band medians attributed to Astra, computed from saved per-genome values.
- W − U_HH's thin envelope (about five genomes), in the table and the roadmap bullet.
- 56 of 201 unresolved settled (28%); 75 s described as the smoke's per-genome processing estimate.
- U_HH − I: no interval, dominated by SH-recip-2051100.
- S3 matching: two of 20 K draws within 0.05 of 1.714, roughly ten proposals per accepted draw at that tolerance, to
  be reassessed.
- M5: estimand and success criterion before power, multiplicity, a separate variance for the S3-matched control; the
  decomposition as variance of estimated host contrasts (51/8/41), doubling genomes × 0.89.
- The results artifacts are committed with the results (D368), as Astra noted they must be.

Please confirm the fixes and say whether anything still blocks publication. Verdict: agree / fix then publish / do not
publish.
