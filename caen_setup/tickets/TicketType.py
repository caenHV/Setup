"""
Module for defining ticket types in the ticket management system.

This module defines the `TicketType` enumeration, which associates ticket types 
with their corresponding ticket classes. It provides a method to retrieve the 
names of all defined ticket types.

Classes
-------
TicketType
    An enumeration of ticket types, each associated with a specific ticket class.

Usage
-----
You can use the `TicketType` enumeration to reference different ticket types 
and retrieve their names.

Example
-------
>>> ticket_names = TicketType.names()
>>> print(ticket_names)
{"SetVoltage", "Down", "GetParams"}
"""

from enum import Enum

from caen_setup.tickets import Tickets


class TicketType(Enum):
    """Enumeration of ticket types associated with their corresponding ticket classes.

    Attributes
    ----------
    SetVoltage : Type[Tickets.SetVoltage_Ticket]
        The ticket class for setting voltage.
    Down : Type[Tickets.Down_Ticket]
        The ticket class for bringing the system down.
    GetParams : Type[Tickets.GetParams_Ticket]
        The ticket class for retrieving parameters.

    Methods
    -------
    names() -> set[str]
        Returns a set of names for all defined ticket types.
    """

    SetVoltage = Tickets.SetVoltage_Ticket
    Down = Tickets.Down_Ticket
    GetParams = Tickets.GetParams_Ticket

    @classmethod
    def names(cls) -> set[str]:
        """Returns a set of names for all defined ticket types.

        Returns
        -------
        set[str]
            A set containing the names of all ticket types defined in the enumeration.
        """
        return {tk_type.value.type_description().name for tk_type in cls}
