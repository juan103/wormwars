# 03m: results (exploratory)

Written 2026-09-29, for review by Astra 6 and Fable 5.1. **Corrected the same day (D114): the
summary sections below ("In brief", "Reading it together") overstate the results; read them with
the Corrections at the end, which replace them.** The numbers are right; the reading was not. **Exploratory throughout:** the analyses
were declared in [`PLAN.md`](PLAN.md) (v4.1, agreed by both reviewers) before the simulations ran,
but every comparison was chosen with 03's and 03r's data in view, and nothing here is confirmatory.
Every number comes from the committed outputs in this folder: `tradeoff.json`, `tails.json` (Q1),
`synapses.json` (Q3), `weights.json` (Q5), `decay.json` (Q4), `lesions.json` (Q2) and
`compute-record.json`. Per-genome arrays are local (`runs/p4m/*.npz`).

## What ran

On 2026-09-29, from the pushed `roadmap` branch, in the plan's order: the graph panel (already
present, nothing rebuilt), synapses (at `66edaee`), weights (`5312475`), decay (`f6971ec`) and lesions
(`a3f2ec1`). The branch moved during the chain as 04a's documents were committed; none of the
guarded files (the code, the configuration, `requirements.txt` and PLAN.md) changed between these
commits, and each command ran on a clean tree. **3.32 GPU-hours** of the 5-hour cap, one
attempt each, all completed. Every command first reproduced 03's N2 numerator and denominator, and
Q4 reproduced 03's numbers for every one of its 80 null graphs, each to a relative difference of 0
(the 10⁻⁶ tolerance was never approached). The lesions' empty deletion reproduced the intact brain
exactly.

## In brief

N2's two unusual properties, **a large food response** and **high history dependence (P4)**, come
apart:
- **the large response depends on where N2's chemical weights sit, and runs through RIA and AIY:**
  permuting the chemical weight magnitudes, or permuting all of N2's weights, brings it down to the
  shuffles' typical level, and so does deleting the RIA pair or the AIY pair;
- **the high P4 survives all of those** and every other single or paired deletion tested. It is
  spread through the network rather than tied to a neuron, a pair or a synapse type;
- **the history mostly fades, but more slowly in N2:** 300 ticks after the ramp, N2 keeps 9.4% of the
  difference, more than 78 of 80 null graphs, and a small minority of its random brains (about 1%)
  settle into a lasting different state.

## Q1: the association (from committed and local data; reported in PLAN.md)

See [`PLAN.md`](PLAN.md) §Q1 and `tradeoff.json`, `tails.json`. In short: within every ensemble,
graphs whose brains respond more strongly to food have lower P4 (Spearman −0.27 to −0.60); N2 is
the strongest responder by far (4.7-7.1 times the median) and yet above every graph but one in P4;
N2's numerator and response are concentrated in a minority of genomes, but its P4 stays high without
them.

## Q3: gap junctions or chemical synapses (`synapses.json`)

| Condition | P4 | Response (denominator) |
|---|---|---|
| intact N2 | 0.931 | 0.129 |
| gap junctions off | 0.945 | 0.143 |
| chemical synapses off, or both off | invalid (no response) | 0.000 |
| chemical magnitudes permuted, 8 seeds | 0.84-0.96 | 0.023-0.048 |
| gap-junction magnitudes permuted, 8 seeds | 0.915-0.929 | 0.118-0.129 |

For reference: the shuffles' pooled 95th percentile of P4 is 0.889, and their pooled median and
maximum response are 0.023 and 0.073.

- **Gap junctions are not needed for either property.** Switched off, N2's P4 changes by +0.014 and
  its response by +0.014. On Q4's 80 null graphs, switching gap junctions off raised P4 by
  0.051-0.143 and the response by 0.006-0.029, each against the graph's own intact values. N2's
  change in P4 lies below the whole null range: gap junctions pull the nulls' P4 down much more than
  N2's.
- **The placement of chemical weights sets the response:** permuting only the chemical magnitudes
  brings N2's response to the null range in all 8 seeds (0.023-0.048), while P4 stays at 0.84-0.96,
  mostly above the nulls' 95th percentile.
- Chemical synapses off leaves no route from the food input to the read-out, as the plan expected;
  it tests nothing about persistence.
- The by-type permutations share their generator seeds with Q5's paired design, so the conditions
  form a 2 × 2 with intact N2, not independent draws (PLAN.md §Q3).

## Q5: wiring or weight placement (`weights.json`)

N2's own wiring, with its anatomical weight magnitudes permuted among its edges, 64 permutations:

