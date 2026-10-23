# M4c: is RIA's part of the switch more than its weight? — the plan

*Draft 1, 2026-10-23, before review. Exploratory: nothing here is a pre-registration, but the genomes, the arms, the
controls, the outcome and the reading are fixed here before anything runs. The third slice of step M4 of
[`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md), proposed in M4b's results ([`M4B-RESULTS.md`](M4B-RESULTS.md), D360) and
started on the owner's word ("Go", 2026-10-23). CPU only.*

## The question

In M4b's dissection of N2's head core C3, cutting only RIAR's 26 or only RIAL's 29 C3-internal chemical edges for 30
ticks sent 20 and 17 of N2's 28 separate-states genomes into one basin from their roots; 14 of C3's 30 neurons, cut
alone the same way, sent none. That ranking was found after the data, on the same 28 genomes, and no control matched
it. M4c asks, on **fresh** N2 genomes, whether each RIA side's C3-internal edges erase the switch more often than
**edge sets of the same anatomical weight** elsewhere.

**Why weight is the first thing to rule out** (computed while planning, from the connectome and M4b's committed
dissection; not a result): RIA's C3-internal edges are the heaviest of any C3 neuron's. Their summed anatomical weight
is 560 (RIAR) and 503 (RIAL), against 26 to 217 for the other 28 neurons. |w| is proportional to the anatomical
weight in every genome (`Genome.random`; the sign is random per edge). Across the 30 neurons, the summed weight and
the dissection's erasures correlate (Spearman 0.50; 0.38 without the two RIAs). Inside C3 no equal-count set of other
edges reaches RIA's weight with a similar weight distribution: the non-RIA C3 edges hold only 4 edges of anatomical
weight 40 or more, and the 26 heaviest of them sum to 597, so a same-count, same-weight set would be nearly the same
set every time. The core control below therefore matches the weight with more edges.

## The genomes

**Eight fresh N2 panels** of 1024 genomes, seeds **7801 to 7808** (not used before: the memory thread used 7001, 7100,
7300, 7500, 7600, 7602 and 7700). Each panel is classified by M2's census code unchanged (`census.run_panel`: probe,
eligibility, the frozen classifier, the float64 roots), written to `runs/memory-m4c/census/`. The census's check C1
compares a panel with M1's arrays, which do not exist for fresh seeds; it is skipped, and nothing else changes. The
genomes used are every **separate-states** genome (both subclasses), each started exactly at its two stored roots.
M2's two N2 panels gave 28 of 2048, so about 110 are expected. **If the eight panels give fewer than 60**, four more
(seeds 7809 to 7812) are classified, once, and all are used.

## The arms (fixed here)

As in M4a's Part 2 and M4b: every cut sets the chosen chemical edges' weights to zero for ticks 1 to 30, then the
intact network runs to tick 330; autapses are never cut; each history's end is assigned by M2's reaching rule
against the genome's two stored roots (`m4a.assign`, through `m4b.outcomes`). The edge sets are N2's, the same for
every genome, and are built once, recorded in `runs/memory-m4c/sets.json` and checked on every reading.

- **intact:** no cut; every genome must keep both roots, or the run stops (M4a's gate).
- **RIAR, RIAL (read):** each side's C3-internal off-diagonal chemical edges, in and out (26 and 29 edges; anatomical
  weight 560 and 503), as in M4b's dissection.
- **X, exterior weight-matched (read):** per side, **20 sets of as many edges, both ends outside C3**, each edge drawn
  near one of the side's edges in anatomical weight (uniformly among the unused exterior edges within max(1, 25%) of
  that weight, else the nearest), the side's edges taken in random order, and a set kept only if its summed weight is
  **within 2%** of the side's (otherwise redrawn, up to 2000 times; built while planning: 0.980 to 1.020, mean 0.993).
  At 5%, drafted first, the sets came out about 3% lighter on average, since a weight window holds more lighter
  edges; 2% removes most of that. `default_rng(20261121)` for RIAR, `20261122` for
  RIAL. This replaces M4a's and M4b's stratification, which fell back to lighter edges where heavy ones ran short (the
  shortfall M4b's review found).
- **W, core weight-matched (read):** per side, **20 sets of C3-internal edges that touch neither RIAL nor RIAR, with
  the same summed weight (within 2%) and as many edges as that takes**: a random permutation of those 207 edges, each
  edge added if the sum stays at most 1.02 times the side's weight, stopping once it reaches 0.98 times.
  `default_rng(20261123)` for RIAR, `20261124` for RIAL. These sets hold more edges than the side (67 to 99),
  which favours the control: a cut of more connections at the same weight can only make RIA's edges look less
  special.
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

Per side s (RIAR, RIAL): **E_s**, the fraction of genomes erased by the side's cut; **E_X** and **E_W**, the fraction
erased under X and W (per genome, the mean over its family's 20 sets, then the mean over genomes); **D_X = E_s − E_X**
and **D_W = E_s − E_W**, each with a 90% interval (5th and 95th percentiles of 2000 resamples, `default_rng(20261126)`;
each resample draws the genomes with replacement and the family's 20 sets with replacement, so the interval carries
both the genomes' and the sets' variation). One graph: the intervals are conditional on N2's wiring and say nothing
about other graphs. **The margin 0.10**, as in M4a and M4b.
- **"RIA's core edges erase the switch more often than as much weight elsewhere"** if, for **both** sides,
  lower(D_X) > 0.10 and lower(D_W) > 0.10.
- **"Matched by weight"** if, for **both** sides, upper(D_X) < 0.10 or upper(D_W) < 0.10.
- **"Unresolved"** otherwise, including one side positive and the other not.
- Reported beside the reading, not read: each family's set with the largest E and how many of the 20 sets reach E_s;
  E_s's 90% interval against M4b's 20/28 and 17/28; every descriptive arm's erased count, edge count and weight; and
  the dissection's order against its weights (Spearman, as above).

**What a positive reading says, and does not:** on fresh N2 genomes, removing one RIA's C3-internal connections for
30 ticks sends a separate-states genome's two histories into one basin more often than removing as much anatomical
weight at matched count outside C3, or spread over more connections inside it. It does not show that RIA stores the
switch: a cut of every C3 connection of one neuron also silences that neuron's part in the core's feedback, which no
scattered control matches, and only two other neurons' stars can match RIA's weight at all (AVAL and AVAR, described,
not read). It is about N2 alone. **A "matched by weight" reading** says RIA's prominence in the dissection is what its
edges' weight predicts, at the precision here.

## Checks and tests

- **Before and on every restart and reading:** every expected panel present, its genome ids exactly the fresh
  census's separate-states genomes, every arm complete, the intact gate passed; `sets.json` rebuilt from the code and
  compared with the saved one; every X set of the side's count, outside C3, without repeats and within 2% of its
  weight; every W set inside C3, touching neither RIA, without repeats and within 2%; every star of the side's count,
  of its neuron's edges and within 5%; no control touching RIAL or RIAR. A smoke run (`MEMORY_M4C_SMOKE`) uses seed 7899 and 256-genome panels, and must write to another folder.
- **Tests** (`tests/test_memory_m4a.py`; sabotages in `scripts/memory_m4/sabotage_m4a.py`): the matched draws (count,
  pool, no repeats, weight within the tolerance, the per-edge closeness); the W draws (inside C3, no RIA, weight within
  the tolerance); the side sets equal M4b's dissection arms; the reading's boundaries; the two-way bootstrap's
  arithmetic; the validation of records and of `sets.json`. Sabotages: the weight tolerance removed; RIA's own edges
  allowed in the controls; the reading without the margin; the sets not resampled in the bootstrap; records not
  validated.

## Outputs and cost

[`scripts/memory_m4/m4c.py`](../../scripts/memory_m4/m4c.py) (stages `census`, `sets`, `arms`) and
[`m4c_read.py`](../../scripts/memory_m4/m4c_read.py), inside `wormwars.accounting`. Outputs in `runs/memory-m4c/`:
the census records of the fresh panels (JSON committed, arrays local), `sets.json`, one record per panel (outcomes per
arm), `readings.json`. **Cost:** an N2 census panel took 16 minutes, so about 2.2 hours for eight; then about 125
arms on about 110 genomes, at M4b's 0.35 s per genome-arm about 80 minutes. About 3.5 CPU hours. No GPU.
