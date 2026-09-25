# WormWars 02b: what experiment 02's champions compute

**Exploratory and descriptive.** This analysis was not pre-registered, and nothing here is a
confirmatory claim. It is roadmap item 1: it uses experiment 02's saved genomes, and runs no
evolution. Script: `analyse.py`, with one JSON output per stage in this folder. Total GPU time
was about 40 minutes. Unless stated, the champions are the generation-39 champions of cells
T0-M0 and T1-M0: 8 N2 runs and 16 SH runs (8 graphs × 2).

## Summary

1. **Criticality follows N2's structure, not where the food enters.**
   - Deleting one interneuron can cost a champion up to 1.8 of its roughly 2.8 score.
   - In N2, the neurons critical in nearly every run are AIZ, RIA, AIY and RIB, the worm's known
     chemotaxis interneurons.
   - They remain critical when food enters through the wrong neurons (R1). The ranking of
     neurons by deletion cost correlates 0.84 across the two mappings. AWC and ASE, no longer
     food inputs under R1, become critical too.
   - So these neurons are hubs of N2's structure, whatever the task mapping.
2. **N2 champions depend on fewer neurons than shuffles do:** on average 54 of 245 eligible
   neurons are critical for N2, and 88 for SH.
3. **Evolution builds history sensitivity.** After identical current input, the motor output of
   evolved champions depends on the preceding food history 2-6 times more than that of
   generation-0 champions. Its direction is not consistent across champions, so this is
   sensitivity, not a demonstrated strategy.
4. **Evolved N2 champions steer toward food; shuffles do not.** Their turn response to a
   left-right food difference moves from slightly away from the food at generation 0 to toward it
   at generation 39. The shuffles stay near zero. Yet reversing the sides costs both groups about
   the same, so the extra steering does not show in the score.
5. **Anatomical magnitudes are largely eroded by generation 39.** The rank correlation of |w| with
   anatomical magnitude falls from 1.0 at generation 0 to 0.35 (N2) and 0.35 (SH).

## 1-2. Deletion criticality

**Method.** A true deletion operator was added (`wormwars/deletion.py`). It removes every
chemical edge and gap junction touching the neuron, and its bias. It is tested to match a
separately built 301-neuron network, and to differ from silencing (D044).
- Each of the 245 eligible neurons (not mapped by the interface, not pharyngeal) was deleted
  from each T1 champion in turn.
- Scores were measured on 32 probe worlds with the run's seed.
- "Critical" means a drop above 5% of the champion's intact score, the performance margin of
  03a v3.2.

| | champions | critical neurons, mean (range) | largest drop, mean | median drop | neurons whose deletion *helps* by more than 5% |
|---|---|---|---|---|---|
| N2 | 8 | 54.5 (34-77) | 1.85 | 0.014 | 0 |
| SH | 16 | 88.1 (54-135) | 1.83 | 0.066 | 0 |

**N2 neurons critical in at least 6 of 8 runs** (T1-M0): AIZL and AIZR 8, RIAL and RIAR 8, RIBL 7,
AIYR 7, and 6 each for ADFL, URYVL, OLQVR, RIR, RMDR, AIYL and RIS. 33 of the 140 neurons that are
critical in any run are critical in only one.

**The control: the same analysis for N2's T1-R1 champions**, with food into ASJ, ASI and ASG.

| neuron | M0: critical in / mean drop | R1: critical in / mean drop |
|---|---|---|
| AIYL | 6/8, 0.97 | 8/8, 1.41 |
| AIYR | 7/8, 0.74 | 7/8, 1.26 |
| AIZL | 8/8, 0.79 | 6/8, 0.90 |
| AIZR | 8/8, 0.74 | 7/8, 1.02 |
| RIAL | 8/8, 1.10 | 7/8, 0.89 |
| RIAR | 8/8, 1.20 | 8/8, 1.26 |
| RIBL | 7/8, 0.72 | 3/8, 0.32 |
| RIS | 6/8, 0.35 | 2/8, 0.10 |

Under R1, AWCL is critical in 8 of 8 runs and ASEL in 7, though neither receives food there.
The rank correlation of mean drop across the 239 neurons eligible under both mappings is 0.84.

**For 03a.** In N2, high criticality picks out the amphid-to-AIY/AIZ/RIA core whatever the
mapping. 03a's high-criticality N2 panel will therefore be dominated by structural hubs. Hubs
have many partners and a strong mirror, and that bears on SC3's structural baselines. This is
worth anticipating in the next review of 03a.

