**No—fix before starting.** I reviewed `d0410a8` and its predecessor against the bound pre-registration. I ran 83 tests successfully, excluding the three tests that write files, and reproduced the failures below using in-memory stubs. I inspected the existing smoke records; I did not rerun stages or the formal GPU equivalence check.

The blocking findings are:

1. **Kill recovery is not wired correctly into E2’s frame.**  
   Files: [e3b1.py:118](D:/Claude/random/wormWars/scripts/e3b1.py:118), [e2.py:529](D:/Claude/random/wormWars/scripts/e2.py:529), [e3b1.py:720](D:/Claude/random/wormWars/scripts/e3b1.py:720), [e3b1.py:1036](D:/Claude/random/wormWars/scripts/e3b1.py:1036).  
   **§5 and §10:** killed attempts must be recoverable and their compute charged. `configure()` replaces E2’s registration dictionary, but the replacement lacks `rerun_kill_tail_seconds`. Kill reconciliation raises `KeyError`; I reproduced this.

   Merely adding that key is insufficient. The frame calculates elapsed work from its supplied files’ modification times. Neither training’s attempt journal nor evaluation’s completed chunks are supplied, and training writes no checkpoint progress record. A kill hours into training can therefore leave only the start marker as the accounting reference. Wire durable progress into reconciliation while preserving completed evaluation chunks.

2. **A kill during an internal second or third attempt leaves training permanently unsettled.**  
   Files: [e3b1.py:647](D:/Claude/random/wormWars/scripts/e3b1.py:647), [e3b1.py:340](D:/Claude/random/wormWars/scripts/e3b1.py:340).  
   **§5:** a second-attempt kill, or any third-attempt stop, makes the stage final. Consider attempt 1 non-finite, followed by a kill during internal attempt 2. The outer frame still has an attempt-1 marker. On recovery, `requires()` detects exhausted training attempts and exits **without writing a final stage record**. `stage_state()` continues returning `"killed"`, blocking subsequent stages. This remains broken after fixing finding 1. Terminal recovery must charge the attempt and durably settle the stage without running another batch.

3. **Internal retry admission omits the running stage’s elapsed time.**  
   Files: [e3b1.py:688](D:/Claude/random/wormWars/scripts/e3b1.py:688), [e3b1.py:392](D:/Claude/random/wormWars/scripts/e3b1.py:392).  
   **§5/§10:** every attempt uses hours already spent in its admission calculation. The callback calls `spent_hours()` without a start time. That reads completed accounting records; the current process’s accounting is written only on exit. Consequently, attempts 2 and 3 ignore the potentially substantial cost of earlier internal attempts. `project` handles its running time; training does not. The eventual 24-hour cap check does not repair an incorrect 22-hour admission decision.

4. **An internal admission refusal is recorded as failure and permits later training.**  
   Files: [e3b1.py:620](D:/Claude/random/wormWars/scripts/e3b1.py:620), [e3b1.py:677](D:/Claude/random/wormWars/scripts/e3b1.py:677), [e3b1.py:690](D:/Claude/random/wormWars/scripts/e3b1.py:690).  
   **§10:** refusal stops subsequent training; refused runs are “not run.” The internal refusal raises `RuntimeError`, writes no refusal file, and salvages `failed_runs` with `final=True`. Thus its state is `"final-stopped"`, which `check_order()` accepts for subsequent training. I reproduced the saved destinations and salvage result. Use the same durable refusal semantics as admission outside the stage.

   The unconditional `failed_runs` salvage also misclassifies a cap-stopped training attempt, which **§5** calls “not run.”

5. **Checkpoint non-finite scores do not identify their runs.**  
   File: [evolve.py:185](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:185).  
   **§5 and §12 test 4:** non-finite runs must be named and excluded from attempt 3. Training-rollout exceptions carry `.runs`; checkpoint-validation exceptions do not. The runner consequently records `runs=[]` and repeats the offending run in attempt 3. I injected a non-finite checkpoint score and confirmed the missing attribute. Apply the run identification to both error branches.

6. **S-peer has an extra, incorrect denominator dependency.**  
   File: [e3b1.py:1088](D:/Claude/random/wormWars/scripts/e3b1.py:1088).  
   **§7:** S-peer normalizes by the seed’s **own-condition first-B time**, and readings have independent requirements. The early return marks all four tests unread when the seed’s shared **visit** mean is zero. With complete first-B observations and a valid own-condition denominator, S-peer should remain readable. My synthetic example has valid S-peer `p=0`, but the runner returns `"not read"`. Check denominators separately for each reading.

