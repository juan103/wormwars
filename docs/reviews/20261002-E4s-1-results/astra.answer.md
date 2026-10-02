**Verdict: fix.** The registered O1 and O1b conclusions stand. The main problems are stronger mechanistic wording, one damaged secondary-data record, and an unmet E3 condition.

Reviewed `roadmap` at `e9e62a7`, read-only. Both NPZ hashes match their records. I independently reproduced all 240 endpoint scores and 5,152 world-level contrast intervals.

From the counts:

| Arm | G0 mean | F mean | Mean climb |
|---|---:|---:|---:|
| M | 2.29468 | 7.14154 | 4.84686 |
| N | 0.23993 | 1.94830 | 1.70837 |
| R | 0.38159 | 3.34888 | 2.96729 |

M−N = **5.19324**, registered 90% interval **[5.05694, 5.33387]**. M−R = **3.79266**, **[3.32368, 4.24726]**. Both have all 16 differences positive and exact two-sided sign-flip p = **0.0000305176**. M’s climb interval is **[4.48094, 5.20057]**; R−N = **1.40057**. Neither companion sentence applies. The gate results, endpoint-use counts, O3 differences and **16.61322 hours** also check out.

1. **“None from the pre-registration as amended” misses a recording defect.**  
   [The endpoint writer](/D:/Claude/random/wormWars/scripts/e4s1.py:783) casts *every* returned array to `int16`, including floating-point motor measurements. For example, `M run00|F|motor1_turn` contains only zeros, whereas the JSON mean is **0.2652645**; its stored forward array also contains only zeros, against JSON **0.9955308**. Across the endpoints, **1,166 of 1,440** motor summaries cannot be recovered from their corresponding arrays. This defeats the per-world motor retention described in D152. **Correction:** disclose the loss under Deviations; distinguish retained JSON aggregates from unusable per-world motor arrays. Target counts and the registered outcome calculations are unaffected. Do not silently replace these records.

2. **“The steering stays in the graft”; “The host did not come to steer by the difference itself.”**  
   These appear in [RESULTS](/D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-1/RESULTS.md:75), the parent README and the front-page row. H tests host stereo benefit **while the module is blind**. It does not test the host’s contribution with the functioning module, and silencing the module establishes dependence, not exclusive localization. Registration §11 explicitly excludes establishing transfer of a particular computation. **Correction:** “All M endpoints classify H as ‘no material benefit’ under the module-blind assay; final performance remains strongly dependent on the graft. Transfer was not demonstrated.” Present co-adaptation as an interpretation consistent with the interventions, rather than a reconstructed learning history.

3. **“So the gain is a co-adapted host-and-module system, not a better module” is too categorical.**  
   [RESULTS:114](/D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-1/RESULTS.md:114). All five M modules that retain Mc also outperform L1 on at least one registered carrier orientation. For example, run 4 scores **6.93359 versus 5.20313** at +0.2; run 8 scores **7.11719 versus 5.15820** at −0.2. Conversely, ten M modules score exactly zero on both carriers. **Correction:** report heterogeneous carrier performance: some modules improve, most lose competence on these carriers, while their evolved whole brains perform well. Include the registered carrier-score shares; Mc’s binary count conceals this distinction.

4. **“E3’s artefact rule (§7): met” is false as written.**  
   [RESULTS:99](/D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-1/RESULTS.md:99). Section 7 requires **all three** conditions, including E3’s positive control. `report.json` explicitly says that control remains required. Run 10 is correctly selected: final validation **7.52344**, hold-out **7.54102**, O2b **1.44932**. **Correction:** “The two E4s-1 eligibility conditions are met; replacement remains conditional on E3’s positive control.” Correct D153 similarly.

5. **“Is kept and used by evolution in every run” / “all 16 runs keep using the module” overstates continuity.**  
   [RESULTS:140](/D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-1/RESULTS.md:140) and [front-page row](/D:/Claude/random/wormWars/README.md:40). The evidence concerns selected representatives at G0, F and six sampled generations. No ancestry or intervening history was traced, as §§5 and 11 explicitly state. Likewise, “no sign flips” compares saved endpoints; it does not establish that none occurred during training. **Correction:** use “selected brains use the module at both endpoints and all six sampled generations,” and “no G0-to-F edge-sign differences.”

6. **The trajectory comparison needs narrower wording.**  
   [“M passes the carrier’s 5.2 by generation 100. N stays near the plateau’s level throughout.”](/D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-1/RESULTS.md:124) M’s generation-100 mean is **5.22119**, against L1’s **5.20313 on different worlds**; no matched generation-100 carrier comparison was recorded. N starts at **0.23608**, plainly outside the plateau. **Correction:** “By generation 100, M’s mean reaches 5.22, approximately the carrier reference of 5.20 measured on other worlds. At the sampled generations from 100 onward, N averages 1.61–1.92.”

7. **The F0 gain statement hides substantial heterogeneity and the probe setting.**  
   [“Open-loop stereo gain rises from 22 … to 117”](/D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-1/RESULTS.md:128) is the **across-run mean of local \(K_D\) at \(m=0.08\)**. Final values range **9.57–428.16**; the median rises **16.81→45.47**. Two runs contribute roughly three quarters of the final summed gain. **Correction:** identify the statistic and input level, and give the median or range. “In M, U and S it stays at about 15–23” likewise describes arm means, not individual runs.

8. **“Running” is stale.**  
   The front-page introduction and E4s status column, plus the parent README’s “Extend it,” still say running. All **17 stages** record completed first attempts, all ten training batches reached 1,000 generations, and evaluation covers all 80 runs. **Correction:** “Completed; results under review,” and update the parent’s status date.

Three further observations should accompany the readings:

- **The chosen E3 candidate is specifically a whole-brain artefact.** Run 10’s module scores **0 on both carriers**; silencing it leaves **0**, and restoring L1 leaves **0.03516**. This does not invalidate its eligibility, but matters for what E3 would inherit.
- **16/16 selected endpoints does not mean population-wide retention.** Only **258/512 = 50.4%** of final M strains clear the *single* real-minus-module-mean threshold. This is not the full two-contrast “uses” classification.
- **R is more informative than “no label named” alone suggests.** **10/16** final R brains classify as users, versus **2/16** at G0, although **0/16** final R modules retain Mc. Designed signs improve performance; these records do not establish that designed signs are necessary for the whole brain to achieve the registered use criterion.

Local history supports commitment before subsequent stages and preservation of the substantive registration through its amendment. I did not independently authenticate remote push times.