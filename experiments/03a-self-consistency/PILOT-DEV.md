# 03a pilot-dev: what it runs and how it chooses

**Status:** plan, 2026-10-17, written with the code (`scripts/e03a.py`, `wormwars/e03a/`) for review by both reviewers
before any GPU work. Pilot-dev is development (DESIGN.md v7.1 §8, §9): its output is the **frozen pilot protocol**,
written into the pre-registration before pilot-check runs. Nothing here is a registered test. It runs only with the
owner's word.

## 1. What it runs

On **one SH-mirror graph** (seed 3 403 000, outside 03's and 03r's SH-mirror seeds; rebuilt from its seed in every
stage and checked by hash, never saved, since it carries N2's weights, permuted), never on N2, inside its own
**6 GPU-hour cap** (T0's accounting across attempts; `CapClock`), which counts toward 03a's 72. World ids 1 482 000 000
to 1 482 799 999, outside every registered range; seeds from 3 403 000 to 3 413 604 (each search's own seed is a hash
of its target-brain's seed, its kind and its index). Every number is in `DEV` in the script.

| Stage | What | Episodes (about) |
|---|---|---|
| `setup` | Build and hash the graph; calibrate its motor gains on random genomes of the intact graph to N2's achieved drive in Task N-mono (D035's rule, `calibrate_in_world`) | small |
| `evolve-intact` | 1 selector and 1 MIP brain, 04a's GA unchanged (1 000 generations, validation every 25), one lockstep batch | 0.53 M |
| `panel` | Deletion scan of every bilateral representative of the eligible neurons on the selector brain, 512 selection worlds; the panel rule (§4); **the two targets are the two highest-relevance representatives** | 0.09 M |
| `evolve-nip` | 1 NIP brain per target, pinned (below), one lockstep batch | 0.53 M |
| `baseline` | On the 2 048 final-evaluation worlds: the MIP brain intact; each target-brain with X deleted; MIP exact restoration (must equal the intact counts); each NIP brain itself (must equal its deleted state) | 0.02 M |
| `tune` | Rounds A, B and C (§2) on the four target-brains (MIP × 2 targets, NIP × 2): 56 searches and their final evaluations | 3.3 M |
| `full` | The chosen settings: every search of the four target-brains (3 refits, 5 random-partner refits, 5 free searches), every result on the 2 048 worlds; and a 2× longer search (2 free searches of 200 generations) on each MIP target-brain | 3.6 M |
| `probe` | The bounded-history probe (L = 5, 10, 20, 50) on the scripted calibrators (D303's KT and KTM winners, D304's KTS winners at T = 5, 10, 20) and on the four evolved brains, plus the full-replay control (L = 10) in the probe's own batch composition | 0.10 M |
| `report` | No simulation: measured throughput per workload, δ_eval and δ_search, the formal design projected at the measured rates, the cuts of §10 if needed, and whether 32 search worlds are allowed | 0 |

About 8.2 M episodes: 5.4 hours at the 420 per second assumed in DESIGN.md §10, less if the wide search batches run
faster, as E2d measured. If the cap is reached, the running stage stops (`CapReached`), its record says so, and what
follows goes to the owner.

## 2. The tuning rules (fixed before running)

Each round runs 2 free searches per setting and target-brain, with every other setting at its current value, and
scores each search's result on the 2 048 final-evaluation worlds (raw count). The setting chosen in one round is carried
into the next and not run again.
- **Round A, the temperature ladder** (geometric, ratio 2): T₁ = 0.03, 0.1 or 0.3. Chosen by swap acceptance between
  neighbours (all searches of that ladder): the ladder inside 20-40% closest to 30%; if none is inside, the closest
  to 30%, flagged (the draft's aim, DRAFT.md "Search algorithm").
- **Round B, the moves:** (p_move, partner moves per move offspring) = (1/3, 1), (1/3, up to 3), (0.6, 1), (0.6, up
  to 3); the rest of the probability split evenly between weight and τ-bias mutations.
- **Round C, the search signal:** the raw count, or 04a's bounded progress bonus (c = 0.5) added to it. Every reported
  score stays the raw count.
- **Rule for B and C:** the mean over the four target-brains of the free searches' mean final count; the first setting
  listed is kept unless a later one beats the best so far by more than 0.02 targets.
- **Search worlds:** 16, or 32 only if `report`'s projection with 32 leaves at least 8 hours of reserve with no cut
  (DESIGN.md §6).

Tuning reads only scores, never the truth. The diagnostics below read the truth, and they are reported, not tuned on.

## 3. What `full` measures (the inputs to the frozen protocol)

- **Resolution:** δ_eval, the root mean square of the 95% half-widths of the target-brains' comparisons (headroom,
  original-partner advantage, functional success, and restoration in MIP; world bootstrap, B = 10 000); δ_search, the
  root mean square of the three refits' SD. Both against p (5% of the MIP brain's intact mean); δ_search also as a
  fraction of p, the form DESIGN.md §6 freezes.
- **Search diagnostics, per free search:** Q, the fraction of X's true partners connected in the coldest replica,
  every 10 generations; partner turnover per 10 generations; accepted partner moves; swap acceptance. Ranking agreement:
  the pairwise Spearman correlation between free searches' final |weight| vectors (each search has its own world
  schedule, so the worlds are independent). The longer search's gain in final count.
