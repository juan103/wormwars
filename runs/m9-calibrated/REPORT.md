# N2 / SH / RD comparison

**Motor gains are calibrated per graph** (each graph's random population produces the same mean |forward| and |turn| as N2 does at the hand-chosen gain), so this compares control rather than raw read-out scale.

Total wall time 0.897 h over 45 runs.

Scores are held-out foraging score (surviving swarm energy / starting energy),
on world ids never used for selection. The unit of analysis is the run.

## Final held-out score

```
N2   1.4115 [1.3661, 1.4526] (1g x 15r)
SH   1.4581 [1.3851, 1.5515] (5g x 15r)
RD   1.4521 [1.3982, 1.5103] (5g x 15r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2          15    1.4115   0.0884   1.2274   1.5351
graph     runs      mean       sd      min      max
SH1          3    1.6073   0.1794   1.4032   1.7402
SH2          3    1.4042   0.0453   1.3713   1.4559
SH3          3    1.4161   0.1428   1.2668   1.5513
SH4          3    1.3845   0.0762   1.3101   1.4623
SH5          3    1.4784   0.0217   1.4571   1.5005
graph     runs      mean       sd      min      max
RD1          3    1.4659   0.1253   1.3603   1.6044
RD2          3    1.5303   0.0871   1.4643   1.6290
RD3          3    1.4237   0.1024   1.3422   1.5386
RD4          3    1.4343   0.0520   1.4017   1.4943
RD5          3    1.4061   0.1141   1.2781   1.4972
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = -0.0466 [-0.1480, +0.0391], P(N2 > SH) = 0.167   -> no separation between N2 and SH
N2 - RD = -0.0406 [-0.1132, +0.0286], P(N2 > RD) = 0.130   -> no separation between N2 and RD
SH - RD = +0.0060 [-0.0896, +0.1136], P(SH > RD) = 0.524   -> no separation between SH and RD
```

## Area under the fitness curve (speed of improvement)

```
N2   1.3586 [1.3441, 1.3732] (1g x 15r)
SH   1.4586 [1.4329, 1.4836] (5g x 15r)
RD   1.4705 [1.4385, 1.5056] (5g x 15r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2          15    1.3586   0.0302   1.3018   1.3968
graph     runs      mean       sd      min      max
SH1          3    1.4692   0.0411   1.4300   1.5119
SH2          3    1.4574   0.0393   1.4120   1.4823
SH3          3    1.4516   0.0683   1.3861   1.5224
SH4          3    1.4418   0.0647   1.4043   1.5166
SH5          3    1.4729   0.0646   1.3983   1.5110
graph     runs      mean       sd      min      max
RD1          3    1.4752   0.1244   1.3727   1.6135
RD2          3    1.4699   0.0548   1.4155   1.5250
RD3          3    1.4715   0.0409   1.4264   1.5063
RD4          3    1.4734   0.0711   1.4143   1.5523
RD5          3    1.4626   0.0842   1.3867   1.5531
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = -0.0999 [-0.1289, -0.0704], P(N2 > SH) = 0.000   -> N2 < SH
N2 - RD = -0.1119 [-0.1496, -0.0768], P(N2 > RD) = 0.000   -> N2 < RD
SH - RD = -0.0120 [-0.0553, +0.0288], P(SH > RD) = 0.288   -> no separation between SH and RD
```

## Held-out score per GPU-hour

```
N2   69.9901 [68.0453, 71.8714] (1g x 15r)
SH   73.5628 [69.8826, 78.2749] (5g x 15r)
RD   73.2545 [70.5425, 76.2040] (5g x 15r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2          15   69.9901   3.8708  62.0520  76.6636
graph     runs      mean       sd      min      max
SH1          3   81.1016   9.0196  70.8586  87.8553
SH2          3   70.8900   2.3323  69.1781  73.5465
SH3          3   71.4566   7.1410  63.9449  78.1579
SH4          3   69.8165   3.8154  66.0796  73.7059
SH5          3   74.5493   1.1297  73.3848  75.6407
graph     runs      mean       sd      min      max
RD1          3   73.9743   6.4144  68.5972  81.0742
RD2          3   77.2180   4.3675  73.9337  82.1745
RD3          3   71.8606   5.1908  67.7936  77.7072
RD4          3   72.2718   2.4597  70.7188  75.1078
RD5          3   70.9478   5.7063  64.5484  75.5067
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = -3.5727 [-8.5577, +0.6135], P(N2 > SH) = 0.052   -> no separation between N2 and SH
N2 - RD = -3.2644 [-6.7481, +0.0678], P(N2 > RD) = 0.027   -> no separation between N2 and RD
SH - RD = +0.3083 [-4.5065, +5.7294], P(SH > RD) = 0.524   -> no separation between SH and RD
```

## Reading this

N2 has one graph, so its interval carries run-to-run variation only. SH and RD have K
graphs each, so their intervals also carry graph-to-graph variation and are wider by
construction. The question is whether N2 sits outside the SH/RD distribution over graphs,
not whether two equally-estimated means differ.

This measures wiring **plus this specific sensor/motor interface** on **this game**. It is
not a test of whether biological wiring is better in general.