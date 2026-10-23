# M4b: is the switch held where its states differ? — the plan

*Draft 1, 2026-10-23, for review by Astra 6 and Fable 5.1 (plan and code together). Exploratory: nothing here is a
pre-registration, but the arms, the controls, the outcome and the reading are fixed here before anything runs. The
second slice of step M4 of [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md), proposed in M4a's results
([`M4A-RESULTS.md`](M4A-RESULTS.md), D358). CPU only.*

## The question

M4a found that cutting C3's internal edges for 30 ticks sends 26 of N2's 28 separate-states genomes into one basin
from their roots, against 14% for equally sized external cuts; on the selected graphs, whose states lie mostly off
C3, C3's cut did no more than their own sampled cuts. That contrast is confounded with graph identity and with the
cut's size (D358). M4b asks two questions on the switch itself:
- **Q2, location against graph identity (read):** in every graph, does cutting the connections among the neurons
  where *that genome's* two stable states differ erase its switch more often than cutting as many connections
  elsewhere? If so in N2 and in the selected graphs alike, the switch is held where its states differ, whatever the
  graph.
- **Q1, the dissection of N2's core (described):** which parts of C3's internal edges, cut alone, erase N2's
  switches?

## The genomes

Every separate-states genome of M2's census (both subclasses), each started exactly at its two stored stable roots on
M2's float64 system, under the final input: N2 at seeds 7600 and 7700 (28), the 10 selected graphs (387), the 30
reference graphs (38), batch 7's core-frozen (52) and hub-frozen (7) shuffles. 512 genomes.

## The arms (fixed here)

Every cut sets the chosen chemical edges' weights to zero for ticks 1 to 30, then the intact network runs to tick 330
(M4a's Part 2). Autapses are never cut.
- **intact:** no cut; every genome must keep both roots, or the run stops (M4a's gate, enforced on restarts).
- **own (Q2):** per genome, its **30 neurons with the largest |v₁* − v₂*|** (ties by index), and the off-diagonal
  chemical edges with both ends among them, in that graph's own wiring.
- **controls (Q2):** per genome, **5 sets of as many edges** with both ends outside those 30 neurons, stratified on
  anatomical weight by M4a's rule (quintile bins of the own set's weights; `default_rng(20261111 + genome)`). M4a's
  largest sampled losses all came from its weight family, so this is the harder control. Each set's summed anatomical
  weight is recorded beside the own set's.
- **Q1, on N2's 28 genomes only:** C3's whole internal edge set (M4a's cut, again); its partition by the read-out (the
  8 read-out neurons among themselves; the read-out with the rest of C3; C3 without the read-out); and, for each of
  C3's 30 neurons, its own C3-internal edges (in and out) alone.

The cut sizes differ between genomes and graphs (the own set's edge count is whatever its 30 neurons enclose); within
a genome, the own set and its controls have the same count, which is what the reading compares.

## The outcome

Each history's end is assigned by M2's reaching rule against the genome's two stored roots (M4a's `assign`): both
kept, **erased** (both histories at one root), swapped, other root, or not reached. "Erased" is a lost history
distinction; the restored network keeps both roots (Astra, M4a results). A genome counts as erased or not; "not
reached" counts as not erased, and every outcome is reported.

## The reading (fixed here)

Per graph group: E_own, the fraction of its genomes erased by the own cut; E_ctrl, the fraction erased under the
controls (per genome, the mean over its 5 sets); **D = E_own − E_ctrl**, with a 90% interval (5th and 95th
percentiles of 2000 resamples, `default_rng(20261112)`), resampling graphs where a group has at least 5 graphs
(selected, reference) and genomes otherwise (N2, the two batch-7 arms). **The margin 0.10** is the smallest effect of
interest: ten percentage points of genomes.
- **"Location-dependent: the own-location cut erases more than equal external cuts in N2 and in the selected
  graphs"** if lower(D) > 0.10 in N2 and in the selected graphs.
- **"Not shown in the selected graphs"** if upper(D) < 0.10 in the selected graphs.
- **"Unresolved"** otherwise.
- The reference and batch-7 groups are reported the same way and not read.
- **Q1** is a description: the count erased by each dissection arm, with its edge count.

What a positive reading says: within each genome, connections among the neurons where its states differ hold the
switch more than as many weight-matched connections elsewhere, in N2 and in the selected graphs. It does not separate
"location" from "the cut hits the neurons whose state differs, so it moves the state directly": a cut among the
differing neurons perturbs the difference itself, which is part of what "held there" means.

## Checks and tests

- **Before:** the census's roots are reused as M4a's Part 2 used them (453 of 453 kept intact there); the gate holds
  here on every genome.
- **Tests** (`tests/test_memory_m4a.py`; sabotages in `scripts/memory_m4/sabotage_m4a.py`, `runs/m4a-sabotage.txt`):
  the top-difference neurons are the largest |v₁ − v₂|; the own edges lie inside them and the controls outside, as many
  and without repeats; the reading's boundaries and the contrast's arithmetic. Two sabotages (no margin; the own set
  taken where the roots differ least) fail as they must.
- **Smoke** (3 genomes per panel, 89 genomes; not read): every intact arm kept both roots; about 14 minutes for the
  whole smoke.

## Outputs and cost

[`scripts/memory_m4/m4b.py`](../../scripts/memory_m4/m4b.py) and
[`m4b_read.py`](../../scripts/memory_m4/m4b_read.py), inside `wormwars.accounting`. Outputs in `runs/memory-m4b/`:
per panel a JSON record (outcomes per arm, each genome's own neurons, edge counts and weights), `readings.json`.
**Cost:** M4a's Part 2 ran 453 genomes with 7 arms in 20 minutes; here 512 genomes with 7 arms, and N2's 28 with 34
more, so about half an hour to an hour. No GPU.
