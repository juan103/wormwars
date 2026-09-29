**Revise.** The comparison design is acceptable, including §13’s departures. The remaining problems concern failure handling, outcome wording, and two incorrect exposure statements.

**Must fix**

1. **“Stopped twice” fails for hard kills.** [scripts/e2.py:342](/D:/Claude/random/wormWars/scripts/e2.py:342) requires an archived *record*. If attempt 1 was killed, only its marker is archived; a caught failure on attempt 2 therefore never becomes final. If attempt 2 is killed, there is no current record, and another `--rerun` reconciles compute but refuses without finalizing it. Recognize consumed attempts from durable rerun metadata/markers and produce a final stopped record after a killed rerun. Test kill→crash, crash→kill, and kill→kill; the existing test covers only two caught exceptions.

2. **A stopped extension silently loses its champions.** [scripts/e2.py:587](/D:/Claude/random/wormWars/scripts/e2.py:587) salvages ordinary run records, whereas `champion_over_both` is created only after successful extension training at [line 755](/D:/Claude/random/wormWars/scripts/e2.py:755). Evaluation accepts a twice-stopped extension but skips every record lacking that field. Register what an incomplete extension contributes, then implement it consistently—preferably the first best checkpoint across the formal run and completed extension checkpoints, explicitly labelled incomplete. Test stopping before and after the first extension checkpoint.

3. **Hold-out arms are not durable across a kill.** [scripts/e2.py:819](/D:/Claude/random/wormWars/scripts/e2.py:819) keeps counts in memory; the arm loops never write a partial record. A hard kill loses every completed arm, contrary to §10’s preservation promise. Write an atomic partial record after each completed arm and preserve it with the attempt. The inherited 04a runner does this.

4. **Complete §8’s terminal outcomes.** [PREREGISTRATION.md §8](/D:/Claude/random/wormWars/experiments/E2-optimizer-screen/PREREGISTRATION.md:227):
   - An over-limit projection finishes with `"completed"` and `within_limit=False`; subsequent refusal has no specified experiment outcome. Add explicit “not started: projection exceeds limit” wording.
   - An incomplete ES can have champions satisfying both numerical thresholds yet be ineligible. Give that case “keep GA: ES did not complete,” rather than attributing it to failing the two thresholds.
   - State how a final incomplete extension affects the experiment outcome, and distinguish terminal outcomes from a first stopped attempt awaiting its mandatory rerun.

5. **Correct §11’s exposure account.** The local [smoke projection record](/D:/Claude/random/wormWars/runs/e2-smoke/projection.json:318) used **1,129,000–1,129,002**, E2’s projection seeds. `use_smoke()` changes projection length but not its seed. Disclose this; give smoke projections a separate seed group going forward. Also, “every score 0” is false: [smoke controls](/D:/Claude/random/wormWars/runs/e2-smoke/evaluation.json:408) include oracle and S-const means of **0.8125**. Narrow that statement to neural scores. I found no formal/pilot seed or reserved-world exposure in the inspected records.

**Suggestions**

- Update `ESRecord.flat_generations` during execution: [loops.py:232](/D:/Claude/random/wormWars/wormwars/e2/loops.py:232) assigns it only on successful return, so stopped records can report zero despite logged flat generations.
- Label the budget’s 10-second checkpoint allowance as conservative. From 04a’s training records, non-checkpoint medians are **4.741/4.716 seconds**, with approximately **3.34/3.29 seconds** of checkpoint excess. About five hours is plausible; the measured E2 projection remains necessary.

**Checked and correct**

- Design v2.2 is carried faithfully. Paired starts, paired pilot settings, proceeding after final training failures, and requiring an amendment after an excessive projection are acceptable choices.
- Allowance: **2,131,968** GA/random versus **2,131,712** ES; checkpoint counts **41/26/9/16** and the **804,864-episode** extension are correct.
- ES encoding, antithetic ordering, average-rank utilities, ascent estimator, Adam, both flat rules, and projection only after an update match the text.
- Candidate rules and earliest-best champion selection match. Successful extension resume restores the required state and selects across both parts.
- `decide()` correctly uses exact fractions, inclusive margins, strict comparison with GA’s median, and the registered floor rule.
- State hashes and all selected champion hashes/configurations are checked before hold-out simulation. Reserved ID ranges are disjoint from the earlier ranges inspected.

I inspected files only; I ran no commands or tests. The claimed fail-before-pass and sabotage history is documented, but I did not independently verify its execution.