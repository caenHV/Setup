# caen-setup

CAEN HV Board Package

This package provides a comprehensive interface for interacting with CAEN V65XX hardware systems, including mock implementations for testing and development purposes. It includes classes for managing hardware boards, handling ticket management, and configuring channel parameters.

## Installation

To install the package, use the following command:

```bash
pip install caen-setup --index-url https://git.inp.nsk.su/api/v4/projects/1206/packages/pypi/simple
```

## Modules

### [`fake_board.py`](caen_setup/setup/fake_board.py)

This module provides a mock implementation of a hardware CAEN board interface for testing and development purposes.

To use this module, create an instance of the `FakeBoard` class and call its methods to initialize the fake board, retrieve or set parameters, and manage channels.

#### Example
```python
from caen_setup.setup.fake_board import FakeBoard

handler = FakeBoard.initialize("40000000", 0, 0)
parameters = FakeBoard.channel_parameters(handler)
print(parameters) 
# ["VSet", "ISet", "Temperature", "IMonH", "IMonL"]

values = FakeBoard.get_parameters(handler, [0, 1], ["VSet", "IMonH"])
print(values) 
# {0: {'VSet': 0, 'IMonH': 0.09}, 1: {'VSet': 0, 'IMonH': 0.04}}

FakeBoard.set_parameters(handler, [0], [("VSet", 5.0)])
values = FakeBoard.get_parameters(handler, [0, 1], ["VSet"])
print(values)
# {0: {'VSet': 5.0}, 1: {'VSet': 0}}

FakeBoard.deinitialize(handler)
```

---

### [`caen_board.py`](caen_setup/setup/caen_board.py)

This module provides an interface for interacting with **real** board of CAEN V65XX system.

#### Prerequesties
You need to have installed all necessary CAEN drivers and libs to run this 
(in our case: [A3818Drv-1.6.8](https://www.caen.it/download/?filter=A3818), [CAENVMELib-v3.4.0](https://www.caen.it/products/caencomm-library/), [CAENComm-v1.6.0](https://www.caen.it/products/caencomm-library/), [CAENHVWrapper-6.3](https://www.caen.it/products/caen-hv-wrapper-library/))

#### Usage
To use this module, create an instance of the `BoardCAEN` class and call its methods to initialize the board, retrieve or set parameters, and manage channels.

#### Example
```python
from caen_setup.setup.caen_board import BoardCAEN

handler = BoardCAEN.initialize("40000000", 0, 0)
parameters = BoardCAEN.channel_parameters(handler, 0)

BoardCAEN.set_parameters(handler, [0], [("param_name", 1.0)])
BoardCAEN.deinitialize(handler)
```

---

### [`handler.py`](caen_setup/setup/handler.py)

This module contains the `Handler` class, which is responsible for managing the state and operations of the overall CAEN V65XX system (a lot of boards).

To use the `Handler` class, create an instance by providing the necessary configuration path and optional parameters. The instance can then be used to interact with the CAEN board.

An example of the handler config is provided in [tests/test_config.json](tests/test_config.json) file

#### Example
```python
from caen_setup import Handler

handler = Handler(config_path="./tests/test_config.json", fake_board=True)
handler.set_voltage(layer=1, voltage_multiplier=0.5)
channel_parameters = handler.get_params(layer=1)
print(channel_parameters)
# [{'channel': {'alias': '1', 'channel_num': 0, 'layer': 1, 'board_info': {'40000000': {'conet': 0, 'link': 0}}}, 'params': {'VSet': 940.0, 'ISet': 0.0, 'VMon': 946.0, 'IMonH': 0.011, 'Pw': 0.0, 'ChStatus': 0.0, 'Trip': 0.0, 'SVMax': 0.0, 'RDWn': 0.0, 'RUp': 0.0, 'PDwn': 0.0, 'Polarity': 0.0, 'Temp': 0.0, 'ImonRange': 0.0, 'IMonL': 0.091, 'VDef': 1880}}]
```

---

### [`Tickets.py`](caen_setup/tickets/Tickets.py)

Module for ticket management in a handler system.

Interaction with CAEN system via tickets execution is a preferable way 
because it provides higher level of abstraction than direct handler object usage.

#### Classes

- **Ticket**: An abstract base class for all ticket types, defining the required interface.
- **Down_Ticket**: Represents a ticket for bringing the system down (sets voltage to 0 and powers down).
- **SetVoltage_Ticket**: Represents a ticket for setting a target voltage.
- **GetParams_Ticket**: Represents a ticket for retrieving parameters.

#### Usage
You can create instances of the concrete ticket classes and execute them using a handler.

#### Example
```python
from caen_setup import Handler
from caen_setup.tickets.Tickets import Down_Ticket, SetVoltage_Ticket, GetParams_Ticket

handler = Handler(config_path="./tests/test_config.json", fake_board=True)

down_ticket = Down_Ticket(params={})
response = down_ticket.execute(handler)
print(response)
# '{"status": true, "body": {}}'

set_voltage_ticket = SetVoltage_Ticket(params={"target_voltage": 1.0})
response = set_voltage_ticket.execute(handler)
print(response)
# '{"status": true, "body": {}}'

get_params_ticket = GetParams_Ticket(params={"select_params": ["VSet", "VDef"]})
response = get_params_ticket.execute(handler)
print(response)
# '{"status": True, "body": {"params": [{...}]}}'
```
---

## Development

### Run
1. Clone this repository and go to this folder
2. Build this python package in the [development mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) (inside your virtual env)
```bash
pip install -e .
```

### Launch tests
To run the tests for this package, follow these steps:
1. Install the `pytest` package via pip:
```bash
pip install pytest
```
2. Run the tests with the following command:
```bash
pytest -v
```