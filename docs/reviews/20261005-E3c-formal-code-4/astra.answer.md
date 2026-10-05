**Fix first. One durability defect remains at `2e40827`.** I checked both reviewers’ archived findings; this is one independent review.

The remaining defect is that **the champion archive and its salvage record can disagree after an interrupted save**.

At [scripts/e3c.py:1155](D:/Claude/random/wormWars/scripts/e3c.py:1155), `per_run` advances before `save_atomic` succeeds. If that save fails, the previous archive survives, but the frame writes the advanced in-memory salvage at [scripts/e2.py:631](D:/Claude/random/wormWars/scripts/e2.py:631). Evaluation then rejects the archive at [scripts/e3c.py:1279](D:/Claude/random/wormWars/scripts/e3c.py:1279).

I reproduced this with the real champion-stage control flow and in-memory dependencies:

- First champion save succeeds.
- Second save raises `OSError`.
- Last durable partial lists run `[0]`.
- Caught-stop salvage lists runs `[0, 1]`.
- Surviving archive contains only run `[0]`.
- Evaluation’s hash-list comparison rejects it.

On a final stopped attempt, this blocks previously completed champions. There is also the reverse interruption window: replacement succeeds, then the process dies before the updated partial record is written.

**Required change:** make recovery preserve a consistent champion record and genome set across both windows. Immutable, versioned archives referenced by the committed progress record would work; verified reconstruction from saved final populations is another option. Merely moving `per_run.append` after the save does not close both windows. Add regressions for failure during replacement and interruption after replacement but before progress publication. The existing [atomic-save test](D:/Claude/random/wormWars/tests/test_e3c_stages.py:535) checks preservation of bytes, not downstream usability.

Against **Astra’s five items**:

| Item | Recheck |
|---|---|
| Path-shape mismatch | **Fixed.** Writer and validator now agree on `[worlds, weys]`: [writer](D:/Claude/random/wormWars/scripts/e3c.py:1234), [validator](D:/Claude/random/wormWars/scripts/e3c.py:1313). |
| Per-play durability and atomic champions | **Partly fixed.** W2-turn, P-joint’s points, learning references and `g-e` legs now enter progress promptly. The archive/record consistency defect above remains. |
| No-evaluate report | **Fixed.** It uses the normal reporting path and retains available cost readings: [report_from](D:/Claude/random/wormWars/scripts/e3c.py:1577). |
| Corrupt archives trigger retraining | **Fixed.** Archive exceptions enter the recorded verification-failure fallback: [reuse handling](D:/Claude/random/wormWars/scripts/e3c.py:1003). |
| Bootstrap seed | **Fixed.** Each contrast starts from scalar seed `20261007`: [bootstrap](D:/Claude/random/wormWars/scripts/e3c.py:1427). |

The pre-start and final-frame cap cases are now tested. I also reproduced both in memory: the former creates no marker or record; the latter retains completed measurements as salvage.

Against **Fable’s earlier findings**, D212–D214 correctly address persisted checkpoint consistency across reuse, retraining after failed verification, salvage-shaped reporting, absent W2-turn/references, Holm with unread contrasts assigned p = 1, and smoke rerun cleanup. The checkpoint exemption is withdrawn in the annotation and the check is enforced again at [scripts/e3c.py:1054](D:/Claude/random/wormWars/scripts/e3c.py:1054). The remaining qualification is the champion recovery defect above.

**Verification:** 65 selected read-only tests passed. I also verified the registered-text hash, engine freeze, four pinned inputs, and all 512 P-joint population hashes. I did not run the writing smoke tests or full suite. I found no additional registered-calculation discrepancy on an uninterrupted run.