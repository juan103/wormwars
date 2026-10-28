**Verdict: agree, to the owner after the wording fixes below.** Round 1's fixes are in and correct, and every number I checked in draft 2 traces to the two JSON files. Nothing needs rerunning. The residual code points do not move a host count.

## Ranked points

1. **The Welch question is settled by the numbers, not by the gate, and my objection reduces to wording.** At the host counts M5 will use, the Welch t and the plain t are the same reading. Where the same cells were run under both readings, the raw false "raises" rate pooled over the six non-ensemble cells is:

   | Selection | As written | Welch |
   |---|---|---|
   | A's cheapest, 135 hosts | 2.47% | 2.43% |
   | A's fewest, 70 hosts | 2.55% | 2.44% |

   At 30 hosts the Welch t alone reads 2.1% to 2.3%, below nominal. So the Welch does not repair the plain t's lean. It is conservative below about 70 hosts and identical above 100. "Passes every cell" holds for the Welch's own selections, and B's selections are different allocations and host counts under the two readings, so that sentence compares different cells. I agree to adopting the Welch, on the stated ground that one t formula serves the balanced and the unbalanced case at no cost to A or C, with the note saying that the as-written failures sit at 30 to 95 hosts, where M5 will not be. The pre-registration should state the adopted reading's simulated rate at the chosen policy, which is about 2.4% raw and 1.1% unqualified from C's and A's cells, and that the plain t would read about 2.5%.

2. **Make the Welch the code's default before M5's plan.** `WELCH_TOO` is an environment flag read at import in `scripts/memory_m5/m5_reading.py:25`. A reader run without the flag silently uses the plain hull. Replace it with a constant and a test before the pre-registration names the reading.

3. **What the owner must see that section 5 lacks.**
   - The 20% rule's margin is one grid step. A 5-host step moves A's cost by about 3.7%, and the savings are 23.0% and 22.1%. The rule says C; the owner should know its resolution.
   - C's cost at the wide spread. Under 3.0e-5 C costs 96 hours against A's 92. C saves 20 hours at the pilot's spread, nothing at the core, and costs a few hours more above it.
   - The trade. C's 0.84 power at the central scenario against A's 0.93 is where the saving comes from.
   - What success means. Six readings must all read "raises". Raw "raises" alone would need 90 to 95 hosts.
   - The continuation sample as a plan item, with its size and CPU cost fixed there.

4. **The "what a cell's gate can detect" arithmetic uses the wrong denominator.** The eight ensemble cells cannot fail, with rates of 0.1% to 1.4%, so 24 cells are at risk, not 32. At a true 2.52% about 2.4 of them fail by noise. At the failing selections' own pooled rates, 2.55% for A's fewest and 2.57% for B's cheapest, each cell fails about 20% to 25% of the time, which is what 6 of 24 looks like. The conclusion "part noise, part lean" stands.

5. **Residual code points, none moving H.**
   - Invalid hosts' audits still enter the pooled rate in `contrasts` (`m5_power.py:566`) and the final per-arm audit bound (`m5_power.py:677`), while the stage-1 bound in `run_c` excludes them. An invalid panel has no usable audit, so both should exclude it. It touches only the invalid-panel sensitivity rows, at R = 1000, by a fraction of a point.
   - The stage-1-bound test (`tests/test_memory_m5_power.py:377`) only checks that the key exists and lies in [0, 1]. A sabotage computing the bound from all hosts' audits would pass it. Strengthen it with a simulation whose stage-2 hosts carry transitions.
   - `summarise_short` drops `cap_seconds`, so C's caps of 149 and 145 hours are traceable only through the caps table. Carry the cap in C's rows.

6. **Small wording errors in the note.** "Within 1e-12": the realised host components miss their targets by up to 4.3e-12, the solver's tolerance on ρ being 1e-6; say "to seven figures". "No run exceeded 1.25 times the mean cost": for C the reference is the fixed-H mean at H_max, not C's own mean, and C's 95th percentile at the core is 99.5 hours against its mean of 90.7. "The Welch t alone: 2.45%" averages over host counts; give the 30-host and 135-host values. "Passes every cell of the gate as designed" should read "of its own four selections".

7. **Agreed as proposed.** The unresolved share stays descriptive with no flag. The continuation sample goes to M5's plan as a descriptive bound on r per arm up to 100,000 ticks, not a success criterion. The identification limit goes to the owner with the pilot's 0 of 47 beside it.

## The five questions

1. **Yes, with point 5's residuals.** The joint fit converges to a host SD of 0.478 and a draw SD of 0.192, matching Astra's independent values, and the test checks that both the count variance and the draw component are reproduced. The quadrature components realise their targets. In `run_c`, invalid hosts leave the interim through the NaN mask and the valid count, leave the reading because the sliced simulation now carries the invalid flag, and a short ensemble stops the run. The stage-1 bound and its coverage are reported. The exclusion after an invalid host requires three valid hosts per ensemble and checks every leave-one-out through the unbalanced interval. The fixed costs include the verification and one block per draw. The new diagnostics and the `c_sens` stage are present.
2. **Agree to the Welch, with point 1's wording and point 2's code change.**
3. **Agreed.**
4. **Points 4 and 6.** Everything else matches the files: all 48 A and B host counts and costs in the section-1 table under both readings, the 90% column, the raw-only and τ = 0 columns, the fit's SDs and ρ values, the implied count variances, the check's quantiles including the Welch half-width at 0.11, the six failing cells and their bounds, the pooled rates, the averaged parts, every row of the A-cheapest scenario table, the exclusion and coverage rates, C's nomination and runner-up costs, its confirmation rows, nulls, "above" row, sensitivity rows and caps, and both savings.
5. **Point 3.**

## What I checked

Both `power.json` files for every number above, the script against the design's sections 4 to 6, the test file, the sabotage log, the fixed-costs file, and round 1's two reviews against the fixes. I ran nothing and changed nothing.