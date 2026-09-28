# 03m: what drives P4? An exploratory look (plan v3)

**Status:** exploratory, declared before the simulations run. Written 2026-09-29 for review by Astra 6
and Fable 5.1.
- v1 (`4c8848e`, `docs/reviews/20260929-000928-03m-plan/`): both said "revise".
- v2 (`0916f41`, `docs/reviews/20260929-002434-03m-plan-v2/`): both said "revise": two v1 fixes were
  only partial, v2 added bugs (among them a filter that pooled every ensemble under "SH"), and four
  Q1 sentences overstated. v3 fixes them (§Changes).
- Nothing here is confirmatory. A confirmatory mechanism study, if one follows, gets its own
  pre-registration, and its label is assigned there (ROADMAP.md, Track B).

**Why now.** 03 and 03r found that N2's random, unevolved brains show more history dependence (P4)
than shuffled graphs: borderline in 03, replicated in 03r (D080). The roadmap's Track B asks where the
effect lives, whether it runs through gap junctions or chemical synapses, and what gives N2's brains
their much stronger response to food. An outside review (a Claude Opus 5.5 instance, shared by the
owner on 2026-09-28; archived in `docs/reviews/20260928-outside-review/`) read the committed data and
suggested cheap checks, which this plan takes up.

**What P4 is.** For each random genome, the raw turn read-out after a food ramp that rises to a level
is compared with the read-out after a ramp that falls to the same level. P4 is the mean |rising −
falling| at the ramp's end (the numerator), divided by the mean |steady contrast|, the difference
between holding the two starting levels for 100 ticks (the denominator, called the "response" below).
P4 uses the brain only, with no world and no motor calibration. The denominator is a finite-time
contrast, not a verified equilibrium one; §Q4 records how much the holds still move.

**Code:** [`scripts/p4m.py`](../../scripts/p4m.py), with CPU tests in `tests/test_p4m.py`. It reuses
03's own code and inputs (`scripts/exp03.py`, instance "03"): the stimulus bank, the P4 definition,
and the probe genomes, drawn exactly as 03 drew them.
- **Every simulating command first recomputes N2's numerator and denominator** in 03's composition
  (2 048 strains, one row each) and stops unless they match 03's committed supplement to a relative
  10⁻⁶. Q4 applies the same check to every panel graph.
- **Every batch keeps that composition** (T1, D091): the lesions run one probe set at a time. The first
  lesion entry is an empty deletion, checked immediately to reproduce the intact values exactly.
- **Formal runs** need 03's 2 048 genomes, a clean tree pushed to its branch, and the registered GPU
  and environment (the shared guards). Smoke runs (`--smoke`) use 8 genomes on the CPU.
- **A measurement with a denominator below 03's floor (10⁻⁴), or not finite, is invalid:** it is
  recorded, never placed among the null graphs, and excluded from every summary. Terms are averaged
  in float64, as 03's supplement was; the JSON holds no NaN.
- **Everything is written as it completes:** each command's summary (`*-partial.json`) and its
  per-genome arrays (`runs/p4m/*.npz`, local). Every output carries its provenance, device and genome
  count.

## Q1. The association (no simulation; done)

From 03's and 03r's committed supplements (`tradeoff.json`):
- within every ensemble, in both instances, graphs whose brains respond more strongly to food have
  **lower** P4: Spearman −0.27 to −0.60;
- P4 also falls with the common turn response, a separately computed measure on the same 2 048
  genomes (`common_turn_M0`): Spearman −0.38 to −0.69, more negative than with the denominator in all
  ten ensemble runs. This removes the literal reuse of P4's denominator, though a separate response
  measure can still inherit its association through the denominator;
- N2's response is 4.7 to 7.1 times the ensemble median, and 1.55 to 2.7 times the most responsive
  graph of each ensemble;
- N2's P4 is above every graph but one in each instance (03: SH-route-20078; 03r: one SH-class
  graph);
- a linear fit of P4 on log(response) within each ensemble, taken out to N2's response, puts N2 4.3
  to 6.7 residual standard deviations above the fit, in all ten ensemble runs. **This is a
  model-dependent description, not a significance score:** it extrapolates beyond every ensemble's
  range, ignores the fit's own uncertainty, and the fit form was chosen after seeing the data;
- the numerator's log-log slope on the denominator is 0.83 to 0.96. That is the same association
  restated (P4's own slope is that value minus 1), not a separate arithmetic component.

In 03, the two routing-constrained ensembles (SH-route, SH-mirror) show the weakest associations,
consistent with direct food-to-read-out routes giving a strong, fast response and a low P4 (Fable,
review v1). **In 03r this ordering does not hold** (SH-class, −0.36, is weaker than SH-mirror, −0.45),
so it is not a finding.

**Q1b, from 03's local per-genome measures** (`tails.json`; the files are not committed, and a hash
of their names and contents is recorded):
- P4's split-half reliability over graphs (even against odd genomes) is 0.94 to 0.99 per ensemble,
  and P4 from even genomes against the response from odd genomes still gives Spearman −0.25 to −0.61.
  An explanation by estimation noise alone is therefore unlikely, though not excluded;
