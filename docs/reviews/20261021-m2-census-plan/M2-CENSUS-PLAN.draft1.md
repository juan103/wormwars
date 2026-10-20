# M2 census: how much of N2's lead is separate states — the plan

*Draft 1, 2026-10-21, before review. Exploratory: nothing here is a pre-registration, but the estimands, the readings
and their thresholds are fixed here before anything runs. Step M2 of [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md), after
its pilot ([`M2-PILOT-PLAN.md`](M2-PILOT-PLAN.md), [`M2-PILOT-RESULTS.md`](M2-PILOT-RESULTS.md); D353, D354). CPU
only.*

## The question

03mc found that N2 keeps more of its history difference at tick 30 than its null ensembles. M1 measured that, on
03mc's arrays, the settling cohort (03mc's settled-and-remaining genomes) carries 30 to 38% of N2's mean tick-30 lead
and 66 to 68% of its tick-300 lead (A5). The roadmap's split asks what the rest is: **how much of N2's excess over
the nulls comes from genomes with separate stable states, and how much from genomes that fade to one state, more
slowly**. The pilot built a classifier that answers this per genome and checked it (every check passed). The census
applies it to every eligible genome of N2 and of M1's 30 random reference graphs, and of three further sets of
graphs that the roadmap names.

What the pilot hands the census, and how this plan takes it:
- **the classifier, frozen:** unchanged rules and thresholds (D353's `classify.py`, `equilibria.py` and the
  pilot's locating, reaching, oscillation and class functions). Two engineering changes, below, each checked for
  equivalence first;
- **the follow-up length:** 2000 ticks;
- **the cheaper "reaches" rule:** it agreed on all 934 pilot histories, but the census keeps the full rule (its cost
  is now small, below) and reports the agreement again;
- **no float64, finer integration or fixed batches:** the main run stays float32 at 32 substeps;
- **two states, not more:** the census counts separate-states genomes, not their states;
- **the locating radius:** kept at 10⁻³ for the classes; its effect is reported as a sensitivity (below).

## The sample

- **Genomes:** 1024 per graph, `Genome.random` with seed 7600, M1's draw, so M1's per-genome numbers apply to the same
  brains. N2 also gets M1's second panel, seed 7700. M1's probe, unchanged: 100 ticks of warm-up at 0.25× or 1.75×
  the final food level, a 10-tick ramp, then the follow-up at the final level, here 2000 ticks; 32 substeps,
  float32.
- **Eligible:** a_i ≥ 10⁻³ (M1), with a_i = |δy_i(0)|. Every eligible genome is classified.
- **Graphs (48 panels):**
  1. **N2,** seeds 7600 and 7700;
  2. **the reference:** M1's 30 random graphs, 6 per ensemble (`runs/memory-m1/panel.json`, `random`);
  3. **the selected graphs:** M1's 10, each ensemble's top-share and top-cohort graph from 03mc (`selected`), among
     them the high-settling null graphs the roadmap names. Reported apart, never in the reference;
  4. **batch 7's core-frozen and hub-frozen shuffles,** three of each (`scripts/memory_spikes/batch7.py`, rewiring
     seeds 700 to 702 and 800 to 802). The census regenerates them with batch 7's code, copied, and checks each against
     `runs/memory-spikes/batch7.json` (edge count, triangle counts, reciprocal pairs, accepted swaps, kept fractions);
     a mismatch stops the census for that arm. They get fresh seed-7600 panels (batch 7 used 7100 and 7400). Reported
     apart. These are spike rewirings, not 03's samplers (the roadmap, finding 5), and their core was chosen on the
     result.

## The run

- **The main run:** the probe for every genome, in chunks of 128 genomes (256 rows), the two histories as rows.
  Recorded per history: δy every tick from 0 to 2000; the full state at ticks 0, 30, 300 and 2000; 03mc's settling
  range over ticks 291-300, 1891-1900 and 1991-2000; and the range over ticks 1801-2000 per neuron (the pilot kept
  the whole tail; the classifier uses only these ranges, and the oscillation check reruns the probe for its own
  record). A non-finite state stops the run, as in M1.
