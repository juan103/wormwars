**Verdict: fix then publish.** The planned readings and roadmap branch stand. No rerun is needed.

I independently reconstructed the comparisons from the first- and second-pass records. Every reported bootstrap mean and interval matches exactly. Calling the reader and summary builder in memory also reproduced `reading.json` and `summary.json` exactly. I did not read the NPZ files or modify anything.

**Numbers:** two cells in the [exploratory table](D:/Claude/random/wormWars/docs/memory/M6-0-RESULTS.md:143) need correction. Recomputed over eligible genomes:

| Tag | Median a | d(5)/a | d(30)/a | d(100)/a | d(30) | d(100) | Returns |
|---|---:|---:|---:|---:|---:|---:|---:|
| g00 | 0.028873 | 0.788272 | 0.226786 | 0.006769 | 0.006441 | 0.00015231 | 16/99 |
| g39 | 0.160960 | 0.845442 | 0.203581 | 0.003937 | 0.026175 | 0.00050153 | 5/102 |
| drift | 0.026443 | 0.791146 | 0.244569 | 0.008807 | 0.006014 | 0.00025797 | 116/401 |

Thus:

- g00’s median `a` should be **0.029**, not 0.028. The latter comes from including all 102 g00 genomes: their median is 0.028222. The table specifies the 99 eligible genomes. Make the introductory comparison use the same population.
- Drift’s median `d(30)/a` should round to **0.24**, not 0.25.

The returns counts agree with the stored flags, and those flags are consistent with `tau_first` and `tau_stay`. Absolute differences above were reconstructed per genome as `a × ratio`, then medianed.

All **12 entries in the non-fading list match**, including their amplitudes and both unresolved → fading transitions. There are no missing entries. Final primary classes include six switches and four unresolved genomes; secondary classes include two switches, two unresolved and one persistent oscillation. The class table, persistence medians, censoring/floor counts, beside-02b numbers and four g79 comparisons all check out.

**Readings:** correct for these records.

- All stages contain the expected genomes; second-pass coverage and seeded audit selections match the plan. All 40 audited genomes remain fading.
- The 120 consistency comparisons pass; maximum relative difference is `0.00017835212825046754`.
- There is one g39 switch and no unresolved g39. Therefore neither unresolved assignment can meet the five-switch requirement, and the inconclusive branch is not triggered.
- The negative wording is applied correctly.
- Primary persistence versus drift is **−0.0947917**, interval **[−0.1701389, −0.0128385]**. That supports the plan’s **“shortened”** reading. The primary comparison against g00 remains inconclusive about direction.

The “[outlasts about 41%](D:/Claude/random/wormWars/docs/memory/M6-0-RESULTS.md:28)” explanation should say **“a block-averaged win share of 40.5%, counting ties as half.”** Strictly exceeding drift contributes 40.0%; ties supply the remaining 0.52 percentage points.

**Interpretation:** the direction is fair, but the current categorical wording is too strong. In particular, [“larger, not longer-lived” and “not a second stable state”](D:/Claude/random/wormWars/docs/memory/M6-0-RESULTS.md:171) need qualification.

The relative-amplitude caveat is present, but it does not sufficiently constrain those conclusions. These measurements establish shorter persistence **relative to each genome’s own starting amplitude**. They do not establish shorter persistence above a common absolute threshold or a shorter useful behavioural memory window. The absolute median effect remains approximately **4.35 times drift’s at tick 30** and **1.94 times at tick 100**. Conversely, a larger amplitude alone does not mechanically shorten this normalized measure: uniform rescaling would cancel.

Suggested replacement:

> On this probe, selection is associated with larger initial history effects and shorter persistence relative to each genome’s own initial effect, compared with drift. Most g39 champions show fading transients, with family median τ_stay of 39–46.5 ticks; one champion shows separate stable states. These results do not determine persistence above a common absolute threshold or the duration of useful memory during behaviour.

Also restore the plan’s explicit qualification that the primary inputs are **conditioned on each run’s g39 champion’s replay**. These are not input-independent properties. Define “stays below” as **through tick 2000**, rather than “for good.”

Two further publication fixes:

- The [secondary drift switch share](D:/Claude/random/wormWars/docs/memory/M6-0-RESULTS.md:106) must retain unresolved bounds: **2–4 of 408, or 0.49–0.98%**. Reporting only 0.5% loses the plan’s required qualification. Any census comparison should retain its different mapping and eligibility context.
- The second-pass timing estimates match local file timestamp gaps: approximately **900 s and 715 s**, averaging **28.3 s/genome**. Those timings are absent from the JSON contents and run log. Archive their timestamp-based derivation or remove the detailed timing claims. Total recorded time, **3445.285 s = 0.9570 hours**, is directly supported.

**Roadmap:** options **3 or 4** follow the plan correctly. Frame that as the planned decision after failing to detect enrichment. It does not establish that switch-mediated behaviour is absent; the primary bank contains one switch champion.