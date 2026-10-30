# M6-3's reading records

- `sources.json`: the 44 sources (39 in the batch, 5 added in round 2), with the Europe PMC query used, the date searched (2026-10-30), identifiers and
  which full-text service supplied the text (`full_text`: `europepmc`, `ncbi-efetch` or null for abstract only).
  Abstracts and full texts are not committed.
- `batch.py`, `totext.py`: the retrieval scripts (Europe PMC search and full-text XML; NCBI E-utilities efetch for
  the PMC open-access and author-manuscript copies). Public interfaces only.
- `quotes-*.txt`: the verbatim quotes the three reading agents used, each with its source key and line number in the
  local plain-text file, except `quotes-states-history.txt`, which has the source key without line numbers. All 386
  were checked by exact string match against those files. The formats differ by agent (`key|line|quote`,
  `key@@line@@quote`, `file|||quote`).
- `check_report.py`: checks every quoted passage in `docs/memory/M6-3-LITERATURE.md` against the local texts and
  abstracts (draft 2: 50 of 50 found; a sabotaged quote is caught).
- `claude-log.md`: Claude's running log of what was read and at what level, including sources fetched before the
  batch.
