**Verdict: revise.** The main design is preserved, but missing-data handling, budget cuts and assay inputs need another pre-registration pass.

The complete-data gate is correct: the equally weighted schedule mean, SE divided by two, and mirrored one-sided 5% labels match the confirmed design. S-gen’s paired test and S-trail/S-peer’s stratified tests have the right directions. The evaluation roster supplies the required conditions. The champion indexing agrees with [`evolve_batch`](/D:/Claude/random/wormWars/wormwars/e04a/evolve.py:165): final populations are evaluated at 124/299; T-F needs the proposed snapshot before breeding.

**All nine hashes match** literal `git show HEAD:<path> | sha256sum`, at HEAD `95800aa`.

Required fixes:

1. **Make the statistics work with missing runs.** [§7](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md:184) permits remaining-run analysis but hardcodes eight in the SE. Define actual sample sizes:
   \[
   v_j=s_j^2/n_j,\quad SE=\sqrt{v_A+v_F}/2,\quad
   \nu=\frac{(v_A+v_F)^2}{v_A^2/(n_A-1)+v_F^2/(n_F-1)}.
   \]
   Retain equal schedule weights. Specify the spread calculation, sensitivity tests with fewer than 16 observations, zero-variance handling, and interval confidence levels. Explicitly resolve whether the repeated-journey threshold remains eight when champions are missing.

2. **Resolve run failure versus stage failure.** [§5](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md:132) grants a stage retry; the confirmed pin grants a run retry. Currently, [`evolve_batch`](/D:/Claude/random/wormWars/wormwars/e04a/evolve.py:147) raises for the entire batch on any non-finite score and assigns final populations only after successful completion. Specify how healthy runs finish after another fails, batch composition during retries, and which saved reads survive. Replace discretionary “may be rerun” with a deterministic rule, subject to the cap.

3. **Define “not read” separately for each reading.** A failed replay or component assay must not discard an otherwise complete shared-trail gate observation. Specify required conditions: shared for G; paired final/124 shared for S-gen; shared/none for S-trail; shared/own for S-peer. Require complete 256-maze panels and a fixed evaluation order if partial stages can contribute. The shrinking Holm family is an unlisted departure from the confirmed three-test family; retain three hypotheses, assigning unread tests p = 1 for adjustment.

4. **Propagate the 250-generation cut.** [§9](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md:262) cuts T-F to 250, but its final read, roster, gate and S-gen still require index 299. Define the final index as `G_F − 1`, including index 249 and corresponding outcome wording.

   Admission also applies ×1.25 to **non-training** work, contrary to confirmed pin 11. Define uninflated projections and where each reserve applies. Register evaluation chunk composition and projection arithmetic, including checkpoint overhead, assays and reduced N’s composition. Explicitly require G-E to **pass** before training; the cited GPU script records mismatches without itself exiting unsuccessfully.

5. **Pin champion-validation access.** [§6](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md:147) specifies scores and ties but omits trail access. Specify shared for T/R and none for N. Selecting N under shared trails would introduce selection on its otherwise unsensed trail response.

6. **Finish the assay specification and records.** [§7’s descriptive readings](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md:237) promise component tests and E3a memory classification without specifying their producing stage, stimulus duration, state-to-goal assignment or handling of non-bistable champions. [`memory_assays`](/D:/Claude/random/wormWars/wormwars/e3/assays.py:78) requires both stimulus and assignment; D = 141 alone is insufficient. E3a’s full classification also requires release assays for non-bistable organisms. Specify calibration/recording or an explicit simpler protocol. Ordinary maze event records do not contain E3a’s stimulus-duration calibration data.

7. **Pin undefined denominators and restore the omitted power qualification.** Specify zero donor exposure handling—currently E3b-0’s coefficient helper returns NaN—and undefined seed/baseline normalizations. Make S-peer’s denominator explicitly the seed’s mean first-B time under **own** access. Carry confirmed pin 1’s distinction between SD in seed units and CV at the tuned mean; merely hashing `power.json` does not carry that qualification. Also correct §12: the oracle and random walk already appear in the confirmed roster.

The budget mostly checks: training is **15.0741 h**, or **18.8426 h** with reserve; champion validation is **1.2059 h**. However, generation-zero checkpoints give **200**, not 176, checkpoint evaluations: **0.2355 h**, not 0.21. My previous review’s 0.207-hour figure was wrong. With the other allowances unchanged, totals are **17.5156 h** and **21.2841 h**, so “about 17.5” and “21.3” remain correct. Assay costs still need explicit inclusion.