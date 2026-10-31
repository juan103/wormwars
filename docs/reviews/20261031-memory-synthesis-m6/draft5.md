# The memory thread, M1 to M6: what was found

*Draft 5, 2026-10-31, before review. It adds M6 (D374-D383): the evolved champions classified (option 0), a bounded
literature check (option 3), whether the switches' states outlast the input (step 1) and whether the champions'
foraging depends on their neural time scale (step 2). By the owner's order (D379) the thread stops here, and this page
takes in its last steps. Draft 4's text is kept except where M6 changes what holds, what is open or what comes next;
the dated annotations under "What comes next" stay as written.*

*Draft 4, 2026-10-29. Drafts 1 to 3 (M1 to M4d, D349-D364) were reviewed in two rounds by Astra 6 and Fable 5.1, both
"fix then publish" in both rounds, every finding taken; they and the reviews are archived in
[`docs/reviews/20261025-memory-synthesis/`](../reviews/20261025-memory-synthesis/). Draft 4 adds M4e and M5's pilot,
power calculation and postponement (D367-D373), at the owner's word after M5 was postponed; its review is in
[`docs/reviews/20261029-memory-synthesis-m4e/`](../reviews/20261029-memory-synthesis-m4e/). The M1 to M4d text is
draft 3's, except where M4e or M5 changes what it says next or what holds.
A synthesis of the memory thread, first written at the owner's request after M4d. It
reports no new run and changes no reading: every reading below is the one its own results file reached, and every
number comes from those files or from [`summary.json`](summary.json), which
[`scripts/memory_summary.py`](../../scripts/memory_summary.py) writes from the committed records (rule 5).
Exploratory throughout; nothing here is a pre-registration. Where this page interprets across steps, it says so.*

## In short

- **The question** was why N2's unevolved random brains keep more of a recent food history than shuffled graphs do
  (03mc's Q-D, registered over all genomes: 0.436 at tick 30 against null medians of 0.255 to 0.291). Steps M1 to M4e
  and M5's pilot ran on the CPU (112.43 recorded hours, no GPU), each with a plan reviewed and agreed by both models
  before its runs (one disclosed exception, M4c's census, below) and its results reviewed after.
- **The lead is real and sits in the upper tail.** It replicates on fresh genomes (N2 0.444 and 0.443 against a
  median of 0.275 over 30 random graphs, none at or above N2). N2's unweighted mean retention is beyond all 640 of
  03mc's graphs, which corrects the earlier claim that only the amplitude-weighted share was extreme; the median
  genome is ordinary. Read-out alignment does not carry the lead, and amplitude does not account for most of it.
- **A few genomes hold the history as a switch.** A validated classifier finds that fewer than 2% of N2's genomes
  (15 and 13 of about 1000) end in one of two stable states depending on the history ("separate states"). 19 of 30
  random null graphs have none, though graphs selected for many such genomes have 12 to 78. At tick 30 the
  switches carry 0.47 and 0.35 of N2's lead (the reading is "inconclusive": the intervals are wide), and mostly
  fading genomes carry the rest; by tick 300 the switches carry most of what is left.
- **In N2 the switch is vulnerable in the head core, most of all at RIA.** Cutting the anatomical head core's
  internal chemical edges for 30 ticks sends 26 of N2's 28 switches into one basin (14% for sampled cuts of the same
  size), though the fixed readings of M4a and M4b are both "unresolved". The one positive reading: on 141 fresh switch genomes,
  cutting either RIA neuron's 26 or 29 core edges erases the history distinction in 72% and 58%, against 22% to 30%
  for three control families matched on summed weight. That is vulnerability, not storage, and RIA is the strongest
  of the single-neuron cuts tested, not the only one that matters.
- **Moved into other graphs, the head core's block raises the switch rate, and its exact wiring is not shown to
  matter.** In ten fresh null hosts (a screen), N2's block lifts the share of switch genomes from 0.04% to 0.62%
  (pooled), in every host. Blocks rewired at the same degrees reach 0.51%. Whether N2's exact wiring adds 0.004 or
  more over them is "Unresolved (the unresolved genomes decide it)".
- **What a dense block carries (M4e): how its weight is concentrated matters.** With every edge of equal magnitude
  and N2's total weight, spreading the weight over N2's 260 edges gives fewer switch genomes than putting it on the
  host's 92 to 126 (4 against 31 of 10,240: "lowers", over every assignment of the unresolved genomes by about four
  genomes). Raising the total weight at N2's count shows no effect of 0.004 or more, as a mean across these ten hosts.
  The equal-magnitude block at N2's count and total weight does not reproduce N2's block's rate; the rise arrives in
  three steps of similar size, described and not read: N2's uneven weights (+0.0026, holding over every assignment),
  its labelled degrees (+0.0023) and its exact block (+0.0020), the last two unresolved. N2's block again gives more
  switch genomes than the intact host in all ten fresh hosts.
- **M5, the test of N2's exact wiring, was prepared and then postponed.** A pilot kept the 22,000-tick protocol and
  put the exact wiring's advantage over a rewired control near the planned effect, its interval including zero
  (+0.0016, −0.0008 to +0.0040). Powered for a true difference of 0.002 (about two genomes in 1000), the recommended
  allocation uses 110 hosts first and up to 160, at a simulated mean of about 72 to 91 CPU hours; the owner postponed
  M5 for its cost against its benefit (D373).
- **M6 turned to behaviour and biology, then the thread stopped** (section 7; 4.80 more CPU hours, 117.23 in all).
  - **Evolution did not detectably favour switches.** Among 02's evolved T1 foraging champions, 1 of 102 is a
    switch, against 5 of 408 mutation-only drift genomes ("We did not detect enrichment"; the intervals include
    enrichment). For 101 of the 102, the history effect selection built is a transient of a few tens of ticks, about
    six times drift's at the start.
  - **The model's switch is not found in the worm's literature.** A bounded, quote-checked check of 44 sources finds
    nearby phenomena (RMD's two stable potentials in one report, persistent command states, a turn memory placed by its
    authors in oscillation phase), and multistability on the connectome is known from earlier models.
  - **About a third of the switches keep two states with no sensory input.** In a 2000-tick removal of all sensory
    input, "55 of 169 switches held two states" and 54 returned to their original states; 112 faded to one state.
  - **The champions' foraging depends on their neural time scale, in both directions.** Making every neuron four times
    faster cut their score by 24.5%, four times slower by 35.1%, with T0's stereo champions descriptively similar.
    Whether the fading history effect itself helps them forage was not answerable at this cost.
