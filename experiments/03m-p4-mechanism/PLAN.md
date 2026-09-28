# 03m: what drives P4? An exploratory look (plan v1)

**Status:** exploratory, declared before it runs. Written 2026-09-29, for review by Astra 6 and
Fable 5.1. Nothing here is confirmatory. A confirmatory mechanism study, if one follows, gets its
own pre-registration, and its label is assigned there (ROADMAP.md, Track B).

**Why now.** 03 and 03r found that N2's random, unevolved brains show more history dependence (P4)
than shuffled graphs, borderline in 03 and replicated in 03r (D080). The roadmap's Track B asks where
the effect lives, whether it runs through gap junctions or chemical synapses, and what gives N2's
brains their 5 to 7 times stronger response to food. An outside review (shared by the owner,
2026-09-28) added a reading of the committed data that we checked (§Q1), and suggested cheap checks,
which this plan adopts.

**What P4 is.** For each random genome, the raw turn read-out after a food ramp that rises to a level
is compared with the read-out after a ramp that falls to the same level. P4 is the mean |rising −
falling| at the ramp's end, divided by the mean |steady contrast|, the difference between holding the
two starting levels. That denominator is the "food response" below. P4 uses the brain only, with no
world and no motor calibration.

**Code:** [`scripts/p4m.py`](../../scripts/p4m.py). It reuses 03's own code and inputs
(`scripts/exp03.py`, instance "03"): the stimulus bank, the P4 definition, and N2's 2 048 probe
genomes, drawn exactly as 03 drew them. **Every simulating command first recomputes N2's numerator
and denominator and stops unless they match 03's committed supplement to a relative 10⁻⁶.**

## Q1. The trade-off (no simulation; done)

From 03's and 03r's committed supplements (`tradeoff.json`):
- within every ensemble, in both instances, graphs whose brains respond more strongly to food have
  **lower** P4: Spearman −0.27 to −0.60;
- N2's food response is 4.7 to 7.4 times the ensemble median, and 1.5 to 2.7 times the most
  responsive graph of each ensemble;
- N2 nevertheless has the highest P4. A linear fit of P4 on log(response) within each ensemble, taken
  out to N2's response, puts N2 4.3 to 6.7 residual standard deviations above the trend, in all ten
  ensemble runs.

**Caveats:** N2's response lies beyond every ensemble's range, so the trend is extrapolated; the fit
form (linear in log response) was chosen after seeing the data; and P4 is a ratio whose numerator may
saturate through the tanh read-out, which could itself produce a negative within-ensemble trend.
**Reading, to be tested:** N2 combines a strong food response with slow, persistent dynamics, a
combination the shuffles do not produce.

## Q2. Where does it live? Neuron deletions

- N2's 2 048 probe genomes, with each neuron deleted in turn (`wormwars/deletion.py`: every edge and
  gap junction touching it, and its bias), and each bilateral pair deleted together (for example
  RIAL with RIAR). The turn and forward read-out neurons are excluded: deleting them changes the
  read-out itself.
- **Reported per deletion:** P4, its numerator and denominator, and where the pair (P4, denominator)
  falls in each of 03's ensembles (the share of graphs below it).
- **Pre-named targets** (from 02b's critical core and the outside review): RIA and AIZ; also AIY,
  AIB, RIB and RIM, which lie on the textbook sensory-to-head-steering route.
- **What would count as a lead:** a single deletion or pair that brings **both** N2's P4 and its
  response into the ensembles' range (P4 below each ensemble's 95th percentile, and the response
  below each ensemble's maximum). Deletions that remove the food input itself (AWA, AWC, ASE) are
  expected to collapse the response and are reported but not read as leads.

## Q3. Gap junctions or chemical synapses?

- N2 with every gap junction switched off;
- N2 with only the chemical weight magnitudes permuted among the existing chemical edges, and with
  only the gap-junction magnitudes permuted (seed 1): the wiring stays, and the placement of weights
  changes by type.

## Q4. Slow relaxation or a lasting state?

- After the ramp, the final input is held for **300 ticks** instead of 5, and |rising − falling| is
  recorded every 10 ticks, for N2 and the first 16 graphs of each of 03's ensembles.
- **Reported:** the mean difference over time; the fraction left at 300 ticks; and the share of
  genomes whose difference at 300 ticks is still above 10% of its value at the ramp's end.
- **Reading:** a difference decaying toward zero is slow relaxation; a share that persists points to
  multiple stable states. Neuron time constants are 0.5-20 ticks, so 300 ticks is 15 or more of the
  slowest.

## Q5. Wiring or weight placement?

- N2's own wiring with its anatomical weight magnitudes permuted among its edges, **64 permutations**
  (seeds 100-163; 03 used seeds 1-3 and 03r 4-6, as N2perm graphs).
- **Reported:** the distribution of P4 and of the response, against N2's and the ensembles'.
- **The outside review's hint, to be tested:** in five of 03's and 03r's six N2perm graphs the
  response fell to about the null median while P4 stayed at 0.86-0.92, which would mean the wiring
  drives the persistence and weight placement drives the response size.

## Not in this plan

- Whether the effect holds for inputs other than food (the roadmap's fourth question): it needs a
  stimulus bank for another channel; left for the confirmatory design.
- Any evolved brain.

## Compute and execution

- **After 04a's evaluation,** on the RTX 5080: 04a is running, and this must not slow it or share its
  cap. P4 needs no world, so the whole plan is small: by 03's timing, the history probe is a small
  part of 111 s per graph. Estimated under 1 GPU-hour; **capped at 3 GPU-hours**, counted by the
  accounting (`runs/p4m/compute.json`).
- A smoke mode (tiny sizes, the CPU, `runs/p4m-smoke/`) exercises every command.
- Outputs are committed in this folder: `tradeoff.json`, `lesions.json`, `synapses.json`,
  `decay.json`, `weights.json`, each carrying the reproduction check.

## What this cannot establish

- A mechanism in the causal sense beyond "this deletion or change moves N2's numbers": the brains are
  random, unevolved, and the read-out is a hand-chosen interface;
- anything about behaviour: P4 is a probe of the brain alone;
- confirmatory claims: every comparison here was chosen with 03's and 03r's data in view.
