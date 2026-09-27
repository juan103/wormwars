# Review: T0 items 3-5 (CPU) at b966a93

**Verdict up front: not yet.** The implementation code is sound, but two of the new tests cannot fail for the reason they exist, and three tests the plan names are absent. I read everything; I could not run the suite (read-only, no execution), so pass/fail claims below are from reading.

Your section numbers are off by one: items 3, 4, 5 correspond to plan sections 4, 5, 6. I reviewed against those.

## Must fix

**1. The jitter test is vacuous: the probe radius is 0.**
`tests/test_t0_items345.py:176` sets `food_probe = "jitter"` but never sets `food_probe_radius`, whose default is `0.0` (`config.py:134`). In `_jittered`, `r = 0 * sqrt(u)`, so every offset is exactly zero in both layouts. The test would pass with the old flat-index keys.

- This also explains why `atol=0` passes although the positions differ between the layouts.
- With a real radius, `(pts + off) - pts` will not be bit-equal across layouts, because `pts` differs and rounding follows it.
- Either compare `_keyed_uniform(0)` and `(1)` directly on the two real layouts, or fix placement first (item 5 below) and compare the sensed food readings. Only the second is truly end to end.

**2. The isolation test does not test isolation.**
`test_islands_stay_isolated_over_generations_without_migration` (line 153) asserts that each logged best is in `by_island[0] | by_island[1]`, the union. With sigma 0 and no migration, every genome is always a copy of some initial genome, whether islands mix or not. It would pass with D064's block-concatenation bug restored.

- The plan asks that "every slot descends from its own island".
- Check the final population by slot: save with `out_dir`, then require slot `i`'s hash to be in `by_island[i % 2]`. Or iterate `_breed_islands` directly over several generations.

## Should fix

**3. Three tests from plan section 6 are missing.**
- **All ring edges and the untouched slots.** Existing tests assert one edge of a 3-island ring (`test_evo_islands.py:57`) or both edges of a 2-island ring (`test_t0_pairing.py:91`). Nothing checks the wrap-around edge with 3 or more islands, or that the other slots are unchanged.
- **The log and snapshots pair under islands.** The pairing test (`test_t0_pairing_confirm.py:110`) runs with one island.
- **An uneven population runs.** The refusal is tested, but not that 5 strains, 2 islands, 1 migrant completes through a migration.

**4. NaN is still swallowed in three places.**
- `wormwars/evo/coevolve.py:197`: the same `max(worst_err, ...)` pattern.
- `scripts/exp02.py:348`: `max(x.ledger_error for x in res.log)`.
- `wormwars/exp02/report.py:219`: `max(r["ledger_error"] for r in recs)`.

Now that `rollout` propagates NaN, the two exp02 sites would drop it again unless it comes first. Finite outputs are unchanged by a NaN-aware maximum.

**5. The layout diagnosis is right in cause, but understated.**
- **Cause, confirmed:** `_build_maps` sizes its per-side draws by `self.n_weys`, the batch's padded maximum (`world.py:412-414`). A neighbour with more weys shifts the world's RNG stream.
- **Understated:** everything drawn afterwards shifts too. That is headings, side 1's angle, the food patches and the hazards. The whole map differs, not only wey positions.
- **Chunking:** `coevolve.play` groups by total headcount, so (100, 150) and (50, 200) share a batch. A chunk boundary between them changes the map. That fits Astra's discrepancy, but "probably its cause" is still unproven.
- **"Does not affect single-swarm experiments"** holds for uniform headcounts only. I found no other caller passing `swarm_sizes`.
- **Suggested fix:** size the draws by the world's own largest swarm. Every uniform-headcount run then keeps its maps exactly.

**6. Numerical checks are narrower than section 5.**
- Corners are uniform-sign only. `tests/test_brain.py:126` calls mixed signs "the hardest case for the gap coupling", and it is not run through a world.
- Finiteness runs on N2 only, 4 worlds, T0 only. SH and RD get it only for scores and energies of one random genome.
- One 01b champion, none of 02's.

**7. The ledger gate test may never exercise deaths.**
At 200 ticks, drain totals 7 against a starting energy of 12, so nothing starves. Only hazards can kill. Add a heavy-mortality or champion case with the flag on, and assert that something died.

## Minor

- **Island validation gaps:** `islands < 1` is not refused; negative migrants get the "exceeds half" message; `population == islands` passes but every island is one frozen elite.
- **The flag lives in `WorldConfig`,** so it enters bundles (`bundle.py:104`), and older code will refuse such a bundle as an unknown field. No test shows scores are bit-identical with it on and off.
- **The flag splits a comment:** it sits between `food_probe_radius` and `food_probe_hold`, which one comment describes.
- **Cost is understated:** two full-field float64 casts plus four reductions per tick, not one reduction.
- **NaN per-tick path untested:** the NaN test runs with the flag off, so `torch.maximum` is never exercised.
- **`evolve` accepts non-finite fitness:** `np.argmax` picks a NaN strain as best.
- **Item 3's test is thin:** 50 ticks, one genome, Dale off.
- **D073 does not state the full suite result.**

## Your questions, directly

| Question | Answer |
|---|---|
| Item 3 (CPU) meets the plan | Yes, thinly |
| Ledger check correct | Yes. Normalisation is per world against its own start, stricter than `test_world.py`'s batch maximum. Per-tick maximum, NaN propagation and opt-in are right |
| Island validation rules | Right. `sizes.min() // 2` handles odd sizes correctly |
| Jitter test adequate | No (finding 1) |
| Layout diagnosis | Right cause, understated scope (finding 5) |
| Missing before the gate | Findings 1-4, plus the GPU items |

D064's wording correction is done (D065).

items 3-5 CPU: not yet