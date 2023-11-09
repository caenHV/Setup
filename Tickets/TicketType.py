from enum import Enum

from Tickets import Tickets


class TicketType(Enum):
    SetVoltage = Tickets.SetVoltage_Ticket
    Down = Tickets.Down_Ticket
    
    @property
    @classmethod
    def names(cls) -> set[str]:
        return {tk_type.name for tk_type in cls}
