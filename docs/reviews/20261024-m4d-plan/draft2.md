# M4d: does N2's head core carry the switch into other graphs? — the plan

*Draft 2, 2026-10-24, after review round 1 (Astra 6 and Fable 5.1, both "revise", all findings taken; draft 1 and
the review are archived in [`docs/reviews/20261024-m4d-plan/`](../reviews/20261024-m4d-plan/)). Exploratory: nothing
here is a pre-registration, but the hosts, the arms, the genomes, the outcome and the reading are fixed here before
any arm runs. The fourth slice of step M4 of [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md): its exploratory transplant
screen. Chosen after M4c by consensus (Claude, Astra 6, Fable 5.1; the consult is archived in
[`docs/reviews/20261024-m4-next/`](../reviews/20261024-m4-next/)) on the owner's "As you prefer, but confirm with fable
and astra" (2026-10-24). CPU only.*

## The question

M4a to M4c cut things. In N2, cutting C3's internal edges for 30 ticks erases most switches (M4b), and RIA's part of
them erases more than any weight-matched control family (M4c). Those are statements about **vulnerability in N2**.
The roadmap's transplant asks the converse, about **portability**: placed into graphs that rarely have the switch,
does N2's head-core wiring raise the share of genomes that have it? M5 is meant to test that with a pre-registration,
but its thresholds depend on base rates in fresh hosts that nobody has measured (Fable, Astra). M4d measures them and
screens the largest candidate, all of C3, before anything smaller.

**What is known** (from committed files):
- **Rare in the nulls:** 38 separate-states genomes among 29,315 eligible on M2's 30 reference graphs, with none on
  19 of the 30; the 10 selected graphs, picked for their many switches, had 12 to 78 each
  ([`M2-CENSUS-RESULTS.md`](M2-CENSUS-RESULTS.md)). In N2: 15 and 13 on M2's two panels, 141 of 8192 drawn genomes in
  M4c's fresh census ([`M4C-RESULTS.md`](M4C-RESULTS.md)).
- **A first, partial transplant has already worked:** batch 7's core-frozen shuffles had 9, 17 and 26 (M2). They kept
  an earlier 30-neuron core's internal edges (18 of its neurons are in C3), N2's gap layer, its autapses and 27% of its
  chemical edges (Fable). M4d keeps none of those: everything outside the block comes from a fresh null graph.
- **The density confound** (Fable): C3 has 260 internal chemical edges (anatomical weight 2347); on 10 of M1's
  reference graphs the same 30 neurons hold 89 to 115 (weight 469 to 667; computed while planning, and checked by
  Astra). Inserting C3 more than doubles the block's edges and multiplies its weight by 3.5 to 5, and a dense heavy
  recurrent block might be bistable whatever its wiring. So the transplant needs controls of the same size and weight,
  and the main contrast is against them.
- **Reciprocity** (Fable): C3's block has 75 reciprocal pairs; 260 edges placed at random among its 870 ordered pairs
  give about 39.

## The hosts

**Ten fresh hosts, two per ensemble** (SH, SH-route, SH-class, SH-mirror, SH-recip), each built by 03's sampler
(`wormwars.exp03.samplers.build`, unchanged) from seed **03mc's seed base + 1000 + i** (i = 0, 1; for example
SH-2011000), never one of the graphs already used: the 640 03mc graphs (offsets 0 to 127) include M2's reference and
selected graphs. Before use, each host's name is checked against every earlier experiment's graph names, and its
array content against their content manifests (every committed `ensembles.json` and
`graphs_content_manifest.json`: 03's, 03r's and 03mc's; 03a's and 03h's graphs used seeds above 3,400,000); a used
name or content, or a `SamplerFailure`, moves that host to the seed two further on (i + 2, i + 4, …), recorded. **Hosts are the unit of replication** (Astra):
everything is reported per host, and the intervals resample hosts.

Every sampler keeps each neuron's degrees and permutes N2's weights (the route cap swaps weights), so a host carries
N2's exact chemical weight multiset (checked while planning on 10 of M1's graphs, and by Fable in the code).