## 3. History: matched current input after different food histories

**Method.** The test runs outside the world, on each champion's brain.
- The final input is the champion's typical sensed input from a short replay.
- The food level reaches it by three routes over 10 ticks: rising (from a quarter of it),
  constant, or falling (from 1.75 times it), each after 30 ticks at the starting level.
- Every other signal is held at its typical value.
- Measured: the motor commands on the final tick. The baseline is the same test on each run's
  generation-0 champion, the best of 32 random genomes. Any recurrent network carries some
  history.

| | forward, rising minus falling: mean (runs above 0) | turn, mean of \|rising minus falling\| |
|---|---|---|
| T0 N2, generation 0 → 39 | 0.036 (4/8) → 0.160 (5/8) | 0.072 → **0.432** |
| T0 SH, generation 0 → 39 | 0.023 (8/16) → 0.065 (9/16) | 0.027 → 0.120 |
| T1 N2, generation 0 → 39 | 0.038 (4/8) → 0.064 (5/8) | 0.074 → 0.212 |
| T1 SH, generation 0 → 39 | 0.023 (8/16) → 0.024 (5/16) | 0.028 → 0.157 |

- The size of the history effect grows with evolution in every group, most for N2.
- Its direction on forward speed is split across runs, so it is not a consistent "speed up when
  food rises" rule.
- Even N2's random champions carry more history than the shuffles' (0.072 against 0.027 at
  generation 0).

Experiment 02's jitter probe could not see this (D039): the jitter was too small, or the
dependence too slow. Whether this history dependence helps foraging is not tested here.

## 4. Behaviour and steering

**Replays:** 8 probe worlds, per tick, alive weys only, about 32 000 wey-ticks per champion.
Standardised regression of the motor commands on five sensed quantities (means over champions):

| | forward: food level / food change / collision total | turn: food left minus right / collision left minus right | R² forward / turn |
|---|---|---|---|
| T0 N2 | −0.32 / +0.25 / −0.24 | +0.23 / +0.10 | 0.31 / 0.43 |
| T0 SH | −0.39 / +0.17 / −0.15 | +0.22 / +0.12 | 0.42 / 0.46 |
| T1 N2 | −0.35 / +0.16 / −0.26 | (no difference) / +0.19 | 0.37 / 0.38 |
| T1 SH | −0.25 / +0.12 / −0.19 | (no difference) / +0.20 | 0.28 / 0.46 |

- Champions slow down where food is strong (kinesis), and slow down near obstacles.
- On the stereo task they turn with the left-right food difference, with the same coefficient
  for N2 and SH.
- These are correlations, not causes. Moving fast changes the food reading, so the coefficient on
  food change is not evidence of temporal sensing.
- Turn-sign persistence is 0.91 (T0 N2), 0.98 (T0 SH) and about 0.998 (T1): the champions circle,
  N2's stereo champions a little less.

**Input response on evolved genomes** (T0-M0; the corrected probe from 02, now run on
champions):

| | signed directional turn (motor; + = toward food) | absolute | common-mode | swap cost in 02 |
|---|---|---|---|---|
| N2, generation 0 → 39 | −0.0026 → **+0.0093** | 0.0120 → 0.0128 | 0.022 → 0.029 | −0.076 → +0.079 |
| SH, generation 0 → 39 | −0.0009 → +0.0003 | 0.0045 → 0.0045 | 0.007 → 0.014 | −0.007 → +0.082 |

Across the 24 T0-M0 champions, the signed directional response correlates with the swap cost at
about 0.3 (Spearman), at both generations.

## 5. Magnitudes

The Spearman correlation between |w| and the anatomical magnitude over each champion's chemical
edges:

| | generation 0 | generation 39 |
|---|---|---|
| N2 | 1.00 | 0.35 |
| SH | 1.00 | 0.35 |

By generation 39 about two thirds of the rank information is gone. This confirms the concern
behind moving the strength control to generation 0 (roadmap).

## What this changes

- **For 03 (generation-0 structure):** N2's random champions already carry more history, and
  N2's hub structure dominates criticality. Both are generation-0 properties worth registering.
- **For 03a:** criticality in N2 is mapping-independent and hub-dominated (section 1).
- **For 04 (capability task):** these champions forage with kinesis, collision steering and some
  stereo steering, and carry history sensitivity whose use is unproven. A task where memory is
  necessary would have to defeat this repertoire.
