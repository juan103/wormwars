# Pre-push review: both pushes need fixes first

**Limits of this review.** I had file read and search only, no git commands. I could not read main's tree, `7c146fc:ROADMAP.md` (v2.2) or any diff, and I could not run the tests or `git ls-files`. Commit history comes from `.git/logs`. I read a sample of the review archive, not all 40+ files. I opened 03r measurement files only for their provenance lines and saw no signal values.

## Push 2: `main` (db447db)

### Blocking

1. **The Corrections entry states a withdrawn prediction as current.** It says the mirror control is "predicted to *lower* directional response… That is how experiment 03 uses it." That was design v2 only; v3 withdrew it.
   - `DECISIONS.md:1184-1185` (D051): "SH-mirror's predicted decrease is withdrawn: symmetric wiring with random weights is not equivariant."
   - `experiments/03-generation0/DESIGN.md:40-42` and `:344`: "SH-mirror has no predicted direction."
   - The entry copied D050's stale wording (`DECISIONS.md:1153-1154`).
   - **Fix:** say the control matches a generic property N2 has, with no predicted direction, and that the decrease was predicted in D050 and withdrawn in D051. db447db has never left the machine, so amending it rewrites no public history.

### Should fix in the same amend

2. **The explanation is right only for an equivariant network.** I checked the read-out: `configs/interface.yaml:59-61` and `wormwars/world.py:568` give turn = mean(SMDD, RMDD, L and R) minus mean(SMDV, RMDV, L and R). The "forbids" argument holds when wiring *and* weights are mirror-symmetric. Add one sentence that symmetric wiring with independent weights is not equivariant, as `astra.answer.md:11` in `docs/reviews/20260925-210723-03-design/` already says.
3. **The date 2026-09-26 matches nothing I can find.** The reflog puts D050's commit and the roadmap's correction note on 2026-09-25 at about 21:25 local; db447db is dated 2026-09-27. Give "found" and "published" dates.
4. **The entry says who found the error, not who made it.** The reasoning came from Fable 5.1's review, that is, from my model (`experiments/02-screening/reviews/20260925-080106-preregistration-fable/fable.answer.md:5`). Claude adopted it after checking the symmetry index, not the argument (`DECISIONS.md:895-901`). The owner's rule on AI contributions asks for this.
5. **`docs/REVIEW_TRAIL.md:29` (episode 9) still credits Fable with catching this explanation**, with no note that its rationale was wrong and no episode for D050. That is true on the roadmap branch; check main with `git show 5706c7e:docs/REVIEW_TRAIL.md`.
6. **A second, differently worded D050 correction already exists on the roadmap branch**, at `experiments/02-screening/RESULTS.md:208-214` (commit d0a3cd8). The hunks are far apart, so a later merge will probably succeed silently and leave both. The entry's "Where else" list should mention it, and one should be reduced to a pointer at merge.
7. **Correct the docstring on main now.** It is comment-only. Copy the roadmap's text exactly (`wormwars/exp02/structure.py:3-9`) so the later merge is clean. Pointing to an unmerged branch is weaker than the owner's "promptly" rule.

### Minor

- "The registered text, unchanged" quotes `PREREGISTRATION.md:118-123` verbatim but omits the covariates sentence at `:124-125`. Say "the reading's text".
- Nothing else on main needs correcting that I could identify: the README's mirror line (`README.md:29`) and `RESULTS.md:204`, `:302`, `:314` state measured facts, not the rationale.

## Push 1: `roadmap` branch

### Blocking (one docs-only commit on top; 7c146fc is untouched)

1. **The branch contradicts its own record at the moment it is pushed.**
   - `DECISIONS.md:1406-1407` (D059): replication "before anything from 03 is published".
   - `experiments/03r-replication/PREREGISTRATION.md:333` binds a README sentence that "a full replication was run before publishing".
   - `ROADMAP.md:9-11` calls 02b "not yet public" and says one statement "must be reconciled… before publication". That statement is at `experiments/02b-champion-analysis/RESULTS.md:18-20`.
   - D062 (`DECISIONS.md:1547-1553`) lists the branch push but not this consequence.
   - **Fix:** add a D063 recording that the owner knowingly relaxes D059 for the timestamp, and what "before publishing" will mean in the bound README sentence. Put a status banner on the branch README, 03's `RESULTS.md` and 02b's `RESULTS.md`. Reword `ROADMAP.md:9-11`.

