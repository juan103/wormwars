# The memory thread, M1 to M4: what was found

*Draft 1, 2026-10-25. A synthesis of the memory thread's first four steps (D349-D364), written at the owner's request
after M4d. It reports no new run and changes no reading: every reading below is the one its own results file
reached, and every number comes from those files or from [`summary.json`](summary.json), which
[`scripts/memory_summary.py`](../../scripts/memory_summary.py) writes from the committed records (rule 5).
Exploratory throughout; nothing here is a pre-registration. Where this page interprets across steps, it says so.*

## In short

- **The question** was why N2's unevolved random brains keep more of a recent food history than shuffled graphs do
  (03mc's Q-D, registered: 0.436 at tick 30 against null medians of 0.255 to 0.291). Four steps, all on the CPU
  (56.4 hours, no GPU), each with a plan reviewed and agreed before its runs (one disclosed exception, below) and its
  results reviewed after.
- **The lead is real and sits in the upper tail.** It replicates on fresh genomes (N2 0.444 and 0.443 against a
  median of 0.275 over 30 random graphs, none at or above N2). N2's unweighted mean retention is beyond all 640 of
  03mc's graphs, which corrects the earlier claim that only the amplitude-weighted share was extreme; the median
  genome is ordinary. Read-out alignment does not carry the lead, and amplitude does not account for most of it.
- **A few genomes hold the history as a switch.** A validated classifier finds that fewer than 2% of N2's genomes (15 and 13 of about
  1000) reach one of two stable states depending on the history ("separate states"), against none in most null graphs. At tick
  30 they carry about 0.35 to 0.47 of N2's lead (the reading is "inconclusive": the intervals are wide), the rest
  being fading genomes that keep more as a class; by tick 300 the switches carry most of what is left.
- **The switch is vulnerable in N2's head core, above all at RIA.** Cutting the head core's internal edges for 30
  ticks sends 26 of N2's 28 switches into one basin (14% for sampled cuts of the same size). Two broader tests read
  "unresolved". The one positive reading: on 141 fresh switch genomes, cutting either RIA neuron's 26 or 29 core
  edges erases the history distinction in 72% and 58%, against 22% to 30% for every weight-matched control family.
  That is vulnerability, not storage.
- **Moved into other graphs, the head core's block raises the switch rate, but its exact wiring is not shown to
  matter.** In ten fresh null hosts, N2's block lifts the share of switch genomes from 0.04% to 0.62% (pooled), in
  every host. Copies rewired at the same degrees reach 0.51%. Whether N2's exact wiring adds anything is
  "Unresolved (the unresolved genomes decide it)".
- **What it adds up to** (interpretation): N2's head core is unusually dense, and a dense, heavily weighted block of
  that kind makes history-dependent switches more common in random brains; within N2, the switches it supports are
  fragile at RIA's connections. Nothing so far shows that N2's specific wiring, as opposed to its block's size,
  weights and degrees, is what matters, and nothing yet connects the switches to behaviour.

## The question and how it was worked

03mc's fourth primary showed N2's random brains keeping 0.436 of their history difference 30 ticks after a food
ramp, more than all but 0 to 2 of each null ensemble's 128 graphs. The owner asked why, through a three-round
brainstorm with Astra 6 and Fable 5.1, which produced [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md): accounting and cheap
kills (M1), a validated dynamical census (M2), a core defined from the anatomy alone (M3), interventions and a
transplant screen (M4), and a pre-registered transplant (M5) that has not run.

Every step followed the same routine:
- a plan fixing the panels, the measures, the reading rules and their thresholds, reviewed by both models until
  both agreed (2 to 9 rounds), and committed with its code and tests before the run. One disclosed exception: M4c's
  classification census started during its plan's first review round; its arms ran after agreement (D361);
- the run on the CPU of the tested machine, inside the compute accounting;
- a results file written from the committed records, with anything not fixed in the plan marked "after the data",
  reviewed by both until both agreed (2 or 3 rounds), and every review archived in `docs/reviews/`.

