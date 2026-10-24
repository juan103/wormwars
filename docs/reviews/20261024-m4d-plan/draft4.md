# M4d: does N2's head core carry the switch into other graphs? — the plan

*Draft 4, 2026-10-24, after three rounds of review (Astra 6 and Fable 5.1: both "revise" in round 1, on the design;
in round 2, on the plan and code, Fable "agree" after small fixes and Astra "revise"; in round 3 both "revise",
narrowly; all findings taken; drafts 1 to 3 and the reviews are archived in [`docs/reviews/20261024-m4d-plan/`](../reviews/20261024-m4d-plan/)). Exploratory: nothing
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
The resampling ignores the five ensembles; for a fixed two-per-ensemble design that is conservative, since a
stratified resample would remove the between-ensemble component (Fable, round 2).
**Before the run, the interval's coverage is simulated** (`m4d_read.py coverage`, `runs/memory-m4d/coverage.json`):
10 hosts whose base rates are drawn from M2's 30 reference graphs' rates, the comparator binomial at the base and T at
the base plus a per-host shift with population mean δ, 1024 genomes each, 2000 simulated screens, the target δ. The
arms are independent binomials, and, since pairing narrows the differences only if the two arms' switches covary
non-negatively (Astra, round 3), the fixed and raised-base cases are repeated with paired genomes whose switches are
as disjoint as the rates allow (the widest differences) and nested (the narrowest). Draft 2 simulated two shifts; on
both reviewers' advice (round 2) there are five: the same in every host; uniform on [0, 2δ]; **sparse**, 10δ in each
host with probability 0.1 (Astra); 2.5δ in the hosts of two of the five ensembles; and the same on a base raised by
0.01 in both arms, as a dense block might raise R's. δ is 0.004 and 0.015; δ = 0 and a sparse δ = 0.008 are added
to measure wrong readings, and one host at 0.012 or at 0.009 with nine at zero (round 3, Fable), to measure the
single-host guard. If any coverage is below 0.85, the reading uses the hull of the bootstrap interval and
the 90% Student-t interval on the ten differences (9 degrees of freedom). **Done, before any arm ran:**
- the bootstrap's coverage is 0.836 to 0.857 for the fixed, uniform and raised-base shifts, so the reading uses the
  hull, whose coverage there is 0.886 to 0.910; for the ensemble shift both are 0.99 or more;
- **for the sparse shift both fail** (0.60 to 0.65, hull 0.62 to 0.66): in about 35% of simulated screens (0.9¹⁰) no
  host responds at all, and 0.34 to 0.37 of screens then show an excluding upper bound. No ten-host design can see a
  response in one host in ten that it did not sample;
- at δ = 0 no screen's lower bound passes m, and every upper bound is below it; at δ = m the lower bound passes m in
  at most 4.5% of screens;
- the pairing changes little: with disjoint or nested switches the hull covers 0.890 to 0.898;
- **the guard** (0.01, below): with one host at 0.012 and nine at zero, the upper bound falls below m in 64% of
  screens and the guard leaves 31% of them reading "no effect"; with one host at 0.009, 89% and 68%. At δ = 0 it
  fires in 0.1% of screens. It catches a host that plainly responds, not a sparse response in general.

So the intervals are calibrated (about 0.90) when the response is spread over hosts, not when it is confined to a
minority of them, and the exclusion readings are worded and guarded for that (below). Identical host differences
(most plausibly all zero) give a zero-width interval; a "no effect" reading from them is sound at m = 0.004 (Fable).
**The margin m = 0.004** (4 genomes in 1024): a quarter of N2's excess over the reference graphs (1.72% of M4c's drawn
genomes against 0.12% of M2's reference graphs' drawn genomes).
- **"C3's block carries the switch into fresh hosts beyond rewired copies at its degrees"** if lower(D_TI) > m and
  lower(D_TR) > m.
- **"A transplant benefit; an advantage of C3's wiring of m or more over rewired copies ruled out, as a mean across
  these ten hosts (a response confined to a minority of host graphs may be missed)"** if lower(D_TI) > m and
  upper(D_TR) < m (Astra: not "a dense block"; that would also need D or R to beat I).
