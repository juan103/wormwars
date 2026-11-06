"""Seeing E5-0's Task H tests fail (AGENTS.md rule 9). The code came before its tests, so each test is run under a
sabotage of the behaviour it checks, and must fail; then the suite runs clean. The log is
runs/e5-0/sabotage_log.txt.

    python scripts/e5_0_sabotage.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "runs" / "e5-0" / "sabotage_log.txt"
TEST = "tests/test_e5_hunt.py"

PLUGIN = r'''
import os, torch
import wormwars.e5.hunt as H
import wormwars.e5.prey as P
import wormwars.world as WD

name = os.environ["E5_SABOTAGE"]
if name == "scent_off_centre":
    orig = H.HuntWorld.prey_scent
    def prey_scent(self):
        p = self.pos.clone(); self.pos[:, 1, 0, 0] += 0.01
        try:
            return orig(self)
        finally:
            self.pos.copy_(p)
    H.HuntWorld.prey_scent = prey_scent
elif name == "ledger_ignores_respawn":
    H.HuntLedger.net = lambda self: WD.Ledger.net(self) - self.removed
elif name == "crowding_active":
    orig_cfg = H.hunt_config
    def hunt_config(base=None):
        c = orig_cfg(base); c.world.crowd_threshold = 0.3; return c
    H.hunt_config = hunt_config
elif name == "prey_bites_and_hunter_attack_ignored":
    orig = H.HuntWorld.__init__
    def __init__(self, *a, **k):
        orig(self, *a, **k); self.attack_scale = torch.ones(2)
    H.HuntWorld.__init__ = __init__
elif name == "respawn_on_the_hunter":
    orig = H.HuntWorld._capture
    def _capture(self, caught):
        orig(self, caught)
        if bool(caught.any()):
            self.pos[caught, 1, 0] = self.pos[caught, 0, 0] + 1.0
    H.HuntWorld._capture = _capture
elif name == "route_skips_waypoints":
    orig = P.PreyBrain.step
    def step(self, v, current):
        if self.kind == "route":
            self.wp = torch.zeros_like(self.wp)  # always steer at the start: no laps, no ordered visits
        return orig(self, v, current)
    P.PreyBrain.step = step
elif name == "route_ignores_speed":
    orig = P.PreyBrain.__init__
    def __init__(self, *a, **k):
        orig(self, *a, **k); self.speed = min(self.speed, 0.1)
    P.PreyBrain.__init__ = __init__
elif name == "body_probe_keeps_the_body":
    orig = H.HuntWorld.__init__
    def __init__(self, *a, **k):
        orig(self, *a, **k); self.prey_body = True
    H.HuntWorld.__init__ = __init__
elif name == "constant_on_both":
    H.HuntWorld._sensor_signals = WD.World._sensor_signals
elif name == "damage_by_energy_difference":
    def _combat(self):
        ar = torch.arange(self.n_worlds)
        before = self.energy[:, 1, 0].double()
        WD.World._combat(self)
        self.ev_damage[ar, self.life] += before - self.energy[:, 1, 0].double()
    H.HuntWorld._combat = _combat
elif name == "stops_early":
    H.HuntWorld.done = lambda self: self.tick_count >= 30
elif name == "no_task_guard":
    WD.World._hunt_task = True
elif name == "attack_scale_not_exact":
    orig = WD.World._combat
    def _combat(self):
        if self.attack_scale is not None and not isinstance(self, H.HuntWorld):
            self.attack_scale = self.attack_scale * 1.001
        return orig(self)
    WD.World._combat = _combat
'''

CASES = [
    ("scent_off_centre", "test_a_ghost_prey_is_task_n"),
    ("ledger_ignores_respawn", "test_the_ledger_balances_through_captures"),
    ("crowding_active", "test_a_pinned_prey_never_moves_and_one_on_one_crowding_never_pushes"),
    ("prey_bites_and_hunter_attack_ignored", "test_bites_need_the_hunters_attack_and_the_prey_never_bites"),
    ("respawn_on_the_hunter", "test_each_new_life_starts_at_least_d_minus_r_from_the_hunter"),
    ("route_ignores_speed", "test_the_route_follower_moves_along_its_loop"),
    ("route_skips_waypoints", "test_the_route_follower_moves_along_its_loop"),
    ("body_probe_keeps_the_body", "test_the_body_probe_keeps_the_bites_and_removes_the_prey_from_the_body_field"),
    ("constant_on_both", "test_the_constant_probe_replaces_the_hunters_food_channels_only"),
    ("damage_by_energy_difference", "test_damage_is_booked_from_combat_without_rounding"),
    ("stops_early", "test_the_episode_runs_to_the_horizon"),
    ("no_task_guard", "test_the_hunt_task_needs_its_world_and_the_world_needs_its_task"),
    ("attack_scale_not_exact", "test_an_attack_scale_of_one_changes_nothing_in_an_existing_fight"),
]


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    lines, bad = [], []
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "e5sab.py").write_text(PLUGIN, encoding="utf-8")
        for sab, test in CASES:
            env = {**os.environ, "E5_SABOTAGE": sab,
                   "PYTHONPATH": os.pathsep.join([tmp, str(ROOT), os.environ.get("PYTHONPATH", "")])}
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "e5sab", f"{TEST}::{test}"], cwd=ROOT,
                               env=env, capture_output=True, text=True)
            ok = r.returncode != 0
            tail = (r.stdout.strip().splitlines() or [""])[-1]
            lines.append(f"{sab:40s} -> {test}: {'FAILED as required' if ok else 'PASSED (sabotage not caught)'}"
                         f"  [{tail}]")
            if not ok:
                bad.append(sab)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", TEST], cwd=ROOT, capture_output=True, text=True)
    lines.append(f"clean run: rc {r.returncode}  [{(r.stdout.strip().splitlines() or [''])[-1]}]")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 1 if bad or r.returncode != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
