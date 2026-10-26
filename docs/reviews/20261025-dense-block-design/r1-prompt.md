# Design round 1: what does a dense block carry? (the memory thread's next study)

You reviewed every step of the memory thread (M1 to M4d; D349-D364). After M4d the owner chose, in this order: the
M1 to M4 write-up (now in review, `docs/memory/SYNTHESIS.md`), then **"A study of what a dense block carries, its size,
weights and degrees"**, then an M5 test of N2's exact wiring after a power calculation (D365, which quotes the
owner). This round is about the second: please propose and criticise its design before anything is written or run.
Read-only. The scientific direction is the owner's; the design is ours to agree.

## What M4d left (`docs/memory/M4D-RESULTS.md`, `runs/memory-m4d/`)

Ten fresh null hosts (two per ensemble), 1024 paired genomes per host, every genome classified by M2's frozen
classifier at 2000 ticks with no floor. Separate-states genomes of 10,240 per arm (unresolved in brackets):
I (host's own block, 94-127 edges, weight 466-861) 4 (0); D (N2's 260 edges, weights and 8 autapses at random
positions) 24 (43); R (rewired at N2's in/out-degrees and out-strengths) 52 (36); Rr (R keeping N2's 75 reciprocal
pairs) 32 (36); P (N2's edges, weights shuffled) 69 (41); T (N2's block) 64 (50); T+G 50 (50). Robust over every
assignment of the unresolved: T-I, R-I, D-I > 0; R-D on counted genomes only (envelope -0.0043 to 0.0090). The
genomes that switch differ almost completely between arms (one shared per pair of T, P, R). Not-settled genomes
gather in T and T+G. The hosts' base rate (0.04%) was a third of the 0.12% M4d's plan assumed.

So the block's count, weight and degrees appear to carry the effect, but the D-I contrast changes the count, the
total weight, the weight distribution, the topology and the autapses at once, and R-D adds N2's degree sequence and
out-strengths together.

## Questions

1. **The estimand.** What should this study establish, in a sentence a reader of `main` would understand? Candidates:
   (a) which block property (edge count, total weight, weight concentration, degree heterogeneity, reciprocity,
   autapses) raises the switch rate, separately; (b) a dose-response: does the switch rate follow one summary of the
   block (for example its summed weight, or the spectral radius or largest real eigenvalue of its scaled weight
   matrix), whatever produced it; (c) whether location matters: the same dense block placed on 30 neurons away from
   the turn read-out, observed independently, against C3's neurons. Which, and in what priority? Is something better?
2. **The arms.** Propose a concrete arm set for the first stage. For instance a factorial on C3's neurons: count
   {host's own, 260} × weights {host multiset, N2 multiset} × placement {uniform random, N2's degree sequence}, with
   D-type blocks scaled by a global gain {0.5, 1, 1.5, 2} as a dose-response; or something smaller. Which controls are
   essential, and which should wait?
3. **Not N2's numbers.** Arms that do not use N2's edges at all (synthetic heavy-tailed weights, synthetic degree
   sequences) would ask whether density per se does it, generically. Should the first stage include them?
4. **The unresolved genomes.** M4d's reading turned on them. Propose a pre-specified treatment (a second, longer
   classification of every arm's unresolved genomes; a different horizon; counting them in the estimand), and its
   cost.
5. **The reading and the margin.** Hosts as the unit again? The margin against the observed base rate? A regression
   across arms (switch rate on block summaries, host random effect) as the primary, or paired contrasts?
6. **Cost and scale.** On this CPU a 1024-genome panel costs about 1100 s (M4d: 70 panels in 25 h). Propose the number
   of hosts, genomes and arms, and a cap. A GPU run would need the owner's word; say if the design needs it.
7. **How it feeds M5.** What result here would change M5's design (for example, if one summary explains the switch
   rate, M5's controls must match it), and what would make M5 unnecessary?

Give a concrete proposal and rank your concerns. Disagree with the framing if it is wrong.
