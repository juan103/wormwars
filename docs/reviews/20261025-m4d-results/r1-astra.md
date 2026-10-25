**Verdict: fix then publish.** The planned reading is correct, and the after-the-data impossibility argument is valid. I found reporting errors and overinterpretations, not a reason to rerun M4d.

I independently reproduced the reading from all 70 panel records, including both interval envelopes. I also ran the regeneration checks: hosts, blocks, sham genomes, arm hashes and panel validation passed. The write/read summaries reproduce, and the companion’s source list matches M4c’s 141 genomes. No files were modified.

Findings, ranked:

1. **The explanation of “unconfirmed candidate” is wrong.**  
   [Results line 113](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:113) describes this as “a second root located but not confirmed.” In [the classifier](/D:/Claude/random/wormWars/scripts/memory_m2/classify.py:95), it is an **oscillation candidate** that failed the period/persistence confirmation, after locating roots without a stable/marginal-root veto. It is not evidence of an almost-confirmed second stable state.

   This matters to the proposed resolution work: these cases are not simply unfinished bistability confirmations. Also replace “most” with “the largest first-reason category”: R has 18/36 and Rr 17/36. The recorded reasons are alphabetically sorted, so the first reason is not necessarily the principal diagnostic failure.

2. **The companion’s “95% lose the switch” needs correction and narrower interpretation.**  
   [Lines 170–172](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:170) combine three problems:

   - The 282 observations are **two redraws of 141 genomes**, not 282 distinct genomes.
   - N2 selected has **13 separate states, 268 fading and one unresolved**. Calling all 269 remaining classifications losses incorrectly resolves that last case.
   - “Depends on far more than the core’s own parameters” suggests an extent of dependence that this joint redraw cannot identify.

   Suggested replacement: “Across 282 genome–exterior trials, 13 classified as separate states, 268 as fading and one remained unresolved. Retaining these core parameters was usually insufficient to preserve switching under the tested exterior redraws.”

   The point ratios are correct: 13/6 ≈ 2.17 and 25/10 = 2.5. Present them as descriptive ratios. Add the host companion’s unresolved counts—**three selected, ten control**. For perspective, only **12 distinct donor genomes** switched in at least one N2 redraw; one switched in both.

3. **Several descriptive conclusions overstate what the comparisons establish.**  
   In [the interpretation bullets](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:131):

   - **P versus T:** “pooled frequencies are close” is accurate. “Moving the weights … changes little” is misleading without that qualification. Only **one host/genome pair** is classified as separate states in both arms: 63 are T-only and 68 P-only. Weight placement changes which genomes switch substantially. The frequency interval, −0.00346 to +0.00249, also allows differences substantial relative to these base rates.
   - **T+G:** replace “add nothing here” with “did not increase the counted pooled frequency.” An interval containing zero does not establish no effect. The 50 unresolved cases in each arm further limit that interpretation.
   - **Rr below R:** the observed counts and the one-draw caveat are correct. Avoid implying that preserving reciprocity generally reduces switching. As an additional descriptive check, the Rr−R hull is **−0.00489 to +0.00098**.
   - **Ladder shares:** one third and four fifths are arithmetically correct: 20/60 and 48/60. The existing warning against separable causal attribution is appropriate. Explicitly condition these shares—and the opening “rewired copies get most of it”—on **counted separate states**. They are not robust shares over unresolved assignments.

   The write-measure interpretation is otherwise appropriately restrained. Specify that these are pooled medians, and that the silent-share denominator is **separate-states genomes above the floor**, not all eligible genomes. All zero-write counts are zero; reporting that would complete the planned diagnostic.

4. **Correct the provenance claim and distinguish verification from a fresh rerun.**  
   [“Clean tree at start and end”](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:38) is not supported by the attempt record. [Accounting](/D:/Claude/random/wormWars/wormwars/accounting.py:236) records cleanliness of `wormwars`, `scripts` and `configs` **at the start**, and the commit hash at the end. It does not record whole-tree cleanliness at either end or code cleanliness at completion.

   Say: “Code/config directories recorded clean at start; the commit hash was unchanged at completion.”

   The reproduction command also needs clarification. On a checkout containing these panel records, `m4d.py` validates/skips existing panels; it does **not** repeat 26 hours of simulation. Document separately:

   - checking the published records, including regenerating local `blocks.json`;
   - a fresh run using a new `MEMORY_M4D_OUT`, with coverage produced before its arms.

   `m4d_tables.py` currently hardcodes the original output directory, so document that limitation or make its destination configurable.

