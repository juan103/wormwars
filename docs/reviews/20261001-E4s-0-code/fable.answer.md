## Verdict: fix then run

The core logic matches plan v2 and I found no bug that would silently corrupt the sweep classes, the qualification, or the 12-of-16 reading. The fixes below are small; items 1–4 should go in before the formal run. I ran nothing: this is from reading the code, the tests and both v1 reviews.

## Bugs and departures from the plan

1. **The projection times each shape once, cold, and leaves out its own time** (`scripts/e4s0.py:333-346`).
   - Each shape's rate comes from a single first call, which includes world construction and first-shape CUDA allocation; the one warm-up is a 1 × 4 batch. The bias is conservative, but it can trigger a shrink of the sweep to 256 worlds that was not needed, which weakens the only interval-based classes.
   - `freeze_sizes(rates, E.clock().spent_hours())` reads only `compute.json`, so the projection's own seconds are missing. `admit` later counts them, so the projection can say "within" and the sweep then be refused.
   - Fix: time each shape twice and use the second, as `e2d.py:521-531` does; add `(time.perf_counter() - ctx.cap.t_start) / 3600` to the spent hours, as `e2d.py:535` does.

2. **Per-world counts are not recorded everywhere the plan promises** ("committed with every summary"). Missing:
   - the G0 selection scores (`e4s0.py:586`), so the pick of each G0 best cannot be audited from the record;
   - the ladder's tuning and re-score counts (`:504`, means only) and the L4 base selection's (`:527`);
   - the robustness children's counts (`:666`, means only).
   - Fix: add them. The largest is tuning, about 250 k integers; if that is too bulky, say so in the plan.

3. **Batch composition is recorded only by the sweep.** The plan says each record holds its composition. The ladder, populations and robustness records hold none.
   - Tuning's last chunk is ragged: 24 strains for 216 candidates, 8 for 648. Record it.
   - The robustness parent runs as 1 padded strain × 64 and the children as 64 × 64 (`:660`, `:664`), so the "share of the parent" compares across compositions, which the plan says is never claimed. Fix: put the parent in the children's chunks, or state the exception in the record.

4. **The fallback reading has a misleading default** (`:671`). It returns "0.25x" whenever the 0.125× condition fails, including when the median child keeps less than half at both scales. The plan defines only the 0.125× case. Fix: add a third outcome, such as "neither scale keeps half: not drawn".

5. **04a run 2 is skipped silently if its label is absent** (`:570`, `:612`). In a formal run a missing "04a run02" should raise in `requires`, not drop item 3.4 from the record.

6. **The tie order differs from the plan's wording.**
   - `ladder_grid` puts the step's own parameter outermost (`:151`); the plan lists it last in "the order of the grid's product as listed".
   - The re-score tie goes to the higher tuning mean (`:503`), not to grid order.
   - Both are immaterial to results. Amend the plan's sentence or the code so they agree.

7. **The reversal's "wrong sign" flag tests the wrong quantity** (`:476-480`, `diagnostics.py:116`). It checks the sign of changed − control, which is negative for any decrease, even if the turn command never crosses zero. A monostable comparator should not trigger this, so it is low-risk, but the flag cannot catch what it is named for. Fix: also check the sign of the changed trace's own final mean.

8. **`module.json` is written before the stage's final cap check** (`:547`). A ladder that then stops on the cap leaves a module file beside a not-completed record. Write it last, or delete it on failure.

9. **A consequence to state, not a bug:** the grid's top values sit on the genome's hard bounds (`w_max` = 3.0, `tau_min` = 0.5; `config.py:36-38`). If the qualifying candidate has w_n or w_o = 3, or τ = 0.5, half of each robustness mutation on those parameters is clamped away. The retained share then looks better than at an interior point. Record which parameters sit on a bound.

## Checked and correct

- **Residual wrapper:** it matches `World._read_motors` operation for operation, adds before the clamp, and uses same-tick signals (`world.py:775` precedes `:785`). The k = 0 check uses one chunking of 8 × 512 for the reference and every k.
- **Sweep classes:** adjacency, k = 256 as neighbour only, k\*, the "harmed at a larger k" flag and the paired direction (k minus k = 0) all match the plan.
- **Ladder:** the ids match the plan's table; the order, stopping, L4 base on L4×2's re-score worlds, ties to the lower step, and the fixed recurrent coefficient are as planned. Qualification is lo95 ≥ 5.0 and "uses"; the `or SMOKE` bypass is smoke-only.
- **G0 selection:** per-population ids, one 512 × 8 chunk, argmax with ties to the lowest index, bests classified on 1 024 worlds, reading at 12.
- **Robustness ownership and seeds:** module-only scales, seed 1 151 000 + j shared across scales.
- **Stage frame:** E4s-0 has its own copy of E2's frame; E2d keeps a separate one, and its seed 0 and 10 000 resamples are imported and tested.
- **Shrink and admission:** the order, the never-grow rule, and admission on spent plus remaining against 1.8 h.
- **World ids:** I found no other use of the 940 million range in code or configs.

## Does v2 resolve the v1 items?

Yes, all the must-fix items from both reviews are addressed in the plan and in code, with two partial ones:

- **Projection** (Fable 6, Astra 5): implemented, but see item 1.
- **Per-world counts** (Astra): pinned in the plan, only partly implemented; see item 2.

One test gap remains: no test covers `mutants()` in the script itself (the pairing across scales and the seed per j). The ownership test calls `Genome.mutate` directly.