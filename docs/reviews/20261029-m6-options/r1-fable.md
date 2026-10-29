Checks done. Here is my review.

## 1. Facts and costs

| Claim in the note | Check |
|---|---|
| About 100 generation-39 T1 champions | 102 files: 96 (4 mappings × 24 runs) + 6 N2perm. Correct. |
| g79 "for two runs" | Wrong for T1: four T1 runs have g79 (N2 run00, run01, SH1 run00, SH2 run00); eight across T0 and T1. |
| Classifier about 1.4 s per genome, both passes | M4e: 32.66 h over 8 arms × 10,240 genomes = 1.44 s. Correct. But the second pass alone cost about 75 s per genome processed (M4E-RESULTS). If every champion gets the 22,000-tick pass, as the note's wording suggests, 204 genomes cost about 4 CPU hours, not "under 1". Fix the rule: second pass only for genomes not fading on the first. |
| T1 about 0.14 s per genome-world on the CPU | No file records it, so I cannot verify it. It is consistent with the GPU rate (167 genome-worlds/s in `experiments/03-generation0/timing.json`, about 6 ms) at a 20 to 25× CPU penalty. Note T1 is 400 ticks (`grid.task_config`), not 200. |
| Option 2 at about 150 CPU hours or a few GPU hours | 32 × 256 × 8 × 60 = 3.9 M genome-worlds: 153 h at 0.14 s, about 6.5 GPU-hours at 167/s. Correct, before holdouts and the relief's scripted gate. |
| "1.5% of N2's random genomes" | 15 and 13 of 937 to 1010 eligible genomes. Fine, but it is a rate among eligible genomes on M0's interface; M4d's no-floor convention should apply to champions. |
| "generation-0 starts" | They are best-of-32 snapshots (`evolve.py:159`, argmax of training fitness), selected, and not the g39 lineage's ancestor in any particular sense. Call them generation-0 champions. |

**The biggest factual gap:** the note says 02's pilot champion was "not hurt by the history ablation (D038), so switches may be rare". That ablation was jitter 1, which D039 says cannot detect an integrating controller. 02b then showed, on exactly M2's probe (0.25/1.75 ramp), that selection built a persistent level memory into every group of T1 champions: turn difference 0.281 (N2) and 0.158 (SH) at g39 against about 0.10 and 0.04 at g0 and under a mutation-only drift control, with 0.83 to 0.87 surviving five more ticks. So option 0 is not a blind count. It asks whether a known, selection-built history effect is a switch or slow fading. That makes its answer more likely to be informative than the note says, and 02b's drift control is the control option 0 needs.

## 2. Sizes

- **Option 0** is fairly sized as descriptive, but say what is readable: with 38 N2 champions and a 1.5% base rate, only a rate above roughly 10% separates from noise; with 64 SH champions and a base rate near 0.1% (19 of 30 null graphs had none), three or more switches would already be notable.
- **Option 1 is oversized by about 5×.** The classification is free: the census and M4c records hold per-genome classes and the genomes regenerate from seeds (N2's 28, M4c's 141 fresh N2 switches, the selected graphs' 12 to 78 each). Only the switches and a matched sample of fading genomes need T1 rollouts: about 1 to 3 CPU hours, plus motor calibration for any graph 02 never calibrated. It is still the weakest option: a random switch set by the probe's history has no reason to be aligned with anything useful, so a null is the expected answer and would not mean switches are useless. 03h's step 0 already found near zero for the history magnitude.
- **Option 2's risk is understated.** Its unit must be the run, and 16 champions per arm cannot carry a rate contrast; classify each run's final population (256 × 32 × 1.4 s, about 3 h, fine) and compare population shares. The food-channel relief has never been built or gated; 03h's gate machinery exists but the relief does not. And 02's exploration found no detectable history use at 120 generations or 4× population by the jitter measure, though 02b's finding softens that.
- **Option 3** is fine as stated. RIA, RMD and SMD are a documented head-steering circuit in the worm, so a proper review would not be empty, but it must meet the literature standard.

## 3. Option 0: what must be fixed first

1. **A drift control, fixed in advance.** Mutation adds about SD 0.5 per weight over 40 generations against an initial scale of 0.2, and M4e showed the switch rate depends on weight concentration. A rise at g39 could be drift, not selection. Reuse 02b's design: each g00 champion mutated 39 times without selection, 4 replicates, same operator and seeds, classified the same way. About 10 CPU minutes.
2. **Compare within mapping and graph**, g39 against g00 and drift. The 1.5% base rate applies to N2 under M0 only; generation-0 rates under R1, R2 and MS interfaces and on SH1 to SH8 are unknown.
3. **Thread the interface through the classifier.** `grid.interface_for(con, mapping, remap_sets)` exists and `measures.history` accepts an interface, but the census's `probe_states(gs, cfg)` takes only the brain config, so the interface and bank are fixed inside it. That is a code change with a test, and the champions must run under their saved config via `brain_config_for` (pre_to_post, padding off).
4. **Plan the unresolved genomes.** The classifier was validated on random genomes. Evolved genomes with grown weights may oscillate or stall more often (M4d's heavy arms gathered not-settled genomes), so fix the second pass's rule and the wording for "mostly unresolved" before looking.
5. **Redefine the state test.** Starting a champion in each root and running T1 confounds the state with an initial condition the world's input may wash out in a few ticks, and the roots are equilibria under a constant bank, not under foraging. The readable check is whether the full state visits both roots' neighbourhoods during a T1 replay. The "use" test proper, a within-task ablation of the switch against a matched control, is a design item for after the count.
6. **Include the four g79 champions** and report N2, SH and N2perm separately.

With these, the cost is about 1 CPU hour for the minimal version and up to about 5 if every champion gets the long pass. Nothing I found makes option 0 unworkable.

## 4. Recommendation

Run option 0 with the fixes above, and read it against 02b's history magnitudes per champion. Skip option 1 as a separate step; if wanted, fold in N2's 169 known switch genomes against matched fading genomes at 16 worlds (under 30 CPU minutes) as a side panel. Hold option 2 until option 0 shows a switch rate among champions clearly above the drift control; if it does not, the switches are probably not what selection built, and option 4 is the honest stop for the compute side, with option 3 at zero compute.