- **"No transplant effect of m or more, as a mean across these ten hosts (a response confined to a minority of host
  graphs may be missed)"** if upper(D_TI) < m. The two exclusions carry that limit in their own wording, so it
  appears wherever the reading is printed or saved (Astra, round 3).
- **"Unresolved"** otherwise.
- **The single-host guard** (round 2, after Astra's sparse case; its threshold lowered in round 3): an exclusion
  reading (the second or the third) is replaced by **"Unresolved (a single host responds)"** if any one host's own
  difference in the excluded contrast (p_hT − p_hR for the second, p_hT − p_hI for the third) is **0.01** or more (10
  genomes in 1024). At the reference hosts' rates (0 to 0.7%) a host's difference has a standard error of at most
  about 0.004, so 0.01 is two and a half or more of them. Draft 3's 0.02 could never fire: one responding host with
  nine at zero brings the upper bound below m only when it responds by less than about 0.013 (Fable, round 3).
- **Robust to the unresolved genomes** (Astra): each host's difference may lie anywhere between all its unresolved
  genomes counted against T (as separate states in the other arm, not in T) and all counted for it. The reading is
  recomputed on the **conservative envelope** of each contrast's interval over that box: the bootstrap percentiles
  rise with every host's difference, so their extremes are at the box's two ends; the Student-t lower bound is
  concave and its upper bound convex in the differences, so their extremes are at the box's corners, and all 2¹⁰
  corners are checked (draft 2 checked only the two ends, which Astra showed can miss a one-host assignment that
  changes the reading). The guard is applied with the largest possible host difference. If the envelope's reading
  differs from the reading, the reading is **"Unresolved (the unresolved genomes decide it)"**, and the counts are
  given. Each contrast's envelope is taken separately, so the check is conservative.

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
- *No effect:* across these ten hosts, the switch does not travel with C3's chemical block under this embedding and
  assay; N2's gap layer (T+G, secondary) and the boundary are the first suspects. It does not reject portability in
  general (Astra), nor a response confined to a minority of host graphs: one in ten hosts responding would be missed
  in about a third of screens (the simulation above).
- *Unresolved:* reported as such, with which rule made it so; no extension without a new plan.

**Power** (rough): with 1024 genomes, a host's p has a standard error of about 0.4 percentage points at 1.5%, and the
arms are paired; between-host variation is unknown (most reference graphs have no switch; the selected graphs up to
78 in 1024). If T reaches the core-frozen shuffles' rate (about 1.7%) and R stays near the reference's, D_TR is about
0.015: in the simulation a spread shift of 0.015 gives a lower bound above m in 97.6 to 100% of screens. Ten hosts
support a coarse screen: a D near m will be unresolved, and a sparse response may be missed (Astra, Fable).

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

- **Before every arm and on every reading** (`m4d.verify_run`, which `m4d_read.py` calls before it reads; draft 2's
  reader skipped it, Fable and Astra, round 2): the hosts the plan's, in order, with distinct names, seeds and
  contents, each in its seed sequence; each host regenerated from its seed and matched to its recorded content
  hash; the freshness check passed; `blocks.json` rebuilt from the code and equal to the saved one; every block arm's
  block holds 260 off-diagonal edges with N2's weight multiset and N2's 8 autapses; R's and Rr's in- and out-degrees
  and out-strengths within the block equal N2's, Rr's reciprocal pairs 75; P's positions equal N2's; outside the
  block, every arm's chemical matrix equals the host's; the sham genome equals `Genome.random`'s bit for bit; every
  arm's panel complete, its genome ids 0 to 1023, and its recorded arm-graph content hash (binding the host and the
  block) equal to the rebuilt graph's.
