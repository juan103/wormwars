**Verdict: ready for the rest of pilot-dev, with small fixes.** None of the fixes is to the simulation code. One is a correction to a premise I introduced in round 2 and that D310 and PILOT-DEV §2 now repeat. One is a budget guard that the first measured rates make worth adding before `full` starts.

## 1. Round-2 findings, checked in the code at 1b0531a

| # | Round 2 | Status | Where |
|---|---|---|---|
| 1 | Partial report raises KeyError | Resolved | `scripts/e03a.py:752-753` writes p, setting and plan into `progress` before any search. `stage_report` takes p from `baseline` (931) and reports a stopped `full` as far as it got (934-942). The test at `tests/test_e03a_script.py:120-148` stops on the second target-brain's final scoring and runs the report. |
| 2 | Run `probe` before the searches | Resolved | `STAGES` at line 78; `stage_probe` needs only `baseline` (856). The module docstring at lines 9-10 still lists `full` before `probe` (cosmetic). The mid-course projection was not added; see finding 1 below, it matters now. |
| 3 | Round B's order | Withdrawn by me, see §2 | |
| 4 | Budget question, reading rule, signal-to-noise record | Resolved | PILOT-DEV §3 fixes the reading. `Trace.paired` (`search.py:211-213`) is filled at 262-263 from `s_cur` before the acceptance loop modifies it, so it is the paired spread the rule sees. `_diagnostics` (633-635) writes the cold score SD and the paired mean and SD. |
| 5 | One 34 816-world chunk | Resolved | `FINAL_CHUNK = 16 384` (474), used by the scan (351) and final scoring (481). Search rollouts are at most 540 strains × 16 worlds per group, below it anyway. |
| 6 | Mirror-zero per type; turnover windows; label check; tune grouping | Resolved except the optional grouping | Per-type subsets with sizes at 683-696. `_turnover` (604-614) now runs 0→10 … 90→100, and 190→200 for the long searches; the test at `test_e03a_script.py:162` pins the count. Labels checked against `baseline` at 755-757. Grouping tune's rollouts by X was optional and is not done; fine. |

## 2. Round B's order: I withdraw my round-2 finding, and the premise needs correcting

The rule at `scripts/e03a.py:580-583` is an argmax over the four settings' mean final counts, with a 0.02-target hysteresis in favour of earlier entries. In round 2 I wrote that because the noise is far larger than 0.02, "round B will almost surely return (1/3, 1)". That is backwards. When the noise dwarfs the tie, a later setting beats the first by more than 0.02 about half the time whenever they are truly equal, so the pick is decided by noise, not by the order. The order only matters inside a 0.02 band. For scale, p is about 0.10 targets here (`panel.json:157-158` gives a selector intact mean of 2.06 and p_sel of 0.103), so the band is a fifth of p and a fraction of the between-search SD. The first-listed setting gets a mild edge, not the decision.

So the three options are practically the same procedure:

- **Keep (1/3, 1) first, as listed.** My preference now, because it needs no plan edit and no re-review. Acceptable.
- **List (0.6, 3) first.** Acceptable, but it would change the outcome only in near-ties, and the planted check's evidence is about anatomy under a perfect oracle, while round B reads function. It is not evidence about the quantity the rule compares.
- **Highest mean regardless of order.** Acceptable; it is what the code already does to within 0.02.

If the owner wanted prior evidence to govern the choice, the lever would be the tie, raised to the noise scale, with the preferred setting first. I do not recommend that: there is no prior evidence on the function score for either order, and "chosen by this rule, not optimised" already covers a noisy argmax.

What does need doing: PILOT-DEV §2's "Open, round 3" bullet (lines 59-61) and D310 (`DECISIONS.md:9388-9389`) state that the order "all but decides round B". That is false and it came from my round-2 finding 3. Under rule 4 it wants a dated annotation beside it, not a rewrite.

## 3. Findings

**1. The measured evolution rate is half the design's assumption, and the search rate that decides whether the 6-hour cap holds is unmeasured (medium; `runs/e03a/pilot-dev/compute.json`, `scripts/e03a.py:737-829`).**

