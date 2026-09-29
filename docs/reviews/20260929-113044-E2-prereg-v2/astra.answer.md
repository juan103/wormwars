**revise**

Three failure-path issues remain. The comparison design needs no redesign.

Must-fix items:

1. **Rerun setup can still deadlock or falsely consume the rerun.** [scripts/e2.py:495](/D:/Claude/random/wormWars/scripts/e2.py:495), `apply_rerun`, and `run_stage` at line 535.
   
   A kill after writing the rerun note but before creating the new marker leaves neither a current record nor a current marker. Another `--rerun` says “rerun once already”; the next stage says “has not run.” Also, archiving still uses bare `os.replace`: failure after moving the record but before moving the marker lets recovery mistake the **first attempt’s marker** for a killed rerun and finalize it.
   
   Make rerun setup recoverable and distinguish the two attempts durably. Test interruptions between archive moves and between writing the note and creating the marker. The four existing crash/kill tests cover failures after setup.

2. **A killed extension before its first checkpoint still loses its champions.** [scripts/e2.py:453](/D:/Claude/random/wormWars/scripts/e2.py:453), `final_killed_record`; §6.
   
   With no partial record, reconstruction produces no `champions_over_both`. `champions()` consequently evaluates zero extension arms, despite the completed formal ES providing the registered fallback champions. The `summary` callback fixes caught training exceptions, but cannot run after a kill.
   
   Reconstruct formal fallback champions when no extension checkpoint survived. Test a killed extension rerun with **no partial record**, through finalization and evaluation.

3. **An early caught extension failure is evaluated but omitted from the reported summary.** [scripts/e2.py:985](/D:/Claude/random/wormWars/scripts/e2.py:985), `analyse`.
   
   Before the first extension checkpoint, salvage returns `records=[]` alongside valid formal fallback champions. Evaluation uses `champions_over_both`, but `analyse()` enumerates `ext["records"]`; it therefore reports `runs={}` and `mean=None` despite having evaluated those champions.
   
   Build the extension summary from `champions_over_both` or the evaluated extension arms. Extend the existing stopped-extension tests through evaluation and assert the reported runs, mean, and incomplete label.

Suggestions:

- Test reconstructed records with formal guards enabled, both with and without partial records. Current kill fixtures use only `git_commit="x"` and disable guards. For a valid, matching partial/marker pair, retaining the original provenance is correct; also check disagreement explicitly.
- Add pairing tests with a deliberate hash mismatch, no shared runs, and known numerical ES-minus-GA differences. The current test checks matching hashes and difference keys only.
- Test `replace()` directly and retry exhaustion. The bounded retry implementations look sound, but the existing test exercises only `write_atomic()`.

Checked and found correct:

- The ordinary four crash/kill combinations now have the intended finalization logic and corresponding tests, subject to item 1.
- Incomplete ES has distinct wording and cannot win despite qualifying scores. §8 now specifies excessive projection, stopped pilot/evaluation, extension incompleteness, and first-stop status.
- Per-arm evaluation snapshots are written inside both arm loops; a test checks retained arms.
- Middle-first pilot ties, stage-two reuse, and the uninformative flag match §4.
- Earliest-best extension selection and formal-first ties are correct once champions reach the record.
- Exposure corrections, separate smoke projection seeds, moved formal projection seeds, budget labels, ES constants, binary state hashing, and checkpoint-time flat counts are addressed.
- Pairing and per-run differences are correct for ordinary complete records.

I inspected HEAD `99f06a9`, the diff from `12725de`, both archived reviews, D120, all requested files, and the shared guards. I did not execute the suite or independently verify the claimed fail-before-pass/sabotage history.