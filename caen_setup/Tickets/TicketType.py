from enum import Enum

from caen_setup.Tickets import Tickets
from caen_setup.Tickets.TicketInfo import Ticket_Type_info


class TicketType(Enum):
    SetVoltage = Tickets.SetVoltage_Ticket
    Down = Tickets.Down_Ticket
    GetParams = Tickets.GetParams_Ticket
    StepByStepRUp = Tickets.StepByStepRUp_Ticket

    @classmethod
    def names(cls) -> set[str]:
        return {tk_type.value.type_description().name for tk_type in cls}
