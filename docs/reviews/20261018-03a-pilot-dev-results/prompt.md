You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing research results in the repository you can read (read-only): **03a's pilot-dev results**, at
commit 374f88c on branch `roadmap` (DECISIONS.md D312). This is a results review, not a code review.

## Context

- 03a's design is `experiments/03a-self-consistency/DESIGN.md` v7.1, agreed by both of you (D307). Pilot-dev's plan
  and its fixed reading rules are in `experiments/03a-self-consistency/PILOT-DEV.md` v3.1, which you reviewed over
  three code rounds (`docs/reviews/20261017-03a-code/`, `docs/reviews/20261018-03a-code-r2/`,
  `docs/reviews/20261018-03a-code-r3/`).
- Pilot-dev ran all its stages on one SH-mirror null graph (seed 3 403 000), not N2, on commits 1b0531a and f27d4c4.
  It used 4.58 of its 6 GPU-hours. 03a has 66.9 of its 72 hours left.
- The records are in `experiments/03a-self-consistency/pilot-dev/`: `setup`, `evolve-intact`, `panel`,
  `evolve-nip`, `baseline`, `probe`, `tune`, `full` and `report` (`.json`), and `compute.json`. D312 summarises
  them. Check D312's numbers against the records, not the other way round.

## What D312 reports (claims to check)

- **`tune`:** round A flagged that no ladder had every neighbour pair inside the 20-40% swap band. The mean rates were
  0.79, 0.88 and 0.95, and the rule kept (0.1, 0.2, 0.4, 0.8). Rounds B and C kept their first settings, with every
  alternative within 0.011.
- **Resolution:** p = 0.098, δ_eval = 0.021, δ_search = 0.042 (0.43 p).
- **Target-brains** (MIP and NIP × URXL and PLNL):
  - every enrichment p is 0.12 or above;
  - functional success is "reached" in all four;
  - MIP/URXL is excluded, because its refits are below exact restoration by 0.132;
  - the outcome of the other three is "functional success, anatomy undetermined".
- **Free searches:**
  - Q stays inside the chance range throughout;
  - AUC is 0.47-0.55;
  - turnover is mostly 0.9-1.0 per 10-generation window;
  - Jaccard agreement is near the independent-random expectation.
- **Offspring minus current, on the same worlds:**
  - on MIP/URXL, mean −0.14 to −0.20 with SD 0.32-0.42;
  - on PLNL, mean −0.01 to −0.04.
- **The longer searches** gain no AUC from 100 to 200 generations, so PILOT-DEV §3's fixed reading applies: "the
  budget stays".
- **Report:** the formal design projects 43.8 GPU-hours with no cut.

**A fact D312 does not mention:** PLNL was a high-relevance target on the selector brain (`panel.json`), but its
deletion deficit in the MIP brain is 0.013, far below p (`baseline.json`).

## What we need from you

1. **Check the results.** Are D312's numbers and readings right against the records? Is anything overstated,
   understated or missing? Give file and field for each error.
2. **Read the results.**
   - Is pilot-dev's search informative about partner identity at all, at this evaluation size (16 worlds per
     state), temperature ladder and budget?
   - What do the swap rates, the turnover, the paired differences and the 0.12 original-partner advantage on
     MIP/URXL say about why Q stays at chance?
   - Be specific about what these records can and cannot establish: one graph, two targets, a shuffled graph
     (DESIGN §8 notes that nothing task-shaped links X to its "true" partners on a shuffled graph, except through MIP
     training).
3. **Diagnostic thresholds for pilot-check's criterion 6** (DESIGN §8; PILOT-DEV §3, "After pilot-dev"). The
   pre-registration must fix acceptance thresholds for turnover, ranking agreement and the longer search's gain from
   these numbers. It must also say how criterion 6 applies to pilot-check's low target, and how δ_search is extracted
   from pilot-check.
   - **Claim to attack** (Claude's draft, not a conclusion): require, on the high targets, final-window turnover at
     most 0.5 in at least half of the free searches, and mean pairwise Jaccard above the independent expectation for
     at least one type. Report the longer-search gain, but don't gate on it. Pilot-dev itself would fail this
     criterion.
   - Propose your own thresholds, or argue that criterion 6 should be something else.
4. **The direction question,** for the owner, who decides it after this review. Given pilot-dev, is spending
   pilot-check (about 10 GPU-hours) and then possibly the formal run (about 44) still the right use of 03a's budget?
   Consider at least:
   - (a) proceed to the pre-registration and pilot-check as designed, accepting a likely registered "pilot failed"
     (criteria 5 and 6), which DESIGN §8 says is reported;
   - (b) amend the search first, then re-check within pilot-dev's remaining 1.4 hours or a new, separately capped
     check. Name the changes, and what evidence in these records supports them: for example, more worlds per
     evaluation, a colder or narrower ladder, fewer offspring, or a different acceptance rule;
   - (c) stop 03a here and report pilot-dev as an exploratory result.
   Say which you recommend and why. Say what result from (a) or (b) would change your mind. Under the design's rules,
   anything chosen after seeing pilot-dev is labelled as such; say where that matters.
5. Anything else that would mislead the pre-registration or waste budget.

Answer with a verdict first: "the results and D312 stand" (possibly with small corrections), or "revise D312". Then
give your recommendation on point 4 in one line. Then numbered findings with file and field or line, and severity.
Do not edit files or run anything.
