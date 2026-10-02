"""No E3 test may run on E3a's registered world blocks or with its evaluation world seed: those are read
only by the formal stages (PREREGISTRATION §7; D166, after the assay tests did so once)."""

from __future__ import annotations

import re
from pathlib import Path

REGISTERED = re.compile(r"\b94[4-8]_?\d{3}_?\d{3}\b|\b1_?171_?000\b")


def test_no_e3_test_names_a_registered_block_or_the_evaluation_seed():
    here = Path(__file__).resolve().parent
    offenders = []
    for f in sorted(here.glob("test_e3_*.py")):
        if f.name == Path(__file__).name:
            continue
        for k, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if REGISTERED.search(line):
                offenders.append(f"{f.name}:{k}: {line.strip()}")
    assert not offenders, offenders
