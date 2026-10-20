This is round 3 of the brainstorm, the selection round. Rounds 1 and 2 generated and built; this round chooses,
critically but honestly. An idea that sounded crazy gets judged on the evidence like any other, and an idea that
sounded sensible gets no free pass.

## The question (unchanged)

Why does the history difference in N2's random brains decay more slowly than in shuffled graphs' brains?
(03mc, `experiments/03mc-p4-confirm/RESULTS.md`: N2 keeps 0.436 of its difference 30 ticks after the ramp; the
null ensembles' medians are 0.255 to 0.291.)

Rounds 1 and 2 are in `docs/reviews/20261020-memory-diverge/` and `docs/reviews/20261020-memory-build/`, with the
owner's ideas (ring attractors, waves trapped in loops, transplanting) and the ChatGPT roadmap the owner supplied.

## What the cheap checks found

Between rounds 2 and 3 Claude ran the cheap discriminating checks that you and Fable proposed in round 2, plus
follow-ups. They are exploratory, on fresh CPU panels (03mc's genomes exist only on CUDA). Scripts are in
`scripts/memory_spikes/` (its README maps scripts to outputs), outputs in `runs/memory-spikes/`. Read the code before
you trust a number. **The main caveat:** most arms use one graph per null ensemble, and graphs within an ensemble differ
a lot. Even N2's own share moves between panels (0.469 on seed 7100, 0.396 on seed 7400, 1024 genomes each), because
the registered share is a ratio of means and so weighted by a heavy tail.

**From the 03mc arrays (seconds; `check_mixture.txt`, `check_structure.txt`):**
- N2's median per-genome retention at tick 30 is ordinary: 0.245, with 17 to 46 of 128 graphs per ensemble at or above it.
- What is extreme is the tail and its weighting:
  - the amplitude-retention correlation is −0.13 in N2 vs −0.39 to −0.42 in every ensemble (0 of 128 graphs as high);
  - 11.5% of N2 genomes grow by tick 30, vs 6.8 to 7.9%;
  - the top 5% of genomes carry 55% of the tick-30 mean, vs 26 to 31%.
- N2's structure is far outside the nulls on directed 3-cycles (2470 vs 1187 to 1676), feed-forward triangles
  (12 553 vs 4524 to 6436), autapses and gap-chemical overlap.
  - A linear fit of retention on 3-cycles across the null graphs extrapolates to 0.438 [0.398, 0.481] at N2's count, with R² of only 0.07.

**Batch 1 (`batch1.json`; seed 7100, 1024 genomes, one graph per ensemble):**

| Arm | share30 | share100 |
|---|---|---|
| N2 | 0.469 | 0.204 |
| six nulls | 0.206 to 0.442 | 0.012 to 0.153 |
| N2, substeps 16 / 32 | 0.469 / 0.469 | |
| N2, warm-up 25 / 400 | 0.415 / 0.471 | |
| N2, food × 0.5 / × 2 | 0.504 / 0.463 | |
| N2 reversed | 0.572 | 0.083 |
| N2 chem + SH gaps | 0.413 | |
| SH chem + N2 gaps | 0.227 | |
| N2 gaps off | 0.539 | |
| SH gaps off | 0.396 | |
| N2, turn neurons' mutual edges zeroed | 0.428 | |
| N2, 8 turn neurons erased at the ramp's end | 0.389 | |
| N2, 8 random neurons erased | 0.469 | |

Comparisons: SH-2010000 is the SH arm (0.206). For the erasure arms the share is relative to the intact start.

**Batch 2 (`batch2.json`):**
- Rewiring three shuffles up to N2's 3-cycle or feed-forward count did not raise retention: 0.23 to 0.28, against parents of 0.206, 0.353 and 0.234.
- Rewiring N2 down to the shuffles' counts lowered it: 0.30 to 0.44.

**Batch 5 (`batch5.json`, `sham_core.json`):** batch 2's surgery moved 70 to 76% of N2's chemical edges.
- **Shams** move the same 73% while holding both triangle counts: they keep N2's retention (0.466 to 0.526).
- **Free rewirings** of the same size drop the counts to null level and give 0.32 to 0.42.
- **But the shams also keep 58% of the internal edges of N2's 30-neuron head core,** against 27 to 36% for free rewiring.

**Batch 3, the one-tick Jacobian at the ramp's end (`batch3.json`, 256 genomes):**
- Spectral radius, its upper tail, and non-normality (Henrici) are the same in N2 and three nulls (median 0.955 per tick).
- 5.1% of N2 genomes have a radius above 1, vs 0 to 0.8%.
- The linear forecast of the read-out tracks the observed per-genome retention (Spearman 0.50 to 0.74). Its median is 0.26 for N2 and 0.18 to 0.25 for the nulls.

**Batch 4, where the residual lives (`batch4.json`, seed 7100):**
- **The whole state difference decays alike:** the median per-genome norm ratio at tick 30 is 0.197 for N2, against 0.192 and 0.200 for two nulls.
- **N2's residual is concentrated:**
  - participation ratio 9.3 vs 23.3 and 17.6;
  - the top 10 neurons hold 78% vs 52 to 58%;
  - it sits on RMD and SMD (the turn read-out itself), RIA, RIM and AIB, at about ten times a null's largest per-neuron residual.
- **The pharyngeal neurons keep their own difference longest** (persistence 0.6 to 0.75), but erasing them changes nothing.
- **Time constants and biases:** no neuron's tau or bias predicts a genome's retention beyond |rho| 0.10, in N2 or the nulls.
- **Erasures at the ramp's end:**

  | Erased | share30 |
  |---|---|
  | nothing | 0.469 |
  | sensory | 0.401 |
  | inter | 0.302 |
  | motor | 0.376 |
  | 30 neurons with the most 3-cycles | 0.349 |
  | 30 with the largest residual | 0.202 |
  | random 30 | 0.44 to 0.47 |

**Batch 6, held-out panel (seed 7400; `batch6.json`):**
- N2 intact is 0.396 on this panel.
- **Erasures,** with the neuron lists chosen on seed 7100:

  | Erased | share30 |
  |---|---|
  | top 30 by residual | 0.165 |
  | top 30 by start difference (23 of the 30 overlap) | 0.096 |
  | 8 turn neurons | 0.324 |
  | random 30 | 0.31 to 0.40 |

- **Other read-outs** (N2, then four nulls):

  | Read-out | N2 | Four nulls |
  |---|---|---|
  | turn | 0.396 | 0.203, 0.320, 0.400 (SH-class), 0.280 |
  | forward | 0.302 | 0.255 to 0.375 |
  | mean absolute difference over all neurons | 0.316 | 0.209 to 0.299 |
  | random signed 8-neuron read-outs, median | 0.324 | 0.228 to 0.320 |
  | per-genome state norm ratio, median | 0.193 | 0.179 to 0.200 |

**Batch 7, the head core (`batch7.json`; three graphs per arm, each on both panels, seeds 7100 and 7400):**
- **The core** is batch 6's `top30_start` list, 30 neurons with 199 internal chemical edges.
- **The control** is the 30 highest-degree neurons outside it, with 202 internal edges.

| Arm | What changes | share30 range (mean) | corr_amp |
|---|---|---|---|
| **core-frozen shuffle** | every edge may swap except the core's internal edges; 73% of edges moved; both triangle counts fall to null level (1344 to 1355 3-cycles) | 0.437 to 0.550 (0.482) | −0.09 to −0.20 |
| **hub-frozen shuffle** | the same, freezing the hubs' internal edges | 0.283 to 0.372 (0.343) | −0.31 to −0.39 |
| **core dissolved** | 140 swaps, each pairing a core-internal edge with an edge outside the core, until the core keeps 30% of its internal edges; 92% of all edges stay; triangle counts stay high (about 2070 3-cycles) | 0.325 to 0.405 (0.363) | |
| **periphery scrambled** | 140 swaps among edges with no endpoint in the core | 0.408 to 0.488 (0.454) | |

N2 intact is 0.469 and 0.396 on the two panels.

## What I want from you

You have a role this round. Both of you get this prompt; follow the line with your name.
- **Astra 6** is the advocate for the dynamical families: 1 (feedback pays the leak, slow modes, the owner's ring and
  line attractors), 2 (chains and transient growth), 4 (switched routes), 5 (saturation), 10 (phase memory), and the
  growing tail (batch 3's radius above 1).
- **Fable 5.1** is the advocate for the structural families: 3 (reservoirs), 6 (gap geometry and the two layers
  fitting together), 8 (mixtures), 9 (read-out geometry), 13 (bilateral sectors), the owner's trapped waves in
  loops, and the triangle and core readings.
- Families 7 (time-constant lottery), 11 (preparation) and 12 (the probe's regime) have no advocate: the checks hit
  them directly. Either of you may take one up if you think it was killed unfairly.

Advocate means: make the strongest honest case for those families
from the evidence, and say what would rescue them. It does not mean defending them past the evidence.

1. **A verdict for every family** from round 2: alive, wounded or dead, with the evidence and the arm or file it comes
   from. For alive and wounded families, give the cheapest remaining kill-check: what result would kill it.
2. **Prosecute the leading reading.** Claude's current reading is roughly this:
   - the typical genome forgets alike in N2 and the nulls;
   - N2's lead lives in the amplitude-weighted measure, in genomes with large differences that forget less;
   - those differences sit in a dense head core around the turn read-out (RIA, RMD, SMD, AIB, AIZ, RIM...);
   - the core's internal wiring is enough to keep most of N2's retention in an otherwise shuffled graph, and
     dissolving it costs a good part of the lead;
   - the triangle counts matter, if at all, through that core.

   Attack it: confounds, circularity, what an alternative reading predicts that this one does not, and whether
   "decays more slowly" is even the right description.
3. **The measure itself.** The registered share is a ratio of means. Is the question still well posed, or should the
   roadmap split it into the typical genome and the amplitude-weighted tail? Say what each version would be evidence of.
4. **A memory roadmap.** Three to six steps that would answer the question, in order. For each, say:
   - what it decides and how much it costs (CPU or GPU);
   - whether it is exploratory or should be pre-registered;
   - what result would change the plan.

   Include the owner's transplant idea in whatever form the evidence supports, or say why not.
5. **One crazy idea** that the evidence has made more plausible, not less, if there is one.

Read the repository and the spike code as needed. Do not edit files or run anything.