- **What it adds up to** (interpretation): N2's head core is unusually dense, and placing its block into other
  graphs makes history-dependent switches more common; on these 30 neurons, with equal magnitudes, spreading a fixed
  weight over more edges lowered the rate, and N2's uneven weights raised it over equal ones (described); within N2,
  the switches are fragile at RIA's connections, and a third of them hold without sensory input. Nothing so far shows
  that N2's labelled degrees or its specific wiring add beyond its block's uneven weights, why N2's fading genomes
  retain more, or that the switches, or the champions' fading history effect, matter for behaviour.

## Terms

- **N2** is the *C. elegans* connectome used as the brain's wiring; the **null graphs** are shuffled versions from
  five ensembles (SH, SH-route, SH-class, SH-mirror, SH-recip), each keeping different properties of N2.
- A **genome** is one random set of weights, time constants and biases on a graph (generation 0, never evolved).
- **The probe:** each genome is given two histories, a 10-tick food ramp from 0.25 or from 1.75 of the final level,
  then held at the same level. The **history difference** is how far the two runs stay apart; time is in **ticks**.
- **The turn read-out** is the eight head motor neurons whose output turns the worm; **a** = |δy(0)| is the
  absolute read-out difference between the two histories at the end of the ramp, and a genome is **eligible** if a
  passes a floor.
- **Retention** r = |δy(30)|/a is how much of the difference remains after 30 ticks; the **share** is
  Σ|δy(30)| / Σ|δy(0)| over a graph's genomes. 03mc's registered share is over all genomes; M1 and M2 use the
  **eligible share**, over eligible genomes only.

## The question and how it was worked

