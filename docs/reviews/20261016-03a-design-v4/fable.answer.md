Facts checked; writing the review now.

**Verdict: revise.** The task choice and the overall shape are sound and the budget arithmetic is right, but the primary recovery statistic as written can pass for trivial reasons (interface membership and degree), the pilot's "uses history" and "uses interneurons" checks do not test what §1 and the roadmap require, and the "separates the outcomes" reading can be met by noise. These are fixable without changing the six-neuron frame or the cap.

## Facts checked against the repository

| Claim in DESIGN.md | Source | Result |
|---|---|---|
| M-avg 2.16, K 1.03, wall-follower 0.66, oracle 8.85, S-const 8.78 (lines 44-47, 61) | `experiments/E1-navigation/RESULTS.md:87-94` | correct |
| 419-429 episodes/s in 8-run lockstep (line 49) | 04a `compute-record.json`: 4 096 000 worlds / 9 784 s = 419; E2: 6 912 000 / 16 117 s = 429 | correct (E4s-1 not checked) |
| ~1 046/s at 256 strains × 32 worlds (line 49) | E2d `projection.json` ga32: 8 192 episodes / 7.83 s = 1 046 | correct |
| 04a: 12 of 16 passed (line 53) | `04a/RESULTS.md:3-4,157-159` | correct (8 of 12 shaped + 4 of 4 unshaped) |
| 02b: 94 of 96 most critical targets touch interface neurons (line 102) | `02b/RESULTS.md:172-174` | correct (12 per champion × 8 champions) |
| `food_sensing = "mono"` reads one point for both sensors (line 38) | `wormwars/world.py:839-840` | correct, but it reads `P_FRONT_C`, the front-centre sample point, not "the head's centre point" as line 39 says; name the point |
| 256 000 episodes per evolution; 57 600 per search; totals (lines 216-226) | recomputed | all sums correct: 92.4 M episodes, 61.2 h at 420/s |
| ~245 eligible neurons (line 83) | 302 − 39 interface (`configs/interface.yaml`) − 18 non-interface pharyngeal | correct |
| SH-mirror, SH-route exist | `wormwars/exp03/samplers.py:31` | correct |
| `deletion.without_neuron` | `wormwars/deletion.py:40-46` | correct, built for exactly this |
| Motor gains "calibrated on intact brains" (line 78) | D035: calibration uses 2 048 random genomes on the intact graph | wording is misleading: random genomes, not evolved brains |

One fact the design does not use but should: E2d (`RESULTS.md:60-72`) found that none of the 47 stereo champions uses the left-right difference. Under the `mean` probe, their scores move by at most 0.18. So the stereo plateau at about 2.2 is already a non-stereo strategy. Line 53's "not known" is too weak: the mono task is very likely evolvable to about the same level, and the existing champions would be a cheap sanity check before any pilot.

## Findings

**1. The primary recovery AUC is biased upward by interface membership. Severity: high.** `DESIGN.md:106-108, 153-154`. With interface neurons in the candidate pool and a label-permutation null that is blind to strata, a target whose true partners include chemosensors or command motors (most high-tier targets, by 02b) gets enrichment from "connect to the neurons that carry the signal", which any task-driven search does regardless of X's identity. That is a prediction, but a trivial one, and the confirmatory family would pass on it. Fix: permute labels within strata (interface versus non-interface, and within interface, sensor versus motor) for the primary null, and report the whole-pool AUC as the descriptive. The §5 secondaries do this split but are not what Holm is applied to.

**2. Degree is not controlled in the null either. Severity: medium.** The draft's SC3 ("adds to structure") is gone from §7, and the structural rankings survive only as refits. The degree ranking's AUC and the mirror ranking's AUC cost nothing (no GPU) and should be reported beside every target's task AUC, with the stratified null also degree-matched (permute within degree bins). Otherwise a pass is explained by hubs.

**3. Pilot criterion 2 does not test history use. Severity: high.** `DESIGN.md:194-195`. K also beats zero and also loses under the constant probe, since it reads the level. "Beat K-mono with a paired lower bound above 0" allows a brain that is K plus a bit. Fix: a direct history probe. The `hold` probe already exists (`world.py:918-921`, `food_probe_hold`, D066): hold the reading for h ticks and the temporal derivative at scales below h disappears while the level stays. Register: champions lose a stated fraction under `hold` at a stated h, and beat K-mono by a registered margin (for example half the scripted M − K gap measured in step 1). A P4-style ramp is not needed here.

