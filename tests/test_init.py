import json
from pathlib import Path

import pytest
from caen_setup import Handler
from caen_setup.Tickets.Tickets import Down_Ticket, SetVoltage_Ticket, GetParams_Ticket


@pytest.fixture
def handler():
    """Defines a handler for tests"""
    return Handler(Path(__file__).parent / "test_config.json")


def test_down(handler):
    down_ticket = Down_Ticket({})
    result = down_ticket.execute(handler)
    assert result == json.dumps({"status": True, "body": {}})


def test_setvoltage(handler):
    set_volt = SetVoltage_Ticket({"target_voltage": 1})
    result = set_volt.execute(handler)
    assert result == json.dumps({"status": True, "body": {}})


def test_getparams(handler):
    selected_params = ["VMon", "IMonH"]
    get_pars = GetParams_Ticket({"select_params": selected_params})
    result = json.loads(get_pars.execute(handler))
    assert result["status"] == True

    items = result["body"]["params"]
    assert len(items) == 24
    for specific_channel in items:
        assert set(specific_channel.keys()) == set(["channel", "params"])
        assert set(specific_channel["channel"].keys()) == set(
            ["alias", "channel_num", "layer", "board_info"]
        )
        assert set(specific_channel["params"].keys()) == set(selected_params)
