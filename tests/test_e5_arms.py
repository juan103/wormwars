"""E5-1's fixed numbers, hosts and arms (docs/E5/E5-1-DESIGN.md §3, §4, §6, §7.2, §9).

The code came before these tests; each is seen failing under a sabotage of what it checks (scripts/e5_1_sabotage.py,
runs/e5-1/sabotage_log.txt).
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome.loader import load_connectome
from wormwars.e4s import arms as EA
from wormwars.e4s import comparator as CMP
from wormwars.e5 import arms as AR
from wormwars.e5 import graphs as GR
from wormwars.e5 import plan as PL

ROOT = Path(__file__).resolve().parents[1]
# E5-1's numbers live in plan.py; the old-against-new reference script cannot import it (it runs on E5-0's engine),
# so its copies are checked against plan.py below
E5_1_FILES = {"wormwars/e5/plan.py", "scripts/e5_1_reference.py", "scripts/e5_1_sabotage.py"}


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def l1():
    return EA.load_l1()


@pytest.fixture(scope="module")
def bcfg():
    return Config().brain


# ----------------------------------------------------------------------------------------------- world ids and seeds
def _ranges():
    return {k: (a, a + n) for k, (a, n) in PL.BLOCKS.items()}


def test_the_world_id_blocks_are_disjoint_and_match_the_design():
    r = sorted(_ranges().items(), key=lambda kv: kv[1])
    for (ka, (a0, a1)), (kb, (b0, b1)) in zip(r, r[1:]):
        assert a1 <= b0, f"{ka} overlaps {kb}"
    assert PL.BLOCKS["formal_validation"] == (985_600_000, 256)
    assert PL.BLOCKS["suite"] == (985_700_000, 17 * 512)
    assert PL.suite_ids("H2b-wall-0.75")[-1] == 985_700_000 + 512 * 17 - 1
    assert PL.suite_ids("H2-0.1")[0] == 985_700_000 + 512 * 8
    assert PL.bridge_ids("H1-reach")[0] == 985_720_512
    assert PL.ids("cuda_checks")[-1] == 985_800_000 + 40_960 - 1


def test_formal_and_pilot_training_schedules_share_no_id():
    from wormwars.e04a.evolve import train_ids
    fa, fn = PL.BLOCKS["formal_training"]
    pa, pn = PL.BLOCKS["pilot_training"]
    assert fa + fn <= pa or pa + pn <= fa  # the spans themselves are disjoint, so no draw can be shared
    formal = np.concatenate([train_ids(PL.run_seed("G-N2", 0), g, 8, fa, fn) for g in range(50)])
    pilot = np.concatenate([train_ids(PL.run_seed("pilot_null", 0, 0), g, 8, pa, pn) for g in range(50)])
    assert formal.min() >= fa and formal.max() < fa + fn and pilot.min() >= pa and pilot.max() < pa + pn
    assert not set(formal.tolist()) & set(pilot.tolist())
    with pytest.raises(ValueError):
        PL.ids("formal_training")


def _literals(lo, hi):
    """Integer literals in [lo, hi) in every Python file of the tree (tracked or new) but E5-1's own."""
    import subprocess
    files = [f for f in subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard",
                                                 "*.py"], cwd=ROOT, text=True).splitlines()
             if f not in E5_1_FILES and not f.startswith("tests/test_e5_")]
    out = []
    for f in files:
        text = (ROOT / f).read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"(?<![\w.])(\d[\d_]{6,})(?![\w.])", text):
            v = int(m.group(1).replace("_", ""))
            if lo <= v < hi:
                out.append(f"{f}: {m.group(1)}")
    return out


def test_no_earlier_stage_uses_e5_1s_ids_or_seeds():
    """Every earlier block in this repository is a literal start with a span of at most 1 M (E2, E4s-1: 500 000), so
    a start within 2 M below E5-1's first id, or inside its blocks, would reach them."""
    assert _literals(983_000_000, 986_300_000) == []
    assert _literals(1_505_000, 1_530_000) == []


