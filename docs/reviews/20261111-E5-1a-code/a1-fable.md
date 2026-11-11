**Verdict: amend and rerun, but tighten the amendment first.** The diagnosis holds; the criterion as coded is weaker than it needs to be, and the sabotage does not show what §14.3 says it shows. I ran nothing (read-only), so the one-step magnitudes below are expectations.

## Diagnosis: right in substance
- **Same genomes and inputs:** `state_level_diagnosis_shapes.json` reproduces attempt 1's CPU−CUDA numbers to the last digit.
- **The float64 reference is genuine:** `Brain` takes its dtype from the genome throughout (`dense()`, `c`, `den`, `initial_state`), and nothing downcasts.
- **Ratios:** 31 to 104, so "30 to 100" is fair.
- **Over-generalised:** "the evolved champions amplify" is too broad. At 16 × 8, only run01 exceeds 1e-4 CPU−CUDA; 13 of 16 stay within 4.5e-5. It is a tail over (genome, input history) that grows with rows, and per-genome values at the stage's shapes are not recorded.
- **Motor figure is scoped narrowly:** the 2e-5 is at 16 × 8, where the state gap was 3.2e-4, not at the stage's shapes, where it is 10 to 30 times larger.

## Amendment: three changes
1. **Judge per strain, not per group.** The training shape is one group of 128, so the worst genome sets a bound of about 0.22 for all 16. Reduce over rows, neurons and ticks per strain, and record per strain.
2. **Add a resynchronised one-step check at the registered 1e-4.** Each tick, step CUDA from the CPU float32 state and compare with the CPU's step, for every genome, shape and tick. Local error is not amplified, and I expect 1e-6 to 1e-5. Without it the check has almost no power on the champions: the bound of 0.22 to 0.69 allows a device gap 15 to 50 times the observed 0.0025 to 0.011.
3. **Factor and floor:** 1.5 and 1e-4 are fine once 1 and 2 are in. Observed ratios are 0.97 to 1.03, so 1.5 is not tuned to pass. Without 2, bound the device gap directly instead (for example ≤ 0.25 × float32's error + 1e-4).

## Sabotage
`amend1-sabotage.txt` is a smoke run: its groups are "small" (2 × 4, 10 ticks), where nothing amplifies and the bound is about 1e-4. It does not show the formal criterion can fail on a champion group at 300 ticks. It is also not in `scripts/e5_1_sabotage.py`. Redo it at 300 ticks on a champion group, from the committed script, and say so in the text.

## Text fixes in §14.3
- **"255 of 256" is wrong.** `cuda.json` has share 0.9921875 for the H1-bite pursuit trace, which is 254 of 256 (largest difference 0.19 cells). That is exactly the two-world limit; H2-0.5 is 256 of 256.
- **"Their float32 error is about 10⁻⁵"** for generation 0 has no committed source: the diagnosis covers only the champions.
- **Worth adding:** the champions' score rows are identical in about 99.6 to 100% of worlds. That is the best evidence the amplification does not bite in the task.

## Reruns
Steps 1 to 3 is right: `guard` enforces `require_same_code` over `scripts/`, and steps 1 and 2 cost about 20 minutes. State two things in the amendment:
- **The cap clock:** attempt 1's 2 465 s stays in `runs/e5-1a/compute.json`, so it counts against the 6 hours. The diagnosis's GPU time is uncounted.
- **The record:** attempt 2 is the record, and a score-level check that passed in attempt 1 and fails in attempt 2 is a stop.

No further review round is needed if these are taken as written.