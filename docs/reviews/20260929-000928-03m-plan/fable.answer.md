# Review of 03m plan v1 (what drives P4)

**Verdict: revise.** `p4m.py` reproduces 03's measurement faithfully and I found no logic bug in the batching, pairs or decay curve. The must-fixes are two text errors, a compute estimate that 03's own timings contradict, a batch-composition problem in the lesions, and one design choice in Q3.

I could not run anything; everything below is from reading the code and committed files.

## What I checked in the code

| Item | Result |
|---|---|
| Genomes | `probe_genomes` matches `measure_graph`: same spec, `task_config(Config(), "T1")` + `brain_config_for_graph`, generator seeded `_gseed(name) + 1`, 2 048 draws. |
| Calibration skipped | Harmless. P4 reads `raw_turn` (`_readout` index 1), which never touches the gains; `_current` uses only brain config. |
| Bank, interface | Same `pilot.json` bank, same M0 interface from 02's remaps. |
| Reproduction gate | Keys `P4_turn_numerator` / `P4_turn_denominator` exist in the supplement. Fails closed outside smoke. |
| `history_in_chunks` | Correct. `Genome.cat([g]*k)` gives blocks in order; the deletion lists and slices line up block for block. |
| `pairs` | Correct for this naming. No false pairs that I can find (AVL, RIR, PVR have no partner); RMD / RMDD / RMDV keys do not collide. |
| `history_curve` | Same stimulus as `M.history`; row 0 is "final". In smoke, N2's row 0 (0.2071436) equals the reproduced numerator. |
| Permutation seeds | 100–163 give generator seeds 200–327; no overlap with 03 (2–7) or 03r (8–13). |
| Deletion of sensors | The deleted neuron still receives current but is isolated, so the input is removed from the network. |

## Must-fix

1. **"N2 nevertheless has the highest P4" is false.**
   - 03: SH-route-20078 is at 0.934 against N2's 0.931.
   - 03r: one SH-class graph is at or above N2.
   - Say "above all but one graph in each instance".

2. **"4.7 to 7.4 times the ensemble median" does not match `tradeoff.json`.**
   - The ten values run from 4.70 to 7.09, so 4.7 to 7.1.
   - The minimum over-max ratio is 1.55, so "1.5" should be 1.6.

3. **The compute estimate is contradicted by committed timings.**
   - 03's `pilot.json` records the history probe at 12.6–13.9 s per graph at 2 048 genomes.
   - At about 12.7 s, my projection is about 2.6 GPU-hours, not "under 1":

     | Command | Work | Projected |
     |---|---|---|
     | lesions | about 375 deletions (284 singles, pairs estimated at about 90) | 1.3 h |
     | decay | 81 graphs × 410/115 ticks | 1.0 h |
     | weights | 64 permutations | 0.23 h |
     | synapses + four gates | 8 histories | 0.03 h |

   - The 3-hour cap is not enforced anywhere in `p4m.py`.
   - `cmd_lesions` writes only at the end, so a kill loses everything.
   - `runs/**/compute.json` is git-ignored, so the cap's record would not be committed.
   - Fix: project from the first chunk, check the cap between chunks, write incrementally, and copy the record into the experiment folder as 04a and E1 do.

4. **Lesions run at a different batch composition from the reference.**
   - Default `--per-chunk 16384` gives 8 deletions × 2 048 strains at 1 row. The gate checks 2 048 strains.
   - T1.md decision 3 says direct-step probes at 1 row differ by strain count, and to fix and record the count.
   - 16 384 strains also means about 12 GB of dense W and G on a 16 GB card, a size never run. `timing.json` shows flat throughput from 512 to 16 384, so nothing is gained.
   - Fix: default to 2 048 and record `per_chunk` in the output.
   - Add an empty deletion list as the first entry. It must reproduce N2's intact values, and it is the only check that can fail for `history_in_chunks`.

