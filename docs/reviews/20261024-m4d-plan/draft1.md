# M4d: does N2's head core carry the switch into other graphs? — the plan

*Draft 1, 2026-10-24, for review by Astra 6 and Fable 5.1. Exploratory: nothing here is a pre-registration, but the
hosts, the arms, the genomes, the outcome and the reading are fixed here before any arm runs. The fourth slice of step
M4 of [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md): its exploratory transplant screen. Chosen after M4c by consensus
(Claude, Astra 6, Fable 5.1; the consult is archived in [`docs/reviews/20261024-m4-next/`](../reviews/20261024-m4-next/))
on the owner's "As you prefer, but confirm with fable and astra" (2026-10-24). CPU only.*

## The question

M4a to M4c cut things. In N2, cutting C3's internal edges for 30 ticks erases most switches (M4b), and RIA's part of
them erases more than any weight-matched control family (M4c). Those are statements about **vulnerability in N2**.
The roadmap's transplant asks the converse, about **portability**: placed into graphs that rarely have the switch,
does N2's head-core wiring raise the share of genomes that have it? M5 is meant to test that with a pre-registration,
but its thresholds depend on base rates in fresh hosts that nobody has measured (Fable, Astra). M4d measures them and
screens the largest candidate, all of C3, before anything smaller.

**What is known** (from committed files):
- **Rare in the nulls:** 38 separate-states genomes among 29,315 eligible on M2's 30 reference graphs, with none on 19 of the 30
  ([`M2-CENSUS-RESULTS.md`](M2-CENSUS-RESULTS.md)). In N2 the rate is higher: 15 and 13 on M2's two panels, 141 of 8192 drawn genomes in
  M4c's fresh census ([`M4C-RESULTS.md`](M4C-RESULTS.md)).
- **A first, partial transplant has already worked:** batch 7's core-frozen shuffles had 9, 17 and 26 (M2). They kept
  an earlier 30-neuron core's internal edges (18 of its neurons are in C3), N2's gap layer, its autapses and 27% of its
  chemical edges (Fable). M4d keeps none of those: everything outside the block comes from a fresh null graph.
- **The density confound** (Fable): C3 has 260 internal chemical edges (anatomical weight 2347); on 10 of M1's
  reference graphs the same 30 neurons hold 89 to 115 (weight 469 to 667; computed while planning). Inserting C3 more than doubles
  the block's edges and multiplies its weight by 3.5 to 5, and a dense heavy recurrent block might be bistable whatever its wiring.
  So the transplant needs controls of the same density and weight, and the main contrast is against them.

## The hosts

**Ten fresh hosts, two per ensemble** (SH, SH-route, SH-class, SH-mirror, SH-recip), each built by 03's sampler
(`wormwars.exp03.samplers.build`, unchanged) from seed **03mc's seed base + 1000 + i** (i = 0, 1; for example
SH-2011000), never one of the graphs already used: the 640 03mc graphs include M2's reference and selected graphs, and
the selected ones were picked for their many switches (Fable). Before use, each host's name is checked against every
earlier experiment's graph names, and its array content against their content manifests (03mc's `content_check`);
a used name or content, or a `SamplerFailure`, moves to the next seed (i = 2, 3, …), recorded. **Hosts are the unit
of replication** (Astra): everything is reported per host, and the intervals resample hosts.

Every sampler keeps each neuron's degrees and permutes N2's weights, so a host carries N2's exact weight multiset
(checked while planning on 10 of M1's graphs: identical, mean anatomical weight 5.6525 = N2's).

## The arms (fixed here)

