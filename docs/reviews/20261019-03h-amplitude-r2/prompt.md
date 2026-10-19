You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are confirming, read-only, the fixes to 03h's exploratory amplitude check (HEAD 26c580f on `roadmap`, plus the
uncommitted `scripts/e03h_amplitude.py` and `tests/test_e03h_amplitude.py`). This is round 2. In round 1 (run
20261019-180156), both said "revise".
- **Fable's findings:** the guide's error rates and the ratio's range; the engine guard to include the driver and the
  bank; the pilot's staleness check before compute; float64 level deciles; keep the realised counts; graph names in
  the record; an optional CUDA smoke.
- **Astra's findings:**
  - (high) the stop wording exceeds the statistic;
  - relief − level and sham − level, to tell benefit from sham damage;
  - the guards' coverage, and the pilot validated before compute;
  - an undefined ratio must not give "stop";
  - missing ledgers, and the end-of-run overrun flags.

**What changed** (see the script's docstring and code):
- **The guide** is now a heuristic for the rank route only:
  - "under 1 at both" reads "the rank route is not supported at these amplitudes; this does not show that random
    brains cannot use the bit";
  - "2 or above" needs the mean to have grown faster than the SD from 0.25;
  - an undefined ratio goes to the owner;
  - three flags mark discordant evidence;
  - the error rates at three graphs are stated: true 0.8 reads 2 or above about 19% of the time for one amplitude,
    19-35% for the larger of two; true 2 reads under 1 about 7% of the time. They come from a non-central t with 2
    degrees of freedom;
  - the ratio is reported with its 90% chi-square range.
- **The readings:**
  - on the selection bank, over all genomes, relief − sham, relief − level and sham − level, each with a shared-world
    interval;
  - the realised counts and graph names are kept;
  - 0.25 is recomputed from the pilot's hash-checked arrays, with the pilot's own interval quoted.
- **The guards, all before any GPU work:**
  - `require_same_code` over the driver's `CODE` (the library, the driver, the configs, the requirements, DESIGN,
    PILOT and the committed inputs);
  - the pilot's records directory is in the dirty check;
  - `P.read("pilot")` must hold, as a completed pilot at 0.25 with a current chain;
  - every upstream hash is recorded;
  - the ledgers are required;
  - the level decile is the pilot's own.
- **The end of the run:** `over_cap_at_end` and `over_own_budget_at_end`.
- **The tests:** 9 pass. Sabotage checks failed as expected for:
  - the cap counting the pilot;
  - the budget refusal before the record moves;
  - the pilot check placed after the record moves.
- **A CUDA smoke preflight** (`--smoke --device cuda`) completed in 43 s.

**Please:**
1. For each round-1 finding of yours, say whether the fix is correct and complete.
2. Name anything new that would mislead the owner's decision, with file, line and severity.

Verdict first: "run" or "revise". Keep it short: this is a confirmation. Do not edit files or run anything.
