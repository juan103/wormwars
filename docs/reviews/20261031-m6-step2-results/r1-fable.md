**Verdict: fix then publish.** Every number in the draft matches the records. The reader applied the plan's checks and wordings correctly. Three interpretive sentences go further than the data, and the warm-up hazard needs one concrete figure. The fixes are wording only.

**1. Numbers.** I re-derived everything I could without a shell. All of it matches.

- The relative-change tables, the controls' table, the validation table, the T0 figures, the matched T1 minus T0 difference, the associations and the tau profiles all round correctly from `reading.json`.
- The block means in `reading.json` agree to every digit with the independent recomputation in `check_step2.txt`. Both scripts' formulas are the plan's. I could not run the bootstrap myself, so the intervals rest on reading the code, which is correct.
- The validation ratios I recomputed by hand from `probe.json`: the switch champion's 0.70 at k = 0.25 is indeed the largest of the 102. The next is T1-R1-N2 run 3 at 0.43. "Shrank least" holds.
- The compute record is internally coherent: 53,952 worlds is 174 runs times their strain-arms times 32 worlds, and the ticks are 200 per world. The reflog shows the plan's commit pushed at 23:16:39 UTC and the run's attempt file stamped 23:17:00 UTC. The push came first, by about 20 seconds.
- The timing-run champion's five scores match the log to three decimals.

**2. The readings.** Correct. The primary, the caveat, the sensitivity and both control wordings follow the plan's templates and cases verbatim. The gate covers consistency and validation, and leaves the numbers in place, as the plan says. The k = 2 `not_below_1` list is the plan's own reporting rule applied literally, since the plan only named k = 4 as the slowing exception. The draft's note is honest and sufficient. Do not alter the record or the reader after the run.

**3. Overclaiming.** Four points.

- **"Most of the cost goes with the sensory and motor neurons' speed."** This is the main overclaim. The complement arm, boundary neurons scaled and interior left alone, was not run. So the 18.5 points cannot be attributed to the 39 boundary neurons rather than to speeding both together. Fable's design-round framing was one-directional: if the interior arm cost as much as full scaling, latency would be ruled out. The outcome leaves latency standing. It does not establish it. Rewrite as: with the 39 boundary neurons left at their own tau, the cost fell from about a quarter to about 6%; the remaining cost appears only when they are sped up too, and whether speeding only them would cost that much was not tested. Add the count, 39 of 302, which is committed in `timing-runs.md`. Soften "fits a response-speed account better" to "leaves the simplest response-speed account standing".
- **The probe's read-out is the turn motor neurons,** which the interior arm leaves unscaled. So the interior arm's 0.57 is read through neurons whose own time constants did not change. Say this beside "the interior arm shortened the history effect less".
- **"Nothing here singles out T1's single-nose task."** The matched interval is -6.1 to +0.4 points, almost all on the side of T1 dropping more. "No difference was detected" is right. "Nothing singles out T1" and "as large in T0 as in T1" are too strong. Say the interval allows T1 to drop up to 6 points more.
- **"Tuned to their time scale."** Two softenings. With five k values, "peaks at or near" the evolved scale. And the generation-0 controls also lose in both directions, 8.6% at 0.25 and 14.2% at 4, so a two-sided loss is not by itself evidence that selection did the tuning. The "does not establish" list already half says this; the headline bullet should too.

The warm-up hazard is stated but not made concrete. Add the scale: tau runs to 20 ticks, so at k = 4 a neuron at the ceiling has an 80-tick time constant inside a 200-tick episode, and the median neuron about 13 ticks. Put it in the "tuned" bullet, where "more steeply on the slow side" currently stands without it.

The association with a is handled correctly. The confound with intact score is named and the dose-response reading refused, as the plan required. Optionally, marked after the data, a partial rank correlation would be about -0.3, so the confound explains part of the association, not all. Not required.

**4. The roadmap step.** Stopping and folding into the synthesis is D379's order, read correctly. The synthesis must not say: that the history effect helps or does not help foraging; that selection tuned the champions' time scale; that T0 and T1 are equal; that the cost sits in the sensory and motor neurons; that slowing costs more because of tuning rather than warm-up; or that the a-association is a dose-response. It must keep the two "exceeded" sentences next to the plan's floor caveat, keep step 2 labelled exploratory with no pre-registration, and take the new compute total from `summary.json` rather than by adding 3.64 to 113.59.

**5. Fixes before publishing**

1. Rewrite the interior-arm bullet and its "establishes" line as in point 3, with the 39-neuron count.
2. Add the read-out caveat for the interior arm's probe ratio.
3. Replace "Nothing here singles out T1" and "as large in T0" with the interval wording.
4. Soften "tuned" to "at or near", and note the generation-0 controls' two-sided loss.
5. Give the warm-up hazard its concrete scale, in the "tuned" bullet.