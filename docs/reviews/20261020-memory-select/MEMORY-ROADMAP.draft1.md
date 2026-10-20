<!-- Archived 2026-10-20: draft 1 of docs/memory/MEMORY-ROADMAP.md, the text both round-1 roadmap reviews quote. It was
never committed; restored verbatim from the session in which Claude wrote it (D346). -->
# Why does N2's history difference decay more slowly? A roadmap

*Draft 1, 20 October 2026. Written by Claude as the master of ceremonies of a three-round brainstorm. The rounds and the
selection are archived in `docs/reviews/20261020-memory-{diverge,build,select}/`. A living plan, not a
pre-registration. Everything below "What the ceremony found" is exploratory.*

## The question

03mc found that N2's random brains keep 0.436 of their history difference 30 ticks after the ramp, against null
ensemble medians of 0.255 to 0.291 (Q-D, registered). The owner asked why, and wanted to answer it with a
different kind of ceremony: first a blind, divergent round ("a bit of crazy ones"), then building on each other's
ideas, then a critical, honest selection.

## How the ceremony ran

| Round | What happened | Who |
|---|---|---|
| 1, diverge, blind | 5 sources, about 60 ideas, written without seeing each other | the owner (ring attractors, waves trapped in loops, transplanting), a ChatGPT roadmap the owner supplied, Claude (13), Fable 5.1 (17), Astra 6 (18) |
| 2, build | 13 mechanism families, hybrids, new ideas, and the cheap experiments that would split the families | Fable, Astra |
| Between 2 and 3 | 8 batches of cheap CPU checks, chosen from round 2's experiments (`scripts/memory_spikes/`, outputs in `runs/memory-spikes/`) | Claude |
| 3, select | A verdict for every family. Astra advocated the dynamical families and Fable the structural ones. Both prosecuted Claude's leading reading. Each proposed a roadmap and one crazy idea. Claude wrote its own selection before reading theirs. | Fable, Astra, Claude |
| After 3 | Both crazy ideas checked within the hour (batch 8) | Claude |

## What the ceremony found (exploratory)

All numbers are from fresh CPU panels, mostly one graph per null ensemble, and graphs within an ensemble differ a
lot. N2's own share moves between panels: 0.469, 0.396 and 0.504 on three panels. Treat them as leads.

1. **The typical N2 brain does not forget more slowly.**
   - Its median per-genome retention is ordinary: 17 to 46 of 128 graphs per ensemble are at or above it.
   - The whole-state difference decays at the same median rate as in the nulls: 0.197 against 0.192 and 0.200.
   - What is extreme is the registered, amplitude-weighted share. It is driven by N2's upper quarter of genomes.
   - In N2, the genomes with large differences lose less of them: the amplitude-retention correlation is −0.13, against −0.39 to −0.42.
   - A more accurate sentence than "decays more slowly" is Astra's: **N2 retains a larger amplitude-weighted fraction of its turn-history signal.**
2. **A minority of N2 brains latch** (batch 8, 512 genomes; the result most worth checking first):
   - in 4.1% of N2 genomes, the network is unstable at the midpoint between the two histories' end states, but stable at each history's own end state. That is a saddle between two stable states;
   - every N2 genome whose difference stays at full size to tick 300 is one of these;
   - these 4% carry 39% of the tick-30 signal;
   - their unstable direction lies 92% on a 30-neuron head core and 67% on RMD and SMD alone (uniform: 10% and 3%);
   - it is almost never oscillatory: 9.5% of these leading eigenvalues are complex;
   - so it is a latch, a flip-flop in the head-motor neurons, not an oscillator.
   - In comparison: one shuffle (SH-2010000) has none. The high-retention null SH-class-2030000 has latches too (1.8%), but they sit mostly elsewhere: 33% on the core.
3. **The structure that matters is a head core, not triangle counts:**
   - **triangle counts don't transfer.** Raising shuffles to N2's triangle counts did nothing (batch 2).
   - **N2's core is enough in a shuffled graph.** N2 with 73% of its edges shuffled, but its head core's 199 internal edges frozen, kept N2's retention (mean 0.482 over six graph-panel pairs), with null-level triangle counts. Freezing a hub set with as many internal edges did not (0.343). This is batch 7.
   - **Dissolving the core costs part of the lead.** It took 70% of the core's internal edges with 140 swaps and gave 0.363; scrambling the periphery as much gave 0.454.
   - **The core's members:** RIA, RIM, RIB, AIB, AIZ, AIY, RMD, SMD, SMB, SIA, SIB, AVE, and some of the AWC and AWA sensory neurons.
