"""The shared guards for pre-registered runs (`wormwars/registration.py`, D103)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from wormwars import registration as reg


def _prov(**kw):
    p = {"git_commit": "abc", "branch": "roadmap", "dirty": False, "python": "3.13.1",
         "gpu": "NVIDIA GeForce RTX 5080"}
    p.update({k: v for k, v in reg.pinned().items() if k != "python"})
    p.update(kw)
    return p


def test_a_start_marker_is_exclusive(tmp_path):
    reg.start_marker(tmp_path, "train", _prov())
    with pytest.raises(SystemExit, match="not rerun"):
        reg.start_marker(tmp_path, "train", _prov())


def test_json_is_written_with_lf_and_hashed_normalised(tmp_path):
    p = tmp_path / "a.json"
    reg.write_json(p, {"x": [1, 2]})
    raw = p.read_bytes()
    assert b"\r\n" not in raw and raw.endswith(b"\n")
    crlf = tmp_path / "b.json"
    crlf.write_bytes(raw.replace(b"\n", b"\r\n"))
    assert reg.file_sha256(p) == reg.file_sha256(crlf)


def test_an_atomic_write_leaves_no_temporary_file(tmp_path):
    p = tmp_path / "ck.json"
    reg.write_json(p, {"a": 1}, atomic=True)
    reg.write_json(p, {"a": 2}, atomic=True)
    assert json.loads(p.read_text()) == {"a": 2}
    assert [f.name for f in tmp_path.iterdir()] == ["ck.json"]


def test_formal_stages_refuse_the_cpu():
    with pytest.raises(SystemExit, match="CUDA"):
        reg.require_formal("cpu", _prov())


@pytest.mark.parametrize("bad, match", [({"python": "3.12.4"}, "pinned"), ({"torch": "0.0"}, "pinned"),
                                        ({"numpy": "0.0"}, "pinned")])
def test_the_pins_are_enforced(bad, match):
    with pytest.raises(SystemExit, match=match):
        reg.require_pins(_prov(**bad))
    reg.require_pins(_prov())


def test_formal_stages_refuse_another_gpu_a_dirty_tree_and_an_unpushed_head(monkeypatch):
    monkeypatch.setattr(reg.torch.cuda, "is_available", lambda: True)
    with pytest.raises(SystemExit, match="registered GPU"):
        reg.require_formal("cuda", _prov(gpu="NVIDIA A100"))
    with pytest.raises(SystemExit, match="uncommitted"):
        reg.require_formal("cuda", _prov(dirty=True))
    calls = []

    def fake_run(cmd, cwd=None, check=False):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 1 if "merge-base" in cmd else 0)

    monkeypatch.setattr(reg.subprocess, "run", fake_run)
    with pytest.raises(SystemExit, match="not pushed"):
        reg.require_formal("cuda", _prov())
    assert any("fetch" in c for c in calls)


def test_the_cap_counts_earlier_attempts_and_this_process(tmp_path, monkeypatch):
    rec = tmp_path / "compute.json"
    rec.write_text(json.dumps({"totals": {"seconds_timed": 3600 * 0.9}}))
    t = [100.0]
    monkeypatch.setattr(reg.time, "perf_counter", lambda: t[0])
    clock = reg.CapClock(1.0, rec)
    clock.check()
    t[0] += 0.2 * 3600
    with pytest.raises(reg.CapReached):
        clock.check()


def test_the_cap_with_no_record_starts_at_zero(tmp_path):
    clock = reg.CapClock(1.0, tmp_path / "missing.json")
    assert clock.spent_hours() == 0.0
    clock.check()


def test_the_lower_bound_is_below_the_mean_and_reproducible():
    d = np.random.default_rng(1).normal(1.0, 1.0, 500)
    lb = reg.lower_bound(d)
    assert lb < d.mean() and lb == reg.lower_bound(d)
    assert reg.lower_bound(np.full(50, 2.0)) == 2.0


def test_the_same_code_check_accepts_output_only_commits_and_refuses_code(tmp_path):
    def g(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)

    g("init", "-q")
    g("config", "user.email", "t@example.invalid")
    g("config", "user.name", "t")
    (tmp_path / "code.py").write_text("a = 1\n")
    g("add", ".")
    g("commit", "-qm", "code")
    base = reg.git("rev-parse", "HEAD", root=tmp_path)
    (tmp_path / "out.json").write_text("{}\n")
    g("add", ".")
    g("commit", "-qm", "output")
    reg.require_same_code(base, ["code.py"], root=tmp_path)
    (tmp_path / "code.py").write_text("a = 2\n")
    g("commit", "-qam", "change")
    with pytest.raises(SystemExit, match="changed since"):
        reg.require_same_code(base, ["code.py"], root=tmp_path)


def test_the_environment_check_names_what_differs():
    was = _prov(connectome_cache_sha256="x")
    reg.require_same_env(was, dict(was))
    with pytest.raises(SystemExit, match="connectome_cache_sha256"):
        reg.require_same_env(was, {**was, "connectome_cache_sha256": "y"})
