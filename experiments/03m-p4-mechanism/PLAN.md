# 03m: what drives P4? An exploratory look (plan v2)

**Status:** exploratory, declared before the simulations run. Written 2026-09-29 for review by Astra 6
and Fable 5.1.
- v1 (`4c8848e`, `docs/reviews/20260929-000928-03m-plan/`): both said "revise". v2 adopts every
  must-fix and most suggestions (§Changes from v1).
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
contrast, not a verified equilibrium one; §Q4 records whether the holds settle.

**Code:** [`scripts/p4m.py`](../../scripts/p4m.py), with CPU tests in `tests/test_p4m.py`. It reuses
03's own code and inputs (`scripts/exp03.py`, instance "03"): the stimulus bank, the P4 definition,
and the probe genomes, drawn exactly as 03 drew them.
- **Every simulating command first recomputes N2's numerator and denominator** in 03's composition
  (2 048 strains, one row each) and stops unless they match 03's committed supplement to a relative
  10⁻⁶.
- **Every batch keeps that composition** (T1, D091): the lesions run one probe set at a time, and the
  first lesion entry is an empty deletion, which must reproduce the intact values exactly.
- **Formal runs use 03's 2 048 genomes only.** Smoke runs (`--smoke`) use 8 genomes on the CPU.
- **A measurement with a denominator below 03's floor (10⁻⁴), or not finite, is invalid:** it is
  recorded, never placed among the null graphs, and excluded from every summary.
- Every output carries its provenance (commit, versions, GPU); per-genome arrays are kept locally
  (`runs/p4m/*.npz`).

## Q1. The association (no simulation; done)

From 03's and 03r's committed supplements (`tradeoff.json`):
- within every ensemble, in both instances, graphs whose brains respond more strongly to food have
  **lower** P4: Spearman −0.27 to −0.60;
- N2's response is 4.7 to 7.1 times the ensemble median, and 1.55 to 2.7 times the most responsive
  graph of each ensemble;
- N2's P4 is above every graph but one in each instance (03: SH-route-20078; 03r: one SH-class
  graph);
- a linear fit of P4 on log(response) within each ensemble, taken out to N2's response, puts N2 4.3
  to 6.7 residual standard deviations above the fit, in all ten ensemble runs. **This is a
  model-dependent description, not a significance score:** it extrapolates beyond every ensemble's
  range, ignores the fit's own uncertainty, and the fit form was chosen after seeing the data.

**What part of the association is arithmetic.** P4 is a ratio. Within every ensemble, the numerator
grows more slowly than the denominator (a log-log slope of 0.83 to 0.96), so the ratio falls as the
response grows without any dynamical trade-off. But P4 also correlates negatively with the
separately measured common turn response (`common_turn_M0`, Spearman −0.38 to −0.69), which does not
share the denominator's construction (`tradeoff.json`), so the association is not only the ratio's
arithmetic. The association is therefore described as **a negative
association**, not a trade-off. The weakest associations are in the two routing-constrained
ensembles (SH-route, SH-mirror), which is consistent with direct food-to-read-out routes giving a
strong, fast response and a low P4 (Fable, review v1).

**Q1b, from 03's local per-genome measures (`tails.json`; not committed data, reproducible from the
binding commit):**
- P4's split-half reliability over graphs (even against odd genomes) is 0.94 to 0.99 in every
  ensemble: the association is not estimation noise;
- **N2's P4 is heavy-tailed:** its top 5% of genomes carry 40% of its numerator and 38% of its
  denominator, against about 19% in the median graph of every ensemble. So N2's large response and
  its high P4 may both be carried by a minority of genomes (Fable, review v1). Q4 tests this directly.

## Q2. Which neurons does it depend on? Deletions

- N2's 2 048 probe genomes with each neuron deleted in turn (`wormwars/deletion.py`: every edge and
  gap junction touching it, and its bias), and each bilateral pair deleted together (for example
  RIAL with RIAR). Only the **turn** read-out neurons (SMD and RMD) are excluded, since P4 reads turn
  alone; the forward read-out neurons (AVA, AVB, AVD, AVE, PVC) are included (Astra, Fable).
- **Reported per deletion:** P4, its numerator and denominator; where the pair falls in each of 03's
  ensembles; its residual from a pooled P4-on-log(response) fit; the neuron's degree.
- **Three classes, reported separately** (Astra, Fable), against 03's five ensembles pooled:
  - **"P4 only":** P4 below the pooled 95th percentile, response still above the pooled maximum.
    This is the most informative class: persistence lost, response kept;
  - **"response only":** the reverse;
  - **"both".**

  Falling below these thresholds means "no longer unusually high", not "inside the ensembles'
  distribution": there is no lower bound and no joint test.
- **Deletions locate dependencies, not where history is stored:** a bottleneck on the path to the
  read-out can be critical without holding the state. Deleting AWA, AWC or ASE, singly or as a pair,
  removes part of the food input path, not all of it.
- **Follow-up, by synapse type:** for the 5 single deletions with the lowest P4, only their chemical
  edges, then only their gap junctions, are deleted.
- **Pre-named targets** (02b's critical core, the outside review): RIA and AIZ; also AIY, AIB, RIB and
  RIM.
- **If no deletion falls in a class,** that is reported as such: P4 in N2 would then not depend on
  any single neuron or pair.

## Q3. Gap junctions or chemical synapses?

- N2 with gap junctions off, chemical synapses off, and both off;
- N2 with only the chemical, or only the gap-junction, weight magnitudes permuted among the existing
  edges, over **8 seeds** (100-107), paired with N2's own genome draws (signs, biases and time
  constants unchanged). v1 used one seed, which turned out to be N2perm1's placement, the atypical
  one (Fable);
