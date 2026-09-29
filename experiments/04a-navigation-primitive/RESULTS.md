# 04a: results

**Outcome, in the wording fixed in advance: "04a: passed".** 8 of the 12 shaped runs passed all
five rules on 1 024 hold-out worlds (the registered bar was 6). All 4 unshaped runs passed too.

Written 2026-09-29, after the evaluation, for review by Astra 6 and Fable 5.1. Every number below
comes from the committed records in this folder: `evaluation.json` (the verdict, the rules, every
per-world count), `evaluation-extras.json`, `evaluation_events.npz` (the event tables),
`train-A.json`, `train-B.json`, `projection.json` and `compute-record.json`.

## What ran

As registered in [`PREREGISTRATION.md`](PREREGISTRATION.md) (v5, bound at `e3d68be`; D103-D109):
- 16 N2 runs, 1 000 generations each, with 02's optimizer (32 genomes, one island), 8 training worlds
  per genome per generation; runs 0-11 with shaping c = 0.5, runs 12-15 without;
- batched 8 runs at a time, each with its own random streams; batch A (runs 0-7) at `7ec22bb`,
  batch B (runs 8-15) at `75307a3`, the evaluation at `2b9ed94`. Only records changed between these
  commits, and every stage passed its same-code, same-environment and committed-record checks;
- each run's champion is its best checkpoint on 256 validation worlds (41 checkpoints), fixed before
  the hold-out; each run's generation-0 baseline is its generation-0 checkpoint;
- the hold-out: 1 024 worlds (996 301 000-996 302 023), used once.

**Compute:** 2.91 GPU-hours of the 6-hour cap (`compute-record.json`): the projection, batch A (1.44
h), batch B (1.36 h) and the evaluation (304 s). One attempt per stage; no rerun.

## The verdict, run by run

| Run | Arm | Hold-out mean | Episodes with ≥ 2 | Mirrored | Constant probe | Gen 0 | Passed |
|---|---|---|---|---|---|---|---|
| 0 | shaped | 2.15 | 82.8% | 0.09 | 0.14 | 0.23 | yes |
| 1 | shaped | 2.05 | 74.8% | 0.16 | 0.14 | 0.63 | no: reliability |
| 2 | shaped | 2.63 | 92.5% | 0.15 | 0.17 | 1.08 | yes |
| 3 | shaped | 2.28 | 88.1% | 0.15 | 0.24 | 0.17 | yes |
| 4 | shaped | 2.29 | 81.3% | 0.20 | 0.24 | 0.96 | yes |
| 5 | shaped | 1.99 | 70.2% | 0.16 | 0.21 | 0.54 | no: reliability |
| 6 | shaped | 2.24 | 89.6% | 0.16 | 0.22 | 0.00 | yes |
| 7 | shaped | 2.32 | 88.7% | 0.12 | 0.27 | 0.55 | yes |
| 8 | shaped | 2.11 | 73.3% | 0.21 | 0.30 | 0.63 | no: reliability |
| 9 | shaped | 2.27 | 87.1% | 0.17 | 0.23 | 0.24 | yes |
| 10 | shaped | 2.30 | 82.8% | 0.17 | 0.21 | 0.27 | yes |
| 11 | shaped | 2.10 | 76.8% | 0.17 | 0.22 | 0.08 | no: reliability |
| 12 | unshaped | 2.81 | 96.1% | 0.07 | 0.08 | 0.16 | yes |
| 13 | unshaped | 2.26 | 90.5% | 0.14 | 0.16 | 1.00 | yes |
| 14 | unshaped | 2.25 | 84.4% | 0.15 | 0.30 | 0.24 | yes |
| 15 | unshaped | 2.14 | 88.8% | 0.19 | 0.34 | 0.12 | yes |

Means are targets reached per 300-tick episode. The four failing runs failed on reliability only
(70-77% of episodes with at least 2 targets, against 80%); every run passed the other four rules.

- **Beats the baselines:** every run beat constant motion (0.44), the random walk (0.29), the
  wall-follower (0.69) and level kinesis K (0.90) with a lower bound of the paired difference of at
  least 1.03 targets, against the required 0.5.
- **Misled by the mirrored cue:** reading the scent at the mirrored point dropped every champion to
  0.07-0.21. For 97-100% of episodes, the head ended the unfinished leg closer to the decoy than to
  the true target (`evaluation-extras.json`, decoy capture). Lower bounds of (0.5 × real − mirrored):
  0.80-1.32, against the required 0.