| Design | P4, median | P4 above the nulls' pooled 95th percentile | P4 below N2's | Response, median | Response above the nulls' maximum |
|---|---|---|---|---|---|
| independent genome draws | 0.885 | 42% | 92% | 0.023 | 0% |
| paired with N2's genome draws | 0.884 | 45% | 92% | 0.024 | 0% |

- **With its weights permuted, N2's wiring loses the large response entirely** (0 of 128 above any
  null graph's), which is the outside review's hint, confirmed on 64 permutations in both designs.
- **It keeps a high P4:** the median permutation sits near the nulls' 95th percentile, and 42-45% are
  above it, but 92% are below N2 itself. So the wiring alone carries much of N2's persistence, and
  the placement of the weights adds to it.

## Q4: how long the history lasts (`decay.json`)

After the ramp, the final input was held for 300 ticks, for N2 and the first 16 graphs of each
ensemble.

| | N2 | 80 null graphs |
|---|---|---|
| mean difference left at 300 ticks, as a share of the ramp's end | 9.4% | median 0.4%; 78 of 80 below N2 (maximum 15.5%, SH-10007) |
| genomes with more than 10% of their difference left (among those starting above 10⁻³) | 2.5% (49 of 1 987) | median 0.3%; 79 of 80 below N2 |
| trajectories settled at 300 ticks | 95% | 94-100% |
| of N2's 49 with separation left, settled | 26 (53%) | |

- **The history mostly relaxes, in N2 as in the shuffles, but N2's relaxes more slowly**, and N2 has
  more genomes whose difference is still there at 300 ticks.
- **About 1% of N2's random brains (26 of 2 048) have settled with the difference intact.** That is
  consistent with a second stable state for the same input in those brains. The rest of the
  remaining separation is in trajectories still moving: a slow mode, an oscillation or a long
  transient (PLAN.md §Q4). It is not evidence for multistability in general.
- **The holds do not settle within 100 ticks** by the plan's criterion (0% of genomes, in N2 and in
  every null graph): the denominator is a finite-time contrast, as the plan cautioned.
- **N2's turn read-out neurons work in a more saturated range:** their mean tanh slope is 0.44 at the
  holds' end against a null median of 0.73. So part of N2's large response and of its read-out's
  nonlinearity is in this final step, which the ratio's interpretation should keep in mind.

## Q2: which neurons it depends on (`lesions.json`)

390 deletions: the empty deletion, 95 bilateral pairs and 294 single neurons (the eight turn
read-out neurons excluded). All valid.

- **No deletion removes N2's elevated P4.** The lowest P4 after any deletion is 0.907 (the AIZ pair),
  still above the nulls' pooled 95th percentile (0.889). No deletion falls in the "P4 only" or "both"
  classes. In the plan's words: no tested valid single or bilateral-pair deletion removed the unusual
  elevation under these thresholds.
- **Two deletions remove the large response and keep P4:** the RIA pair (response 0.049, P4 0.936)
  and the AIY pair (0.061, 0.927), the "response only" class. Singly, RIAR, RIAL, AIYR and AIYL
  lower the response less (0.088-0.104), and ASE, the food sensor pair, to 0.089.
- **The pre-named targets:** RIA 0.936, AIZ 0.907, AIY 0.927, AIB 0.936, RIB 0.928, RIM 0.933 (P4);
  none moves P4 far from N2's 0.931.
- **The follow-up by synapse type,** for the five single deletions with the lowest P4 that kept a
  response: deleting only their chemical edges reproduces most of the drop (AIZL: 0.920 against
  0.918 for the full deletion), and deleting only their gap junctions does not (AIZL: 0.941). The
  effects are small.

## Reading it together

