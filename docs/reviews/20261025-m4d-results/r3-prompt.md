# Review request: M4d's results, draft 3 (round 3)

Round 2 (`docs/reviews/20261025-m4d-results/r2-fable.md`, `r2-astra.md`): both "fix then publish". Draft 3 is
`docs/memory/M4D-RESULTS.md` (draft 2 archived as `draft2.md`). Read-only. All findings taken:
- **Power (Astra 1):** the "about 5% power ... far more hosts ... out of reach" passage is replaced: at δ = m the rule
  fires in at most 4.5% of screens, as expected at the null boundary whatever the number of hosts; feasibility needs a
  power calculation for specified effects above m, host variability, a planned treatment of unresolved genomes and a
  base-rate margin. The owner's M5 option no longer says "out of reach".
- **T − P interval (both):** "as wide as the whole transplant effect (0.0059), reaching about half of it on either side".
- **Timing (both):** the slowest panels are "two of the three with the most unresolved genomes (12 and 10; the third,
  with 13, took 1653 s)"; the I panel at 1815 s shows the sharing; the records cannot say how much. Fast panels 790 to
  1624 s.
- **Not-settled pattern (Astra):** "commonest with N2's exact weighted block (T and T+G)"; P keeps the edges and has 46.
- **Descriptive envelopes (Astra):** `m4d_tables.py` now prints the unresolved envelope for R − D, R − I, D − I, T − Rr,
  T − P and (T+G) − T; the text gives them, and the owner's density option now says R − D holds on counted genomes
  only (envelope −0.0043 to 0.0090), while T − I, R − I and D − I hold over every assignment.
- **Nits (Fable):** "consistent with" for the companion controls; the resolution outcomes now name the single-host
  form in both places; `verify_run` computes the arm hash and `validate` matches it; the manual sha256sum line is
  dropped (the tables script stops on a mismatch); the note that `m4d.py hosts blocks` appends to the local compute
  record.
- **Rule 9 (Fable):** the digest stop is now `check_digest` in `m4d_tables.py`, with a test
  (`test_the_tables_stop_on_a_changed_blocks_file` in `tests/test_memory_m4d.py`) and a sabotage (24 of 24 fail as
  they must: `runs/m4d-sabotage.txt`).

Please check the fixes and give a verdict: agree / fix then publish / do not publish.
