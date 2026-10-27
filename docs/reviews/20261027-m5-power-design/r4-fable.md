**Verdict: revise, narrowly. No further round needed; the pilot may run once the three items under Q1 are in.** The departure from "exactly" is justified, and I checked the mechanism rather than take the diagnostic's word for it. But the composition check as coded does not yet test the claim the tolerance rests on, and a tolerance failure has no registered remedy.

## Q1. The tolerance: accepted, not the full replay, with two additions

**The mechanism is real and the full replay would buy nothing the continuation uses.** `locate_and_reach` calls `System.newton` (`scripts/memory_m2/equilibria.py:45`), which solves on a shrinking active set with batched `solve_ex` (`:60`, `:65`), and the compact continuation drops finished strains from its batch (`pilot.py:239-242`). Both make the float64 fields depend on who else is in the batch. The float32 hold never reads any of it: `continue_hold` takes only `end` (`m4e.py:359-368`), and `extend` passes the first-pass `y` through unchanged. So replaying every target in its original composition for 10 to 12 CPU hours would reproduce classifier fields bit for bit that do not feed the 100,000-tick result. Decline it.

One correction to the prompt's cost reasoning: M4e's second pass runs in chunks of 128 of `who` (`m4e.py:428-434`), not the panel's whole second-pass batch. The conclusion stands either way.

**Addition 1: the composition check must compare the float32 state across compositions.** As written, `composition_check` (`m5_pilot.py:278`) replays the chunk and compares its classifier outputs to the record. That proves this machine reproduces M4e within composition (rule 6), which is necessary. It does not prove what the tolerance rests on: that the pilot's batch of 2 or 3 ends in the same float32 state as the chunk. That claim lives only in the diagnostic log for one T genome and in a synthetic-panel test, and for Rr, a new graph, nowhere. Add to the check: replay the panel's targets as the stage will (`replay`), and require `torch.equal` on `end` and array equality on `tail` and `y` against the chunk's, per arm. One extra batch per arm, about a minute each.

Recommended beyond that, the owner's call: do the state comparison for every target's first-pass chunk, hold only, no classifier. The expensive part of the 10 to 12 hours is the classifier (about 150 s per chunk against 50 s for the hold in the diagnostic log). Roughly 60 to 80 chunks at 50 s is about an hour, and it makes "the continuation starts from M4e's state" verified on every genome rather than on one per arm.

**Addition 2: pre-register what happens when the check fails.** The composition dependence is not only last-bit rounding. The line search's `r1 < r0` (`equilibria.py:76`, `:82`) and `solve_ex`'s `info` (`:66`) are hard branches, and the (b) targets are exactly the genomes sitting on them: Newton failures, marginal roots. A flipped branch moves a root distance by order one, or changes the reason, with the state identical. Across about 100 targets and two passes that is not negligible, and the code's only response is a stop (`m5_pilot.py:274`) with the remedy to be chosen after seeing data. Register now: on a failure of the registered check, run `m4e.classify_panel` for that panel (M4e's code and composition, about 17 minutes); if it reproduces the record bit for bit for that genome, the discrepancy is the classifier's composition dependence, both values are recorded and the stage continues; if it does not, the stage stops. The same rule for a class or reason flip, which for these genomes is the more likely form.

**Addition 3, wording.** The plan's (c) says the first pass's outputs "must be reproduced exactly" (plan line 114) while the code applies the tolerance (`m5_pilot.py:434`). The `replay` docstring says a genome's first pass is "tested identical alone" (`:237`); it is not, and T1 says alone differs, which is why the companion exists. Both are the claim-versus-evidence slips round 3 was about.

## Q2. The round-3 fixes

Checked against the code, all present and right:

- **Records validated** before use and on resume: `panel_record` runs `m4e.validate` with the rebuilt digest (`:301`); `validate_rr` now checks genome ids and second-pass column lengths (`:144`, `:154`); `check_out` guards resume and reading (`:319`, `:353`, `:418`, reader `:117`).
- **Output guard** (`:37`): M4d, M4e and `m4e.OUT`. M2's folder is not covered; minor.
- **Companion** (`:230`, `:240`), recorded in `batches`; the smoke shows `[465, 0]`.
- **Paired variance** (`m5_pilot_read.py:41`): Astra's formula, correct and non-negative by construction; the independent split beside it (`:94`). `p11` is pooled over host-draws rather than within panels; at these rates that is the sensible choice.
- **Incomplete stages**: partial s and r reported with "not applied: incomplete" (`:158`); the reader no longer raises on a missing panel.
- **100,000-tick contrasts** (`:221-226`), **denominators** (`counts`, `:70`), **reasons** at both horizons, **phase timings** (`:383`, `:440`), **three overlaps** (`:119-121`). The smoke's overlap numbers equal Astra's round-3 figures to five places, a good cross-check.

Small gaps, none blocking:

- Paired T × Rr tables exist only at 22,000; Astra asked for them at 100,000 too.
- `max_root_deviation` is stored per stage file but not surfaced in `report.json`; the results note will want to quote it.
- `check_out` does not re-run `check_replay` on a file's stored `recorded_*` against `replayed_*` at read time, so the reader trusts the writer. Cheap to add.
- The reader's `contrast` and `main` have no test. Before the pilot, run `contrast` on M4e's T and K and confirm the independent split reproduces M4e's published shares. It costs nothing and is the only end-to-end exercise that code will get before results depend on it.

The counts in the prompt check out: 19 dots in `runs/pytest-m5-pilot.txt`, 21 of 21 sabotages failing by their own tests' checks, and no NaN in any of M4e's 160 arm records, so the float comparison in `check_replay` will not trip on one.