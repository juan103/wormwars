You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

This is not a review. It is the first, "divergent" round of a brainstorm, and in this round wild ideas are wanted.
Nothing you say here will be criticised in this round, and you will not see anyone else's ideas until it ends.

## The question

Why does the history difference in N2's random brains decay more slowly than in shuffled graphs' brains?

## The facts

The repository is WormWars (your working directory, read-only). Its brains are rate networks on the *C. elegans*
connectome (N2) or on null graphs. Read `wormwars/brain.py` for the equation:

    tau_j dv_j/dt = -v_j + b_j + sum_i W[i,j] tanh(v_i) + sum_i G[i,j] (v_i - v_j) + I_j

**In a random, unevolved brain, only three things are specific to N2:**
- its topology;
- its anatomical chemical magnitudes;
- its anatomical gap-junction magnitudes.

Signs, time constants (log-uniform per neuron) and biases are drawn at random for each genome (`Genome.random` in
`brain.py`). The null ensembles are degree-preserving shuffles with extra constraints; see
`wormwars/exp03/samplers.py` (SH, SH-route, SH-class, SH-mirror, SH-recip).

**P4** is a history-dependence measure. After a food signal ramps up or down to the same final level, how much
does the turn read-out still differ? It is that difference divided by how strongly the read-out separates two
held levels. The probe is in `wormwars/exp03/twin.py`; the statistics are in `mc.py` and `mc_report.py`.

N2's P4 is distinctive against every ensemble, in three studies (03, 03r, 03mc). The mechanism studies are
`experiments/03m-p4-mechanism/RESULTS.md` (exploratory) and `experiments/03mc-p4-confirm/RESULTS.md`
(confirmatory). Their findings:
- **Relaxation:** N2 keeps 0.436 of its history difference 30 ticks after the ramp; the ensembles' medians are
  0.255 to 0.291.
  - At ticks 10, 50, 100 and 300, N2 keeps 0.77, 0.27, 0.13 and 0.09, against medians of 0.62-0.67, 0.11-0.13,
    0.02-0.03 and 0.001-0.009.
  - 43 of N2's 1 977 genomes keep more than 10% at tick 300.
- **Gap junctions:** switching them off raises P4 everywhere, but less in N2 (+0.02) than in the nulls (+0.07 to
  +0.10).
- **RIA and AIY:** deleting either pair cuts N2's response by 50-61%, and the history numerator by about the same
  amount, so P4 barely moves. No null graph comes close to those cuts.
- **Weight placement:** N2's response is far above that of permutations of its own weight magnitudes, but the
  permutations keep about half of N2's excess P4.
- **The read-out's tanh slope:** N2's turn read-out neurons are at a mean slope of 0.44; the ensembles' medians are
  0.73-0.74.
- **Not established:** a mechanism, stable states, or whether any deletion removes the elevated P4.

The per-tick retention curves are committed in `experiments/03mc-p4-confirm/report.json` (`descriptive.curves`).

## What I want from you

At least 12 ideas for what could make the decay slower in N2.
- **Be daring.** Borrow concepts from far-away fields (physics, engineering, chemistry, ecology, economics,
  epidemiology, music, materials, anything), and tools built for some other purpose.
- **Do not self-censor.** Include at least three ideas you think are probably wrong but would be remarkable if
  true, and mark them as such.
- **Plain ideas are welcome too,** but no more than a third of the list.

For each idea, give:
1. a short name, and the field it borrows from;
2. the claim, in plain words: what in N2 makes the trace last;
3. what we would see if it is true;
4. **the cheapest check that could kill it.** Prefer the committed data, or a CPU computation of an hour or less.
   Name the files or code you would use;
5. one line on why it might matter if it is true.

You may read the repository to make your ideas concrete or to check a fact, but do not spend this round finding
fault with your own ideas. Do not edit files or run anything. Finish with the three ideas you would most like to see
given a real chance, and why.
