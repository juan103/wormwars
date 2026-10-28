# M5's power calculation, the script and its results: round 3 (Astra only)

Round 2 (`r2-prompt.md`, `r2-fable.md`, `r2-astra.md` in this folder): Fable agreed; Astra asked to revise narrowly,
for the invalid-host audit repair and the note's wording. Both agreed to the Welch reading and to recommending C.

What changed (each new test seen failing first; 49 pass; `runs/m5-power-sabotage.txt`):
- `scripts/memory_m5/m5_power.py`: `valid_hosts`; `contrasts` pools the audit rate over valid hosts only; `readings`'
  audit bound, its coverage and the hidden-count coverage use valid hosts only; `stage1_bound` (stage 1's valid
  audits only), used by `run_c`, whose hidden-count coverage also uses the final valid hosts; `run_c` keeps its
  rescaled-draw count and `over_125_own_mean`; `summarise_short` carries `cap_seconds`. `MR.WELCH_TOO` defaults to
  the adopted reading; `M5_WELCH_TOO=0` gives the reading as first written.
- `scripts/memory_m5/m5_reading.py`: `WELCH_TOO = True`, a constant (Fable).
- `tests/test_memory_m5_power.py`: four new tests at the end, including your counterexample
  (`test_an_invalid_hosts_audit_cannot_change_the_valid_reading`); three older tests pinned to the plain hull,
  because their worked numbers are the reading as first written.
- Reruns of the stages `scenarios`, `c`, `c_sens` and `report` for both readings (`power-r2.log` in each folder).
  Only the invalid-panel rows changed; every other scenario row and every C confirmation reproduced exactly. Your
  replayed C own-mean tail (143 and 62 of 10,000) matches `over_125_own_mean`.
- `docs/memory/M5-POWER-RESULTS.md`: draft 3 (archived here as `draft3.md`), with both reviewers' round-2 points.

Read-only. Is your round-2 repair complete and correct, and does draft 3 fix your wording points? Anything that
must change before the owner sees section 5? Verdict: agree / revise.
