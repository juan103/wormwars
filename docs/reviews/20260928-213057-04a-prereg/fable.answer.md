# Review: 04a pre-registration, draft v1

**Verdict: revise.** The design is sound and covers the D101 list. The blockers are one conflict with the connectome rule, several places where the text and the code disagree, and one overclaim in the outcome wording. None needs a redesign.

I could not run anything. I did not verify hashes, GPU timings, or the content of E1's committed smoke records.

## 1. The D101 list

Everything on the list is present. Two items from my own E1 review are missing:
- **The grid-edge limitation is not stated.** The wall-follower and random walk won at grid edges, so the blind baselines may be under-tuned.
- **No engine equivalence check is declared** (AGENTS rule 7). The config hash guard checks the configuration, not behaviour. `rollout.py` changed, and `world.py` changed twice.

One item is done wrongly: see must-fix 1.

## 2. Shaping

The formula is sound, and I found no way to game it.
- **Arrival always wins within an episode.** An unfinished leg has d1 > 1.5, so progress ≤ 1 − 1.5/d0 and the bonus is at most about 0.47. Arriving adds 1 and resets progress to 0.
- **Parking is not possible.** Coming within the radius is an arrival.
- **Nothing accumulates.** `final_progress` reads the final position only, and the leg start is always defined (`world.py:560-568`).
- **The bound is per episode, not per genome.** Averaged over 8 worlds, a genome with no arrivals can outrank one with an arrival. That is the intended signal, but the text should say so.
- **c = 0.5 is reasonable.** Among zero-count genomes any c > 0 gives the same ranking, so c matters only when trading arrivals against progress across worlds.
- **The likelier attractor is blind search,** as in 02, in both arms. The cue and baseline rules catch it.

## 3. Batching and independence

I found nothing in the code that couples runs.
- **Streams are per run:** initialisation, breeding generator and world schedule (`evolve.py:121-128`). `breed` consumes only its own run's generator.
- **Row layout is consistent:** `strain_of` and the flattened ids agree in `_play`, and chunking slices rows correctly.
- **The world draws no random numbers during ticks.** Its only generators are the per-world map and target streams (`world.py:411, 493`).

Two gaps:
- **Independence is tested only with the fake simulator.** The real-simulator test checks that a strain gets the right targets, not that its scores are unaffected by its batch-mates.
- **Failure is coupled.** One non-finite strain stops all 8 runs of its batch, and a crash in batch B blocks the evaluation of batch A's 8 runs.

## 4. Champion and generation-0 baseline

Both are fair.
- **Selection over 41 checkpoints biases the validation mean, not the hold-out.** A lucky early pick makes passing harder, so the error is conservative.
- **64 worlds is thin.** The standard error of the mean is about 0.3, so the choice among late checkpoints is mostly noise. 256 worlds would cost about 10 minutes in total.
- **The champion is chosen by mean, but the rule likely to bind is reliability.**
- **Generation 0 is best-of-32, not an equal-budget random search.** Rule 4 shows improvement over the start, not that the optimizer beats sampling.

## 5. Rules and outcome

- **Thresholds:** the per-run rules are the design's, and I would keep them. In practice rule 1 implies rules 2 and 4, so reliability and the cue are the binding rules.
- **Multiplicity:** no correction is needed. Within a run the rules are a conjunction, and six false passes are implausible.
- **S-const as a gate:** no. Reference only, as D101 agreed.
- **"At least as often as not" is an overclaim.** With 6 of 12, the exact one-sided 95% lower bound on the pass rate is about 0.25. Supporting a rate of at least 0.5 would need 10 of 12.
- **Missing:** the no-information contrast (real − constant) with its bound, which I raised in E1's review.

## 6. Budget and guards

- **The arithmetic checks:** 9 498 + 164 + 192 + 60 ≈ 9 900 s.
- **Whether 1 000 generations is enough is unknown.** No evolution has run on Task N. "Under this budget" is honest framing, but a "not passed" will be ambiguous.
- **Guards:** adequate where tested. The untested paths that matter are must-fix 3 and 4.

## Must-fix

1. **Genome files against the connectome rule.**
   - The evaluation requires every candidates file committed and pushed (`e04a.py:424-425`).
   - Checkpoint 0 of each file is an unevolved genome, and E1's config initialises anatomically (`gate.json:28`).
   - D028 measured such genomes as 100% proportional to the connectome's weights. `test_publication_hygiene.py:68` would fail.
   - The same applies to a module whose champion is checkpoint 0, and to any unmutated elite that survives from generation 0.
   - **Fix:** pre-commit by hash only, which `train-X.json` already carries. Regenerate generation-0 genomes from the seed and verify the hash. Commit genome files only after the hygiene check.
   - I am unsure whether early checkpoints (generation 25 or 50) pass D028's recovery measure. Measure before committing.
2. **Text that disagrees with the code.** Registered text cannot change after binding.
   - §8 names `train-A-candidates.npz` and `train-A-final.npz`. The code writes `genomes/runNN-candidates.npz` and a local, uncommitted `runs/e04a/runNN-final.npz`.
   - "Applies every rule mechanically": the projection limit is not enforced. `cmd_train` never reads `projection.json`.
   - §7's "> 8 192" rule differs from `equivalent_k` when the curve is not monotone.
   - "Never used for selection": the validation worlds select the champion.
3. **Enforce and test the projection guard.** `cmd_project` has no test.
4. **`require_committed` is never exercised.** It is skipped under `--smoke`, guarded or not. It first runs at formal batch B, after batch A's data exist.
5. **Bind the E1 inputs.** `freeze.json` and `gate.json` set the gating baselines and the config check, but are neither in `GUARDED` nor hashed.
6. **Reword the outcome.** Drop "at least as often as not", and report k of 12 with its exact interval.
7. **Commit the development records** (AGENTS rule 5). The 4.749 s is in untracked `runs/e04a-smoke/projection.json`. I found no record of the 3 s and 2.2 s timings.
8. **Declare and run an engine equivalence check** against E1's engine on non-reserved ids.

## Suggestions

- **Add a real-simulator independence test** within one composition: swap a batch-mate's worlds and genome, and check the strain's counts are unchanged.
- **Pre-declare the rerun rule for crashes** (same seeds, from scratch, once), rather than amending after partial curves are visible.
- **Write the gating verdict before the non-gating extras.** Today a crash in a replay or module save voids a completed evaluation.
- **Run a short, disclosed pilot evolution on smoke ids** (about 15 minutes) before binding, or pre-declare a plateau descriptor.
- **Add to §10:**
  - the grid-edge limitation;
  - the best-of-32 baseline;
  - the per-episode bound;
  - that the module carried to E3 is selected on the hold-out, so E3 should re-measure it on fresh ids.
- **Note the tie-breaking.** Ties go by index, which matters in the unshaped arm.

## Checked in the code

- seeding, id ranges, the checkpoint count (41) and champion rule;
- the rollout's per-strain ids and chunking;
- `final_progress` and its bound;
- `run_rules` and `outcome_of` against §6;
- the cap clock and the accounting path;
- the guards' order in each stage;
- `.gitignore` and the hygiene test;
- the budget arithmetic.

**04a pre-registration: revise**