**4. The roadmap's "solutions use interneurons" has no explicit pilot criterion. Severity: high.** `ROADMAP.md:567` versus `DESIGN.md:191-201`. Criterion 4 is about NIP headroom, which shows X *can* be used after reinsertion, not that evolved solutions use it. The deletion scan is the direct measure: register "each pilot graph has at least 3 eligible neurons whose drop's lower bound exceeds p" as a criterion. Note also that τ gives every neuron memory, so "needs memory" does not imply "needs interneurons"; with all three sensor pairs receiving the same signal, a fast-τ versus slow-τ sensor pair could compute the derivative at the sensor layer. Routing (SH-route caps direct sensor-to-readout edges) is what forces interneurons, and that is why the scan must be a criterion.

**5. "Separates the outcomes" can be met by noise. Severity: high.** `DESIGN.md:161-162`. "At least two different outcome summaries among the non-excluded" is satisfied by one "inconclusive" and one anything. Require two of the three substantive outcomes (anatomical recovery, functional success with anatomy undetermined, search failure).

**6. 512 final-evaluation worlds cannot resolve the three-state scheme at p ≈ 0.115. Severity: medium.** Intact scores are about 2.3 (04a), so p is about 0.115 targets per episode. Per-world paired differences have SD about 1, so a 95% interval on 512 worlds is ±0.09. "Equivalent" then needs |diff| < 0.03 and "above" needs diff > 0.2; everything between is undetermined, and most comparisons will land there. 2 048 worlds halves the width for about 1.5 extra GPU-hours (roughly 600 evaluations × 2 048 episodes). Same point for the relevance scan: its world count is unspecified (line 85); at 64 worlds a drop's SE is about p, so register 512 or more. Both are cheap.

**7. The medium tier is likely empty as defined. Severity: medium.** `DESIGN.md:93-94`. With a plateau near 2.3 and p = 0.115, few neurons will have drops above p at all, and "above p but outside the top 10" may contain none. A cleaner partition by the same margin: high = lower bound above p (top 3); medium = interval contains p (drawn by seed); low = interval inside ±p. No arbitrary rank cut, and every eligible neuron falls in one tier.

**8. Mono input plus the one-member-per-pair rule may empty the high tier of paired neurons. Severity: medium, a risk to report rather than fix.** With identical left and right input, bilateral pairs are closer to duplicates than under stereo, so deleting one member may drop little. The high tier could then be all unpaired neurons, and 03m's leads (RIA, AIY) would be excluded by construction. The pilot will show it; add a per-graph report of drops by paired versus unpaired, and say in advance what is done if no paired neuron qualifies.

**9. The expansion reading has a non-trivial chance rate. Severity: medium.** `DESIGN.md:156-160`. A 90% interval over 3 target-brains and 5 searches undercovers (the draft itself says so for 3-6 units), and it is tried on up to 5 targets. Even under the null the MIP − NIP half of the criterion fires for at least one target around 20% of the time before the enrichment requirement thins it. State the approximate chance rate in the registration, or use 95% with the same Holm family. Also, the outcome summary's "anatomical enrichment" uses the uncorrected per-target 95th percentile (draft, line 182) while the family uses Holm; say which defines "anatomical recovery" in the outcome table.

**10. Search resolution. Severity: medium, pilot-checked.** A 16-world mean count has a resolution of 1/16 and SE about 0.2; a single edge move on one neuron will usually change the true score by less than p. Common random numbers make within-generation comparisons paired, which helps, but 100 generations with about a third of 32 offspring per generation moving a partner is roughly 1 000 partner moves to place about 20-30 partners among 280 candidates. Two cheap mitigations to register as pilot-tunable: (a) use 04a's shaped fitness (count + c × progress, c fixed) as the *search* signal while keeping the raw count for every score, which gives a continuous signal at this resolution; (b) record Q, the fraction of true partners along the trajectory, in the pilot (the draft's funnel analysis), so a weak search is diagnosed rather than inferred from criterion 5.

