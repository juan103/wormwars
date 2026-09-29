You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing code in WormWars, an open-science project that evolves brains on the C. elegans
connectome. The repository is your working directory; read `AGENTS.md` for its rules.

**Context:** you agreed the plan `experiments/E2d-taskn-diagnosis/PLAN.md` (v4; D129-D131), an
exploratory diagnosis of Task N after E2's floor fired. Its runner is now written; the plan says it
goes to both of you before any GPU work.

**What to review:** `scripts/e2d.py` (see D132 in `DECISIONS.md`), with its tests
`tests/test_e2d_analysis.py` and `tests/test_e2d_commands.py`. The runner reuses E2's stage frame by
importing `scripts/e2.py` as a module and reassigning its globals (`configure()`); read the parts of
`scripts/e2.py` it relies on (`run_stage`, `rerun_plan`, `train_batch`, `run_method`, `require_earlier`).

**Please check, against the plan's text:**
1. **The rules:** `world_ci`, `classify`, `set_reading`, `plateau_reading`, `budget_reading`,
   `run_summary`, `sign_flip_p`, `arm_reading` (with and without run 2), `leaves_plateau`,
   `interaction`, `top_k`, `_pair_rates`/`_bin_rows`/`sibling_ranking`, and `analyse_c0`. Does each do
   exactly what the plan says? Pay particular attention to interval levels (95% over worlds, 90% over
   runs), the complement per draw, exclusions, and which sets are read.
2. **The stages:**
   - Part B's genomes, de-duplication, references and checks (`cmd_probe`, `analyse_b`).
   - C0's children and pairs (`children`, `es_pairs`: the same noise at every scale or σ; the
     parent/mean evaluated).
   - The replay (`cmd_replay`: E2's seeds, ids, composition, generations 0-25, twice, compared with
     E2's first two checkpoints).
   - The arms: the settings from `REGISTERED["arms"]`, pairing with E2's runs, `pairing_check`, the
     admission rule (`admit`, reruns included), and the hard stop (`training_clock`).
   - The hold-out pass: the matched references GA′ and C2′ (`matched`), the arms' references, missing
     arms, and the contrasts.
3. **The frame reuse:** is reassigning E2's module globals safe? For example, can any E2 function
   still write to E2's folders, read E2's registered numbers, or use E2's wording?
4. **Anything that would make a GPU run produce a wrong or misleading record,** or waste the budget.
5. The tests: do they pin what matters? Name any rule whose test could pass with the rule broken.

**Answer format:** a verdict first, one of "run" (proceed to the guarded smoke and the formal
stages), "fix" or "rethink"; then must-fix items (numbered, each with file:line and the change),
then suggestions, then what you checked and found correct. Be concrete and brief. You are read-only.