03mc's fourth primary showed N2's random brains keeping 0.436 of their history difference 30 ticks after the ramp,
more than all but 0 to 2 of each null ensemble's 128 graphs. The owner asked why, through a three-round brainstorm
with Astra 6 and Fable 5.1, with a ChatGPT roadmap the owner supplied, which produced
[`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md): accounting and quick checks that could kill a candidate cheaply (M1), a
validated dynamical census (M2), a core defined from the anatomy alone (M3), interventions and a transplant screen
(M4), and M5, a confirmatory transplant needing a pre-registration, prepared and then postponed (section 6).

The routine at every step:
- a plan fixing the panels, the measures, the reading rules and their thresholds, reviewed by both models (2 to 9
  rounds), their fixes taken, and committed with its code and tests before the run. Some final rounds ended with one
  reviewer's narrow fixes taken without a further round. Two disclosures: M4a's design changed after a smoke run during
  its review, on other genomes, whose numbers the plan reports and used to change the controls; the reported run came
  afterwards (M4A-PLAN, D357). M4c's classification census started during its plan's first review round and ran an
  unarchived working-tree version of `m4c.py`; its records were checked afterwards for metadata and alignment, which
  is not a check that the executed code was the committed one (D361, D362). M3 ran no new simulation: it closed on M1's existing analysis plus one
  table;
- the run on the CPU of the tested machine, inside the compute accounting;
- a results file written from the committed records, with anything not fixed in the plan marked "after the data",
  reviewed by both (2 or 3 rounds) with every fix taken, and every review archived in `docs/reviews/`.

| Step | What it asked | Reading | CPU hours | Results |
|---|---|---|---|---|
| M1 | Is the lead an artefact of amplitude, alignment, weighting or a cheap mechanism? | amplitude rule (D1) inconclusive, then "does not fire" in its replication; alignment rule (D2) "does not fire" | 3.89 | [`M1-RESULTS.md`](M1-RESULTS.md) |
| M2 pilot | Can a classifier sort genomes into stable states, fading, oscillation and unresolved, reliably? | every check passed; two states reached from nine tested starts | 1.31 | [`M2-PILOT-RESULTS.md`](M2-PILOT-RESULTS.md) |
| M2 census | How much of N2's lead is separate states? | tick 30 "inconclusive"; tick 300 "most" (descriptive) | 12.03 | [`M2-CENSUS-RESULTS.md`](M2-CENSUS-RESULTS.md) |
| M3 | Does a core defined from the anatomy predict the outcomes? | closed as a completed screen | none | [`M3-NOTE.md`](M3-NOTE.md) |
| M4a | Do the head core's connections maintain the history? | "unresolved" | 6.37 | [`M4A-RESULTS.md`](M4A-RESULTS.md) |
| M4b | Is the switch held where its two states differ? | "unresolved" | 0.69 | [`M4B-RESULTS.md`](M4B-RESULTS.md) |
| M4c | Is RIA's part more than its weight? | positive | 5.72 | [`M4C-RESULTS.md`](M4C-RESULTS.md) |
| M4d | Does N2's head-core block carry the switch into other graphs? | "Unresolved (the unresolved genomes decide it)" | 26.34 | [`M4D-RESULTS.md`](M4D-RESULTS.md) |
| M4e | What does a dense block carry: its edge count, its total weight? | Δ_count "lowers" (size unresolved); Δ_weight direction unresolved, no effect of 0.004 or more as a mean across ten hosts | 32.66 | [`M4E-RESULTS.md`](M4E-RESULTS.md) |
| M5 pilot | M5's protocol, audit and spread, on M4e's hosts | design inputs, not a reading | 23.42 | [`M5-PILOT-RESULTS.md`](M5-PILOT-RESULTS.md) |
| M6 option 0 (added 2026-10-30) | Is the history effect selection built in 02's champions a switch or fading? | no enrichment detected (1 of 102 champions a switch); persistence "shortened" against drift, relative to each genome's own start | 0.96 | [`M6-0-RESULTS.md`](M6-0-RESULTS.md) |
| M6 option 3 | Does the worm's literature show the model's switch? | not found; nearby phenomena recorded | none | [`M6-3-LITERATURE.md`](M6-3-LITERATURE.md) |
| M6 step 1 | Do the switches' states outlast the input? | "55 of 169 switches held two states" without sensory input; 54 returned | 0.20 | [`M6-OUTLAST-RESULTS.md`](M6-OUTLAST-RESULTS.md) |
| M6 step 2 | Does the champions' foraging depend on their neural time scale? | four times faster "reduced" their score (−24.5%); both controls' reductions exceeded (floor caveat) | 3.64 | [`M6-STEP2-RESULTS.md`](M6-STEP2-RESULTS.md) |

The hours are recorded wall-clock hours on the CPU, summed before rounding to 112.43 (56.35 for M1 to M4d). The
brainstorm's own exploratory batches, before M1, are not included, nor is M5's power calculation, a simulation outside
the compute accounting with no neural updates (about 45 CPU minutes per reading; [`M5-POWER-RESULTS.md`](M5-POWER-RESULTS.md)).
*Annotated 2026-10-30 (D377): with M6's option 0 the recorded total is 113.39 hours (`summary.json`, `compute`); the 112.43 above is M1 to M5's pilot.*
With all of M6 the recorded total is 117.23 CPU hours (`summary.json`, `compute`, `total`), still with no GPU. M6's
steps followed the same routine: each was reviewed by both models before its run and after it, in one or two rounds.

## What was found, step by step

### 1. The lead is in the upper tail, not an artefact (M1)

- **It replicates.** On fresh CPU genomes N2's eligible share at tick 30 is 0.444 and 0.443 on two panels, against a
  median of 0.275 over 30 random graphs (6 per ensemble; range 0.181 to 0.405).
- **The weighting does not make it.** The eligible-genome version of the registered share splits exactly into the
  mean per-genome retention plus a covariance term (on 03mc's arrays, 0.43451 = 0.58615 − 0.15164). N2's mean retention,
  0.586, is beyond all 640 of 03mc's graphs (ensemble medians 0.370 to 0.412); the covariance term lowers N2's share
  more than most graphs' (medians −0.111 to −0.128). This corrected the roadmap's first finding, which had said the
  extreme part was the amplitude-weighted share.
- **But the median genome is ordinary** (17 to 46 graphs per ensemble at or above it), the upper quartile of
  retention is extreme, and trimming the top 5% of contributors puts N2 inside every ensemble's range. Which genomes,
  ranked by retention, carry the lead was not measured.
- **Amplitude** (D1): the first test could not read (its matched comparison covered only 34% and 41% of N2's
  signal); a targeted replication with smaller scalings met every condition and read "does not fire": f = 1.01 and
  1.03, so amplitude does not account for most of the lead. f is a fraction of the lead within the matched strata,
  over a mixture the new scalings changed, not of the original lead.
- **Alignment** (D2): "does not fire". The difference's alignment with the turn read-out improves less in N2 than in
  the reference, so persistence of the activity difference carries all of N2's excess.
- **The quick checks:** equal time constants leave 92% of the lead ("survives"); the left-right antisymmetric share
  is large but not distinctive ("not rejected"); gap dissipation reads "support" narrowly on one panel and partial on
  the other; genomes that grow transiently are more common in N2 than in the five null graphs sampled ("not
  rejected").

### 2. Two kinds of genome: switches and slow faders (M2)

- **The classifier.** For each genome the two histories are followed for 2000 ticks, candidate equilibria are located
  by Newton's method and their stability checked, and the genome is classed: separate states (each history reaches
  its own stable root), fading (one root), persistent oscillation, or unresolved. The pilot passed all six checks:
  agreement with 03mc's settling rule (420 of 421), resolution (0.4% unresolved), robustness to integration and
  batching (99.5% or more), return from 9990 perturbations, the derivative check, and six planted genomes named
  exactly. From nine ramp starts, every separate-states genome reached exactly two stable roots, switching once; nine
  starts cannot exclude more states.
- **The census** (48 panels, 47,084 eligible genomes) passed every check. N2 has 15 and 13 separate-states genomes
  of about 1000 on its two panels; 19 of the 30 reference graphs have none; the 10 graphs selected in 03mc for a high
  share or many settled genomes have 12 to 78 each.
- **The split at tick 30 is "inconclusive"** on both panels: separate states carry 0.47 (90% interval 0.28 to 0.67)
  and 0.35 (0.14 to 0.55) of N2's mean lead over the reference, fading genomes 0.44 and 0.64, and unresolved genomes
  about 0.09 on the first panel. "Little" is excluded on one panel; "most" on neither. The split is by genome: each
  genome's whole tick-30 difference, transient part included, goes to its class, so it is not a split of persistent
  against transient signal.
- **The two parts enter differently.** Switches enter N2's lead by N2 having more of them; as a class, weighted by
  amplitude, they keep about their whole start difference at tick 30 (0.98 and 1.02), though individual genomes range
  from 0.27 to 1.69. Fading genomes enter by retention: as a class, N2's keep 0.38 and 0.40 at tick 30, against a
  reference median of 0.27 (after the data, above all 30 reference graphs); that is an aggregate, not a statement
  that most individual fading genomes fade more slowly. Fading's part is transient: at tick 300 the switches carry
  0.87 and 0.99 of what lead remains.
- **Batch 7's frozen shuffles** (from the brainstorm; descriptive, three graphs each): graphs that keep frozen a
  30-neuron core chosen from N2's own start difference (`top30_start`, not C3 below; the two share 18 neurons) have 9
  to 26 switches, differing on that core as N2's do, which is partly by construction; graphs that keep a hub set
  have 1 to 4.

### 3. Where the switch is vulnerable (M3, M4a, M4b, M4c)

- **The anatomy core (M3).** C3, the 30 neurons of the turn read-out's one-step input neighbourhood with the most
  internal connections, was fixed from N2's anatomy before any intervention; it contains the eight read-out neurons.
  N2 is outside every null graph's range on local density, so within-ensemble correlations, all weak, could not test
  whether that density matters; M3 was closed as a completed screen, and C3 went to M4.
- **Cutting the core (M4a), "unresolved".** Cutting C3's 260 internal chemical edges for 30 ticks costs more of the
  full-state separation than each of 30 sampled cuts of equal size, on both panels, but on one panel the interval
  crosses the margin (lower bound 0.008 against 0.10); the cut is also nearly four times stronger at once, so
  maintenance is not separated from disruption. Described: started from their two roots, 26 of N2's 28 switches end
  in one basin after the cut, against 14% under the sampled cuts; in the selected graphs, whose switches differ
  mostly off C3, C3's cut erases about as many as their sampled cuts.
- **Cutting each switch's own edges (M4b), "unresolved".** In N2, cutting the edges among a switch's 30
  most-differing neurons erases 89%, against 31% and 11% for exterior and outgoing controls (the outgoing controls
  carried only 0.39 of the own set's weight in N2). Across ten selected graphs the effect is not demonstrated: two
  respond like N2, and six of the other eight erase fewer under the own cut than under the exterior control. A
  dissection of C3, described: RIAR's 26 and RIAL's 29 core edges alone erase 20 and 17 of the 28 switches, while 14
  of C3's 30 neurons, cut alone, erase none.
- **RIA against its weight (M4c), positive.** Pre-specified after M4b, on 141 fresh N2 switch genomes: cutting RIAR's
  or RIAL's core edges erases 0.72 and 0.58, against 0.22 to 0.30 for edge sets of the same summed weight drawn three
  ways (exterior edges, more core edges, the same number of core edges). All six differences have lower bounds of
  0.23 to 0.38, above the 0.10 margin, and no single control set of 60 per side reaches either RIA side. The
  dissection's order repeated on the fresh genomes (Spearman +0.86). The limits: no control removes one core
  neuron's whole chemical star inside the core, as cutting RIA does; one heavier, more concentrated core set erased
  fewer, but one set does not exhaust explanations by the distribution of weight; and SMDVL, RMDR and SMDVR also
  erase many switches with less weight.
- **What "erased" means** throughout: both histories end in the same basin after the network is restored. Both
  stable states still exist, so a cut that erases has moved the histories, not destroyed the switch.

### 4. Moving the block (M4d)

- **The design.** In ten fresh null hosts, two per ensemble, C3's block of chemical edges was replaced by one of six
  blocks, beside the intact host (I), on the same 1024 genomes per host: **D**, 260 off-diagonal edges with N2's block
  weights at random positions, plus N2's eight autapses at their original neurons; **R**, N2's block rewired at its in- and out-degrees and out-strengths; **Rr**,
  R keeping the number of N2's reciprocal pairs (75), not the pairs themselves (corrected, below); **P**, N2's edges with their weights shuffled; **T**, N2's block itself (260
  off-diagonal edges of total weight 2347, plus 8 autapses); **T+G**, T with N2's gap junctions in the block. Every
  genome was classified, and hosts were the unit.
- **Robust:** with N2's block, 64 of 10,240 genomes are switches, against 4 with the host's own block; T exceeds I in
  every host, and over every assignment of the unresolved genomes (T − I +0.0059, 90% interval 0.0048 to 0.0069).
- **Not resolved:** the rewired blocks reach 52 (T − R +0.0012, −0.0009 to 0.0032). On the counted genomes that would
  rule out a wiring advantage of 0.004 or more as a mean across these ten hosts (a response confined to a minority of
  host graphs may be missed); but the classifier left 50 genomes unresolved with T and 36 with R, and over every
  assignment of them the upper bound reaches 0.0087. No assignment could make the decision rule pass, which does not
  exclude a true advantage of 0.004.
- **Described:** D gives 24, P 69. T shares one switch genome with P and one with R, as R does with Rr, while T and
  T+G share 25 of 64 and 50. Genomes that did not settle within the observed horizon
  (persistent oscillation or unresolved) gather in T and T+G (76 and 70, against 43 to 53 in the other block arms
  and none in the intact hosts). Moving N2's switch genomes' core parameters into fresh exteriors kept the switch in
  13 of 282 trials in N2 (6 for the control) and 25 of 1410 in the hosts (10).

### 5. What a dense block carries (M4e)

- **The design.** In ten more fresh null hosts, two block draws each, 1024 paired genomes per host and arm, C3's block
  was replaced by equal-magnitude random blocks crossing the edge count (the host's 92 to 126, or N2's 260) with the
  total weight (the host's 487 to 771, or N2's 2347): **U_LL**, **U_LH**, **U_HL** and **U_HH**, the first letter the
  count and the second the weight. Beside them: **W**, U_HH's support with N2's uneven weights; **K**, N2's labelled
  in- and out-degrees with its weights shuffled and reciprocity matched to W; **T**, N2's block; and **I**, the intact
  host. Every genome that mattered (separate states, oscillating or unresolved) and 40 pre-drawn fading genomes per
  panel were classified again at a hold of 22,000 ticks. Agreed with both reviewers in two design rounds (Astra's
  factorial, Fable's question about a block summary) and three on the plan and code.
- **Δ_count (U_HH − U_LH) "lowers".** At N2's total weight, spreading it over 260 edges gives 4 separate-states
  genomes against 31 on the host's count: −0.0026 (95% interval −0.0041 to −0.0012), lower in 9 of the 10 hosts. Over
  every assignment of the unresolved genomes the upper bound is −0.0004, about four genomes; on the first pass alone
  the direction would have been unresolved. The size is unresolved.
- **Δ_weight (U_HH − U_HL): direction unresolved.** Raising the total weight at N2's count gives 4 against 12:
  −0.0008 (−0.0017 to +0.0001), and no effect of 0.004 or more, as a mean across these ten hosts (a response confined
  to a minority of host graphs may be missed).
- **The second pass was used.** No audited fading genome became separate states (783 to 800 audited per arm); it
  settled 56 of 201 first-pass unresolved genomes. "Every assignment" here and below covers the genomes left
  unresolved, given every other genome's class; it does not allow for transitions the audit could have missed among
  unaudited fading genomes (Astra), which matters most for the thin margins of Δ_count and W − U_HH.
- **Described, not read.** U_HH, the equal-magnitude block at N2's count and weight, is the lowest of the eight arms.
  N2's block's rise over it arrives in three steps:

  | Step | Mean | 95% interval | Over every assignment of the unresolved genomes |
  |---|---|---|---|
  | N2's uneven weights on the same support (W − U_HH) | +0.0026 | 0.0008 to 0.0044 | above zero, just (0.0005) |
  | N2's labelled degrees (K − W) | +0.0023 | 0.0004 to 0.0043 | unresolved |
  | N2's exact block against K (T − K) | +0.0020 | −0.0020 to +0.0059 | unresolved |

  T − K is a package, not exact wiring alone: T also carries N2's 8 autapses and 75 reciprocal pairs (Astra). T − I is
  +0.0062 (0.0028 to 0.0095), in all ten hosts, against M4d's +0.0059.
- **After the data.** Every block whose spectral summary S3 (the square root of the spectral radius of the
  block with each weight squared) is below 1 sits at a similar low rate, U_HH included, and the rate rises only in the four arms at 1.26 and
  above; no arm lies between, so these arms cannot locate a threshold or tell a step from a steep continuous rise
  (Fable). Arms with similar
  summaries still differ: U_LH, W, K and T have 31, 31, 55 and 75 separate-states genomes.

### 6. M5 prepared, then postponed

- **The question** (the owner's third item): does N2's exact block (T) raise the share of genomes confirmed as
  separate states by the protocol over M4d's rewired control Rr, which keeps the number of N2's reciprocal pairs?
  Success is a lower confidence limit above zero; power was planned at a true difference of 0.002.
- **The pilot** (on M4e's hosts; none of its data would enter M5). None of the 117 genomes unresolved at 22,000 ticks
  (T 33, K 37, Rr 47) resolved by 100,000 ticks, so M5 keeps the 22,000-tick protocol and treats its unresolved genomes
  as a class at that horizon, a protocol treatment: the pilot did not tell the classifier's limits from hard dynamics.
  0 of 1500 audited fading genomes per arm changed class. T − Rr was +0.0016 (−0.0008 to +0.0040), above zero in 6 of
  10 hosts, reported and not used. Its spread across hosts was SD 0.0034; genome sampling was 94% of the estimated
  variance, with the host component's negative moment estimate set to zero and weakly determined by ten hosts, so the
  power calculation also ran a wider host spread, up to M4e's T − K.
- **The power calculation** simulated M5's whole reading, with success as "raises" in six readings (raw,
  audit-adjusted, the two one-arm sensitivities to the unresolved genomes, and each of those combined with the audit).
  Three design rounds with both reviewers, then three on the results (the third Astra only). For 80% power at 0.002 the
  agreed rule recommends two stages: under the simulation model, 110 hosts first and up to 160, at a mean of about 72
  CPU hours at the pilot's spread (power 0.84), 91 at the wider core spread (0.81) and 96 above it (0.75), capped at
  145 hours; a fixed 135 hosts would take about 92. The reading gained a Welch t after the simulated nulls, before
  any M5 data. **The identification limit** (Astra): M5 could show more genomes confirmed as separate states by this
  protocol, not more underlying separate states.
- **Postponed** by the owner on 2026-10-29 (D373), for its cost against its benefit, after Claude recommended it:
  an effect near two genomes in 1000, near the pilot's estimate, whose interval includes zero, for 72 to 91 CPU hours
  plus a pre-registration and a results review; nothing else waits on its answer. The design, pilot and power
  calculation are kept, and resuming starts at the choice of host count. The counts hold for the code at 7f04382; if
  the engine or the reading changes, the power script is rerun first. A GPU run would change the cost side.

### 7. M6: the evolved champions, the literature, and the thread's last two checks

*Added in draft 5. Every step here is exploratory: plans fixed the measures and wordings before the runs, none was
pre-registered.*

**Option 0, the evolved champions** (D376-D377; [`M6-0-RESULTS.md`](M6-0-RESULTS.md)). M6 began with an options note
([`M6-OPTIONS.md`](M6-OPTIONS.md)), and the owner chose to classify 02's evolved T1 foraging champions first. Every
saved T1 genome (102 generation-39 champions, 102 generation-0, 4 generation-79) and 408 new mutation-only drift
genomes were classified by M2's frozen classifier, under each run's food mapping, on each run's own input bank.
- **Switches:** "We did not detect enrichment of probe-defined switches in g39 champions relative to the
  mutation-only control; 1 were found" (1 of 102, against 5 of 408 drift; g39 minus drift −0.015, −0.044 to +0.013).
  The intervals include enrichment.
- **The fading effect:** for 101 of the 102 champions, the history effect is a transient (median τ_stay 39 to 46.5
  ticks by family), about six times drift's at the start. The fixed reading, "shortened" against drift, is relative
  to each genome's own start.

**Option 3, the literature** (D378; [`M6-3-LITERATURE.md`](M6-3-LITERATURE.md)). At the owner's choice, with both
reviewers consulted, a bounded check of 44 sources (30 full texts, every quoted passage matched against the sources)
asked whether the worm shows what the model found. **It does not show the model's switch.** Nearby:
- RMD's two stable membrane potentials (one report; its mechanism is open);
- persistent command and modulatory states, and neurons integrating recent motor history;
- a turn memory that Dunn et al. 2025 place in the phase of distributed head-swing oscillations, which the model's
  probe does not assay;
- RIA as an integrator, with no source checked showing or testing a stored state.

Multistability on the connectome is known from earlier models (Kunert-Graf et al. 2017; Liu J et al. 2022), so the
thread's switches are attractors of a known kind, selected by a specified history. This is not biological validation
of the model, in either direction.

**Step 1, do the states outlast the input?** (D380-D381; [`M6-OUTLAST-RESULTS.md`](M6-OUTLAST-RESULTS.md); Fable's
suggestion.) The 169 N2 census switches of M2 and M4c were probed, then held for 2000 ticks with the food input off
(F0) or all sensory input off (Z), then given their input back.
- **Under Z:** "55 of 169 switches held two states during a 2000-tick removal of all sensory input (1 unresolved)"
  (two located, linearly stable fixed points, each reached by its history), and "54 of 169 switches returned to their
  original states after" it. 112 faded to one state; 111 of those ended in the rising-start history's state.
- **F0 agrees** with Z on whether a switch held for 163 of the 169.
- **After the data:** the switches sort into the two known kinds, roughly one to two: multistable without sensory
  input (as in Liu J et al. 2022), or needing the food input to keep two states (as in Kunert-Graf et al. 2017).
- **Not shown:** that the input-free states are the original ones (the roots move; "returned" is the test), basin
  sizes in a noiseless model, or anything about behaviour.

**Step 2, does the champions' foraging depend on their neural time scale?** (D382-D383;
[`M6-STEP2-PLAN.md`](M6-STEP2-PLAN.md), [`M6-STEP2-RESULTS.md`](M6-STEP2-RESULTS.md); Astra's suggestion.) The owner
asked whether the champions' fading history effect matters for their foraging. Both reviewers agreed in the design
round that no intervention at this cost isolates it, so the step asked the nearest answerable question. Every neuron's
time constant was multiplied by k, with the substeps divided by k, an exact time rescaling that keeps the fixed-point
equations and changes every transient; foraging was scored on 02b's 32 criticality worlds.
- **The fixed readings:** "Making every neuron four times faster reduced the champions' T1 foraging score (mean
  within-champion change -24.5%, 95% interval -26.4% to -22.5%)", with the fixed caveat that faster neurons also
  respond faster. The reduction exceeded that of the generation-0 champions and of the drift genomes, under the plan's
  caveat: those controls score lower (1.77 and 0.93, against 2.73) and have less to lose.
- **Both directions cost:** −7.5% at twice as fast, −12.7% at twice as slow, −35.1% at four times as slow. Mean score
  was highest at the intact time scale among the five tested; that does not establish a tuned optimum, the generation-0
  champions also lose in both directions, and the slow arms carry a warm-up hazard in a 200-tick episode.
- **T0's stereo champions** gave descriptively similar losses; the matched difference at four times as fast is −2.8
  points (−6.1 to +0.4). No difference was detected; equivalence is not established.
- **Leaving the 39 sensory and motor neurons at their own time constants** cut the cost of speeding the rest to 6.0%.
  The complementary arm was not run, so the cost is not placed in those neurons, and the arm does not separate
  response speed from memory.
- **The validation** passed: on the probe, the continued history difference shrank to a median 0.23 of intact at four
  times as fast, and grew at four times as slow.

## What holds, and what is open

*Interpretation across steps, after the data.*

| Statement | Status | Where |
|---|---|---|
| N2's tick-30 lead replicates on fresh CPU genomes | holds | M1 |
| N2's mean per-genome retention is extreme; the median genome is ordinary | holds | M1 |
| Amplitude does not account for most of the lead | holds (D1's replication, on this probe) | M1 |
| Read-out alignment does not carry the lead | holds | M1 |
| Some genomes hold the history in two stable states, and N2 has more of them than most random null graphs | holds | M2 |
| How N2's tick-30 lead divides between switches and fading | open (both parts are real; the proportions are not settled) | M2 |
| Why N2's fading genomes retain more at tick 30 | open (not addressed by M4, which studied the switches) | M2 |
| In N2, the switches are fragile to a 30-tick cut of the head core | holds as a description (26 of 28); the panel-level reading is "unresolved" | M4a |
| The targeted cut works across graphs | not demonstrated (two of ten selected graphs respond like N2) | M4b |
| RIA's core edges erase more switches in N2 than edge sets matched on summed weight | holds (positive), in N2, for a 30-tick cut, under three control schemes | M4c |
| RIA stores the switch | not shown; vulnerability only | M4c |
| N2's head-core block makes switches more common in fresh null hosts | holds in two ten-host screens (positive counted contrasts in every host; the aggregate contrast positive over every assignment) | M4d, M4e |
| N2's exact wiring inside the block adds 0.004 or more over rewired copies | unresolved | M4d |
| At N2's total weight, equal-magnitude weight spread over more edges gives fewer switches | holds in direction, by a thin margin over the unresolved genomes; size unresolved | M4e |
| More total weight at N2's count (equal magnitudes) raises the rate by 0.004 or more | excluded as a mean over ten hosts; direction unresolved | M4e |
| N2's uneven weights raise the rate over equal magnitudes on the same support | holds as a description, not a reading | M4e |
| N2's labelled degrees, or its exact block, add over the step before | unresolved (described) | M4e |
| N2's exact block raises the protocol-confirmed share over the rewired control Rr | untested; M5 postponed | M5 pilot |
| Selection on T1 foraging made switches more common than drift | not detected (1 of 102 champions; the intervals include enrichment) | M6-0 |
| The champions' history effect is a transient of a few tens of ticks | holds for 101 of 102, on each run's own bank | M6-0 |
| The model's switch is shown in the worm | not found in a bounded check; nearby phenomena recorded | M6-3 |
| About a third of N2's census switches keep two states without sensory input | holds (55 of 169 under Z, 54 returned) | M6 step 1 |
| The champions' foraging depends on their neural time scale | holds, in both directions | M6 step 2 |
| That dependence is larger for T1's single-nose task than T0's stereo task | not detected; equivalence not established | M6 step 2 |
| The champions' fading history effect matters for their foraging | open; not separable from response speed at this cost | M6 step 2 |
| The switches matter for behaviour | untested (one evolved champion has one) | none |

**A reading across the steps** (interpretation, not a test). In M4d the contrasts against the intact host hold over
every assignment of the unresolved genomes: T, R and D all beat I, the last by less (its envelope's floor 0.0009, under
the 0.004 margin; 0.0013 on counted genomes). The step from random placement to N2's degrees (R − D) holds on counted genomes only, and T − R is
small on counted genomes and bounded between −0.0054 and 0.0087 over the unresolved ones. M4d changed the block's
properties together, so it does not isolate the edge count, the total weight, the degrees or the autapses as causes.
In N2, the switches are fragile at RIA's core connections, which erase more than three controls matched on summed
weight. These are compatible: a dense, heavy block may make switches common, while where a particular switch is
fragile may depend on the wiring. No step tested that account.

M4e separates some of what M4d changed together. The equal-magnitude block at N2's count and total weight did not
reproduce T's observed rate, and at N2's weight more edges lowered the rate: changing how concentrated the weight is
changes how often genomes switch, on these 30 neurons. How much of the transplant benefit that explains is unresolved. The arm averages look more like a threshold in the block's
coupling than a graded dose. Whether N2's degrees or exact wiring add beyond its weights is not resolved; the pilot's
estimate of the exact wiring's advantage over Rr is small and includes zero.

## What it does not show, and the limits that apply throughout

- **One probe:** every result is for the 10-tick ramp from 0.25 or 1.75 of the final food level. M1 and M2's split
  read the turn read-out; M4a read the full-state separation; the classifier and M4d count separate states whether
  or not the read-out differs. Pulses, other durations and other inputs are untested.
- **Unevolved brains:** all genomes are random draws (generation 0). Whether evolved brains use these switches, and
  whether they matter for foraging, is untested. *Draft 5: M6-0 and M6's step 2 studied 02's evolved T1 champions;
  only 1 of 102 is a switch, so whether switches matter for foraging stays untested, and step 2 tested the champions'
  time scale, not their history effect alone.*
- **One connectome and its nulls:** N2 against shuffled and random graphs from the project's samplers; the
  interventions are on N2, and the cross-graph tests on selected or fresh null graphs.
- **Exploratory:** each step fixed its readings before running, but none was pre-registered, and later steps were
  chosen after earlier results (M4c's RIA after M4b's dissection, M4d after M4c, M4e after M4d). M5, the one
  confirmatory step, is postponed.
- **The classifier:** float32 trajectories stall near roots (M2 pilot), Newton's method is sensitive near sustained
  motion, and in M4d's hosts one horizon left 0.3% to 0.5% of genomes unresolved, as many as the effect (the
  census left 33 of 47,084). M4e's second pass at 22,000 ticks settled 28% of its first-pass unresolved genomes, and in
  M5's pilot none of 117 resolved by 100,000 ticks. M5 treats them as a class at its horizon: the unchanged classifier
  could not resolve them, whether from its own limits or from hard dynamics, and they bound what any contrast between
  arms can show.

## Corrections made along the way

- **The roadmap's first finding** ("what is extreme is the registered, amplitude-weighted share") was corrected by
  M1 (D350), beside the finding.
- **M1's ‖δa(0)‖ reading** ("a small part of the lead is attributable to amplitude") was withdrawn after its
  replication showed that comparison was unbalanced (D352; Fable).
- **Claude's own messages to the owner** overstated during M1 ("the average genome keeps 0.59", the lead from "the
  upper half of genomes generally", then "roughly the top quarter"); M1-RESULTS corrects all three. During the
  brainstorm, "2× or 4× finer" integration (really 16 substeps against the baseline 32) and "a latch, a flip-flop"
  (too strong) were corrected before publication (D346).
- **Draft 3 of this page described M4d's Rr** as "R keeping N2's 75 reciprocal pairs". Rr keeps their number, 75,
  not N2's particular pairs: a swap may break one pair and make another (M5-PILOT-PLAN). The pilot's 20 Rr blocks share
  52 to 67 of N2's 150 reciprocal edges (mean 59). Caught by both reviewers of draft 4 (Fable had caught the same phrase
  in D369's review); corrected in section 4, with a dated note in M4D-RESULTS.
- Every results file lists, in its header and in DECISIONS.md, what each review caught.

## Lessons for what comes next

- **Plan the unresolved genomes.** M4d's reading turned on 86 genomes the classifier could not resolve. A follow-up
  should fix in advance a second, longer classification for every arm's unresolved genomes (Fable, Astra). M4e did,
  and its second pass decided Δ_count's direction.
- **Set margins against observed base rates.** The intact hosts gave 0.04% switches, a third of the 0.12% the plan
  took from M2's reference graphs.
- **Match the controls' weight, and check it.** M4b's outgoing controls carried only 0.39 of the own set's weight in
  N2, found in review; M4c matched summed weight in all three families. M4a's effect-matched controls selected weakly
  affected genomes and were set aside.
- **Count before claiming.** Results drafts were corrected for counts and wording in review; for example M4a's
  draft 1 said the switches hold "most" of the intact separation at tick 60, which was 33% and 34%.
- **Scope cost against benefit early** (Claude, after the owner asked whether the long runs were giving important
  information). M5's preparation took a 23-hour pilot and, for the power calculation alone, six review rounds before
  its answer: 72 to 91 more CPU hours for an effect near two genomes in 1000. The reviewers' reference calculation in
  M4e's results (about 60 hosts for 0.002 at a spread of 0.0055) already pointed to a cost of that order. It could not
  have replaced the pilot and the full calculation, which settled the control's spread, the audit and the
  identification limit (Astra). The owner's order did put the host count before the plan, so that safeguard worked;
  what went further than the decision needed was the precision bought before it (Fable). A rough cost and the likely
  size of the answer should go to the owner before a step's plan.
- **Ask whether the question can be answered before costing it** (M6's step 2). The owner's question, whether the
  champions' fading history effect matters, met an intervention that could not isolate it; the design review said so
  and the step was reframed, with the owner told. A test that also slows the dynamics was what showed the loss was
  two-sided, and the T0 champions were what showed it was not specific to the single-nose task.
- **Check where a setting is read.** In M6's step 2 a substeps setting on the experiment's configuration never
  reached the brain, which reads the genome's own; a timing run showed identical scores and caught it before the plan.

## What comes next

The owner chose, on 2026-10-25, in this order (D365 quotes them): this write-up; "a study of what a dense block
carries, its size, weights and degrees" (M4e); and an M5 test of N2's exact wiring, after working out how many hosts it
would need. The first two were completed, in that order; M5's preparation reached its host-count recommendation,
and the owner postponed M5 there (D373).

On 2026-10-29 the owner agreed ("Sure", D374) to Claude's suggestion for what follows: this update, then a design for
M6's behaviour question ([`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md)): does a brain with these switches use them in a task that needs
memory? 03h's lessons apply: a path for the remembered signal that the read-out can see, and a power rule fixed in
advance. All on the CPU unless the owner gives the GPU.
*Annotated 2026-10-30 (D375-D377): the design began with an options note ([`M6-OPTIONS.md`](M6-OPTIONS.md)), and the owner chose its option 0, classifying 02's evolved T1 champions first ([`M6-0-RESULTS.md`](M6-0-RESULTS.md)). Selection did not make switches more common than a mutation-only drift control (1 of 102 champions). The history effect it built is, for 101 of the 102, a transient of a few tens of ticks, larger than drift's at the start. Next, by the plan's branch and at the owner's word: biology (option 3) or stopping the thread (option 4).* *Corrected 2026-10-30 (D379, Astra, Fable): "Selection did not make switches more common than a mutation-only drift control" overstates M6-0's fixed reading, "We did not detect enrichment of probe-defined switches in g39 champions relative to the mutation-only control"; its intervals include enrichment. The fading transient is on each run's own input bank.*
*Annotated 2026-10-30 (D378): the owner chose option 3. A bounded literature check ([`M6-3-LITERATURE.md`](M6-3-LITERATURE.md)) does not show the model's switch in the worm; it records a two-state membrane property in RMD (one report, mechanism open), persistent command and modulatory states, and a turn memory placed by its authors in oscillation phase, which the probe does not assay. Multistability on the connectome is known in earlier models, so the thread's switches are attractors of a known kind, selected by a specified history.*
*Annotated 2026-10-30 (D379): the owner's order for what follows: a quick check of whether the switches' states outlast the input, then a test of whether the evolved champions' fading history effect matters for their foraging, then the thread stops, its results folded into this write-up.* *The quick check has run (D380-D381, [`M6-OUTLAST-RESULTS.md`](M6-OUTLAST-RESULTS.md)): "55 of 169 switches held two states during a 2000-tick removal of all sensory input (1 unresolved)", 54 returned to their original states after it, and 112 faded to one state. The switches sort into M6-3's two known kinds, roughly one to two: multistable without sensory input, or needing the food input. The recorded total is now 113.59 CPU hours (`summary.json`).* *Annotated 2026-10-31 (D382-D383, [`M6-STEP2-RESULTS.md`](M6-STEP2-RESULTS.md)): the champions' test has run, reframed in review as whether their foraging depends on neural time scale. The champions' foraging depends on their neural time scale: making every neuron four times faster cut the T1 champions' score by 24.5% (95% interval 22.5% to 26.4%), and making them four times slower cut it by 35.1%. T0's stereo champions lost about as much (matched difference at four times faster: -2.8 points, -6.1 to +0.4; no difference detected, equivalence not established). Leaving the 39 sensory and motor neurons at their own time constants cut the cost to 6.0%. The tested interventions do not establish whether the fading history effect benefits foraging. The recorded total is now 117.23 CPU hours (`summary.json`). The thread now stops, by the owner's order, and this write-up takes in its last steps.*

