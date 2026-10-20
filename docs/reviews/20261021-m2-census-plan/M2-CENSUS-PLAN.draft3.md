# M2 census: how much of N2's lead is separate states — the plan

*Draft 3, 2026-10-21, after two rounds of review (Astra 6 and Fable 5.1, both "revise" each time; drafts 1 and 2 and
the reviews are archived in [`docs/reviews/20261021-m2-census-plan/`](../reviews/20261021-m2-census-plan/)). Exploratory: nothing here is a pre-registration, but the estimands, the readings
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
  pilot's locating, reaching, oscillation and class functions). One engineering change, below, checked for
  equivalence first;
- **the follow-up length:** 2000 ticks;
- **the cheaper "reaches" rule:** it agreed on all 934 pilot histories, but the census keeps the full rule (its cost
  is now small, below) and reports the agreement again;
- **no float64, finer integration or fixed batches:** the main run stays float32 at 32 substeps;
- **two states, not more:** the census counts separate-states genomes, not their states;
- **the locating radius:** kept at 10⁻³ for the classes; its effect is reported as a sensitivity (below).

## The sample

- **Genomes:** 1024 per graph, `Genome.random` with seed 7600, M1's draw, so M1's per-genome numbers apply to the same
  brains. The whole panel of 1024 is drawn first and then sliced into chunks (`Genome.random` draws in batches, so
  drawing chunk by chunk would give other genomes; Astra), as the pilot's `graph_run` does. N2 also gets M1's second panel, seed 7700. M1's probe, unchanged: 100 ticks of warm-up at 0.25× or 1.75×
  the final food level, a 10-tick ramp, then the follow-up at the final level, here 2000 ticks; 32 substeps,
  float32.
- **Eligible:** a_i ≥ 10⁻³ (M1), with a_i = |δy_i(0)|. Every eligible genome is classified. The ineligible
  genomes' fractions of each graph's numerator and denominator are reported (M1).
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
  The pilot's own `probe_states` record (every tick to 300, every 10th to 1800, every tick from 1801 to 2000), used
  by the classification of the same chunk and then discarded. Kept per genome: δy every tick from 0 to 2000 (local),
  a, |δy| at ticks 30, 100 and 300, 03mc's settled flag (ticks 291-300), cohort membership, and the two roots
  (local). The ramp's steady contrast is computed for M1's validity rule. A non-finite state stops the run, as in
  M1.
- **The classification:** the pilot's `full_classify` on the eligible genomes of each chunk of 128, right after the
  chunk's main run.
- **One engineering change,** which changes no rule:
  - **the continuation drops finished strains from its batch.** The pilot integrated every row until the slowest was
    done. In a spike on the pilot's 196 genomes of N2 and SH-2010013, the compacted continuation gave the same
    reaching verdict and the same stopping time for every history, 3.3 to 3.5 times faster (113.5 s against 34.3 s,
    133.2 s against 37.7 s; `scripts/memory_m2/spike_compact.py`, output `runs/memory-m2/spike_compact.txt`). A committed test repeats this comparison on a small set and also requires the distance
    windows to agree within 10⁻¹² (rule 7);
  - *(draft 2 had a second change, a main run that kept only ranges instead of the whole tail. It is dropped: each
    chunk of 128 is classified right after its own main run, from the pilot's own record, which holds about 200 MB a
    chunk and is then discarded. So the record is the pilot's.)*
- **Order:** N2 seed 7600; the reference graphs, one per ensemble in turn; N2 seed 7700; the selected graphs; batch
  7's graphs. Each graph writes its own files and is skipped if they exist, so a stopped run resumes.

## Checks before and during the run

- **C1, reproduction of M1.** On the 42 panels M1 ran (N2's two, the 30 random, the 10 selected), the census's a_i,
  |δy_i(30)| and |δy_i(100)|, eligibility and cohort membership are compared with M1's arrays
  (`runs/memory-m1/panels/*.npz`, local), genome by genome, and its eligible shares at ticks 30, 100 and 300 and its
  cohort contributions C(30) and C(300) with M1's panel records (`runs/memory-m1/panels/*.json`; M1's arrays do not
  keep |δy(300)|; Astra). M1's intact run was one batch of 1024; the census runs chunks of 128, and T1 §3 claims no
  bitwise equality across compositions. So the gaps are saved and summarised, and the census **stops for
  investigation** if more than 1% of a panel's genomes differ by more than 10⁻³ in a or |δy(30)| (M1's own rule).
  Changes of eligibility or cohort membership are counted, named, and reported with their tick-30 and tick-300
  numerators, since N2's cohorts hold only 14 and 12 genomes (Astra). The census uses its own arrays throughout,
  never M1's.
