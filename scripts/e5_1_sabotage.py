"""Seeing E5-1's checks fail (AGENTS.md rule 9). Tests seen failing before their code existed are logged in
runs/e5-1/*-first-fail*.txt; the rest (the settings, the plan, the hosts and arms, and checks that a first run passed)
are run here under a sabotage of the behaviour they check, and must fail; then the files run clean. The log is
runs/e5-1/sabotage_log.txt.

    python scripts/e5_1_sabotage.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "runs" / "e5-1" / "sabotage_log.txt"
FILES = ["tests/test_e5_mixed.py", "tests/test_e5_ga.py", "tests/test_e5_arms.py", "tests/test_e5_genome_guards.py"]

PLUGIN = r'''
import os
import numpy as np
import torch
import wormwars.e5.settings as ST
import wormwars.e5.prey as P
import wormwars.e5.hunt as H
import wormwars.e5.plan as PL
import wormwars.e5.graphs as GR
import wormwars.e5.arms as AR
import wormwars.e5.ga as GA
import wormwars.e04a.evolve as EV
import wormwars.e4s.arms as EA

name = os.environ["E5_1_SABOTAGE"]
if name == "weights_off":
    orig = ST.weighted_fitness
    ST.weighted_fitness = lambda c, weights=(10, 2, 2, 2, 2, 2, 4, 6): orig(c, weights)
elif name == "suite_order":
    ST.SUITE = ST.SUITE[:8] + ST.SUITE[9:10] + ST.SUITE[8:9] + ST.SUITE[10:]
elif name == "speeds_h2b":
    ST.SPEEDS_H2B = (0.25, 0.5, 0.8)
elif name == "prey_spacing":
    orig = ST.prey_params
    def prey_params():
        p = orig(); p["route"]["spacing"] = 7.0; return p
    ST.prey_params = prey_params
elif name == "score_plain_mean":
    ST.suite_score = lambda means: float(np.mean([means[n] for n in ST.SUITE]))
elif name == "column_weights_unchecked":
    ST.column_weights = lambda slots: np.asarray(ST.TRAINING_WEIGHTS, dtype=np.int64)[np.asarray(slots)]
elif name == "mixed_route_gain":
    orig = P.MixedPrey.attach_world
    def attach_world(self, world):
        orig(self, world); self.gain = self.gain * 1.01
    P.MixedPrey.attach_world = attach_world
elif name == "mixed_speed_shifted":
    orig = P.MixedPrey.attach_world
    def attach_world(self, world):
        orig(self, world); self.speed_t = self.speed_t.roll(1)
    P.MixedPrey.attach_world = attach_world
elif name == "pin_push_lost":
    orig = H.HuntWorld._resolve_move
    def _resolve_move(self, proposed):
        before = self.pin_push.clone()
        out = orig(self, proposed)
        if self.pinned is None:
            self.pin_push = before
        return out
    H.HuntWorld._resolve_move = _resolve_move
elif name == "route_key_life":
    orig = P.RouteTable.get
    P.RouteTable.get = lambda self, world, i, life, start=None, spacing=6.0: orig(self, world, i, life + 1, start, spacing)
elif name == "route_cache_ignores_life":
    orig = P.RouteTable.get
    def get(self, world, i, life, start=None, spacing=6.0):
        return orig(self, world, i, 0, None, spacing) if life > 0 else orig(self, world, i, life, start, spacing)
    P.RouteTable.get = get
elif name == "validation_plain_mean":
    orig = EV._weighted
    def _weighted(counts, w):
        return np.asarray(counts, dtype=np.float64).mean(axis=1) if np.asarray(w).size != 8 else orig(counts, w)
    EV._weighted = _weighted
elif name == "ledger_unchecked":
    GA.LEDGER_TOL = float("inf")
    orig = GA.TaskHRollout.__init__
    def __init__(self, *a, **k):
        orig(self, *a, **k); self.ledger_tol = float("inf")
    GA.TaskHRollout.__init__ = __init__
elif name == "blocks_overlap":
    PL.BLOCKS["o0"] = (985_721_000, 64)
elif name == "pilot_schedule_shared":
    PL.BLOCKS["pilot_training"] = PL.BLOCKS["formal_training"]
elif name == "scan_blind":
    def pytest_runtest_setup(item):  # the test module's own exemption list, emptied: plan.py's literals are seen
        item.module.E5_1_FILES = set()
elif name == "shr_seed_base":
    PL.SEED_BASE["G-SHr"] = 1_511_100
elif name == "admission_duplicate":
    PL.ADMISSION = PL.ADMISSION[:-1] + ("S18",)
elif name == "manifest_ignored":
    GR.content_sha256 = lambda arrays: "0" * 64
elif name == "l1_output_missing":
    orig = EA.load_l1
    def load_l1(*a, **k):
        m = orig(*a, **k)
        syn = tuple(s for s in m.synapses if s[1] != "SMDDL")
        return type(m)(m.name, m.neurons, syn, dict(m.tau), dict(m.bias), dict(m.noses), m.nose_gain, m.neuron_class)
    EA.load_l1 = load_l1
elif name == "gains_swapped":
    orig = GR.calibrated_gains
    GR.calibrated_gains = lambda n: tuple(reversed(orig(n)))
elif name == "a0r_keeps_gaps":
    orig = AR.lesioned
    def lesioned(genome, ext):
        out = orig(genome, ext)
        return out.with_params(g=genome.g)
    AR.lesioned = lesioned
elif name == "a0_gaps_free":
    orig = AR.scales
    def scales(ext, l1, arm):
        s = orig(ext, l1, arm); s["g"] = torch.ones_like(s["g"]); return s
    AR.scales = scales
elif name == "lesion_takes_the_module":
    def lesioned(genome, ext):
        return genome.with_params(w=torch.zeros_like(genome.w), g=torch.zeros_like(genome.g))
    AR.lesioned = lesioned
elif name == "p_not_permuted":
    AR.permuted_config = lambda bcfg, k: bcfg
elif name == "g_n2_other_seed":
    orig = AR.initial
    def initial(arm, run_seed, *a, **k):
        return orig(arm, run_seed + 1 if arm == "G-N2" else run_seed, *a, **k)
    AR.initial = initial
elif name == "identity_by_label":
    import hashlib
    AR.edge_hash = lambda spec: hashlib.sha256(b"N2").hexdigest()
elif name == "ga_sigma":
    PL.GA["mutation"]["w_sigma"] = 0.1
else:
    raise SystemExit(f"unknown sabotage {name}")
'''

M, G_, A = "tests/test_e5_mixed.py", "tests/test_e5_ga.py", "tests/test_e5_arms.py"
CASES = [
    ("weights_off", M, "test_the_weighted_fitness_is_the_scores_thirds"),
    ("suite_order", M, "test_the_suite_and_training_mixture_follow_the_design"),
    ("speeds_h2b", M, "test_the_settings_are_e5_0s"),
    ("prey_spacing", M, "test_the_prey_parameters_come_from_e5_0s_records"),
    ("score_plain_mean", M, "test_the_suite_score_is_the_mean_of_three_strata"),
    ("column_weights_unchecked", M, "test_validation_weights_follow_the_slots"),
    ("mixed_route_gain", M, "test_a_mixed_prey_of_one_kind_is_the_prey"),
    ("mixed_speed_shifted", M, "test_the_mixed_world_is_each_slot_alone"),
    ("pin_push_lost", M, "test_a_per_world_pin_matches_the_single_pin"),
    ("route_key_life", M, "test_the_route_cache_draws_e5_0s_waypoints"),
    ("route_cache_ignores_life", M, "test_the_route_cache_draws_e5_0s_waypoints"),
    ("validation_plain_mean", G_, "test_weights_drive_selection_and_the_validation_score"),
    ("ledger_unchecked", G_, "test_the_rollout_stops_on_sequence_overflow_and_on_the_ledger"),
    ("blocks_overlap", A, "test_the_world_id_blocks_are_disjoint_and_match_the_design"),
    ("pilot_schedule_shared", A, "test_formal_and_pilot_training_schedules_share_no_id"),
    ("scan_blind", A, "test_no_earlier_stage_uses_e5_1s_ids_or_seeds"),
    ("shr_seed_base", A, "test_the_run_seeds_follow_the_design"),
    ("admission_duplicate", A, "test_the_admission_order_holds_every_test_batch_once"),
    ("manifest_ignored", A, "test_an_sh_route_graph_is_rebuilt_to_03rs_manifest"),
    ("l1_output_missing", A, "test_the_graft_keeps_l1s_outputs_and_noses_on_both_hosts"),
    ("gains_swapped", A, "test_calibrated_gains_are_03rs"),
    ("g_n2_other_seed", A, "test_g_n2_is_e4s1s_m_construction"),
    ("a0r_keeps_gaps", A, "test_a0r_is_g_n2s_draw_with_the_host_wiring_zeroed"),
    ("a0_gaps_free", A, "test_the_anchors_pin_the_host_wiring_and_free_its_biases_and_tau"),
    ("lesion_takes_the_module", A, "test_the_lesion_zeroes_only_the_host_wiring"),
    ("p_not_permuted", A, "test_p_permutes_the_hosts_initial_magnitudes_only"),
    ("identity_by_label", A, "test_run_records_carry_the_graphs_identity"),
    ("ga_sigma", A, "test_the_ga_is_e2s_as_e4s1_ran_it"),
]


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    lines, bad = [], []
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "e51sab.py").write_text(PLUGIN, encoding="utf-8")
        for sab, file, test in CASES:
            env = {**os.environ, "E5_1_SABOTAGE": sab,
                   "PYTHONPATH": os.pathsep.join([tmp, str(ROOT), os.environ.get("PYTHONPATH", "")])}
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "e51sab", f"{file}::{test}"], cwd=ROOT,
                               env=env, capture_output=True, text=True)
            ok = r.returncode == 1  # a test failure, not a collection or plugin error
            tail = (r.stdout.strip().splitlines() or [""])[-1]
            lines.append(f"{sab:28s} -> {test}: {'FAILED as required' if ok else f'NOT CAUGHT (rc {r.returncode})'}"
                         f"  [{tail}]")
            if not ok:
                bad.append(sab)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", *FILES], cwd=ROOT, capture_output=True, text=True)
    lines.append(f"clean run: rc {r.returncode}  [{(r.stdout.strip().splitlines() or [''])[-1]}]")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 1 if bad or r.returncode != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
