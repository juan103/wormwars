# M4b: is the switch held where its states differ? — the plan

*Draft 2, 2026-10-23, after one round of review of plan and code together (Astra 6 and Fable 5.1, both "revise";
draft 1 and the review are archived in [`docs/reviews/20261023-m4b-plan/`](../reviews/20261023-m4b-plan/)). Exploratory: nothing here is a
pre-registration, but the arms, the controls, the outcome and the reading are fixed here before anything runs. The
second slice of step M4 of [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md), proposed in M4a's results
([`M4A-RESULTS.md`](M4A-RESULTS.md), D358). CPU only.*

## The question

M4a found that cutting C3's internal edges for 30 ticks sends 26 of N2's 28 separate-states genomes into one basin
from their roots, against 14% for equally sized external cuts; on the selected graphs, whose states lie mostly off
C3, C3's cut did no more than their own sampled cuts. That contrast is confounded with graph identity and with the
cut's size (D358). M4b asks two questions on the switch itself:
- **Q2, a targeting rule across graphs (read):** in every graph, does cutting the connections among the neurons
  where *that genome's* two stable states differ erase its switch more often than cutting as many weight-matched
  connections elsewhere, and more often than as many connections running out of those neurons? The comparison is
  within each genome, so graph identity and the cut's size are held fixed in it.
- **Q1, the dissection of N2's core (described):** which parts of C3's internal edges, cut alone, erase N2's
  switches?

## The genomes

Every separate-states genome of M2's census (both subclasses), each started exactly at its two stored stable roots on
M2's float64 system, under the final input: N2 at seeds 7600 and 7700 (28), the 10 selected graphs (387), the 30
reference graphs (38), batch 7's core-frozen (52) and hub-frozen (7) shuffles. 512 genomes.

## The arms (fixed here)

Every cut sets the chosen chemical edges' weights to zero for ticks 1 to 30, then the intact network runs to tick 330
(M4a's Part 2). Autapses are never cut.
- **intact:** no cut; every genome must keep both roots, or the run stops (M4a's gate, enforced on restarts). On N2,
  the intact and C3 arms repeat M4a's Part 2 on the same genomes, roots and float64 brain, and **must equal its
  outcomes exactly**, or the run stops (Fable).
- **own (Q2):** per genome, its **30 neurons with the largest |v₁* − v₂*|** (ties by index), and the off-diagonal
  chemical edges with both ends among them, in that graph's own wiring.
- **exterior controls (Q2):** per genome, **5 sets of as many edges** with both ends outside those 30 neurons,
  stratified on anatomical weight by M4a's rule (quintile bins of the own set's weights; `default_rng(20261111 +
  genome)`). M4a's largest sampled losses all came from its weight family. Each set's summed anatomical weight is
  recorded beside the own set's.
- **outgoing controls (Q2; Fable, round 1):** per genome, **5 sets of as many edges running out of those 30 neurons
  into the rest**, stratified the same way (`default_rng(20261111 + 100000 + genome)`). An exterior edge's presynaptic
  neuron sits at about the same value in both roots, so cutting it removes nearly the same input from both histories
  and can erase only by pushing the shared state across a boundary; an outgoing edge's presynaptic neuron differs, as
  the own cut's do, so this control shares the own cut's asymmetry. Where a genome has fewer outgoing edges than own
  edges, all of them are cut, and the count is recorded.
- **Q1, on N2's 28 genomes only:** C3's whole internal edge set (M4a's cut, again); its partition by the read-out (the
  8 read-out neurons among themselves; the read-out with the rest of C3; C3 without the read-out); and, for each of
  C3's 30 neurons, its own C3-internal edges (in and out) alone.

The cut sizes differ between genomes and graphs (the own set's edge count is whatever its 30 neurons enclose: in the
smoke about 170 on N2 and about 85 on the selected graphs); within a genome, the own set and its controls have the
same count, which is what the reading compares. **Pre-stated** (Fable): E_own and D are also reported by the own set's
edge count (terciles within each group), and a "not shown" from own sets far smaller than N2's is not evidence against
the targeting rule there. **A genome whose 30 neurons enclose no edge** has nothing to cut; it is excluded from the
reading and counted (Fable).

## The outcome

Each history's end is assigned by M2's reaching rule against the genome's two stored roots (M4a's `assign`): both
kept, **erased** (both histories at one root), swapped, other root, or not reached. "Erased" is a lost history
distinction; the restored network keeps both roots (Astra, M4a results). A genome counts as erased or not; "not
reached" counts as not erased, and every outcome is reported.

