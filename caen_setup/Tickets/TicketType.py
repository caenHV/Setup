from enum import Enum

from caen_setup.Tickets import Tickets


class TicketType(Enum):
    SetVoltage = Tickets.SetVoltage_Ticket
    Down = Tickets.Down_Ticket
    GetParams = Tickets.GetParams_Ticket

    @classmethod
    def names(cls) -> set[str]:
        return {tk_type.value.type_description().name for tk_type in cls}
