You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing code in WormWars, an open-science project that evolves brains on the C. elegans connectome.
The repository is your working directory; read `AGENTS.md`.

**What to review** (the `roadmap` branch, latest commit): `scripts/e4s1.py`, `wormwars/e4s/arms.py`,
`wormwars/e4s/readings.py` and their tests (`tests/test_e4s1_lib.py`, `tests/test_e4s1_script.py`).
- They implement the **bound** pre-registration `experiments/E4s-stereo-module/E4s-1/PREREGISTRATION.md`
  (D150), which cannot change except by dated amendment.
- D151 records what was built. A smoke run of every stage completed; its records are local.
- Nothing formal has run. The formal run is about 16-19 GPU-hours, so errors are expensive.

**Please answer:**
1. A verdict: "run", "fix then run" or "revise".
2. Every departure from the pre-registration, and every bug that could make a formal result wrong
   without failing a test (numbered; file, line, fix). In particular check:
   - the gates (G1-G3) as registered: genomes, inputs, shapes, coverage, tests;
   - the arms' generation 0, masks, seeds, R's draws and N's construction;
   - the training stage (hooks, admission, saved genomes, end-of-run assertions);
   - F, C and G0, and the 14 hold-out conditions and their applicability;
   - D, H, Mc, the motor measures, and the G0 population count;
   - the evaluation along training (checkpoint indices) and the final populations;
   - the stage order, reruns and admission.
3. Anything the analysis will need that the records do not store.

Be concrete and brief. You are read-only: do not edit files.