- **The large food response** (4.7-7.1 times the shuffles') is a property of N2's weight placement on
  its chemical synapses, carried through RIA and AIY. That fits 02b's finding that RIA is part of
  N2's critical core, and RIA's known place on the sensory route to head steering. It is a statement
  about these random, unevolved brains and this read-out, not about the worm.
- **The high persistence** is not carried by any one neuron, pair or synapse type. N2's wiring with
  its weights permuted keeps much of it, and gap junctions reduce it less in N2 than in the shuffles.
- **The Q1 puzzle, reframed:** across shuffles, a stronger response goes with less persistence. N2
  combines both, and they have different sources: removing the response (RIA, AIY, or weight
  permutation) leaves N2's P4 high.

## What this does not establish

- A mechanism in the causal sense beyond "this change moves these numbers": the brains are random and
  unevolved, the read-out is a hand-chosen interface, and deletions locate dependencies, not stores;
- anything about behaviour, or about evolved brains;
- confirmatory claims: every comparison was chosen with 03's and 03r's data in view. A confirmatory
  study would register, for example, the RIA/AIY dissociation and the slower relaxation, on fresh
  genomes and fresh null graphs.

## Deviations and disclosures

- **No deviation from the plan** that I have found. The graph rebuild was not needed: 03's graph
  files were present locally and passed their hash checks.
- **Development exposure** (PLAN.md): the plan was written with 03's and 03r's results known; smoke
  runs used 8 genomes on the CPU.
- **Order of work:** the plan was merged into `roadmap` after 04a's evaluation (`69286d9`), and the
  formal runs used the pushed `roadmap` HEADs listed above.

## Corrections (2026-09-29, D114)

Both reviewers checked these results (`docs/reviews/20260929-061029-03m-results/`). They found that
the runs followed the plan and that every number recomputes from the outputs (Astra recomputed all
627 valid P4 ratios). Both said "fix": four claims in the summary are contradicted by the outputs.
RESULTS.md was committed about two minutes after the last run ended (Fable), and the overclaims
are all in the sections written last. What was written above is left as it was; these corrections
replace it.

1. **"The two properties come apart" and "they have different sources" are not shown** (both).
   Written: *"N2's two unusual properties ... come apart"* and *"removing the response ... leaves N2's
   P4 high"*, *"they have different sources"*. P4 is a ratio. Deleting the RIA pair cuts the raw
   history signal (the numerator) by 61.5% and the response by 61.7%; deleting the AIY pair, by 53.1%
   and 52.8%. The ratio survives because both parts fall together; the history signal itself depends
   on RIA and AIY as much as the response does. What is supported: these deletions reduce the
   response's size while leaving the normalised P4 nearly unchanged.
2. **RIA and AIY do not bring the response to "the shuffles' typical level"** (both). Written: *"brings
   it down to the shuffles' typical level, and so does deleting the RIA pair or the AIY pair"*. The
   RIA pair leaves a response of 0.049, 2.2 times the null median and above 96% of the null graphs;
   the AIY pair 0.061, 2.7 times and above 98%. They fall below the nulls' maximum, which is what the
   "response only" class means, but stay in the nulls' upper tail. Only the weight permutations reach
   the typical level. The single deletions give 0.089-0.104.
3. **High P4 does not survive "every weight permutation"** (both). Written, in the summary and the
   README: *"the high P4 survives all of those"*, *"every ... weight permutation tested"*. Under the
   plan's classes, 37 of 64 independent and 35 of 64 paired permutations fall in "both": P4 below the
   nulls' pooled 95th percentile, and the response below their maximum. Only 27 and 29 of 64 stay above
   that percentile; the lowest are 0.733 and 0.730; 59 of 64 are below N2 in each design; the median
   drop from N2 (0.046) is about twice the largest deletion's. Two of Q3's eight chemical-only
   permutations also fall below the percentile. Relative to the pooled null median, the permutations'
   medians keep about 60% (independent) and 58% (paired) of N2's excess P4: N2's topology under these
   permutations keeps an elevated P4 distribution, and the placement of the weights contributes a
   substantial part. The two designs reuse the same 64 permutations; they are not 128 independent
   ones. "0 of 128 above any null graph's" response means above the pooled null maximum.
4. **Gap junctions: the reading ran against the plan's own rule** (Fable; Astra on the response).
   Written: *"Gap junctions are not needed for either property"* and *"not carried by any ... synapse
   type"*. Gap junctions are not needed for N2's absolute values. But the plan's rule compares N2's
   change with the null panel's, and N2's change in P4 (+0.014) lies below the whole null range
   (+0.051 to +0.143): switching gap junctions off raises the shuffles' P4 much more than N2's. With
   gap junctions off in every brain, the panel's median P4 rises from 0.822 to 0.908, and 5 of the 80
   null graphs match or exceed N2's 0.945 (intact, N2 was above all 80; the highest was 0.898). So
   **how far N2's P4 stands above the shuffles depends on gap junctions**, which is the opposite of
   what the summary said. N2's response change (+0.014) lies inside the null range (+0.006 to
   +0.029), and its gaps-off response (0.143) stays above every gaps-off null graph (at most 0.082).
   Chemical synapses off leaves a response of 3.6 × 10⁻⁵, below the validity floor; it does not show
   that no path exists, and it establishes nothing about whether chemical synapses are dispensable.
5. **"Distributed" is an inference from a negative screen** (both). What was tested: no single or
   bilateral-pair deletion, of those tried, lowered N2's P4 below the threshold. That does not
   establish a network-wide distribution: redundancy within a small circuit, dependencies that differ
   between genomes, and the excluded turn read-out neurons remain possible.