- **gap junctions off is also measured on Q4's 80 null graphs,** so N2's change is compared with the
  nulls' change, not with intact nulls (Fable).
- **Reading:** a condition matters if it moves N2's P4 or response outside the range of its 8 seeds'
  or the nulls' matched change. Switching one type off tests dependence on that type; it does not
  show that the other type is irrelevant.

## Q4. How long does the history last?

- After the ramp, the final input is held for **300 ticks** instead of 5, and |rising − falling| is
  recorded at ticks 0, 5, and every 10, for N2 and the first 16 graphs of each of 03's ensembles.
  Tick 0 is 03's numerator, a per-graph reproduction check; tick 5 is 03's "after".
- **Reported:** the mean difference over time; the ratio of means at 300 ticks; among genomes whose
  starting difference is at least 10⁻³ (an absolute floor; the share excluded is reported), the share
  whose difference at 300 ticks is still above 10% of its start ("separation remaining"); whether each
  trajectory has settled (the largest change in the full state over the last 10 ticks below 10⁻⁴);
  whether the 100-tick holds settled; the top-5% share of the numerator; and the mean tanh slope of
  the turn read-out neurons at the holds' and the ramp's end (saturation).
- **Reading, narrowed** (Astra, Fable): separation that remains at 300 ticks in trajectories that
  have settled is consistent with more than one stable state for the same input; remaining
  separation in unsettled trajectories could be a slow network mode, an oscillation out of phase, or
  a long transient. 300 ticks is 15 or more of the slowest neuron time constant, not necessarily of
  the slowest network mode. Signed per-genome curves are kept locally.

## Q5. Wiring or weight placement?

- N2's own wiring with its anatomical weight magnitudes permuted among its edges, **64 permutations**
  (seeds 100-163; 03 used 1-3 and 03r 4-6 as N2perm graphs), in **two designs** (Astra, Fable):
  - **independent:** each permutation with its own genome draws, as 03 drew its N2perm graphs;
  - **paired:** N2's own genome draws, with only the magnitudes permuted.
- **Reported:** both distributions of P4 and of the response, against N2's and each ensemble's.
- **The outside review's hint, to be checked, not assumed:** in five of 03's and 03r's six N2perm
  graphs the response fell to about the null median while P4 stayed at 0.86-0.92. If the
  permutations keep a high P4 and lose the large response, that suggests the wiring alone supports
  persistence and the weight placement sets the response size; persistence can also change with
  weight placement, so the result is read from the distribution, not asserted.

## Not in this plan

- Whether the effect holds for inputs other than food: it needs a stimulus bank for another channel.
- Connection deletions beyond Q2's follow-up by synapse type: left for the confirmatory design.
- Any evolved brain.

## Compute and execution

- **After 04a's evaluation,** on the RTX 5080: 04a is running, and this must not slow it or share its
  cap.
- **Estimate** (from 03's pilot timing of the history probe, about 12.7 s per graph at 2 048
  genomes; Fable): lesions about 1.3 GPU-hours (about 375 deletions, plus 10 follow-ups); decay about
  1.0; weights about 0.5 (two designs); synapses about 0.05. **About 2.9 GPU-hours in total; the cap
  is 4 GPU-hours** for every command together, counted by the accounting (`runs/p4m/compute.json`)
  and checked before every batch. The aggregate is copied to `compute-record.json` here.
- Partial results are written as batches complete (`*-partial.json`).
- Order: synapses, weights, decay, lesions (cheapest first, so a cap hit loses the least).
- Outputs committed here: `tradeoff.json`, `tails.json`, `lesions.json`, `synapses.json`,
  `decay.json`, `weights.json`, `compute-record.json`.

## What this cannot establish

- A mechanism in the causal sense beyond "this deletion or change moves N2's numbers": the brains are
  random and unevolved, and the read-out is a hand-chosen interface;
- anything about behaviour: P4 is a probe of the brain alone;
- confirmatory claims: every comparison here was chosen with 03's and 03r's data in view.

## Changes from v1 (review v1)

**Must-fixes:** "highest P4" corrected (both); the ranges (4.7-7.1; 1.55-2.7) corrected (both); the
compute estimate from 03's timings, with a cap enforced before every batch and partial writes
(Fable, Astra); the lesions in 03's composition, with an empty deletion as a reproduction check
(both); invalid measurements never placed among the nulls (Astra); smoke forced to the CPU and
formal runs to 2 048 genomes (Astra); Q3's by-type permutations over 8 seeds (Fable); per-genome
arrays kept (Fable); Q4's reading narrowed, with an absolute floor and a settling check (both); the
lead rule split into three classes (both); Q5's causal wording narrowed and a paired design added
(both); the residual-SD figures described as model-dependent (Astra); AWA, AWC and ASE deletions
described as partial input-path lesions (Astra).

**Suggestions adopted:** Q1's arithmetic checks (log-log slope; the common turn response) and the
per-genome tails (both); the forward read-out neurons included (both); gaps off on the null panel
(Fable); settling of the holds and read-out saturation (Astra); a follow-up by synapse type for the
top deletions (Astra); CPU tests (Fable); provenance on every output (Fable); the outside review
archived (Fable).
