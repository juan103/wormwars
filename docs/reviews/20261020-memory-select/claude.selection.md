# Claude's selection, written before reading Astra's and Fable's (round 3)

Written after sending the prompt and before either answer came back, so that the three selections are independent.

## Verdicts

| Family | Verdict | Evidence |
|---|---|---|
| 1. Feedback pays the leak (slow modes, ring and line attractors) | **wounded** | The spectral radius distribution is the same in N2 and three nulls (batch 3), so there is no N2-wide slow mode. Alive only in the tail: 5.1% of N2 genomes have a radius above 1, against 0 to 0.8%, and 11.5% of 03mc's N2 genomes grow. A local slow mode on the core is not ruled out: batch 3 looked at the whole spectrum, not the core's block. Kill-check: the core block's leading eigenvalue in core-frozen shuffles vs hub-frozen shuffles. |
| 2. Chains and transient growth | **wounded, near dead** | Henrici non-normality and 10-tick state growth are the same as the nulls' (batch 3). |
| 3. Reservoirs | **dead as the cause** | The pharynx keeps its own difference longest (batch 4), but erasing it changes nothing. A reservoir that never returns is not memory the read-out can use. |
| 4. Switched routes | **untested** | Nothing tested it directly. Low priority: the linear forecast tracks the per-genome retention (Spearman 0.58 in N2), which leaves little room for a switching story. |
| 5. Saturation | **wounded** | The linear forecast at the ramp's end gets the median about right (0.26 vs 0.24 observed). Saturation may still shape the tail. |
| 6. Gap geometry and fitting layers | **wounded but alive** | The chemical layer carries the effect (batch 1's factorial). Gaps shorten memory in every graph, and N2's own gaps cost it less than a shuffle's (0.469 vs 0.413). That is a second-order effect, one graph per arm. |
| 7. Time-constant lottery | **dead** | No neuron's tau predicts retention beyond \|rho\| 0.10 (batch 4). |
| 8. Mixtures and heavy tails | **alive, and part of the answer** | The median genome is ordinary; the amplitude-weighted tail is not (check_mixture). |
| 9. Read-out geometry | **reshaped** | Not "the read-out happens to be aligned": the turn-over-everything ratio is in the null range (batch 6). What is real is that the slowest-decaying large differences sit on a core that includes the read-out. |
| 10. Phase memory | **dead** | Sign flips show no N2 excess. |
| 11. Preparation | **dead** | Warm-up from 25 to 400 ticks barely moves anything. |
| 12. The probe's regime | **dead at this probe** | Food from ×0.5 to ×2 barely moves anything. Untested at other ramp shapes. |
| 13. Bilateral sectors | **untested** | The core is bilateral (L/R pairs of RIA, RMD, SMD, AIB, AIZ, RIM), so sectors may come back inside the core. |
| Integrator artefact (Fable) | **dead** | Substeps 16 and 32 give identical results. |
| Triangles (Claude, Fable) | **dead as a count, alive through the core** | Raising shuffles to N2's counts does nothing (batch 2). Triangle-held shams keep retention only because they keep the core (batch 5, sham_core). The core-frozen shuffle keeps retention with null-level counts (batch 7). |
| Owner's trapped waves in loops | **alive in a narrower form** | The loops that matter are inside the head core, not loops in general. |
| Owner's transplant | **the right next experiment** | The core-frozen shuffle is already half a transplant: N2's core in an otherwise random graph keeps most of the retention, and a hub core with as many edges does not. |

## What I think the answer is shaping up to be

N2's brains do not forget more slowly in general. The whole state decays at the same typical rate. A head-motor core
around the turn read-out (RIA, RIM, AIB, AIZ, RMD, SMD and a few others) does three things:
- it receives the largest part of the ramp's difference;
- it keeps it longer in the genomes where the difference is large;
- it delivers it to the read-out.

Its internal wiring is enough to carry most of N2's lead into an otherwise shuffled graph.

## The weaknesses I see in my own reading

- **The core was chosen with genome data** from N2 brains (top 30 by start difference on seed 7100). Choosing it
  from the anatomy alone, without any brain run, would remove the circularity.
- **Dissolving the core costs only part of the lead** (0.36 against about 0.25 for nulls), so something outside the core's internal edges also matters. The core's input edges are the first suspect.
- **One fixed definition:** 30 neurons, one list. A dose-response over core size and membership is missing.
- **No mechanism yet:** "the core" is a place, not a mechanism. Why does this core keep large differences? Family 1
  (a local slow mode in the core block), the core's gap junctions (family 6), and its bilateral structure (13) are the
  candidate mechanisms, in that order.
- **Noisy panels:** N2's own share moves from 0.469 to 0.396 between panels, so effects under about 0.05 need more panels or graphs.

## The roadmap I would propose (before reading the others)

1. **Freeze the finding** (CPU, exploratory, about 2 hours):
   - define the core from the anatomy alone, without brain runs: for example the neurons within two synapses of the turn read-out, ranked by internal density;
   - rerun core-frozen and hub-frozen shuffles with 10 graphs each, on two panels.
2. **Mechanism inside the core** (CPU, exploratory):
   - the core block's spectrum vs a hub block's;
   - the core's gap junctions on and off;
   - left-right symmetry broken inside the core.
3. **The transplant** (CPU first; then pre-registered, perhaps on the GPU at 03mc's scale):
   - put N2's core wiring into graphs from each 03mc ensemble;
   - put it on a different set of 30 neurons away from the read-out, to see whether memory follows the core or the read-out;
   - remove it from N2.

   This one deserves a pre-registration, because it is the confirmatory test of the answer.
4. **The split measure:** report the typical genome (median) and the amplitude-weighted tail separately, and say which one the answer explains.
