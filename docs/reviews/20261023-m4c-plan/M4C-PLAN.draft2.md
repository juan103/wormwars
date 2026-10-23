# M4c: is RIA's part of the switch more than its weight? — the plan

*Draft 2, 2026-10-23, after review round 1 (Astra 6 and Fable 5.1, both "revise", every finding taken; draft 1 and
the reviews are archived in [`docs/reviews/20261023-m4c-plan/`](../reviews/20261023-m4c-plan/)). Exploratory: nothing
here is a pre-registration, but the genomes, the arms, the controls, the outcome and the reading are fixed here before
any arm runs. The third slice of step M4 of [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md), proposed in M4b's results
([`M4B-RESULTS.md`](M4B-RESULTS.md), D360) and started on the owner's word ("Go", 2026-10-23). CPU only.*

**Disclosed (Fable, round 1):** the classification of the fresh panels (the stage `census`, below) was started during
review round 1, to save time. It cuts nothing and computes no arm; its only output used later is which genomes are
separate states and their roots, which no control or reading depends on. No arm runs before the plan is agreed.

## The question

In M4b's dissection of N2's head core C3, cutting only RIAR's 26 or only RIAL's 29 C3-internal chemical edges for 30
ticks sent 20 and 17 of N2's 28 separate-states genomes into one basin from their roots; 14 of C3's 30 neurons, cut
alone the same way, sent none. That ranking was found after the data, on the same 28 genomes, and no control matched
it. M4c asks, on **fresh** N2 genomes, whether each RIA side's C3-internal edges erase the switch more often than
**edge sets of the same anatomical weight**, chosen by three fixed sampling schemes. The answer is about those
schemes; it is not an unrestricted test of "explained by weight" (Astra).

**Why weight is the first thing to rule out** (computed while planning, from the connectome and M4b's committed
dissection; not a result): RIA's C3-internal edges are the heaviest of any C3 neuron's. Their summed anatomical weight
is 560 (RIAR) and 503 (RIAL), against 26 to 217 for the other 28 neurons. |w| is proportional to the anatomical
weight in every genome (`Genome.random`; the sign is random per edge). Across the 30 neurons, the summed weight and
the dissection's erasures correlate (Spearman 0.50; 0.38 without the two RIAs), but the neurons' edge sets overlap:
each C3 edge belongs to two neurons' sets, and RIA's edges sit inside the SMD and RMD sets that rank next, so the
correlation partly restates RIA (Fable). Inside C3, the non-RIA edges hold only 4 edges of anatomical weight 40 or
more. Draft 1 concluded that a same-count, same-weight core set would be nearly the same set every time; Astra showed
that count and total weight can both be matched by many sets, so draft 2 adds that family (C), while the distribution
of weights still cannot be matched (below).

## The genomes

**Eight fresh N2 panels** of 1024 genomes, seeds **7801 to 7808** (not used before: the memory thread used 7001, 7100,
7300, 7500, 7600, 7602 and 7700; Fable found 7801 to 7812 nowhere else in the repository). Each panel is classified by
M2's census code unchanged (`census.run_panel`: probe, eligibility, the frozen classifier, the float64 roots), written
to `runs/memory-m4c/census/`. The census's check C1 compares a panel with M1's arrays, which do not exist for fresh
seeds; it is skipped (the census module is patched only inside that call and restored, tested), and nothing else
changes. **A cached census record is used only if** it names N2, its seed, the role "fresh" and the panel size, and its
arrays align with its eligible genomes (Astra). **An invalid panel** (M1's validity rule, recorded by the census) is
dropped and counted, as M2 dropped invalid panels (Fable). The genomes used are every **separate-states** genome (both
subclasses) of the valid panels, each started exactly at its two stored roots. M2's two N2 panels gave 28 of 2048, so
about 110 are expected. **If the eight panels give fewer than 60**, four more (seeds 7809 to 7812) are classified,
once, and all are used; 60 triggers the extra panels, it does not guarantee a final count (Astra).

## The arms (fixed here)

As in M4a's Part 2 and M4b: every cut sets the chosen chemical edges' weights to zero for ticks 1 to 30, then the
intact network runs to tick 330; autapses are never cut; each history's end is assigned by M2's reaching rule
against the genome's two stored roots (`m4a.assign`, through `m4b.outcomes`). The edge sets are N2's, the same for
every genome, and are built once, recorded in `runs/memory-m4c/sets.json` and checked on every reading. 165 arms.

- **intact:** no cut; every genome must keep both roots, or the run stops (M4a's gate).
- **RIAR, RIAL (read):** each side's C3-internal off-diagonal chemical edges, in and out (26 and 29 edges; anatomical
  weight 560 and 503), as in M4b's dissection. The dissection arms "C3:RIAR" and "C3:RIAL" cut the same edges; their
  outcomes must be identical, or the reading stops (Fable).
- **X, exterior, count and weight matched (read):** per side, **20 sets of as many edges, both ends outside C3**, each
  edge drawn near one of the side's edges in anatomical weight (uniformly among the unused exterior edges within
  max(1, 25%) of that weight, else the nearest), the side's edges taken in random order, and a set kept only if its
  summed weight is **within 2%** of the side's (otherwise redrawn, up to 2000 times). `default_rng(20261121)` for
  RIAR, `20261122` for RIAL. Built: summed weight 0.980 to 1.020 of the side's (mean 0.993). At 5%, drafted first, the
  sets came out about 3% lighter on average; 2% removes most of that. This replaces M4a's and M4b's stratification,
  which fell back to lighter edges where heavy ones ran short.
