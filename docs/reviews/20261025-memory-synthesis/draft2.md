# The memory thread, M1 to M4: what was found

*Draft 2, 2026-10-25, after one round of review (Astra 6 and Fable 5.1, both "fix then publish"; every finding taken;
draft 1 and the reviews are archived in [`docs/reviews/20261025-memory-synthesis/`](../reviews/20261025-memory-synthesis/)).
A synthesis of the memory thread's first four steps (D349-D364), written at the owner's request after M4d. It
reports no new run and changes no reading: every reading below is the one its own results file reached, and every
number comes from those files or from [`summary.json`](summary.json), which
[`scripts/memory_summary.py`](../../scripts/memory_summary.py) writes from the committed records (rule 5).
Exploratory throughout; nothing here is a pre-registration. Where this page interprets across steps, it says so.*

## In short

- **The question** was why N2's unevolved random brains keep more of a recent food history than shuffled graphs do
  (03mc's Q-D, registered: 0.436 at tick 30 against null medians of 0.255 to 0.291). Four steps ran on the CPU
  (56.35 recorded hours, no GPU), each with a plan reviewed by both models before its runs and its results reviewed
  after.
- **The lead is real and sits in the upper tail.** It replicates on fresh genomes (N2 0.444 and 0.443 against a
  median of 0.275 over 30 random graphs, none at or above N2). N2's unweighted mean retention is beyond all 640 of
  03mc's graphs, which corrects the earlier claim that only the amplitude-weighted share was extreme; the median
  genome is ordinary. Read-out alignment does not carry the lead, and amplitude does not account for most of it.
- **A few genomes hold the history as a switch.** A validated classifier finds that fewer than 2% of N2's genomes
  (15 and 13 of about 1000) end in one of two stable states depending on the history ("separate states"). 19 of 30
  random null graphs have none, though graphs selected for many such genomes have more than N2. At tick 30 the
  switches carry 0.47 and 0.35 of N2's lead (the reading is "inconclusive": the intervals are wide), and mostly
  fading genomes carry the rest; by tick 300 the switches carry most of what is left.
- **In N2 the switch is vulnerable in the head core, most of all at RIA.** Cutting the anatomical head core's
  internal chemical edges for 30 ticks sends 26 of N2's 28 switches into one basin (14% for sampled cuts of the same
  size), though two panel-level tests read "unresolved". The one positive reading: on 141 fresh switch genomes,
  cutting either RIA neuron's 26 or 29 core edges erases the history distinction in 72% and 58%, against 22% to 30%
  for three control families matched on summed weight. That is vulnerability, not storage, and RIA is the strongest
  of the single-neuron cuts tested, not the only one that matters.
- **Moved into other graphs, the head core's block raises the switch rate, and its exact wiring is not shown to
  matter.** In ten fresh null hosts (a screen), N2's block lifts the share of switch genomes from 0.04% to 0.62%
  (pooled), in every host. Blocks rewired at the same degrees reach 0.51%. Whether N2's exact wiring adds 0.004 or
  more over them is "Unresolved (the unresolved genomes decide it)".
- **What it adds up to** (interpretation): N2's head core is unusually dense, and placing a block with its edge count
  and weights into other graphs makes history-dependent switches more common; within N2, the switches are fragile at
  RIA's connections. Nothing so far shows that N2's specific wiring matters beyond its block's size and weights, why
  N2's fading genomes retain more, or that any of this matters for behaviour.

## Terms

- **N2** is the *C. elegans* connectome used as the brain's wiring; the **null graphs** are shuffled versions from
  five ensembles (SH, SH-route, SH-class, SH-mirror, SH-recip), each keeping different properties of N2.
- A **genome** is one random set of weights, time constants and biases on a graph (generation 0, never evolved).
- **The probe:** each genome is given two histories, a 10-tick food ramp from 0.25 or from 1.75 of the final level,
  then held at the same level. The **history difference** is how far the two runs stay apart; time is in **ticks**.
- **The turn read-out** is the eight head motor neurons whose output turns the worm; **a** is the read-out
  difference at the end of the ramp, and a genome is **eligible** if a passes a floor.
- **Retention** is how much of the difference remains after a delay; the **share** is the summed read-out difference
  at tick 30 over the summed difference at the start, over a graph's eligible genomes.

## The question and how it was worked

