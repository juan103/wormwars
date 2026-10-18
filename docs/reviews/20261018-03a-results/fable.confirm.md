**Publish.** Every finding from my review is resolved, and the rewrite introduced no numeric error. I re-checked every number on the page against `summary.json` and, where the summary does not hold it, against the raw records. Four trivial loose ends remain, listed last. None needs to block the push.

**My findings, by number**

1. ROADMAP review timing: resolved, `ROADMAP.md:9-12`. The corrected chronology matches PILOT-DEV's status lines 12 to 14.
2. "Registered recovery statistic": resolved, `RESULTS.md:288`.
3. "N2 would share it": resolved. `RESULTS.md:29`, `174-176` and `262` now claim only that neither NIP target-brain had headroom above p.
4. The probe reading: resolved. All three KTS rows are in the table at `RESULTS.md:109-111`, the ±0.19 and the no-scale point are at `116-125`, and the design's other limits at `126-128`. The differences check: T=10 gains 0.1929 and 0.1592, T=20 loses 0.1944.
5. Advantage under V1 and the single-chain variants: resolved, `RESULTS.md:269-271`.
6. Corrections list and record range: resolved, `RESULTS.md:301-302`, `306-308`, `331`.
7. Reproduce it: resolved as to the refusal and the rerun's reuse of finished rows, `RESULTS.md:316-321`, which match `scripts/e03a.py:791-800` and `1436-1445`. One small gap is listed below.
8. The preflight's hours: resolved. `pilot-dev/preflight-compute.json` is committed and its total of 92.61376 seconds matches the local `runs/e03a-smoke-cuda/pilot-dev/compute.json` exactly. The note at `summary.json:62` now says where it comes from.
9. Q ranges: resolved, `RESULTS.md:162` and `166-167`.
10. "A reading": resolved, `RESULTS.md:24`.
11. "One target-brain with headroom": resolved, `RESULTS.md:31`, `257`, `274`.
12. Project README lead: resolved, `README.md:36`, with the earlier text quoted.
13. Stale "does not fit our compute": resolved by annotation, `README.md:401-403`.
14. 03a README annotations and the mixed commit-and-hours sentence: resolved, `README.md:37-39`, `197-198`, `203-204`.
15. ROADMAP's "full map" line: resolved, `ROADMAP.md:588-589`.

Astra's eleven are also taken. The three double-roundings now read 0.08, 1.16 and 2.34, which are the single roundings of the raw values. The per-type null SDs quoted at `RESULTS.md:217` are the recorded ones. Their finding 6 shares the gap below.

**Numbers checked and correct:** the stage table, the compute lines, the champions, the panel, all 45 probe cells, the tuning figures, the four-column `full` table, the longer-search AUCs, the paired-difference means and SDs, the projection, the three-variant table including each interval bound against the raw values in `search-check.json`, the lesion, the re-evaluation table and its Spearman values, and every figure in the summary paragraphs.

**Remaining, all trivial**

- `RESULTS.md:317-318`. Moving `pilot-dev/*.json` aside also removes `compute.json` and `preflight-compute.json`. The stages write their aggregate to `runs/e03a/pilot-dev/compute.json` and nothing copies it back, so `e03a_summary.py` would fail after a from-scratch run. Say to move the ten stage records aside, and to copy the new aggregate into `pilot-dev/` before rebuilding the summary.
- `RESULTS.md:183`. "0.6-1.0" holds for the refits and the 100-generation free searches. The two longer searches have 0.55 and 0.65 as their lowest pair rates. Add "in the 100-generation searches", or widen to 0.55.
- `ROADMAP.md:7`. The entry's header still reads D302-D318 while its corrections cite D319.
- `experiments/03a-self-consistency/README.md:164`. "The compute aggregate" is now two files.