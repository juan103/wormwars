# Review of E2 design v1 (`docs/E2/DESIGN.md`)

The frame is sound: equal simulator work, a random floor, a conservative default to the GA. The ES arm is under-specified in ways that could decide the result on their own, the floor is not a real floor as written, and one budget figure contradicts E1's record. I checked the design against the repository; I could not check the ENOMAD paper.

## Checked against the repository

- **04a's numbers** (2.0-2.8 targets, 23-32% of the oracle, unshaped 4 of 4, best champion run 12) match `RESULTS.md`.
- **"The GA pays no tuning cost"** holds: D105 records that its settings were deliberately kept unchanged for Task N.
- **"About k = 4"** understates the record, which gives 3.5-6.9, and correction 3 warns against reading it as a steering gain.
- **The budget figure is wrong.** 1.6 s per 96-strain generation is below E1's measured time for a single run of 32 strains (2.32-2.34 s, `freeze.json`). E1's curve gives about 2.8 s for 3 runs, so about 0.8 GPU-hours per method, not 0.45, and about 2.7-3 for three methods with tuning.

## Must-changes

1. **Specify the ES fully.** Each gap below can make it lose for a trivial reason.
   - **Learning-rate units.** σ is in GA-mutation units; the learning rate's units are not stated. If they are the same coordinates, lr/σ is 0.005-0.06, against 0.3-2 in ENOMAD's baseline as you quote it. Adam then moves each coordinate at most 10 mutation-σ in 1 000 generations, while a GA lineage moves one per generation. Grid the rate as a multiple of σ (for example 0.1, 0.3, 1).
   - **The start.** 78-97% of generation-0 genomes score zero on every training world, so a single random mean usually starts on the plateau, while the GA starts from the best of 32. Use the best of 32 random genomes, charged 256 episodes.
   - **Ties.** Fitness is a mean of 8 integer counts, so ties are everywhere and total at the start. Use average ranks, and make an all-tied generation a zero update.
   - **Bounds.** Gap conductances start near 0.05 with σ 0.04 and a floor at 0, so many perturbations clamp on one side and break antithetic symmetry. State the rule for clamping evaluated genomes and projecting the mean.
   - **Weight decay.** In normalised coordinates, biases sit about 10 units from zero and log τ up to 20. A decay term of 0.05-0.1 matches or exceeds the gradient noise (about 0.05/σ, my estimate), pulling τ toward 1 tick. Set it to 0.
2. **Make random sampling a real floor.** If the candidate is the checkpoint generation's best, only 1 312 of 32 000 genomes can become champion. Use the best training score since the previous checkpoint.
3. **Reconcile the decision rule with the roadmap.** If random sampling comes within 0.5 of the GA, the roadmap says to diagnose before building on the task; the design says E3 keeps the GA. State which takes precedence, and what happens if two challengers qualify.
4. **The pilot selects on noise.** It has one 100-generation run per setting. 04a's runs 8-15, all on the same settings, stood at 0.51-2.08 at generation 100 (`train-B.json`). Use at least 3 runs per setting or a smaller grid, with pilot seeds disjoint from formal seeds.
5. **Correct the budget** as above.
6. **Equivalence and tests (rules 7, 9).** The GA run through any new shared loop must reproduce `evolve_batch` on the CPU, same seeds and same hashes. The ES update needs a test on a known function, sabotage-checked.

## The six questions

| # | Answer |
|---|---|
| 1 | OpenAI-ES is defensible. ARS is its close relative and adds little. sep-CMA-ES would barely adapt its variances in 1 000 generations at this dimension (my estimate from its default rates). |
| 2 | Charge the tuning, as the standing rule requires, but by limiting the champion's eligible checkpoints, not by shortening runs. Report the full-length result as descriptive. |
| 3 | Dropping shaping is supported for the GA (descriptively). It is untested for the ES, which a sparse integer fitness handicaps. Add a shaped ES arm (c = 0.5 exists), or state the limit in the outcome wording. |
| 4 | The rule is strict but sensible. With 04a's between-run SD (0.17-0.30) and n = 3, a false switch is under about 2%, and power is 50% at a true gain of 0.5 and 85-96% at 0.75. Use 8 runs. |
| 5 | No. It is new infrastructure, and the natural test is refining a 04a champion. |
| 6 | See the must-changes, and the E3 point below. |

## Suggestions

- **Run 8 per method** in 04a's measured (256, 8, 1) composition: about 1.4 GPU-hours per method, 1.7 times the cost of 3 runs. It needs a dated roadmap amendment and a cap near 6-7. Then replace "worst champion" with "at least 6 of 8 above the GA's median".
- **Say which E3 use the choice serves.** E3 evolves a selector and fine-tunes from a working module; E2 tests neither. A short refinement arm from 04a's module would test the second.
- **Add the mirrored and constant probes** to each champion's hold-out, so "better" means better cue use.
- **ES shape.** 32 × 8 is the GA's shape. Consider more directions on fewer worlds, or state it as a limitation.
- **Compositions** are not a fairness threat against a 0.5 margin. Keep every hold-out arm at (1, 1 024, 1) padded, and batch per method, since a non-finite score stops the whole batch.
- **Fresh ranges.** Use new validation and hold-out id ranges.

## ENOMAD summary

I cannot confirm its numbers from memory and have no access to the paper here. Nothing in it is implausible: mesh-adaptive direct search is practical only to about 50 variables, which fits blocks of 49. The two contrasts are fair as argued. Before registration, cite a section or table for each number, give the untrained connectome's score behind "working controller", and say whether their baselines were tuned. "No working prior" holds only from scratch; 04a's champions are one.

**E2 design: revise**