| Step | What it asked | Reading | CPU hours | Results |
|---|---|---|---|---|
| M1 | Is the lead an artefact of amplitude, alignment, weighting or a cheap mechanism? | D1 inconclusive, then "does not fire" in its replication; D2 "does not fire" | 3.89 | [`M1-RESULTS.md`](M1-RESULTS.md) |
| M2 pilot | Can a classifier sort genomes into stable states, fading, oscillation and unresolved, reliably? | every check passed; two states only | 1.31 | [`M2-PILOT-RESULTS.md`](M2-PILOT-RESULTS.md) |
| M2 census | How much of N2's lead is separate states? | tick 30 "inconclusive"; tick 300 "most" (descriptive) | 12.03 | [`M2-CENSUS-RESULTS.md`](M2-CENSUS-RESULTS.md) |
| M3 | Does a core defined from the anatomy predict the outcomes? | closed as a completed screen | seconds | [`M3-NOTE.md`](M3-NOTE.md) |
| M4a | Do the head core's connections maintain the history? | "unresolved" | 6.37 | [`M4A-RESULTS.md`](M4A-RESULTS.md) |
| M4b | Is the switch held where its two states differ? | "unresolved" | 0.69 | [`M4B-RESULTS.md`](M4B-RESULTS.md) |
| M4c | Is RIA's part more than its weight? | positive | 5.72 | [`M4C-RESULTS.md`](M4C-RESULTS.md) |
| M4d | Does N2's head-core block carry the switch into other graphs? | "Unresolved (the unresolved genomes decide it)" | 26.34 | [`M4D-RESULTS.md`](M4D-RESULTS.md) |

The ceremony's own spike batches, before M1, are not in the 56.4 hours.

## What was found, step by step

### 1. The lead is in the upper tail, not an artefact (M1)

- **It replicates.** On fresh CPU genomes N2's eligible share at tick 30 is 0.444 and 0.443 on two panels, against a
  median of 0.275 over 30 random graphs (6 per ensemble; range 0.181 to 0.405).
- **The weighting does not make it.** The registered share splits exactly into the mean per-genome retention plus a
  covariance term. N2's mean retention is 0.586, against ensemble medians of 0.370 to 0.412, and none of 03mc's 640
  graphs reaches it; the covariance term lowers N2's share more than most graphs' (−0.152 against −0.111 to −0.128).
  This corrected the roadmap's first finding, which had said the extreme part was the amplitude-weighted share.
- **But the median genome is ordinary** (17 to 46 graphs per ensemble at or above it), the upper quartile of
  retention is extreme, and trimming the top 5% of contributors puts N2 inside every ensemble's range. Which genomes,
  ranked by retention, carry the lead was not measured.
- **Amplitude** (D1): the first test could not read (its matched comparison covered only 34% and 41% of N2's
  signal); a targeted replication with smaller scalings met every condition and read "does not fire": f = 1.01 and
  1.03, so amplitude does not account for most of the lead. f is a fraction of the lead within the matched strata,
  not of the original lead.
- **Alignment** (D2): "does not fire". The difference's alignment with the turn read-out improves less in N2 than in
  the reference, so persistence of the activity difference carries all of N2's excess.
- **Cheap kills:** equal time constants leave 92% of the lead ("survives"); the left-right antisymmetric share is
  large but not distinctive ("not rejected"); gap dissipation reads "support" narrowly on one panel and partial on
  the other; transient growers are more common in N2 than in the five null graphs sampled ("not rejected").

### 2. Two kinds of genome: switches and slow faders (M2)

- **The classifier.** For each genome the two histories are followed for 2000 ticks, candidate equilibria are located
  by Newton's method and their stability checked, and the genome is classed: separate states (each history reaches
  its own stable root), fading (one root), persistent oscillation, or unresolved. The pilot passed all six checks:
  agreement with 03mc's settling rule (420 of 421), resolution (0.4% unresolved), robustness to integration and
  batching (99.5% or more), return from 9990 perturbations, the derivative check, and six planted genomes named
  exactly. From nine ramp starts, every separate-states genome reached exactly two stable roots, switching once.
- **The census** (48 panels, 47,084 eligible genomes) passed every check. N2 has 15 and 13 separate-states genomes
  of about 1000 on its two panels; 19 of the 30 reference graphs have none; the 10 graphs selected in 03mc for a high
  share or many settled genomes have 12 to 78 each.
- **The split at tick 30 is "inconclusive"** on both panels: separate states carry 0.47 (90% interval 0.28 to 0.67)
  and 0.35 (0.14 to 0.55) of N2's mean lead over the reference, fading genomes 0.44 and 0.64. "Little" is excluded
  on one panel; "most" on neither.
- **The two parts enter differently.** Switches enter N2's lead by N2 having more of them; each keeps about its whole
  start difference. Fading genomes enter by retention: as a class, weighted by amplitude, N2's keep 0.38 and 0.40 of
  their difference at tick 30, against a reference median of 0.27 (after the data, above all 30 reference graphs).
  Fading's part is transient: at tick 300 the switches carry 0.87 and 0.99 of what lead remains.