- **N2's numerator and response are concentrated in few genomes:** its top 5% of genomes by numerator
  carry 40% of the numerator, above every graph in four ensembles and all but one in SH-recip (median
  graphs: 18-20%); its top 5% by response carry 38% of the response (medians 17-19%); and the two
  top-5% sets are 92% the same genomes (medians 75-84%);
- **but N2's high P4 does not rest on that minority:** with its top 5% by numerator removed, N2's P4
  is 0.895, still above 97% to 100% of each ensemble's graphs with the same removal.

## Q2. Which neurons does it depend on? Deletions

- N2's 2 048 probe genomes with each neuron deleted in turn (`wormwars/deletion.py`: every edge and
  gap junction touching it, and its bias), and each bilateral pair deleted together (for example RIAL
  with RIAR). Only the **turn** read-out neurons (SMD and RMD) are excluded, since P4 reads turn
  alone; the forward read-out neurons (AVA, AVB, AVD, AVE, PVC) are included.
- **Order:** the empty deletion; the pre-named targets (RIA, AIZ, AIY, AIB, RIB, RIM, from 02b's
  critical core and the outside review), as pairs and then singly; every other single; every other
  pair. A cap hit loses the pre-named targets last.
- **Reported per deletion:** P4, its numerator and denominator, and their change from intact; where the
  pair falls in each of 03's ensembles; its residual from a pooled P4-on-log(response) fit; the
  neuron's degree. The thresholds are recorded with the results.
- **Three classes, reported separately,** against 03's five ensembles pooled:
  - **"P4 only":** P4 below the pooled 95th percentile, the response still above the pooled maximum.
    This is the most informative class: persistence lost, response kept;
  - **"response only":** the reverse;
  - **"both".**

  The thresholds are asymmetric (Fable): N2's P4 (0.93) is close to the pooled 95th percentile, while
  its response is well above the pooled maximum, so "P4 only" needs a small drop and the response
  classes a large one. The changes from intact are reported so that either can be read without the
  classes. Falling below a threshold means "no longer unusually high", not "inside the ensembles'
  distribution".
- **Deletions locate dependencies, not where history is stored:** a bottleneck on the path to the
  read-out can be critical without holding the state. Deleting AWA, AWC or ASE removes part of the
  food input path, not all of it.
- **Follow-up, by synapse type:** for the 5 valid single deletions with the lowest P4 among those that
  keep at least the pooled null median response, only their chemical edges, then only their gap
  junctions, are deleted.
- **If no deletion falls in a class,** that is reported as: no tested valid single or bilateral-pair
  deletion removed the unusual elevation under these thresholds (Astra).

## Q3. Gap junctions or chemical synapses?

- N2 with gap junctions off, chemical synapses off, and both off. With chemical synapses off, food
  input barely reaches the read-out, and the measurement is expected to be invalid;
- N2 with only the chemical, or only the gap-junction, weight magnitudes permuted among the existing
  edges, over **8 seeds** (100-107), paired with N2's own genome draws;
- **gap junctions off is also measured on Q4's 80 null graphs.**
- **Reading:** "change" is the difference from intact N2, in P4 and in the response. Gaps off matters
  if N2's change lies outside the null panel's range of changes under the same condition. A by-type
  permutation matters if its 8 seeds' changes lie on one side of zero. Chemical off has no matched
  null. Switching one type off tests dependence on that type; it does not show that the other type is
  irrelevant.

## Q4. How long does the history last?

- After the ramp, the final input is held for **300 ticks** instead of 5, and |rising − falling| is
  recorded at ticks 0, 5 and every 10, for N2 and the first 16 graphs of each of 03's ensembles. Tick
  0 and the steady contrast must reproduce 03's numerator and denominator for each graph.
- **Reported:** the mean difference over time; the ratio of means at 300 ticks; among genomes whose
  starting difference is at least 10⁻³ (the share excluded is reported), the share whose difference at
  300 ticks is still above 10% of its start ("separation remaining"); whether each trajectory has
  settled; how much the turn read-out still moves over the holds' last 10 ticks; the top-5% share of
  the numerator; and the mean tanh slope of the turn read-out neurons at the holds' and the ramp's
  end (saturation). Shares with no eligible genome are reported as missing, with their counts.
- **Settling** is the largest range of any neuron's state over every tick of the last 10 (Astra: a
  comparison of the window's two ends would miss an oscillation that returns to its start). Below
  10⁻⁴, a trajectory counts as settled.
- **Reading, narrowed:** separation that remains at 300 ticks in trajectories that have settled is
  consistent with more than one stable state for the same input. Remaining separation in unsettled
  trajectories could be a slow network mode, an oscillation out of phase, or a long transient. 300
  ticks is 15 or more of the slowest neuron time constant, not necessarily of the slowest network
  mode.

