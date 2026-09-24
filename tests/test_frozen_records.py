"""A frozen experiment record must stay byte-for-byte what was frozen.

Corrections to a frozen experiment go in a separate, unfrozen `CORRECTIONS.md` beside it, never into
the frozen files: editing them and recomputing their hashes would erase the proof of what was
frozen (review finding, DECISIONS.md D033).

`bundle-hashes.txt` for experiment 01 was written on Windows, where Git checks text files out with
CRLF line endings, so it pins the CRLF form. On a system that checks out LF, a naive sha256 of the
file will not match. This test therefore hashes text files in their CRLF form, whatever the checkout
did. Line endings are not content; everything else must match exactly.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FROZEN = sorted(p.parent for p in (ROOT / "experiments").glob("*/bundle-hashes.txt"))
BINARY = {".npz", ".pt", ".png", ".gif", ".mp4", ".xlsx"}


def _crlf(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


@pytest.mark.parametrize("folder", FROZEN, ids=lambda p: p.name)
def test_every_pinned_file_is_exactly_what_was_frozen(folder):
    lines = (folder / "bundle-hashes.txt").read_text(encoding="utf-8").splitlines()
    pinned = [l for l in lines if l.strip() and not l.startswith("#")]
    assert pinned, "no hashes pinned"
    bad = []
    for line in pinned:
        want, _, rel = line.partition("  ")
        rel = rel.strip()
        path = ROOT / rel if rel.startswith("runs/") else folder / rel
        if not path.exists():
            bad.append(f"{rel}: missing")
            continue
        raw = path.read_bytes()
        got = hashlib.sha256(raw if path.suffix in BINARY else _crlf(raw)).hexdigest()
        if got != want:
            bad.append(f"{rel}: sha256 {got[:12]}... != pinned {want[:12]}...")
    assert not bad, "frozen record changed:\n  " + "\n  ".join(bad)


def test_experiment_01_is_frozen_and_its_corrections_live_beside_it():
    folder = ROOT / "experiments" / "01-foraging-n2-vs-controls"
    assert folder in FROZEN
    corrections = folder / "CORRECTIONS.md"
    assert corrections.exists(), "corrections to a frozen experiment belong in CORRECTIONS.md"
    pinned = (folder / "bundle-hashes.txt").read_text(encoding="utf-8")
    assert "CORRECTIONS.md" not in pinned, "CORRECTIONS.md must stay unfrozen"
