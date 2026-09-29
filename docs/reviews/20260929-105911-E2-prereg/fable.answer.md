## Verdict: revise

Four small fixes, no redesign. The science and the arithmetic are sound, and the text carries design v2.2 faithfully. These need fixing now because the text is frozen after binding. I ran nothing (read-only), so the test and sabotage results are taken as reported.

## Must-fix

1. **"Final" is never reached after a kill** (`scripts/e2.py:342`, `:373`, `:421-424`; §10).
   - `require_earlier` treats a stopped stage as final only if `attempt1(record)` exists. A killed first attempt leaves no record, so only its marker is archived.
   - Sequence: attempt 1 killed, rerun crashes. The next stage says "rerun it once first", and `--rerun` says "has been rerun once already". Deadlock, where §10 says the stage is final.
   - If the second attempt is killed, there is no record at all and later stages say "has not run".
   - **Change:** define finality by the rerun note or either archived file, and register what a killed second attempt means (simplest: "E2: not completed (the run stopped)" in §8.4 and §10).
   - **Tests:** E2's test file has no kill-path test. `reconcile_kill` and `rerun_plan` are copies, so 04a's tests do not cover them, and "tested the same way" is not yet true.

2. **An ES batch that did not complete gets the performance wording** (`decide()`, `scripts/e2.py:218-226`; §8.2).
   - It returns "keep 02's GA (the ES did not satisfy both replacement criteria after paying for its tuning)", which reads as a measured result.
   - **Change:** add a distinct outcome, for example "keep 02's GA (the ES's batch did not complete; no comparison was made)", with a test case.

3. **A planning figure is called measured** (`PREREGISTRATION.md:292-293`).
   - "About 10 s per checkpoint" is 04a's conservative planning figure (its pre-registration, lines 328-330), not a measurement.
   - 04a measured about 3.2 s: `compute-record.json` gives 264.7 s over 82 checkpoints, and its projection 3.29 s.
   - **Change:** relabel it. The 5.0 h total stands as an upper estimate; at the measured rate it is about 4.7 h (my arithmetic).

4. **`REGISTERED["es"]` is never read** (`scripts/e2.py:97-99`).
   - The loop uses `P // 2` and `OpenAIES`'s defaults (`loops.py:178`, `optimizers.py:66-67`). The values agree today.
   - **Change:** pass them through or pin the equality in a test. Otherwise narrow the claim at `PREREGISTRATION.md:18-19`.

## Suggestions

- **Pilot ties:** if every setting totals zero at generation 199, the tie rule picks σ 0.5 and rate 0.1 σ, the setting least able to leave a plateau. Tie to σ = 1, or register that an all-tied pilot is reported as uninformative.
- **Projection headroom:** 04a's projection ran at 5.25 s per generation against 4.75 s in training. At that rate E2 projects at about 5.1 h against 5.5 h. At the limit, the cap leaves about 1.4 h, less than one GA rerun.
- **Extension:** its champion is chosen over 42 checkpoints (generation 622 included) against the GA's 41. Disclose it in §6.
- **Outcome scope:** the design promised the outcome wording would say "under unshaped fitness only". It is in §1 and §12, not in §8's sentences.
- **§8.4** does not name an evaluation that stops twice.
- **§7** should say that champions from incomplete batches are evaluated and reported.
- **§12** should say E2 compares procedures: the GA nominates a best-of-32 genome, the ES its mean.
- **Pairing:** report per-run differences (ES minus GA), and check that generation-0 checkpoint hashes match across methods.
- **Hashing:** `file_sha256` replaces CRLF bytes, so the binary state file's recorded hash will not match a plain sha256.
- **Test gaps:**
  - No test that a tie in the extension's champion goes to the formal checkpoint.
  - The id-disjointness test uses a hand-typed list, which omits 03's timing ids at 990 million.
- **README:** the experiment folder has none yet.

## Checked and found correct

- **Allowance:** 2 131 968 and 2 131 712; 623 is the largest length that fits (624 gives 2 133 760). Checkpoint counts are 41, 26, 9 and 16; the extension is 804 864 episodes.
- **ES update:** the estimator and its sign, Adam with bias correction, average ranks, and both flat rules freezing the mean, moments and counter. Projection happens only after a real update.
- **Candidates and champions:** each method's checkpoint candidate matches the text, and the champion is the first best checkpoint.
- **Resume:** runs 623-999 on the same schedule, restores the noise generator, and takes formal checkpoints first.
- **Decision:** exact fractions, "at least" for the margin and the floor, strictly above the GA's median, and the incomplete-batch branches.
- **Hash checks:** champion hashes and brain configuration are checked before the start marker and before any hold-out world.
- **§13's four departures** are acceptable, given fix 1.
- **Ids and seeds:** no file in the repository contains an id in the 995 million block. Seeds are disjoint from each other and from 04a's. The smoke run used the CPU, seeds 1 128 000+ and ids below 10 000.
- **Test counts:** 14, 15 and 46 match.

## Not checked

- The ENOMAD citations.
- Whether the sabotage checks were run.