6. **"Settle into a lasting different state" was not measured** (both). Written: *"a small minority of
   its random brains (about 1%) settle into a lasting different state"* and *"About 1% of N2's random
   brains (26 of 2 048) have settled with the difference intact"*. What was measured: 26 of 2 048 genomes kept more than 10% of
   their starting separation at tick 300 and met the full-state settling criterion over the last ten
   ticks. That is consistent with distinct stable states, as the plan says, but a ten-tick test does
   not show lasting stability. And it is not specific to N2: SH-10007 has 171 such genomes and
   SH-mirror-40003 has 37; SH-10007's P4 is an unremarkable 0.867.
7. **The saturation sentence overstated** (both). Written: *"part of N2's large response and of its
   read-out's nonlinearity is in this final step"*. What is measured: N2's turn read-out neurons have
   a mean tanh slope of 0.44 at the holds' end, below all 80 null graphs (0.66-0.80). A lower slope
   compresses differences; whether it contributes to N2's response needs another comparison. It
   complicates reading the output ratio.

**The corrected summary.**
- **The slower relaxation holds throughout the window:** N2 keeps a larger share of the difference
  than all 80 null graphs at ticks 5, 10 and 50, and than 78 of 80 at tick 300. By ensemble, SH-mirror
  and SH-recip relax much more slowly than SH (median 2.5% and 1.5% left at 300 ticks, against 0.08%),
  and N2 (9.4%) is near their top rather than apart from them.
- **N2's large response depends on the placement of its weights** (all-weight and chemical-only
  permutations bring it to the null range) **and on RIA and AIY** (deleting either pair roughly halves
  it or more). Those deletions reduce the history signal in proportion, so P4 as a ratio changes little.
- **N2's P4 elevation over the shuffles depends partly on gap junctions** (switching them off narrows
  it) **and partly on weight placement** (permutations keep about 60% of it).
- **No tested single or paired deletion removed the elevated P4.**

**Also, as the reviewers asked:** none of the guarded files changed between the four commits the
commands ran at (Astra checked the Git objects: identical); the smoke runs were not repeated after the
merge into `roadmap`, and the only change after the last smoke run was `allow_pickle=False` in four
test lines.

**For a confirmatory follow-up** (both reviewers' suggestions, not yet a plan): on fresh genomes and
fresh null graphs, (1) N2's P4 with gap junctions off, ranked against each ensemble with gap
junctions off; (2) the RIA and AIY deletions, with matched control deletions and a registered
equivalence margin for P4, analysing numerator and denominator jointly; (3) N2's rank among many
fresh weight permutations; (4) the retained separation at 300 ticks, by ensemble; (5) P4 on the
read-out neurons' state before the tanh, against saturation. "No deletion removes P4" should be
described, not registered.

**Further corrections, from the confirmation round** (2026-09-29, D114;
`docs/reviews/20260929-064250-03m-results-confirm/`). Both reviewers confirmed the corrections above
in substance and asked for these:
- *"the AIY pair 0.061, 2.7 times"*: 2.65 times (0.0606 / 0.0229, the pooled null median response).
- *"the lowest are 0.733 and 0.730"*: 0.733 and 0.729.
- *"the median drop from N2 (0.046)"*: 0.046 in the independent design and 0.047 in the paired one.
- The 60% and 58% of N2's excess P4 are measured from the pooled null median P4, 0.8174, over 03's
  640 null graphs (`experiments/03-generation0/supplement.json`).
- *"Only the weight permutations reach the typical level"*: only the all-weight permutations'
  **medians** do (0.023-0.024). Individual all-weight permutations range from 0.013 to 0.052, and
  three of Q3's eight chemical-only seeds give 0.045-0.048, about the RIA pair's level (Fable).
- *"The slower relaxation holds throughout the window"*: N2 keeps a larger share than all 80 null
  graphs at every recorded tick from 5 to 50, with a thin margin at tick 50 (0.300 against SH-10007's
  0.298); from tick 60 SH-10007 is above it (79 of 80), and from tick 150 SH-mirror-40014 too (78 of
  80, through tick 300). These counts are exact at every recorded tick (Fable).
- *"The single deletions give 0.089-0.104"* replaced the first write-up's *"RIAR, RIAL, AIYR and AIYL
  lower the response less (0.088-0.104)"*: the lowest is RIAR's 0.0885, which rounds to 0.089 (Astra).
  So the note at the top ("the numbers are right") holds with that one rounding.
- *"The rest of the remaining separation is in trajectories still moving: a slow mode, an oscillation
  or a long transient"*: the other 23 of N2's 49 qualifying genomes did not meet the settling
  criterion. That splits the genomes, not the size of the remaining separation (Astra).
- *"Chemical synapses off leaves no route from the food input to the read-out"*: it leaves a response
  of 3.6 × 10⁻⁵, below the validity floor; it does not show that no path exists (Astra; as in
  correction 4).