- **Helped by the real cue:** with the scent replaced by a constant level, the champions fell to
  0.08-0.34; lower bounds of (real − constant) were 1.73-2.70, against the required 0.5.
- **Beats generation 0:** every run beat its own generation-0 checkpoint (0.00-1.08) by a lower bound
  of at least 1.22.
- **The share:** 8 of 12 shaped runs, 0.67, with an exact one-sided 95% lower bound of 0.39. As §6
  of the registration says, this is a benchmark on these runs and these hold-out worlds, not a
  population success rate; each run's bounds are marginal, not simultaneous.

## What the champions are, and are not

**They steer by the cue, slowly.** The counts sit in a narrow band: most episodes reach exactly 2 or
3 targets, and almost none reach 0 (0-19 of 1 024 per run). That is why means of 2.1-2.3 clear the
80% reliability bar. But:
- **they are far from E1's scripted navigator.** The champions reach 23% to 32% of the oracle's mean
  (8.83); S-const, E1's navigator, reaches 8.71 on the same worlds;
- **their performance-equivalent gain is low:** on the hold-out gain curve, the champions' means fall
  between the stereo steerer at k = 2 (1.09) and k = 8 (2.99). The interpolated equivalent k is
  3.5-6.9. The registration's caveat applies: this is a performance equivalence, not a measured
  steering gain;
- **their paths are indirect:** the median path efficiency of finished legs is 0.27-0.34, against
  0.83 for S-const and 0.70 for S-const at k ≤ 32; the median finished leg takes 86-116 ticks, against
  31 for S-const.

So 04a's rules, taken from E1's positive control, test whether a brain navigates by the cue at all,
reliably, better than blind search and better than where it started. The champions do. They do not
test how well: by speed and path, these are weak navigators.

**Shaping.** The unshaped arm passed 4 of 4, and its best run (12) was the best of all 16 (2.81).
With 4 unshaped runs, this is descriptive only (§6), but it does not support the idea that the
shaping term was needed. E1's pilot met the design's condition for shaping (74% of random genomes
scored zero); evolution found the cue without it here.

**Training curves.** Validation means rose from 0.0-1.1 at generation 0 to about 1.5-2.1 by
generation 100 and moved noisily within about 1.5-2.9 afterwards; champions came from generations
175-950 (`train-A.json`, `train-B.json`). The development pilot's plateau near 2 (§9) described this
well.

## Checks

- **The replay check:** each champion's checkpoint batch, reloaded from disk and replayed in the same
  composition on the 256 validation worlds, reproduced every recorded per-world count (256 of 256,
  for all 16 runs; `evaluation-extras.json`).
- **The module for E3:** run 2, the passing shaped champion with the highest hold-out mean (2.63). It
  was chosen on the hold-out, so that mean is optimistic; E3 re-measures it on fresh worlds.
- **Baselines on 04a's hold-out, re-run as registered:** S-const 8.71, S-const at k ≤ 32 5.56, M-avg
  2.18, the oracle 8.83, K 0.90, the wall-follower 0.69, constant motion 0.44, the random walk 0.29.
  These agree with E1's gate within 0.06.

## Deviations and disclosures

- **No deviation from the registration** that I have found.
- **Timing:** the projection measured 5.25 s per generation; training ran at 4.8-7 s. Batch A slowed
  for some minutes when other CPU work (03m's development and tests) ran beside it; the cap was never
  close.
- **The event tables are 44 MB** (`evaluation_events.npz`, 16 × 4 neural arms and 18 scripted arms ×
  1 024 worlds), within GitHub's limits but large.
- **Genome files are local** (`runs/e04a/`), not published, because early genomes carry the
  connectome's weights (D028); their hashes are in the records.
- **The limits in §10 of the registration stand:** no null-graph comparison, so nothing here says N2's
  wiring helps; the blind baselines may be under-tuned; generation 0 is a best-of-32 baseline, not an
  equal-budget random search.

## What this means for the roadmap

- **E3 has a module:** a cue-following N2 navigator that reaches moved targets reliably, if slowly.
- **Whether a better optimizer finds a better navigator is E2's question,** which now starts from a
  measured baseline: 02's optimizer, 1 000 generations, champions at k ≈ 4 equivalent.
- **Whether the result depends on N2's wiring** needs the null-graph bridge (Bridge 1), deferred.
