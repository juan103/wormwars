# M6, behaviour: options, rough costs and the likely size of each answer

*Draft 1, 2026-10-29, for the owner, before any plan (D374; the synthesis's lesson "scope cost against benefit early").
Exploratory. Nothing here has run except a throwaway timing of T1 on the CPU, below.*

## The question

Does a brain with history-dependent switches use them in a task that needs memory? M1 to M4e found that a few random
genomes hold the food probe's history in two stable states, that N2's head-core block makes them more common, and
that in N2 they are fragile at RIA. None of that touched behaviour (SYNTHESIS, "What it does not show").

**What the repository already has:**
- **A task where memory pays:** 02's T1 (single-nose foraging, a swarm of 20 sharing food). A scripted controller gains
  +0.985 from memory; a "the food fell" bit replaces 98% of that (03h).
- **03h's lesson:** in random brains the bit entered through ASKL and ASKR, which have no direct read-out, and its
  average effect was about 0.5% of the selected deciles' scores. A relief must reach the read-out, and a power rule
  must be fixed before any data.
- **The probe's food channel is T1's** (03h's design): the history M2's classifier reads is a food history in T1's
  own input bank.
- **Evolved T1 brains already exist, locally:** 02 saved each run's best genome at generations 0 and 39 (and 79 for
  two runs) for every cell: T1 under four food mappings (M0, MS, R1, R2), on N2 (8 runs per mapping), eight shuffles
  (SH1 to SH8; 2 runs each) and three weight permutations of N2 (2 runs each). That is about 100 generation-39 T1
  champions and their generation-0 starts (`runs/exp02-screening/`, untracked; `.npz` with `allow_pickle=False`).
- **The CPU cost of T1:** about 0.14 s per genome per world (a throwaway timing, 16 and 64 genomes × 4 worlds on
  `pilotSH101`, 8 threads). M2's classifier cost about 1.4 s per genome in M4e, both passes included.

## The options

| | What it asks | Rough cost | Likely size of the answer |
|---|---|---|---|
| **0. Classify 02's champions** | Did 40 generations of selection on T1 produce switch champions more often than generation 0 (about 1.5% of N2's random genomes)? For any champion with separate states: start it in each state and compare its T1 score and turning | under 1 CPU hour; no new evolution | descriptive, about 100 champions. 02's pilot champion beat the memoryless controller without being hurt by the history ablation (D038), so switches may be rare. Either way it sizes options 1 and 2 |
| **1. Generation-0 association** | In graphs rich in switches (03mc's selected graphs, 12 to 78 each per 1000; N2, about 15; M4e's T hosts), do switch genomes forage better on T1 than fading genomes of the same graph? | about 5 to 10 CPU hours (about 160,000 genome-worlds, plus reusing or redoing the classification) | probably small: 03h's step 0 found the size of the history held had a near-zero mean association with T1 fitness on 16 SH graphs (its direction a weak positive one). With dozens to a few hundred switch genomes, only a large difference would be detected |
| **2. Evolution with memory needed or relieved** | Does needing memory make evolution recruit switches? Evolve on T1 with and without a relief that reaches the read-out, then classify the champions | about 150 CPU hours for 32 short runs (population 256, 8 worlds, about 60 generations), or a few GPU hours with the owner's word; plus a design, a plan and, if confirmatory, a pre-registration | unknown; the most direct test of "use". Option 0 would give the first estimate of the base rate it needs |
| **3. Biology** | Do the real worm's RMD and SMD neurons show anything comparable? | no compute; a literature review to the project's standard (a proper deep research, verified, not a model session with snippets) | unknown; it would say whether the model's switch resembles anything the worm is known to do |
| **4. Stop the thread here** | Turn to another roadmap item, for example the owner's v2.2 question (worm-like tasks under worm-like plasticity) | none | the thread's answer stands as the synthesis gives it |

## Recommendation (Claude)

Option 0 first. It costs under a CPU hour, uses genomes that already exist, and its answer decides whether 1 or 2 is
worth paying for: if 02's T1 champions are switches far more often than random genomes, option 2 becomes the main
question; if they are not, option 1 or stopping looks better.

What option 0 would fix before it runs (a short plan, reviewed): which champions (every T1 generation-39 champion and
its generation-0 start, nothing selected after looking), the classifier and probe each champion is classified with
(its own food mapping's interface, T1's bank, M2's rules and 22,000-tick second pass), the comparison (the share of
switch champions against generation 0's starts and against each graph's random genomes), and the state test's
measure. It is descriptive: about 100 champions from 40-generation runs cannot carry a confirmatory claim.