03mc's fourth primary showed N2's random brains keeping 0.436 of their history difference 30 ticks after the ramp,
more than all but 0 to 2 of each null ensemble's 128 graphs. The owner asked why, through a three-round brainstorm
with Astra 6 and Fable 5.1, with a ChatGPT roadmap the owner supplied, which produced
[`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md): accounting and quick checks that could kill a candidate cheaply (M1), a
validated dynamical census (M2), a core defined from the anatomy alone (M3), interventions and a transplant screen
(M4), and M5, a confirmatory transplant that would need a pre-registration and has not been planned.

The routine at every step:
- a plan fixing the panels, the measures, the reading rules and their thresholds, reviewed by both models (2 to 9
  rounds), their fixes taken, and committed with its code and tests before the run. Some final rounds ended with one
  reviewer's narrow fixes taken without a further round. Two disclosures: M4a's design changed after a smoke run during
  its review, which took no result number from it (M4A-PLAN); and M4c's classification census started during its
  plan's first review round and ran an unarchived working-tree version of `m4c.py`, checked afterwards against the
  committed code's record checks (D361, D362). M3 ran no new simulation: it closed on M1's existing analysis plus one
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

The hours are recorded wall-clock hours on the CPU; they sum to 56.35. The brainstorm's own exploratory batches,
before M1, are not included.

## What was found, step by step

### 1. The lead is in the upper tail, not an artefact (M1)

- **It replicates.** On fresh CPU genomes N2's eligible share at tick 30 is 0.444 and 0.443 on two panels, against a
  median of 0.275 over 30 random graphs (6 per ensemble; range 0.181 to 0.405).
- **The weighting does not make it.** The eligible-genome version of the registered share splits exactly into the
  mean per-genome retention plus a covariance term (on 03mc's arrays, 0.435 = 0.586 − 0.152). N2's mean retention,
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
  blocks, beside the intact host (I), on the same 1024 genomes per host: **D**, 260 edges with N2's block weights and
  its 8 autapses at random positions; **R**, N2's block rewired at its in- and out-degrees and out-strengths; **Rr**,
  R keeping N2's 75 reciprocal pairs; **P**, N2's edges with their weights shuffled; **T**, N2's block itself (260
  off-diagonal edges of total weight 2347, plus 8 autapses); **T+G**, T with N2's gap junctions in the block. Every
  genome was classified, and hosts were the unit.
- **Robust:** with N2's block, 64 of 10,240 genomes are switches, against 4 with the host's own block; T exceeds I in
  every host, and over every assignment of the unresolved genomes (T − I +0.0059, 90% interval 0.0048 to 0.0069).
- **Not resolved:** the rewired blocks reach 52 (T − R +0.0012, −0.0009 to 0.0032). On the counted genomes that would
  rule out a wiring advantage of 0.004 or more as a mean across these ten hosts (a response confined to a minority of
  host graphs may be missed); but the classifier left 50 genomes unresolved with T and 36 with R, and over every
  assignment of them the upper bound reaches 0.0087. No assignment could make the decision rule pass, which does not
  exclude a true advantage of 0.004.
- **Described:** D gives 24, P 69. T, P and R switch on almost entirely different genomes (one shared per pair, as
  R and Rr), while T and T+G share 25 of 64 and 50. Genomes that did not settle within the observed horizon
  (persistent oscillation or unresolved) gather in T and T+G (76 and 70, against 43 to 53 in the other block arms
  and none in the intact hosts). Moving N2's switch genomes' core parameters into fresh exteriors kept the switch in
  13 of 282 trials in N2 (6 for the control) and 25 of 1410 in the hosts (10).

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
| N2's head-core block makes switches more common in fresh null hosts | holds in a ten-host screen (every host, every assignment) | M4d |
| N2's exact wiring inside the block adds 0.004 or more over rewired copies | unresolved | M4d |
| The switches matter for behaviour | untested | none |

**A reading across the steps** (interpretation, not a test). In M4d the contrasts against the intact host hold over
every assignment of the unresolved genomes: T, R and D all beat I, the last by less (its lower bound 0.0009, under the
0.004 margin). The step from random placement to N2's degrees (R − D) holds on counted genomes only, and T − R is
small on counted genomes and bounded between −0.0054 and 0.0087 over the unresolved ones. M4d changed the block's
properties together, so it does not isolate the edge count, the total weight, the degrees or the autapses as causes.
In N2, the switches are fragile at RIA's core connections, which erase more than three controls matched on summed
weight. These are compatible: a dense, heavy block may make switches common, while where a particular switch is
fragile may depend on the wiring. No step tested that account.

## What it does not show, and the limits that apply throughout

- **One probe:** every result is for the 10-tick ramp from 0.25 or 1.75 of the final food level. M1 and M2's split
  read the turn read-out; M4a read the full-state separation; the classifier and M4d count separate states whether
  or not the read-out differs. Pulses, other durations and other inputs are untested.
- **Unevolved brains:** all genomes are random draws (generation 0). Whether evolved brains use these switches, and
  whether they matter for foraging, is untested.
- **One connectome and its nulls:** N2 against shuffled and random graphs from the project's samplers; the
  interventions are on N2, and the cross-graph tests on selected or fresh null graphs.
- **Exploratory:** each step fixed its readings before running, but none was pre-registered, and later steps were
  chosen after earlier results (M4c's RIA after M4b's dissection, M4d after M4c).
- **The classifier:** float32 trajectories stall near roots (M2 pilot), Newton's method is sensitive near sustained
  motion, and one horizon leaves 0.3% to 0.5% of genomes unresolved, which in M4d was as large as the effect.

## Corrections made along the way

- **The roadmap's first finding** ("what is extreme is the registered, amplitude-weighted share") was corrected by
  M1 (D350), beside the finding.
- **M1's ‖δa(0)‖ reading** ("a small part of the lead is attributable to amplitude") was withdrawn after its
  replication showed that comparison was unbalanced (D352; Fable).
- **Claude's own messages to the owner** overstated during M1 ("the average genome keeps 0.59", the lead from "the
  upper half of genomes generally", then "roughly the top quarter"); M1-RESULTS corrects all three. During the
  brainstorm, "2× or 4× finer" integration (really 16 substeps against the baseline 32) and "a latch, a flip-flop"
  (too strong) were corrected before publication (D346).
- Every results file lists, in its header and in DECISIONS.md, what each review caught.

## Lessons for what comes next

- **Plan the unresolved genomes.** M4d's reading turned on 86 genomes the classifier could not resolve. A follow-up
  should fix in advance a second, longer classification for every arm's unresolved genomes (Fable, Astra).
- **Set margins against observed base rates.** The intact hosts gave 0.04% switches, a third of the 0.12% the plan
  took from M2's reference graphs.
- **Match the controls' weight, and check it.** M4b's outgoing controls carried only 0.39 of the own set's weight in
  N2, found in review; M4c matched summed weight in all three families. M4a's effect-matched controls selected weakly
  affected genomes and were set aside.
- **Count before claiming.** Results drafts were corrected for counts and wording in review; for example M4a's
  draft 1 said the switches hold "most" of the intact separation at tick 60, which was 33% and 34%.

## What comes next

The owner chose, on 2026-10-25, in this order (D365 quotes them):
1. this write-up;
2. "a study of what a dense block carries, its size, weights and degrees", which the M4d contrasts favour;
3. an M5 test of N2's exact wiring, after working out how many hosts it would need for effects above the margin,
   with the unresolved genomes and base rates planned in advance.

All on the CPU unless the owner gives the GPU.

## Who did what

- **The owner:** the question, the brainstorm's format and three of its ideas (a ring of states became M2's
  question; loops became M4's wiring question; transplanting became M4d and M5), the ChatGPT roadmap they supplied,
  the go-ahead at each step, and the direction after M4d. Choices in between were delegated: M4a's direction was
  agreed with both reviewers (D357), M4b and M4c were Claude's proposals, and M4d was chosen by consensus under the
  owner's "As you prefer, but confirm with fable and astra" (D363).
- **Astra 6:** the decomposition of the registered measure that produced M1's correction, and the amplitude scaling
  around the midpoint that D1 used; the persistence-alignment split; the separation of write, hold and read; M4a's
  Part 2 from the roots, the assay behind "26 of 28" that M4b and M4c used; M4c's control family C (same count and
  total weight inside the core); M4d's corner envelope over the unresolved genomes, which produced its reading;
  independent reproductions of M1's summary and bootstrap, D1's replication, and M4d's checks and reading; the
  null-boundary correction to M4d's power argument.
- **Fable 5.1:** the amplitude objection that became D1; the anatomy predictor and core defined without the result
  (M3); the core dissection that pointed at RIA; M4a reading the full state, since C3 holds the read-out's inputs;
  M4b's outgoing control; M4d's Rr arm, and the argument that M5 cannot be pre-registered without host base rates,
  which made M4d a screen; the withdrawal of M1's ‖δa(0)‖ reading; M4d's not-settled pattern and the argument that
  resolving its unresolved genomes could not change the decision.
- **Both:** the classifier's validation design in M2's nine plan rounds; and, for M4a, that a null reads "not
  demonstrated", not "access" (D357).
- **Claude:** ran the brainstorm, wrote every plan, the code and tests, ran every step, and wrote the results files
  and this synthesis; DECISIONS.md records what each review caught in each.

## Where the numbers come from

[`summary.json`](summary.json) (written by [`scripts/memory_summary.py`](../../scripts/memory_summary.py) from
`runs/memory-m1/`, `runs/memory-m2/`, `runs/memory-m2-census/`, `runs/memory-m4a/` to `runs/memory-m4d/`) holds the
compute, the readings and the headline numbers above. Everything else, including "every check passed" for the census
(the summary carries only C2, C3 and C5), is quoted from the step's results file named beside it.
