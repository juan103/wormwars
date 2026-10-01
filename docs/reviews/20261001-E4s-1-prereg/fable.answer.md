## 1. Verdict: bind after fixes

The arms, estimands and outcome rules are sound. O1's five rules, the 3 × 3 O2 table (all nine cells), the O2b bands and C2's ordered reading are each exclusive and complete, and each is implementable from the stated measures. `power.json` matches every number the draft quotes. The fixes below are all text; none changes an arm. I ran nothing.

Checked and correct:
- F, C and G0 match `evolve_batch` (`rec.candidates[-1]`, `champion_index`, `candidates[0]`; `np.argmax` gives ties to the lowest index).
- A factor of 0 pins exactly in `Genome.mutate`: the noise is multiplied by 0, and τ is multiplied by exp(0) = 1.
- World seed 1 100 001 is `scripts/e2.py:88`; 4 862 s is `train-ga.json:180308`.
- The module's full hash is in `ladder.json:34471`.
- The 942 M ids and the 1 160 000-1 168 000 seeds do not collide with E4s-0's (940 M; 1 150 000, 1 151 000).
- The open-loop constants match E4s-0's attenuation probe (`scripts/e4s0.py:67`).

## 2. Must-fix

1. **§4, R's draw: "applied" is ambiguous.** It can mean each weight becomes draw × 3, or each designed weight is multiplied by the draw. These give different realised grafts from the same seed. Pin one, for example "edge k's weight is s_k × 3.0".

2. **§3 G2: the shapes do not cover the 48 genomes.** "Filled by tiling the 48 genomes in order" puts only genomes 0-7 (all random N2) in the 8 × 256 shape and only genome 0 in the two single-strain shapes. No 04a champion is ever tested in those shapes. State that each shape is repeated until all 48 are covered (6 batches of 8; 48 single runs), or name the subset.

3. **§3 G2: the input history is not reproducible as written.**
   - It does not say whether the uniform draw is per tick × neuron only (shared across rows and strains) or also per row, nor the array shape and order of the draw.
   - "The module's noses receive the food signals as the interface routes them" has no meaning under an imposed history, because there are no food signals. Say whether the noses get the currents imposed on the `food_left`/`food_right` sensors, their own draws, or 0.
   - State that the ungrafted and grafted brains each run in their own batch of the named shape, on CUDA.

4. **§3 G3: the execution shape is missing.** Say 1 padded × 256 per genome, or another shape. The closed-loop comparison depends on composition (rule 6). Cite the records that carry the 24 hashes (04a's `train-A.json`/`train-B.json`, E2's `train-ga.json`); Fable's confirmation review asked for the list by sha256.

5. **§3 against §8: can a failed gate be rerun?** §3 says a failure stops E4s-1. §8 allows one rerun per stage that "stops". Add: a gate that completes and fails its test is final; the rerun is only for a stage that did not complete.

6. **§8: the stage list and order are not stated.** Write: projection, G1, G2, G3, batches 1-10, evaluation, each with a committed record. Also pin the projection's seeds and worlds outside the registered blocks (E2d used smoke ids and its own seed base), and state that it reads no scores. Otherwise "nothing has run on E4s-1's worlds or seeds" can be broken by the projection.

7. **§8: "an evaluation reserve" has no value.** Admission depends on it. State whether it is the 6 h evaluation cap, the projected evaluation time, or another figure. Say what a stage cap does when a stage exceeds it but the 24 h total still fits.

8. **§4: an end-of-run assertion failure has no consequence.** State it, for example: the arm's batch is "not read" and E4s-1 stops for diagnosis. If N's pin fails, O1 must not be read.

9. **§6 O2: the denominators under incomplete runs.** Say whether "12 of 16" (6 of 8) stays fixed when runs are "not read". Fixed is the safer rule, and it matches §7. Also say what the arm's reading is when no label reaches the threshold: "no label named", with the counts. "Mixed" is used but never defined.

10. **§2: the bounds are missing, and they shape what mutation can do.** L1's 20 weights are ±3.0 with `w_max` = 3.0, and its τ is 0.5 with `tau_min` = 0.5 (`wormwars/config.py:36-38`; `ladder.json` records `on_bounds: w_n, w_o, tau`). The same holds for R's edges. So in M, R, U and S the module's weights can only shrink and its τ only grow, and about half of each parameter's mutations are clamped back. State this in §2 and in §11. Otherwise a loss of use at F reads as "evolution discarded the module" when one-sided drift from a boundary optimum is an equal candidate.

11. **§6 power: SD 1.3 is an assumption with no cited basis.** The draft omits the SD 2.0 row that is in `power.json` (7% / 28% / 64%). Either cite where 1.3 comes from, or quote both rows and write "about 1 target per episode if the SD is about 1.3; 64% at SD 2.0". This applies to §11's fourth bullet too.

12. **§6: the bootstrap implementation.** Name it: E2d's `_boot_means(d, 10 000, 20 261 001)`, 5th and 95th percentiles by `np.percentile`, the same seed for O1 and O1b. "Percentile bootstrap" alone leaves the generator and the index draw open.

13. **Departures from design v2 are not flagged as such.** Rule 2's spirit, and the question's "nothing contradicts the design":
    - C2's "harmful" bound moved from 0 to −0.25, and "uses" now comes first;
    - an unclear G0 with "uses" at F is folded into "uses at F only", where the design said an unclear endpoint is never folded into a label;
    - the index changed from 1-16 to 0-15.

    All three are defensible. List them in one "Changes from design v2" paragraph.

14. **§2: give the module's sha256 in full.** "Checked in full" against an abbreviated hash is not checkable from the binding text.

Should-fix, not blocking:
- **§9, rule 5: the episode count does not reproduce.** I count about 14 distinct 1 024-world rollouts per genome, not 11: real; 2 for D; 2 new for H; 6 for Mc; lesion, reset and rescue. Even at 11, the listed parts sum to about 4.1 M episodes, not 3.7 M. At 14 it is about 4.9 M, still inside the 6 h evaluation cap. Show the arithmetic.
- **§5: say which arms get which measures.** D and Mc on N are vacuous. Reset and rescue at G0 equal "real" for M.
- **§5 motor measures: define m and d.** Left = m + d/2, right = m − d/2, the command clamped, as in `cmd_attenuation`.
- **O1 rule 3's label:** "positive, below 0.5" should read "positive, estimate below 0.5". The upper bound can exceed 0.5.

## 3. What could be read two ways after the data are in

- **F against C.** If M − N differs between them, both will be on the table. Add: "C never changes an O1 or O1b label".
- **"Supports" for O1 with a non-positive M climb.** The draft says M need not climb, but the label still reads "leads to a better final brain". Add a fixed sentence that goes with the label whenever M's mean climb interval includes 0: "N ended lower; M did not improve".
- **O1b "supports" with R − N < 0.** Fix the companion sentence in the same way: "random signs were worse than no graft". R − N is descriptive, so without fixed wording the emphasis is chosen after the data.
- **Loss of use at F** (item 10): selection against the module, or clamped drift. F0 against M is the only handle on this and it has 8 runs. Say in advance that F0 − M is the comparison that addresses it, descriptively.
- **A G1 fail, at 4.7% by chance.** "The code and the environment may be checked" leaves open whether a found bug permits a re-gate on the same worlds. Say that any re-gate is an amendment, on fresh worlds.
- **The O3 median split.** Pin it as 8 against 8 by rank, ties to the lower run index, so the split cannot shift.