## Q5. Wiring or weight placement?

- N2's own wiring with its anatomical weight magnitudes permuted among its edges, **64 permutations**
  (seeds 100-163; 03 used 1-3 and 03r 4-6 as N2perm graphs), in **two designs:**
  - **independent:** each permutation with its own genome draws, as 03 drew its N2perm graphs;
  - **paired:** N2's own genome draws, with only the magnitudes permuted.
- **Reported:** both distributions of P4 and of the response, against N2's and each ensemble's.
  Per-genome arrays are kept, so whether the permutations keep N2's concentrated minority can be
  checked afterwards.
- **The outside review's hint, to be checked, not assumed:** in five of 03's and 03r's six N2perm
  graphs the response fell to about the null median while P4 stayed at 0.86-0.92. If the permutations
  keep a high P4 and lose the large response, that suggests the wiring alone supports persistence and
  the weight placement sets the response size. Persistence can also change with weight placement, so
  the result is read from the distribution, not asserted.

## Not in this plan

- Whether the effect holds for inputs other than food: it needs a stimulus bank for another channel.
- Connection deletions beyond Q2's follow-up by synapse type: left for the confirmatory design.
- Any evolved brain.

## Compute and execution

- **After 04a's evaluation,** on the RTX 5080: 04a is running, and this must not slow it or share its
  cap.
- **First, on the CPU:** `p4m.py graphs` rebuilds Q4's 80 null graphs from 03's record (about 0.3
  hours, counted by the accounting). The decay command refuses to start if any is missing.
- **Estimate** (03's pilot timed the history probe at 12.6-13.9 s per graph at 2 048 genomes; Fable):
  lesions about 1.4 GPU-hours (about 386 deletions and 10 follow-ups); decay about 1.0, plus 0.3 for
  gaps off on the panel; weights about 0.5 (two designs); synapses about 0.1. **About 3.6 hours in
  all, with the graph rebuild; the cap is 5 hours** for every command together, counted by the
  accounting (`runs/p4m/compute.json`) and checked before every batch. The aggregate is copied to
  `compute-record.json` here after each command, including one that stops.
- **Order:** graphs, synapses, weights, decay, lesions: cheapest first, so a cap hit loses the least.
- Outputs committed here: `tradeoff.json`, `tails.json`, `synapses.json`, `weights.json`,
  `decay.json`, `lesions.json`, `compute-record.json`.

## What this cannot establish

- A mechanism in the causal sense beyond "this deletion or change moves N2's numbers": the brains are
  random and unevolved, and the read-out is a hand-chosen interface;
- anything about behaviour: P4 is a probe of the brain alone;
- confirmatory claims: every comparison here was chosen with 03's and 03r's data in view.

## Changes

**From v1 (review v1):** "highest P4" and the ranges corrected; the compute estimate from 03's
timings, a cap before every batch, partial writes; the lesions in 03's composition with an empty
deletion; invalid measurements never placed; smoke on the CPU and formal runs at 2 048 genomes; Q3
over 8 seeds; per-genome arrays; Q4's reading narrowed, with a floor and a settling check; three
lead classes; Q5's wording narrowed and a paired design added; Q1's arithmetic and tail checks; the
forward read-out neurons included; gaps off on the null panel; saturation; a follow-up by synapse
type; CPU tests; provenance; the outside review archived.

**From v2 (review v2):**
- **Bugs:** Q1b pooled every ensemble under "SH" (both): exact membership, a test, and `tails.json`
  regenerated. Settling compared two endpoints 11 ticks apart (Astra): now the range over every tick
  of 10, with a test of an oscillation. The compute record missed the command that wrote it (both):
  now exported after the accounting records the attempt, success or stop, tested.
- **Retention** (both): synapses and weights write partial summaries and per-genome arrays after every
  condition; the lesions' arrays are saved every 20 deletions and the follow-up's too; decay keeps its
  per-genome steady contrasts and settling and saturation terms.
- **The empty deletion** is checked right after its batch, not after the sweep (both).
- **Compute:** the estimate corrected to about 3.6 hours, the graphs rebuilt first, the cap raised to
  5, and the pre-named targets run first (Fable).
- **Q1's text** (both): split-half 0.94-0.99 per ensemble; the tails with N2's rank, the denominator's
  null figures, the overlap of the two sets and P4 without the top 5%; the log-log slope described as
  a restatement; the common-response check described accurately; the routing ordering not a finding;
  noise "unlikely", not excluded.
- **Q2:** the empty-screen sentence narrowed (Astra); thresholds and changes from intact recorded; the
  follow-up restricted to deletions that keep a response (Fable).
- **Q3's reading rule** defined (Fable, Astra).
- **Also:** formal runs require a clean, pushed tree; terms averaged in float64; no NaN in JSON;
  missing conditional shares; per-graph reproduction in Q4 enforced; device and genome count recorded;
  Q1b's inputs hashed; tests of the tails, the decay summary and the window statistic.