- **Per target-brain, descriptive:** the attributes (headroom, advantage, functional success; restoration in MIP), the
  stratified enrichment p (B = 10 000), the structural AUCs (mirror, class model, degree), the strata and the support.
- **Throughput** per workload from the accounting (`selection` for evolution, `measure` for the scan, `tuning`,
  `search`, `final`, `probe`).

**After pilot-dev** (not in the code): the acceptance thresholds for the diagnostics (turnover, ranking agreement, the
longer search's gain) are proposed from these numbers, reviewed by both reviewers, and written into the
pre-registration before pilot-check is run. Nothing is turned into a rule after pilot-check is seen.

## 4. Implementation choices the design left open

Each is stated so the reviewers can object.
1. **NIP brains are pinned on the intact mask** (`wormwars/e03a/arms.py`). The design says the NIP brains of a target
   share a mask with X's edges removed. Instead:
   - generation 0 is the run's ordinary initial population with X's edge weights set to zero;
   - those edges' mutation scales are zero, so they stay exactly zero (tested through a real evolution, with a
     sabotage check);
   - a brain with X's edges at zero is X deleted (tested).

   This lets NIP brains of several targets share a lockstep batch with the others. Every arm's initial magnitudes keep
   one normalisation: `Genome.random` scales by the mean anatomical weight of the mask's edges.
2. **Pilot-dev's arms:** 1 selector, 1 MIP and 1 NIP brain per target, 2 targets. Relevance in pilot-dev comes from
   one selector brain, so the "three-brain mean" is one brain.
3. **The union mask:**
   - X's candidate pool for each type is every other neuron, so the union adds 3 × 301 possible edges plus X's
     self-connection if it has one;
   - an unconnected candidate's weight is stored but never read;
   - a moved edge keeps its weight;
   - the best offspring is the first on ties;
   - every acceptance and swap draws its uniform number, so the random stream does not depend on the branch taken.
4. **Strata:** degree is counted over partners, with self-connections excluded. **Eligibility** paths treat gap
   junctions as both directions.
5. **Structural comparators** (`structural.py`):
   - degree is type-matched: out-degree for in-partners, in-degree for out-partners, gap degree for gap partners;
   - the class model uses the dataset's five classes.
6. **Accounting** gains a `search` category, for 03a's searches.
7. **What the reviewers should know:** on a planted synthetic problem (tests), the search finds a planted partner set
   quickly with 16 candidates, but slowly with 30. N2's targets have 301 candidates per type. Pilot-dev's Q trajectories
   and the longer search measure whether 100 generations are enough. If they are not, that is a pilot-dev finding,
   reported, and a change to the search budget goes back to the design.

## 5. DESIGN.md §8's implementation tests, and where each is

All run on the CPU in the ordinary suite (`python -m pytest tests/test_e03a_*.py`).

