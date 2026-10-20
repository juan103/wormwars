**Verdict: revise.** The plan's order and steps can stand, but finding 2 (the latch) overstates what batch 8 measured, omits a committed 03mc result that cuts against it, and the attributions need three corrections. None of this takes long, but it has to happen before the push, because finding 2 is the roadmap's headline.

## Factual claims

**Batch 8 claims the files do not support as worded**

- *"in 4.1% of N2 genomes, the network is unstable at the midpoint ... but stable at each history's own end state."* The script computes the two fractions separately (`scripts/memory_spikes/batch8.py:74-75`) and never their conjunction. The file gives 21 of 512 midpoint-unstable and 6 of 512 unstable at their own ramp-end state. Only the 8 settled genomes are shown to be both (midpoint-unstable, own-end stable). For the other 13 nothing is known.
- *"That is a saddle between two stable states."* The Jacobians are taken at the ramp-end states and their midpoint (`batch8.py:61`). None of these is a fixed point. The midpoint is still relaxing, so a spectral radius above 1 there shows local expansion, not a saddle. Astra's own wording was "could indicate a separating saddle". Write "consistent with a saddle" and say the stability of the actual end states at tick 300 is untested. M2 should take the Jacobian there.
- *"every N2 genome whose difference stays at full size to tick 300 is one of these."* The criterion is retention above 10% and a change under 2% between ticks 250 and 300 (`batch8.py:70`). The 8 that pass happen to have a median retention near 1.0, but "full size" is not the definition, and a genome at full size still drifting 3% would be excluded. Say "every settled, separated genome (8 of 512)".
- *"A minority of N2 brains latch ... 4.1%."* The 4.1% are midpoint-unstable. The latch, in the sense the roadmap means, is the 1.6% that settle. 62% of the midpoint-unstable genomes did not settle. The roadmap should keep the two numbers apart and add a class for them in M2.
- *"their unstable direction lies 92% on a 30-neuron head core ... (uniform: 10% and 3%)."* Supported as the mean squared-modulus mass of the leading right eigenvector over 21 genomes. The comparison is unfair, though. N2's stable genomes already put 43% on the core and 24% on RMD/SMD (`batch8.json`, the `rho_le1` entries). The core list is also the top-30 start-difference list, so the localisation partly restates how the core was chosen.
- *"it is almost never oscillatory: 9.5% ..."* That is 2 of 21. Report counts beside percentages throughout finding 2. The script also does not record the sign of a real leading eigenvalue; a value below minus 1 would be a flip, not a latch. Implausible with 32 substeps, but free to record.

**A committed result the roadmap omits.** 03mc already counted "settled with separation" genomes on all 640 graphs (`experiments/03mc-p4-confirm/RESULTS.md:149-151`, `report.json:5692-5907`). N2 has 26 of 2048. The ensemble medians are 0 or 1, but single null graphs reach 41, 28, 113, 81 and 126. A null graph with 126 settled genomes has five times N2's latch rate. So latching is not what makes N2 unusual; at most its location or amplitude weighting is. Batch 8 shows the same thing in miniature: SH-class-2030000 has 6 settled genomes to N2's 8 and a share of 0.483 to N2's 0.504. The roadmap calls the latch "the result most worth checking first" without saying this.

**Other claims**

- *"the genomes with large differences lose less of them"* (finding 1). The correlation is still negative in N2 (−0.13). Large differences still retain less, just less steeply than in nulls. Astra flagged this in round 3; the roadmap says "all accepted" but kept the sentence.
- *"8 batches of cheap CPU checks"* between rounds 2 and 3. Seven; batch 8 came after round 3, as the next row says.
- *"erased, the signal regrows from the rest of the core."* The regrowth is measured (`batch1.json`, `batch6.json`: 83% and 82% of intact). Its source is not. The "core" part is an inference from batch 4's residual localisation. I made the same leap in round 3.
- *"no neuron's tau or bias predicts retention beyond |rho| 0.10."* True for N2; SH-class-2030000 reaches 0.12 (`batch4.json`). Say "about 0.1".
- *"N2's response is about five times a null's."* Supported: 0.114 against the permutations' median 0.024 in Q-C, and null-graph denominators of 0.013 to 0.044 in `measurements.json`. Cite one of them.