5. **Q3's by-type permutation uses seed 1, which is N2perm1's placement.**
   - Chemical generator seed 2 and gap seed 3 are exactly N2perm1's.
   - N2perm1 is the outlier of the six: response 3.9 × the SH median, P4 0.797.
   - One draw, and the atypical one. Run by-type permutations over several of Q5's seeds, which costs little.

6. **Keep the per-genome arrays.** `p4_of` discards them, and re-analysis would cost GPU-hours again under the cap. See Q1 below for why they matter. It is about 9 MB as a local `.npz`.

## Q1: is the trade-off sound?

**Probably not a sampling-noise ratio artefact.** 03's pilot put P4's reliability at 0.99 (SE 0.006 against a between-graph SD of 0.074). Shared noise cannot produce a Spearman of −0.3 to −0.6. A split-half check would confirm it.

**It is more likely structural, and partly the routing effect 03 already knew.**
- The correlation is weakest in the two ensembles with the routing cap (SH-route −0.29 and −0.35, SH-mirror −0.27 and −0.45) and strongest in SH (−0.60, −0.57).
- Those capped ensembles also have higher mean P4 (0.84 against 0.75).
- Direct food-to-read-out edges give a strong, fast response, hence low P4. N2 does not share that axis, so the extrapolated trend is a weak reference.

**What I would check first: per-genome tails.**
- In the smoke decay run (8 CPU genomes, so only a hint), one N2 genome held a difference of about 0.77 at 300 ticks. That one genome carries 47% of the mean numerator.
- None of the 80 null genomes persisted.
- If that holds at 2 048, N2's large response and high P4 are both carried by a minority of genomes with a lasting state, and "slow, persistent dynamics" is the wrong description.
- This needs 03's per-genome measures, which are local and not in this worktree.

**Saturation** looks unlikely at the mean level: values near 0.13 on a ±2 scale, and 03's RESULTS found no rise of the ratio with contrast within N2.

## Q2–Q5

**Q2, the lead criterion.**
- The thresholds are real: P4 must fall below about 0.853 (SH's 95th percentile) and the response below about 0.048.
- Requiring both selects neurons that cut the route to the read-out, and hides dissociations. Report three classes: response only, P4 only, both.
- Five of six weight permutations already fail the P4 half, so zero leads is likely. Say what that would mean.
- Add each deletion's residual from Q1's trend, and the neuron's degree.

**Q2, the exclusions.**
- P4 uses the turn read-out only. Excluding the ten forward read-out neurons (AVA, AVB, AVD, AVE, PVC) is unnecessary and removes the largest hubs from the screen.
- The roadmap asks for connection deletions too. The plan has none and does not list them under "Not in this plan".

**Q3.** Gaps-off N2 is compared with intact nulls, which mixes two differences. Run gaps-off on Q4's 80 graphs as well. Q3 also states no reading criterion.

**Q4.**
- "Persists points to multiple stable states" overclaims. A limit cycle out of phase, chaos or a very slow network mode look the same at 300 ticks. Record whether each trajectory is stationary at the end.
- 300 ticks is 15 of the slowest neuron constant, not of the slowest network mode.
- The 10% rule needs an absolute floor: null curves plateau near 5 × 10⁻⁶, so genomes with tiny starting differences give noise ratios.

**Q5.** Each permutation draws its own genomes, as 03 did. Pairing with N2's genomes would isolate weight placement more cleanly; doing both is cheap.

## Suggestions

- Re-run smoke on the committed code. The smoke lesions, synapses and weights outputs came from an earlier `reproduce_n2` (their gate values are 0.1226, the decay one is 0.2071), all at `7ec22bb`.
- Add CPU tests for `history_in_chunks`, `history_curve` and `pairs` (rule 9); none exist.
- NaN handling: a collapsed response gives `P4_share_below` 0.0, non-standard JSON, and a NaN median in `cmd_weights`.
- Compare each null graph's decay row 0 with its supplement numerator.
- Stamp outputs with commit, device and versions.
- I found no archived copy of the outside review; rule 10 would want one if its readings are cited.

**03m plan: revise**