The **block** is C3's 30×30 chemical submatrix, diagonal included. Every arm except I removes the host's block (its
edges among C3's 30 neurons and their autapses) and puts a new block in its place; everything outside the block
(boundary edges, the exterior, the whole gap layer) stays the host's. C3's neurons keep their identities, so the
host's sensory inputs and the eight turn read-out neurons, all of which are in C3 (M3), stay where they are.

| Arm | The block | What it adds over the arm before it |
|---|---|---|
| **I**, intact host | the host's own | — |
| **D**, density | 260 edges at uniformly random off-diagonal positions, N2's 260 internal weights shuffled onto them; N2's 8 C3 autapses | N2's edge count and weights in the block |
| **R**, rewired | N2's 260 edges rewired within the block by double-edge swaps that keep every neuron's in- and out-degree within the block (no autapse created, no duplicate; 20 accepted swaps per edge), each weight moving with its edge; N2's 8 autapses | each neuron's within-block degrees and strengths |
| **P**, permuted | N2's 260 edges in place, their weights shuffled among them; N2's 8 autapses | N2's exact edges |
| **T**, transplant | N2's block exactly | N2's weight on each edge |
| **T+G** (secondary) | as T, and the host's gap junctions among C3's neurons replaced by N2's 44 | N2's gap junctions in the block |

D, R and P are drawn once per host (`default_rng(20261201 + 10·host + arm)`), recorded in `runs/memory-m4d/blocks.json`
and checked on every reading. D, R, P and T share the block's edge count, its weight multiset and its autapses, so any
difference among them is about where the edges and weights are, not how many or how heavy. I against D is the effect
of density and weight alone. The block arms add about 150 edges and about 1800 of anatomical weight to the host; that
is a property of the transplant, carried equally by its controls.

**Not in this stage** (named so they are not forgotten): smaller blocks (RIA's star, C3 without RIA, the read-out's
part), placement away from the read-out with an independent observation of the state, size- and weight-matched
non-C3 N2 blocks, N2's block without its autapses, and the reverse (a host block inside N2). Each needs its own
controls; they belong to a second stage, planned after this reading (below).

## The genomes: paired across arms, untouched parameters preserved

`Genome.random` scales every |w| by the graph's mean anatomical weight and draws its random numbers in edge order, so
the same seed on a changed graph gives a different brain everywhere (Astra). M4d therefore draws **one genome panel
per host, on the intact host** (1024 genomes, `Genome.random`, seed **7901 + host**, the memory thread's next unused
seeds; checked unused at implementation), and builds every arm's genome from it:
- every chemical edge outside the block keeps the host genome's signed weight; every neuron keeps its τ and bias;
  every gap junction keeps its g (in T+G, those outside the block);
- a block edge (i, j) gets |w| = `init_w_scale` × its anatomical weight / the host's mean anatomical weight (N2's,
  since the multiset is kept), clamped as `Genome.random` clamps, and the sign s_ij from one 30×30 sign matrix drawn per
  genome (`default_rng(20261211 + host)`), shared by every arm, so P and T differ only in magnitudes and an edge
  present in two arms has the same sign in both;
- T+G's block gap junctions get g = `init_g_scale` × anatomical weight / the host's mean gap weight.

Built this way with the host's own block (a sham), the genome must equal `Genome.random`'s exactly; that is a test,
and a check on every host. Under the N2 configuration Dale's law is off and magnitudes are anatomical, so nothing
else depends on the graph.

## The outcome: over every drawn genome

**Each genome is classified by M2's frozen classifier** (`pilot.probe_states`, `pilot.full_classify`, at 2000 ticks,
roots in float64), **with no eligibility floor** (Astra): the census classifies only genomes whose read-out difference
at the start of the hold passes `START_FLOOR`, and a block containing every read-out neuron could raise that
amplitude without adding a single state. M2's panels had 937 to 1010 eligible genomes of 1024, so this costs little.
- **The primary measure:** per host h and arm a, **p_ha**, the fraction of the 1024 drawn genomes classified
  **separate states** (both subclasses: the two histories end at two distinct stable roots, with or without a read-out
  difference). Unresolved genomes count as not separate states, and are reported per arm.
- **Write, hold, read** (reported, not read; Fable, Astra): per genome, at the end of the ramp, the max-norm difference
  between the two histories' states over C3's neurons and its share of the whole state difference ("written");
  separate states ("held"); the read-out-silent subclass against the other ("read"). A block that changes how much is
  written will show it here, before any claim about keeping.
- **Panel validity:** M1's rule, recorded for every arm; an arm whose panel is invalid is reported, not dropped, since
  the primary measure needs no floor. If more than 5% of an arm's genomes are unresolved, the reading names it.

## The reading (fixed here)

**D_TI** = mean over hosts of (p_hT − p_hI), **D_TR** = mean over hosts of (p_hT − p_hR), each with a 90% interval:
the 5th and 95th percentiles of 2000 resamples (`default_rng(20261221)`), each drawing the ten hosts with replacement
and, within each host, its 1024 genome indices with replacement, the same indices in every arm (the arms are paired).
**The margin m = 0.004** (4 genomes in 1024): a quarter of N2's excess over the reference graphs (1.72% of M4c's drawn
genomes against 0.12% of M2's reference graphs' drawn genomes).
- **"C3's wiring carries the switch into fresh hosts beyond its density and degrees"** if lower(D_TI) > m and
  lower(D_TR) > m.
- **"C3 carries it as a dense block; an advantage of its wiring of m or more is ruled out"** if lower(D_TI) > m and
  upper(D_TR) < m.
- **"No transplant effect of m or more"** if upper(D_TI) < m.
- **"Unresolved"** otherwise.

T against R is the primary contrast because it is M5's (roadmap: "an internally rewired copy"); T against I is
required with it, so a block that only beats a harmful control does not count. One outcome, one horizon, two contrasts
that must both pass: no second chance to declare success (Astra).

**Reported beside the reading, not read:** D_TP, D_RD, D_DI and D_(T+G)T with their intervals; every host's 1024-genome
counts per arm, and how many of the ten hosts have p_T > p_R and p_T > p_I (Fable); the same per ensemble; the
unresolved counts; the write measures by arm; the read-out-silent share; each block's in- and out-degrees,
reciprocal pairs and weight; and the companion below.

