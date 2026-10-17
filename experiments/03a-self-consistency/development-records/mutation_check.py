"""Mutation check for 03a's tests (rule 9; D308): each planted bug must make its named test fail. Every file is
restored after each run. Run from anywhere: py -3.13 <this file> > mutation-check.txt"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
M = [
    ("wormwars/e03a/reinsert.py", "w[:, self.pos_in] = torch.where(st.m_in, st.w_in, zero)",
     "w[:, self.pos_out] = torch.where(st.m_in, st.w_in, zero)", "tests/test_e03a_reinsert.py::test_direction_in_partners_drive_x_and_out_partners_are_driven_by_it"),
    ("wormwars/e03a/reinsert.py", "g[:, self.pos_gap] = torch.where(st.m_gap, st.g, zero)",
     "g[:, self.pos_gap] = st.g", "tests/test_e03a_reinsert.py::test_union_mask_equals_the_network_built_with_exactly_those_partners"),
    ("wormwars/e03a/reinsert.py", "        w = self.w_bg.unsqueeze(0).repeat(S, 1)\n",
     "        w = self.w_bg.unsqueeze(0).repeat(S, 1) * 1.0000001\n", "tests/test_e03a_reinsert.py::test_the_background_is_bitwise_unchanged_by_reinsertion"),
    ("wormwars/e03a/reinsert.py", "        tau[:, self.x] = st.tau\n", "        tau[:, self.x] = st.tau\n        tau[:, (self.x + 1) % self.con.n] = st.tau\n",
     "tests/test_e03a_reinsert.py::test_mip_exact_restoration_reproduces_the_intact_brain"),
    ("wormwars/e03a/probe.py", "        for cur in keep:\n            v = self.inner.step(v, cur)\n", "        for cur in keep[1:]:\n            v = self.inner.step(v, cur)\n",
     "tests/test_e03a_probe.py::test_full_replay_reproduces_the_unperturbed_episode_bitwise"),
    ("wormwars/e03a/probe.py", "        if self.t > 0 and self.t % self.L == 0:", "        if self.t > 0 and (self.t + 1) % self.L == 0:",
     "tests/test_e03a_probe.py::test_the_first_action_that_can_differ_is_at_2L_plus_1"),
    ("wormwars/e03a/null.py", "    keys = strat[None, :] + rng.random((B, K)) * 0.5", "    keys = rng.random((B, K)) * 0.5",
     "tests/test_e03a_null.py::test_permutations_stay_within_strata_and_are_permutations"),
    ("wormwars/e03a/null.py", "    return float((1 + int((null >= observed).sum())) / (len(null) + 1))",
     "    return float((1 + int((null > observed).sum())) / (len(null) + 1))", "tests/test_e03a_null.py::test_observed_ties_with_identity_draws_are_counted"),
    ("wormwars/e03a/null.py", "    out = np.empty(n, dtype=np.int64)\n    for b, g in enumerate(groups):",
     "    groups = [set(np.nonzero(by_rank == b)[0].tolist()) for b in range(3)]\n    out = np.empty(n, dtype=np.int64)\n    for b, g in enumerate(groups):",
     "tests/test_e03a_null.py::test_a_tied_group_goes_wholly_to_the_lower_bin"),
    ("wormwars/e03a/stats.py", "    return float(obs), float((d >= obs - 1e-12).mean())", "    return float(obs), float((d > obs + 1e-12).mean())",
     "tests/test_e03a_stats.py::test_exact_p_matches_brute_force_and_counts_the_observed_split"),
    ("wormwars/e03a/stats.py", "        if p[j] <= alpha / (m - i):", "        if p[j] <= alpha / m:",
     "tests/test_e03a_stats.py::test_holm_step_down"),
    ("wormwars/e03a/search.py", "            ok = bool(d >= 0 or u < np.exp(d / T[r]))", "            ok = bool(d > 0 or u < np.exp(d / T[r]))",
     "tests/test_e03a_search.py::test_no_task_accepts_every_best_offspring_and_every_swap"),
    ("wormwars/e03a/search.py", "                m[s, a], m[s, b] = False, True", "                m[s, b] = True",
     "tests/test_e03a_search.py::test_partner_counts_never_change_and_refits_never_move"),
    ("wormwars/e03a/search.py", "            ids = np.concatenate([np.tile(asks[i][2], (asks[i][1].n, 1)) for i in idx])",
     "            ids = np.concatenate([np.tile(asks[i][2], (asks[i][1].n, 1)) + np.arange(asks[i][1].n)[:, None] for i in idx])",
     "tests/test_e03a_search.py::test_common_random_numbers_every_state_of_a_generation_plays_the_same_worlds"),
    ("wormwars/e03a/search.py", "        out.append(free_search(problem, scfg, bcfg, mcfg, search_seed(seed, \"free\", i), label=f\"free-{i}\", **kw))",
     "        out.append(free_search(Problem(problem.K, problem.counts, problem.self_loop), scfg, bcfg, mcfg, search_seed(seed, \"free\", i), label=f\"free-{i}\", **kw))\n        out[-1].current.bias += float(np.asarray(truth['in']).nonzero()[0][0]) * 1e-3",
     "tests/test_e03a_search.py::test_information_boundary_free_searches_do_not_see_the_truth"),
    ("wormwars/e03a/panel.py", "    to_iface = _reach(fwd.T, mapped)  # can reach the interface", "    to_iface = set(range(con.n))",
     "tests/test_e03a_panel.py::test_a_neuron_with_no_path_to_the_interface_is_not_eligible"),
    ("wormwars/e03a/structural.py", "        out[\"in\"][k] = chem[mc, xp]", "        out[\"in\"][k] = chem[xp, mc]",
     "tests/test_e03a_panel.py::test_mirror_ranking_reads_the_partners_mirror"),
]
bad = 0
for path, a, b, test in M:
    p = ROOT / path
    src = p.read_text(encoding="utf-8")
    assert src.count(a) == 1, (path, a[:60])
    p.write_text(src.replace(a, b), encoding="utf-8", newline="\n")
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", test], cwd=ROOT, capture_output=True, text=True)
    finally:
        p.write_text(src, encoding="utf-8", newline="\n")
    killed = r.returncode != 0
    bad += not killed
    print(("KILLED  " if killed else "SURVIVED") + "  " + test.split("::")[1])
print("survivors:", bad)