### Should fix soon

2. **`ROADMAP.md:22` overstates with "proves".** GitHub's receipt time shows the text was public at time T; that results came later rests on local records. State what those records show. I verified:
   - a sampled measurement carries `git_commit` 7c146fc with `code_dirty: false` (`runs/exp03r/measures/SH-recip-1050000.json:40635-40636`);
   - no `N2*` file exists in `runs/exp03r/measures/`;
   - N2 runs last (`scripts/exp03.py:608-617`).

   Also state whether any interim 03r value has been inspected.
3. **`ROADMAP.md:15` is wrong.** "94 of the 96 most critical N2 neurons" should be 96 targets: 12 neurons in each of 8 champions, with repeats (`02b RESULTS.md:143-144`). D062's four corrections missed this.
4. **`experiments/03-generation0/RESULTS.md:21`** says everything was fixed before any N2 measurement. It does not say this rests on local commit dates. Only the roadmap and D062 say so.
5. **The carried-over example contradicts 03's design.** `ROADMAP.md:273-274` suggests "a reward for staying away from food"; `DESIGN.md:165-168` rejects avoidance because it can be solved by not moving.

### Minor

- `ROADMAP.md:8`: the sign is reversed (it is dorsal minus ventral), the wrong text is in the pre-registration rather than the write-up, and "not yet public" goes stale with push 2.
- **Data:** `graphs_manifest.json` holds names and hashes; `ensembles.json` and `pilot.json` hold summary statistics and signal values. I saw no edges in what I sampled. Graph arrays sit in `runs/exp03*/graphs/*.npz`, ignored by `.gitignore:6,20`.
- **02b carries connectome-derived facts** the hygiene test does not look for: per-neuron `interface_edges` counts (`kept_edges.json`), four named connections (`RESULTS.md:129`) and degree percentiles. They cannot reconstruct the graph, but the rule says "in any form" (`ROADMAP.md:224`), so the owner should decide knowingly.
- **Personal data:** I found no email, username, home path or credential in text files. `D:/Claude/random/wormWars` appears 185 times in 19 Astra review files, including 02's. `DECISIONS.md:1050` mentions the owner's ChatGPT plan.
- Push the named branch only, never `--all`: local refs include `refs/codex/...`.

### Operational risk to the live run

- **Do not check out main in this directory while 03r runs.** Amend db447db in a separate worktree; `git push origin main` needs no checkout.
- **A resume from HEAD will be refused.** `check_resumable` compares the commit (`scripts/exp03.py:176-182`), and HEAD is already past 7c146fc. Resume only from a checkout of 7c146fc.

## The three questions

- **Does publishing 03 harm 03r's integrity?** No. The code and outcome wording are bound and the run is automated. The 03r pre-registration itself quotes 03's headline (`PREREGISTRATION.md:9-12`, `:25-26`), so publishing it alone would show the number without its caveats. The risk is how it is read, which the banner handles.
- **Does the timing claim hold?** The central statement is accurate. Fix "proves" and add the state at push time. Confirm with `git diff 7c146fc roadmap -- experiments/03r-replication wormwars scripts configs` that nothing bound changed. Tagging 7c146fc is a reasonable optional extra.
- **Are D062's four corrections right?** The first three check out against 03's `RESULTS.md:160`, `:210-214`, 02b's `RESULTS.md:21-26` and the 03r pre-registration `:133`, `:157-158`. I could not verify which model ran the session. The carry-over section is consistent with D045, D047 and the 03a draft (`DRAFT.md:581-591`), but I could not compare it with v2.2 itself.

**Push 1 (roadmap): push after fixes.**
**Push 2 (main): push after fixes.**