4. **Ruled out or weakened, each for the specific version tested:**

   | Idea | Verdict | Evidence |
   |---|---|---|
   | a numerical artefact | dead | 16 substeps against the baseline 32 give the same result |
   | warm-up length | dead | 25 to 400 ticks |
   | food level | dead | × 0.5 and × 2 |
   | a time-constant lottery | dead in its marginal form | no neuron's tau or bias predicts retention beyond \|rho\| 0.10; tau interactions are untested (Astra) |
   | a pharyngeal reservoir | dead | the pharynx keeps its own difference longest, but erasing it changes nothing |
   | a network-wide slow mode or transient growth | weakened | spectra and non-normality as in the nulls |
   | the eight read-out neurons as the store | weakened | erased, the signal regrows from the rest of the core |
   | gap junctions | a modifier, not the cause | the chemical layer carries the effect, and gap junctions shorten memory in every graph tested |
   | Fable's oscillator idea | dead as stated | the unstable modes are real, not complex |

5. **Weaknesses the reviewers found in this reading, all accepted:**
   - **Circularity.** The core was chosen from brain data: the 30 neurons with the largest start difference. Only the hub control and the dissolution contrast are non-tautological (Fable).
   - **Writing, holding and reading are not separated.** The core contains the write path into the read-out as well as the read-out, so "the core stores" is not shown. A strong feed-forward pipe into slow neurons could look similar outside the latching minority (Fable, Astra).
   - **Response amplitude is untested.** N2's response is about five times a null's, and the dynamics are nonlinear (Fable).
   - **Erasures conflate where the difference was with how much was erased.** Controls should match the erased norm (Astra).
   - **The spike rewirings are not 03's samplers:** they keep N2's 38 autapses and carry each weight with its edge. Comparisons inside a batch are fair; comparisons with 03mc's ensembles are not (Fable).
   - **Frozen is not exact.** Freezing protects the core's edges but allows new ones. Genomes are drawn per graph, so the same seed does not give the same signed brain (Astra).
   - **Dissolution changes two things at once:** it removes internal edges and adds boundary edges (Astra).
   - **Two numbers lacked a committed source when first quoted.** The 03mc-panel extrapolation (now regenerated in `check_structure.txt`) and the substeps description (corrected above).

## What the owner's ideas became

- **Ring attractors** narrowed to their discrete, pinned relative: a two-state latch in a minority of brains. A
  continuous ring or line would need a continuum of end states. Step M2 tests that directly.
- **Waves trapped in loops:** loops in general (triangle counts) are out. Loops inside the head core are alive, and
  step M4 separates their wiring from their density.
- **Transplanting** is step M5. The core-frozen shuffle was already half a transplant, and it worked.

## The roadmap

Two decision points can change the plan: M1's amplitude arm and M3's predictor. All steps up to M4 are exploratory and
run on the CPU. M5 is the confirmatory one.

**M1. Settle the measure and the amplitude** (CPU, about 2 hours; exploratory; Fable step 1, Astra step 1).
- **Population accounting on 03mc's arrays** (seconds). Astra's decomposition:
  - the registered share = mean per-genome retention + cov(amplitude, retention) / mean amplitude;
  - the same split within amplitude strata;
  - how far the tick-30 and tick-300 contributors overlap;
  - the nulls' top 5% trimmed, as N2's was.
- **Four panels of 1024 genomes on N2 and eight null graphs,** including the highest-retention graph of each ensemble. Report three quantities with panel standard errors:
  - typical retention: the median, among genomes with a non-trivial start;
  - the latch fraction;
  - the registered ratio of means.
- **The amplitude arm:** scale the ramp-end difference by 0.25, 0.5 and 2 around the midpoint.
- **Changes the plan if:** N2 falls to the nulls' level at small amplitude. The question then becomes the size of the response (03mc's Q-B and Q-C territory), and M4 and M5 are redesigned around it.