| Quantity | Value |
|---|---|
| `selection` rate, two-run batch (512 worlds a rollout) | 200 worlds/s |
| `measure` rate, 16 384-world chunks | 892 worlds/s |
| Spent, pilot-dev plus preflight | 0.79 h |
| Left under the 6 h cap | 5.2 h |
| Still to run: `evolve-nip` at the measured rate, `baseline` and `probe` | about 0.85 h |
| Still to run: `tune` and `full` | 6.9 M episodes |
| Search rate at which the cap is just met | about 440 worlds/s |

The design assumed 420 worlds/s for everything. If the search batches run at that rate, `full` hits the cap on its last target-brain. If they run like the scan, the whole plan finishes with about two hours to spare. Search rollouts are 3 456 worlds a group in `tune` and 8 640 in `full`, between the two measured compositions, so either outcome is plausible. Two cheap protections:

- Before `full`, read the `tuning` category's rate from the compute aggregate and project `full`'s 3.6 M episodes. If it does not fit, ask the owner for a cap amendment then, rather than hitting the cap inside `full`. A line printed at the end of `stage_tune` would do it; this is the projection asked for in rounds 1 and 2.
- A `--rerun` of `full` after a cap stop restarts all four target-brains, since the loop at 754 never skips a target-brain with a completed row in the archived attempt. The saved states at `runs/e03a/pilot-dev/states/` are not reused. Skipping completed target-brains is a few lines and saves up to 0.9 M episodes per finished target-brain.

Neither changes a measurement. If the owner would rather extend the cap on demand, that is a defensible choice too; I am flagging the arithmetic, not insisting.

**2. The false premise about round B's order (medium, correction; `PILOT-DEV.md:59-61`, `DECISIONS.md:9388-9389`).** See §2 above. Mine to own.

**3. The prompt's premise is incomplete: `panel` also ran (low; `experiments/03a-self-consistency/pilot-dev/panel.json`).** It ran at 1b0531a on 2026-10-18 at 01:19 UTC, completed in 97 s, after round 2's fixes were committed and before this round. Its targets are URXL and PLNL, the only three high-tier representatives being URXL, PLNL and AIBL, with no flags. D310's wording ("wait for these fixes to be committed") is consistent with this; the prompt's ("the later stages wait for this round") is not. It cost 0.03 h and nothing in it depends on this round, but the record should say which stages ran before round 3 closed.

**4. Small documentation mismatches (low).** The module docstring at `scripts/e03a.py:9-10` lists `full` before `probe`. PILOT-DEV §1 line 20 says seeds run to 3 413 604, but the no-task control at `scripts/e03a.py:799` uses 3 414 000 to 3 414 003. The no-task searches simulate nothing, so no world or seed range is at stake.

**5. Residual, accepted scope (low; `scripts/e03a.py:770-777`).** States are saved when a target-brain's ordinary searches reach generation 100. A stop before that loses the current target-brain's searches entirely. Astra asked for periodic saves of ongoing searches; the plan chose the two save points instead. Acceptable, and worth one sentence in the plan.

## 4. New bugs in the changed code

I found none that would waste budget or mislead the output. Checked and correct: `keep_finished` fires once, after the lockstep generation in which every ordinary search finishes, by which point both long searches hold their generation-100 snapshot (`search.py:296-297`); `_save_states` writes atomically through `XState.arrays()`; the failed record carries the completed rows because `progress["target_brains"]` is the same list `rows` that `stage_full` appends to; `_attributes` matches the signatures of `reliable_brain`, `functional` and `outcome` in `stats.py:192-216`; `expected_jaccard` returns 1 at m = K (`null.py:251-252`); `_no_task` gives `tell` exactly R + Rλ zeros, so every best offspring and every swap is accepted deterministically; the no-task and enrichment nulls use the same permutation bank (`null_seed + x`); the `probe` record keeps partial results on a failed control because `out` and `progress` share their nested dicts; `stage_report` withholds the projection whenever `search` has no measured rate, which is the case until `full` runs.