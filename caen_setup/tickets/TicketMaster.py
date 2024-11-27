"""
Module for managing ticket serialization and deserialization.

This module defines the `TicketMaster` class, which provides static methods for 
serializing and deserializing ticket objects, as well as inspecting JSON strings 
to ensure they conform to expected structures.

Classes
-------
TicketMaster
    A class that provides methods for ticket serialization, deserialization, and inspection.

Usage
-----
You can use the `TicketMaster` class to convert `Ticket` objects to JSON strings 
and back, as well as to validate the structure of JSON strings representing tickets.

Example
-------
```
>>> ticket = Ticket(name="Concert Ticket", params={"seat": "A1", "price": 100})
>>> json_string = TicketMaster.serialize(ticket)
>>> print(json_string)
{"name": "Concert Ticket", "params": {"seat": "A1", "price": 100}}

>>> deserialized_ticket = TicketMaster.deserialize(json_string)
>>> print(deserialized_ticket)
<__main__.Ticket object at 0x...>

>>> is_valid = TicketMaster.inspect(json_string, TicketType.CONCERT)
>>> print(is_valid)
True
```
"""

import json
from typing import Any, Type
from caen_setup.tickets.Tickets import Ticket
from caen_setup.tickets.TicketType import TicketType


class TicketMaster:
    @staticmethod
    def serialize(ticket: Type[Ticket]) -> str:
        """Serializes a Ticket object to a JSON string.

        Parameters
        ----------
        ticket : Type[Ticket]
            The Ticket object to serialize.

        Returns
        -------
        str
            A JSON string representation of the Ticket object.
        """
        return ticket.description.json  # type: ignore

    # Factory
    @classmethod
    def deserialize(cls, json_string: str) -> Ticket:
        """Deserializes a JSON string into a Ticket object.

        Parameters
        ----------
        json_string : str
            The JSON string to deserialize.

        Returns
        -------
        Ticket
            A Ticket object created from the JSON string.

        Raises
        ------
        KeyError
            If the JSON string does not contain the required fields.
        """
        data: dict[str, Any] = json.loads(json_string)
        name: str = data["name"]
        tk_type = TicketType[name].value
        tk: Ticket = tk_type(params=data["params"])
        return tk

    @staticmethod
    def inspect(json_string: str, ticket_type: TicketType) -> bool:
        """Inspects a JSON string to ensure it contains
        the required fields and matches the expected ticket type.

        Parameters
        ----------
        json_string : str
            The JSON string to inspect.
        ticket_type : TicketType
            The expected ticket type to validate against.

        Returns
        -------
        bool
            True if the JSON string is valid for
            the specified ticket type, False otherwise.

        Raises
        ------
        KeyError
            If the JSON string does not contain
            the required fields or if the 'params'
            field is not a dictionary.
        """
        data: dict[str, Any] = json.loads(json_string)
        if "name" not in data.keys():
            raise KeyError("Passed json_string doesn't have 'name' field")

        if "params" not in data.keys():
            raise KeyError("Passed json_string doesn't have 'params' field")

        if type(data["params"]) is not dict:
            raise KeyError(
                "'params' field  in the passed json_string is not of type dict"
            )

        if not ticket_type.value.params_keys.issubset(data["params"].keys()):
            return False

        return True
