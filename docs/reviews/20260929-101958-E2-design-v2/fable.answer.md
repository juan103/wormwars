# Review of E2 design v2 (`docs/E2/DESIGN.md`)

My six must-changes from v1 are met. v2 adds one material error and a few gaps, all fixable in the pre-registration. I could not check the ENOMAD summary (no access to the paper); its changes match Astra's v1 corrections.

## Checked against the repository

| Claim in v2 | Finding |
|---|---|
| GA settings, bounds, 5 404 parameters | Match `wormwars/config.py:211-232` and `wormwars/brain.py:246-252`. `p_mutate` is 1.0, so σ = 1 in the ES's encoding equals one GA mutation per coordinate. |
| 4.67 s per generation; 04a at 4.75-5.2 s | Match `freeze.json:512-519` and 04a's correction 2. |
| Between-run SD 0.17-0.30 | Matches 04a's hold-out means (shaped 0.17, unshaped 0.30). |
| ES runs "about 780" generations | **Wrong.** See must-change 1. |
| "A dated roadmap amendment records this" (8 runs) | **Not there.** `ROADMAP.md:161` still says 3 runs, with no amendment. |

## The tuning charge: which rule

**Either is acceptable. I prefer Astra's allowance as the registered rule and withdraw my objection to it.**

- **The two rules give the same champion** if the ES's σ and learning rate are constant, because the trajectory up to the allowance does not depend on what runs after it. v2 declares no noise schedule, so this must be stated.
- **Astra's rule makes "equal simulator work" literally true** and keeps the ledger simple.
- **Suggested addition:** continue the same 8 runs to generation 1 000 as a labelled descriptive arm, about 0.5 GPU-hours. Without it, a "keep the GA" result cannot be separated from the charge itself.
- **The charge is not small.** In 04a, 10 of 16 GA champions came from checkpoints after generation 625. Restricting each run to checkpoints up to 625 lowers its champion's validation mean by 0.11 on average (0.16 for the 4 unshaped runs). Runs 11 and 12 lose 0.50 and 0.61. I computed this from `train-A.json` and `train-B.json`; these are validation means, not hold-out.

## Must-changes (for the pre-registration; no new design round needed)

1. **Correct the ES's run length.** The pilot is 15 runs of 200 generations, or 768 000 episodes. That leaves 1 280 000 of the 2 048 000 allowance, so **625 generations per run**, about 622 once the 23 best-of-32 starts are charged. "About 780" matches a 9-run pilot. Register the formula and say the starts are charged.
2. **Fix one charging rule** and declare σ and the learning rate constant.
3. **Make the outcome wording honest about the charge.** "Keep the GA" means the ES did not win by 0.5 after paying for its tuning. It does not mean the ES is no better at equal length.
4. **Complete the decision rule.**
   - "If both challengers qualify" contradicts "random sampling cannot be chosen". Only the ES can be chosen.
   - Define "within 0.5" one-sidedly: random sampling's mean ≥ the GA's mean − 0.5.
   - Say what happens if the GA's own batch is incomplete.
   - Say whether the diagnosis blocks E3.
5. **Add the roadmap amendment** before binding.
6. **Clarify the GA test.** 04a's committed hashes come from CUDA runs, and `evolve_batch` seeds breeding with a device generator (`wormwars/e04a/evolve.py:123`). A CPU run can therefore match them at generation 0 only. Compare E2's call against a direct `evolve_batch` call on the CPU. Because both call the same function, the test needs a sabotage check (rule 9).

## Suggestions

- **The pilot's cost is a choice.** 15 runs take 37.5% of the allowance; a σ-only pilot of 9 runs would leave 775 generations. I would keep both stages, knowingly.
- **The pilot screens, it does not optimise.** 04a's 16 runs stood at 0.63-2.21 at generation 200, SD 0.36. With 3 runs per setting, differences under about 0.6 are noise.
- **Skipped updates:** freeze Adam's moments and step count on a flat batch, and test a flat batch that follows non-flat ones. Otherwise momentum moves the mean.
- **Still to fix for the ES:** gradient normalisation, Adam's ε, how ranks combine across antithetic pairs, and the noise streams.
- **Checkpoints:** `evolve_batch` also checkpoints at generation 0 (41 in all). Define the same schedule for the other two methods. The ES gets about 26, which is part of the charge.
- **Pilot compositions** (288 and 192 strains) are unmeasured; declare and time them.
- **Power:** the estimate attributed to me was for 3 runs. For 8 runs at SD 0.30, a false switch is under 0.1% and power is 50% at a true gain of 0.5 and about 95% at 0.75. This assumes the ES's spread matches the GA's, which is untested.
- **Housekeeping:** `DECISIONS.md` ends at D116, with no entry for the E2 design reviews.

**E2 design: proceed to pre-registration**