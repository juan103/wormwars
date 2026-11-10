# Review request: E5-1's design, draft 1 (WormWars, stage 05, the hunter)

You are reviewing a research design in the repository you are running in (read-only). Please read, in this order:

1. `docs/E5/E5-1-DESIGN.md`: **the document under review** (draft 1).
2. `docs/E5/SCOPE.md` (draft 2): the stage's scope, in particular §4 (the ladder), §7 (E5-1 and the null arm), §8.
3. `experiments/E5-hunter/E5-0/RESULTS.md` (draft 2) and `experiments/E5-hunter/E5-0/summary.json`: what the CPU
   feasibility check found.
4. As needed to check claims: `docs/E4s/E4s-1-DESIGN.md` and `experiments/E4s-stereo-module/E4s-1/` (the graft's
   evolution, its arms, rules and rates); `experiments/03-generation0/README.md` and `wormwars/exp03/samplers.py` (the
   null ensembles); `experiments/02-screening/README.md` (the routing tripwire); `ROADMAP.md`'s "Standing rules";
   `wormwars/brain.py` (`Genome.cat`), `wormwars/e04a/evolve.py` (`evolve_batch`), `wormwars/e5/` (Task H, the
   prey), `wormwars/graft.py`, `wormwars/e4s/comparator.py`, `experiments/E1-navigation/freeze.json`
   (`throughput_04a_shape`), `experiments/03a-self-consistency/` (its one null-graph evolution and its gains).

**Context.** The owner chose stage 05 with a prey ladder (static, a defined route, then earlier organisms) and asked
for a null-graph arm so 05 also tests whether N2's wiring helps a hunter. E5-0 (CPU only, no evolution) found every
rung solvable and not too easy, E4s-1's grafted champions and L1 qualifying everywhere, E2d's N2-only champions
failing once the prey moves, and no fall-off of the positive control with prey speed. E5-1 is the first evolution on
Task H, and the first evolution on a null-graph ensemble since experiment 02. It will need about 30-45 GPU-hours (to be
replaced by a benchmark) and the owner's word for the GPU. A pre-registration follows the design, the pilot (E5-1a)
and the power simulation; the pilot must never run the confirmatory comparison.

**What I want from you:**
- **Is the confirmatory question well posed and answerable?** In particular §4's choice to graft L1 into both test
  arms ("N2 as a host for L1"), against a no-graft pair or both; SH-route as the null; N2's motor gains for every
  graph rather than per-graph calibration.
- **Confounds and fairness** between G-N2 and G-SHr: starts, gains, seeds and pairing, batch shapes, budgets, the
  graft's attachment, anything that would favour one side.
- **The ladder (§3):** the fixed training mixture against a curriculum; the eight slots; the held-out suite; the
  three-strata score.
- **The statistics (§5):** O1's estimand, the hierarchical bootstrap, the rules and δ = 0.25; the rough power
  arithmetic; whether O0, O1c, O2 and O3 are read correctly and not overclaimed.
- **The gates and pilot (§6):** are the CUDA checks enough for a task never run on CUDA; does any pilot step leak the
  confirmatory comparison; are the stop rules right.
- **Cost (§7):** check the arithmetic against the cited rates; what is missing.
- **Code (§8):** is anything that needs an equivalence check or a guard missing? Check the `Genome.cat` claim.
- **Every factual claim** that cites a file: please check it against the file, and say which you checked.
- Answer §10's open questions with a recommendation each.

**Format:** a verdict first (one of "proceed", "fix then proceed", "revise"), then must-fix items, then should-fix,
then answers to §10, then anything else. Number your items. Quote the design's text where you object to it. Be direct;
say when you are unsure.
