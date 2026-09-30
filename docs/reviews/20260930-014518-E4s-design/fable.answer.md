# Verdict: **revise**

The idea is testable and the controls are mostly the right ones, but Stage A cannot run as written, and the Stage B outcomes are biased toward "kept". I ran nothing; everything below is from reading code and records.

## Must-fix

1. **Stage A, background: the wey cannot move.** The module drives only the turn neurons. With the 302 neurons silent, the forward command is 0 (`world.py:742-752`), so the score is about 0.
   - Add a registered forward drive, for example a bias on AVB/PVC, and put it in the tuning grid.
   - Fix the turn neurons' τ in Stage A.
2. **Stage A, add a generation-0 graft measurement.** Measure M2 and the inert module on about 256 random N2 backgrounds and on 04a run 2. Two things make Stage A unrepresentative of B1's start:
   - Random backgrounds move at about 0.2 of full speed (config.py's D014 note; E1's generation 0: mean 0.031, best 0.69).
   - Their turn-neuron τ is log-uniform over 0.5-20 ticks (`brain.py:235-237`), which puts a lag inside a high-gain loop.
3. **Stage B, outcomes: the champion rule hides erosion.** E2's champion is the best validation checkpoint, generation 0 included (`e04a/evolve.py:98-100`). Read the outcomes on the final generation's best, with the champion beside it.
4. **Stage B, outcomes 1 and 2:**
   - They can both be true: B1 3.0 against B3 2.2 passes "kept" after falling from 8.
   - +0.5 is nearly guaranteed by the gate plus elitism.
   - Generation 0's lesion cost is capped by locomotion, so "half of it" is almost unreachable.
   - Use retention against Stage A's benchmark or the peak lesion cost, with exclusive classes: kept, partly eroded, eroded, not read.
5. **Engine: the GA loop is not covered.** `evolve_batch` hard-wires `initial_population` and `breed` (`e04a/evolve.py:122,170`), and `Genome.mutate` takes scalar sigmas (`brain.py:257-273`). A seeded start and 0.25× scales need a change or a copy. Declare it, with two checks:
   - a per-parameter σ vector of ones reproduces `mutate` bit for bit;
   - default hooks reproduce E2's generation 0-25 hashes.
6. **Engine: "02's initialisation".** On an extended spec, `Genome.random` normalises by the mean over all edges and draws different shapes (`brain.py:214-219,228`). Draw on N2's spec, then embed. B4 needs the same, because `load_genome` refuses another label or edge hash (`genomes.py:191-201`).
7. **B3, "inert" is undefined.** Zero-weight edges left in the mask regrow in one generation. Keep B1's spec and pin the 16 fan-out weights at σ = 0, so B1 and B3 draw identical noise. Log mutation counts along each lineage, since elitism makes B3's drift an inexact null.
8. **Gate, gain ≥ 32.** The probe's slope cannot exceed 66.7 on its δ grid (`e4s_gain_probe.py:35,93`), so k = 256 and k = 8192 read the same. It also starts from a zero state, so it cannot see a bistable module latching.
   - Use a small-signal grid, per common level.
   - Add a reversal test with the state carried over.
9. **Text that contradicts E2d's corrections.**
   - "All sit near 2.2": only 35 of 47 are in the band.
   - "By the temporal route": not measured.
   - "Supports the gain hypothesis" (also D139): low gain is what non-stereo looks like under either reading, so it is consistent with the hypothesis, not evidence for it.
10. **Engine, "exactly on the CPU".** I expect this can fail for a benign reason: BLAS blocking can depend on matrix size. Declare now a short-horizon tolerance and a score-level check. CUDA exactness at n = 332 is untested (rule 6).
11. **Rule 1: the hygiene guard would pass E4s files silently.** It keys on 302 and known labels (`test_publication_hygiene.py:104-105,124-126,243-246`). Generation-0 candidates carry anatomical magnitudes. Extend it before any E4s genome is committed.
12. **Noses: "unchanged" against a tuned nose gain.** An interface gain is not evolvable and the worm does not get it. Use 1.0, or disclose it as part of the module.

## Suggestions

- **Runs:** 16 for B1 and B3, read as 12 of 16; 8 for B2 and B4, descriptive only.
- **Mutation:** keep 0.25× in the main arm and add one 8-run arm at 02's scale, because the scale sets the erosion rate by construction. A frozen-module arm would make outcome 3 attributable.
- **M1:** Stage A only.
- **`hold`:** not an arm now. Register the refresh interval and run S-const under it first; it has never run on Task N.
- **B4:** one background, so a case study. State that the population is 32 copies.
- **Turn copy:** it copies T_L/T_R, not the executed turn, so they differ on any non-silent background.
- **Tuning:** four parameters is too few. Tune open-loop first, then a registered search that includes ring gain across the bifurcation.
- **Gain against topology:** optimise N2's open-loop gain by gradient, within bounds.
- **Budget:** the 24-hour cap is sensible. Cost scales nearer n², about 21%, not 10%.
- **Biology:** stated honestly. Carry the report's † caveats; I did not verify its citations.
- **E3:** say which artefact it takes.

## Checked and correct

- Only `load_connectome` checks for 302 (`loader.py:124`); the brain, world and interface are size-generic.
- Module-only probes work as interface variants, since duplicate entries sum (`world.py:734-738`).
- The report's L − R table, re-derived by hand, matches.
- E1's gain curve, M-avg 2.20, the probe's 0.098 and 0.68, and the 1.35 h GA time match the records.