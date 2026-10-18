You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing research code in the repository you can read (read-only): **03h's step-1 code**, at commit 436a73c
on branch `roadmap` (DECISIONS.md D326). It implements design v3.2 §7.1
(`experiments/03h-history-use/DESIGN.md`), which you agreed in four rounds. Nothing has run on the GPU apart from the
test suite.

**What to read:**
- **The world:** `wormwars/world.py` (`_food_fell` and the `food_fell` validation and state) and
  `wormwars/config.py` (`food_fell`, `food_fell_rates`, `_OMITTED_WHILE_UNSET`).
- **The interface variant:** `configs/interface-03h.yaml`; `wormwars/e03h/__init__.py`; `wormwars/interface.py`.
- **The ASK cap:** `wormwars/exp03/samplers.py` (`ASK_KINDS`, `constrained_neurons(extra)`).
- **The gate families:** `wormwars/exp02/scripted.py` (`ScriptedBrain` reading the bit) and
  `wormwars/e03h/scripted.py` (`BitKinesis`, `SlowMemoryKinesis`).
- **The history probe:** `wormwars/exp03/measures.py` (`history(per_history=True)`).
- **The statistic:** `wormwars/e03h/stats.py` (`partial_spearman`).
- **Step 0:** `scripts/e03h_step0.py`.
- **The tests:** `tests/test_e03h_*.py`.

**Please:**
1. Say whether each piece matches the design (§3-§7), and name any mismatch. Look in particular at:
   - the bit's definition (after the clamp, first tick, dead weys, per wey);
   - the sham's keying, its stationary start and its transitions;
   - the transition counts' conventions;
   - the T = 1 exactness;
   - whether `BitKinesis` really equals `MemoryKinesis` at threshold 0 under relief;
   - step 0's regeneration recipe and its bit-equal verification.
2. Name any bug that would mislead step 0, the gate, the pilot, or the formal run, with file, line and severity.
3. Name any gap in the tests, including whether rule 7's check covers what it claims to.
4. Name any change to earlier experiments' behaviour. The design says none: hashes, default outputs and `KINDS` are
   unchanged.

Answer with a verdict first: "ready for step 0" (possibly with small fixes) or "revise". Then give numbered findings.
Do not edit files or run anything.
