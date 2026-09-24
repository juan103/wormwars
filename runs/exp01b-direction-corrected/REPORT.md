# N2 / SH / RD comparison

**Motor gains are calibrated per graph** (each graph's random population produces the same mean |forward| and |turn| as N2 does at the hand-chosen gain), so this compares control rather than raw read-out scale.

Total wall time 1.058 h over 45 runs.

Scores are held-out foraging score (surviving swarm energy / starting energy),
on world ids never used for selection. The unit of analysis is the run.

## Final held-out score

```
N2   1.6285 [1.5882, 1.6676] (1g x 15r)
SH   1.5591 [1.4684, 1.6319] (5g x 15r)
RD   1.5345 [1.4828, 1.5862] (5g x 15r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2          15    1.6285   0.0819   1.4809   1.7408
graph     runs      mean       sd      min      max
SH1          3    1.6111   0.0919   1.5193   1.7031
SH2          3    1.5762   0.0661   1.5100   1.6422
SH3          3    1.4246   0.1355   1.3325   1.5803
SH4          3    1.5325   0.1841   1.3400   1.7069
SH5          3    1.6512   0.0068   1.6449   1.6585
graph     runs      mean       sd      min      max
RD1          3    1.5978   0.0954   1.4938   1.6813
RD2          3    1.5611   0.0332   1.5233   1.5859
RD3          3    1.4950   0.0694   1.4203   1.5573
RD4          3    1.5663   0.0392   1.5359   1.6105
RD5          3    1.4522   0.0147   1.4369   1.4661
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = +0.0694 [-0.0152, +0.1689], P(N2 > SH) = 0.941   -> no separation between N2 and SH
N2 - RD = +0.0940 [+0.0285, +0.1597], P(N2 > RD) = 0.998   -> N2 > RD
SH - RD = +0.0247 [-0.0785, +0.1164], P(SH > RD) = 0.699   -> no separation between SH and RD
```

## Area under the fitness curve (speed of improvement)

```
N2   1.5902 [1.5743, 1.6066] (1g x 15r)
SH   1.5226 [1.4928, 1.5525] (5g x 15r)
RD   1.5228 [1.4898, 1.5662] (5g x 15r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2          15    1.5902   0.0332   1.5321   1.6516
graph     runs      mean       sd      min      max
SH1          3    1.4989   0.0519   1.4520   1.5547
SH2          3    1.5321   0.0711   1.4621   1.6042
SH3          3    1.5141   0.0658   1.4385   1.5589
SH4          3    1.5140   0.0606   1.4446   1.5562
SH5          3    1.5538   0.0498   1.5147   1.6099
graph     runs      mean       sd      min      max
RD1          3    1.5103   0.0748   1.4428   1.5908
RD2          3    1.5141   0.0244   1.4877   1.5357
RD3          3    1.5829   0.1010   1.4664   1.6435
RD4          3    1.5146   0.0618   1.4704   1.5852
RD5          3    1.4921   0.0386   1.4492   1.5241
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = +0.0676 [+0.0336, +0.1017], P(N2 > SH) = 1.000   -> N2 > SH
N2 - RD = +0.0674 [+0.0207, +0.1051], P(N2 > RD) = 0.998   -> N2 > RD
SH - RD = -0.0002 [-0.0523, +0.0451], P(SH > RD) = 0.511   -> no separation between SH and RD
```

## Held-out score per GPU-hour

```
N2   77.7039 [75.6429, 79.6102] (1g x 15r)
SH   67.1825 [60.5271, 74.2059] (5g x 15r)
RD   58.7254 [56.8308, 60.9107] (5g x 15r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2          15   77.7039   4.0845  69.9424  82.3958
graph     runs      mean       sd      min      max
SH1          3   78.1871   4.3540  73.7908  82.4974
SH2          3   73.5373   6.0661  67.5712  79.6986
SH3          3   58.9822   5.5896  55.1239  65.3923
SH4          3   61.8647   7.6651  53.8868  69.1732
SH5          3   63.3411   1.9078  61.9461  65.5152
graph     runs      mean       sd      min      max
RD1          3   61.2827   5.4148  55.4489  66.1477
RD2          3   58.3148   0.9971  57.2558  59.2355
RD3          3   56.8613   2.7100  53.9090  59.2358
RD4          3   60.6466   1.1681  59.2985  61.3588
RD5          3   56.5219   1.2797  55.1577  57.6958
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = +10.5214 [+3.3047, +17.4178], P(N2 > SH) = 0.998   -> N2 > SH
N2 - RD = +18.9785 [+16.0314, +21.7009], P(N2 > RD) = 1.000   -> N2 > RD
SH - RD = +8.4571 [+1.5739, +15.7074], P(SH > RD) = 0.994   -> SH > RD
```

## Reading this

N2 has one graph, so its interval carries run-to-run variation only. SH and RD have K
graphs each, so their intervals also carry graph-to-graph variation and are wider by
construction. The question is whether N2 sits outside the SH/RD distribution over graphs,
not whether two equally-estimated means differ.

This measures wiring **plus this specific sensor/motor interface** on **this game**. It is
not a test of whether biological wiring is better in general.