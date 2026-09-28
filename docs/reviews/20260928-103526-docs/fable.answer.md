# Documentation review: WormWars `roadmap` branch

**Verdict: ready with fixes.** The experiment numbers and the registered wordings are accurate. The problems are in the reproduction procedure for 03/03r, the new ROADMAP status block, and several AGENTS.md rules that overstate.

**Limits of this check.** I had no shell, so I ran nothing and could not use `git show`. I read 03r's historical code from the on-disk worktree `../wormWars-03r-binding` (HEAD `7c146fc`). I could not read code at `132acae`, `225e8f8` or `971bbb3`.

## Must fix

**1. 03 and 03r: the documented rerun sequence fails at step 2.**
- Where: `experiments/03-generation0/README.md:151-158`, `experiments/03r-replication/README.md:171-178`.
- Step 1 runs `rebuild-graphs --into ../wormWars-03/runs/exp03/graphs`, which creates that directory (`scripts/exp03.py:295`). Step 2 is `git worktree add ../wormWars-03 132acae`, which git refuses when the path exists and is not empty.
- The 2026-09-28 check (D087) verified the rebuild, not this sequence.
- Fix: add the worktree first, then rebuild into it from the current checkout.
- Also say in 03's README to copy `supplement.py` into the worktree only after `run`. In current code the dirty check covers `experiments/03-generation0` (`scripts/exp03.py:160-163`), so an untracked file there would make `run` refuse.

**2. `ROADMAP.md:15` cites a file that is not committed and holds known-bad numbers.**
- `docs/foundations/T1_profile.json` is untracked (`??` in git status).
- The copy on disk records commit `e8faf26`, before `a7836c5` fixed "the first full run's post-profiler timing was 4x slow".
- Its `levers.S32_B160` block shows that artefact: "current" 21.6 ms, with apparent speed-ups of ×2.8 to ×5.5 (lines 603-661).
- Fix: rerun at `a7836c5` or later, commit the result, then cite it.

**3. `ROADMAP.md:15-16`: "On 02's task the brain's matrix products dominate" is not what the profile shows.**
- `bmm` is 70% of GPU kernel time (`T1_profile.json:543`).
- The world's share of tick time is 0.55 on 02-T1 and 0.70 on the Task N proxy (lines 423, 464).
- Fix: state those numbers instead of "dominate".

**4. `ROADMAP.md:25-26` misstates 03a's gap.**
- It says 03a "needs about 2.5 times more than the best found, which is ×1.36".
- The sources say ×2.5 over measured throughput, with the best exact lever at ×1.36 (`docs/foundations/T1.md:104-105`, `DECISIONS.md:2468`).
- The on-disk profile gives ×1.35 at R = 4 (190.5 / 140.8); ×1.36 comes from the scratch run that `T1.md:28-30` says is to be replaced.

**5. Padding is not in this branch.**
- `ROADMAP.md:18` says single-strain padding "is implemented"; `AGENTS.md:68` says "T1 adds padding for new work".
- `pad_single_strain` does not exist in `wormwars/` here. It exists only in the local worktree `../wormWars-t1` (branch `t1-padding`, no remote ref).
- Fix: say it is on a working branch and not merged.

**6. `ROADMAP.md:5` says the section below "is kept as written on 27 September". It was not.**
- That section contains 28 September content (`:44`, `:53`, `:59`), and D082/D083 record edits to it.
- It still says 02b is "not yet on main" (`:32`) and D050 "is prepared" (`:31`).
- Fix: correct the header, or update the two stale lines.

**7. `README.md:31`: "one more graph would have reversed the verdict".**
- "Reversed" is a registered verdict label in 03 with a different meaning (`03-generation0/PREREGISTRATION.md:183-184`).
- One more SH-route graph would have given "not distinctive" at Holm 0.070.
- Fix: use "would have failed it".

**8. `README.md:352`: "`PLAN.md` … (milestones 0-9)".**
- `PLAN.md` has milestones 0-12: 0-11 done, 12 deferred. 01's README (`:22`) says M0-M11.

**9. AGENTS.md rules that are false or overstated as descriptions.**

