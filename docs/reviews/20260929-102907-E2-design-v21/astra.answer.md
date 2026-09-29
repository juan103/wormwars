**Most points are met, but the allowance and generation counting still need a narrow correction.** I read the files on `roadmap`; I ran no code or tests.

- **ES update: met.** The normalization, ascent sign, Adam constants and bias correction match the design. The early return freezes the mean, moments and step counter. The [new test](/D:/Claude/random/wormWars/tests/test_e2_optimizers.py:131) exercises a flat batch after five non-flat updates and checks all four. I verified its contents, not the reported test or sabotage results.
- **Decision structure: met.** Only ES can replace GA; incomplete GA blocks the decision; the random-floor inequality includes random sampling beating GA, and diagnosis takes precedence over E3. The [roadmap amendment](/D:/Claude/random/wormWars/ROADMAP.md:167) is present.
- **Extension separation: met.** Constant hyperparameters, locking the eligible champion first, and a separately budgeted descriptive continuation satisfy my earlier conditions.

The remaining corrections are:

1. **Make generation labels consistent with the arithmetic.** The [allowance calculation](/D:/Claude/random/wormWars/docs/E2/DESIGN.md:121) correctly gives **622 updates after the formal start screen**, leaving **256 episodes unused across the method**. But it charges each pilot for 200 total generations while [selecting at generation 200](/D:/Claude/random/wormWars/docs/E2/DESIGN.md:110). With generation 0 charged, that endpoint requires 201 generations. Likewise, extending “to generation 1,000” gives 1,001 evaluations, whereas the inherited GA evaluates 0–999. State explicit ranges: pilot **0–199**, formal ES **0–622**, and equal-length extension **0–999**, if those are intended.

2. **Close the accounting definition.** “Episodes whose scores drive selection” includes checkpoint validations: they select champions. Excluding those as overhead does not establish the [roadmap’s equal-total-work requirement](/D:/Claude/random/wormWars/ROADMAP.md:161).

   This can apparently be fixed **without changing 622**. Assuming the pilot follows the common checkpoint schedule, each pilot has nine validations. Training plus checkpoint validation then totals:
   
   - GA/random: **2,131,968 episodes per method**.
   - ES, including all pilot work: **2,131,712 episodes**, with the same **256-episode rounding remainder**.

   Explicitly state that schedule and accounting, with common final evaluations and shared controls identified separately. Alternatively, amend the claim to a narrower training-and-tuning allowance.

Also correct the [“keep the GA” wording](/D:/Claude/random/wormWars/docs/E2/DESIGN.md:160): ES can exceed GA by 0.5 yet fail the six-of-eight condition. Say **“ES did not satisfy both replacement criteria after paying for tuning.”**

These are specification corrections, not a request to redesign the experiment. I found no other new blocker within this confirmation’s scope.

**E2 design: revise**