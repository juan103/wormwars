# M6 step 2: the timing and smoke runs seen before the plan (archived at Astra's request)

All on the CPU of the tested machine, 2026-10-30, on T1-M0-N2 run 0's champion (g39) unless stated. The worlds are
02b's 32 criticality worlds (`grid.PROBE_IDS[:32]`), and the scores are `rollout(...).score` means over those worlds.
The code was inline Python run from the repository root with `CUDA_VISIBLE_DEVICES=""`; its essentials are below.

## 1. Scaled tau, unchanged substeps (the design note's figures)

`g = repeat(champ, 4); g.tau[1] *= 0.5; g.tau[2] *= 0.25; g.tau[3] *= 2.0`, then one `rollout`:

```
T1-M0-N2-run00 1 genome x 32 worlds: 4.2 s; mean score 2.8243456
4 genomes: 14.2 s; means [2.8243456 2.6195273 2.0798616 2.8395457] null equal: True
```

## 2. A substeps setting on the experiment config that did not reach the brain

The substeps were set on `cfg.brain` and not on the genome's own config, which `Brain` reads:

```
T1 1 (13.33 s for 3, [2.8243456 x3], substeps 32)
T1 0.25 (13.49 s for 3, [2.0798616 x3], substeps 128)   # identical to (1): the setting had no effect
T1 4 (13.52 s for 3, [2.2331295 x3], substeps 8)
T0-M0-N2-run00: T0 1 (13.49 s for 3, [2.7597685 x3], substeps 32)
```

The k = 4 figure here is tau x 4 at 32 substeps, not an exact rescaling.

## 3. The exact rescaling (tau x k, substeps 32/k, set on the genome's config)

```
1 32 13.7 s for 3; 2.8243456
0.25 128 52.8 s for 3; 2.0430784
0.5 64 26.9 s for 3; 2.611343
2 16 7.3 s for 3; 2.8312051
4 8 4.1 s for 3; 2.2273297
```

## 4. The driver's smoke run (2 worlds, `score_run` and `probe_one`)

- g39: 0.25 2.053, 0.5 2.653, 1 2.877, 2 2.960, 4 2.272, interior 0.25 2.667.
- g00: 0.25 2.585, 1 2.360, 4 1.896.
- drift0: 0.25 0.753, 1 0.756, 4 1.220.
- The run took 11.3 s.
- The genome hashes matched M6-0's for g39, g00 and drift0.
- The champion's tau profile: median 3.298, 2.3% at the floor, 3.0% at the ceiling; 39 boundary neurons.
- The probe on the own bank, continued integral over ticks 1 to 100: 8.60 at k = 1, 2.03 at 0.25, 24.19 at 4, and
  2.70 for the interior arm. The full-probe integrals were 8.60, 1.06, 18.31 and 2.06.