- **The classification:** the pilot's `full_classify` on the eligible genomes of each graph, in chunks of 128.
- **Two engineering changes,** neither changing a rule:
  - **the continuation drops finished strains from its batch.** The pilot integrated every row until the slowest was
    done. In a spike on the pilot's 196 genomes of N2 and SH-2010013, the compacted continuation gave the same
    reaching verdict and the same stopping time for every history, 3.3 to 3.5 times faster (113.5 s against 34.3 s,
    133.2 s against 37.7 s; `scripts/memory_m2/spike_compact.py`, output `runs/memory-m2/spike_compact.txt`). A committed test repeats this comparison on a small set and also requires the distance
    windows to agree within 10⁻¹² (rule 7);
  - **the main run keeps ranges instead of the whole tail.** A test requires the same candidates and the same
    reference range as the pilot's full-tail record on a small set.
- **Order:** N2 seed 7600; the reference graphs, one per ensemble in turn; N2 seed 7700; the selected graphs; batch
  7's graphs. Each graph writes its own files and is skipped if they exist, so a stopped run resumes.

## Checks before and during the run

- **C1, reproduction of M1.** On the 42 panels M1 ran (N2's two, the 30 random, the 10 selected), the census's a_i,
  |δy_i(30)| and |δy_i(100)|, eligibility and cohort membership are compared with M1's arrays
  (`runs/memory-m1/panels/*.npz`, local), genome by genome. M1's intact run was one batch of 1024; the census runs
  chunks of 128, and T1 §3 claims no bitwise equality across compositions. So the gaps are saved and summarised, and
  the census **stops for investigation** if more than 1% of a panel's genomes differ by more than 10⁻³ in a or
  |δy(30)| (M1's own rule). Changes of eligibility or cohort membership are counted and named. The census uses its
  own arrays throughout, never M1's.
- **C2, the planted genomes.** The pilot's six (R6), classified by the census code before the census starts. Every
  one must be named exactly, or nothing runs.
- **C3, P against the integrator.** At 20 located roots drawn at random over the census
  (`default_rng(20261029)`), P³² against the automatic derivative of one float64 tick, within 10⁻⁸ (R4′).
- **C4, resolution.** Per graph, the unresolved fraction of eligible genomes and of the eligible tick-30 numerator,
  against the pilot's R2 thresholds (5% and 10%). A graph above either is named. It is not dropped: the unresolved
  genomes enter the split as a band (below).
- **The cost guard.** After N2's first panel and the first reference graph, the script projects the whole census. If
  the projection exceeds 16 hours, it stops and the plan is revisited.

## The estimands

For a graph g and tick t ∈ {30, 300}, over its eligible genomes E:
- **the eligible share** s_g(t) = Σ_E |δy_i(t)| / Σ_E a_i (M1);
- **the class contributions** X_g(t) = Σ_{i ∈ E, class X} |δy_i(t)| / Σ_E a_i, for X = S (separate states, both
  subclasses), F (fading), O (persistent oscillation) and U (unresolved). Exactly, s = S + F + O + U.

**The split,** as M1's A5 took it, from pairwise contrasts averaged over the reference R (the 30 random graphs), so
that the parts add up:
- Λ(t) = s_N2(t) − mean_R s_g(t), and Λ_X(t) = X_N2(t) − mean_R X_g(t), with Λ = Λ_S + Λ_F + Λ_O + Λ_U;
- **φ_X(t) = Λ_X(t) / Λ(t),** the part of N2's mean lead carried by class X.

**The unresolved band** (the roadmap: unresolved genomes enter "as an explicit uncertainty band, not as zero"):
- φ_S⁻ = (S_N2 − mean_R (S_g + U_g)) / Λ, every unresolved genome counted as separate states in the reference and as
  something else in N2;
- φ_S⁺ = (S_N2 + U_N2 − mean_R S_g) / Λ, the reverse.

The same is defined for F. The lead by M1's own definition (N2 minus the reference median) is reported beside Λ, and
not split, since medians do not add.

**Uncertainty:** M1's bootstrap. Graphs are resampled within ensembles. Genome indices are resampled once for all
seed-7600 panels, which share their draws index by index, and independently for N2's seed-7700 panel. 2000
resamples, 90% percentile intervals, `default_rng(20261028)`. A resample with Λ ≤ 0 is counted. If more than 100 of
the 2000 have it, the reading is inconclusive; otherwise they are dropped and their number reported.

## The readings (fixed here)

At tick 30, on each of N2's two panels, from the 90% intervals of the band's two ends:
- **"separate states carry most of N2's lead"** if the interval of φ_S⁻ lies wholly above 0.5;
- **"separate states carry little of N2's lead"** if the interval of φ_S⁺ lies wholly below 0.25. This is the
  roadmap's branch point: "settling explains little of the excess. The graded part then becomes the main target";
- **"separate states carry a part of N2's lead"** otherwise, with φ_S, the band and the intervals reported.

The two panels must give the same reading. If they do not, the reading is **"not replicated"**, with both reported.
Tick 300 is read the same way, as a description. *Beforehand:* M1's A5 puts the cohort's part at 0.30 to 0.38 at
tick 30 and 0.66 to 0.68 at tick 300, and the pilot found the cohort to consist of separate-states genomes. So the
expected reading at tick 30 is "a part" or "little", depending on how many separate-states genomes lie outside the
cohort.

## Descriptions (no readings)

- **Per graph and class:** counts, contributions at ticks 30 and 300, and φ_X per ensemble (6 graphs each).
- **Settling and share:** across the 30 reference graphs, the Spearman correlation of s(30) with S(30) and with
  s(30) − S(30), pooled and per ensemble. Six graphs per ensemble cannot test 03mc's within-ensemble association;
  this only says whether the fresh panels look the same.
- **The core-frozen and hub-frozen shuffles:** S(30), F(30), s(30) and the number of separate-states genomes per
  graph, against N2 and the reference. And **where the states differ:** for each separate-states genome, the fraction
  of ‖v₁* − v₂*‖² (the two roots' difference) on batch 7's 30 core neurons and on the 8 read-out neurons, averaged
  per graph with weights |δy(30)|. This answers the roadmap's "do the core-frozen graphs keep N2's settling and its
  location, and do the hub-frozen graphs lose it?" descriptively, with three graphs per arm.
- **Graded fading:** for each fading genome, the slowest discrete rate of P³² at its common root (the log of its
  largest eigenvalue modulus, per tick), and its median per graph weighted by |δy(30)|, N2 against the reference;
  and F(30) split by tertiles of that rate, pooled over the reference.
- **M1's cohort against the classes,** on every eligible genome of every graph: the 2 × 2 of cohort membership
  against "separate states", and the classes of the cohort genomes that are not separate states.
- **The cheaper "reaches" rule** against the full verdict, on every history, as in the pilot.
- **The locating radius, a sensitivity.** Every history that is "not approaching" with a located, accurate, stable
  root between 10⁻³ and 10⁻² away gets the continuation anyway. Reported: how many there are, how many reach, how
  their genomes' classes would change, and φ_S with those changes. The classes and the readings use the frozen rule.
- **Oscillations and the unresolved:** per graph, counts by reason, and the confirmed oscillations' periods.
- **Cost:** per graph and stage.

## Tests (rule 9; each first seen failing)

- the compacted continuation against the pilot's on a small set: same verdicts and stopping times, windows within
  10⁻¹²; a sabotaged compaction (finished strains kept, but their windows read late) must fail;
- the reduced main-run record against the full tail: same candidates and reference ranges;
- the split's arithmetic: the parts add up to Λ, the band brackets φ_S, and a toy case with known contributions;
- the bootstrap: one set of genome indices for the seed-7600 panels, an independent one for seed 7700, graphs
  resampled within ensembles;
- the batch-7 regeneration against `batch7.json`.

## Outputs and cost

Scripts in `scripts/memory_m2/census.py` (with `split.py` for the estimands), inside `wormwars.accounting`.
Outputs in `runs/memory-m2-census/`: per graph, a class record (JSON, committed) and arrays (local); the checks
C1 to C4; `split.json` and `summary.json`. **Cost:**
- the main run, 1024 genomes in chunks of 128: about 7 minutes per graph, from the pilot's 0.4 s per genome in
  batches of about 100. In one batch of 1024 it took 19 minutes in a benchmark (`runs/memory-m2/spike_main_1024.txt`); the chunked figure is an estimate, measured in the smoke test;
- the classification with the compacted continuation: about 0.35 s per genome, so about 6 minutes per graph, plus
  about 2 minutes per oscillation candidate (the pilot had one in 467 genomes);
- in all, about 13 to 15 minutes per graph, so **about 11 to 12 hours of CPU** for 48 panels, and the stop at a
  projected 16 hours.

No GPU. The plan and its scripts are reviewed by Astra and Fable before anything runs, and the results before they
are committed.

## What it does not do

- **It does not explain the lead.** It splits it between classes of dynamics; why N2 has more separate-states genomes,
  or slower fading, is M3's and M4's question.
- **One probe, one draw of genomes per graph,** 30 reference graphs.
- **The classes are the pilot's,** with its limits: cycles longer than 50 ticks and quasi-periodic orbits stay
  unresolved, and "persistent" means over the 22,000 ticks observed.