**What each reading says, and does not.**
- *Positive:* with everything outside it from a fresh null graph and its parameters random, N2's C3 block raises the
  share of genomes with two stable states beyond copies with its edge count, weights and degrees. Conditional
  sufficiency under this embedding (Astra): C3 stays on its own neurons, with the host's inputs and its own read-out.
  It does not show the block stores anything alone, nor which part matters.
- *Dense block:* density and degrees carry it; what M5 would transplant changes (a decision for the owner, since it
  changes the thread's direction).
- *No effect:* the switch does not travel with C3's chemical block under this embedding and assay; N2's gap layer
  (T+G, secondary) and the boundary are the first suspects. It does not reject portability in general (Astra).
- *Unresolved:* reported as such; no extension without a new plan.

**Power** (rough, to be checked on the smoke): with 1024 genomes, a host's p has a standard error of about 0.4
percentage points at 1.5%, and the arms are paired; between-host variation is unknown (most reference graphs have 0
switches, M2's selected graphs up to 78 in 1024). If T reaches the core-frozen shuffles' rate (about 1.7%) and R stays
near the reference's, D_TR is about 0.015, well past m; a D near m will be unresolved.

## The circuitry companion (secondary, descriptive; Fable)

T asks about anatomy with random parameters. The companion asks about **selected circuitry**: M4c's 141 N2 switch
genomes keep their C3-block chemical weights (signs included) and their C3 neurons' τ and bias, and everything else is
drawn fresh by the paired construction: (a) in N2, two fresh exteriors each (genome seeds 7931 and 7932); (b) in each
host's T graph, one fresh exterior (seed 7941 + host). Reported: the share still classified separate states, against
N2's base rate and each host's p_T. It needs M4c's local census arrays; it is skipped, and said so, if they are absent.

## Checks and tests

- **Before every arm and on every reading:** each host regenerated from its seed and matched to its recorded content
  hash; the freshness check passed; `blocks.json` rebuilt from the code and equal to the saved one; every block arm's
  block holds 260 off-diagonal edges with N2's weight multiset and N2's 8 autapses; R's in- and out-degrees within the
  block equal N2's; P's positions equal N2's; outside the block, every arm's chemical matrix equals the host's; the
  sham genome equals `Genome.random`'s; every arm's panel complete and its genome ids 0 to 1023.
- **Tests** (`tests/test_memory_m4d.py`; sabotages in `scripts/memory_m4/sabotage_m4d.py`): the block replacement
  (outside entries unchanged, block as specified); R's degrees, no autapse or duplicate; D's and P's multisets; the
  paired genomes (outside parameters identical to the host genome's, block magnitudes, shared signs, the sham exact);
  the classification without a floor (a genome below `START_FLOOR` is classified); the reading's boundaries; the
  paired two-way bootstrap's arithmetic; the freshness check (a used name or content rejected); record validation.
  Sabotages that must fail: the arm genome drawn by `Genome.random` on the arm's graph; the eligibility floor
  restored; R without the degree constraint; the signs not shared; the reading without the margin; the bootstrap not
  paired; records not validated.
- **Smoke** (not read, not committed): one SH host from a smoke seed, 256 genomes, all arms, in another folder, timed,
  to benchmark the run.

## Outputs and cost

`scripts/memory_m4/m4d.py` (stages `hosts`, `blocks`, `arms`, `companion`) and `m4d_read.py`, inside
`wormwars.accounting`. Outputs in `runs/memory-m4d/`: the hosts' records (names, seeds, content hashes, sampler
counts; graph arrays stay local, regenerated from seeds), `blocks.json`, one record per host and arm (each genome's
class, roots' distance, read-out difference and write measures), `companion.json`, `readings.json`.
**Cost:** 60 panels of 1024 genomes (ten hosts, six arms) at M2's median of 847 s per panel, about 14 hours, plus the
companion (about 1700 genomes, under half an hour) and the hosts (minutes): **about 15 CPU hours**, benchmarked on the
smoke first. No GPU.

## After the reading

Fixed now, so the screen is bounded (Astra):
- **Positive:** a second stage (M4e), planned and reviewed separately, screens the smaller blocks named above, each
  against a matched non-C3 block and its own rewired copy, on **new** fresh hosts; whatever succeeds is replicated on
  further fresh hosts before M5, which keeps its own independent hosts.
- **Dense block:** M5's structure becomes density and degrees; the owner decides whether to go on.
- **No effect:** M5 is not drafted as a transplant of C3; T+G and the boundary are reported, and the owner decides
  the thread's direction (a write-up of M1 to M4 is ready either way).
- **Unresolved:** reported; the next step is decided with both reviewers and, if it changes direction, the owner.
