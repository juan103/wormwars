You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Consultation: E4's pilot attempt 1 shows the GA does not move off E-G. How should E4 proceed?

You are consulting on the WormWars repository (your working directory), read-only. Read
`experiments/E4-two-minds/pilot-attempt1-summary.json` (the numbers below come from it), `docs/E4/E4-DESIGN.md`
(design v3, §1 training, §2 readings, §6 pilot), and D250-D251 in `DECISIONS.md`.

**What happened.** The exploratory pilot (X0 and X+, 4 paired runs each, 100 generations, population 32, elites 3,
truncation 8, from 32 copies of E-G, T-F's mask at mutation factor 0.25 with w_sigma 0.08, tau_sigma 0.15,
bias_sigma 0.05, p_mutate 1.0, 8 training mazes per strain per generation, 6 × 6 islands, H = 1 800) stopped at its
3-hour cap in X+'s generation 80 (56 s per generation; X+ was not saved). Findings:
1. **The generation-1 load** (32 copies of E-G bred once, 4 replicates, 8 mazes): X0's population mean 1.94 visits per
   wey against E-G's ~6; X+ costs a further 0.21 at cross-link factor 0.25, 0.39 at 0.5, 0.65 at 1.0, 0.95 at 2.0,
   1.14 at 4.0. Only 0.25 meets the design's absolute bound (0.25 visits), so X+ trained at 0.25, where a neutral slot
   barely moves.
2. **X0's training does not improve on E-G.** Generation 0's population mean is 6.23. From generation 1 the
   population mean sits near 2.4-3.4 for 100 generations. The best strain of each generation (on its own 8 mazes,
   noisy) averages 6.3-6.7 in generations 0-9 and 6.3-6.9 in 90-99, per run. Only 3-19% of the final population
   reaches 5 visits. The final best strains' lineages carry 22-57 mutations over 99 breedings.

So selection holds a few elites near E-G while mutation drags almost every child far below it. If the GA cannot move
off E-G at this mutation strength, P2 (X+ − X0 after training) and "recruitment" of cross-links measure little,
whatever the cross-link factor.

**Options, as claims to attack** (not my conclusion):
- **(A) Weaker mutation of the inherited parameters** (factor 0.05-0.1, or p_mutate < 1 so each child changes a few
  parameters), with the cross-links on their own scale; the load bound re-set relative to X0's own generation-1 load.
- **(B) Freeze the modules; evolve only the 32 cross-links in X+.** X0 is then E-G itself (no training), P2 becomes
  "X+ champions against E-G", and P1 stays within X+. It isolates transfer cleanly, and every mutation goes where the
  question is, but it gives up co-evolution of modules and links.
- **(C) Keep the design, train longer** (300+ generations) and accept the load.
- **(D) Something else** (selection: more elites or larger populations; a different seed than E-G; a relative load
  bound alone).

**What I want:**
1. Your reading of the two findings. Is "the GA does not move off E-G" supported by these numbers, or is the best-of-8
   measure too noisy to say? What cheap check would settle it (CPU or a few GPU minutes)?
2. Which option, or which combination, and why. What does each cost in what E4 can conclude about transfer?
3. What the next pilot should be (sizes, G, what it must measure), given 56 s per generation at 4 runs × 32 × 8 and
   about 3 GPU-hours already spent of E4's 30.
4. Whether any of this is a scientific-direction change that the owner must decide (rather than a design detail).

**The answer I want:** a recommendation first, then numbered points. Terse; do not restate the design.
