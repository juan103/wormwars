**Verdict: revise.** The three parts are the right ones and most of Part A checks out, but Part C's comparison cannot carry its readings as designed, and two readings claim more than the probes measure. I could not execute code; everything I recomputed was by hand from the JSON.

## Must-fix

1. **Part C: the reference is unpaired.** New seeds compared with E2's eight runs let seed luck meet the 0.3 rule. 04a's unshaped runs (same GA, same task) average 2.37 against E2's GA at 1.96, a gap of 0.40 with nothing changed. Do one of these, and say whether the arms share seeds:
   - reuse E2's run seeds (1 120 000-7) and its training and validation ids, and report paired differences per run (mean, median, runs improved of 8);
   - keep new seeds and add unchanged GA and ES control arms (about 2.2 h more; the cap must rise).

2. **Part C: C3 changes two things.** Halving σ also halves the learning rate (0.15 to 0.075). E2's ES was still rising at generation 622, so C3 can lose on speed alone. Keep the rate at 0.15, or declare a two-change arm whose null does not clear σ.

3. **Part C: C1's checkpoint gap can be fixed, not only disclosed.** E2 saved every checkpoint candidate.
   - Re-choose E2's GA champion among 11 checkpoints as C1's matched reference.
   - Add a second reference cut at generation 250.
   - My rough estimate is that best-of-41 against best-of-11 is worth about 0.1.

4. **Part A: corrections.**
   - "All eight of the ES's" within a quarter target of M-avg is seven: ES run 7 is 1.931, which is 0.269 below 2.199.
   - "Where most candidates sit" contradicts the next bullet (population mean 0.54, 24% zeros).
   - The plateau bullet omits that six of the eight extension champions are above M-avg, one at 2.91. M-avg is a reference level, not a ceiling.
   - Say how tied k-world means were scored. At k = 8 I estimate about one resample in seven ties.
   - No script or output file for these numbers is committed (rule 5).

5. **Part B: the reading's name and cases.** `mean` and `swapped` show whether a champion uses the left-right difference, not that its strategy is temporal.
   - Call it a "non-stereo plateau", or add the existing `hold` probe with M-avg and K as references.
   - Fix the reading for 3 or more qualifying champions, and add a middle class between "uses" and "does not".
   - Define "near M-avg's level".
   - Count per set, not of 48: ES run 6 and extension run 6 are the same genome.

6. **Part C's champions get `real` and `mean` only,** but the rule needs `swapped`. Add it.

7. **Decision guidance.**
   - Budget has no reading, though the roadmap's rule names it. State one from the extension records.
   - "The optimizer is not the bottleneck" is too strong for three single changes. Gentler mutation makes smaller differences, which need more worlds, so both single arms could fail where the pair works.
   - A gain of 0.3 is improvement within the plateau, not leaving it. Part B's rule on the arms' champions can define leaving.
   - Add a reading for an arm 0.3 worse, and say C3 cannot overturn E2's registered outcome.

## Suggestions

- **Arms:** add C4, 32 worlds with halved mutation for 250 generations (about 1.35 h). If the cap stays at 5 h, drop C3 before C4, because E3's optimizer is the GA. I would not add more worlds for the ES or a budget arm: the extension already is one.
- **A cheap operator probe (about 20 GPU-minutes):** for each GA champion, 64 children at mutation scales 1, 0.5 and 0.25, each on 256 worlds. This gives ranking accuracy among relatives, which is the fair model of selection. Champion pairs from different runs are not.
- **Ranking table:** say that it does not describe the ES, which averages over the population and through Adam. Its "truth" is also a 1 024-world mean from the same worlds.
- **Part A per run:** pooled figures hide two regimes. In the stretches I sampled, run 0 had a population mean near 0.58 with 24% zeros, and run 2 near 0.48 with 8% zeros.
- **Winner's curse:** the two figures are not comparable (best of 800 against best of 32). Runs 2 and 6 lift the GA's 0.85 correlation.
- **Part B checks:**
  - M-avg under `swapped` should match on all 1 024 worlds. Under `mean` it should match only in aggregate, because its frozen `fall_threshold` is 0.0 and last-bit rounding can flip a comparison.
  - Add the k = 4 stereo steerer as a calibration reference.
  - Say what happens if a check fails.
- **Report individually:** 04a's run 2 (E3's module), extension run 3 and 04a's run 12.
- **Runner:**
  - add a timing projection for C1's 8 192-world rollout;
  - add E2's 995 million block to the id-range test;
  - test `mean` and `swapped` on Task N;
  - report per-run tables beside the 8-run bootstrap.

## Checked and found correct

- **Pair counts:** 80, 122 and 110, recomputed from the 32 hold-out means.
- **Ranking table:** consistent with a normal approximation at a paired per-world SD near 0.95; the bootstrap itself was not recomputed.
- **Standard errors:** 0.21-0.38 follows from the SD range. A 47-world sample of GA run 0 gave an SD of 0.88.
- **Winner's curse:** random sampling's 320 nominees average 1.146 in training and 0.813 on validation; the GA's validation mean is 1.626. The GA's 1.81 and both correlations were not recomputed.
- **Population figures:** spot checks agree (GA run 0, generations 500-559; ES run 0, generations 300-359, near 1.2).
- **Probes:** `mean` and `swapped` do what the plan says (`wormwars/world.py:693`), on Task N's sensing path, before scaling and the clamp. Scripted controllers read the injected current, so the probes reach them.
- **Arithmetic:** 256 000 and 159 488 episodes, the halved scales, and the time estimates against E2's ledger.
- **Ids, seeds and files:** the 992 million block and seeds from 1 130 000 are unused, and the genome files for all 48 champions exist locally.