- **Batch 7's arms** (descriptive, three graphs each): shuffles that keep N2's head core frozen have 9 to 26
  switches, differing in the same place as N2's; shuffles that keep a hub set have 1 to 4.

### 3. Where the switch is vulnerable (M3, M4a, M4b, M4c)

- **The anatomy core (M3).** C3, the 30 neurons of the turn read-out's one-step neighbourhood with the most internal
  connections, was fixed from N2's anatomy before any intervention. N2 is outside every null graph's range on local
  density, so within-ensemble correlations, all weak, could not test whether that density matters; M3 was closed as
  a completed screen, and C3 went to M4.
- **Cutting the core (M4a), "unresolved".** Cutting C3's 260 internal edges for 30 ticks costs more of the separation
  than each of 30 sampled cuts of equal size, on both panels, but one panel's interval reaches the margin; the cut is
  also about four times stronger at once, so maintenance is not separated from disruption. Described: started from
  their two roots, 26 of N2's 28 switches end in one basin after the cut, against 14% under the sampled cuts; in the
  selected graphs, whose switches differ mostly off C3, C3's cut erases about as many as their sampled cuts.
- **Cutting each switch's own neurons (M4b), "unresolved".** In N2, cutting the edges among a switch's 30
  most-differing neurons erases 89%, against 31% and 11% for exterior and outgoing controls; across ten selected
  graphs the effect is not demonstrated (two respond like N2, most do not). A dissection of C3, described: RIAR's 26
  and RIAL's 29 core edges alone erase 20 and 17 of the 28 switches, while 14 of C3's 30 neurons, cut alone, erase
  none.
- **RIA against its weight (M4c), positive.** Pre-specified after M4b, on 141 fresh N2 switch genomes: cutting RIAR's
  or RIAL's core edges erases 0.72 and 0.58, against 0.22 to 0.30 for edge sets of the same summed weight drawn three
  ways (exterior edges, more core edges, the same number of core edges). All six differences have lower bounds of
  0.23 to 0.38, above the 0.10 margin, and no single control set of 60 per side reaches either RIA side. The
  dissection's order repeated on the fresh genomes (Spearman +0.86).
- **What "erased" means** throughout: both histories end in the same basin after the network is restored. Both
  stable states still exist, so a cut that erases has moved the histories, not destroyed the switch.

### 4. Moving the block (M4d)