- **C2, the planted genomes.** The pilot's six (R6), run and classified through the census's own path (the
  compacted continuation; Astra) before the census starts. Every one must be named
  exactly, or nothing runs.
- **C3, P against the integrator.** At 20 located roots drawn at random over the census
  (`default_rng(20261029)`), P³² against the automatic derivative of one float64 tick, within 10⁻⁸ (R4′).
- **C4, resolution.** Per graph, the unresolved fraction of eligible genomes and of the eligible tick-30 numerator,
  against the pilot's R2 thresholds (5% and 10%). A graph above either is named. It is not dropped: the unresolved
  genomes enter the split as a band (below).
- **C5, the pilot's genomes again** (Fable). The census reclassifies the pilot's 467 genomes, all on census graphs,
  in a new batch composition and through the changed pipeline. Their classes and both roots are compared with the
  pilot's (`classes__*.json`, `roots__*.npz`) at R3's thresholds: classes agree for at least 95%, and every "separate
  states" history reaches the same root (within 10⁻⁶). This is the one end-to-end test of the compacted continuation
  and the chunking together, at scale. A failure is investigated before the split is read.
- **The cost guard.** After N2's first panel and the first reference graph, the script projects the whole census,
  every stage included (the oscillation checks and the radius sensitivity too; Astra). If the projection exceeds 16
  hours, it stops and the plan is revisited.

## The estimands

For a graph g and tick t ∈ {30, 300}, over its eligible genomes E:
- **the eligible share** s_g(t) = Σ_E |δy_i(t)| / Σ_E a_i (M1);
- **the class contributions** X_g(t) = Σ_{i ∈ E, class X} |δy_i(t)| / Σ_E a_i, for X = S (separate states, both
  subclasses), F (fading), O (persistent oscillation) and U (unresolved). Exactly, s = S + F + O + U.

**The split,** as M1's A5 took it, from pairwise contrasts averaged over the reference R (the 30 random graphs), so
that the parts add up:
- Λ(t) = s_N2(t) − mean_R s_g(t), and Λ_X(t) = X_N2(t) − mean_R X_g(t), with Λ = Λ_S + Λ_F + Λ_O + Λ_U;
- **φ_X(t) = Λ_X(t) / Λ(t),** the part of N2's mean lead carried by class X. φ is defined only if the observed Λ is
  positive; otherwise every reading is inconclusive. Negative parts and parts above 1 are kept as they come
  (Astra).

**What the split is** (Fable, Astra): a split **by genome**. Each genome's whole |δy(30)| goes to its class; a
separate-states genome's tick-30 difference also contains a transient part, which the split does not separate out.
And both of N2's panels are read against the same 30 seed-7600 reference panels, so agreement between them
replicates N2's draw of genomes, not the reference.

**The unresolved band** (the roadmap: unresolved genomes enter "as an explicit uncertainty band, not as zero"):
- φ_S⁻ = (S_N2 − mean_R (S_g + U_g)) / Λ, every unresolved genome counted as separate states in the reference and as
  something else in N2;
- φ_S⁺ = (S_N2 + U_N2 − mean_R S_g) / Λ, the reverse.

The same is defined for F. The band is assignment uncertainty; the bootstrap below is sampling uncertainty, and
the two are reported apart (Astra). The lead by M1's own definition (N2 minus the reference median) is reported
beside Λ, and not split, since medians do not add.

**Uncertainty:** M1's bootstrap. Graphs are resampled within ensembles. Genome indices are resampled once for all
seed-7600 panels, which share their draws index by index, and independently for N2's seed-7700 panel. 2000
resamples, 90% percentile intervals, `default_rng(20261028)`. A resample with Λ ≤ 0 is counted. If more than 100 of
the 2000 have it, the reading is inconclusive; otherwise they are dropped and their number reported.

## The readings (fixed here)

At tick 30, on each of N2's two panels, from the 90% intervals of the band's two ends (lower(·) and upper(·)):
- **"separate states carry most of N2's lead"** if lower(φ_S⁻) > 0.5;
- **"separate states carry little of N2's lead"** if upper(φ_S⁺) < 0.25;
- **"separate states carry a part of N2's lead, between a quarter and a half"** if lower(φ_S⁻) > 0.25 and
  upper(φ_S⁺) < 0.5;