| §8 requires | Test |
|---|---|
| Deletion equals a network built without X | `test_e03a_reinsert.py::test_deletion_through_the_union_equals_a_network_without_x` (re-indexed network, rtol 1e-5, atol 1e-6; and bitwise against `delete_neurons`) |
| The union mask with zeroed edges equals the network built with exactly that partner set, gap denominators included, at a declared tolerance | `::test_union_mask_equals_the_network_built_with_exactly_those_partners` (declared exact), with the sabotage `::test_an_absent_gap_partner_changes_its_neighbours_denominator_when_present` |
| The frozen background is bitwise unchanged | `::test_the_background_is_bitwise_unchanged_by_reinsertion`; MIP exact restoration `::test_mip_exact_restoration_reproduces_the_intact_brain`, `::test_restoration_with_a_self_connection` |
| In NIP evolution, X's edges stay at zero through initialisation and every mutation | `test_e03a_arms.py::test_nip_runs_stay_pinned_through_evolution_and_intact_runs_are_unchanged` (a real lockstep evolution), sabotage `::test_without_the_scales_x_regrows_its_edges`; `test_e03a_reinsert.py::test_nip_pinning_holds_through_initialisation_and_mutation`, sabotage `::test_pinning_check_fails_when_x_keeps_its_edges` |
| Direction; gap symmetry after moves; degrees constant during a search; common random numbers | `test_e03a_reinsert.py::test_direction_in_partners_drive_x_and_out_partners_are_driven_by_it`, `::test_gap_junctions_are_symmetric_after_moves`; `test_e03a_search.py::test_partner_counts_never_change_and_refits_never_move`, `::test_common_random_numbers_every_state_of_a_generation_plays_the_same_worlds`, `::test_identical_states_score_identically_in_one_batch` |
| The information boundary, with sabotage checks that pinning and truth isolation fail when broken | `test_e03a_search.py::test_information_boundary_free_searches_do_not_see_the_truth` (a rewired graph with the same counts: identical union, background, free-search initial states and every proposal); sabotage `::test_information_boundary_sabotage_a_leaking_initialisation_is_caught`, `::test_information_boundary_sabotage_a_leaking_proposal_is_caught`; `test_e03a_null.py::test_strata_do_not_read_the_truth` |
| A planted optimum on a small synthetic problem | `test_e03a_search.py::test_planted_optimum_is_found`, sabotage `::test_planted_optimum_is_not_found_without_moves` |
| The no-task control's AUCs match the stratified null | `test_e03a_null.py::test_no_task_control_matches_the_stratified_null` (24 replicate target-arms, p roughly uniform, mean AUC within 0.03 of the null mean), sabotage `::test_no_task_check_can_fail_when_the_search_is_biased` |
| The replay probe's full replay equals the unperturbed episode; the rebuild passes the prescribed-sequence validation | `test_e03a_probe.py::test_full_replay_reproduces_the_unperturbed_episode_bitwise`, `::test_the_first_action_that_can_differ_is_at_2L_plus_1`, `::test_the_rebuild_is_a_fresh_run_over_the_last_L_inputs`, `::test_prescribed_sequence_where_the_discarded_history_changes_a_slow_controllers_action`, `::test_memoryless_and_one_tick_controllers_are_unaffected_by_the_probe`, `::test_the_calibrators_closed_loop_kt_and_ktm_unchanged_kts_changed` |
| Family 2's procedure on simulated nulls | `test_e03a_stats.py::test_family2_simulation_under_the_sharp_null_is_at_most_nominal`, sabotage `::test_family2_simulation_detects_a_real_difference`; the full validation, 20 000 datasets per scenario, is `scripts/e03a.py family2`, recorded in `family2-validation.json` |

Beyond §8: the strata rules, the permutations, the AUC against a brute-force count, the support against brute-force
enumeration (`test_e03a_null.py`); Holm and the exact test against brute force, the comparisons and outcome rules
(`test_e03a_stats.py`); the panel rule and the structural comparators (`test_e03a_panel.py`); the driver end to end at
smoke size (`test_e03a_script.py`).

**Rule 9.** The tests were written after the code in this round. To see each core check fail, 17 deliberate bugs were
planted one at a time, each against the test meant to catch it. 16 were caught. The survivor makes acceptance strict
(`>` for `>=`), and it is equivalent on ties: a tie is still accepted, because the uniform draw is always below
exp(0) = 1.