5. **Fix the smaller reporting and plan-wording issues.**

   - [Line 85](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:85): “10,240 genomes each” should clearly mean **per arm across ten hosts**, with 1,024 per host.
   - The panels total **90,532 seconds = 25.14778 hours**. Report 25.15 hours, or 25.1 to one decimal, rather than 25.2.
   - The **260 edges and weight 2347 exclude autapses**. Say “260 off-diagonal chemical edges, plus eight autapses.” Including autapses gives 268 entries and weight 2379.
   - Restore the minority-response parenthetical in the quoted second reading at lines 15–16. The plan explicitly requires that limitation wherever an exclusion reading is printed.
   - Separate the robust direction of T−I from its counted rate: 0.625% is the counted pooled T rate; assigning its unresolved cases can raise it to 1.113%.

The remaining displayed counts, percentages, per-host cells, descriptive contrasts, medians, host/block ranges and compute totals checked out.

**On the reading itself:** my independently calculated values are:

| Contrast | Mean | 90% hull | Unresolved envelope |
|---|---:|---|---|
| T−I | 0.005859375 | [0.004791936, 0.006926814] | [0.004632480, 0.012499875] |
| T−R | 0.001171875 | [−0.000874436, 0.003218186] | [−0.005356504, 0.008695436] |

These give exactly the saved **“Unresolved (the unresolved genomes decide it)”** under the plan. The counted single-host maxima are below the guard. The envelope permits larger host differences, but its reading is already unresolved.

The additional impossibility proof is sound **for the fixed classifier outcomes, integer reassignment of unresolved cases, and fixed bootstrap procedure**:

- At the all-for-T endpoint, the bootstrap lower bound is **0.00400390625**, but the Student-t lower bound is **0.00365591706**. The hull therefore fails the positive criterion.
- Every other attainable difference vector lies componentwise below that endpoint with at least one host reduced by 1/1024.
- Using the same resampling indices, bootstrap quantiles are componentwise nondecreasing. The largest lower bound among those ten one-genome-down vectors is **0.00390625**, below the margin.

Thus no assignment can produce a positive reading. Because T−I’s envelope lower bound exceeds the margin, the no-transplant-effect reading is also impossible. The remaining categories are the second reading and unresolved. Print enough digits to make the endpoint’s strict comparison understandable. This proves inability to satisfy the positive decision rule; it does **not** exclude a true wiring advantage of 0.004.

**On `blocks.json`:** keeping it local is the right decision under repository rule 1. I verified that the summary matches every corresponding local statistic and chain record, and that its SHA-256 matches the local file. The ignore rule works.

The summary supports aggregate checking; it cannot independently establish exact degree/out-strength preservation or edge placement. Those checks require the legitimately obtained source data and deterministic regeneration. That is an acceptable reproducibility arrangement. Add an explicit comparison against the published digest before regenerating tables, since the tables script otherwise overwrites the summary.

`hosts.json` contains within-C3 degrees of the **generated null graphs**, not N2’s original C3 degree vectors. These are structural summaries, but they do not reproduce N2’s adjacency or edge weights. I found no edge-list or anatomical-weight payload in the proposed M4d publication files.

**For the next step, I recommend option (b): publish the corrected unresolved screen and take the direction decision to the owner with both reviews.** Resolving the 86 cases could establish an exclusion, so it is not scientifically worthless. But it cannot unlock the positive branch while the resolved classifications remain fixed, and the corrected diagnostic shows that many cases concern unconfirmed oscillations rather than merely unfinished root finding.

I would prioritize the M1–M4 synthesis, with a separately planned density/degree study if the owner wants that question pursued. Do not treat accepting the screen as accepting the second reading: the wiring advantage remains unresolved. A bounded resolution study becomes worthwhile if the owner specifically needs the exclusion at 0.004 to make a consequential next decision; it should remain a separately planned, explicitly after-the-data follow-up.