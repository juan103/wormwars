Status: I've read the plan, the runner, the drivers, both records and Astra's original wording; the verdict follows. I could not run anything, so the points about mechanism are from reading the code and records.

## Verdict: amend and continue, but not with the amendment as written

The fallback is the wrong response, and the claim is about half right. The amendment drops the one condition that was a trail property rather than a controller property (the saturation cap), and it overstates what the diagnosis shows.

## 1. Is the diagnosis right?

**No bug is evident in the polarity setup.** In `maze_runs.py:157-210`:
- The trail goes into the A channel, the follower's goal is A, and the ageing and limit are as the plan says.
- `pass_none` is 0.0117 in all 24 rows, as it should be for a condition that ignores the constants.
- A steering sign error is ruled out by shared − none being positive.

**"Structural" is right in substance, but "by construction" is too strong.**
- Facing down-slope is an unstable equilibrium for a bilateral follower, not an impossibility. With ±0.3 rad jitter there is a small L − R; my rough estimate is that it grows too slowly for the roughly 78-tick limit and is swamped by the cross-corridor profile and the reflex.
- The stronger evidence is in the record: real ≈ permuted in every row (real 0.016-0.09, permuted 0.016-0.10). The follower gains nothing from the slope.

**The diagnosis omits that the test fails at every heading.**
- Facing toward A, real − max(none, permuted) is +0.14 at the best-rate setting and +0.02 at the pilot. At a uniform heading it is +0.08 and −0.06.
- Even correctly oriented on a real trail, the follower misses the limit in 39-50% of mazes, and the no-trail follower passes 47%.
- So the reading is: this follower gets little from a single-pass trail aged one leg within 2× the oracle's time. The turnaround is only part of it.
- A minor flaw: the "toward" start is "away" + π (`_start`, line 149). Where the route bends at the middle cell, that faces a wall, not A.

**The nose-range explanation is incomplete.** Decomposing the diagnosis counts:

| Setting | In range | Above 0.35 | Exactly 0 | Between 0 and 0.005 |
|---|---|---|---|---|
| Pilot | 34% | 9% | 22% | 35% |
| Best rate | 34% | 31% | 22% | 13% |

- The largest missing piece at the pilot is sub-threshold signal, not occlusion or stacking.
- The denominator counts on-route ticks from tick 0, before any trail exists. So the 90% target is ill-posed as measured, which is a measurement flaw rather than a controller limit.
- The saturation half (at most 5% above 0.35) is well-posed, and it is a trail property. The follower clamps and does not care; the seed's modules were qualified for the range. The proposed winner fails it at 35% on the 256 mazes.

**"The trails are usable" should be "trails help as route marking".** Nothing shows the gradient is used. The peer effect is on the later-leg rate, on 64 selection mazes, at a setting picked as the maximum. It is not criterion 3's measure (first-B time of later discoverers).

## 2. Fallback or amendment?

Not the fallback.
- Astra's original sentence is "controller failure does not automatically justify changing trail chemistry" (`docs/reviews/20261002-E3b-0-plan/astra.answer.md:33`). So the plan's clause argues against the nonlinear fallback here, not against amending the test.
- Nonlinear trails would not help a memoryless bilateral follower turn round, and they would break the linear peer controls.

## 3. Changes to the amendment

1. **Polarity as reported: agreed, with honest wording.** Say "the slope exists physically (gradient share) but is behaviourally unverified", not that the gradient share is the polarity check. E3b-1 should make no directional-trail claim unless a controller that can read a longitudinal slope (for example, one with temporal comparison) passes the test. Adding such a controller as an instrument changes neither the trails nor the rule.
2. **Keep a saturation condition; drop only the 90% in-range half.** Rate rises monotonically with d₀ and with lower μ in the recorded rows. Without a cap, the rule plus the μ 0.0025 widening walks straight into saturation, and criterion 4 fails later at higher cost. Two options:
   - keep above ≤ 5%: only six rows pass (μ 0.01, λ 0.04, half d₀; and the four μ 0.02 rows), with rates of 3.8-4.9;
   - or state a looser cap as post hoc, and require the component tests at the high levels actually met (say the 95th and 99th percentile) before Stage C. The amendment's wording says "including the low ones" and misses the high ones.
3. **The in-range share should be redefined, not just demoted.** Count unoccluded noses, after the goal's trail first exists, with the sub-threshold share reported separately.
4. **Shared versus shared − none is moot.** The no-trail follower does not depend on the trail constants, so both give the same ordering. Run none once on all 256 selection mazes and report the difference.
5. **Selection bias is acceptable for choosing.** Mazes 0-63 are a subset of the selection set, so the +2.85 is optimistic, and only the report mazes (1000-1255) count. The real exposure is that the rule change itself was fitted to these mazes, so the results should carry the "adaptively selected" label, not just a footnote.

## 4. Fix before the rerun

- **The recorded config looks wrong.** `stage-b.json`'s `resolved_config` shows `max_ticks` 1200 and the pilot constants, while the stage ran at H 2400 across the grid. Confirm it is only the frame's base config and say so, or record the per-setting config.
- **Check the polarity ceiling on the CPU.** Report time-to-A distributions and the pass rate at 4× for the toward heading, with "toward" pointing at the previous route cell. This shows whether the low ceiling is the follower or the limit.
- **Record the reviews before the new stage.** Write the amendment as D178, with both reviews archived. The widening should be a new stage that reads Stage B's record, not a re-execution of Stage B.
- **Expect the edge again.** If μ 0.0025 wins, the one allowed widening is spent; state now that the search stops there.