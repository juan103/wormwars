**Verdict: publish.**

One limit on what I verified: this session has no shell, so I could not run either `git diff`. I checked the working tree at 798148f, page by page, against the sources each fixed line cites. Every fix named in D283 is present and correct, and I found no new error.

**Checked against sources, item by item:**

1. **ROADMAP "Where things stand"** (`ROADMAP.md:15-34`). The unevolved-duplicate control is E-G at generation 0, as `docs/E4/E4-DESIGN.md:233` defines it, and E-G was scored in the pilot (D259) and in E4-D's check (D280). Only the selector-removed control is listed as not run, matching v3's three controls at `ROADMAP.md:503`. Question 2's wording matches the record: the within-module cut was called infeasible in the v1 reviews and replaced in design v2 (D243, `DECISIONS.md:7793-7811`); the training contrast and the acute interventions went with the dropped formal run (D258); the pilot's X+ arm was lost at its cap. Shared dependence exists in the design (`E4-DESIGN.md:202`) and nothing records it running. The pruning protocol is dated D144 at `ROADMAP.md:505`. "Later biology questions (below)" resolves to `ROADMAP.md:604`. Bridge 1's deferral is at `DECISIONS.md:2182` (D077). No Track E README mentions null graphs or shuffles, so "no Track E experiment has run on null graphs" holds.

2. **Survey v2** (`ROADMAP.md:31-32`, `647-648`). Nothing outside ROADMAP and DECISIONS mentions the survey, so "nothing here cites it" is true. The new wording claims only that the corrections cannot be checked here.

3. **The 03m line** (`ROADMAP.md:275-276`). "Possible, not planned" is kept with the dated note that it is next in Track B, consistent with `ROADMAP.md:11` and `307`.

4. **README** (`README.md:710-713`). Machine catches are now "for example", naming D106 and D279. D279 (`DECISIONS.md:8615`) says the failure was found by checking CI after the push, so calling it machine-caught is correct. The 2026-10-14 entry (`README.md:60-62`) marks the pilot and pre-registration as reaching main on 10-15 and cites D269-D274, which are the precheck, pilot and binding.

5. **Review trail** (`docs/REVIEW_TRAIL.md:130-133`). The three episodes it names match their rows: 16 (Linux CI), 27 (the script's disjointness test), 46 (the formal run's generator raising). D279 sits outside the table as a process lapse. "Seventy-seven episodes" matches the last row.

6. **AGENTS rule 6**. The dated correction quotes the replaced "CPU runs repeat exactly" and cites D202 and D218, both of which are the CI-on-Linux decisions.

7. **E3b-1's README** (`experiments/E3-ab-organism/E3b-1/README.md:99-105`). The comparator question is narrowed with E3b-2's finding that the latch's switching is still in use, which matches E3b-2's summary in the top README.

8. **E4's compute figures.** `summary.json` gives 6.09 before the formal run, 2.7475 for check plus L and 0.4582 for F, summing to 9.296, so 9.30 and 3.21 are right. E4's README gives 4.20 for the main task and 25.80 remaining, which sum to 30.

**One observation, not a finding against D282 or D283:** D258 (`DECISIONS.md:8225`) says the main-task pilot, diagnostics and stage A took "about 4.4 GPU-hours", while E4's README and `summary.json` carry 4.20. D258 is a kept decision record and the living pages agree with the committed record, so nothing needs changing for this publication. A dated note on D258 would close the gap if you want it closed.