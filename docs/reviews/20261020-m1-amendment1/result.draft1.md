*Draft 1 of the section appended to `docs/memory/M1-RESULTS.md`, as reviewed in r3 (rebuilt from the edits made after the review; the table note and the roadmap annotation as in r3's prompt).*

## Amendment 1's result: D1's targeted replication (2026-10-20)

*Added after the replication ran, without changing the text above. The design is M1-PLAN's amendment 1, reviewed in
two rounds and committed and pushed before it ran (d025d7a, D351). Numbers from `runs/memory-m1/d1_small_k.json`
(compute in `d1_small_k-compute-record.json`, the run's console output in `d1_small_k_run.txt`).*

- **The run.** On 2026-10-20 at 14:33 UTC, at commit d025d7a: N2's two panels with M1's four amplitude arms and four
  new ones (k = 1/8, 1/16, 1/32, 1/64), 184 s of CPU, exit 0. The rerun reproduced M1's arrays exactly for the old
  arms (largest gap 0; the batch had M1's row count).
- **D1 does not fire.** On D1's basis (a), the conditions are now met on both panels:
  - coverage 100% of N2's intact-arm numerator and denominator;
  - the baseline lead ratio 1.69 and 1.76;
  - balance: the worst used stratum is 9.5% (seed 7600) and 9.3% (seed 7700) from the reference median's E[a | k],
    in stratum 0; every other used stratum is within 2.1%.

  f = **1.01 [0.96, 1.05]** on seed 7600 and **1.03 [0.98, 1.07]** on seed 7700, with no bad resamples. Both
  intervals lie wholly above 0.25, so D1 does not fire: **amplitude does not account for most of N2's tick-30 lead;
  at matched amplitude more than a quarter of it remains.** Both point estimates are above 0.75 (descriptive).
- **What f is here** (fixed in the amendment). f is the fraction of N2's lead *within the used strata* that survives
  standardisation, over a mixture of observations that the new arms changed. It is not the fraction of the original
  intact lead removed. Beside it, descriptively: N2's standardised lead is 0.175 and 0.195, against M1's intact
  eligible leads of 0.170 and 0.169 (ratios 1.03 and 1.16). The new arms supply 32% (seed 7600) and 25% (seed 7700)
  of N2's used-strata numerator; the old arms supply the rest.
- **Scale sensitivity** (diagnostics, gating nothing). N2's median within-genome ratios r(1/64)/r(1/32) and
  r(1/8)/r(1/4) are 0.9999 and 0.9998 (seed 7600), 0.9999 and 0.9998 (seed 7700), inside the band [0.8, 1.25], so the
  reading carries no annotation. N2's share against each new arm's own start is 0.47, 0.53, 0.56 and 0.54 at
  k = 1/8 to 1/64 (seed 7600) and 0.56, 0.45, 0.44 and 0.46 (seed 7700), against its intact 0.444 and 0.443. As k
  falls, the population above the floor shrinks (849 to 385 genomes at seed 7600), so these shares are over different
  genomes.
- **On ‖δa(0)‖** (descriptive, as planned). The balance condition fails there, and badly: in the used ‖δa(0)‖
  strata, N2's mean a is 1.3 to 2.4 times the reference median's (worst 2.44, seed 7600). At matched size of the
  activity difference, N2's difference is about twice as visible to the turn read-out at the start. f = 1.01 and 1.02
  on that basis, with the conditions unmet; the standardised lead is 0.61 and 0.65 of the intact lead. M1's own
  ‖δa(0)‖ reading (f = 0.85 [0.70, 0.98] and 0.92 [0.82, 1.02], above) was on the old arms only.
- **Reading.** D1 is resolved on this probe: matching amplitude across graphs, with every N2 genome represented at
  some matched amplitude, leaves N2's lead in place. This is accounting, not mechanism. The match is on a, with
  mismatched k: N2's matched observations come partly from strongly shrunk arms and the nulls' from natural or
  enlarged ones. N2's retention barely depends on the scale of the difference, which makes that mismatch matter
  little here. The ‖δa(0)‖ imbalance is a separate, descriptive observation: at the ramp's end, N2's activity
  difference is better aligned with the read-out than the nulls' at the same norm (a = ‖c‖ ‖δa‖ |cos θ|, so within a
  narrow ‖δa(0)‖ stratum the ratio of mean a is approximately a ratio of starting alignments). D2 measured the change in alignment over the
  follow-up, not its starting level, so this is a separate quantity; it bears on the size of a, not on its retention.
