# N2 / SH / RD comparison

Total wall time 0.345 h over 18 runs.

Scores are held-out foraging score (surviving swarm energy / starting energy),
on world ids never used for selection. The unit of analysis is the run.

## Final held-out score

```
N2   1.3689 [1.2664, 1.4699] (1g x 6r)
SH   1.5499 [1.4266, 1.6567] (3g x 6r)
RD   1.5005 [1.4329, 1.5772] (3g x 6r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2           6    1.3689   0.1415   1.1617   1.5737
graph     runs      mean       sd      min      max
SH1          2    1.5666   0.0199   1.5525   1.5807
SH2          2    1.4266   0.0193   1.4129   1.4402
SH3          2    1.6567   0.0657   1.6102   1.7031
graph     runs      mean       sd      min      max
RD1          2    1.5029   0.0214   1.4878   1.5180
RD2          2    1.5684   0.1084   1.4918   1.6451
RD3          2    1.4302   0.0377   1.4035   1.4569
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = -0.1811 [-0.3293, -0.0296], P(N2 > SH) = 0.009   -> N2 < SH
N2 - RD = -0.1316 [-0.2597, -0.0062], P(N2 > RD) = 0.020   -> N2 < RD
SH - RD = +0.0494 [-0.0835, +0.1757], P(SH > RD) = 0.767   -> no separation between SH and RD
```

## Area under the fitness curve (speed of improvement)

```
N2   1.3757 [1.3237, 1.4173] (1g x 6r)
SH   1.4338 [1.3927, 1.4656] (3g x 6r)
RD   1.5146 [1.4747, 1.5538] (3g x 6r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2           6    1.3757   0.0650   1.2585   1.4429
graph     runs      mean       sd      min      max
SH1          2    1.4467   0.0390   1.4192   1.4743
SH2          2    1.4077   0.0785   1.3521   1.4632
SH3          2    1.4469   0.0404   1.4184   1.4755
graph     runs      mean       sd      min      max
RD1          2    1.4929   0.0173   1.4806   1.5051
RD2          2    1.5395   0.0062   1.5350   1.5439
RD3          2    1.5114   0.1008   1.4401   1.5826
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = -0.0581 [-0.1195, +0.0019], P(N2 > SH) = 0.029   -> no separation between N2 and SH
N2 - RD = -0.1389 [-0.2030, -0.0792], P(N2 > RD) = 0.000   -> N2 < RD
SH - RD = -0.0808 [-0.1372, -0.0274], P(SH > RD) = 0.001   -> SH < RD
```

## Held-out score per GPU-hour

```
N2   70.0152 [63.7570, 76.2983] (1g x 6r)
SH   81.7389 [75.3294, 87.3947] (3g x 6r)
RD   79.2382 [75.7008, 83.3222] (3g x 6r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2           6   70.0152   8.6870  58.7377  82.0461
graph     runs      mean       sd      min      max
SH1          2   82.4927   1.2667  81.5970  83.3884
SH2          2   75.3294   1.0842  74.5628  76.0960
SH3          2   87.3947   3.6892  84.7860  90.0033
graph     runs      mean       sd      min      max
RD1          2   79.3352   1.2292  78.4660  80.2044
RD2          2   82.8477   5.7511  78.7811  86.9144
RD3          2   75.5315   1.9386  74.1607  76.9023
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = -11.7237 [-20.1643, -3.0948], P(N2 > SH) = 0.003   -> N2 < SH
N2 - RD = -9.2230 [-16.6429, -1.7288], P(N2 > RD) = 0.007   -> N2 < RD
SH - RD = +2.5008 [-4.4809, +9.2076], P(SH > RD) = 0.760   -> no separation between SH and RD
```

## Reading this

N2 has one graph, so its interval carries run-to-run variation only. SH and RD have K
graphs each, so their intervals also carry graph-to-graph variation and are wider by
construction. The question is whether N2 sits outside the SH/RD distribution over graphs,
not whether two equally-estimated means differ.

This measures wiring **plus this specific sensor/motor interface** on **this game**. It is
not a test of whether biological wiring is better in general.