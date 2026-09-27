# Review of 03r results: not yet

The registered verdicts are computed correctly and the fixed wording is used correctly. What blocks publication is one missing caveat on P3, the README sentence that does not exist yet, and stale text.

I checked every number in RESULTS.md against `report.json` and `supplement.json`. I could not check the raw measurements, the 23.95 GPU-hours, the per-measurement provenance, the N2-last order, or that the two reports are identical.

## 1. Numbers

Everything matches except three rounding errors (minor, below). That covers the P4 gate table, the 03-beside-03r table, P1 and P3 values, counts and Holm p-values, the variants' P4 values and ranks, the decomposition table, the forward read-out counts and the other secondaries.

## 2. Verdict fidelity

- **Primary:** maximum p is 0.0155, and all five rank and margin gates pass.
- **03's rule:** P4 Holm is 3 × 2/129 = 0.0465, distinctive.
- **Outcome row:** row 1 is the right one, and its wording is quoted verbatim in both RESULTS files.
- **P3 "reversed":** this is what §6 yields. Opposite-direction Holm is 0.0465, and every effect interval is beyond its margin.

## Must fix

**1. P3 "reversed" lacks the caveat that matters most: N2's P3 measurement is much noisier than the ensemble graphs'.**
- **The noise:** N2's P3 SE is 0.0120. Only 3 of the 768 ensemble graphs have a larger one, and about 80% are below 0.008.
- **Why it matters:** the rank test assumes N2's measured value is exchangeable with the ensembles'. A noisier measurement lands in the tails more often at the same latent value, so the rank p is too small here.
- **How strong the evidence is:** N2 is −0.024 with SE 0.012, about 2.0 SE from zero. My own noise-aware calculation gives a one-sided p of about 0.025, and about 0.07-0.09 after Holm across three signals. That is exploratory and should be labelled so.
- **The only noise-aware gate** is the 90% effect interval, which is a one-sided 5% test with no multiplicity correction. It passed narrowly, with upper ends of −0.003 to −0.005.
- **What to change:**
  - Keep the registered label, and add the SE comparison and the "2 SE" statement beside it.
  - Reword "score slightly worse" as an estimate.
  - In 03's pointer, replace "(N2 below every ensemble)" with the counts.
  - Add the variants' P3 to the table: N2perm4-6 are −0.002, −0.002 and +0.005, and N2-rev is −0.0001. None shares the negative value.
- **P4 is not affected:** N2's P4 SE is ordinary and the effect is more than 10 SE.

**2. The README sentence §10 requires does not exist.**
- RESULTS.md says "the README says a full replication was run before 03 was merged into main". At HEAD the README has only the branch banner, which still says 03r "is running".
- Before main it needs the fixed outcome wording, the probe caveat verbatim, the D063-amended sentence with the reason, and the four contributions from D059.
- If the README mentions P3, it needs the caveat from item 1.

**3. 03's RESULTS.md still says 03r is "pre-registered … and running"** (line 332), under a banner that says it replicated.

## Should fix

**4. The provenance claim is stronger than its evidence.**
- `scripts/exp03.py` computes provenance once at the start of the run and stamps it on every file. So "every measurement records `7c146fc` with `code_dirty: false`" describes the start, not each measurement.
- The run was launched from the main directory, where code was edited and committed during the run, including `scripts/exp03.py` itself (D069).
- I believe the loaded code was unaffected: the measurement path uses no worker processes, and its lazy imports fire on the first graph. That is an argument, not a check.
- **Recommended:** re-measure N2 and one late ensemble graph from the binding worktree and compare bit for bit, as 03 did. Also confirm that the input files read per graph (`remaps.json`, `graphs_manifest.json`) still hash to the recorded values.
- DISCLOSURE.md's "code and configs are unchanged since" is no longer true of HEAD. Add a dated addendum.

**5. §10 asks for both runs under both rules.** Add a small table: 03 gives 0.0155 and 0.0465, and 03r gives 0.0155 and 0.0465. Say the identical values are a coincidence of discreteness: one SH-route graph in 03, one SH-class graph in 03r.

**6. State the one-graph margin under 03's rule in the summary.** One more SH-class graph at or above N2 would have given 0.070 and outcome row 2. That was the reason for the replication.

**7. Say that the single-signal primary was chosen after seeing 03's data, on Fable's argument** (D060, prereg §1). Both rules pass, but it belongs in the contributions paragraph.

**8. `supplement.json` records no provenance.** State which commit's code produced it.

## Minor

- **Rounding:**
  - 03's SH-recip lower bound is +0.158 (0.15850), not +0.159. 03's own RESULTS has +0.158.
  - N2's calibration deviation is 2.7% (0.02749), not 2.8%.
  - N2perm5's common mode is 0.007 (0.00745), not 0.008.
- **"Roughly 2.6%"** divides by 0.9, which matches T0's mean (0.91). P3 is a T1 score, which the 03 pre-registration puts at about 0.89. Name the denominator.
- **P1 "same label":** true of the overall label only. SH went from consistent to inconclusive, and N2 moved from +0.004 to −0.013.
- **"Final checks by Astra 6 and Fable 5.1":** the two final checks were Astra's alone. Fable's last pass was the recheck.
- **Run facts:** say whether 23.95 hours includes N2 and its variants, since the cap covers ensemble graphs only, and whether the run was ever resumed.
- **Omitted secondaries:** the absolute directional response and P1 by condition are in `report.json` but not in RESULTS.md, unlike in 03.

## 3 and 4. Overclaiming and disclosures

- **P4** is presented with appropriate caution. The "what this is and is not" block is accurate.
- **P3** is correctly framed as unpredicted and secondary, but it is overclaimed by omission (item 1).
- **Deviations** are accurate as far as they go, and incomplete on the code edits during the run (item 4).

**03r results: not yet.**