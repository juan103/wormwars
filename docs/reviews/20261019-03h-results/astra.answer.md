**revise**

Checked the working files at `a322cf9` on `roadmap`. Static inspection only: no project scripts or tests were run, and no files were changed.

1. **High — “No 03h brain ran on N2” is false.**  
   [RESULTS.md:5](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:5), repeated at line 216, both READMEs and ROADMAP. The equivalence checker explicitly pins **N2**, creates random genomes, and performs T1 rollouts with both interfaces: [e03h_equivalence.py:15](/D:/Claude/random/wormWars/scripts/e03h_equivalence.py:15), implementation at line 93. The committed CPU and CUDA equivalence records document those comparisons.

   Replace the blanket statement with: **“N2 was used for engine-equivalence checks, but not for 03h’s history–fitness or relief comparisons.”** This preserves the relevant scientific limitation without misreporting what ran.

2. **High — The headlines turn uncertain scenario calculations into an established inability to detect N2.**  
   [RESULTS.md:16](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:16), lines 36–39 and 210–211; [experiment README:20](/D:/Claude/random/wormWars/experiments/03h-history-use/README.md:20); [ROADMAP.md:15](/D:/Claude/random/wormWars/ROADMAP.md:15); [root README:38](/D:/Claude/random/wormWars/README.md:38) and line 54.

   “Could not separate,” “could not be tested,” and “had almost no power” are stronger than the records establish. These are Gaussian **rank-component scenario rates**, fitted to three graphs, with assumed N2 variability. They neither calculate complete-B power nor establish the ensemble tail. RESULTS lines 149–150 correctly acknowledge this, contradicting the headlines.

   Likewise, **U = 0 is an assumed favourable scenario, not an established “strongest plausible effect.”** U compares separately selected deciles under sham and relief; nothing establishes U ≤ 0 for N2. The record itself includes U > 0 scenarios.

   Suggested wording: **“Exploratory Gaussian scenarios suggested poor sensitivity of B’s rank component if N2’s relief–sham contrast were zero; N2’s response and full-B power were not measured.”**

   Also, “0.5%–34% depending on assumptions” omits the upper-SD scenarios: [b-power.json:43](/D:/Claude/random/wormWars/experiments/03h-history-use/development-records/b-power.json:43) records zero simulated successes for one of them. Either identify the selected scenarios explicitly or report the full simulated range, without treating zero observed successes as zero theoretical probability.

3. **High — The history–fitness conclusion repeats an overclaim already corrected in D330.**  
   [RESULTS.md:41](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:41), lines 212–213, and the corresponding README/ROADMAP summaries.

   “The size of the history held does not predict fitness” is precisely the generalisation [D330:10268](/D:/Claude/random/wormWars/DECISIONS.md:10268) retracts. The supported result is a **near-zero mean partial Spearman association of the specified H, conditional on S, in these SH samples**: −0.023628, with six positive graphs. No negligible-association margin was tested; DESIGN explicitly disallows that conclusion.

   H_dir’s +0.062490 and 14/16 are correctly reported, but describe an exploratory association among five readings, conditional on shared worlds. Prefer **“H_dir showed a weak positive association”** over the categorical “its direction does [predict fitness].” The “Not shown” section should explicitly exclude causal use of history as memory and mediation of any N2 advantage.

4. **Medium — Two important decisions made after seeing data need explicit disclosure on the page.**  
   [RESULTS.md:40](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:40) and [RESULTS.md:160](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:160).

   The page identifies the owner’s amplitude-check and stopping decisions, but does not clearly explain that **the owner made B the sole planned confirmatory claim and demoted A after seeing step 0**, following the direction review. D330 records this and the resulting removal of Holm’s stricter threshold.

   It also omits D338’s explicit statement that the amplitude check was **outside PILOT.md’s amplitude rule**. The registered escalation required the 0.25 shift not to move; it did move. State that the owner nevertheless commissioned an exploratory 0.5/1.0 check, whose guide was fixed before that check. Calling it exploratory is appropriate but does not fully disclose the departure.

5. **Medium — Keep “barely use the bit” descriptive, and identify what the decile contrast measures.**  
   [RESULTS.md:32](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:32), lines 115 and 207–220.

   The numerical claim of a **small average benefit on these three graphs** is supported. The wording should not imply a demonstrated inability to read ASK or uniformly small responses across individual brains.

   In particular, the “best tenth gained” contrast uses **a separately selected top 26 under each condition**, not one fixed group’s treatment response. PILOT.md states this; the results page should too. The diagnostic measures a one-tick turn response, not every behavioural consequence of ASK input.

