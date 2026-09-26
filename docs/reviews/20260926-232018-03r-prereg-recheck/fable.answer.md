**Must fix before binding: none that block the run.** One text sentence contradicts the code and should be corrected in the binding commit:

- **§10 "The gate table is published whatever the outcome"** cannot hold for the withheld case. When P4 is incomplete, `build` computes nothing for it (`report.py:185-189`), so `replication_primary` returns only the withheld record and counts, no per-ensemble ranks, no side-by-side. §6 already states correctly what a withheld report contains (the five accounting counts). Change §10 to "for every evaluated outcome; when withheld, the accounting counts of §6", or make the code compute the descriptive per-ensemble values regardless of completeness. Text is the cheaper fix.

**Should fix (cheap now, expensive after the first measurement):**

- **The pinned connectome cache is hashed with the CRLF-normalising hash.** `provenance()` applies `_sha` to every `INPUT_FILES` entry (`scripts/exp03.py:161`), including the binary `cook2019_herm.npz`. D056 chose `_sha_raw` for binaries. The result is still a deterministic fingerprint, so provenance checking works, but it is the wrong function for an npz and any later fix means re-measuring every graph.
- **Cap headroom is thinner than §8 implies.** D060's smoke measurement took 126 s, not 111 s. At 126 s the 768 ensemble graphs need 26.9 h against the 28 h cap, 4% headroom. Skips are proportional and the floors tolerate 6.25%, so the design degrades gracefully up to about 134 s/graph, and a withheld result needs roughly 150 s/graph. The smoke figure probably includes warm-up, but since the cap cannot be changed later, decide now whether 28 is the number.

**Minor:**

- For N2perm4-6, the fresh secondary permutation changes what "M0-permuted" means relative to 03: in 03 an N2perm graph's M0-permuted condition reused its own permutation, in 03r it gets a second, different one. Descriptive only, but worth one clause in §4.
- `spent_hours` sums N2's and its variants' seconds too. That only matters on a resume after N2 is measured, where it makes the cap bite harder, which is consistent with "never extended".

**My v1 findings, checked in text and code:**

| # | finding | status |
|---|---|---|
| 1 | §10 outcome wording | resolved: table of five fixed sentences, gate table, side-by-side, no pooling |
| 2 | threshold argument, error rates, effect-interval comparison | resolved: §6, §5, `side_by_side` |
| 3 | 256 SH-route stated as my request | resolved: §3 |
| 4 | cap can defeat N2-last | resolved: "never extended"; enforced structurally, since changing `INSTANCES` changes the commit and `check_resumable` refuses |
| 5 | cap in `INSTANCES`, CLI refused | resolved: `cap_hours`, test |
| 6 | withheld primary written | resolved: `replication_primary` |
| 7 | §7 relabelled, 0.925 row, independence | resolved: §7 with prior and noise columns; `power.py` logic is right |
| 8 | probe caveat in README sentence | resolved: §10 |
| minor | n = valid graphs; calibration map; power.py assumptions | all resolved |

Astra's items I could verify by reading are also in: per-ensemble gates match `classify` and `rank_p` exactly, the fresh permutation seed reaches the brain via `manual_seed(seed*2+salt)` with no range issue, and instance 03's paths return `current` unchanged. The cutoffs in §6 and the §0 and §6 arithmetic check. Test count is 18. I did not execute the tests or regenerate 03's report; D060's claim that 03 regenerates identically is taken from the log.

**Verdict:** ready to bind once the §10 sentence is corrected and, in the same commit, the cache hash switched to `_sha_raw`.