- **W, core, weight matched with more edges (read):** per side, **20 sets of C3-internal edges that touch neither RIAL
  nor RIAR, with the same summed weight (within 2%) and as many edges as that takes**: a random permutation of those
  207 edges, each edge added if the sum stays at most 1.02 times the side's weight, stopping once it reaches 0.98
  times. `default_rng(20261123)` for RIAR, `20261124` for RIAL. Built: 67 to 99 edges. Draft 1 called this control
  conservative; that does not follow (Astra): in a signed recurrent network more edges at the same total weight are a
  different perturbation, not a larger one, and these sets' summed squared weights are only 0.47 (RIAR) and 0.53
  (RIAL) of the side's.
- **C, core, count and weight matched (read; Astra, Fable):** per side, **20 sets of exactly as many C3-internal edges
  touching neither RIA, with the same summed weight (within 2%)**, from a swap chain uniform over all such sets: start
  from the n heaviest (ties by index), swap a member for a non-member while that brings the sum closer, until within
  2%; then propose uniform swaps, accepted whenever the sum stays within 2% (a symmetric proposal, so the chain is
  uniform over the feasible sets); after 20 000 steps, a set every 5000 steps. `default_rng(20261127)` for RIAR,
  `20261128` for RIAL. Built: summed weight 0.980 to 1.018; but the weight distribution is not matched: the sets'
  summed squared weights are 0.76 (RIAR) and 0.90 (RIAL) of the side's, and the sets overlap (0.63 and 0.39 of their
  edges in common, on average, since few heavy edges remain).
- **Recorded for every family** (`sets.json`, `readings.json`): each set's summed weight, the ratio of summed squared
  weights, the heaviest edge, the edge count, and the family's mean pairwise overlap. X's squared ratios are 0.93 to
  1.11.
