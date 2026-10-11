You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E4 design v2: please review

You are reviewing, read-only, the WormWars repository in the current directory, at b43be86 (branch `roadmap`).

Your review of v1 is archived in `docs/reviews/20261011-E4-design/`. D243 in `DECISIONS.md` records it, with the
gate-leak measurement (`scripts/e4_gate_leak.py`, `docs/E4/gate-leak.json`). The design is `docs/E4/E4-DESIGN.md`
v2: §0 summarises the changes, and §10 lists the open decisions. **No GPU is to be used yet** (the owner).

**Please answer:**
1. Were your required changes taken correctly?
2. **The new choices:**
   - the output gate with ungated comparators and a frozen selector, given the measured leak;
   - P1 by cut and mean substitution as primary;
   - the joint table;
   - the scale rule;
   - E4-D's ordering.

   Are they sound?
3. Is anything new wrong or missing?
4. **Verdict:** "proceed to the pre-registration", or "revise" with a numbered list limited to what would make a
   result wrong or uninterpretable.
