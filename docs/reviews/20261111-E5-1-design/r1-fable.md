# Review of E5-1's design, draft 1

**Verdict: fix then proceed.** The backbone is sound: graft in both test arms, SH-route, a fixed mixture, graphs as the null's unit. Six items need fixing before a pre-registration, and M1 to M3 change the cost or the arms, so draft 2 deserves a short second look. I ran nothing; everything below comes from reading files.

## Must-fix

**M1. The training mixture cannot run in one world as the code stands, and §7 and §8 miss this.**
- The design says "slot k of the 8 always holds setting k" and lists only "a hunt rollout for `evolve_batch`".
- `e5/play.py` takes one prey, one `rule` and one `pinned` per `HuntWorld`. `PreyBrain` has one `kind` and one scalar `speed`. `HuntWorld.pinned` is a single bool.
- Running eight worlds per generation is very expensive. E1's `throughput_04a_shape` (2.33 s at 256 strain-worlds, 4.68 s at 2 048) implies about 2.0 s fixed per rollout. My extrapolation: about 18.6 s per generation for an N2 batch and 16.6 s for a null batch, so the null arm alone is about 74 hours.
- The alternative is one mixed world with per-world prey kind, speed and pin mask. That is new prey and world code. It needs a CPU check per slot against `play()`'s single-setting path, and gate 1 must run at that shape.
- Draft 2 should commit to the mixed world, list it in §8 and bench it. "Engine changes are none beyond the guard" then needs qualifying.

