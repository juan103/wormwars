You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E3c pre-registration, draft 1: please review before it binds

You are reviewing, read-only, the WormWars repository in the current directory, at commit 54f6f5f
(branch `roadmap`).

**The draft:** `experiments/E3-ab-organism/E3c/PREREGISTRATION.md`.

**Its basis:**
- the design you agreed, `docs/E3/E3c-DESIGN.md` v2.1;
- the pilot and the replay-and-probe you reviewed (`PILOT.md`, D203-D206). The from-scratch champions are
  scent-free wall-followers;
- the owner's choices:
  - run E3c as designed if scent-free (D205);
  - **a dual practical margin** keeping both your proposals: Fable's 0.10 of the seed's mean and Astra's 0.5
    visits per wey, combined so that "beyond the margin" needs the larger and "no relevant difference" the
    smaller.

**New code behind it:**
- `wormwars/e3/e3c_stats.py` and `tests/test_e3c_stats.py`: the registered statistics. They implement Welch
  with Holm, intervals at each contrast's Holm level, the dual margin, the labels and the floor guard;
- `scripts/e3c_power.py` → `power.json`: the power analysis, summarised in §8.

**Please check, and answer each, citing section and line:**
1. **Faithfulness:**
   - Does the draft register what the design and D205/D206 require?
   - Is every post-pilot change listed in §13 and justified?
   - Is anything missing, such as a reading you asked for in the pilot reviews?
2. **The statistics:**
   - Are the label rule and the Holm-level intervals correct, and is `e3c_stats.py` right?
   - Is the dual-margin rule stated unambiguously?
   - Q2's false-positive rate rises to about 0.06 when S-mod fails in a quarter of its runs (§8). Is
     disclosing it enough, or should the rule change before binding? If so, how, without tuning to the
     pilot?
3. **The power analysis:**
   - Is the simulation faithful to the registered procedure?
   - Are its scenarios adequate, especially the failure mixture and P-joint's distribution?
   - Is §8's summary correct against `power.json`?
4. **The coverage hypothesis and the noses-removed reading** (§7.3):
   - Are the classes, the "coverer" criterion and the supported/mixed/not supported rule sound as fixed in
     advance?
   - Is appending the class counts to Q1's and Q2's labels a fair qualifier?
5. **The blocks, ids, seeds, stages, champions rule, cap and cuts** (§3-§6, §10): any error, or anything that
   could make the formal run invalid or unreproducible?
6. **The wording:** any claim stronger than the evidence, especially about what E3c can say after the pilot?
7. **Your verdict:**
   - "bind it";
   - or "revise", with a numbered list of required changes, separated from optional suggestions.