- **Tests** (`tests/test_memory_m4d.py`; sabotages in `scripts/memory_m4/sabotage_m4d.py`): the block replacement
  (outside entries unchanged, block as specified); R's degrees and out-strengths, no autapse or duplicate (03's chain
  allows autapses, so R has its own acceptance rule; Fable); Rr's reciprocal count; D's and P's multisets; the paired
  genomes (outside parameters identical to the intact genome's, block magnitudes, shared signs, the host's signs kept,
  the sham exact); the classification without a floor (a genome below `START_FLOOR` is classified); the reading's
  boundaries and the single-host guard; the unresolved envelope, with Astra's one-host counterexample as a regression
  test; the host bootstrap's arithmetic and the hull; the coverage simulation (the hull never covers less; a zero
  shift never reads positive; the scenarios' shifts); the freshness check, with a true positive (03mc's SH-2010000
  rebuilt hashes to a recorded content; Fable); the host list; record validation, including the arm-graph hash; the
  reader's entry point calling `verify_run` first, its panels validated against their arm graphs, and fewer than ten
  hosts refused; the paired counts (marginals kept, nested and disjoint as named). Nineteen tests pass
  (`runs/pytest-m4d.txt`). Twenty-three sabotages fail as they must (`runs/m4d-sabotage.txt`): the arm genome drawn by
  `Genome.random` on the arm's graph; the signs drawn fresh at the host's edges; the eligibility floor restored; R
  without the degree constraint; the block checks, the outside check, the sham check, the freshness check, the
  host-list check, record validation and the arm-hash check each disabled; content hashed another way; the reading
  without the margin; the single-host guard removed; genomes resampled within hosts; the hull not taken; the
  unresolved bounds ignored; the envelope from the two ends only; the companion copying the whole genome; the reader
  without `verify_run`; the reader's panels not validated; one host read; the pairing ignored.
- **Smoke** (not committed): host SH-2019000 (smoke seed; 103 edges in C3's block), 256 genomes, all seven arms, every
  check passed, the sham exact; R needed 14,402 attempts for its 5200 swaps and Rr 51,603 (reciprocal pairs: D 36,
  R 39, Rr, P and T 75). 210 to 469 s per arm (Rr slowest), about 285 s on average, so about 1140 s per 1024-genome
  panel. Rerun with draft 3's code, identical counts; draft 2's reader printed a one-host "reading" (Astra, round 3),
  and the current reader, run on the same folder, checks everything and reads nothing
  (`runs/m4d-smoke-read-log.txt`).

## Outputs and cost

`scripts/memory_m4/m4d.py` (stages `hosts`, `blocks`, `arms`, `companion`; inside `wormwars.accounting`) and
`m4d_read.py` (with `coverage`; it simulates and reads, and runs no network, so it is not counted). **The reader
refuses to read fewer than ten hosts** (a smoke is checked, not read; Astra, round 3). Outputs in `runs/memory-m4d/`: the hosts' records (names, seeds, content hashes, sampler
counts; graph arrays stay local, regenerated from seeds), `blocks.json`, one record per host and arm (each genome's
class, roots' distance, read-out difference and write measures), `companion.json`, `coverage.json`, `readings.json`.
**Cost:** 70 panels of 1024 genomes (ten hosts, seven arms) at 847 s (M2's median) to 1290 s (M4c's, with the CPU
shared; Fable) each, about 1140 s on the smoke: 16.5 to 25 hours, about 22 on the smoke's rate; plus the companion (about 3400 genomes, 0.8 to 1.2 hours) and the hosts
(minutes): **about 17 to 26 CPU hours**, benchmarked on the smoke first. Each panel is written when done, so a stopped
run resumes; **the run stops itself after 30 hours** (Astra), counted across invocations: the cap clock adds every
earlier invocation's recorded seconds from the run's compute record (`registration.CapClock`; draft 2's clock reset on
restart, Fable and Astra, round 2). What has finished by then is reported as incomplete, not read. No GPU.

## After the reading

Fixed now, so the screen is bounded (Astra):
- **Positive:** a second stage (M4e), planned and reviewed separately, screens the smaller blocks named above, each
  against a matched non-C3 block and its own rewired copies (reciprocity kept), on **new** fresh hosts; whatever
  succeeds is replicated on further fresh hosts before M5, which keeps its own independent hosts.
- **A transplant benefit, a wiring advantage ruled out:** the owner decides whether M5 tests density and degrees;
  D and R against I are given to inform it.
- **No effect** (across these ten hosts): M5 is not drafted as a transplant of C3; T+G and the boundary are reported, and the owner decides
  the thread's direction (a write-up of M1 to M4 is ready either way).
- **Unresolved:** reported; the next step is decided with both reviewers and, if it changes direction, the owner.
