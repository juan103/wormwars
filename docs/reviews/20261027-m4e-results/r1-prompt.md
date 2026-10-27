# Review request: M4e's results, draft 1

You reviewed M4e's design in two rounds and its plan and code in three (`docs/memory/M4E-PLAN.md`, draft 4; D367;
your answers are in `docs/reviews/20261025-dense-block-design/` and `docs/reviews/20261026-m4e-plan/`). The run has
finished. Please review the results write-up, `docs/memory/M4E-RESULTS.md` (draft 1), against the plan and the
outputs. Read-only.

**Outputs** (all in `runs/memory-m4e/`): `readings.json` (from `scripts/memory_m4/m4e_read.py`; console
`read_log.txt`), the 160 panel records `arms/<host>__d<draw>__<arm>.json`, `hosts.json`, `coverage.json` (committed
before any arm ran), `blocks-summary.json` and `tables.json` (from `scripts/memory_m4/m4e_tables.py`; console
`tables_log.txt`), `m4e-attempt.json`, `m4e-compute-record.json`, `m4e_log.txt`, `stage0.json`. `blocks.json` stays
local (N2's C3 weights edge by edge in W, K and T; rule 1); the summary carries its sha256.

**The reading:** Δ_weight (U_HH − U_HL) −0.0008 [−0.0017, +0.0001]: direction unresolved; "no effect of 0.004 or
more, as a mean across these ten hosts (...)". Δ_count (U_HH − U_LH) −0.0026 [−0.0041, −0.0012]: "lowers" (holds on
the envelope, −0.0094 to −0.0004); size "unresolved (the unresolved genomes decide it)" ("at least 0.001" on the
interval, "size unresolved" on the envelope). The second pass was used (no audited fading genome became separate
states; 783 to 800 audited fading per arm); on the first pass alone Δ_count's direction would be unresolved by the
envelope. One incident: the reader's first invocation wrote readings.json and then crashed printing "Δ" to a cp1252
console; rerun with PYTHONIOENCODING=utf-8, byte-identical readings.json.

Please check, and say what must change before this is committed and pushed:
1. **The reading:** is it the plan's reading, computed as the plan fixed it (two fields, the envelope rule that a size
   sub-field stands only if it holds on both, the guard, the coverage response, the second pass and its audit)?
2. **Every number** in the write-up against the files. Overclaims, missing caveats, wording beyond the data.
3. **The after-the-data interpretations:** "concentration matters" and M4d's finding "read here as mostly a
   coupling-strength effect"; the strong arms not collapsing on S2 or the predictor; the dose model's excluded hosts
   (six hosts have every U-arm switch at U_LH, the largest S2; the draft says the mean slope over the remaining four
   should not be read as evidence against a rise with S2); the per-host pattern (low-coupling arms switch almost only
   in three hosts). Are any of them misleading or too strong?
4. **What is committed:** the 160 panel records, `blocks-summary.json` (K's and T's degree ranges), `tables.json`
   (every genome's predictor value, a derived scalar of its signed block including N2's block in T). Does anything
   carry connectome structure that rule 1 forbids?
5. **For M5** (the owner's third item: an M5 test of N2's exact wiring, after first working out how many hosts it
   would need to detect a given effect). The draft says M5's controls must match concentration (K-type controls match
   S1 and S2 but not S3), carry the second pass and a dynamics outcome, and take T − K's host spread (SD 0.0055) as the
   power calculation's input. Is that the right reading of the plan's "After the reading" rules? What should the power
   calculation assume (which contrast, which variance components: hosts, draws, genomes; which effect sizes; how to
   treat the unresolved genomes)?

Rank your findings, and give a verdict: agree / fix then publish / do not publish.
