**Ready for the rest of pilot-dev, with small fixes before `tune`/`full.** The main round-2 blockers are fixed. State retention is only partly fixed, and the new interpretation of the search diagnostics overclaims.

I checked the working files; `.git` identifies `roadmap` at `1b0531a42b13c1004679dc49ad3559f274af14b0`. I did not execute code or tests or modify files.

1. **Round-2 findings: disposition.**

   | Round-2 finding | Status | Code-based assessment |
   |---|---|---|
   | **1. Partial reporting — high** | **Resolved** | [`stage_full:752`](D:/Claude/random/wormWars/scripts/e03a.py:752) initializes metadata before searching. [`stage_report:931`](D:/Claude/random/wormWars/scripts/e03a.py:931) obtains `p` from baseline, accepts partial `full`, and withholds projection when rates or completed probe timings are missing. |
   | **2. Disposable search states — high** | **Partly resolved** | [`keep_finished:770`](D:/Claude/random/wormWars/scripts/e03a.py:770) saves ordinary-search results and long-search generation-100 snapshots before the extension continues. Final states are saved before final evaluation. However, there are no periodic saves of ongoing searches or their diagnostic traces; see finding 3. |
   | **3. Projection — high for budget decisions** | **Resolved for pilot-dev** | [`stage_probe:904`](D:/Claude/random/wormWars/scripts/e03a.py:904) measures full replay separately; [`stage_report:958`](D:/Claude/random/wormWars/scripts/e03a.py:958) prices one control per projected brain. Full-search composition timings are retained, and the report explicitly labels extrapolations. The aggregate rate remains an assumption, now disclosed. |
   | **4. Turnover and mirror-zero subset — medium** | **Resolved** | [`_turnover:604`](D:/Claude/random/wormWars/scripts/e03a.py:604) includes generation zero and the final complete window. [`_descriptive:683`](D:/Claude/random/wormWars/scripts/e03a.py:683) uses each type’s own zero subset, reports sizes/positives/scoreability, and averages scoreable AUCs. |
   | **5. Planted-check wording and settings — medium** | **Wording resolved; recommendation revised below** | Chance levels and “upper bound” are explicitly corrected. Keep 100 generations and paired extensions. |
   | **6. Library/control observations — low–medium** | **Resolved, with a downstream-gating caveat** | Device transfer, bootstrap weighting and non-finite family-2 handling remain correct. `expected_jaccard(K,K)` now returns 1. Control wording is corrected; failures stop before later brains. See finding 4 about explicitly blocking subsequent stages. |
   | **7. Inherited round-1 disposition table** | **Previously resolved items remain resolved; remaining qualifications below** | The missing no-task result and five attributes are now emitted by [`_no_task:714`](D:/Claude/random/wormWars/scripts/e03a.py:714), `_attributes:725` and `stage_full:799`. Longer-search/cap recovery remains partial because traces are not retained. Test coverage remains partial: interruption coverage improved, but does not exercise interruption during the extension or verify projection arithmetic. |

2. **Medium — round B’s stated premise is wrong. I prefer the highest observed mean.**

   [`stage_tune:580`](D:/Claude/random/wormWars/scripts/e03a.py:580) replaces the incumbent whenever a later mean exceeds it by 0.02. Consequently, the selected observed mean is **within 0.02 of the maximum observed mean**. Noise much larger than 0.02 does not make the first setting almost certain to win; noisy differences can readily displace it.

   The claim in [`PILOT-DEV.md:59`](D:/Claude/random/wormWars/experiments/03a-self-consistency/PILOT-DEV.md:59) that order “all but decides” the round should be corrected. I also withdraw any implication in my round-2 response that accepted that reasoning. The problem is noisy selection, not general dominance by the first entry.

   My preferences:

   - **Highest observed mean:** preferred, with a fixed tie-breaker. It removes the arbitrary tolerance/order interaction. Describe it as an exploratory choice, not demonstrated superiority.
   - **Current order, `(1/3, 1)` first:** acceptable. Its allocation to weight and τ/bias exploration is defensible.
   - **Fable’s order, `(0.6, 3)` first:** also acceptable. I do not accept that the planted oracle establishes it as the best real-task setting, but listing it first is not a reason to block pilot-dev.

   Changing the default as well as the order changes round A’s mutation setting. Those are separate decisions. I would retain the current round-A default.

3. **Medium — interrupted searches still lose diagnostics and ongoing progress.**

   [`_save_states:704`](D:/Claude/random/wormWars/scripts/e03a.py:704) correctly writes all `XState` arrays through a temporary file and replacement. The callback in [`run_lockstep:304`](D:/Claude/random/wormWars/wormwars/e03a/search.py:304) correctly runs after completed generations.

   But the driver uses that callback only once, when ordinary searches finish. A stop at generation 150 preserves generation-100 states, while losing generation-150 progress and **all current-target Q, turnover, acceptance and paired-score histories**. Final states cannot reconstruct those histories. A stop before generation 100 preserves no current-target states.

   Add periodic saves of current states and diagnostic traces, including at ordinary-search completion. This needs no resumability implementation. The regression at [`test_e03a_script.py:120`](D:/Claude/random/wormWars/tests/test_e03a_script.py:120) interrupts final scoring after searches finish; it does not cover this remaining case.

4. **Medium — moving `probe` earlier does not enforce its success as a prerequisite.**

   [`stage_tune:524`](D:/Claude/random/wormWars/scripts/e03a.py:524) requires only completed baseline; [`stage_full:740`](D:/Claude/random/wormWars/scripts/e03a.py:740) requires baseline and tune. Neither requires completed probe. `STAGES` supplies ordering, but the CLI executes separately requested stages.

   Thus a failed probe can still be followed by expensive searches, contrary to the stated control policy. Require `read("probe")` before `tune`, and preferably before `full` too. Also update the command examples at [`e03a.py:8`](D:/Claude/random/wormWars/scripts/e03a.py:8), which still place probe after full.

5. **Medium — the new “signal-limited” conclusion is unsupported; the recorded spreads are not pure noise estimates.**

   [`Trace.paired:262`](D:/Claude/random/wormWars/wormwars/e03a/search.py:262) correctly computes offspring-minus-current differences on shared worlds. However, their spread mixes mutation effects, replica differences and evaluation noise. The cold-score SD also mixes changing states with changing worlds. Neither isolates evaluation noise.

   Moreover, [`_diagnostics:633`](D:/Claude/random/wormWars/scripts/e03a.py:633) exports averages of the per-generation paired summaries, not the per-generation series promised by the plan. Preserve those series.

   The claim at [`PILOT-DEV.md:94`](D:/Claude/random/wormWars/experiments/03a-self-consistency/PILOT-DEV.md:94)—no observed gain means “signal-limited” and “more generations would not help”—is too strong. Two extensions per MIP target cannot establish either conclusion. Use: **“No improvement detected over this extension; retain the budget because these measurements do not justify increasing it.”** That preserves the budget decision without inventing a mechanism.

6. **Low — diagnostic tests still provide less assurance than their names suggest.**

   [`test_e03a_script.py:157`](D:/Claude/random/wormWars/tests/test_e03a_script.py:157) checks turnover using smoke searches of two/four generations. Both turnover lists are empty, so it cannot catch wrong ten-generation boundaries. Add a deterministic mask-history check spanning at least generations 0–20.

   The successful-run no-task and attribute paths look consistent with their descriptive scope. Their raw enrichment threshold is explicitly named `enrichment_p_below_0.05`; it must remain distinct from the formal Holm-controlled outcome.