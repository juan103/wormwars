# N2 / SH / RD comparison

**Motor gains are NOT calibrated**: every graph uses the single hand-chosen gain, which was tuned on N2. Graphs whose wiring happens to drive the read-out harder start out moving more. See `wormwars/calibration.py`.

Total wall time 0.892 h over 45 runs.

Scores are held-out foraging score (surviving swarm energy / starting energy),
on world ids never used for selection. The unit of analysis is the run.

## Final held-out score

```
N2   1.4115 [1.3661, 1.4526] (1g x 15r)
SH   1.5214 [1.4470, 1.5804] (5g x 15r)
RD   1.4825 [1.4343, 1.5379] (5g x 15r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2          15    1.4115   0.0884   1.2274   1.5351
graph     runs      mean       sd      min      max
SH1          3    1.5805   0.0703   1.5052   1.6446
SH2          3    1.5594   0.0691   1.5163   1.6391
SH3          3    1.3976   0.0877   1.3193   1.4923
SH4          3    1.5414   0.0850   1.4470   1.6120
SH5          3    1.5280   0.1181   1.3915   1.5966
graph     runs      mean       sd      min      max
RD1          3    1.5363   0.1434   1.4027   1.6879
RD2          3    1.5259   0.0584   1.4685   1.5852
RD3          3    1.4199   0.0551   1.3571   1.4601
RD4          3    1.4657   0.0836   1.3898   1.5554
RD5          3    1.4649   0.0540   1.4309   1.5271
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = -0.1099 [-0.1846, -0.0257], P(N2 > SH) = 0.005   -> N2 < SH
N2 - RD = -0.0711 [-0.1407, -0.0065], P(N2 > RD) = 0.014   -> N2 < RD
SH - RD = +0.0388 [-0.0516, +0.1187], P(SH > RD) = 0.817   -> no separation between SH and RD
```

## Area under the fitness curve (speed of improvement)

```
N2   1.3586 [1.3441, 1.3732] (1g x 15r)
SH   1.4770 [1.4421, 1.5157] (5g x 15r)
RD   1.5022 [1.4679, 1.5322] (5g x 15r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2          15    1.3586   0.0302   1.3018   1.3968
graph     runs      mean       sd      min      max
SH1          3    1.4885   0.0810   1.4009   1.5608
SH2          3    1.5344   0.0228   1.5100   1.5550
SH3          3    1.4358   0.0243   1.4181   1.4635
SH4          3    1.4798   0.0692   1.4222   1.5565
SH5          3    1.4466   0.0213   1.4262   1.4688
graph     runs      mean       sd      min      max
RD1          3    1.5134   0.0401   1.4801   1.5579
RD2          3    1.5159   0.0275   1.4941   1.5468
RD3          3    1.4975   0.0717   1.4185   1.5583
RD4          3    1.4893   0.1101   1.3713   1.5894
RD5          3    1.4948   0.0939   1.3973   1.5845
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = -0.1184 [-0.1597, -0.0803], P(N2 > SH) = 0.000   -> N2 < SH
N2 - RD = -0.1435 [-0.1780, -0.1062], P(N2 > RD) = 0.000   -> N2 < RD
SH - RD = -0.0252 [-0.0726, +0.0253], P(SH > RD) = 0.155   -> no separation between SH and RD
```

## Held-out score per GPU-hour

```
N2   71.2487 [69.0007, 73.2792] (1g x 15r)
SH   76.7430 [73.0364, 79.7103] (5g x 15r)
RD   74.7846 [72.3554, 77.5280] (5g x 15r)
```

Per graph:

```
graph     runs      mean       sd      min      max
N2          15   71.2487   4.3798  61.9731  77.4077
graph     runs      mean       sd      min      max
SH1          3   79.6761   3.5265  75.9075  82.8963
SH2          3   78.6861   3.4273  76.5562  82.6396
SH3          3   70.5767   4.2634  66.7112  75.1495
SH4          3   77.7588   4.3145  72.9627  81.3244
SH5          3   77.0174   6.1272  69.9429  80.6398
graph     runs      mean       sd      min      max
RD1          3   77.5177   7.2022  70.8239  85.1386
RD2          3   76.7998   2.8030  73.9926  79.5987
RD3          3   71.5382   2.7608  68.4376  73.7300
RD4          3   74.0211   4.2625  70.1464  78.5869
RD5          3   74.0461   2.7725  72.3773  77.2465
```

Contrasts (bootstrap of the difference, 95% interval):

```
N2 - SH = -5.4943 [-9.2259, -1.3008], P(N2 > SH) = 0.005   -> N2 < SH
N2 - RD = -3.5358 [-6.9892, -0.3278], P(N2 > RD) = 0.015   -> N2 < RD
SH - RD = +1.9584 [-2.5634, +5.9669], P(SH > RD) = 0.818   -> no separation between SH and RD
```

## Reading this

N2 has one graph, so its interval carries run-to-run variation only. SH and RD have K
graphs each, so their intervals also carry graph-to-graph variation and are wider by
construction. The question is whether N2 sits outside the SH/RD distribution over graphs,
not whether two equally-estimated means differ.

This measures wiring **plus this specific sensor/motor interface** on **this game**. It is
not a test of whether biological wiring is better in general.