**The thread stops here** (draft 5, 2026-10-31), by the owner's order of 2026-10-30 (D379): the quick check, the
champions' test, then stop. Nothing is scheduled. What is kept for anyone who picks it up:
- **M5,** the test of N2's exact wiring, prepared and postponed (section 6); resuming starts at the host count.
- **Open questions** from the table above: why N2's fading genomes retain more; whether the switches, or the
  champions' fading history effect, matter for behaviour. The second needs an intervention that changes the history
  effect without changing response speed, which step 2's review found no cheap way to do (resetting each brain towards
  its steady state was costed at about 100 times step 2).
- **The literature check's pointer:** the worm's best-described turn memory is held in oscillation phase, which this
  probe cannot see.

## Who did what

- **The owner:** the question, the brainstorm's format and three of its ideas (a ring of states became M2's
  question; loops became M4's wiring question; transplanting became M4d and M5), the ChatGPT roadmap they supplied,
  the go-ahead at each step, the direction after M4d (M4e, then M5 after a power calculation), M5's postponement
  and the turn to behaviour; in M6, option 0, option 3 with both reviewers consulted, and the order of the last steps
  (the quick check, the champions' test, then stop). Choices in between were delegated: M4a's direction was
  agreed with both reviewers (D357), M4b and M4c were Claude's proposals, and M4d was chosen by consensus under the
  owner's "As you prefer, but confirm with fable and astra" (D363).
- **Astra 6:** the decomposition of the registered measure that produced M1's correction, and the amplitude scaling
  around the midpoint that D1 used; the persistence-alignment split; the separation of write, hold and read; M4a's
  Part 2 from the roots, the assay behind "26 of 28" that M4b and M4c used; M4c's control family C (same count and
  total weight inside the core); M4d's corner envelope over the unresolved genomes, which produced its reading;
  independent reproductions of M1's summary and bootstrap, D1's replication, the M2 pilot's numbers (with Fable), and
  M4d's checks and reading; for M4a, that a null reads "not demonstrated", not "access" (D357); the
  null-boundary correction to M4d's power argument. M4e's factorial of edge count by total weight with W and K arms,
  its larger audit, and T − K as a package; for M5, its target fixed before its power, the identification limit, the
  Welch t in the reading (D372), rule C's invalid hosts and stage-1 audit bound, and an invalid host's audit leaking
  into the reading. In M6: the run-level enrichment test and τ_stay (M6-0); the literature check's reframing around
  history-dependent dynamics, and Liu J 2022 (M6-3); separating holding from returning, and Z as the test of the
  network alone (step 1); the champions' test itself, the exact rescaling's validation with written states held fixed,
  the matched T1 − T0 contrast, and the step-2 results' corrections ("tuned optimum", T0 equivalence, the interior arm).
