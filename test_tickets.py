import json
from caen_setup.Tickets.TicketMaster import TicketMaster
from caen_setup.Tickets.TicketType import TicketType
from caen_setup.Tickets.Tickets import GetParams_Ticket

data = json.dumps({
    'name' : 'Down', 
    'params' : {
        
    }
})
# tk = TicketMaster.deserialize(data)
# print(tk.type_description())
# a = TicketType.SetVoltage
# print(TicketType.names())


# ticket_json = TicketMaster.serialize(GetParams_Ticket({}))
print(type(GetParams_Ticket({})))