**M2. Gains: keep the choice, but one reason is wrong and one claim is contradicted by committed data.**
- "per-graph hunter gains need per-swarm gains: an engine change" is wrong. Every world object holds one graph. `ScriptedBrain.command` inverts through whatever gains it is given, and `World._read_motors` reads them back from the config. Setting the config's gains per graph and building `PreyBrain` from the same config leaves the prey's commands unchanged up to rounding.
- Your first reason, that calibration rescales the graft's effective gain, is the real one and is enough.
- "a difference in drive counts as part of what the wiring does" is contradicted by 03r's `supplement.json`:

  | Graph | Forward gain | Turn gain |
  |---|---|---|
  | N2 | 4.27 | 2.08 |
  | SH-route, median of 256 | 4.67 | 2.95 |
  | N2perm4 (N2's edges, weights permuted) | 4.68 | 3.07 |
  | N2perm5 | 4.83 | 2.92 |
  | N2perm6 | 4.37 | 3.04 |

- So N2's random brains give about 1.4 times the turn drive at equal gain, and permuting weights on N2's own wiring removes that. This is three draws on 03's task, so indicative only, but it points to weight placement, not wiring.
- 03a's own record agrees in direction: at 4.0 and 2.0 the SH-mirror graph reached forward 0.40 against N2's 0.55, and turn 0.25 against 0.39.
- Fixes:
  - reword the claim;
  - add N2perm as a small descriptive arm (three graphs, two runs each);
  - measure drive at F as well as G0;
  - add a G0-only measurement at calibrated gains, which takes minutes.
- The direction of the bias is unknown: a louder host may mask L1, and a slower one hurts. Say so.

**M3. The host's wiring may contribute too little for the test to be informative.**
- In E4s-1, silencing the module leaves 0.11, and H shows "no material benefit".
- M run 4's evolved module alone on the silent carrier scores 6.93, against a whole-brain mean of 7.14. Ten of 16 modules score 0 alone, so the picture is mixed.
- On E5-0's suite, unevolved L1 on a wiring-free carrier scores 3.01 against the evolved N2 champions' 2.85, and 4.12 against 2.04 at speed 1.0.
- Biases and τ on the 12 read-out neurons evolve in both arms whatever the graph. "No detected advantage" may be close to foregone, and a difference may only show which random host interferes less.
- Minimum fix: a host-wiring lesion probe on every F (host-to-host weights zeroed, biases kept).
- Recommended: an anchor arm of 8 runs in one N2-shaped batch, starting from the carrier with host weights pinned at 0, biases and τ free, and the module at 0.25×.
- State in §9 how each O1 outcome reads against that anchor.

**M4. B's start is ambiguous: "one E4s-1 M champion (F of run i)".**
- In E4s-1, F is the final generation's best (hold-out 7.14) and C is the validation champion (7.37).
- E5-0 tested C: `hunters.e4s1_champions` picks `r["champion"]["checkpoint"]`.
- Every E5-0 number the design leans on (2.85, SD 0.23, 7.41 at ghost, "qualify at every rung") describes C. Say C, or say that F was never measured on Task H.

**M5. The pilot's decision rules must be written before it runs and must not use the N2-against-null contrast.**
- Steps 3 and 4 put N2 and null numbers side by side, a small O0 and O1 on other graphs. After that, "δ … Fixed in the pre-registration after the power simulation" and "500 generations if the pilot shows flat late training". Formal data stays untouched, but the choices become contingent on the contrast.
  - Fix δ now.
  - Write the rule from pooled within-arm spreads to counts.
  - Fix the generations without looking at arm trajectories.
- The stop rule "no strain of any pilot population captures anything" cannot fire. E5-0's motionless hunter gets 0.21 to 0.26 captures per episode on routes from speed 0.4, and ungrafted generation-0 brains get 0.22 to 0.24. Use a scent- or module-dependent signal, such as E4s-1's count of G0 users.
- "on any graph": a failure on null graphs only is a finding, not a reason to stop or redesign. Define the stop on N2, or on both arms.
- A 100-generation pilot cannot show flatness at 500. 02 found shuffles catching up late, so shortening favours whichever arm starts ahead.
- "2 runs on 2 pilot graphs" gives one degree of freedom for the between-graph SD, at generation 100. §5 says "4 graphs"; §6 says 2. Run the simulation over a grid of SDs, as E4s-1 did, and use the pilot as a plausibility check.

**M6. O1's rules.**
- "N2 ahead" needs Δ̂ ≥ δ, so power at Δ = δ is at most 50% at any sample size. The simulation cannot "decide the counts" against that target. Target the correct label at Δ = 0 and at Δ = 2δ.
- At your own guesses (SE 0.119, which I confirm), a true null reads "no detected advantage" about 63% of the time, inconclusive 30%, "reversed" 5%, "N2 ahead" 2% (normal approximation).
- About 80% needs an SE near 0.09. For example, 32 N2 runs and 24 graphs × 2 gives 0.092; 32 N2 runs and 16 graphs × 4 gives 0.099.
- The rules are asymmetric: "reversed" needs no margin and "N2 ahead" needs δ. There is no prior direction here, so make it "SH-route ahead" with −δ.
- The estimand compares N2 with the mean graph. "N2 ahead" does not mean N2 is unusual within the ensemble.
  - Register the wording "above the average SH-route graph".
  - Report the latent between-graph SD, Δ over that SD, and how many graphs exceed N2's mean.

## Should-fix

1. **Training and score weights disagree.** Static is 1 of 8 slots and about 10% of a strong hunter's captures, but a third of the score. Rebalance the slots (for example 2 static, 4 route, 2 movers) or justify.
2. **"interpolation and transfer" overstates.** No prey kind is unseen, and route 0.1 sits between static and 0.2. Rename it, or hold one kind out.
3. **O0 on the best of 32 mixes host quality with an extreme draw.** Measure the G0 populations, for example on 256 mixture worlds.
4. **"a better host for evolving a hunter" is a claim about the climb (O1c); O1 is about endpoints.** Fix the sentence and write companion sentences in advance, as E4s-1 did. Report Δ along training from the validation checkpoints, which are free.
5. **Gate 1, state level.** "the maximum absolute state difference" does not name its two sides (CPU against CUDA, or shape against shape). It uses one genome per graph type; E4s-1's gate 2 used 48.
6. **Gate 1, world level.** Nothing tests the hunt world's own code on CUDA beyond a 0.05 score tolerance. Add:
   - prey paths with a motionless ghost hunter, CPU against CUDA, for each prey kind;
   - early-tick traces for the scripted pursuit;
   - H1-ghost against Task N on CUDA, since O3 relies on it and E5-0 showed it on CPU only.
7. **The 0.05 tolerance on 512 worlds can fail by chance** for neural hunters under bites, and a failure stops the stage. Use a paired interval or more worlds.
8. **Bootstrap.** Resampling 2 runs within each drawn graph widens the interval slightly; a percentile interval over 16 units narrows it by a similar amount. Fix the procedure text and have the simulation report coverage and false-label rates.
9. **Batch shapes differ between arms** (8 runs for N2, 2 for nulls). This is not a plausible bias, but rule 6 claims exactness only within one composition. Run G-N2 in 2-run batches or declare it. Interleave the arms, and say what is analysed if the cap stops the run.
10. **"256 validation worlds" has no stated composition.** C depends on it.
11. **Probe label.** "the module-only `mean` (… E4s-1's H probe)": in E4s-1 that condition is D's. H is the host's class while the module is blind.
12. **Guards missing from §8.**
    - `Genome.assign` has the same hole as `cat`.
    - Compare by value: `evo/genomes.edge_hash` exists, and `moved()` makes new spec objects, so identity will not work.
    - `Genome.cat` has 133 call sites, so run the whole suite.
    - The publication guard splits labels on "+" and looks the base up in `anat`; a null graph plus L1 has no entry there.
    - Each run record should carry its graph's hashes.
13. **Cost.**
    - "about 1.35 hours" is below all ten cited E4s-1 batches (4 876 to 5 151 s, mean 4 984 s, or 1.38 h).
    - The null rate of 2.6 s is rollout-only, while N2's 4.9 s includes breeding and checkpoints. On the same basis nulls come to about 12.3 h.
    - The mutational-sensitivity step is unsized. By my estimate, 24 parents × 256 mutants × 256 worlds is about 1.6 M episodes, as large as the endpoint evaluation.
    - There is no reserve for reruns.
    - The evaluation line has slack: about 3.05 M episodes at E4s-1's 465 worlds per second is 1.8 h at Task N's rate.
14. **Name the graphs.** "first 16 … by index" and "17 to 20" are ambiguous between 0- and 1-based. §4 promises drive for "each graph", but §6.3 measures pilot graphs only.
15. **O3.** For G-N2 it is not "inherited function"; the arm never trained on Task N. Add G-SHr on H1-ghost, which is free.

## Answers to §10

1. **Graft in both arms:** acceptable as the confirmatory pair, with M3's anchor and the narrower wording. Do not add or substitute the no-graft pair now. Tell the owner plainly that this answers "N2 as a host for L1", not their question as asked.
2. **One ensemble:** SH-route only. Spend any extra on N2perm, not SH. A second shuffle does not address the weight-placement gap (M2).
3. **Gains:** N2's for every graph, as the primary, with M2's corrections and additions.
4. **Mixture and suite:** keep the fixed mixture and the three-strata score. Rebalance the slots (should-fix 1). Do not hold the movers out; drop the word "transfer". H3 and H4 are the real transfer tests.
5. **δ and counts:** fix δ = 0.25 now, as a convention, and say what it is relative to M3's anchor. The counts are probably too few for a clean null label. Prefer more graphs. If the bench confirms that batch cost is nearly flat in runs, 4 runs per graph and 32 N2 runs are cheap.
6. **B's start:** 32 identical copies, of C (M4).
7. **B in E5-1:** yes, but it runs after the confirmatory arms, on its own cap line.

## Factual claims checked

| Claim | Checked against | Result |
|---|---|---|
| `Genome.cat` keeps the first spec without checking | `brain.py:161-169` | Correct; equal edge counts would concatenate silently |
| `evolve_batch` takes one `BrainSpec` | `e04a/evolve.py` | Correct |
| E1's 2.33 s and 3.04 s | `freeze.json` | Correct (and 4.68 s at 8) |
| E4s-1's batches, 4 876 to 5 151 s | `train-*.json` | Correct; the "1.35 h" derived from them is not |
| Suite means 2.85, 3.01, 0.76, 0.11 | E5-0 `RESULTS.md` §4 | Recomputed, correct |
| Other §2 numbers (4.57 to 7.72, 1.13, 0.01, 3.5 to 3.6, 2.04, 4.51, 27%, 7.41) | E5-0 `RESULTS.md` | Correct |
| SD 0.23 and range 2.60 to 3.41 | not checked | Scratch arithmetic by your own note; rule 5 needs a script |
| 16 output synapses onto 8 turn neurons, kept by name | `e4s/comparator.py`, `samplers.py` | Correct |
| SH-route's definition, 03's caveat, 02's tripwire | `samplers.py`, both READMEs | Correct |
| 03a's gains, 6.27 and 3.22 | `pilot-dev/setup.json` | Correct |
| `_route_for` loops in Python on each capture; host syncs in `hunt.py` | `prey.py`, `hunt.py` | Correct |
| E4s-1's arms, 0.25×, 16.61 h | design, `RESULTS.md`, `compute-record.json` | Correct |

Not checked: 03r's manifests, D-numbers in `DECISIONS.md`, E2's own 1.35 h figure.

## Anything else

- F is picked on 8 worlds, one per setting, which is noisier than in E4s-1. Choose F or C as the registered genome now, by a rule that ignores the contrast.
- The 16 formal graphs already have 03r covariates (P4, calibrated gains). Register a descriptive plot of each graph's mean score against them.