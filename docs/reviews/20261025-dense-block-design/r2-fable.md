**Verdict: revise.** The arm set, hosts, primary contrasts and cost are right. Three parts need changing: the direction threshold, the audit, and what "saved tick-2000 states" assumes.

**1. The merge and U_HX.** Agree, and keep U_HX. Its per-edge weight is about 18 anatomical, roughly 0.64 scaled, well under the clamp. It gives the secondary slope a sevenfold S1 range and a fiftyfold S2 range, and it samples the top regime where sustained oscillation may replace switching. Add one line to the joining observation: Δ_count positive means count or connectivity per se, zero means S1, negative means S2 or S3. Also name U_LL − I as the construction check. If equal-magnitude random wiring at the host's own count and weight already differs from I, the factorial's low corner is not the host's baseline.

**2. Fresh hosts.** Agree with Astra. The pairing loss is acceptable because M4e re-runs I and T on its own hosts and W and K re-create the comparisons that needed D, P and R. Testing contrasts motivated by R > D on the hosts that produced it would be partly circular. My stage 1b becomes unnecessary.

**3. One margin, not two.** The "lower > 0.001" rule makes the screen's own plausible effect sizes unreadable. I checked against M4d's counts:

| Contrast | M4d size | Binomial SE | Lower bound at 95% each, t(9) |
|---|---|---|---|
| D − I | 0.0020 | 0.0005 | about 0.0008 |
| T − R | 0.0012 | 0.0011 | about −0.0013 |

An effect the size of M4d's D − I reads "unresolved" under the 0.001 rule and "raises" against zero. Astra proposed 0.001 as a benchmark to report around, not a threshold. Read direction against zero, as M4d did, keep 0.004 for exclusion, and report where the interval sits relative to 0.001. The two readings also overlap as written: an interval within [0.0005, 0.0035] both "raises" and "shows no effect of 0.004 or more". State them as one joint reading, direction plus size. Say the family level explicitly: "95% each" under Bonferroni over two is a 90% family, M4d's level. Keep M4d's single-host guard at 0.01. Put a precision statement in the plan: at M4d-like rates the half-width is 0.0012 to 0.0025, so contrasts under about 0.003 will mostly read unresolved.

**4. The audit, the horizon, and the states.**
- Zero flips in 256 bounds the flip rate at about 1.2%, three times the margin and about 120 genomes per arm. Such an audit cannot certify the pass at the effect's scale, and 99% allows two flips. Use at least 1024 fading genomes, 128 per block arm, with zero flips to separate states as the criterion and the 1% rule for any change. Fix the size before the run at what the smoke benchmark allows.
- Pass every separate-states genome too, about 300 to 600 across arms, cheap. The horizon question bites there, and the reading then uses one horizon for every switch it counts. Report the transition table.
- M4d's harness does not save tick-2000 states. The panel JSON holds class columns only, and the state and input that probe_states returns stay in memory. The M4e harness must write them for the genomes that will get the pass, or re-simulate the 2000 ticks with a bitwise check against the first pass, which CPU exactness on this machine allows. The plan must say which.
- The hold continuation should be float32, as the main probe is. The classifier's own float64 continuations, which already reach 20,000 ticks for oscillation candidates, stay unchanged. Say so, or "the same rules" is not quite true.
- 22,000 ticks is fine. The commonest failure, the unconfirmed candidate, is a history that has not settled, and a longer hold is the right remedy for it.

**5. Missing or waiting.** Pre-specify a fallback for K's reciprocal matching if the sampler cannot hit W's count within a fixed tolerance: report the achieved count, no matching. Nothing else should wait. Cost of 32 hours plus up to 12 for the pass fits the 48-hour cap only if the pass is batched, so the smoke benchmark must size the audit before the cap is frozen.