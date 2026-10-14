You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Results review: the evolutionary E4-D's formal run (WormWars)

You reviewed this experiment's pre-registration (three rounds, `docs/reviews/20261014-E4-D-evo-prereg*`) and its formal
code (three rounds, `docs/reviews/20261014-E4-D-evo-formal-code*`; both "run it" on 5237304). The formal run is now
complete, and the results are written up for publication on `main`. HEAD is 7c0ebde on branch `roadmap`.

**Read:**
- `experiments/E4-two-minds/E4-D-evo/RESULTS.md` and `README.md` (new);
- `experiments/E4-two-minds/E4-D-evo/summary.json` and `scripts/e4d_evo_summary.py` with its tests
  (`tests/test_e4d_evo_summary.py`) — every number in RESULTS should come from summary.json;
- the records it reads, in `experiments/E4-two-minds/E4-D-evo/formal/` (check, train-l/f, evaluate-l/f, report-l/f,
  compute records, start markers);
- the pre-registration, `experiments/E4-two-minds/E4-D-evo/PREREGISTRATION.md` (§7 the readings and the wording, §5 the
  stages, Amendment 1);
- DECISIONS D279-D280, and the status lines changed in `README.md`, `ROADMAP.md` and `experiments/E4-two-minds/README.md`
  (`git diff 5935ea7 7c0ebde`).

**What happened, in brief:** check passed; L (32 runs) read "practically relevant transfer found" (mean gain 0.412, LB
0.401); F (4 runs) the same; S not triggered. D279 discloses that three record commits were pushed without the hygiene
tests (CI red, fixed by a narrow exemption for binary per-maze outcome arrays).

**What I want:**
1. Is the registered reading reported correctly and in the registered wording, with the registered limits (§7.1)?
   Is anything claimed beyond what §1 says the labels claim?
2. Is every number in RESULTS.md, the README lines and D280 traceable to summary.json or a record, and correct? Please
   recompute a sample yourself from the records, not from summary.json.
3. Are the descriptive and exploratory parts labelled correctly? In particular: the slot contrasts were chosen after
   seeing L's data; the removed-cue observation was not predicted. Is any interpretation stronger than the data?
4. Any deviation from the pre-registration that is not disclosed?
5. Does D279's exemption weaken the connectome guard in a way that matters?
6. Anything else that should be fixed before publication on main.

**The answer I want:** a verdict ("publish", "fix then publish", or "revise and re-review"), then numbered findings with
severity, file:line and the fix. Terse.
