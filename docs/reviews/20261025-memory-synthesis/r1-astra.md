**Verdict: fix then publish.** The main numbers and formal outcome labels are correct. Several qualifications already established in the step reviews have been lost in this synthesis. These require wording corrections, not new experiments.

Ranked findings:

1. **High — M2 again turns class attribution into a statement about individual genomes and mechanisms.** At [line 103](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:103), “each keeps about its whole start difference” is false. The **amplitude-weighted class averages** are 0.98 and 1.02; individual switch genomes range from approximately **0.27 to 1.69**. Moreover, the split assigns each genome’s *entire* tick-30 signal—including its transient component—to its class. It does not separate persistent from transient signal. Both qualifications are explicit in [M2-CENSUS-RESULTS](/D:/Claude/random/wormWars/docs/memory/M2-CENSUS-RESULTS.md:153) and were Astra findings in D356.

   Replace “each” with “the class, in aggregate,” and restore the split-by-genome caveat. Also change [line 22](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:22): the remainder is **mostly** fading, not entirely fading. At seed 7600, unresolved genomes account for approximately **8.7% of the lead**.

2. **High — Restore M4d’s restricted exclusion wording.** At [line 143](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:143), the counted-genome result “rules out a wiring advantage of 0.004 or more” drops a substantive restriction: **“as a mean across these ten hosts (a response confined to a minority of host graphs may be missed).”** This was deliberately required after the coverage checks and explicitly restored in the M4d review. Keep it here too.

   “No assignment could make the reading positive” is correct, but means the **decision rule cannot pass on these assignments**, not that a true effect above the margin is excluded.

3. **Medium — The exact M1 decomposition is labelled with the wrong population.** [Line 72](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:72) says the “registered share” splits into the reported mean and covariance term. Those quantities describe the **eligible-genome share**. In [accounting.json](/D:/Claude/random/wormWars/runs/memory-m1/accounting.json:3), the registered all-genome share is **0.43616054**, while the eligible share is **0.43451035 = 0.58615457 − 0.15164422**.

   Say “the eligible-genome version of the registered share.” Explain eligibility briefly; otherwise the outside reader cannot understand the population change.

4. **Medium — The cross-step interpretation needs narrower causal wording and one substantial open question.** The interpretation labels are clear, and prioritising a study of block properties is fair. However, [lines 172–177](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:172) should say **T−R is small on counted classifications**, and replace “more than their weight explains” with “more erasure than the three controls matched on summed anatomical weight.”

   M4c does not exhaust weight-distribution explanations or match removal of one core neuron’s connections. M4d changes block properties together; it does not isolate density, total weight, degrees or autapses as causes. Retain those limits beside the interpretation.

   Add an explicit open question: **why N2’s fading class retains more at tick 30 remains unexplained.** The later focus on switches does not complete the explanation of the original Q-D advantage, and M4d measures switch incidence rather than recovery of that retention advantage.

5. **Medium — Two M4d descriptions overgeneralise.** At [lines 146–148](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:146):

   - “Never settle” should be **“did not settle within the observed horizon.”**
   - “The genomes that switch differ almost completely between arms” needs named comparisons. T–P, T–R and R–Rr each share one switch genome; **T and T+G share 25**, so the blanket statement is wrong. [Source](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:185)

   Also clarify at line 136 that **2347 is the weight of the 260 off-diagonal edges**, with eight autapses additional.

6. **Medium — The page conflates two different head cores.** [Batch 7’s paragraph](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:107) describes its frozen core, then introduces C3 without explaining the distinction. Batch 7 uses the result-selected `top30_start`; C3 is anatomy-defined. They share **18 of 30 neurons**, and the Batch 7 localisation result is partly conditioned on how its core was selected. [M3-NOTE](/D:/Claude/random/wormWars/docs/memory/M3-NOTE.md:15)

   Name both sets explicitly. This matters to the argument, not just terminology.

7. **Medium — Correct the review/provenance narrative.** [Lines 45–51](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:45) overstate a uniform process of review “until both agreed.” Several final archived answers remained “revise” or “fix then publish,” with fixes subsequently incorporated—M4a’s plan, M4b’s plan and M4d’s results provide examples. M3 was also a closure of existing analyses plus a descriptive table, not another separately planned simulation.

   Say that both reviewed the plans/results and their requested fixes were incorporated. Expand the M4c exception to include the material provenance limitation: **the census executed an unarchived working-tree version of `m4c.py`**. Starting during review is only part of that disclosure. [Source](/D:/Claude/random/wormWars/docs/memory/M4C-RESULTS.md:36)

8. **Medium — Two entries in “Lessons” are wrong or unsupported.** At [line 214](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:214), the corrected M4a claim was “most of the **intact separation**,” actually **33% and 34%**. The **54% and 58%** figures concern its contribution to C3’s loss and do exceed half. The synthesis currently misreports its own correction.

   I could not substantiate the **8.5-hour detached-waiter** statement in D364 or the cited results/reviews. D364 does not record it. Remove it or supply a committed source; it adds little to this scientific synthesis.

9. **Medium — Attribution is broadly supported, but omits important contributions and blurs delegation.** The decomposition, persistence–alignment split, M4d independent reruns and null-boundary correction are correctly attributed to Astra. Fable’s anatomy predictor, dissection proposal, amplitude objection and nonsettling observation are also supported.

   I would make these specific changes:

   - Credit **Astra’s midpoint amplitude-scaling design**, with Fable pressing the objection; the roadmap already distinguishes these.
   - Credit **Astra’s addition of M4c’s count-and-total-weight-matched core control family C**, and **M4d’s conservative corner-envelope correction**. These were substantive design corrections, beyond “provenance and reporting catches.” [M4c review](/D:/Claude/random/wormWars/docs/reviews/20261023-m4c-plan/r1.astra.md:3), [M4d review](/D:/Claude/random/wormWars/docs/reviews/20261024-m4d-plan/r2.astra.md:3)
   - Acknowledge both reviewers’ classifier work in M2; that major part of the thread is absent from the attribution.
   - Mention the owner-supplied **ChatGPT roadmap**, and describe the owner as setting direction and delegating choices. D363 says M4d was chosen by consensus **under that delegation**, not personally selected by the owner.

10. **Lower — Add a short reader’s introduction and correct the blanket assay description.** Define N2, a random genome, the history difference, a tick, eligibility and the turn read-out. Define T/I/R when first used. “Ceremony,” “cheap kills” and “Batch 7” currently require project knowledge.

    [“Every result … read at the turn read-out”](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:181) is inaccurate: M4a’s primary endpoint uses full-state separation, while the classifier and M4d include read-out-silent separate states. Likewise, “two states only” should mean **two states reached from the nine tested starts in the pilot**, not an exhaustive bound. Describe M5 as a **planned confirmatory transplant requiring pre-registration**, rather than implying registration already exists.

On the **summary script**, I found no incorrect field mapping or arithmetic in the current outputs. The compute records sum to **56.351422 hours**, correctly rounded to **56.4**, and **27,853,691,776 neural updates**. The quoted M1, M2 and M4 headline values and reading strings match their sources. Label the hours as **recorded wall-clock hours on CPU**.

The tests check builder/snapshot consistency and include a meaningful changed-record sabotage; they do not validate the prose or independently establish that the selected fields are the right estimands. I inspected them but could not rerun them: `python` was inaccessible and `py` reported no installed interpreter. No files were modified.