## The arms (fixed here)

The **block** is C3's 30×30 chemical submatrix, diagonal included. Every arm except I removes the host's block (its
edges among C3's 30 neurons and their autapses) and puts a new block in its place; everything outside the block
(boundary edges, the exterior, the whole gap layer) stays the host's. C3's neurons keep their identities, so the
host's sensory inputs and the eight turn read-out neurons, all of which are in C3 (M3), stay where they are.

| Arm | The block | What it keeps of N2's block |
|---|---|---|
| **I**, intact host | the host's own | — |
| **D**, density | 260 edges at uniformly random off-diagonal positions, N2's 260 internal weights shuffled onto them | the edge count, the weight multiset, the autapses |
| **R**, rewired | N2's 260 edges rewired by double-edge target swaps ((a,b),(c,d) → (a,d),(c,b)) within the block, no autapse or duplicate created, 20 accepted swaps per edge; each weight moves with its source, so out-strengths are kept and in-strengths are not | as D, and every neuron's in- and out-degree within the block, and its out-strength |
| **Rr**, rewired, reciprocity kept (secondary; Fable) | as R, a swap accepted only if the block's reciprocal-pair count stays at 75 (SH-recip's rule) | as R, and the 75 reciprocal pairs |
| **P**, permuted | N2's 260 edges in place, their weights shuffled among them | the exact edges (so degrees and reciprocal pairs), not the strengths |
| **T**, transplant | N2's block exactly | everything |
| **T+G** (secondary) | as T, and the host's gap junctions among C3's neurons replaced by N2's 44 | everything, and the block's gap junctions |

Every block arm also carries N2's 8 C3 autapses in place of the host's (1 to 6 on M1's graphs). D, R, Rr and P are
drawn once per host (`default_rng(20261201 + 10·host + arm)`), recorded in `runs/memory-m4d/blocks.json` and checked
on every reading. D, R, Rr, P and T share the block's edge count, weight multiset and autapses, so any difference
among them is about where the edges and weights are, not how many or how heavy. **The ladder is not a chain of single
additions** (Astra): I against D changes the count, the weight, the topology and the autapses together, and R and P
keep different things (R the out-strengths, P the exact edges). Each contrast is read for what its two arms keep, as
in the table. The block arms add about 150 edges and about 1800 of anatomical weight to the host; that is a property
of the transplant, carried equally by its controls.

**Not in this stage** (named so they are not forgotten): smaller blocks (RIA's star, C3 without RIA, the read-out's
part), placement away from the read-out with an independent observation of the state, size- and weight-matched
non-C3 N2 blocks, N2's block without its autapses, and the reverse (a host block inside N2). Each needs its own
controls; they belong to a second stage, planned after this reading (below).

## The genomes: paired across arms, untouched parameters preserved

`Genome.random` scales every |w| by the graph's mean anatomical weight and draws its random numbers in edge order, so
the same seed on a changed graph gives a different brain everywhere (Astra). M4d therefore draws **one genome panel
per host, on the intact host** (1024 genomes, `Genome.random`, seed **7901 + host**; Fable found the 79xx seeds unused
in the repository), and builds every arm's genome from it:
- every chemical edge outside the block keeps the intact genome's signed weight; every neuron keeps its τ and bias;
  every gap junction keeps its g (in T+G, those outside the block);
- a block edge (i, j) gets |w| = `init_w_scale` × its anatomical weight / the intact spec's float32
  `chem_anat.mean()` (the same tensor arithmetic as `Genome.random`; that mean equals N2's, since the multiset is
  kept), clamped as `Genome.random` clamps (no N2 weight reaches the clamp);
- its sign s_ij comes from one 30×30 sign matrix per genome, shared by every arm: **the intact genome's sign wherever
  the host has a block edge (i, j)**, and a fresh draw elsewhere (`default_rng(20261211 + host)`) (Astra, Fable). So
  an edge present in two arms, or in the host and an arm, has the same sign in both, and P and T differ only in
  magnitudes;
- T+G's block gap junctions get g = `init_g_scale` × anatomical weight / the intact spec's float32 `gap_anat.mean()`.

Built this way with the host's own block (the sham), the genome must equal `Genome.random`'s bit for bit; that is a
test, and a check on every host. Under the N2 configuration Dale's law is off and magnitudes are anatomical
(`_apply_magnitude_mode` returns them untouched), so nothing else depends on the graph.

## The outcome: over every drawn genome

**Each genome is classified by M2's frozen classifier** (`pilot.probe_states`, `pilot.full_classify`, at 2000 ticks,
roots in float64), **with no eligibility floor** (Astra): the census classifies only genomes whose read-out difference
at the start of the hold passes `START_FLOOR`, and a block containing every read-out neuron could raise that
amplitude without adding a single state. M2's panels had 937 to 1010 eligible genomes of 1024, so this costs little.
- **The primary measure:** per host h and arm a, **p_ha**, the fraction of the 1024 drawn genomes classified
  **separate states** (both subclasses: the two histories end at two distinct stable roots, with or without a read-out
  difference). Unresolved genomes count as not separate states, are reported per arm, and bound the reading (below).