## The reading (fixed here)

Per graph group: E_own, the fraction of its genomes erased by the own cut; E_ext and E_out, the fractions erased
under the exterior and the outgoing controls (per genome, the mean over its 5 sets, so the pairing within a genome is
kept); **D_ext = E_own − E_ext** and **D_out = E_own − E_out**, each with a 90% interval (5th and 95th percentiles of
2000 resamples, `default_rng(20261112)`). Groups of at least 5 graphs (selected, reference) resample graphs; N2 and
the two batch-7 arms keep their graphs fixed and resample genomes within each, so their intervals are conditional on
those graphs (Astra: N2's two panels are one graph). **The margin 0.10** is the smallest effect of interest: ten
percentage points of genomes.
- **"Preferential erasure: cutting the edges among a genome's most-differing neurons erases its switch more often
  than as many exterior or outgoing edges, in N2 and in the selected graphs"** if lower(D_ext) > 0.10 and
  lower(D_out) > 0.10 in N2 and in the selected graphs.
- **"Not shown in the selected graphs"** if upper(D_ext) < 0.10 in the selected graphs.
- **"Unresolved"** otherwise.
- The reference and batch-7 groups are reported the same way and not read. **Per graph,** E_own, E_ext and E_out are
  reported (Astra), with each graph's own-edge median.
- **Q1** is a description: the count erased by each dissection arm, with its edge count.

**What a positive reading says, and does not** (Astra, Fable): under this targeting rule, removing the induced
subgraph of a genome's 30 most-differing neurons erases its switch more often than removing as many weight-matched
exterior or outgoing edges, aggregated over the genomes of N2 and of the selected graphs. It does not establish that
storage location, independently of the lesion's structure, explains the effect: the own set is a concentrated
subgraph with its own feedback, which the controls do not match; and a cut among the differing neurons perturbs the
difference itself. It is not a claim about every genome or every graph.

## Checks and tests

- **Before and on every restart and reading** (Astra, round 1): every expected panel present, with exactly the
  census's separate-states genome ids (a smoke's truncated record is rejected), every arm complete, the intact gate
  passed, and on N2 the match with M4a's Part 2. A smoke run (`MEMORY_M4B_MAX`) must write to another folder.
- **Tests** (`tests/test_memory_m4a.py`; sabotages in `scripts/memory_m4/sabotage_m4a.py`, `runs/m4a-sabotage.txt`):
  the top-difference neurons are the largest |v₁ − v₂|; the own edges lie inside them and the exterior controls
  outside, as many and without repeats; the reading's boundaries (including the outgoing condition), the contrast's
  arithmetic with both resampling schemes, and the exclusion of empty own sets; the validation of saved records
  (other genome ids, an incomplete arm, a failed intact arm). Three sabotages (no margin; the own set taken where the
  roots differ least; records not validated) fail as they must.
- **Smokes** (not read; outputs not committed): with draft 1's arms, 3 genomes per panel, **78 genomes** over the 29
  panels with separate-states genomes (draft 1 said 89, wrongly; Astra), in about 7 minutes; with draft 2's arms, 2
  genomes per panel. Every intact arm kept both roots.

## Outputs and cost

[`scripts/memory_m4/m4b.py`](../../scripts/memory_m4/m4b.py) and
[`m4b_read.py`](../../scripts/memory_m4/m4b_read.py), inside `wormwars.accounting`. Outputs in `runs/memory-m4b/`:
per panel a JSON record (outcomes per arm, each genome's own neurons, edge counts and weights), `readings.json`.
**Cost:** M4a's Part 2 ran 453 genomes with 7 arms in 20 minutes; here 512 genomes with 12 arms, and N2's 28 with 34
more, so about an hour. No GPU.
