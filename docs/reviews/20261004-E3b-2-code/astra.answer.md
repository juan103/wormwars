**Fix then start.** Draft 2 incorporates the substantive plan-review changes, but the implementation is incomplete. There are also errors in switching measurements and an output-isolation hole.

I checked the actual inputs: all 20 champion hashes match; both partitions have the specified sizes; and both partitions’ all-champion endpoints reproduce every champion bitwise. The 18 attribution tests and eight read-only runner checks pass. I did not launch a formal stage or rerun the file-writing smoke pipeline.

1. **Blocking — an argument rejected by the runner can still write into E3b-1’s accounting.**  
   Files: [scripts/e3b2.py:776](D:/Claude/random/wormWars/scripts/e3b2.py:776), [wormwars/accounting.py:330](D:/Claude/random/wormWars/wormwars/accounting.py:330).

   **Plan:** §2 makes E3b-1 immutable input, including its records.

   **Code:** `run_script` reads `--out` directly from the command line before `main()` validates arguments. Thus:
   ```
   python scripts/e3b2.py report --out runs/e3b1
   ```
   selects `runs/e3b1/compute` and `runs/e3b1/compute.json`. Argparse subsequently rejects `--out`, but accounting writes failed attempts and rebuilds the aggregate in its `finally` blocks.

   I reproduced destination selection with writes mocked out. `output_paths()` and its test do not cover this route.

   **Fix:** validate arguments before opening accounting, and bind accounting exclusively to the selected E3b-2 directory. Test both `--out PATH` and `--out=PATH` rejection without historical writes.

2. **Blocking — “crossed” measures target-side occupancy, latency is one tick short, and final-tick visits disappear.**  
   Files: [attribution.py:229](D:/Claude/random/wormWars/wormwars/e3/attribution.py:229), [attribution.py:305](D:/Claude/random/wormWars/wormwars/e3/attribution.py:305).

   **Plan:** §5D measures crossing toward the new goal **after a confirmed visit**, with latency measured **from the visit**.

   **Code:**
   - A leg succeeds whenever q is on the target side; no threshold crossing is required. Constant `q = −1.5`, with goal changing A→B, produces one successful crossing with latency zero. I reproduced this.
   - The start time is the next tick, when the changed goal becomes `goal_before`. A crossing one tick after the visit therefore has reported latency zero.
   - A visit on the last simulated tick creates no leg or censored observation, because there is no following callback. I reproduced that too.

   The real-run comparison against `SwitchTally` does not catch these errors: both implementations share them.

   **Fix:** distinguish “already on the target side” from an actual directional crossing; retain the confirmed visit’s tick; and register horizon-ending legs. Add independently specified tests for these cases. State explicitly how censored legs enter the reported switching fraction.

3. **Blocking — the recorder does not collect several promised readings.**  
   Files: [attribution.py:280](D:/Claude/random/wormWars/wormwars/e3/attribution.py:280), [e3b2.py:636](D:/Claude/random/wormWars/scripts/e3b2.py:636).

   **Plan:** §5D specifies the middle-half sensitivity analysis, opposite coding, eligible weys, goal occupancy, and uncertainty over mazes.

   **Code:** collects only the middle-third/intended-coding counters. It lacks eligible-wey and per-goal occupancy counters. The report supplies intervals for per-goal agreement and switching fractions, but none for latency or equal-weight agreement.

   **Fix:** collect and report the missing quantities, including maze-bootstrap intervals for latency and equal-weight agreement. In particular, the middle-half reading cannot be reconstructed from the currently saved counters; this must be fixed before acquisition.

4. **Blocking — the attribution report omits a central planned analysis.**  
   Files: [e3b2.py:486](D:/Claude/random/wormWars/scripts/e3b2.py:486), [e3b2.py:546](D:/Claude/random/wormWars/scripts/e3b2.py:546).

   **Plan:** §5A requires allocations in both visits per wey and seed-mean units, the shared-minus-none decomposition, and schedule summaries with paired maze-bootstrap intervals.

   **Code:** reports separate shared and none tables in normalized units. It never produces their allocation differences or uncertainty for those differences. Bootstrap intervals exist only for schedule Shapley allocations; gain, reversion and transplant have run-level t intervals only.

   **Fix:** report the trail-dependence decomposition directly, resampling shared, none, all champions and the common denominator jointly. Add raw-unit allocations and the missing schedule bootstrap summaries.

   The underlying `shapley`, `dividends`, `rebuild`, `reversion`, `transplant`, `read_table` and `shapley_matrix` calculations look correct. The implemented Shapley bootstrap correctly shares maze draws across champions and resamples the denominator.