- **Write, hold, read** (reported, not read; Fable, Astra), per genome:
  - *written:* at the end of the ramp, the squared norm of the two histories' state difference, and the fraction of
    it on C3's neurons (undefined when the difference is zero; those genomes are counted);
  - *held:* separate states;
  - *read:* the absolute read-out difference between the two roots, |c′(tanh r₁ − tanh r₀)|, by arm; and the
    read-out-silent share among genomes at or above `START_FLOOR` only, since the subclass rule compares with 0.1·a and
    says little when a is near zero (Astra, Fable).

  The write amplitude is a diagnostic: it does not isolate keeping from writing.
- **Panel validity:** M1's rule, recorded for every arm; an invalid panel is reported, not dropped, since the primary
  measure needs no floor.

## The reading (fixed here)

**D_TI** = mean over the ten hosts of (p_hT − p_hI), **D_TR** = mean over hosts of (p_hT − p_hR), each with a 90%
interval: the 5th and 95th percentiles of 2000 resamples (`default_rng(20261221)`) of **the ten hosts with
replacement**, each resample averaging its hosts' paired differences. Genomes are not resampled again: each host's
difference already carries its genomes' variation, and resampling them as well would count it twice (Astra, Fable).
The resampling ignores the five ensembles; that is conservative for a fixed two-per-ensemble design, since it adds
the between-ensemble variation (a stratified resample of two hosts per stratum would halve the variance instead).
**Before the run, the interval's coverage is simulated** (`m4d_read.py coverage`, `runs/memory-m4d/coverage.json`):
10 hosts whose rates are drawn from M2's 30 reference graphs' rates (arm I) and the same plus a shift δ (arm T), 1024
binomial genomes each, 2000 simulated screens; δ is 0.004 or 0.015, fixed or uniform on [0, 2δ] per host, and the
target is δ. If any coverage is below 0.85, the reading uses the wider of the bootstrap interval and the 90%
Student-t interval on the ten differences (9 degrees of freedom). **Done, before any arm ran:** the bootstrap's
coverage is 0.843, 0.857, 0.852 and 0.859, so the reading uses the widened interval, whose coverage is 0.898, 0.910,
0.903 and 0.904.
**The margin m = 0.004** (4 genomes in 1024): a quarter of N2's excess over the reference graphs (1.72% of M4c's drawn
genomes against 0.12% of M2's reference graphs' drawn genomes).
- **"C3's block carries the switch into fresh hosts beyond rewired copies at its degrees"** if lower(D_TI) > m and
  lower(D_TR) > m.
- **"A transplant benefit; an advantage of C3's wiring of m or more over rewired copies ruled out"** if
  lower(D_TI) > m and upper(D_TR) < m (Astra: not "a dense block"; that would also need D or R to beat I).
