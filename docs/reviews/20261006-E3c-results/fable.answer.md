# E3c results review: fix then publish

The numbers are sound: I found no figure that disagrees with the records beyond two small slips. The required fixes are in the prose, which in four places says more than the registered readings allow.

I could not run code, so the permutation p-values and the bootstraps are not rerun. Everything else below was recomputed by hand from `report.json`, the stage records and `compute-record.json`.

## 1. Do the numbers match the records?

Yes, with two slips.

**Recomputed and matching:**
- **Arm means, SDs and mean d** (`RESULTS.md:80-85`).
- **Both Welch intervals:** se, df and bounds reproduce `report.json:377-382` and `:442-447`.
- **Margins and labels:** they follow from `e3c_stats.py:70-80`.
- **Exact p-values:** they are whole counts over 12 870 splits (1 276 and 674).
- **Mann-Whitney:** U is 17 for Q1 and 16 for Q2, which gives 0.130 and 0.105.
- **Holm, the L intervals, the retained-fraction differences, the cost-curve generations and medians:** all match, checked against the curves.
- **Secondary-outcome means, Spearman ranges, offsets and K_D ranges:** all match.
- **The ledger:** stage seconds give 18.70 h, and `compute-record.json:189` gives 22.65 h.
- **40 of 40 checkpoint checks.**

**The slips:**
- **`RESULTS.md:22-23`, "within 0.1 visit per wey":** the registered interval reaches −0.120 visits (`RESULTS.md:96`), and the 95% one reaches −0.109. Only the point estimate (−0.048) is within 0.1.
- **`RESULTS.md:173`, "85-92% of the maze":** run 22's coverage is 0.8448 (`report.json:7403`), so 84-92%.

**Loose wording on numbers:**
- **`RESULTS.md:116`, "excludes 0 … by about 0.05 visits":** the bootstrap interval is −0.067 to −0.032 visits. 0.05 is its centre, not its distance from 0.
- **`RESULTS.md:100`, the Holm row:** 0.152 is Holm over the Welch p-values (0.106 and 0.076, `report.json:380,445`; `e3c_stats.py:95-99`). The row sits under the exact-test rows and the Welch p-values are not shown. Holm of the exact p-values would be 0.105.
- **`RESULTS.md:72`, "all four legs":** the registered text names three (`PREREGISTRATION.md:99-100`). `g-e.json` has a fourth, the snapshot hook (`:372`). Name them.

## 2. Are the registered labels reported as registered?

The labels themselves are, but two registered attachments are missing and one sentence contradicts the registration.

- **Labels:** the margin labels, exact labels, "supported", the nose classes and "no material loss" are quoted as `report.json` emits them and follow the rules.
- **The qualifier is missing.** §7.3 says the nose-class and coverer counts "are appended to Q1's and Q2's labels, both shown" (`PREREGISTRATION.md:398-399`). They are in `report.json:418-439` and `:483-504`, but no label in `RESULTS.md` or the README carries them.
- **The decomposition is missing.** §7.1 puts it "beside each contrast" (`PREREGISTRATION.md:298-301`). It is Fisher p = 1.0 with 95% Welch intervals of [−0.0213, +0.0024] and [−0.0177, +0.2771] (`report.json:400-417`, `:465-482`).
- **`RESULTS.md:106-107` contradicts the registration.** "With no failed run, that label is calibrated under the no-failure model" is the inference §7.1 withdrew: "an observed absence of failures cannot confer that status" (`PREREGISTRATION.md:269-270`, also `:488`). The observed S spreads also differ, 0.031 against 0.070, and separate S spreads are a named unsimulated limit (`:505`).

## 3. Is anything stated beyond the evidence?

Yes, in four places that need fixing, plus the roadmap note.

- **P-sel (`RESULTS.md:240-241`; also `DECISIONS.md:7101`).** "Can also reach the from-scratch level … 3 of 4 runs" is wrong.
  - The three are at 6.14, 6.14 and 5.58; the lowest S champion is 6.59. They sit 0.5-1.1 visits below S-mod's mean, at or beyond the experiment's own 0.5-visit margin.
  - What the record supports: three runs above P-fixed by 0.46-1.03, near W2-turn (5.77). The fourth is 0.19 above the floor line.
  - "By a scent-free route" is also too strong. Runs 20-21 have K_D of 12.6 and 7.5, and all four score higher with the noses removed (run 23 by 0.57). The registered caveat (`RESULTS.md:147`) says exactly this cannot be inferred.
  - `RESULTS.md:189`, "about unchanged" with trails off, hides run 23's +0.52.