**M2. The latch census** (CPU, 1 to 2 hours; exploratory; Astra steps 2 and 3, Fable step 2).
- **Several graphs per ensemble, several panels.** Classify every genome as latched, fading or oscillating, with the Jacobian at both histories' end states and at the midpoint. Find where the unstable direction lies.
- **Discrete or continuous?**
  - Write a family of histories (ramp starts between 0.25 and 1.75 of the final level) and see whether the end states cluster into two or form a continuum.
  - Check that a latched state survives small perturbations.
- **Batch 7's graphs:** do core-frozen shuffles keep the latch fraction and its location while hub-frozen shuffles lose it?
- **The split:** how much of N2's lead is latches, and how much is graded slower fading in large-amplitude genomes.
- **Changes the plan if:** latches explain little of the lead. The graded part then becomes the main target, with saturation and gap damping as its candidates.

**M3. A definition that does not use the result** (CPU, under an hour; exploratory; Fable step 3).
- **Define the core from the anatomy alone,** for example the turn read-out's two-step in-neighbourhood ranked by internal density. Compute it and a write-read path measure for all 640 03mc graphs, and correlate within ensembles with the upper quartile and the latch fraction.
- **Look at what the 2 to 5 high-retention null graphs per ensemble share** (Fable).
- **Changes the plan if:** the within-ensemble correlation is under 0.2. The core is then an N2 fact with no structural handle, and M5 waits.

**M4. Take the core apart: write, hold, read** (CPU, 2 to 4 hours; exploratory; Astra step 3, Fable step 4).
- **Branch identical saved states, and intervene only during the hold:**
  - cut core edges or switch gap junctions off;
  - erase with controls matched for erased norm;
  - re-inject the proposed latch coordinate to rescue a disrupted trace (Astra).
- **Core-frozen shuffles with one change each:**
  - internal edges rewired within the core at fixed degrees;
  - internal weights permuted;
  - reciprocal pairs broken;
  - only the sensory half frozen, or only the motor half;
  - the boundary edges rewired.

  All of these run under 03's sampler conventions as well as the spikes'.
- **The cheap kills left open in round 3:**
  - the tau-permutation and equal-tau controls (Astra);
  - the gap dissipation ratio (Fable);
  - the antisymmetric (left-right) share (Fable);
  - complement erasure: everything outside the core (Fable).
- **Output:** the smallest structure whose freezing keeps the latch and the lead, which is the "module" to transplant.

**M5. The transplant, pre-registered** (the owner's idea; CPU screen, then the confirmatory run, perhaps on the GPU with the owner's word; Fable step 5, Astra steps 4 and 5).
- **Hosts and controls:**
  - put M4's module into independently generated hosts from each ensemble's own sampler, with a hub set and an internally rewired copy as matched controls;
  - remove it from N2;
  - vary whether N2's gap junctions and autapses come with it;
  - place it at the read-out and also away from it, to see whether memory follows the module or needs the read-out's access.
- **Before the run:** fix the primary measure, the thresholds and the wording, and commit and push them (Fable's draft thresholds are a starting point: share30 from about 0.25 to at least 0.40, latch fraction from under 1% to at least 3%, the controls moving neither).
- **Cost:** benchmark first.
- **A failure in foreign hosts** would mean the core needs N2's surroundings, which is itself an answer.

**M6. Then behaviour and biology** (not scheduled).
- **Behaviour:** does a latching brain use its latch on the memory-task track? 03h's lessons apply: a relief through a channel the read-out can see, and a power rule fixed in advance.
- **Biology:** whether the real worm's RMD and SMD neurons show anything comparable is a literature question. It has to meet the project's literature standard before anything is designed on it.

## Contributions

- **The owner:** the question, the ceremony's format, three of round 1's ideas (two survive in a narrower form, one became M5), and the ChatGPT roadmap (its integrator check, M0, ran first and ruled the artefact out).
- **Fable 5.1:**
  - in round 2, the discriminating experiments that most spikes came from;
  - in round 3, the sampler-convention and substeps corrections, the amplitude objection, the predictor test (M3), the core dissection (M4) and the oscillator idea that batch 8 then ruled out.
- **Astra 6:**
  - in round 3, the decomposition of the registered measure, the saddle reading of the midpoint Jacobian (borne out by batch 8), and the separation of write, hold and read;
  - the matched-norm erasure objection, and the bookkeeping catches (the missing extrapolation output, the trim definition);
  - the latch idea that batch 8 then supported.
- **Claude:** ran the ceremony and the eight spike batches, the core reading, and this draft.