6. **Medium — “No sham damage” and the amplitude intervals need narrower interpretation.**  
   [RESULTS.md:163](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:163), especially line 175.

   An interval containing zero does not establish no damage. Write **“No ensemble-mean sham damage was detected.”**

   Add the conditioning beside the amplitude table and all-genome intervals: these bootstrap intervals resample shared worlds while holding the graphs and genome draws fixed, and the decile intervals also hold selections fixed. They are not uncertainty intervals over new graph samples.

   Explain that the “90% range” for mean/SD varies the SD using Gaussian chi-square bounds **while fixing the observed mean**. [ratio_range():170](/D:/Claude/random/wormWars/scripts/e03h_amplitude.py:170) does not construct a full confidence interval for the population ratio.

7. **Medium — “Reproduce it” is not an executable fresh-clone procedure.**  
   [RESULTS.md:260](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:260).

   Running `bind` creates a guarded record; the next stage requires it committed and HEAD pushed. That intervening step is missing. A literal checkout of `ff1fd31` also leaves a detached HEAD unless a branch is created, whereas `require_pushed()` checks `origin/<branch>`.

   The amplitude instructions additionally omit its required revision transition, handling of the existing completed amplitude record, and creation of `runs/e03h/step0/compute.json`. Rerunning the pilot alone does not create that ledger. At the current HEAD, the newly added summary script also falls within the bound `scripts` guard; the amplitude checker excludes only its own script.

   Provide a concrete reproduction branch/revision sequence, or a supported replay procedure, covering the binding, records, local arrays and ledgers. The current prose leaves outsiders to solve these guard failures themselves.

8. **Medium — The documented CPU power rerun can break the summary builder.**  
   [e03h_summary.py:122](/D:/Claude/random/wormWars/scripts/e03h_summary.py:122), connected to [RESULTS.md:258](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:258).

   Without local pilot arrays, `b_power.py` writes `"selection_bank_relief_minus_sham": null` into `b-power.json`. The summary builder then unconditionally indexes `["per_graph"]` beneath that field and fails. The two summary tests cover the committed snapshot and one numerical mutation, not this documented reproduction path.

   Make the optional-data path compatible with summary generation, or preserve the committed input and direct the power rerun to a separate output.

9. **Medium — Rounding conceals a positive interval endpoint.**  
   [RESULTS.md:172](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:172), and [summary.json:404](/D:/Claude/random/wormWars/experiments/03h-history-use/summary.json:404).

   The 0.25 all-genome relief–sham lower endpoint is **+0.0000433026**, not zero: [amplitude-check.json:393](/D:/Claude/random/wormWars/experiments/03h-history-use/development-records/amplitude-check.json:393). Printing `[0.0000, 0.0012]` obscures whether this conditional interval excludes zero, which matters to the surrounding interpretation. Preserve enough precision or explicitly say it is positive before rounding.

10. **Low — One displayed per-graph value is rounded incorrectly.**  
    [RESULTS.md:166](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:166).

    At amplitude 0.5, the third graph’s shift is **0.0064502682**, which rounds directly to **+0.006** at three decimal places, not +0.007. This appears to be double rounding through summary.json’s 0.0065. The same error appears in D339’s table.

11. **Low — The review status is premature and the review counts are inconsistent.**  
    [RESULTS.md:72](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:72), line 285, and [experiment README:30](/D:/Claude/random/wormWars/experiments/03h-history-use/README.md:30).

    At this HEAD, D340 says reviewing the page is **next**, and `docs/reviews/20261019-03h-results/` does not exist. “This page has had one review” is therefore unsupported in the reviewed snapshot. Update it after archiving the reviews.

    RESULTS counts four design rounds; the README says five. If the latter includes the post-step-0 direction review, name it separately so the chronology is clear.

12. **Low — The experiment README retains a now-false statement of the original knowledge gap.**  
    [experiment README:8](/D:/Claude/random/wormWars/experiments/03h-history-use/README.md:8).

    “No file relates a genome’s history to how well it forages” is false now that step0.json and step0b.json exist. Write **“Before 03h, no file…”** and distinguish the newly measured associations from the still-untested causal memory claim.

The other quoted measurements I checked agree with their source fields: stage commits and times, accounting total **0.3489 hours**, gate scores and intervals, sham rates, pilot readings, history tables, amplitude means/SDs/ratios, and the discordance verdict. The manuscript’s main problems are inferential wording, the false blanket N2 statement, disclosure omissions and reproduction instructions—not wholesale numerical disagreement.