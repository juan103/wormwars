# Review: the memory thread's synthesis, M1 to M4 (draft 1)

You reviewed every step of the memory thread (M1 to M4d; D349-D364). The owner asked for the write-up of M1 to M4,
which Astra recommended after M4d. Please review `docs/memory/SYNTHESIS.md` (draft 1), read-only, against the
committed results files (`docs/memory/M1-RESULTS.md`, `M2-PILOT-RESULTS.md`, `M2-CENSUS-RESULTS.md`, `M3-NOTE.md`,
`M4A-RESULTS.md` to `M4D-RESULTS.md`, `MEMORY-ROADMAP.md`), DECISIONS D346-D364, and the new summary:
`scripts/memory_summary.py` writes `docs/memory/summary.json` from the committed records
(`tests/test_memory_summary.py` checks it equals what the records give, with a sabotage).

Please check:
1. **Every number and reading** against its source. Is any reading stated more strongly than its fixed wording
   ("inconclusive", "unresolved", positive, "Unresolved (the unresolved genomes decide it)")?
2. **The cross-step interpretation** ("What it adds up to", "What holds, and what is open", "A reading across the
   steps"). Is it fair, properly labelled as interpretation, and not stronger than the data? Is anything important
   missing (a limit, a negative result, a correction)?
3. **The "Who did what" section.** Is the attribution accurate from the archived reviews and DECISIONS? Correct
   anything misattributed or missing, especially your own contributions.
4. **Readability for an outside reader of `main`.** Is the page clear without the step files? Anything confusing?
5. **The summary script**: does it read the right fields, and is anything the synthesis quotes from it wrong?

Rank your findings. Verdict: agree / fix then publish / do not publish.
