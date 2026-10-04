You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Code review: E3b-2 (where E3b-1's gain comes from), before its GPU run

You are reviewing code in the WormWars repository (your working directory). You may read any file.

## Context

E3b-2 is an exploratory follow-up to E3b-1 (published; `experiments/E3-ab-organism/E3b-1/`).
- **Its plan** is `docs/E3/E3b-2-PLAN.md`, draft 2.
- **You reviewed draft 1;** both said "go with changes". Your answers are in
  `docs/reviews/20261004-E3b-2-plan/`, and D194 in `DECISIONS.md` maps the changes. Draft 2's §10 lists them.

**The implementation, written test-first** (commits 8e2dbbf and 443dcb0 on `roadmap`):
- `wormwars/e3/attribution.py`:
  - the partitions;
  - the hybrids;
  - Shapley values, dividends, reversion and transplant;
  - the lesions and clamps (`HeldBrain`);
  - `SwitchTally` and the vectorised `LatchRecorder`;
- `scripts/e3b2.py`:
  - the runner, in E2's stage frame, configured for E3b-2's own folders;
  - stages `project`, `attribution`, `lesions`, `latch` and `report`;
- `tests/test_e3b2_attribution.py` and `tests/test_e3b2_runner.py`:
  - five sabotage checks were caught;
  - a CPU smoke of every stage passes, with stand-in champions (mutated seeds).

## The question

**Does the code implement draft 2 faithfully, and did draft 2 carry out your plan-review changes, so the GPU
run can start?**

For each problem give:
- the file and line;
- what the plan says;
- what the code does;
- a severity: blocking (it would change a reported number, the attribution, the lesion or latch readings, the
  compute accounting, or E3b-1's records) or non-blocking.

Please check especially:
1. **The partitions and hybrids** (`parameter_groups`, `hybrid`) against `tuning.scales` and the organism.
2. **The calculator** (`shapley`, `dividends`, `rebuild`, `reversion`, `transplant`) and `read_table`,
   `shapley_matrix` and the maze-paired bootstrap in `attribution_report`.
3. **The lesions:**
   - the clamps at each organism's own A and B states. When the relay signs disagree (`a_high` returns
     None), the code takes the seed's convention: A is the high state;
   - the input cut and the gate cut;
   - scent removed (`without_scent`);
   - the reflex held at −0.5;
   - the W2 reference (the seed with all 32 outputs at 0);
   - `HeldBrain` starting clamped neurons at their values.
4. **The recorder** (`LatchRecorder`):
   - decoding through the strain assignment;
   - the goal before the switch;
   - legs, crossing, latency and censoring;
   - the undecided band (the middle third);
   - agreement per goal;
   - its cross-check against `SwitchTally` on a real run.
5. **The runner:**
   - the chunk plans (A: one champion's 16 hybrids per chunk, the all-seed first; B: two champions × 8;
     C: 8 lesion variants, with scent chunks and the W2 reference apart; D: 21 organisms);
   - resume, which validates the full specification;
   - output isolation from E3b-0 and E3b-1;
   - the hash checks on E3b-1's champions;
   - the drop order and admission;
   - the report.
6. **Anything that differs between smoke and formal,** or that could write into E3b-1's folders.

## Rulings made during implementation (claims to attack)

- **The GPU benchmark** in `project` times chunks on its own block, 7300-7555, outside every block. The
  plan said "on smoke mazes", but the smoke ids (9800-9899) are only 100 mazes, and a 16 × 256 chunk needs
  256.
- **The seed's shared mean** (the denominator everywhere) is the all-seed hybrid in the first champion's
  A-shared chunk. The report checks that all 16 copies are bitwise equal (`seed_exact_across_chunks`).
- **Lesion costs** use the lesion stage's own intact variant (a different composition from A's
  all-champion hybrid). The difference between the two is not reported.
- **The latch-measure intervals** are maze-bootstrap intervals of a ratio of sums, so mazes with more ticks
  weigh more, as in the totals.

Please end with a verdict: "start the GPU run", "fix then start" (listing the blocking fixes), or "revise".
