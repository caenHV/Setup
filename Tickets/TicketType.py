from enum import Enum

from Tickets import Tickets
from Tickets.TicketInfo import Ticket_Type_info


class TicketType(Enum):
    SetVoltage = Tickets.SetVoltage_Ticket
    Down = Tickets.Down_Ticket
    GetParams = Tickets.GetParams_Ticket
    
    @property
    @classmethod
    def names(cls) -> set[str]:
        return {tk_type.name for tk_type in cls}
    