- **"inconclusive"** otherwise (Astra: a wide interval is not "a part"), with φ_S, the band and the intervals
  reported, and what they do exclude said in words (for example "at least a quarter").

If more than 100 resamples have Λ ≤ 0, or the observed Λ is not positive, that panel's reading is inconclusive,
whatever the intervals (Astra). **Combining the two panels,** in this order (Fable, Astra):
1. if either panel is inconclusive through its denominator, the result is inconclusive;
2. if both give the same reading, that is the result;
3. if one is conclusive and the other "inconclusive", the result is "*X* on one panel, inconclusive on the other";
4. if both are conclusive and differ, the result is **"not replicated"**.

Each panel's reading, interval and band are reported in every case. Tick 300 is read the same way, as a
description.

**The roadmap's branch** ("settling explains little of the excess. The graded part then becomes the main target") is
taken only on "little" **and** lower(φ_F⁻) > 0.5, **on both panels**: little from separate states does not by itself
say that fading carries the rest, since oscillations or the unresolved could (Astra). "Little" without it reads
"little; the remainder not attributed to fading".

*Beforehand* (Fable, Astra, from M1's committed panel records): on these panels N2's cohort contribution C(30) is
0.081 (seed 7600) and 0.060 (seed 7700), the 30 reference graphs' mean C(30) is 0.0059, and their mean eligible
share is 0.273, so Λ is about 0.171 and 0.170, and the cohort's contrast is about 0.44 and 0.32 of it. If the
census's separate states were exactly M1's cohort, φ_S would be near those values. Separate-states genomes outside
the cohort raise φ_S where they are N2's and lower it where they are the reference's (Astra), so this does not
settle the reading in advance. With 12 to 14 cohort genomes per N2 panel a genome bootstrap will give wide
intervals: "a part" or "inconclusive" is the likely reading, "little" would need many reference genomes with
separate states outside their cohorts, and "most" many of N2's. **The census's deliverable is the split itself**
(the point estimates, the band and the intervals) and the descriptions below, more than the reading.

## Descriptions (no readings)

- **Per graph and class:** counts, contributions at ticks 30 and 300, and φ_X per ensemble (6 graphs each).
- **The contributions over time** (Astra): X_g(t) for every tick from 0 to 300 and every 100th to 2000, per class,
  from the recorded δy, for N2 and the reference mean. No new simulation.
- **Composition against retention** (Fable): for S and F, the class's share of the eligible denominator,
  w_X = Σ_X a / Σ_E a, and its own retention, ρ_X(t) = Σ_X |δy(t)| / Σ_X a, so X = w_X ρ_X. Λ_X is the mean over
  the 30 pairs (N2, g) of X_N2 − X_g. Over the pairs where both graphs have the class, each pair's difference splits
  exactly into a composition part, (w_N2 − w_g)(ρ_N2 + ρ_g)/2, and a retention part, (ρ_N2 − ρ_g)(w_N2 + w_g)/2.
  A pair where one graph lacks the class has ρ undefined there (0/0; most reference graphs have no cohort, so this
  is common for S; Fable, Astra): its whole difference is reported as a third part, **presence**, and not split.
  So Λ_X = composition + retention + presence, each a mean over all 30 pairs, with the number of presence pairs
  reported. This says whether N2 has more of a class or keeps more within it; for F it is the direct measure of
  "graded slower fading".
- **Settling and share** (Astra): across the 30 reference graphs, the Spearman correlation of s(30) with the number
  of cohort genomes and with the number of separate-states genomes (each as a fraction of the eligible), pooled and per
  ensemble, undefined where a count is constant. Most reference graphs will tie at zero cohort genomes (20 of the
  30 had an empty cohort in M1), so the pooled coefficient is weak and the per-ensemble ones say almost nothing
  (Fable). Correlating s with S would correlate a total with its own part, so it is not used. Six graphs per ensemble cannot test 03mc's within-ensemble association, which the roadmap asks the
  census to test; that test is deferred, and this only says whether the fresh panels look the same.
- **The core-frozen and hub-frozen shuffles:** S(30), F(30), s(30) and the number of separate-states genomes per
  graph, against N2 and the reference. And **where the states differ:** for each separate-states genome, the fraction
  of ‖v₁* − v₂*‖² (the two roots' difference) on batch 7's 30 core neurons, on its 30 hub neurons, and on the rest,
  averaged per graph with weights |δy(30)|, on every arm and on N2 and the reference (Fable: the core needs its
  control). The 8 read-out neurons all lie inside the core, so their fraction is reported as part of it, and the core
  was chosen on N2's start difference. This answers the roadmap's "do the core-frozen graphs keep N2's settling and its
  location, and do the hub-frozen graphs lose it?" descriptively, with three graphs per arm.
- **The asymptotic rate of fading:** for each fading genome, the slowest discrete rate of P³² at its common root
  (the log of its largest eigenvalue modulus, per tick), and its median per graph weighted by |δy(30)|, N2 against
  the reference. This is the late, asymptotic rate; the slowest mode can be weakly excited or invisible to the
  read-out, and tick-30 retention is mostly transient (307 of the pilot's 349 fading genomes were cancellations;
  Fable, Astra). So it is a description beside the composition-retention split above, not a measure of tick-30
  fading.
- **M1's cohort against the classes,** on every eligible genome of every graph: the 2 × 2 of cohort membership
  against "separate states", with each cell's count and its tick-30 and tick-300 numerators, so that S(30) − C(30)
  traces to the off-diagonal cells (Fable); and the classes of the cohort genomes that are not separate states.
- **The cheaper "reaches" rule** against the full verdict, on every history, as in the pilot.
- **The locating radius, a sensitivity.** Every history that is "not approaching" with a located, accurate, stable
  root between 10⁻³ and 10⁻² away gets the continuation anyway. Reported: how many there are, how many reach, how
  their genomes' classes would change, and φ_S with those changes. The classes and the readings use the frozen rule.
- **Oscillations and the unresolved:** per graph, counts by reason, and the confirmed oscillations' periods.
- **Cost:** per graph and stage.

## Tests (rule 9; each first seen failing)

- the compacted continuation against the pilot's: same reaching verdicts, stopping times and capped flags, and
  distance windows, forecast windows and returned states within 10⁻¹², on a set built to include staggered
  completions, surviving strains at non-contiguous indices, a last strain running alone, and rows that reach the cap
  (Astra); a sabotaged compaction (a finished strain's window read one tick late) must fail. A real oscillation
  candidate never enters this continuation (its root is unstable, or it is not reached); the candidates go through
  the census path in C2, where the planted cycles are oscillation candidates;
- the split's arithmetic: the parts add up to Λ, the band brackets φ_S, a toy case with known contributions, and the
  composition-retention-presence identity with an empty class on either side (Fable, Astra);
- the readings and their combination: each reading's boundary, the denominator override on either panel, "X on one
  panel, inconclusive on the other", "not replicated", and the branch condition on both panels (Astra);
- the bootstrap: one set of genome indices for the seed-7600 panels, an independent one for seed 7700, graphs
  resampled within ensembles;
- the batch-7 regeneration against `batch7.json`.

## Outputs and cost

Scripts in `scripts/memory_m2/census.py` (with `split.py` for the estimands), inside `wormwars.accounting`; the
compacted continuation is `continuation_compact` in `pilot.py`, off unless asked for, so the pilot's own path is
unchanged.
Outputs in `runs/memory-m2-census/`: per graph, a class record (JSON, committed) and arrays (local); the checks
C1 to C5; `split.json` and `summary.json`. **Cost:**
- the main run and the classification together: 0.64 s per genome in a smoke test of the census code on 64 N2
  genomes (40.7 s, one chunk), so about 11 minutes per 1024-genome graph. In one batch of 1024 the main run alone took
  19 minutes (`runs/memory-m2/spike_main_1024.txt`), which is why the census runs chunks;
- the oscillation candidates: the pilot had two candidate histories in 467 genomes, so about 4.4 per 1024-genome
  graph (Astra). Each costs about 40 s here (in the spike, N2's 100 genomes, with genome 26's two candidate
  histories, took 199 s against 123 s for SH-2010013's 96 without any), so about 3 minutes per graph;
- in all, about 14 minutes per graph, so **about 11 hours of CPU** for 48 panels, with the stop at a projected 16
  hours. The candidate rate is uncertain (one genome in the pilot) and these are extrapolations, not a benchmark of
  the whole path; the guard measures it on the first two panels, N2's among them (Astra).

No GPU. The plan and its scripts are reviewed by Astra and Fable before anything runs, and the results before they
are committed.

## What it does not do

- **It does not explain the lead.** It splits it between classes of dynamics; why N2 has more separate-states genomes,
  or slower fading, is M3's and M4's question.
- **One probe, one draw of genomes per graph,** 30 reference graphs.
- **The classes are the pilot's,** with its limits: cycles longer than 50 ticks and quasi-periodic orbits stay
  unresolved, and "persistent" means over the 22,000 ticks observed.