| Location | Claim | What the repository shows |
|---|---|---|
| `AGENTS.md:23`, `README.md:285` | Every script writes a run bundle | Only `evolve_forage`, `coevolve`, `experiment` and `exp02` call `write_bundle`. `exp03.py` stores per-measurement provenance instead. |
| `AGENTS.md:71-72` (rule 8) | Scripts run inside accounting | `watch.py`, `showcase.py`, `bench_scaling.py` and `bench_brain.py` do not. Accounting dates from T0 and is absent from 03r's binding `exp03.py`, so the published GPU-hours are wall-time sums. |
| `AGENTS.md:52-56` (rule 2) | Pre-register before running; a bound pre-registration is never edited | 01 has no pre-registration and 02b is exploratory. 02's was amended after evolution started (`02-screening/PREREGISTRATION.md:68`, `:296-313`, D041). 02's and 03's carry later annotations. |
| `AGENTS.md:59-60` (rule 4) | Every correction gets a DECISIONS entry | C3 and C4 have none; `docs/REVIEW_TRAIL.md:22` records only "C4". |
| `AGENTS.md:75-77` (rule 10), `README.md:108` | Reviews are archived; "the reviews verbatim" | 01b's D033 review is "kept outside the repository" (`DECISIONS.md:640-641`, 01b README `:163`). |

- For rule 2, the accurate statement is: registered text is never changed or removed, and dated notes are added beside it.
- Rule 2 also omits the standing rule to push before the run (`ROADMAP.md:238`), and that 03 and 03r did not meet it.

## Should fix

**10. `README.md:116-117`: "Every verdict is computed from committed files".**
- True for 02: `report` reads committed files (`scripts/exp02.py:600-605`).
- For 03/03r, `report.json` lets an outsider recompute rank counts and p-values. The margin gate, SEs and effect intervals need the uncommitted per-genome measurements.
- The same wording appears at 03 README `:142-143` and 03r README `:163-164`.

**11. 02's rerun uses `git checkout` in the main clone (`02-screening/README.md:170-176`).**
- The outputs become untracked files that the current branch tracks, so checking the branch out again will likely be refused.
- I could not confirm what `971bbb3` tracks. A worktree, as in 03, avoids the problem.

**12. Softened caveats.**
- `README.md:88-92` gives 03r's push timing but not 03's: its pre-registration was first pushed after its run (03 README `:99-101`).
- 03r README `:41-42` drops the registered point that a systematic implementation error would also replicate (`03r-replication/PREREGISTRATION.md:67-70`).

**13. Quoting and rounding.**
- `README.md:29` capitalises inside the quote. The registered label is "challenged: no meaningful N2 use" (`runs/exp02-screening/analysis.json:2241`).
- `README.md:59, 65, 67, 76` use 0.047 beside 0.0155. `report.json` and the experiment READMEs use 0.0465. I would use 0.0465 throughout.
- `DECISIONS.md:2298` says "about 0.08 after Holm". `03r-replication/RESULTS.md:146-147` and the READMEs say 0.072. The READMEs are right; D081 needs a dated note.

**14. Rebuilt graph files.** Add one sentence to both READMEs: they carry permuted anatomical weights, so do not commit or share them. `--into` can point outside the ignored `runs/` tree.

## Verified clean

- **03r's outcome sentence** is exact at `README.md:32` and `:42-43`, 03 README `:25-26`, 03r README `:18-19` and `ROADMAP.md:44`, against `PREREGISTRATION.md:315`.
- **The probe caveat** is verbatim, and the D063 amendment matches `DECISIONS.md:1570-1573`.
- **02's verdict and prediction, and 01b's three predictions**, match their sources, apart from the capitalisation in item 13.
- **Numbers** in all seven READMEs match their `RESULTS.md`, `report.json`, the frozen 01 record and `DRAFT.md`.
- **Commands in current code:** every subcommand and flag exists, with the stated defaults (`exp02.py:627-628`, `experiment.py:55, 64`, `exp03.py:719-725`).
- **Commands at `7c146fc`:** `run` and `report --instance 03r` exist, and `supplement.py` is identical to the current one.
- **Named tests and the three tags** exist.
- **Privacy:** no email addresses in the new files. Repository-wide, the only addresses are noreply ones, in two archived review prompts already on main.
- **Local paths:** `remeasure.py:11-12` hard-codes `D:\Claude\random\wormWars`, which 03r's README discloses.
- **Connectome:** no connectome data, and no instruction that would redistribute it.

Docs: ready with fixes — (1) worktree before `rebuild-graphs` in 03 and 03r; (2) rerun and commit `T1_profile.json`; (3) replace "dominate" with the measured shares; (4) correct the ×2.5 / ×1.36 sentence; (5) say padding is unmerged; (6) fix the "kept as written" header or the stale lines; (7) replace "reversed the verdict"; (8) milestones 0-11; (9) narrow AGENTS.md rules 2, 4, 8, 10, line 23 and `README.md:108, 285`; then items 10-14.