def test_the_reference_scripts_copies_are_plans():
    import importlib.util
    spec = importlib.util.spec_from_file_location("e5_1_reference_for_test", ROOT / "scripts" / "e5_1_reference.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    from wormwars.e5 import settings as ST
    p = ST.prey_params()
    assert m.WORLD_SEED == PL.WORLD_SEED and m.IDS_FIRST == PL.BLOCKS["cuda_checks"][0]
    assert m.IDS_COUNT <= PL.BLOCKS["cuda_checks"][1] and m.E_PREY == p["e_prey"]
    assert m.ROUTE == p["route"] and m.WALK == p["walk"]
    assert [s[0] for s in m.settings()] == [s["name"] for s in ST.e5_0_settings()]
    assert [(s["rule"], s["prey"], s["speed"], s["pinned"]) for s in ST.e5_0_settings()] == [s[1:] for s in m.settings()]


def test_the_run_seeds_follow_the_design():
    assert PL.run_seed("G-N2", 31) == 1_510_031 == PL.run_seed("B", 31) == PL.run_seed("A0r", 31)
    assert PL.run_seed("G-SHr", 3, 19) == 1_511_000 + 4 * 19 + 3
    assert PL.run_seed("A0", 7) == 1_512_007
    assert PL.run_seed("P", 1, 2) == 1_513_009
    assert PL.run_seed("pilot_null", 2, 1) == 1_518_006 and PL.run_seed("pilot_n2", 3) == 1_519_003
    with pytest.raises(ValueError):
        PL.run_seed("G-SHr", 4, 0)


def test_the_admission_order_holds_every_test_batch_once():
    units = PL.ADMISSION
    assert len(units) == 28 and len(set(units)) == 28
    assert sorted(u for u in units if u.startswith("N")) == [f"N{k}" for k in range(1, 9)]
    assert sorted((u for u in units if u.startswith("S")), key=lambda u: int(u[1:])) == [f"S{j}" for j in range(20)]
    runs = sorted(r for u in units if u.startswith("N") for r in PL.batch_units(u)["runs"])
    assert runs == list(range(32))
    s5 = PL.batch_units("S5")
    assert s5["graph"] == "SH-route-1020005" and s5["seeds"] == [1_511_020, 1_511_021, 1_511_022, 1_511_023]
    assert PL.SH_ROUTE_CUT == PL.SH_ROUTE[:16] and PL.SH_ROUTE_PILOT[0] == "SH-route-1020020"
    assert not set(PL.SH_ROUTE) & set(PL.SH_ROUTE_PILOT)


# ----------------------------------------------------------------------------------------------- hosts
def test_an_sh_route_graph_is_rebuilt_to_03rs_manifest(con):
    g, info = GR.sh_route(con, "SH-route-1020000")
    assert info["matches_content_manifest"] and g.label == "SH-route-1020000"
    assert g.chem.shape == con.chem.shape and not np.array_equal(g.chem > 0, con.chem > 0)
    assert int((g.chem > 0).sum()) == int((con.chem > 0).sum())  # the degree sequence keeps the edge count
    with pytest.raises(ValueError):
        GR.sh_route(con, "SH-1010000")


def test_the_graft_keeps_l1s_outputs_and_noses_on_both_hosts(con, l1):
    g, _ = GR.sh_route(con, "SH-route-1020001")
    for host in (con, g):
        ext, spec, iface = GR.grafted(host, l1)
        assert spec.n == 306 and ext.label == f"{host.label}+comparator-L1"
        assert int(EA.output_edge_mask(ext, l1).sum()) == 16


def test_calibrated_gains_are_03rs():
    f, t = GR.calibrated_gains("N2")
    assert t == pytest.approx(2.0829, abs=1e-4)
    assert all(np.isfinite(GR.calibrated_gains(n)).all() for n in ("N2perm4", "SH-route-1020000"))


# ----------------------------------------------------------------------------------------------- arms
def _ext(con, l1):
    return GR.grafted(con, l1)[0]


def test_g_n2_is_e4s1s_m_construction(con, l1, bcfg):
    ext = _ext(con, l1)
    a = AR.initial("G-N2", 1_510_000, con, ext, l1, bcfg, 32)
    b = CMP.embedded_population(con, ext, l1, bcfg, run_seed=1_510_000, population=32)
    assert torch.equal(a.flat(), b.flat())


def test_a0r_is_g_n2s_draw_with_the_host_wiring_zeroed(con, l1, bcfg):
    ext = _ext(con, l1)
    hw, hg = AR.host_masks(ext)
    g = AR.initial("G-N2", 1_510_003, con, ext, l1, bcfg, 32)
    a = AR.initial("A0r", 1_510_003, con, ext, l1, bcfg, 32)
    assert (a.w[:, hw] == 0).all() and (a.g[:, hg] == 0).all()
    assert torch.equal(a.w[:, ~hw], g.w[:, ~hw]) and torch.equal(a.tau, g.tau) and torch.equal(a.bias, g.bias)
    assert (g.w[:, hw] != 0).any()


def test_the_anchors_pin_the_host_wiring_and_free_its_biases_and_tau(con, l1, bcfg):
    ext = _ext(con, l1)
    hw, hg = AR.host_masks(ext)
    _, _, me, _, mn = EA._masks(ext)
    for arm in ("A0", "A0r"):
        s = AR.scales(ext, l1, arm)
        assert (s["w"][hw] == 0).all() and (s["g"][hg] == 0).all()
        assert (s["w"][me] == 0.25).all() and (s["tau"][mn] == 0.25).all() and (s["tau"][~mn] == 1).all()
        assert (s["bias"][~mn] == 1).all()
    s = AR.scales(ext, l1, "G-N2")
    assert (s["w"][hw] == 1).all() and (s["g"] == 1).all() and (s["w"][me] == 0.25).all()
    a0 = AR.initial("A0", 1_512_000, con, ext, l1, bcfg, 32)
    ref = CMP.carrier_genome(ext, l1, bcfg, forward=1.0, turn=0.2, n_strains=32)
    assert torch.equal(a0.flat(), ref.flat()) and (a0.w[:, hw] == 0).all() and (a0.g == 0).all()
    gen = torch.Generator().manual_seed(0)
    m = a0.clone()
    for _ in range(5):
        m.mutate(Config().mutation, generator=gen, scales=AR.scales(ext, l1, "A0"))
    assert (m.w[:, hw] == 0).all() and (m.g[:, hg] == 0).all()
    assert not torch.equal(m.bias[:, :302], a0.bias[:, :302]) and not torch.equal(m.w[:, me], a0.w[:, me])


def test_the_lesion_zeroes_only_the_host_wiring(con, l1, bcfg):
    ext = _ext(con, l1)
    hw, hg = AR.host_masks(ext)
    g = AR.initial("G-N2", 1_510_001, con, ext, l1, bcfg, 4)
    les = AR.lesioned(g, ext)
    assert (les.w[:, hw] == 0).all() and (les.g[:, hg] == 0).all()
    assert torch.equal(les.w[:, ~hw], g.w[:, ~hw]) and torch.equal(les.tau, g.tau) and torch.equal(les.bias, g.bias)
    assert int(hw.sum()) == BrainSpec.from_connectome(con).n_chem and int(hg.sum()) == BrainSpec.from_connectome(con).n_gap


def test_p_permutes_the_hosts_initial_magnitudes_only(con, l1, bcfg):
    ext = _ext(con, l1)
    hw, hg = AR.host_masks(ext)
    _, _, me, _, mn = EA._masks(ext)
    seed = PL.run_seed("P", 0, 0)
    p = AR.initial("P", seed, con, ext, l1, bcfg, 4, perm_seed=4)
    n2 = AR.initial("G-N2", seed, con, ext, l1, bcfg, 4)  # the same seed: signs, tau and biases pair
    assert p.cfg == bcfg and p.spec.same_as(n2.spec)
    assert torch.equal(p.w[:, me], n2.w[:, me]) and torch.equal(p.tau, n2.tau) and torch.equal(p.bias, n2.bias)
    assert torch.equal(p.w[:, hw].abs().sort(dim=1).values, n2.w[:, hw].abs().sort(dim=1).values)
    assert not torch.equal(p.w[:, hw].abs(), n2.w[:, hw].abs())
    assert torch.equal(p.g.sort(dim=1).values, n2.g.sort(dim=1).values) and not torch.equal(p.g, n2.g)
    assert AR.host_magnitude_sha256(p, ext) != AR.host_magnitude_sha256(n2, ext)
    q = AR.initial("P", seed, con, ext, l1, bcfg, 4, perm_seed=5)
    assert not torch.equal(p.w, q.w)


def test_b_is_32_copies_of_one_champion(con, l1, bcfg):
    ext = _ext(con, l1)
    champ = AR.initial("G-N2", 1, con, ext, l1, bcfg, 1)
    b = AR.initial("B", PL.run_seed("B", 0), con, ext, l1, bcfg, 32, champion=champ)
    assert b.n_strains == 32 and torch.equal(b.flat(), champ.flat().expand(32, -1))


def test_run_records_carry_the_graphs_identity(con, l1):
    g, _ = GR.sh_route(con, "SH-route-1020002")
    a, b = AR.identity("G-N2", 0, 1, "N2", _ext(con, l1)), AR.identity("G-SHr", 8, 2, g.label, _ext(g, l1))
    assert a["edge_sha256"] != b["edge_sha256"] and b["label"] == "SH-route-1020002+comparator-L1"
    assert a["n_chem"] == b["n_chem"]


def test_the_ga_is_e2s_as_e4s1_ran_it():
    """E4s-1 ran E2's registered GA (scripts/e4s1.py copies `E.REGISTERED["ga"]`); E5-1's is the same but for the
    generation count."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("e2_for_e5_1_test", ROOT / "scripts" / "e2.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    want = {k: v for k, v in m.REGISTERED["ga"].items() if k != "generations"}
    assert PL.GA == want
    assert PL.CHECKPOINT_EVERY == m.REGISTERED["checkpoint_every"]
