You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a design in WormWars, an open-science project that evolves brains on the C.
elegans connectome. The repository is your working directory; read `AGENTS.md` for its rules.

**Context:**
- E2 and its diagnosis E2d (published) found a "non-stereo plateau": no evolved champion meets the
  "uses the left-right difference" criterion. The owner decided (D139) to hand-build the stereo
  capability ahead of plan (two noses, a fly-style ring attractor, a left/right turning readout, then
  evolution), with a 96 GPU-hour ceiling.
- **Design v1 was reviewed by Astra 6 (OpenAI) and Fable 5.1 (Anthropic)**; both said "revise". You are one of them. The
  reviews are archived verbatim in `docs/reviews/20260930-014518-E4s-design/` (`astra.answer.md`,
  `fable.answer.md`). D141 in `DECISIONS.md` records what was checked and changed.
- **Design v2 is `docs/E4s/DESIGN.md`** (commit 68812ac). Its last section maps every v1 must-fix to
  its change. The graft functions are in `wormwars/graft.py` with `tests/test_graft.py` (D140). The
  gain probe was extended (`scripts/e4s_gain_probe.py`, output in
  `experiments/E4s-stereo-module/development-records/gain-probe.json`).
- Nothing has run on E4s's worlds or seeds.

**Please answer:**
1. Is each v1 must-fix (both reviewers') resolved by v2? Name any that are not, or that are resolved
   wrongly.
2. Did v2 introduce new problems? In particular check:
   - the carrier (Stage A): forward drive by bias on AVB/PVC, turn bias, turn-neuron τ = 1;
   - M2's structure (no direct path; the turn-copy relays reading the turn motor neurons; the
     shifter wiring and sign) and whether it can plausibly reach the gate within the genome bounds;
   - the A0 component-check thresholds and the shifter calibration target;
   - the gate (G1-G3) and M0's separate gate;
   - the generation-0 graft measurement and its pre-stated "integration" wording;
   - the outcomes O1-O3: the F-versus-C choice, the exclusive classes, the 12-of-16 rule, the
     B1-B3 pairing;
   - the arms B1-B6, the mutation ownership, the 0.25× factor and its fallback rule;
   - the engine changes and their checks (per-parameter scales, `evolve_batch` hooks, E2's
     generation 0-25 hash reproduction, embedding, tolerances, the hygiene extension);
   - the budget (about 16 h estimated, 30 h cap).
3. Is v2 ready to be turned into a pre-registration? If yes, list anything the pre-registration must
   pin that v2 leaves open.

**Answer format:** a verdict first, one of "proceed to pre-registration", "revise" or "rethink";
then must-fix items (numbered, each with the section and the change), then suggestions, then what you
checked and found correct. Be concrete and brief. You are read-only: do not edit files.
