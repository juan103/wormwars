# M6, behaviour: options, rough costs and the likely size of each answer

*Draft 2, 2026-10-29, for the owner, before any plan (D374; the synthesis's lesson "scope cost against benefit early").
Draft 1 and one round of review by Astra 6 and Fable 5.1 (both recommend option 0, with fixes) are in
[`docs/reviews/20261029-m6-options/`](../reviews/20261029-m6-options/). Exploratory. Nothing here has run except a
throwaway timing of T1 on the CPU.*

## The question

Does a brain with history-dependent switches use them in a task that needs memory? M1 to M4e found that a few random
genomes hold the food probe's history in two stable states, that N2's head-core block makes them more common, and
that in N2 they are fragile at RIA. None of that touched behaviour (SYNTHESIS, "What it does not show").

**What the repository already has:**
- **A task where memory pays a scripted controller:** 02's T1 (single-nose foraging, a swarm of 20 sharing food, 400
  ticks). A scripted controller gains +0.985 from memory, and a "the food fell" bit replaces 98% of that (03h). That
  shows memory pays within those controller families, not that T1 requires it (Astra).
- **03h's lesson:** in random brains the bit entered through ASKL and ASKR, which have no direct read-out, and its
  average effect was small. A relief must reach the read-out, and a power rule must be fixed before any data.
- **Selection already built a history effect on this probe (02b; Fable, Astra).** On the same 0.25/1.75 food ramp,
  02's generation-39 T1 champions' turning differs by history far more than at generation 0 or under a mutation-only
  drift control: 0.281 against 0.104 and 0.097 (N2), 0.158 against 0.035 and 0.045 (SH). It is 0.90 to 0.95 of the
  steady-state difference and 0.83 to 0.87 of it survives five more ticks: a slow or persistent memory of level. T0's
  champions show it too, so it is not specific to T1 (`experiments/02b-champion-analysis/RESULTS.md`, section 2).
  Whether it is a switch or slow fading is open. *Draft 1 said instead that D038's history ablation made switches
  likely rare; that ablation was jitter 1, which D039 says cannot detect an integrating controller (Fable).*
- **02's evolved genomes, locally** (`runs/exp02-screening/`, untracked): the best genome of each run at generations 0
  and 39 for T1 under four food mappings (M0, MS, R1, R2): 102 generation-39 champions (32 N2, 64 on eight shuffles, 6
  on three weight permutations of N2, under M0 only), 102 generation-0 champions, and four T1 generation-79 snapshots.
  The generation-0 champions are each run's best of 32 random genomes, selected, not random genomes and not
  ancestors of the generation-39 champions in any particular sense.
- **Costs on the CPU:** T1 about 0.14 s per genome per world (a throwaway timing, not in any file; consistent with the
  GPU's 167 genome-worlds per second at a 20 to 25× penalty, Fable). M2's classifier about 1.4 s per genome with M4e's
  selective second pass; the 22,000-tick pass itself costs about 75 s per genome it processes.

## The options

| | What it asks | Rough cost | Likely size of the answer |
|---|---|---|---|
| **0. Classify 02's champions** | Is the history effect selection built (02b) a switch or slow fading? Classify every T1 champion (generations 0, 39 and 79) and a mutation-only drift control, within each mapping and graph | about 1 CPU hour; up to about 5 if every champion needs the long pass | descriptive, readable only coarsely: with 38 N2 champions and N2's 1.5% random rate, only a rate above roughly 10% separates from noise; on the shuffles, whose random rate is near 0.1%, three or more switches would already be notable (Fable). It decides whether 2 or 5 is worth paying for |
| **5. A small causal study within genomes** (new, Astra) | In already-classified switch genomes: do T1's own histories set the switch, and does erasing or swapping its state during the task change performance, against sham and rescue controls? | small (CPU hours), but the intervention needs validation; a design item after option 0 | the most direct test of use of the six; a null would close this probe's switch route, not useful memory in general |
| **1. Generation-0 association** | Do switch genomes forage better on T1 than fading genomes of the same graph? | about 1 to 3 CPU hours: the classes are already in the census and M4c's records, so only the switches and a matched fading sample need T1 rollouts (Fable) | a null is the expected answer and would not show switches useless: a switch set by the probe has no reason to be aligned with anything useful (Fable); 03h's step 0 measured a different, continuous history measure, not switch membership (Astra). At most a side panel to option 0 |
| **2. Evolution with memory needed or relieved** | Does needing memory change how often evolution builds switches? | about 150 CPU hours for 32 short runs (population 256, 8 worlds, about 60 generations), or about 6.5 GPU-hours with the owner's word; plus building and gating a relief that reaches the read-out (it does not exist yet), a design, a plan and, if confirmatory, a pre-registration | unknown. Its unit is the run, so each run's final population must be classified (about 3 more CPU hours). It tests whether training conditions change switch prevalence, not that switches supply useful memory (Astra). Hold it unless option 0 finds a switch rate clearly above drift (Fable) |
| **3. Biology** | Do the real worm's RIA, RMD and SMD neurons, a documented head-steering circuit, show anything comparable? | no compute; a literature review to the project's standard (verified, not a model session with snippets) | it would say whether the model's switch resembles anything the worm is known to do |
| **4. Stop the thread here** | Turn to another roadmap item, for example the owner's v2.2 question (worm-like tasks under worm-like plasticity) | none | the thread's answer stands as the synthesis gives it |

## Recommendation

**Claude, Astra and Fable agree: option 0 first.** Then, if champions turn out to be switches clearly more often than
drift, option 5 (Astra) or option 2 (Fable); if they do not, the evolved memory is slow fading, this probe's switch
route looks closed for the compute side, and option 3 or 4 is the honest next step. A negative count closes this
probe's switch route only, not useful memory in general: fading dynamics, or switches under other inputs, could
still matter (Astra).

**What option 0 fixes before it runs** (a short plan, reviewed):
1. **Every T1 champion**, generations 0, 39 and 79, reported by mapping and by N2, shuffles and permutations; nothing
   selected after looking.
2. **A drift control:** each generation-0 champion mutated 39 times with the run's settings and no selection, 4
   replicates, as in 02b (about 10 CPU minutes), classified the same way. Without it a change across evolution could
   be drift: mutation grows the weights, and M4e showed the switch rate depends on how concentrated they are.
3. **Comparisons within mapping and graph** (generation 39 against generation 0 and drift); N2's 1.5% applies to N2
   under M0 and among eligible genomes only, so no pooled baseline. M4d's convention: no eligibility floor.
4. **The interface threaded through the classifier:** the probe now hard-codes M0 (`scripts/memory_m1/common.py`).
   Each champion runs under its own mapping's interface, bank and saved configuration and gains, a code change with a
   test.
5. **The unresolved genomes planned:** evolved genomes with grown weights may oscillate or stall more often than the
   random genomes the classifier was validated on. The second pass covers genomes not fading on the first pass, and
   the wording for "mostly unresolved" is fixed first.
6. **No root-start test in T1:** starting a champion in each root tests sensitivity to the initial state, not use
   (both). Instead, whether the full state visits both roots' neighbourhoods during a T1 replay, as a description;
   the use test proper is option 5's.
7. **Read beside 02b:** each champion's class next to its 02b history magnitude.