- **Q2, "similar scores" (`RESULTS.md:36`).** This reads "unclear" as near-equivalence. §1 forbids that: "'Unclear' is never read as equivalent" (`PREREGISTRATION.md:70`). The interval allows +1.57 visits.
- **Q2, the point estimate as a finding (`RESULTS.md:236`, `:115`; `README.md:8`).** "Reach a level about 0.66 visits higher" sits under "Shown", and the bootstrap gloss says "P-joint's advantage". The bootstrap conditions on these 16 champions and says nothing about run-to-run variation, which is where Q2's uncertainty lies. Say "these eight champions averaged 0.66 more".
- **Q2, the exact p of 0.052.** This is handled correctly (`RESULTS.md:111-112`). I would add the registered sentence that "no difference detected" does not establish identical distributions, since the spreads plainly differ.
- **Coverage (`RESULTS.md:238-239`).**
  - "Holds" should be "supported, a descriptive classification".
  - "And quickly" is not measured. The cost curve tracks score, and coverer status was assessed only on final champions.
- **Coverage, "different strategies" (`RESULTS.md:36`; `README.md:9-10`).** The dichotomy is cleaner than the data.
  - P-joint is 4 "partial" and 4 "nose-dependent". Runs 2-3 keep 76-84% without noses and pass the tour-match criterion.
  - Without noses, P-joint's champions score 2.85-5.96, mean 4.05, against the seed's 1.47 (`report.json:7958-9848`, `:10445`).
  - So tuning added a large nose-free component to every champion: +2.58 in that condition, against +2.21 intact. That is my own exploratory reading, but it undercuts "by navigating with their noses" as the account of P-joint's level.
  - The README's "wall-follower" and "every tuned engineered organism navigates with its noses" are not registered terms.
- **The roadmap note (`RESULTS.md:249-251`).** It is correctly labelled unregistered, but two parts are asserted without support.
  - The example is untested and doubtful on E3c's own numbers. By my rough estimate a lap takes about 700 ticks (6.67 visits at two per lap), and P-fixed needs about 470 ticks per visit. A horizon shorter than a lap leaves the navigator about one visit.
  - "E4 … is affected the same way" is an assertion. `ROADMAP.md:377-391` does not tie E4 to this task. Say "would be, if it used this task".

## 4. Is anything registered missing or mislabelled?

Nothing is mislabelled as registered. Missing, beyond the qualifier and decomposition above:

- **P-sel against P-joint** (§7.4, `PREREGISTRATION.md:406`): −1.19, −1.19, −1.75 and −4.66 (`report.json:10490-10508`).
- **§11's "how it is kept" items** (`PREREGISTRATION.md:565-575`): the common-costs note, the lineage lines and the reuse-cost scenarios.
- **R-shared against P-fixed:** it has only a table row and no sentence (3.20 against 5.12).

Two things are worth disclosing though not required:
- **W2-turn's chosen 1.4 is the grid's edge.** Validation means were still rising (5.82 to 5.95, `champions.json:1619-1622`), so 5.77 is a lower bound for that reference.
- **Nine of the 28 champions' turn offsets sit at 0.60,** apparently a limit.

**"Deviations: none"** is consistent with what I could check. By the local remote-tracking log, each stage's HEAD was pushed 3-191 seconds before its start marker.

## 5. Verdict: fix then publish

1. Correct the P-sel claims at `RESULTS.md:240-241` and `:189`.
2. Add a dated correction to D219 for "three at the from-scratch level" (rule 4).
3. Remove "similar scores" (`:36`), and reword `:236` and `:115` as sample descriptions.
4. Replace the calibration sentence (`:106-107`) with the registered caveat, and state the unequal S spreads.
5. Fix "within 0.1 visit" (`:22-23`), "85-92%" (`:173`) and the Q1 bootstrap wording (`:116`).
6. Append the qualifier to both labels, and add the decomposition beside each contrast.
7. Label the Holm row as Welch-based and show the Welch p-values.
8. Reword `:238-239`: "supported", not "holds"; drop "quickly".
9. State P-joint's mixed classes and its noses-removed scores against the seed's.
10. Align `README.md:9-10` with the registered terms.
11. Add P-sel against P-joint and §11's missing items, and name the `g-e` legs.
12. In the roadmap note, mark the example as untested and make the E4 sentence conditional.