- **"No transplant effect of m or more"** if upper(D_TI) < m.
- **"Unresolved"** otherwise.
- **Robust to the unresolved genomes** (Astra): each contrast is recomputed twice, with every unresolved genome
  counted as separate states in T and as not in the other arm, and the reverse. If either assignment changes the
  reading, the reading is "unresolved (the unresolved genomes decide it)", and the counts are given.

T against R is the primary contrast because it is M5's (roadmap: "an internally rewired copy"); T against I is
required with it, so a block that only beats a harmful control does not count. One outcome, one horizon, two contrasts
that must both pass: no second chance to declare success (Astra).

**Reported beside the reading, not read:** D_TRr, D_TP, D_RD, D_DI, D_RI and D_(T+G)T with their intervals; every
host's 1024-genome counts per arm, and how many of the ten hosts have p_T > p_R and p_T > p_I (Fable); the same per
ensemble; the unresolved counts; the write and read measures by arm; each block's in- and out-degrees, reciprocal
pairs and weight; and the companion below.

**What each reading says, and does not.**
- *Positive:* with everything outside it from a fresh null graph and its parameters random, N2's C3 block raises the
  share of genomes with two stable states, beyond copies with its edge count, weights, autapses, degrees and
  out-strengths. Conditional sufficiency under this embedding (Astra): C3 stays on its own neurons, with the host's
  inputs and its own read-out. R does not keep N2's 75 reciprocal pairs, so T over R is not yet "beyond its
  reciprocity"; Rr reports that, descriptively (Fable). It does not show the block stores anything alone, nor which
  part matters.
- *A transplant benefit, a wiring advantage ruled out:* the block helps, and N2's exact wiring adds less than m over
  rewired copies at its degrees. Whether density and degrees carry it needs D or R against I too; redirecting M5 to
  them is a decision for the owner, since it changes the thread's direction.
- *No effect:* the switch does not travel with C3's chemical block under this embedding and assay; N2's gap layer
  (T+G, secondary) and the boundary are the first suspects. It does not reject portability in general (Astra).
- *Unresolved:* reported as such; no extension without a new plan.

**Power** (rough): with 1024 genomes, a host's p has a standard error of about 0.4 percentage points at 1.5%, and the
arms are paired; between-host variation is unknown (most reference graphs have no switch; the selected graphs up to
78 in 1024), and neither a single-host smoke nor the simulation measures it. If T reaches the core-frozen shuffles'
rate (about 1.7%) and R stays near the reference's, D_TR is about 0.015, well past m. Ten hosts support a coarse
screen: a D near m will be unresolved, and the "ruled out" and "no effect" readings need small between-host
variation (Astra, Fable).

## The circuitry companion (secondary, descriptive; Fable, Astra)

T asks about anatomy with random parameters. The companion asks about **selected parameters**: M4c's 141 N2 switch
genomes (their ids are in the committed census records `runs/memory-m4c/census/N2__780x.json`; the genomes regenerate
from seeds 7801 to 7808) keep their C3-block chemical weights (signs included) and their C3 neurons' τ and bias, and
everything else is drawn fresh by the paired construction: (a) in N2, two fresh exteriors each (genome seeds 7931 and
7932); (b) in each host's T graph, one fresh exterior (seed 7941 + host; the fresh genome's block signs at positions the host lacks from `default_rng(20261231 + host)`).
**Its paired control** (Astra): the same fresh genomes unchanged, so their block signs and C3's τ and bias are the
fresh draw's. Reported: the
share classified separate states in each, against N2's base rate and each host's p_T. It transfers weights **and**
neuronal parameters, so a difference is about that selected set, not the circuitry alone; and reclassification shows
continued switching, not that the original roots are kept.

## Checks and tests

