# 03a pilot-dev: what it runs and how it chooses

**Status:** plan v3.1, 2026-10-18, written with the code (`scripts/e03a.py`, `wormwars/e03a/`).
- **v1** (`a4956e5`, D308): Fable "ready for pilot-dev, with small fixes"; Astra "revise" (code review round 1, run
  20261017-190316, `docs/reviews/20261017-03a-code/`). v2 takes every finding (§6; D309).
- **v2** (`a5760c4`, D309): Fable "ready for pilot-dev, with small fixes"; Astra "revise" (round 2, run
  20261018-021702, `docs/reviews/20261018-03a-code-r2/`). v3 takes every finding but one, where they disagree
  (round B's order, §2), and puts that one to them (§6; D310).
- **v3** (`1b0531a`, D310): both "ready for the rest of pilot-dev, with small fixes" (round 3, run 20261018-031947,
  `docs/reviews/20261018-03a-code-r3/`). v3.1 makes those fixes (§6; D311).
- **The owner's word for the GPU:** given 2026-10-18 ("you have my go ahead for the gpu"). `setup` and `evolve-intact`
  ran on v2's code while round 2 was under review. `panel`, `evolve-nip`, `baseline` and `probe` ran on v3's code
  (`1b0531a`) while round 3 was under review. None of them depends on what rounds 2 and 3 changed.

Pilot-dev is development (DESIGN.md v7.1 §8, §9): its output is the **frozen pilot protocol**, written into the
pre-registration before pilot-check runs. Nothing here is a registered test. It runs only with the owner's word.

## 1. What it runs

On **one SH-mirror graph** (seed 3 403 000, outside 03's and 03r's SH-mirror seeds; rebuilt from its seed in every
stage and checked by hash, never saved, since it carries N2's weights, permuted), never on N2, inside its own
**6 GPU-hour cap**. T0's accounting counts the cap across attempts, the CUDA preflight included, and it counts toward
03a's 72. World ids are 1 482 000 000 to 1 482 799 999, outside every registered range. Seeds run from 3 403 000 to
3 414 003 (the no-task control's, which simulate nothing); each search's own seed is a hash of its target-brain's
seed, its kind and its index. Every number is in `DEV`
in the script.

| Stage | What | Episodes (about) |
|---|---|---|
| CUDA preflight | Every stage at smoke size on CUDA (`--smoke --device cuda`), so a device or memory fault surfaces before the GPU budget is spent (Astra) | seconds |
| `setup` | Build and hash the graph; calibrate its motor gains on random genomes of the intact graph to N2's achieved drive in Task N-mono (D035's rule, `calibrate_in_world`) | small |
| `evolve-intact` | 1 selector and 1 MIP brain, 04a's GA unchanged (1 000 generations, validation every 25), one lockstep batch; every checkpoint's genomes and records saved as it happens | 0.53 M |
| `panel` | Deletion scan of every bilateral representative of the eligible neurons on the selector brain, 512 selection worlds; the panel rule (DESIGN.md §4); **the two targets are the two highest-relevance representatives** | 0.09 M |
| `evolve-nip` | 1 NIP brain per target, pinned (§4), one lockstep batch | 0.53 M |
| `baseline` | On the 2 048 final-evaluation worlds: the MIP brain intact; each target-brain with X deleted; the deletion deficit. **Two controls that must hold exactly** (counts, final head positions and every target event, inside `replay_mode()`, each pair in the same batch composition): MIP's exact restoration reproduces the intact brain, and each NIP brain plays exactly as its deleted state. A failure fails the stage, and nothing downstream runs | 0.02 M |
| `probe` | Before the searches, so a cap reached in them still leaves its timings (Fable). The bounded-history probe (L = 5, 10, 20, 50) on the scripted calibrators and the four evolved brains, each condition timed, the full-replay control included. **Controls that must hold exactly:** KT and KTM play exactly the same episodes at every L, and the full-replay control (L = 10) reproduces each evolved brain's episodes. The first failure stops the stage | 0.10 M |
| `tune` | Rounds A, B and C (§2) on the four target-brains (MIP × 2 targets, NIP × 2): 56 searches and their final evaluations; each finished round kept | 3.3 M |
| `full` | The chosen settings, target-brain by target-brain: every search (3 refits, 5 random-partner refits, 5 free searches), every result on the 2 048 worlds; on each MIP target-brain 2 free searches run to 200 generations, each scored at generation 100 and at 200; the no-task control. What finishes is kept: the record's metadata from the start; each target-brain's search states, saved locally once its ordinary searches end and again at the end; each scored row | 3.6 M |
| `report` | No simulation: what was measured (rates, δ_eval and δ_search, per-composition search timings), and the formal design projected at the measured rates with the cuts of §10 if needed, and whether 32 search worlds are allowed. A stopped `full` is reported as far as it got; a missing measurement withholds the projection instead of assuming a rate | 0 |

About 8.2 M episodes: 5.4 hours at the 420 per second assumed in DESIGN.md §10. The search batches are wider, so they
may run faster, as E2d measured. The two-run evolution batches may run slower than 04a's eight (Fable). If the cap is
reached, the running stage stops (`CapReached`) and its record keeps what finished. What follows goes to the owner.

## 2. The tuning rules (fixed before running)

Each round runs 2 free searches per setting and target-brain, with every other setting at its current value, and
scores each search's result on the 2 048 final-evaluation worlds (raw count). The setting chosen in one round is carried
into the next and not run again.
- **Round A, the temperature ladder** (geometric, ratio 2): T₁ = 0.03, 0.1 or 0.3. Swap acceptance is measured per
  neighbour pair, over all searches of a ladder.
  - A ladder qualifies if every neighbour pair is inside 20-40%.
  - Among qualifying ladders, the one whose mean pair rate is closest to 30% is chosen.
  - If none qualifies, the ladder whose worst pair is nearest the band is chosen, flagged.
  - The 20-40% aim is the draft's (DRAFT.md "Search algorithm"); counting per pair keeps one closed pair from hiding in
    an average (Astra).
- **Round B, the moves:** (p_move, partner moves per move offspring) = (1/3, 1), (1/3, up to 3), (0.6, 1), (0.6, up
  to 3); the rest of the probability split evenly between weight and τ-bias mutations.
- **Round C, the search signal:** the raw count, or 04a's bounded progress bonus (c = 0.5) added to it. Every reported
  score stays the raw count.
- **Rule for B and C:** the mean over the four target-brains of the free searches' mean final count; the first setting
  listed is kept unless a later one beats the best so far by more than 0.02 targets.
  - **Open, round 3:** with noise far above 0.02, the listed order all but decides round B. Fable would list (0.6, up
    to 3) first, the planted check's best; Astra would keep the order above. The order stays as listed until both
    reviewers agree, or the owner decides.
    - *Corrected 2026-10-18 (D311; Fable, Astra, round 3): the premise above is wrong. When the noise is far above
      0.02, a later setting displaces the first whenever noise favours it, so noise decides, not the order. The order
      only matters within 0.02, and the pick is always within 0.02 of the highest mean. Both reviewers accept keeping
      the order as listed (Fable's preference; Astra prefers the highest mean but accepts this). It stays, and the
      round is described as a noisy choice, not an optimisation.*
  - The between-search noise is far larger than 0.02, so the pre-registration will call these settings chosen by this
    rule, not optimised (Fable, Astra).
- **Search worlds:** 16, or 32 only if `report`'s projection with 32 leaves at least 8 hours of reserve with no cut
  (DESIGN.md §6).

Tuning reads only scores, never the truth. The diagnostics below read the truth; they are reported, never tuned on.

## 3. What `full` measures (the inputs to the frozen protocol)

- **Resolution:**
  - δ_eval is the root mean square of the 95% half-widths of the target-brains' comparisons: headroom, original-partner
    advantage, functional success, and restoration in MIP (world bootstrap, B = 10 000).
  - δ_search is the root mean square of the three refits' SD.
  - Both are compared against p, which is 5% of the MIP brain's intact mean. δ_search is also given as a fraction of
    p.
  - These are pilot-dev's measurements. DESIGN.md §6 freezes δ_search from pilot-check, by an extraction rule the
    pre-registration fixes in advance (Astra).
- **Search diagnostics, per free search and per longer search:**
  - Q, the fraction of X's true partners connected in the coldest replica, at generation 0 and after every 10
    generations, beside its chance level (Astra: v1 sampled generations 1, 11, … 91);
  - partner turnover over each window 0 → 10, 10 → 20, …, to the last generation;
  - the signal against the noise (Fable): the SD of the coldest replica's score across generations, and per generation
    the mean and SD of offspring minus current on the same worlds, kept as series, beside the refit-minus-deleted
    difference. These spreads mix mutation effects, replica differences and evaluation noise, and are read as such,
    not as pure noise (Astra, round 3);
  - accepted partner moves;
  - swap acceptance per neighbour pair;
  - the final count and the AUC.
- **Agreement between free searches,** whose world schedules are independent:
  - per type, the Jaccard index of their partner sets, beside its expectation for independent random sets (Fable);
  - the Spearman correlation of their |weight| vectors, which shared zeros dominate.
- **Are 100 generations enough?** The same long searches are scored at generation 100 and at generation 200: final
  count and AUC. Their Q trajectories run through generation 200 (Fable, Astra).
  - **How it will be read, fixed now** (Fable, Astra; both would keep 100 generations for pilot-dev):
    - Q at 100 within noise of chance, and no gain from 100 to 200: no improvement is detected over this extension,
      and the budget stays, because these measurements do not justify increasing it. (v3 said "the search is
      signal-limited ... more generations would not help", which two extensions per MIP target cannot establish;
      Astra, round 3.)
    - Q still rising at 100, and the long searches gaining in AUC: a budget amendment is proposed to both reviewers
      before the pre-registration, paid for by §10's cuts and the move settings.
    - Function plateauing while anatomy still improves is reported as such; it points to the same amendment.
    - The long searches run on the MIP target-brains only, and conclusions are scoped to them.
- **Per target-brain, descriptive** (DESIGN.md §6, "Also reported"):
  - the attributes, the deletion deficit, and the stratified enrichment p (B = 10 000), with one permutation bank per
    target shared by both arms;
  - the AUC over interface and over non-interface candidates;
  - precision at k against the same null, and average precision beside chance;
  - the structural AUCs (mirror, class model, degree) and the task minus the composite;
  - for paired targets, the AUC on the candidates the mirror ranking leaves at zero, per type (each type's zero set,
    its size and partner count; v2 took the intersection over types; Astra, Fable);
  - the no-task control (§8): five free searches with fitness zero, ranked and tested against the same null;
  - the five attributes and the outcome, per target-brain, with pilot-dev's own δ_search;
  - the strata and the support.
- **Throughput** per workload: `selection` and `holdout` for evolution (its selection and validation episodes priced
  separately), `measure` for the scan, `search`, `final`, and the probe's per-condition times.
  - Each extrapolation is named in the report: the evolution rates come from two-run batches; the probe is priced
    per brain from its measured condition times.

**After pilot-dev** (not in the code): the acceptance thresholds for the diagnostics (turnover, Jaccard agreement, the
long searches' change from generation 100 to 200) are proposed from these numbers and reviewed by both reviewers. They
are written into the pre-registration before pilot-check runs; nothing becomes a rule after pilot-check is seen.

Pilot-dev measures them on two high-relevance targets only, so the pre-registration must say how they apply to
pilot-check's low target. Either criterion 6 is scoped to the high targets, or the low target's diagnostics are read
separately (Fable, Astra).

## 4. Implementation choices the design left open

Each is stated so the reviewers can object.
1. **NIP brains are pinned on the intact mask** (`wormwars/e03a/arms.py`; accepted by both reviewers, round 1, and
   annotated beside DESIGN.md §3).
   - The design says the NIP brains of a target share a mask with X's edges removed. Instead, generation 0 is the run's
     ordinary initial population with X's edge weights set to zero, and those edges' mutation scales are zero, so they
     stay exactly zero.
   - This is tested through a real evolution, with a sabotage check. The intact runs in the same batch evolve exactly
     as without the hooks (tested).
   - A brain with X's edges at zero is X deleted (tested).
   - What it changes (Astra): the NIP brain has no functional exposure to X during evolution, but its initial magnitude
     scale comes from the intact graph. `Genome.random` normalises by the mean anatomical weight of the mask's edges,
     X's included.
   - The reason is batching: NIP brains of several targets share a lockstep batch with the others, and every arm keeps
     one normalisation.
2. **Pilot-dev's arms:** 1 selector, 1 MIP and 1 NIP brain per target, 2 targets. Relevance in pilot-dev comes from
   one selector brain, so the "three-brain mean" is one brain. The targets' deletion deficits in the MIP brain are
   reported before any search is read (Astra).
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
7. **The search budget: an open question for the reviewers (round 2).** Fable's free check
   (`development-records/planted_scale_check.py`, `planted-scale-check.json`) runs the search on a planted problem at
   N2's scale:
   - **Set-up:** K = 301 candidates and the true counts of AIYL, RIAL and AIZL; 5 seeds per setting; the default
     ladder.
   - **With a perfect, noiseless signal:** the search connects 33-52% of the planted partners after 100 generations and
     46-66% after 200. p_move = 0.6 does best.
   - **With an illustrative noisy signal** (each partner worth 0.1, noise SD 0.3; numbers chosen arbitrarily): it
     connects 8-20%, against chance levels of 3.6% (AIYL), 10.1% (RIAL) and 6.5% (AIZL).
     - *Corrected 2026-10-18 (D310; Astra): v2 said "against a chance level of about 3%", which is right for AIYL
       only and overstated the enrichment for the other two.*
   - **What it means:** even this favourable oracle leaves recovery partial at 100 generations.
     - *Corrected 2026-10-18 (D310; Astra): v2 called the noiseless oracle "the upper bound". It is not one. Its
       landscape and reward scale are its own, weights and τ do not matter to it, and the noisy version's noise is
       independent across states, unlike the simulator's shared worlds. It is a favourable-oracle diagnostic.*
     - Partial recovery can still rank partners above chance, since the ranking averages five searches. The pilot
       criteria stop the experiment if it does not.
   - **Options:**
     - keep 100 generations, and let pilot-dev's measurements and the pilot criteria decide;
     - add higher move rates to round B;
     - lengthen the search within the cap.

   I have not changed the design's budget, and a change goes back to the design with both reviewers.
   - **Round 2's answer:** both keep 100 generations and measure on the real task first (§3 gives the reading). Fable
     adds that discovery is proposal-limited even with the oracle, so the move rate is the free lever, and that the
     design's budget cannot absorb longer searches (§10). Astra adds that a higher move rate takes exploration from
     weights and τ, which the oracle ignores and the task may need.
8. **Not yet in the code** (Astra): the formal driver (pilot-check and N2) is not written. That includes the five-brain
   target-arm aggregation, families 1 and 2 on real data, and the registered readings. It comes with the
   pre-registration and is reviewed with it. Pilot-dev has one brain per arm and cannot exercise these.

## 5. DESIGN.md §8's implementation tests, and where each is

All run on the CPU in the ordinary suite (`python -m pytest tests/test_e03a_*.py`), except two marked `gpu`, which run
where CUDA is present.

| §8 requires | Test |
|---|---|
| Deletion equals a network built without X | `test_e03a_reinsert.py::test_deletion_through_the_union_equals_a_network_without_x` (re-indexed network, rtol 1e-5, atol 1e-6; and bitwise against `delete_neurons`) |
| The union mask with zeroed edges equals the network built with exactly that partner set, gap denominators included, at a declared tolerance | `::test_union_mask_equals_the_network_built_with_exactly_those_partners` (declared exact), with the sabotage `::test_an_absent_gap_partner_changes_its_neighbours_denominator_when_present` |
| The frozen background is bitwise unchanged | `::test_the_background_is_bitwise_unchanged_by_reinsertion`; MIP exact restoration `::test_mip_exact_restoration_reproduces_the_intact_brain`, `::test_restoration_with_a_self_connection`; in the driver, `baseline`'s controls (`test_e03a_script.py::test_a_failed_restoration_control_fails_the_baseline_stage`) |
| In NIP evolution, X's edges stay at zero through initialisation and every mutation | `test_e03a_arms.py::test_nip_runs_stay_pinned_through_evolution_and_intact_runs_are_unchanged` (a real lockstep evolution), sabotage `::test_without_the_scales_x_regrows_its_edges`, and `::test_intact_runs_evolve_exactly_as_without_the_nip_hooks`. (`test_e03a_reinsert.py::test_nip_pinning_holds_through_initialisation_and_mutation` checks only a spec without X's edges, where nothing can regrow; Fable, Astra) |
| Direction; gap symmetry after moves; degrees constant during a search; common random numbers | `test_e03a_reinsert.py::test_direction_in_partners_drive_x_and_out_partners_are_driven_by_it`, `::test_gap_junctions_are_symmetric_after_moves`; `test_e03a_search.py::test_partner_counts_never_change_and_refits_never_move`, `::test_common_random_numbers_every_state_of_a_generation_plays_the_same_worlds`, `::test_identical_states_score_identically_in_one_batch`, `::test_the_simulator_moves_genomes_to_the_requested_device`, `::test_a_search_generation_runs_on_cuda` (gpu) |
| The information boundary, with sabotage checks that pinning and truth isolation fail when broken | `test_e03a_search.py::test_information_boundary_free_searches_do_not_see_the_truth` (a rewired graph with the same counts: identical union, background, free-search initial states and every proposal); sabotage `::test_information_boundary_sabotage_a_leaking_initialisation_is_caught`, `::test_information_boundary_sabotage_a_leaking_proposal_is_caught`; `test_e03a_null.py::test_strata_do_not_read_the_truth` |
| A planted optimum on a small synthetic problem | `test_e03a_search.py::test_planted_optimum_is_found`, sabotage `::test_planted_optimum_is_not_found_without_moves`; at N2's scale, `development-records/planted_scale_check.py` (§4, item 7) |
| The no-task control's AUCs match the stratified null | `test_e03a_null.py::test_no_task_control_matches_the_stratified_null` (24 replicate target-arms, p roughly uniform, mean AUC within 0.03 of the null mean: a check against gross bias, not a calibration; Astra), sabotage `::test_no_task_check_can_fail_when_the_search_is_biased` |
| The replay probe's full replay equals the unperturbed episode; the rebuild passes the prescribed-sequence validation | `test_e03a_probe.py::test_full_replay_reproduces_the_unperturbed_episode_bitwise`, `::test_the_first_action_that_can_differ_is_at_2L_plus_1`, `::test_the_first_difference_is_exactly_at_action_2L_plus_1` (L = 5, 10, 20), `::test_the_rebuild_is_a_fresh_run_over_the_last_L_inputs`, `::test_prescribed_sequence_where_the_discarded_history_changes_a_slow_controllers_action`, `::test_memoryless_and_one_tick_controllers_are_unaffected_by_the_probe`, `::test_the_calibrators_closed_loop_kt_and_ktm_unchanged_kts_changed`; in the driver, `probe`'s controls |
| Family 2's procedure on simulated nulls | `test_e03a_stats.py::test_family2_simulation_under_the_sharp_null_is_at_most_nominal`, sabotage `::test_family2_simulation_detects_a_real_difference`, `::test_family2_withholds_a_target_with_a_non_finite_brain`; the full validation, 20 000 datasets per scenario, is `scripts/e03a.py family2`, recorded in `family2-validation.json` |

Beyond §8:
- `test_e03a_null.py`: the strata rules, the permutations, the AUC against a brute-force count, the support against
  brute-force enumeration, the subset AUC and the expected Jaccard.
- `test_e03a_stats.py`: Holm and the exact test against brute force; the comparisons against an explicit bootstrap loop;
  the outcome rules.
- `test_e03a_search.py`: Metropolis acceptance at an intermediate probability; adverse swaps and both swap parities;
  the coldest-replica result; snapshots.
- `test_e03a_panel.py`: the panel rule, both directions of eligibility, the relevance interval against an explicit
  bootstrap loop, and the class model against a hand count.
- `test_e03a_script.py`: the driver end to end at smoke size; the CUDA preflight (gpu).

**Rule 9.** The tests were written after the code in this round. As selected evidence that the core checks can fail,
20 bugs were planted one at a time (`development-records/mutation_check.py`, output in `mutation-check.txt`). A bug
counts as caught only if pytest reports its named test as failed, and the failing line is kept. This is not
comprehensive validation (Astra).

## 6. Changes

**v3 → v3.1 (code review round 3: run 20261018-031947; both "ready for the rest of pilot-dev, with small fixes";
D311):**
- **Controls gate the searches:** `tune` and `full` require a completed `probe` (Astra 4).
- **Saving:**
  - `full` saves every search's current state and trace every 10 generations, as well as when the ordinary searches
    end and at the end (Astra 3);
  - a rerun of `full` reuses the target-brains a stopped attempt finished (Fable 1).
- **A budget guard:** before any search, `full` is projected at `tune`'s measured rate. If it would not fit the cap,
  it is refused and the owner decides (Fable 1).
- **The paired-noise series** are kept whole, and read as mixtures, not noise; the reading rule no longer claims a
  mechanism (Astra 5).
- **Tests:** a deterministic turnover test over generations 0-20 (Astra 6).
- **Corrected:** round B's premise (§2), which was Fable's round-2 finding and was repeated in D310 and v3.
- **Documented:** the stage order in the script's docstring; the seed range; which stages ran during rounds 2 and 3.

**v2 → v3 (code review round 2: run 20261018-021702; Fable "ready for pilot-dev, with small fixes", Astra "revise";
D310):**
- **Partial results:**
  - `full` writes p, the setting and the plan into its record before any search, so a stopped `full` can be
    reported; the report takes p from `baseline`, and reports what was measured even when `full` stopped (Fable 1,
    Astra 1);
  - a missing input withholds the projection instead of failing the report;
  - each target-brain's search states are saved locally once its ordinary searches end, and again at the end; the
    rankings go into the record (Astra 2).
- **`probe` runs before the searches** (Fable 2). The full-replay control is timed and priced in the projection, one
  per brain (Astra 3). The report names each extrapolation, and no longer claims the formal target-brains have the
  measured shape.
- **Diagnostics:**
  - turnover runs over the windows 0 → 10 → … → G (Astra 4);
  - the mirror-zero subset is per type, with its sizes (Astra 4, Fable 6);
  - Fable's signal-to-noise record (finding 4);
  - the no-task control and the five attributes are written (Astra 10).
- **Small fixes:**
  - final scoring and the scan run in chunks of 16 384 worlds (Fable 5);
  - `full` checks its target-brains against `baseline`'s;
  - `expected_jaccard` gives 1 when every candidate is a partner;
  - `baseline` and `probe` stop at the first failed control (Astra 6).
- **Corrected:**
  - the planted check's chance levels (3.6%, 10.1%, 6.5%, not "about 3%");
  - "upper bound" is now "favourable-oracle diagnostic";
  - D309's "whole episodes" is now "counts, final head positions and every target event" (Astra 5, 6).
- **Kept, by both:** 100 generations and the paired 100 → 200 extensions; the reading rule in §3.
- **Open:** round B's order (§2).

**v1 → v2 (code review round 1: run 20261017-190316; Fable "ready for pilot-dev, with small fixes", Astra "revise";
D309):**
- **The CUDA search path** moved CPU genomes into CUDA rollouts. The simulator now moves them, a test checks it with the
  meta device, and the CUDA preflight runs every stage on CUDA first (Astra 1, blocking).
- **Controls stop the run:**
  - restoration, NIP deletion equivalence, the full-replay control and KT and KTM invariance now compare counts, final
    positions and every target event, inside `replay_mode()`;
  - a failure fails its stage, and the later stages require it (Astra 2).
  - Writing this, v1's counts-only check turned out to hide a NaN comparison in the event table (unfinished legs are
    NaN). The comparison treats NaN as equal.
- **The report:**
  - selection and validation are priced separately, the scan at its own rate, and the probe per brain from measured
    condition times;
  - pilot-check has 14 evolutions, not 16;
  - no rate is ever assumed, and every extrapolation is named (Astra 3, Fable 4, 11).
- **Partial results kept:** evolution checkpoints, tuning rounds and target-brains survive a stop. The cap is checked
  before setup (Astra 5, Fable 4).
- **The longer searches:**
  - the same searches are scored at generation 100 and at 200, with their diagnostics;
  - Q starts at generation 0 and is sampled after every 10 generations, beside chance;
  - Jaccard agreement replaces Spearman as the measure to freeze (Astra 4, Fable 2, 3).
- **Smaller fixes:**
  - one permutation bank per target, shared by both arms (Astra 6, Fable 8);
  - family 2 withholds a target with a non-finite brain value (Astra 7);
  - the relevance bootstrap no longer builds a [neurons, B, worlds] array (Fable 5);
  - per-pair swap rates choose the ladder (Astra 9);
  - the descriptive outputs of DESIGN.md §6 are written (Fable 11, Astra 10);
  - stronger tests (Fable 10, Astra 11);
  - the mutation check tells failures from errors (Astra 12).
- **Documented:** the NIP pinning's effect on initialisation and its DESIGN.md annotation (Astra 8, Fable 9); B and C
  as chosen, not optimised (Fable 6); the low target's diagnostics (Fable 7); the planted check at N2's scale and the
  open search-budget question (Fable 1).