- **Descriptive arms (not read):**
  - **heaviest same-count core set:** per side, the n heaviest C3-internal edges touching neither RIA (ties by index);
    its weight is 1.07 (RIAR) and 1.27 (RIAL) times the side's;
  - **other neurons' stars:** per side, for every neuron other than RIAL and RIAR whose own edges (in and out, not
    touching RIA) admit a set drawn as for X but within 5% of the side's weight (500 tries, `default_rng(20261125 +
    neuron)`), that set. Only AVAL and AVAR qualify (AVAR for RIAR; both for RIAL); at 2% only AVAR for RIAL would;
  - **RIA's both sides together** (RIAL's and RIAR's C3-internal edges, 53 edges, weight 1002), and **each side's
    edges outside C3** (33 and 34 edges);
  - **M4b's dissection again:** all of C3, its three read-out partitions, and each of C3's 30 neurons' C3-internal
    edges alone, on the fresh genomes, with each arm's summed weight.

## The outcome

Each genome counts as **erased** (both histories at one root) or not; "not reached" counts as not erased, and every
outcome (both kept, erased, swapped, other root, not reached) is reported per arm.

## The reading (fixed here)

Per side s (RIAR, RIAL) and family f (X, W, C): **E_s**, the fraction of genomes erased by the side's cut; **E_f**,
the fraction erased under the family (per genome, the mean over its 20 sets, then the mean over genomes); **D_f = E_s −
E_f**, with a 90% interval (5th and 95th percentiles of 2000 resamples, `default_rng(20261126)`; each resample draws the
genomes with replacement and the family's 20 sets with replacement, so the interval carries both the genomes' and the
sets' variation). One graph: the intervals are conditional on N2's wiring and say nothing about other graphs. **The
margin 0.10**, as in M4a and M4b.
- **"RIA's core edges erase the switch more often than every weight-matched control family"** if, for **both** sides
  and **all three** families, lower(D_f) > 0.10.
- **"An advantage of 0.10 or more ruled out against at least one control family on each side"** if, for both sides,
  some family has upper(D_f) < 0.10; the reading names, per side, the families that did it (Astra, Fable).
- **"Unresolved"** otherwise, including one side positive and the other not.
- Reported beside the reading, not read: each family's set with the largest E and how many of the 20 sets reach E_s;
  E_s's 90% interval against M4b's 20/28 and 17/28; every descriptive arm's erased count, edge count and weight; and
  the dissection's order against its weights (Spearman, with the overlap caveat above).

**Power** (Fable): with about 110 genomes, the intervals of D will be roughly ±0.08 to ±0.10 wide, so a positive
reading needs D near 0.2 or more for both sides in every family.

**What each outcome says, and does not.**
- *Positive:* on fresh N2 genomes, removing one RIA's C3-internal connections for 30 ticks erases the switch more often
  than removing as much anatomical weight under each of the three schemes: as many exterior edges of matched weights,
  more core edges, or as many core edges of the same total. It does not show that RIA stores the switch: a cut of
  every C3 connection of one neuron also silences that neuron's part in the core's feedback, which no scattered control
  matches; RIA's weight is more concentrated than C's (squared ratio 0.76 and 0.90); and only two other neurons' stars
  can match RIA's weight at all (AVAL and AVAR, described, not read). It is about N2 alone.
- *An advantage ruled out:* against the named family, RIA's edges do not erase 0.10 or more beyond what that scheme's
  sets do. It does not establish equivalence, nor that weight explains RIA's prominence (Astra): the difference may be
  strongly negative, and the two sides may be ruled out by different families. Against W alone it may also mean that
  cutting a third of the non-RIA core erases as often, which is coverage rather than weight (Fable); against C it says
  that same-count, same-total core sets erase as often, with less concentrated weight.

## Checks and tests

- **Before and on every restart and reading:** every expected panel present; its census record checked as above; its
  genome ids exactly the valid fresh census's separate-states genomes; every arm complete, no unexpected arm; the
  side arms equal to their dissection arms; the intact gate passed; `sets.json` rebuilt from the code and compared
  with the saved one; every X set of the side's count, outside C3, without repeats and within 2% of its weight; every W
  set inside C3, without repeats and within 2%; every C set of the side's count, inside C3, without repeats and within
  2%; every star of the side's count, of its neuron's edges and within 5%; no control touching RIAL or RIAR. A smoke
  run (`MEMORY_M4C_SMOKE`) uses seed 7899 and 256-genome panels, and must write to another folder.
- **Tests** (`tests/test_memory_m4a.py`; sabotages in `scripts/memory_m4/sabotage_m4a.py`, `runs/m4a-sabotage.txt`):
  the matched draws (count, pool, no repeats, weight within the tolerance, the per-edge closeness); the weight fill
  (pool, no repeats, within the tolerance); the sides equal M4b's dissection arms; no control holds an RIA edge
  (checked independently of the code's rule); a set breaking a rule is rejected; the reading's boundaries; the two-way
  bootstrap's arithmetic; the validation of records (including a side arm differing from its dissection arm); cached
  census records (another graph, seed, role or size, misaligned arrays, an invalid panel); the extra-panel rule; the
  census patched only inside `classify` and restored on failure; a changed `sets.json` rejected. Eight sabotages (the
  weight tolerance removed; RIA's edges allowed in the controls; the reading without the margin; the sets not
  resampled; records not validated; census records not checked; the census left patched; C's count not matched) fail
  as they must.
- **Smoke** (draft 1's arms; not read, not committed): seed 7899, 256 genomes, 4 separate-states genomes, every check
  passed, 125 arms in 229 s.

## Outputs and cost

[`scripts/memory_m4/m4c.py`](../../scripts/memory_m4/m4c.py) (stages `census`, `sets`, `arms`) and
[`m4c_read.py`](../../scripts/memory_m4/m4c_read.py), inside `wormwars.accounting`. Outputs in `runs/memory-m4c/`:
the census records of the fresh panels (JSON committed, arrays local), `sets.json`, one record per panel (outcomes per
arm), `readings.json`. **Cost:** about 16 minutes per census panel, so about 2.2 hours for eight; then 165 arms on
about 110 genomes, at M4b's 0.35 s per genome-arm about 1.8 hours. About 4 CPU hours. No GPU.
