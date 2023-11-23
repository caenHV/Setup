import json
from caen_setup.Tickets.TicketMaster import TicketMaster
from caen_setup.Tickets.TicketType import TicketType

data = json.dumps({
    'name' : 'Down', 
    'params' : {
        
    }
})
tk = TicketMaster.deserialize(data)
print(tk.type_description())
a = TicketType.SetVoltage
print(TicketType.names())