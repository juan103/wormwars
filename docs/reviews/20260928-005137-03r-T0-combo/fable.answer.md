# Second opinion: 03r results (revised) and T0's GPU checks

**Checked:** the revised files, D059, D063, D080, D081, pre-registration §9-§10, `report.json`, the script, `T0_gpu.json`, the attempt records in `runs/t0-gpu/compute/`, `rollout.py` and `accounting.py`.

**Not checked:** I cannot run anything, so the test suite, the input hashes, and how `runs/remeasure-03r.json` was produced are unverified.

## A. 03r results

**My earlier points are resolved**, apart from the README items below. Astra's points are resolved too.

The new numbers match `report.json`:
- **P3 noise:** N2's SE is 0.01197, and exactly 3 of the 768 ensemble graphs have one as large (0.01199, 0.01232, 0.01332).
- **Variants' P3, N2-rev's invalid P1 and the added secondaries** all match.

### Must fix

1. **The README's lead sentence overclaims** (`README.md:23-24`).
   - **"A full replication confirmed it"** contradicts §10 ("not an independent confirmation") and the README's own "Not independent evidence". Use "reproduced it" or "replicated".
   - **"More than any of five null wirings do"** reads as individual graphs. One graph sits at or above N2 in each run. D063 made this same correction to 03's conclusion: say "unusually high relative to all five null ensembles".

2. **Pre-registration §9 is not addressed.** It says "any mid-run code change means re-measuring every graph". Code changed in the working directory during the run, including `scripts/exp03.py` (D069), yet `RESULTS.md:233` says "Otherwise none".
   - I accept the substance. The process never reloaded, there was no resume, and the two latest-measured graphs re-measure bit for bit.
   - But it belongs under Deviations, naming §9 and saying why the rule was not triggered.

### Should fix

3. **The README gives P3 only its exploratory p.** It omits the registered label ("reversed against every ensemble") and its Holm p of 0.0465. §10 requires the label, so give the label first and the caveat second.
4. **The README shows 03 under one rule only.** §10 asks for both runs under both rules. Add 03's P4-alone p (0.0155) and say P4 alone is the registered primary for 03r only.
5. **`runs/remeasure-03r.json` is local and carries no provenance.** It has no commit, device, date or list of arrays compared. Commit it beside the results with those fields.
6. **"It could not reach the already-loaded process"** (`RESULTS.md:61-62`) is stated as fact. The evidence is two graphs, so write "did not, as far as checked".

### Minor

- **The noise-aware p:** −0.02368 / 0.01197 is 1.98 SE, which gives a one-sided p of 0.024 and 0.072 after Holm under a normal. The text says 0.027 and 0.08. State the calculation.
- **"One more graph"** (`README.md:42`, `:47`) should name the ensemble: SH-route in 03, SH-class in 03r.
- **"Effect sizes are close"** (`README.md:49`) quotes N2's values, not effect sizes.
- **Ensemble descriptions:** SH-route caps direct food read-out edges rather than "keeping its food routing", and SH-mirror also carries the routing cap.
- **The probe caveat** is a paraphrase of §10's quoted words. Use them exactly.
- **Details line:** add D081.
- **`supplement.py`** lives in `experiments/03-generation0/`. Give the path.
- **`ROADMAP.md:36`** still reads "03r tests the first link. If it replicates…".

## B. T0's GPU checks

The exact results stand on the JSON: 9 historical replays, the 3-generation regression, the identity checks and the replay-mode repeats. The interpretation of the exceedance is plausible but not yet honestly complete.

### Must fix

1. **A second declared check failed, and D081 does not say so.** `replay_mode_chunking_identical` is false in all six cases, with the same maxima as default mode.
   - **T0.md §2 and §4 are false on CUDA as written.** §2 claims any `chunk_worlds` gives the same scores "in each execution mode's own terms", and §4 claims exactness under `replay_mode()`.
   - **The plan's fallback claim is unavailable.** "Replay within X only under replay_mode" does not hold, because replay mode does not rescue chunking.
   - **What to change:** a dated amendment to T0.md, and the same qualifier in the `replay_mode` section of `REPRODUCIBILITY.md`.

2. **The follow-up that carries the interpretation is not recorded.** There is no script and no output file, and `T0_gpu.json` pools repeats and chunking into one statistic. What is committed disagrees with the wording:
   - **"3 of 512 worlds differed":** the 99th percentile of 1 536 values is 1.19e-07, so at least 16 differ. Presumably 3 exceed the bound. Say that.
   - **"A few worlds":** in the 600-tick champion case the 90th percentile of 384 values is 0.0083. If repeats are identical, at least 38 of 128 worlds differ by more than 0.008.

3. **The run has no usable code provenance.**
   - `accounting.attempt` reads the commit in its `finally` block (`wormwars/accounting.py:219`), so it records HEAD at the end, with no dirty flag.
   - The CUDA quick run ended at 22:29:18Z recording `43f6faa`, a commit whose script had failed at 22:25:31Z with the generator error. So it ran an uncommitted fix.
   - The full run started 36 seconds later and records `bb2f245`. `T0_gpu.json` itself records no commit.
   - **What to change:** record commit and dirty state at the start, then rerun from a clean tree. It takes 13 minutes.

### Should fix

4. **"More than one strain" is a generalisation.** With 16 worlds, the chunk sizes tested give 4, 16, 32 and 32 strains per chunk. Two and three strains per chunk are untested, and so is a remainder chunk of one.
5. **The cause is stated as fact** in `REPRODUCIBILITY.md:30`, and as "likely" in D081. It is testable in one step: compare `torch.bmm` at `brain.py:388-389` for a batch of one against the same strain inside a batch of two.
6. **`REPRODUCIBILITY.md:42-47` now conflicts with the evidence.** Default-mode repeats were identical and 600-tick historical replays were exact. Say the nondeterminism was not observed on this setup, and is not guaranteed absent.
7. **The ledger bound and finiteness were never checked on CUDA.** None of the T0 test files mention CUDA, and the script compares only scores. `rollout` already returns `ledger_rel_error`, so recording it is free.
8. **Historical replay ran at current code.** T0.md §4.3 declared the original code version. The result is stronger, but it is a deviation to state.
9. **600 ticks is 01b's real episode length,** not only a stress test. 01b's final scores are single-strain evaluations in every condition, so I see no bias, but say so.

### Minor

- **"To 6 decimals"** understates it: the differences are exactly 0.
- **The regression** covers 3 generations of one run, and the JSON has no pass field.

### Does the gate pass, and what remains

The exceedance alone does not block, by the plan's own rule. The gate still does not pass, because of must-fix items 1 to 3. Before T0 closes:
- fix the accounting provenance and rerun clean;
- commit the follow-up, with repeats and chunking separated, 2 and 3 strains per chunk, and a remainder of one;
- amend T0.md and `REPRODUCIBILITY.md`;
- add the CUDA ledger check;
- state the test result at the closing commit.

Before T1 starts, two more things:
- **A guard or padding in `rollout`,** so tuning chunk size cannot silently create single-strain chunks.
- **A T1 equivalence tolerance declared with this finding in hand.** A per-world bound of 1e-4 at 200 ticks cannot survive any kernel change. Use bit-identity at fixed composition, a short-horizon bound, and an aggregate one.

03r results: not yet
T0: not yet