# Review of 04a's results (commit 5312475, roadmap)

The run followed the registration and the verdict stands. The table and every headline number in RESULTS.md match the records. The prose has several errors and two overclaims, all text-only, and because 5312475 is already pushed they belong in a dated Corrections section, as E1's did (D101).

## 1. Did the run follow the registration?

Yes, with one letter-level difference to disclose.

| Stage | Ran at | Pushed (local reflog, UTC) | Start marker (UTC) |
|---|---|---|---|
| Binding | `e3d68be` | 21:28:46 | |
| Projection | `e3d68be` | | 21:49:12 |
| Batch A | `7ec22bb` | 21:51:00 | 21:51:13 |
| Batch B | `75307a3` | 23:18:08 | 23:18:19 |
| Evaluation | `2b9ed94` | 00:39:49 | 00:40:01 |

- **Order and push:** every stage's HEAD was pushed before its marker. This is the local reflog, not GitHub's push log.
- **Same code and environment:** all four stages record a clean tree and identical Python, numpy, torch, CUDA, GPU, connectome, config and E1 input hashes. The guards chain `e3d68be` → `7ec22bb` → `75307a3` → `2b9ed94` over the guarded paths. I could not run `git diff`; I rely on the guard code and the completed records.
- **Ids, seeds, compositions:** all as registered. Hold-out 996 301 000-996 302 023, validation 998 000 000-255, seeds 1 105 000-015, c = 0.5 for runs 0-11 and 0 for 12-15, compositions (256, 8, 1) and (8, 256, 1). The padding count equals exactly 64 neural arms, so the hold-out arms were padded.
- **Champion selection:** I re-derived all 16 as the first maximum of 41 validation means. All match, including the hashes in the extras.
- **Rules and outcome:** `run_rules` matches §6, and the bootstrap is E1's function line for line. 8 of 12 gives "04a: passed". I checked the Clopper-Pearson bound by hand: 0.39.
- **The difference:** the guarded smoke run ran on `9531aaf`, after the formal projection, not on the binding commit as the registration's order says. The code is the same, so it is harmless, but `guarded-smoke.json` still says "on the binding commit".

## 2. Are the numbers right?

**Correct:** the 16-row table, the baseline means, all quoted bound ranges (1.03, 0.80-1.32, 1.73-2.70, 1.22), the decoy shares, 0-19 zero episodes, 23-32% of the oracle, equivalent k 3.5-6.9 (two recomputed by hand), path efficiency and leg times, champion generations 175-950, the replay check, agreement with E1's gate within 0.06, and 2.91 GPU-hours.

**Wrong:**
- **Training curves.** "About 1.5-2.1 by generation 100" fails for runs 9 and 11, which were at 0.74 and 0.51. Run 11 stayed below 1.0 until generation 300. "Within about 1.5-2.9 afterwards" omits dips to 0.84-1.4 in most runs.
- **Timing.** "Training ran at 4.8-7 s" does not match the logs. No generation took under 4.6 s, and 592 of 1 000 (A) and 865 of 1 000 (B) took under 4.8 s. Batch averages with checkpoints were 5.20 s and 4.88 s.
- **README.** "About 2.1-2.8 targets" should be 2.0-2.8; the range is 1.99-2.81, and its own "23%" is run 5 at 1.99.
- **D110.** "The projection (9531aaf)" is the commit holding the record; it ran at `e3d68be`.

## 3. Is the reading fair?

- **Reliability with means of 2.1-2.3:** fair. A leg takes about 100 ticks, so 2-3 legs fit in 300. The rule is a point estimate, though: run 4 passes by 13 episodes (833 against 820), about one standard error. A lower-bound version would give 7 of 12, so the verdict does not hinge on it.
- **Uses the cue:** supported by both probes and the decoy capture. **"Steer" and "like a stereo steerer" are not.** The probes cannot separate stereo steering from temporal comparison. The records point away from the k = 4 steerer and towards M-avg:

| | Mean | First arrival | Median leg (ticks) | Path efficiency |
|---|---|---|---|---|
| Champions | 1.99-2.81 | 0.98-1.00 | 86-116 | 0.27-0.34 |
| Stereo steerer, k = 4 | 2.18 | 0.92 | 80 | 0.48 |
| M-avg | 2.18 | 1.00 | 117 | 0.42 |

  Six of 16 champions are below M-avg's mean. RESULTS.md lists M-avg but never uses it, and the README drops the performance-equivalence caveat. This matters for E3, which takes the module as a left-right cue follower.
- **"Slow navigators":** fair, and slightly understated. The champions' path efficiency is no higher than the blind baselines' finished legs (0.27-0.32), though those are rare, lucky legs.
- **Unshaped arm:** "4 of 4 passed without shaping" is a fair existence statement. The README's flat "Shaping was not needed: the unshaped arm did as well" drops the "descriptive, 4 runs" qualifier. All four unshaped runs were also in batch B.
- **Module for E3:** run 2, by the registered rule, with the optimism caveat stated. Correct.

## 4. Must-fix

All text; add as dated corrections quoting the original.

1. Correct the training-curves sentence.
2. Correct the timing sentence.
3. README: 2.0-2.8.
4. README: qualify the shaping bullet (4 runs, descriptive, one batch).
5. Qualify the mechanism wording in RESULTS.md and README: say the probes do not identify the computation, restore the caveat, and report M-avg beside the champions.
6. Replace "No deviation" with the guarded smoke run disclosure.
7. D110: dated correction of the projection's commit. Its "replayed exactly" should read "reproduced every per-world count" (rule 6).
8. Before main: ROADMAP.md still says "Nothing has run on 04a's validation, hold-out or training worlds", and the root README still says "Next on the roadmap: 04a".

## Suggestions

- State the run 4 margin and that a lower-bound rule would give 7 of 12.
- Report the generation-0 zero share per run (0.78-0.97), which §7 registers as reported. Three generation-0 baselines (runs 2, 4 and 13 at 1.08, 0.96 and 1.00) already beat K's 0.90.
- Give the decoy medians (2.4-4.1 cells to the decoy, 12.8-14.9 to the target) and note chance is about 50%.
- Note that hold-out means are within 0.08 of validation means, so selection optimism was small.
- The named compute parts sum to 2.894 h; the rest of 2.91 h is the extras and start-up.
- README "Reproduce it": mention `--device cpu` for readers without CUDA.

## What I checked, and did not

- **Read:** RESULTS.md, README, PREREGISTRATION.md, AMENDMENTS.md, the four start markers, `projection.json`, `compute-record.json`, `evaluation-extras.json`, `evaluation.json` (rules, means, gain curve, secondary measures), both training records (specs, all 656 checkpoint means, generation-0 logs, timing counts), `guarded-smoke.json`, `scripts/e04a.py`, `wormwars/registration.py`, `wormwars/e04a/evolve.py`, E1's `lower_bound` and `secondary`, E1's RESULTS.md, D100-D110, and the local reflogs.
- **Not done:** I could not run anything. The bootstrap bounds are not recomputed; I checked every mean difference I sampled by arithmetic and that the bounds are consistent with plausible standard errors. I did not tabulate the full count distributions, open `evaluation_events.npz`, verify the 44 MB size, or diff the commits.

**04a results: fix**