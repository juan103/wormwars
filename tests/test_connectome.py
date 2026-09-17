"""Milestone 1 acceptance checks for the connectome loader and the interface."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.connectome import Connectome, ConnectomeError, load_connectome
from wormwars.interface import load_interface

# The 20 pharyngeal neurons of the hermaphrodite. The bite action is read from two of them, so
# their presence is a hard requirement on the dataset, not a nice-to-have.
PHARYNGEAL = [
    "I1L", "I1R", "I2L", "I2R", "I3", "I4", "I5", "I6",
    "M1", "M2L", "M2R", "M3L", "M3R", "M4", "M5",
    "MCL", "MCR", "MI", "NSML", "NSMR",
]


@pytest.fixture(scope="module")
def con() -> Connectome:
    return load_connectome()


def test_neuron_count(con):
    assert con.n == 302
    assert len(set(con.names)) == 302, "neuron names must be unique"


def test_pharyngeal_neurons_present(con):
    missing = [n for n in PHARYNGEAL if n not in con.index_of]
    assert not missing, f"pharyngeal neurons missing from the dataset: {missing}"
    assert sorted(con.of_class("pharyngeal")) == sorted(PHARYNGEAL)


def test_every_mapped_neuron_present_by_individual_name(con):
    iface = load_interface(con)
    # 39 distinct neurons are named in the interface; each must resolve individually.
    assert len(iface.mapped_neurons) == 39
    for name in (
        "AWAL AWAR AWCL AWCR ASEL ASER ASKL ASKR ADLL ADLR AFDL AFDR ASHL ASHR "
        "ALML ALMR AVM PLML PLMR AVBL AVBR PVCL PVCR AVAL AVAR AVDL AVDR AVEL AVER "
        "SMDDL SMDDR RMDDL RMDDR SMDVL SMDVR RMDVL RMDVR MCL MCR"
    ).split():
        assert name in con.index_of, f"{name} missing"


def test_interface_fails_loudly_on_a_missing_neuron(con, tmp_path):
    bad = tmp_path / "iface.yaml"
    bad.write_text(
        "sampling: {forward_offset: 0.6, lateral_offset: 0.5}\n"
        "sensors:\n  - {signal: food_left, neurons: [AWAL, NOTANEURON]}\n"
        "motors:\n"
        "  forward: {plus: [AVBL], minus: [AVAL]}\n"
        "  turn: {plus: [SMDDL], minus: [SMDVL]}\n"
        "  pump: {neurons: [MCL, MCR], squash: sigmoid, gain: 4.0}\n",
        encoding="utf-8",
    )
    with pytest.raises(ConnectomeError, match="NOTANEURON"):
        load_interface(con, bad)


def test_interface_rejects_unknown_signal(con, tmp_path):
    bad = tmp_path / "iface.yaml"
    bad.write_text(
        "sampling: {forward_offset: 0.6, lateral_offset: 0.5}\n"
        "sensors:\n  - {signal: smell_of_rain, neurons: [AWAL]}\n"
        "motors:\n"
        "  forward: {plus: [AVBL], minus: [AVAL]}\n"
        "  turn: {plus: [SMDDL], minus: [SMDVL]}\n"
        "  pump: {neurons: [MCL, MCR], squash: sigmoid, gain: 4.0}\n",
        encoding="utf-8",
    )
    with pytest.raises(ConnectomeError, match="smell_of_rain"):
        load_interface(con, bad)


def test_gap_matrix_symmetric_and_nonnegative(con):
    assert np.array_equal(con.gap, con.gap.T), "gap junction matrix must be exactly symmetric"
    assert (con.gap >= 0).all()
    assert np.all(np.diag(con.gap) == 0), "gap self-edges are meaningless and must be dropped"


def test_chemical_matrix_is_directed_and_nonnegative(con):
    assert not np.array_equal(con.chem, con.chem.T), "chemical connectivity is directed"
    assert (con.chem >= 0).all()


def test_weight_kind_is_documented(con):
    assert con.weight_kind == "em_sections"
    assert "EM serial sections" in con.meta["weight_meaning"]
    assert "NOT a synapse count" in con.meta["weight_meaning"]


def test_provenance_metadata_present(con):
    for key in ("source_url", "sha256", "citation", "transformations", "chem_sheet", "gap_sheet"):
        assert con.meta.get(key), f"missing provenance field {key}"
    assert con.meta["sha256"] == (
        "1f4fdbf84746b69b49a8da0816f52787860ce349b638dce37924ba80f90c70c9"
    )


def test_isolated_neurons_are_kept_not_dropped(con):
    # CANL/CANR make no chemical synapses. They stay in the 302 so that the node set is identical
    # across N2, SH and RD.
    for name in ("CANL", "CANR"):
        i = con.index(name)
        assert con.chem[i].sum() == 0
        assert con.gap[i].sum() > 0  # they do have gap junctions
    all_dead = [
        n for i, n in enumerate(con.names)
        if con.chem[i].sum() == con.chem[:, i].sum() == con.gap[i].sum() == 0
    ]
    assert all_dead == [], f"unexpected fully isolated neurons: {all_dead}"


def test_somatic_pharyngeal_bridge_is_the_rip_i1_gap_junction(con):
    # The only wiring between the somatic and pharyngeal nervous systems. Milestone 10 ablates it,
    # and the pump read-out depends on it, so it is checked here.
    for somatic, pharyngeal in (("RIPL", "I1L"), ("RIPR", "I1R")):
        assert con.gap[con.index(somatic), con.index(pharyngeal)] > 0


def test_index_raises_for_unknown_neuron(con):
    with pytest.raises(ConnectomeError, match="not in the N2 dataset"):
        con.index("AVAX")
