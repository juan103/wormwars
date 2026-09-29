**fix** — the headline readings are correct. The interpretation overclaims, and the prose omits required statistical qualifications. No rerun is warranted.

Must-fix items:

1. **Mechanism claims exceed the probes.** [RESULTS.md:71](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/RESULTS.md:71), lines 176–182; [README.md:8](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/README.md:8); [D136:3963](D:/Claude/random/wormWars/DECISIONS.md:3963). Replace “no champion uses/steers by the left-right difference” with **“no champion meets the plan’s ‘uses the left-right difference’ criterion.”** There are 43 distinct champions classified “no material benefit” and four unclear, including detectable benefits. “They do not benefit from intact bilateral input” is also too absolute. Preserve “a non-stereo plateau” explicitly as the plan’s operational reading.

2. **The basin and ceiling claims are unsupported.** [RESULTS.md:176](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/RESULTS.md:176), especially lines 183–197. These records establish neither a common basin nor why random sampling approached the GA, and certainly not that the module is “near its ceiling.” Random sampling’s median is **1.64**, versus approximately **2.17–2.32** for the read sets; only **35/47** distinct champions lie in the fixed 1.90–2.50 band. The low-gain controller demonstrates probe sensitivity at that performance, **not representability or evolutionary reachability within the brain’s parameterization**. Describe sensing, interface, shaping and seeding as hypotheses to test.

3. **Report the bootstrap/sign-flip disagreements required by PLAN §Part C.** [RESULTS.md:126](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/RESULTS.md:126) and lines 146–151. C1’s positive bootstrap interval accompanies **p = 0.125**; the interaction’s negative interval accompanies **p = 0.1484375**. Both disagreements are already recorded in `evaluation.json`. Add the other arm p-values and the omitted interaction sensitivity result: **without run 2, −0.140206, 90% interval [−0.314453, +0.007394]**. “Not claimed” is correct; it should not obscure the negative estimate.

4. **Correct and qualify run 2’s role.** [RESULTS.md:133](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/RESULTS.md:133). Its contribution to total paired gain is **80.6% for C1, 49.9% for C2, 64.1% for C4**; “most of each” is false for C2. Moreover, C1/C4 already have nonzero generation-0 observations under their 32-world evaluations. Distinguish this changed initial selection signal from C2’s rescue of the original zero-scoring start. C2’s remaining seven runs all improve: its qualified reading reflects failure to reach **+0.3**, not disappearance of the gain.

5. **Correct the ledger total.** [RESULTS.md:169](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/RESULTS.md:169): the attempts sum to **14,036.101790 seconds**, rounding to **14,036**, not 14,037. The latter sums the rounded rows. **3.90 hours remains correct.**

6. **Restore Part A’s proxy qualification.** [README.md:26](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/README.md:26): 54% correct/16% tied comes from resampling shared **hold-out worlds for distinct champions**, not measuring actual training comparisons. State that distinction.

Because these statements are committed, record the corrections with a date and quoted original wording, as AGENTS.md requires.

For E3, my suggestions are:

- **Gentler mutation is a defensible operator lead.** Retest it with fresh paired seeds, separating failed-start avoidance from improvement among successful starts.
- Retain the narrow noise conclusion. C0 is **0.81864**, only 0.01864 above threshold; parent-specific rates span **0.746–0.866**. At half/quarter mutation, pooled rates are **0.79420/0.77170**. Evaluation effort could matter differently after changing mutation.
- Treat C3’s zero run as evidence of a conditional escape problem, not a universal requirement for larger σ. Longer ES runs remain promising, with additional checkpoint opportunities disclosed.
- Test stereo representability before attributing failure to search. Otherwise, use the selected module with its measured limitations.

What I checked and found correct:

- Recomputed Part B’s world means, bootstrap intervals, classes, set medians and readings; all control checks pass. Budget gain is **+0.242920**, interval **[+0.119507, +0.379285]**.
- Recomputed C0’s bins, mutation statistics, overlaps, ES signs and reference errors.
- Recomputed every arm and combined contrast:

| Arm | Mean gain, all 8 | Without run 2 | Plan reading |
|---|---:|---:|---|
| C1 | +0.221802 | +0.049107 | inconclusive |
| C2 | +0.432007 | +0.247349 | supports, carried by run 2 |
| C4 | +0.304443 | +0.125000 | supports, carried by run 2 |
| C3 | −0.157349 | +0.106306 | inconclusive |

- No arm leaves the plateau; qualifying champion counts are respectively **0, 2, 0, 1**. Interaction “not claimed” is correct.
- Verified Part A regeneration, matched-reference selection, recorded pairing, both replay matches, source hashes, unchanged runner/engine/plan, nine completed attempts and episode accounting. C3’s 622 perturbation generations remain zero; E2’s ES first scores at generation 52.

No files were modified; I did not rerun GPU work or independently verify historical remote push times.