5. **Blocking — lesion reporting does not match the specified outcomes and units.**  
   File: [e3b2.py:608](D:/Claude/random/wormWars/scripts/e3b2.py:608).

   **Plan:** §5C promises lesion costs per organism and schedule, for every §3 outcome, using the stated normalization.

   **Code:** normalizes visits only; other outcomes are raw differences. Schedule summaries contain visits only. The lesion-cost table uses mean legs and does not provide the specified median-legs contrast, although absolute variant medians are saved elsewhere.

   **Fix:** complete the outcome summaries and resolve the units explicitly before running. Raw differences for rates and shares are reasonable, but that is an amendment to the written plan, not its current implementation.

6. **Blocking — benchmark admission omits saving, and a killed benchmark can be undercharged.**  
   Files: [e3b2.py:440](D:/Claude/random/wormWars/scripts/e3b2.py:440), [scripts/e2.py:521](D:/Claude/random/wormWars/scripts/e2.py:521).

   **Plan:** §7 times saving and counts failed attempts within the cap.

   **Code:** times `play_chunk` without chunk compression, writing or replacement. It also runs eight benchmark rollouts without intermediate cap checks or durable progress records. Kill reconciliation then estimates elapsed time from the latest saved file plus 900 seconds. During `project`, that file can still be the original start marker. Eight chunks can exceed 900 seconds—E3b-1’s cited timing already makes that plausible.

   **Fix:** benchmark the actual save path, check the cap between repeats, and persist benchmark progress so kill reconciliation covers completed work.

   The drop order and the admission arithmetic itself are correct.

7. **Blocking — three supposedly fixed input hashes are not enforced.**  
   Files: [e3b2.py:58](D:/Claude/random/wormWars/scripts/e3b2.py:58), [e3b2.py:104](D:/Claude/random/wormWars/scripts/e3b2.py:104).

   **Plan:** §2 fixes and hash-checks E3b-1’s `champions.json`, `evaluate.json` and `PREREGISTRATION.md`.

   **Code:** their expected hashes are `None`, which disables comparison. Their hashes are recorded, but any committed replacements before `project` would become accepted inputs. Later-stage code guards do not establish the intended initial versions.

   **Fix:** pin the three expected hashes. The individual champion parameter hashes are checked correctly.

There are also these **non-blocking** discrepancies:

- **Resume does not literally validate every maze ID.** [e3b2.py:357](D:/Claude/random/wormWars/scripts/e3b2.py:357) stores first ID, last ID and count. I confirmed that `[7000,7001,7003]` and `[7000,7002,7003]` produce identical specifications. Current contiguous blocks avoid the collision; store the complete ordered list nevertheless.
- **Maze preflight runs late and only in `project`.** [e3b2.py:454](D:/Claude/random/wormWars/scripts/e3b2.py:454) invokes it after benchmarking; subsequent stages do not invoke it. §§3/8 say before the first stage and at every stage.
- **The historical probe comparison is absent from the runner.** [e3b2.py:680](D:/Claude/random/wormWars/scripts/e3b2.py:680) recomputes resting turns without checking the references required by §5E. I independently compared all 21 organisms’ two readings with the committed references: maximum difference was **zero**. Add that check.
- **The plan’s chunk estimate is stale.** The implementation has A=32, B=8, C=28, D=2: **70 production chunks**, rather than approximately 63. Admission counts the implemented chunks correctly.

On the implementation rulings:

- **Benchmark block 7300–7555:** acceptable. Document it as a pre-run amendment to “on smoke mazes.”
- **First A-shared seed as the common denominator:** acceptable. The shared seed-vector equality check is implemented. Add the equivalent within-condition check for A-none.
- **Lesion-stage intact baseline:** appropriate. Report its difference from A’s intact endpoint as a composition diagnostic; I would not block on that omission.
- **Ratio-of-sums maze bootstrap:** appropriate for the stated tick-weighted totals. Resampling mazes preserves the intended uncertainty unit.

The actual interventions otherwise check out: own-root clamps and initialization, relay and gate cuts, scent removal, reflex at −0.5, and the silenced-output W2 reference. All 21 actual organisms have consistent relay signs with A high, so the `None` fallback is unused. I also checked all 20 actual champions with both outputs silenced on CPU smoke mazes: positions, visits, visit ticks and entries matched the silenced seed bitwise.

**Verdict: fix then start — close the accounting output override; correct and complete latch measurements; complete attribution and lesion reporting; repair benchmark timing and kill accounting; and pin the three input hashes.**