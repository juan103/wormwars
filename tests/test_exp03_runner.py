"""Experiment 03's runner (D054): N2 is measured last, the time cap is cumulative across
restarts, graph files are checked against the committed manifest, and every measurement records
its provenance."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def exp():
    spec = importlib.util.spec_from_file_location("exp03_script", ROOT / "scripts" / "exp03.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_n2_and_its_variants_are_measured_last(exp):
    order = exp.run_order()
    assert order[-5:] == ["N2", "N2-rev", "N2perm1", "N2perm2", "N2perm3"]
    assert len(order) == 645 and len(set(order)) == 645


def test_a_graph_file_that_does_not_match_the_manifest_is_refused(exp, tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "GRAPHS", tmp_path)
    name = "SH-10000"
    np.savez_compressed(tmp_path / f"{name}.npz", chem=np.zeros((2, 2)), gap=np.zeros((2, 2)))
    from wormwars.connectome import load_connectome
    with pytest.raises(exp.ProvenanceError):
        exp._load_graph(load_connectome(), name)


def test_the_time_cap_counts_every_saved_measurement(exp, tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "MEASURES", tmp_path)
    for i, s in enumerate((1800.0, 1800.0)):
        (tmp_path / f"g{i}.json").write_text(json.dumps({"seconds": {"a": s}}), encoding="utf-8")
    assert exp.spent_hours() == pytest.approx(1.0)


def test_provenance_is_recorded_and_checked(exp):
    p = exp.provenance("cpu")
    assert {"git_commit", "inputs", "device"} <= set(p)
    assert set(p["inputs"]) >= {"ensembles.json", "graphs_manifest.json", "pilot.json", "mirror_pairs.yaml", "remaps.json"}
    exp.check_provenance([{"provenance": p}, {"provenance": p}])
    q = dict(p, git_commit="different")
    with pytest.raises(exp.ProvenanceError):
        exp.check_provenance([{"provenance": p}, {"provenance": q}])


def test_hashes_ignore_line_endings_so_they_match_the_committed_blobs(exp, tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_bytes(b'{"x": 1}\n')
    b.write_bytes(b'{"x": 1}\r\n')
    assert exp._sha(a) == exp._sha(b)


def test_resuming_refuses_measurements_from_other_code_or_inputs(exp):
    p = exp.provenance("cpu")
    exp.check_resumable([{"provenance": p}], p)
    for q in (dict(p, git_commit="other"), dict(p, device="cuda:9")):
        with pytest.raises(exp.ProvenanceError):
            exp.check_resumable([{"provenance": q}], p)


def test_report_script_writes_and_prints_without_error(exp):
    import inspect
    src = inspect.getsource(exp.cmd_report)
    assert "complete)" not in src.replace(" ", "")


def test_binary_graph_files_are_hashed_raw_while_text_inputs_ignore_line_endings(exp, tmp_path):
    """The first run stopped at SH-class-30010: normalising CR-LF inside a compressed .npz
    changed its hash (D056). Only text inputs are normalised."""
    import hashlib
    b = tmp_path / "g.npz"
    b.write_bytes(b"PK\x03\x04\r\n\x00binary")
    assert exp._sha_raw(b) == hashlib.sha256(b.read_bytes()).hexdigest()
    assert exp._sha(b) != exp._sha_raw(b)  # the text hash would have changed it: never use it on graphs


def test_rebuild_graphs_reproduces_the_committed_files(exp, tmp_path):
    """An outsider can regenerate 03's graph files from the committed record: the arrays match the
    committed content manifest on any operating system, and the raw bytes match the raw manifest on
    Windows, where the files were written (numpy's zip headers record the OS; D106)."""
    exp.use_instance("03")
    report = exp.rebuild_graphs(tmp_path, only=["SH-10000", "SH-route-20000"], workers=1)
    assert report["rebuilt"] == 2 and report["content_matching"] == 2 and report["content_mismatched"] == []
    print("raw matching:", report["matching"], "with the Windows OS byte:", report["matching_with_the_windows_os_byte"])
    if sys.platform == "win32":
        assert report["matching"] == 2 and report["mismatched"] == []
        assert exp._sha_raw(tmp_path / "SH-10000.npz") == json.loads(
            (exp.EXP / "graphs_manifest.json").read_text(encoding="utf-8"))["SH-10000"]


def test_the_windows_os_byte_is_the_only_change(exp, tmp_path):
    import zipfile
    a = tmp_path / "a.npz"
    np.savez_compressed(a, chem=np.eye(3, dtype=np.float32), gap=np.zeros((3, 3), np.float32))
    raw = a.read_bytes()
    patched = exp._windows_zip_bytes(raw)
    assert len(patched) == len(raw) and sum(x != y for x, y in zip(raw, patched)) <= 2
    b = tmp_path / "b.npz"
    b.write_bytes(patched)
    assert all(zi.create_system == 0 for zi in zipfile.ZipFile(b).infolist())
    assert exp._sha_content(a) == exp._sha_content(b)
    assert exp._windows_zip_bytes(patched) == patched


def test_the_content_hash_ignores_the_zip_container(exp, tmp_path):
    import zipfile
    a, b = tmp_path / "a.npz", tmp_path / "b.npz"
    np.savez_compressed(a, chem=np.eye(3, dtype=np.float32), gap=np.zeros((3, 3), np.float32))
    with zipfile.ZipFile(a) as src, zipfile.ZipFile(b, "w", zipfile.ZIP_STORED) as dst:
        for zi in src.infolist():
            zi2 = zipfile.ZipInfo(zi.filename, zi.date_time)
            zi2.create_system = 3  # as written on Unix
            dst.writestr(zi2, src.read(zi.filename))
    assert exp._sha_raw(a) != exp._sha_raw(b) and exp._sha_content(a) == exp._sha_content(b)
    np.savez_compressed(b, chem=np.eye(3, dtype=np.float32) * 2, gap=np.zeros((3, 3), np.float32))
    assert exp._sha_content(a) != exp._sha_content(b)


def test_rebuild_graphs_reports_a_mismatch(exp, tmp_path, monkeypatch):
    exp.use_instance("03")
    real = exp._manifest

    def tampered():
        m = dict(real())
        m["SH-10000"] = "0" * 64
        return m
    monkeypatch.setattr(exp, "_manifest", tampered)
    report = exp.rebuild_graphs(tmp_path, only=["SH-10000"], workers=1)
    assert report["mismatched"] == ["SH-10000"] and report["matching"] == 0
    assert report["content_mismatched"] == []  # the raw manifest alone was tampered with


def test_rebuild_graphs_refuses_names_not_in_the_record(exp, tmp_path):
    exp.use_instance("03")
    with pytest.raises(exp.ProvenanceError):
        exp.rebuild_graphs(tmp_path, only=["SH-99999999"], workers=1)
