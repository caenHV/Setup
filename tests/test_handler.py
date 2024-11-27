from math import isclose
from pathlib import Path
from random import random

import pytest
from caen_setup import Handler


@pytest.fixture
def handler():
    """Defines a handler for tests"""
    return Handler(Path(__file__).parent / "test_config.json")


def set_voltage(handler, layer, def_vlt_multiplier):
    handler.set_voltage(layer, def_vlt_multiplier)
    channels = handler.get_params(layer)
    for channel in channels:
        ch_layer = channel["channel"]["layer"]
        voltage_multiplier = (
            def_vlt_multiplier if (ch_layer == layer) or (layer is None) else 0
        )
        assert isclose(
            channel["params"]["VSet"],
            channel["params"]["VDef"] * voltage_multiplier,
        ), "Bad layer set voltage"

    return


def test_get_params(handler):
    req_params = ["VSet", "ISet", "VMon", "VDef"]
    all_params = handler.get_params(layer=None, params=req_params)
    for ch_pars in all_params:
        assert set(ch_pars.keys()) == set(["channel", "params"])
        channel_keys = set(ch_pars["channel"])
        param_keys = set(ch_pars["params"])
        assert channel_keys == set(["alias", "channel_num", "layer", "board_info"])
        assert param_keys == set(req_params)
    return


def test_set_voltage(handler):
    testdata = [
        (1, 0.7),
        (2, 1.1),
        (1, 1.0),
        (2, 0.4),
    ]
    for layer, def_vlt_multiplier in testdata:
        set_voltage(handler, layer, def_vlt_multiplier)

    for _ in range(5):
        set_voltage(handler, None, random())
    return
