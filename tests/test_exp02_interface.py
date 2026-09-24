"""Interface variants: remapping one signal's neurons, negating it, and hashing the result."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.connectome import load_connectome
from wormwars.connectome.loader import ConnectomeError
from wormwars.interface import (
    interface_from_spec,
    interface_hash,
    load_interface,
    load_interface_spec,
    negated_spec,
    remapped_spec,
)


@pytest.fixture(scope="module")
def con():
    return load_connectome()


def test_from_spec_matches_load_interface(con):
    a = load_interface(con)
    b = interface_from_spec(con, load_interface_spec())
    assert interface_hash(a) == interface_hash(b)


def test_remap_moves_only_the_food_neurons(con):
    spec = load_interface_spec()
    new = remapped_spec(spec, "food", [("ASIL", "ASIR"), ("ASJL", "ASJR"), ("ASGL", "ASGR")])
    a, b = load_interface(con), interface_from_spec(con, new)
    names = con.names
    fl = [names[i] for s, i in zip(b.signal_names, b.sensor_neuron) if s == "food_left"]
    fr = [names[i] for s, i in zip(b.signal_names, b.sensor_neuron) if s == "food_right"]
    assert fl == ["ASIL", "ASJL", "ASGL"] and fr == ["ASIR", "ASJR", "ASGR"]
    keep = [k for k, s in enumerate(a.signal_names) if not s.startswith("food_")]
    assert np.array_equal(a.sensor_neuron[keep], b.sensor_neuron[keep])
    assert np.array_equal(a.sensor_gain, b.sensor_gain)
    for part in ("forward_plus", "forward_minus", "turn_plus", "turn_minus", "pump_neurons"):
        assert np.array_equal(getattr(a, part), getattr(b, part))
    assert interface_hash(a) != interface_hash(b)
    assert spec["sensors"][0]["neurons"] == ["AWAL"], "the input spec must not be mutated"


def test_remap_refuses_neurons_already_in_use(con):
    spec = load_interface_spec()
    for pairs in ([("ASKL", "ASKR"), ("ASIL", "ASIR"), ("ASJL", "ASJR")],   # pheromone sensor
                  [("AVAL", "AVAR"), ("ASIL", "ASIR"), ("ASJL", "ASJR")]):  # motor read-out
        with pytest.raises(ValueError, match="already"):
            remapped_spec(spec, "food", pairs)


def test_remap_refuses_the_wrong_number_of_pairs():
    with pytest.raises(ValueError, match="pairs"):
        remapped_spec(load_interface_spec(), "food", [("ASIL", "ASIR")])


def test_remap_to_a_missing_neuron_fails_loudly(con):
    new = remapped_spec(load_interface_spec(), "food",
                        [("NOPEL", "NOPER"), ("ASIL", "ASIR"), ("ASJL", "ASJR")])
    with pytest.raises(ConnectomeError, match="NOPE"):
        interface_from_spec(con, new)


def test_negation_flips_only_that_signal(con):
    a = load_interface(con)
    b = interface_from_spec(con, negated_spec(load_interface_spec(), "food"))
    food = np.array([s.startswith("food_") for s in a.signal_names])
    assert np.array_equal(b.sensor_gain[food], -a.sensor_gain[food])
    assert np.array_equal(b.sensor_gain[~food], a.sensor_gain[~food])
