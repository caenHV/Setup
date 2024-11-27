"""
Module for ticket information representation.

This module defines two data classes, `Ticket_Type_info` and `Ticket_info`, 
which are used to represent the structure and parameters of ticket types and 
individual tickets, respectively. Each class includes methods to convert 
instances to JSON format for easy serialization.

Classes
-------
Ticket_Type_info
    Represents the information of a ticket type, including its name and parameters.
Ticket_info
    Represents the information of a ticket, including its name and parameters.

Usage
-----
You can create instances of these classes to represent ticket types and tickets, 
and use the `json` property to obtain a JSON string representation of the instance.

Example
-------
```
>>> ticket_type = Ticket_Type_info(name="VIP", params={"arg1": {"info": "VIP access"}})
>>> print(ticket_type.json)
{"name": "VIP", "params": {"arg1": {"info": "VIP access"}}}

>>> ticket = Ticket_info(name="Concert Ticket", params={"seat": "A1", "price": 100})
>>> print(ticket.json)
{"name": "Concert Ticket", "params": {"seat": "A1", "price": 100}}
```
"""

from dataclasses import dataclass
import json
from typing import Any


@dataclass
class Ticket_Type_info:
    """Represents the information of a ticket type.

    Attributes
    ----------
    name : str
        The name of the ticket type.
    params : dict[str, dict[str, Any]]
        A dictionary where the keys are argument names and the values are dictionaries
        that describe the parameters of the ticket type.
    """

    name: str
    params: dict[str, dict[str, Any]]
    """dictionary of (arg_name: str, arg_info: dict) that describes (somehow) Ticket."""

    @property
    def json(self) -> str:
        """Converts the Ticket_Type_info instance to a JSON string.

        Returns
        -------
        str
            A JSON string representation of the Ticket_Type_info instance.
        """
        return json.dumps(self.__dict__)


@dataclass
class Ticket_info:
    """Represents the information of a ticket.

    Attributes
    ----------
    name : str
        The name of the ticket.
    params : dict[str, Any]
        A dictionary where the keys are argument names and the values are the corresponding
        parameter values for the ticket.
    """

    name: str
    params: dict[str, Any]
    """dictionary of (arg_name: str, arg_info: dict[par_name: str, par_val: Any]) that describes the ticket."""

    @property
    def json(self) -> str:
        """Converts the Ticket_info instance to a JSON string.

        Returns
        -------
        str
            A JSON string representation of the Ticket_info instance.
        """
        return json.dumps(self.__dict__)