- **Fable 5.1:** the amplitude objection that became D1; the anatomy predictor and core defined without the result
  (M3); the core dissection that pointed at RIA; M4a reading the full state, since C3 holds the read-out's inputs;
  M4b's outgoing control; M4d's Rr arm, and the argument that M5 cannot be pre-registered without host base rates,
  which made M4d a screen; the withdrawal of M1's ‖δa(0)‖ reading; M4d's not-settled pattern and the argument that
  resolving its unresolved genomes could not change the decision. M4e's dose question on a block summary and its
  stage 0, the threshold reading of its arms, and the S3-matched estimand; for M5, keeping the planning effect at
  0.002, the continuation sample in place of a flag, and bringing the pilot's continuation evidence (none of 47 Rr
  genomes resolved by 100,000 ticks) into the decision; and the Welch t's acceptance in round 2. In M6: the 30
  graph-and-run blocks as the unit (M6-0); the RMD guard and the model precedents (M6-3); the outlast check itself and
  the classifier's distinctness level (step 1); the exact rescaling (substeps divided by k), T0's champions as the
  temporal control, the interior arm, the warm-up hazard, and, in the results, that the interior arm cannot place the
  cost in the boundary neurons.
- **Both:** the classifier's validation design in M2's nine plan rounds; independent reproductions of M4e's readings;
  for M5, no host count before a pilot (D369); in M6, the Kunert-Graf correction (the probe holds the final input, so
  "outlasts its input" was wrong), and that no cheap intervention isolates the champions' history effect, which
  reframed step 2.
- **Claude:** ran the brainstorm, wrote every plan, the code and tests, ran every step, and wrote the results files
  and this synthesis; merged the two M4e designs; recommended postponing M5; in M6, the options note, the order of
  the last steps the owner accepted, and the literature check's retrieval and reading. DECISIONS.md records what each
  review caught in each.

## Where the numbers come from

[`summary.json`](summary.json) (written by [`scripts/memory_summary.py`](../../scripts/memory_summary.py) from
`runs/memory-m1/`, `runs/memory-m2/`, `runs/memory-m2-census/`, `runs/memory-m4a/` to `runs/memory-m4e/`,
`runs/memory-m5-pilot/` and `runs/memory-m5-power-welch/`, and since draft 5 `runs/memory-m6-0/`,
`runs/memory-m6-outlast/` and `runs/memory-m6-step2/`) holds the compute, the readings and the headline numbers above.
M6-3's sources, quotes and checking scripts are in
[`docs/reviews/20261030-m6-3-scope/reading/`](../reviews/20261030-m6-3-scope/reading/). Everything else, including "every check passed" for the census
(the summary carries only C2, C3 and C5), is quoted from the step's results file named beside it.
