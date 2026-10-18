You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing research code and a short plan in the repository you can read (read-only): **03a's bounded search
check**, at commit 1877a05 on branch `roadmap` (DECISIONS.md D314). This round is short, and it gates about 1 GPU-hour.

## Context

- In the last round (`docs/reviews/20261018-03a-pilot-dev-results/`, D313) you both reviewed pilot-dev's results.
  Both of you recommended option (b): a bounded check of the search on MIP/URXL, within pilot-dev's remaining 1.42
  GPU-hours, followed by pilot-check only if the refits become reliable and recovery is above chance, and otherwise
  (c), stop.
- The owner chose (b).
- The plan is `experiments/03a-self-consistency/PILOT-DEV.md` §7 (v3.2). It merges your two proposals:
  - Fable's per-edge lesion;
  - Astra's fixed-state re-evaluation at 16, 32 and 64 worlds;
  - four search variants: V1, three offspring at 32 worlds; V2, a colder ladder; V3, one chain at 64 worlds; V4, one
    chain at 32 worlds with the best offspring confirmed on 64 fresh worlds.
  - The decision rule maps the variants to outcomes (i), (ii) and (iii).
- **Choices Claude made that neither of you specified:**
  - the variants' exact numbers;
  - the single chain's temperature, 0.01;
  - "reliable" = restoration equivalent or above, and refit SD ≤ p/2;
  - "recovers" = enrichment p < 0.05/4 (Bonferroni over the variants);
  - no random-partner refits in the variants.
- **The code:**
  - `stage_search_check`, `_lesion`, `_lesions`, `_reeval`, `_check_outcome`, `_check_projection`, `_variant_cfg` and
    `DEV["check"]` in `scripts/e03a.py`;
  - `ConfirmedExchange`, and `ReplicaExchange.tell` split into `_scored` and `_advance` (meant as code motion only),
    in `wormwars/e03a/search.py`;
  - the tests at the end of `tests/test_e03a_search.py` and `tests/test_e03a_script.py`.

## Please

1. **Will the check answer the question it is for?** That question is whether a feasible change to the search
   restores MIP/URXL reliably with its true partners and finds them above chance.
   - Is any variant mis-specified or wasted?
   - Is the rule sound? Consider the thresholds, the multiplicity, and three refits for an SD.
   - Is anything missing that you would need in order to read outcome (ii) or (iii) afterwards?
   - Say if you would change a number. The check runs once, and is not repeated.
2. **Bugs** in the new code that would waste the hour or mislead the record. In particular:
   - `ConfirmedExchange`'s two-phase ask/tell inside `run_lockstep`;
   - whether the `tell` split preserves the original behaviour and random draws exactly;
   - the re-evaluation's world draws and its truth block;
   - the lesion (gap edges included);
   - the projection's episode count.
3. Anything in PILOT-DEV §7's wording that overstates what the check can show.

Answer with a verdict first: "run it" (possibly with small fixes) or "revise". Then numbered findings, each with file
and line and a severity. Do not edit files or run anything.