**11. Budget has no room for a second pilot. Severity: medium.** `DESIGN.md:213-231`. 72 − 61 = 11 h, and one pilot is 10.8 h. A ladder retune or a change to 16 search worlds after the first pilot would force the cut order before the formal run starts. Pre-cut the SH-mirror arm now (see Q3) and the reserve becomes about 35 h. Also the union-mask cost is unmeasured: 6 dense rows and columns add roughly 5 000 candidate edges to a 7 000-edge graph; on a one-wey task the world dominates (T1), so it probably costs little, but the 420/s figure was measured without it. Criterion 6 covers it; say so.

**12. Smaller points.**
- `DESIGN.md:113`: "chemical self-connections kept as in the original" — in MIP, keeping the *weight* leaks X's evolved self-weight. Keep the partner, re-initialise the weight by the partner-independent rule, as the draft did.
- `DESIGN.md:138`: "functional recovery as a fraction of the intact score" is undefined for NIP; say the denominator is the intact brains' mean and that the NIP brain's pre-reinsertion score is reported beside it.
- `DESIGN.md:78`: D035 calibrates on random genomes, not intact evolved brains; reword.
- `DESIGN.md:120-121`: structural-baseline *refits* (72 GPU refits, about 2.7 h) feed no §7 reading. Keep the rankings as AUC comparators (free), drop the refits.
- The no-task control (lines 177-179) is right and costs nothing; keep it, and note that the acceptance rule "replace if s_o ≥ s_c" is what makes it a pure random walk.

## Answers to §10

1. **Task.** Yes, Task N-mono is defensible, and E2d makes it stronger than the design claims: evolution already lands on a non-stereo strategy at 2.2. But a one-target scripted gap is thin, and criterion 2 as written does not test history (finding 3). Add the `hold` probe with a registered margin and the interneuron-use criterion (finding 4). Run the existing 04a champions under mono as a free sanity check before step 1 (they are local, `runs/e04a/`).
2. **02b risk.** Search all connections, as proposed, since choosing targets by "criticality not from interface adjacency" would select against exactly the neurons the task uses. But then the null must be stratified (finding 1), or the fix for the 02b risk creates a new trivial pass.
3. **Null arm.** Cut it from the proof of concept. Three SH-mirror graphs with one brain per arm cannot separate anything, and the pilot's two SH-mirror graphs already give a descriptive shuffled-graph anchor at no extra cost. If the owner wants a null in the formal run, one graph (about 8 h), not three. SH-mirror over SH-route is the right choice if kept, because mirror symmetry is the generic explanation for recovered partners.
4. **Tiers.** Not well defined as written (finding 7); use the interval-versus-p partition.
5. **Family and expansion reading.** Keep the 12-member per-target family, with the stratified null, because it gives "anatomical enrichment" a defined threshold; register no panel-level test. Keep the expansion reading as a reading, but state its chance rate (finding 9) and tighten "separates the outcomes" (finding 5).
6. **Machinery.** Keep the five attributes, three-state margins and reliability; they are what makes "inconclusive" visible. Drop the structural-baseline refits and PR-AUC can stay as descriptive. Raise final-evaluation worlds to 2 048 (finding 6).
7. **Budget.** Arithmetic correct. Cut order is right, but apply the first cut now so a pilot retune fits (finding 11).

## What a pre-registration still needs

- The stratified permutation null, written out (strata, bins, B).
- The `hold` probe's h and margin; K-mono's and M-mono's tuning grids on fresh tuning-world ids, disjoint from E1's and 04a's ranges (`wormwars/e1/task.py:17-20`).
- World counts for the relevance scan, search, validation and final evaluation, and their id ranges.
- The exact pilot pass numbers (criterion 2's margin, criterion 4's "3 of 8", criterion 5's "half") and the retune rule: how many pilot attempts, and what counts as a retune versus a failure.
- The interneuron-use criterion and the paired-versus-unpaired report rule.
- The shaped-or-raw search fitness decision, fixed after the pilot and before N2.
- Which threshold labels "anatomical recovery" in the outcome table.

What could be cut: the SH-mirror arm, the structural-baseline refits, and the 90% bootstrap in favour of the Holm family's own intervals.