Everything else I checked holds: the 0.436 and medians, the three panel shares, the 17 to 46 graphs, 0.197 against 0.192 and 0.200, −0.39 to −0.42, batch 7's four means (recomputed from `batch7.json`), 73% moved, 199 edges, 70% removed, the core list, the substeps and warm-up and food arms, the pharynx, batch 3's spectra, and the regenerated extrapolation in `check_structure.txt`.

## Fairness

- **One misattribution.** *"Fable's draft thresholds ... latch fraction from under 1% to at least 3%."* I wrote "growth fraction", the fraction whose full-state difference grows over ten ticks. Given that null graphs reach 6% settled genomes on their own, a latch-fraction threshold is also a worse endpoint than the one I proposed.
- **The amplitude arm is credited to me alone.** Astra designed the midpoint-preserving scaling in round 2 (idea B and Measurement 3) and repeated it in round 3. I pressed it as "untested" using Astra's design. Credit both, design to Astra.
- **The erasure-conflation objection** was raised by both of us; the roadmap credits Astra only. Minor.
- **The batch-8 join.** My family-1 kill-check was "count the settled-with-separation genomes against rho above 1 on a fresh panel". That is the test batch 8 ran. The roadmap calls it Astra's join. Both proposed it.
- **Astra's round 2 is uncredited** while mine is. The decomposition formula, the alpha scaling and the maintenance-erasure design that became batches 4 and 6 are all in Astra's round-2 answer.
- **What I said against Claude's reading** is represented fairly in finding 5. My "half right" on the oscillator is fair too: the complex-eigenvalue half failed, the RMD/SMD-eigenvector half held. The roadmap could say so.
- **Missing from my steps:** the three cheap kills moved from my step 3 (minutes) to M4 (hours in). They are seconds to minutes and should run in M1. My family 2 and 4 kill-checks (growers with rho below 1; the Spearman excluding rho-above-1 genomes) are seconds on batch 3's data and are absent. Optional.

## The plan

- **Order:** right in outline. Two changes. M3's predictor is minutes and gates M5, so run it beside M1. Start M2 from 03mc's existing 640-graph settled census and arrays (seconds), not from fresh panels, and pull the null graphs with 81 to 126 settled genomes. That is also my round-3 "what do the high-retention nulls share" question.
- **Decision points:** the header says two, the steps list three (M1, M2, M3). Say three. Require each pivot to replicate on a second panel or several graphs first; N2's own share moves 0.40 to 0.50 between panels.
- **"Latch fraction" is undefined in M1.** Batch 8 offers two definitions that differ by 2.5×. Fix the trajectory-based one (settled and separated) as primary. It is computable on 03mc's arrays and cheap; the Jacobian becomes M2's mechanism check.
- **Costs** are optimistic by about 2× where Jacobians are involved. From batch 8's timings, 36 arms of 1024 genomes with follow 300 are about 2.2 CPU hours without Jacobians and near 7 with them. M2's "1 to 2 hours" is similar. Not a blocker; say which.
- **M2's oscillation class** needs every-tick recording. The probe samples every 10 ticks after tick 10 (`spikes.py:28`), so the flip count aliases.
- **Pre-registration:** M1 to M4 exploratory is right. M5 confirmatory is right. Nothing in M5 should move earlier. M5's thresholds should be relative to each host's own baseline, since hosts vary this much.

## What must change before the push

1. Rewrite finding 2 with the distinctions above: 21 midpoint-unstable, 8 settled, counts beside percentages, ramp-end states named as such, "consistent with" a saddle, the stable-genome baseline for the eigenvector, and the 03mc census with its 126-genome null graph.
2. Fix "lose less of them", "8 batches", "regrows from the rest of the core", and the tau bound.
3. Correct "latch fraction" to "growth fraction" in M5, credit Astra for the amplitude design and round 2, and credit the join to both.
4. Define the latch fraction in M1, state the three decision points, and move the cheap kills into M1.

The small fixes: cite `measurements.json` for the five-times figure, note the costs with and without Jacobians, and add the every-tick recording to M2.