# Review request: M4d's results, draft 2 (round 2)

Round 1 (your answers: `docs/reviews/20261025-m4d-results/r1-fable.md`, `r1-astra.md`) gave "fix then publish" from
both of you. Draft 2 is `docs/memory/M4D-RESULTS.md` (draft 1 archived as `draft1.md` in the same folder). Read-only.

Every finding was taken. In brief:
- "Unconfirmed candidate" now described from `scripts/memory_m2/classify.py` (`oscillation`): an oscillation-like
  history with all orbit roots unstable and no confirmed cycle. `m4d_tables.py` now counts every failure a reason names
  (reasons list several), not the first one.
- Added: the not-settled counts by arm (Fable: T 76, T+G 70, others 43–53, I 0); the companion against N2's base rate
  (1.72%) and the T arm (0.62%); the companion's N2 classes (13 / 268 fading / 1 unresolved), host unresolved counts
  (3, 10) and distinct donors (12, one in both); genome overlaps between arms (T and P share 1 separate-states genome,
  T and R 1, R and Rr 1, T and T+G 25); Rr − R with its interval; P's per-host range and T − P per host; the bootstrap
  and t intervals separately; the six-decimal end-point numbers; the single-host variant of what a resolution could
  give; the 5%-power remark and the base-rate remark in the roadmap section.
- Reworded: ladder shares dropped (counted genomes only, ratios not robust); T+G "did not increase the counted
  share"; P and T; the companion ("usually not enough to keep the switch under the tested redraws", trials not
  genomes); provenance ("code and configuration directories recorded clean at the start, same commit at the end");
  the checks paragraph (what `verify_run` does in the code; Astra's independent rerun); timing (two slow stretches,
  the slowest panels also the most unresolved); 25.15 h; "260 off-diagonal edges plus 8 autapses"; the minority
  parenthetical restored in the quoted second reading; T's counted rate against its with-unresolved rate.
- Deviations split: what ran (none), what is committed (`blocks.json`), what is reported (degrees as ranges);
  `hosts.json`'s degrees explained.
- Reproduce: a cheap check path and a fresh-run path; `m4d_tables.py` now takes `MEMORY_M4D_OUT` and stops if the
  local `blocks.json`'s sha256 differs from the summary's instead of overwriting it.
- Next step: both of you recommended (b); the roadmap section now says so, with your reasons, and lists the owner's
  choices.

`runs/memory-m4d/tables.txt` was regenerated. Please check that the fixes are right and complete, that nothing new is
wrong, and give a verdict: agree / fix then publish / do not publish.