7. **Secondary outcome labels contradict their alternatives and ignore Holm.**  
   Files: [tuning.py:96](D:/Claude/random/wormWars/wormwars/e3/tuning.py:96), [e3b1.py:1140](D:/Claude/random/wormWars/scripts/e3b1.py:1140), [e3b1.py:1153](D:/Claude/random/wormWars/scripts/e3b1.py:1153), [e3b1.py:1215](D:/Claude/random/wormWars/scripts/e3b1.py:1215).  
   **§7:** S-peer tests shorter times; secondary conclusions use Holm; positive S-trail wording is “increased trail dependence.” `T.gate()` always assigns G’s directional labels, regardless of `alternative`. A beneficial S-peer estimate of −0.1 with `p=0` is labelled `"worse"`.

   Furthermore, `readings` prints these unadjusted labels. I reproduced `"better"` with raw `p=0.04909` while Holm gives `p=0.14727`, unrejected. The numerical directional p-values and Holm calculation are correct; the reported conclusions are not. Separate test availability, raw statistics, and corrected secondary conclusions.

8. **The readings command crashes after terminal champion failure.**  
   File: [e3b1.py:1210](D:/Claude/random/wormWars/scripts/e3b1.py:1210).  
   **§5:** if `champions` stops finally, every reading is “not read,” without relabelling training runs. The stopped record has no `champions` key, but `cmd_readings()` accesses it unconditionally. I reproduced `KeyError: 'champions'`. Handle this terminal state explicitly.

9. **S-trail’s reported four means do not correspond to its registered contrast.**  
   File: [e3b1.py:1142](D:/Claude/random/wormWars/scripts/e3b1.py:1142).  
   **§7:** report the four means and the decomposition associated with the stratified contrast. The test uses complete shared/none pairs and equal schedule weights. The four means independently pool all available shared observations and all available none observations. With incomplete chunks, these can represent different runs; with unequal schedule sizes, their weighting also differs from the test. The stated decomposition then fails. I reproduced this with the final block-2 chunk missing. Calculate the summaries on the same complete pairs and schedule weights, and emit the decomposition explicitly.

Additional findings:

- **Non-blocking: validation composition is reported inaccurately.** [e3b1.py:752](D:/Claude/random/wormWars/scripts/e3b1.py:752), [e3b1.py:789](D:/Claude/random/wormWars/scripts/e3b1.py:789). All 32 genomes are validated, satisfying that part of §6, but default `chunk_worlds=512` produces eight chunks of **4 × 128**, while the record claims **32 × 128**. The benchmark uses the same splitting. Smoke fits in one chunk and does not expose this discrepancy. Correct the composition record; if one simultaneous 32 × 128 batch was intended, explicitly implement and benchmark it before running.

- **Non-blocking: saved learning-curve observations lose fractional visits.** [evolve.py:172](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:172), [evolve.py:189](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:189). Colony visits per wey can be multiples of 1/8, but generation-zero and checkpoint arrays use `astype(int)`. The selection scores and checkpoint means remain untruncated; the saved observation arrays do not faithfully reproduce them.

- **Non-blocking reporting gaps in §7:** [maze_runs.py:372](D:/Claude/random/wormWars/wormwars/e3/maze_runs.py:372) never computes replay route overlap, unlike the older `play_replay`; [tuning.py:128](D:/Claude/random/wormWars/wormwars/e3/tuning.py:128) returns no S-gen interval, including the specified zero-SE point interval. These outputs need completing.

- **Non-blocking enforcement gap in §5:** [e3b1.py:644](D:/Claude/random/wormWars/scripts/e3b1.py:644) checks earlier training stages’ states but does not require their records to be committed before the next training stage. The operator can follow the rule manually, but the runner does not enforce its advertised stage-publication sequence.

I found the mutation mask, degraded start, initial copies, run seeds, training IDs, checkpoint indices, pre-breeding snapshot, N access, champion tie-breaking, evaluation block order, replay coefficient calculation, and nose-recorder placement consistent with the registration. G’s main arithmetic, sign-flip weighting, minimum-run defaults, and Holm arithmetic also check out. N’s four-run timing and the completed-run projections for champion/evaluation admission are implemented.

On the implementation rulings: the brain-based carrier+W2 matches the literal “W2 alone on the carrier,” but must not be presented as replication of E3b-0’s scripted baseline. Plain `Brain` is equivalent to `StartedBrain` for this oscillator-free seed. The checkpoint subtraction and conservative evaluation projection are reasonable implementations. The CPU hook comparison establishes hook-on/off equivalence, not equivalence against the previous CPU engine; describe that evidence accurately.

**Verdict: fix then start**—fix the nine blocking findings above, particularly kill recovery/accounting, internal retry admission/refusal, checkpoint failure identification, and registered reading outputs.