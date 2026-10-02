**Verdict: fix then run.** HEAD is `910fc7e`; the pre-registration is unchanged from `989da99`. The runner has outcome-changing mismatches despite the completed smoke.

1. **Random-sampling champion ties are wrong.** The shortlist is ordered by selection score, then `champion_of()` breaks validation ties by shortlist position—not original draw number. For shortlist `j=[9,2]` and tied validation means, it selects 9. Break validation ties explicitly by `j`. [e3a.py:728](D:/Claude/random/wormWars/scripts/e3a.py:728), [e3a.py:793](D:/Claude/random/wormWars/scripts/e3a.py:793).

2. **Census qualifiers can change between screening and evaluation.** `checked_selectors` rounds parameters to nine decimals, then reconstructs genomes from those rounded values. I reproduced a changed float32 parameter through this round-trip. Preserve the actual screened genomes and verify their hashes. [e3a.py:532](D:/Claude/random/wormWars/scripts/e3a.py:532), [e3a.py:825](D:/Claude/random/wormWars/scripts/e3a.py:825).

3. **Calibration and test compositions violate §5.** They run one padded strain × 256, whereas the registration specifies 32 × 256. This can affect CUDA results; padding does not establish composition independence. Implement the registered composition. [e3a.py:843](D:/Claude/random/wormWars/scripts/e3a.py:843), [e3a.py:914](D:/Claude/random/wormWars/scripts/e3a.py:914).

4. **Stage guards permit premature work and mishandle failures.**
   - G0 accepts a completed-but-failed G-E; G1 accepts a failed G0.
   - Champion stages accept `"absent"`, `"killed"` and `"awaiting-rerun"` training as “not read,” allowing empty champion records to be frozen before training.
   - Earlier training records are not consistently required to be committed before the next batch.
   - After Stage 2 stops finally, Stage 3 can reach `champs[r.run]` with no champion and crash.
   
   Enforce terminal prerequisites, passing gates and publication boundaries; handle genuinely unavailable champions explicitly. [e3a.py:441](D:/Claude/random/wormWars/scripts/e3a.py:441), [e3a.py:486](D:/Claude/random/wormWars/scripts/e3a.py:486), [e3a.py:571](D:/Claude/random/wormWars/scripts/e3a.py:571), [e3a.py:647](D:/Claude/random/wormWars/scripts/e3a.py:647), [e3a.py:764](D:/Claude/random/wormWars/scripts/e3a.py:764).

5. **Projection and admission are not the registered calculation.** Final-population validation is priced as 256 episodes per champion instead of **32 × 256**. Remaining non-training work is approximated by `fixed * 0.5`; the stage argument and reduced RS count are ignored. There is no post-census recomputation, no enforcement of `plan["fits"]`, and no projected evaluation-admission check. Several timings run only once. Also, projection’s `play()` calls use **evaluation seed 1,171,000**, although their IDs are smoke IDs; the record incorrectly claims the smoke seed throughout. [e3a.py:193](D:/Claude/random/wormWars/scripts/e3a.py:193), [e3a.py:353](D:/Claude/random/wormWars/scripts/e3a.py:353), [e3a.py:366](D:/Claude/random/wormWars/scripts/e3a.py:366), [e3a.py:618](D:/Claude/random/wormWars/scripts/e3a.py:618), [e3a.py:854](D:/Claude/random/wormWars/scripts/e3a.py:854).

6. **Several readings are wrong or incomplete.**
   - Under four-pair RS reduction, S2-b checks working status only among paired GA runs. It can report “neither found” when GA run 7 is working.
   - Stage 3 omits the registered “neither found” branch.
   - B-task switches its comparator only when Stage 3 is unavailable; §8 explicitly says Stage 2 under reduction step 1. Implement that text or clarify through an amendment.
   - S2-b’s mandated comparison wording is absent. Partial zero-success S2-a wording omits “0 of n read.” Capped S2-c still emits an ordinary interval treating unchecked qualifiers as failures.
   
   [e3a.py:962](D:/Claude/random/wormWars/scripts/e3a.py:962), [e3a.py:973](D:/Claude/random/wormWars/scripts/e3a.py:973), [readings.py:78](D:/Claude/random/wormWars/wormwars/e3/readings.py:78), [readings.py:118](D:/Claude/random/wormWars/wormwars/e3/readings.py:118).

7. **Registered measurements are missing.** There are no saved q/RA/RB/u/module-contribution traces, hysteresis sweep, or training-generation offsets. The census’s first-64 diagnostic does not supply training-generation diagnostics. Successful latch champions omit release results, including the requested two-tick release report. [e3a.py:530](D:/Claude/random/wormWars/scripts/e3a.py:530), [e3a.py:653](D:/Claude/random/wormWars/scripts/e3a.py:653), [assays.py:106](D:/Claude/random/wormWars/wormwars/e3/assays.py:106).

8. **End assertions are incomplete.** No explicit unchanged-mask assertion exists; Stage 3 omits gap conductances; RS bypasses assertions. An assertion failure blocks the champion stage instead of recording the affected batch as “not read.” Add sabotage tests for these actual checks. [e3a.py:677](D:/Claude/random/wormWars/scripts/e3a.py:677), [e3a.py:767](D:/Claude/random/wormWars/scripts/e3a.py:767).

The library’s main contracts look correct on inspection: entries and goal switching, next-tick levels, cue exclusion from events, joint geometry rejection, sampler ties and mutation factors, held q/RA/RB probes, fixed-point bracketing, memory thresholds and assignments, calibration medians, and RS world pairing. The reset’s `exit_tick + 1 + 10` correctly accounts for when the **sensed level** returns to zero.

I found **no concrete regression in earlier task behaviour**, but the equivalence evidence is narrower than claimed. The foraging check reuses genomes carrying Task N’s **32-substep** brain configuration, rather than the default eight; it omits field-state hashes, an explicit foraging score, and the rollout path. Fix that coverage and rerun G-E after the implementation fixes. [e3_equivalence.py:59](D:/Claude/random/wormWars/scripts/e3_equivalence.py:59), [e3_equivalence.py:85](D:/Claude/random/wormWars/scripts/e3_equivalence.py:85).

I checked the saved smoke/equivalence records and reproduced the logical counterexamples using synthetic inputs. I did not run worlds, modify files, or rerun the full suite.