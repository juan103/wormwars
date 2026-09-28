# Confirmation pass: documentation at `eba1c3e`

**Verdict: not yet, but close.** My earlier points are resolved except two that the fixes left incomplete (AGENTS.md rules 2 and 10), and the profile file is still uncommitted. The 01b correction, the ROADMAP numbers and all four rerun recipes check out.

**Limits of this check.** I had no shell, so I ran nothing and did not see `git show eba1c3e`. I read the working tree plus three on-disk worktrees: `../wormWars-main` (the old README), `../wormWars-03r-binding` (code at `7c146fc`) and `../wormWars-t1` (padding). I could not read code at `132acae`, `225e8f8`, `971bbb3` or `7b26c87`, and I did not re-add 01's 2.66 hours.

## 1. My earlier points

| # | Point | Status |
|---|---|---|
| 1 | 03/03r: worktree before `rebuild-graphs`; `supplement.py` after `run` | Resolved (03 README `:154-172`, 03r README `:173-187`) |
| 2 | `T1_profile.json` untracked | Open by design (D088, `DECISIONS.md:2611-2612`) |
| 3 | "dominate" | Resolved (`ROADMAP.md:17-20`) |
| 4 | ×2.5 / ×1.36 | Resolved in `ROADMAP.md:29-31`; not in `T1.md:103-105` (item D below) |
| 5 | Padding unmerged | Resolved (`ROADMAP.md:21-22`, `AGENTS.md:77-78`). `pad_single_strain` is absent from `wormwars/` here and present in `../wormWars-t1` |
| 6 | "kept as written" header | Resolved (`ROADMAP.md:5`, `:36`, `:37`) |
| 7 | "reversed the verdict" | Resolved (`README.md:31`) |
| 8 | Milestones | Resolved (`README.md:359`) |
| 9 | AGENTS.md line 23, rules 4 and 8, `README.md:292` | Resolved |
| 9 | AGENTS.md rules 2 and 10 | **Partly** (items A and B below) |
| 10 | Verdicts from committed files | Resolved in 03/03r READMEs (`:145-149`, `:165-169`). Main `README.md:119` now says "checked", which is acceptable |
| 11 | 02 rerun in worktrees | Resolved (02 README `:169-186`) |
| 12 | Softened caveats | Resolved (`README.md:92-94`; 03r README `:38-39`, `:42-44`) |
| 13 | Quoting and rounding | Resolved; D081 note added (`DECISIONS.md:2299`) |
| 14 | Do not share graph files | Resolved (03 `:179-180`, 03r `:193-194`) |

**The declined 0.0465.** I accept it. `report.json:2336` holds 0.046511…, which rounds to both.

## 2. The areas you named

**01b headline correction: correct.**
- The quoted old line matches main exactly (`../wormWars-main/README.md:103-104`).
- The new line matches 01b `RESULTS.md:3-6` and D033 (`DECISIONS.md:651-653`), including "not detectably different".
- It says "final score" where RESULTS says "final held-out score"; the table directly below supplies the term.

**ROADMAP numbers against the current profile file: all match.**

| Text | File | Value |
|---|---|---|
| bmm "about 70%" of kernel time | `T1_profile.json:543` | 0.701 |
| World "about 55%" on 02-T1 | `:423` | 0.553 |
| World "about 70%" on the Task N proxy | `:464` | 0.701 |
| Batching "about 1.35 times" | `:98`, `:136` | 190.5 / 140.8 = 1.35 |

- The file on disk is still the `e8faf26` run (`:3`). Its `levers.S32_B160` block still shows the ×2.8 to ×5.5 artefact (`:603-661`).
- After regenerating, re-check "the largest candidate" against that block as well as the three shares.

**03/03r procedures: work as written, checked at `7c146fc`.**
- `GRAPHS` is `runs/exp03[r]/graphs` (`exp03.py:45, 54, 81`), which matches `--into`.
- The dirty check covers `wormwars`, `scripts`, `configs`, the experiment folder, `pilot.json` and `remaps.json` (`:159-161`). Graph files under `runs/` do not trip it.

**02/02b procedures: consistent with the code at `7c146fc`.**
- `OUT` is relative to the working directory (`exp02.py:40`), and genomes sit flat in it (`:354`, `:519`), so both `cp` lines do what they say.

**AGENTS.md rules 4 and 8: true.**
- `attempt`, `recorded` and `run_script` exist (`accounting.py:197, 259, 270`), and the drivers call them (`exp02.py:633`, `exp03.py:730`, `experiment.py:254`, 02b `analyse.py:458`).

## 3. Must fix before main

**A. "01b's review is the one kept outside the repository" is false** (`README.md:110-111`, `AGENTS.md:87-90`).
- Astra's 2026-09-24 roadmap review, which found the reversed synapses, is cited as `Astra6/reviews/2026-09-24-roadmap-v1.md` (`experiments/02-screening/reviews/20260925-003052-design-v1/prompt.md:24`).
- `.gitignore:56-59` excludes `Astra6/` as "not part of the published record".
- Reviews before 2026-09-24 were relayed by the owner (`docs/REVIEW_TRAIL.md:13-14, 21, 26`). The earliest archived review is 02's design v1, 2026-09-25.
- I named only D033 in the first pass, so part of this is my miss. The fix then turned it into a uniqueness claim.
- Fix: say reviews from 2026-09-25 on are archived, and that 01's reviews, the 24 September roadmap review and 01b's are not.

**B. Rule 2's push exceptions are probably incomplete** (`AGENTS.md:59-64`).
- Only 03 and 03r are named.
- 02 was designed, registered, run and reviewed before publication at `5706c7e` (`DECISIONS.md:998`).
- 01b was registered and run at the same commit, `5161e76` (01b README `:3-4`, `:156`).
- I cannot prove push times from files. Verify them against GitHub.
- If confirmed, say the push rule dates from 27 September and no run so far met it.
- `AGENTS.md:47-48`, "the exceptions are named", promises completeness. Soften it to "known exceptions".

**C. Regenerate and commit `T1_profile.json`,** then re-check `ROADMAP.md:17-20` and `:29-31` against it.

## 4. Should fix

**D.** `T1.md:103-105` still says "largest exact candidate" and "×1.36". Its own table says "Not yet known" (`:80`), and the ROADMAP now says 1.35 with exactness untested. T1.md reaches main for the first time with this push.

**E.** `ROADMAP.md:7-10` lists 02's D050 correction under D085. It went to main on 27 September (D063, `DECISIONS.md:1625`).

**F.** 03r README `:189` is still headed "The graph files come first." The worktree now comes first.

**G.** `ROADMAP.md:17` says "02's task". The profile is 02's task T1 (`t1_profile.py:13, 70`).

**H.** `README.md:292-293`: "its output" should be "their output".

**I.** Confirm that `225e8f8`, `971bbb3`, `7b26c87`, `132acae` and `7c146fc` are reachable from `origin/main`. Otherwise `git worktree add` fails in a fresh clone.

**J.** 02b README: on other hardware, regenerated genomes are paired with the original tracked `probes.json` scores in the `response` stage. One sentence would cover it.

Docs: not yet — (A) correct the review-archive claim in `README.md:110-111` and `AGENTS.md:87-90`; (B) verify and complete rule 2's push exceptions in `AGENTS.md:59-64`; (C) regenerate and commit `T1_profile.json`, then re-check the ROADMAP's figures against it.