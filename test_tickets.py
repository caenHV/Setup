import json
from caen_setup.Tickets.TicketMaster import TicketMaster

data = json.dumps({
    'name' : 'Down', 
    'params' : {
        
    }
})
tk = TicketMaster.deserialize(data)
print(tk.description)