- **The design.** N2's C3 chemical block (260 edges plus 8 autapses, weight 2347) replaced the C3 block of ten fresh
  null hosts, two per ensemble, beside six other arms on the same 1024 genomes per host: the intact host, the same
  edges at random positions, rewired at fixed degrees (with and without N2's reciprocal pairs), N2's edges with
  shuffled weights, and N2's block with its gap junctions. Every genome was classified, and hosts were the unit.
- **Robust:** with N2's block, 64 of 10,240 genomes are switches, against 4 with the host's own block; T exceeds I in
  every host, and over every assignment of the unresolved genomes (D_TI +0.0059, 90% interval 0.0048 to 0.0069).
- **Not resolved:** the rewired copies reach 52 (D_TR +0.0012, −0.0009 to 0.0032). On the counted genomes that rules
  out a wiring advantage of 0.004 or more; but the classifier left 50 genomes unresolved with N2's block and 36 with
  the rewired copies, and over every assignment of them the upper bound reaches 0.0087. No assignment could make the
  reading positive.
- **Described:** random placement of the same edges gives 24; N2's edges with shuffled weights 69; the genomes that
  switch differ almost completely between arms; the genomes that never settle gather in the arms with N2's exact
  weighted block (76 with T and 70 with T+G, against 43 to 53 in the other block arms and none in the intact hosts).
  Moving N2's switch genomes' core parameters into fresh exteriors kept the switch in 13 of 282 trials in N2 (6 for
  the control) and 25 of 1410 in the hosts (10).

## What holds, and what is open

*Interpretation across steps, after the data.*

| Statement | Status | Where |
|---|---|---|
| N2's tick-30 lead replicates on fresh CPU genomes | holds | M1 |
| N2's mean per-genome retention is extreme; the median genome is ordinary | holds | M1 |
| Amplitude does not account for most of the lead | holds (D1's replication, on this probe) | M1 |
| Read-out alignment does not carry the lead | holds | M1 |
| Some genomes hold the history in two stable states, and N2 has more of them than most null graphs | holds | M2 |
| How N2's tick-30 lead divides between switches and fading | open (both parts are real; the proportions are not settled) | M2 |
| In N2, the switches are fragile to a 30-tick cut of the head core | holds as a description (26 of 28); the panel-level reading is "unresolved" | M4a |
| The targeted cut works across graphs | not demonstrated (two of ten selected graphs respond like N2) | M4b |
| RIA's core edges matter more than their weight for the switch in N2 | holds (positive), in N2, for a 30-tick cut, under three control schemes | M4c |
| RIA stores the switch | not shown; vulnerability only | M4c |
| N2's head-core block makes switches more common in other graphs | holds (every host, every assignment) | M4d |
| N2's exact wiring inside the block is what does it | unresolved | M4d |
| The switches matter for behaviour | untested | none |

**A reading across the steps** (interpretation, not a test): the robust contrasts in M4d are the ones that change
the block's size, weights and degrees (T and R against I, D against I), while the one that changes only the wiring
at fixed degrees (T against R) is small. In N2, the switches the dense block supports are fragile at RIA, its heaviest
neuron's connections, but more than their weight explains. These two facts are compatible: a dense, heavily weighted
core may make switches common, while where each particular switch is fragile depends on the wiring. Neither step
tested that account.

## What it does not show, and the limits that apply throughout

- **One probe:** every result is for a 10-tick ramp from 0.25 or 1.75 of the final food level, read at the turn
  read-out. Pulses, other durations and other inputs are untested.
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
  replication showed that comparison was unbalanced (D352).
- **Claude's own messages to the owner** overstated twice during M1 ("the average genome keeps 0.59", "the upper
  half generally"); M1-RESULTS corrects both. Earlier, during the brainstorm, "2× or 4× finer" integration (really
  16 substeps against the baseline 32) and "a latch, a flip-flop" (too strong) were corrected before publication
  (D346).
- Every results file lists, in its header and in DECISIONS.md, what each review caught.

## Lessons for what comes next

- **Plan the unresolved genomes.** M4d's reading turned on 86 genomes the classifier could not resolve. A follow-up
  should fix in advance a second, longer classification for every arm's unresolved genomes (Fable, Astra).
- **Set margins against observed base rates.** The intact hosts gave 0.04% switches, a third of the 0.12% the plan
  took from M2's reference graphs.
- **Match the controls' weight, and check it.** M4b's outgoing controls carried only 0.39 of the own set's weight in
  N2, found in review; M4c fixed it. M4a's effect-matched controls selected weakly affected genomes and were set
  aside.
- **Count before claiming.** Results drafts were corrected for counts and wording in every round (for example M4a's
  "most" of the loss, which was 54% and 58%).
- **Watch background waiters.** One review answer was missed for 8.5 hours by a detached waiter (D364).

## What comes next

The owner chose, on 2026-10-25, in this order:
1. this write-up;
2. a planned study of what a dense block carries (in the owner's words, "its size, weights and degrees"), which the
   M4d contrasts favour;
3. an M5 test of N2's exact wiring, after working out how many hosts it would need for effects above the margin,
   with the unresolved genomes and base rates planned in advance.

All on the CPU unless the owner gives the GPU.

## Who did what

- **The owner:** the question, the brainstorm's format, three of its ideas (a ring of states became M2's question;
  loops became M4's wiring question; transplanting became M4d and M5), and every choice of direction (M4d's
  confirmation with both reviewers, this write-up and its order).
- **Astra 6:** the decomposition of the registered measure that produced M1's correction; the persistence-alignment
  split; the separation of write, hold and read; independent reruns of M4d's checks and reading; the null-boundary
  correction to M4d's power argument; in M4a-M4d, provenance and reporting catches.
- **Fable 5.1:** the core defined without the result (M3) and the core dissection that pointed at RIA; the amplitude
  objection that became D1; M4d's not-settled pattern and the "resolution cannot change the decision" argument; in
  M4b-M4d, the weight-matching and comparison catches.
- **Claude:** ran the brainstorm, wrote every plan, the code and tests, ran every step, and wrote the results files
  and this synthesis; DECISIONS.md records what each review caught in each.

## Where the numbers come from

[`summary.json`](summary.json) (written by [`scripts/memory_summary.py`](../../scripts/memory_summary.py) from
`runs/memory-m1/`, `runs/memory-m2/`, `runs/memory-m2-census/`, `runs/memory-m4a/` to `runs/memory-m4d/`) holds the
compute, readings and headline numbers above. Everything else is quoted from the step's results file named beside it.