- **Before every arm and on every reading:** each host regenerated from its seed and matched to its recorded content
  hash; the freshness check passed; `blocks.json` rebuilt from the code and equal to the saved one; every block arm's
  block holds 260 off-diagonal edges with N2's weight multiset and N2's 8 autapses; R's and Rr's in- and out-degrees
  and out-strengths within the block equal N2's, Rr's reciprocal pairs 75; P's positions equal N2's; outside the
  block, every arm's chemical matrix equals the host's; the sham genome equals `Genome.random`'s bit for bit; every
  arm's panel complete and its genome ids 0 to 1023.
- **Tests** (`tests/test_memory_m4d.py`; sabotages in `scripts/memory_m4/sabotage_m4d.py`): the block replacement
  (outside entries unchanged, block as specified); R's degrees and out-strengths, no autapse or duplicate (03's chain
  allows autapses, so R has its own acceptance rule; Fable); Rr's reciprocal count; D's and P's multisets; the paired
  genomes (outside parameters identical to the intact genome's, block magnitudes, shared signs, the host's signs kept,
  the sham exact); the classification without a floor (a genome below `START_FLOOR` is classified); the reading's
  boundaries and the unresolved bounds; the host bootstrap's arithmetic; the coverage simulation; the freshness check
  (a used name or content rejected); record validation. Sabotages that must fail: the arm genome drawn by
  `Genome.random` on the arm's graph; the signs drawn fresh at the host's edges; the eligibility floor restored; R
  without the degree constraint; the reading without the margin; genomes resampled within hosts; records not
  validated.
  Twelve tests pass (`runs/pytest-m4d.txt`); thirteen sabotages (the seven above, and the block checks, the outside
  check, the sham check, the unresolved bounds, the freshness check and the companion's copy each disabled) fail as
  they must (`runs/m4d-sabotage.txt`).
- **Smoke** (not read, not committed): host SH-2019000 (smoke seed; 103 edges in C3's block), 256 genomes, all seven
  arms, every check passed, the sham exact; R needed 14,402 attempts for its 5200 swaps and Rr 51,603 (reciprocal
  pairs: D 36, R 39, Rr, P and T 75). 210 to 469 s per arm (Rr slowest), about 285 s on average, so about 1140 s per
  1024-genome panel.

## Outputs and cost

`scripts/memory_m4/m4d.py` (stages `hosts`, `blocks`, `arms`, `companion`) and `m4d_read.py` (with `coverage`), inside
`wormwars.accounting`. Outputs in `runs/memory-m4d/`: the hosts' records (names, seeds, content hashes, sampler
counts; graph arrays stay local, regenerated from seeds), `blocks.json`, one record per host and arm (each genome's
class, roots' distance, read-out difference and write measures), `companion.json`, `coverage.json`, `readings.json`.
**Cost:** 70 panels of 1024 genomes (ten hosts, seven arms) at 847 s (M2's median) to 1290 s (M4c's, with the CPU
shared; Fable) each, about 1140 s on the smoke: 16.5 to 25 hours, about 22 on the smoke's rate; plus the companion (about 3400 genomes, 0.8 to 1.2 hours) and the hosts
(minutes): **about 17 to 26 CPU hours**, benchmarked on the smoke first. Each panel is written when done, so a stopped
run resumes; **the run stops itself after 30 hours** of wall time (Astra), and what has finished is reported as
incomplete, not read. No GPU.

## After the reading

Fixed now, so the screen is bounded (Astra):
- **Positive:** a second stage (M4e), planned and reviewed separately, screens the smaller blocks named above, each
  against a matched non-C3 block and its own rewired copies (reciprocity kept), on **new** fresh hosts; whatever
  succeeds is replicated on further fresh hosts before M5, which keeps its own independent hosts.
- **A transplant benefit, a wiring advantage ruled out:** the owner decides whether M5 tests density and degrees;
  D and R against I are given to inform it.
- **No effect:** M5 is not drafted as a transplant of C3; T+G and the boundary are reported, and the owner decides
  the thread's direction (a write-up of M1 to M4 is ready either way).
- **Unresolved:** reported; the next step is decided with both reviewers and, if it changes direction, the owner.
