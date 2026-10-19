You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing, read-only, a question about 03h in this repository (branch `roadmap`, HEAD d3567e4, plus two
uncommitted files named below). Please check the claims against the files, not against this prompt.

**Background.**
- 03h's design: `experiments/03h-history-use/DESIGN.md` (v3.3). The owner chose B as the only registered claim and A
  as a pre-specified secondary (§13, D330).
- The pilot's registration: `PILOT.md`, bound at ff1fd31 (D335).
- The pilot ran on 2026-10-19 (D336, `DECISIONS.md`). Its record is `experiments/03h-history-use/pilot/pilot.json`, and
  its action was "proceed to the pre-registration":
  - every gate passed;
  - W = 16;
  - the decile shift moved at amplitude 0.25 (+0.0077, 95% interval [0.0044, 0.0107]);
  - the plan is W_t = 64 with SH, projected at 4.24 GPU-hours against a 6-hour cap.
- D336 flagged that B's shift is small and heterogeneous: per graph +0.019, −0.0003 and +0.004. It asked the
  pre-registration round to examine B's power, because the pilot registered no rule on B's power (PILOT.md §5.3 is
  about A2).

**What B needs** (DESIGN §6, §13):
- per graph, U = T_sham − T_relief;
- N2 passes if at most two of the 64 SH-mirror-ASK graphs have U at or above N2's (p ≤ 3/65);
- plus N2's level advantage and the ensemble's decile shift > 0 by their intervals.

**New, exploratory, uncommitted:** `experiments/03h-history-use/development-records/b_power.py` and its output
`b-power.json`. They model B's rank test from the pilot's numbers:
- the nulls' U is drawn from N(−0.0077, SD 0.0102), with the SD also taken at its 90% chi-square bounds for 2 degrees
  of freedom, 0.0059 and 0.045;
- N2's U is drawn from N(u, 0.0028).

The results, as pass rates:
- if N2 gains nothing from the relief (u = 0): 0.005 at the point SD, and 0.22 at the lower SD bound;
- if the relief harms N2 as much as it helps the nulls (u = +0.0077): 0.29, and 0.94 at the lower bound;
- the u needed for 80% power is +0.014 at the point SD;
- the selection bank adds context. Over all 256 genomes, relief − sham averages +0.003, −0.0003 and −0.0007 per
  graph: random brains barely respond to the bit. The pilot's turn response is about 1e-4.

**A claim to attack** (Claude's, not settled): as designed, B has almost no power for any plausible effect.
"N2 gains nothing from the relief" is already the extreme of the hypothesis, short of the relief harming N2. Running the
formal run (about 4.2 GPU-hours) would very likely give "not established", which is uninformative. The owner should be
offered these options:
1. **Run as designed,** with the power disclosed in the pre-registration. What it would still give:
   - the manipulation check at 64 graphs;
   - A's secondary readings;
   - N2's level advantage.
2. **Redesign B** under a new design round: a stronger relief channel, a different statistic, or a different
   injection site. That would need a new pilot, and the pilot's cap has 0.79 GPU-hours left.
3. **Stop 03h at the pilot and report it.** The relief channel barely reaches random brains' foraging at generation 0,
   so B cannot be read with this manipulation.

Changing the primary claim, for example promoting A, is the owner's decision. Stopping or redesigning is a
scientific-direction change, so it goes to the owner in any case.

**Please answer:**
1. Is the power model sound? Name any error in `b_power.py`, its assumptions, or its reading of `pilot.json` that
   changes the conclusion. Cover the normality, the 3-graph SD, the correlated shared-world noise, and the selection
   noise in U.
2. Given the files, is B's power as low as claimed? Is there an analysis-only change, fixed before the formal run, that
   would materially raise it without a new pilot? Is any such change legitimate after seeing the pilot?
3. Which option do you recommend to the owner (1, 2, 3, or another), and why? If 2, what would the minimal redesign be?
4. Anything the pre-registration must say about B's power if option 1 is chosen.

Verdict first, as one of "run as designed", "redesign B", "stop and report", or "other: ...". Then numbered findings,
short. Do not edit files or run anything.
