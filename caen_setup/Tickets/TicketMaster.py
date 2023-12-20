import json
from typing import Any, Type
from caen_setup.Tickets.Tickets import Ticket
from caen_setup.Tickets.TicketType import TicketType
    
class TicketMaster:
    @staticmethod
    def serialize(ticket: Type[Ticket])->str:
        return ticket.description.json # type: ignore
    
    # Factory
    @classmethod
    def deserialize(cls, json_string: str)->Ticket:
        data: dict[str, Any] = json.loads(json_string)
        name: str = data['name']
        tk_type = TicketType[name].value
        tk: Ticket = tk_type(params = data['args'])
        return tk
            
    
    @staticmethod
    def inspect(json_string: str, ticket_type: TicketType)->bool:
        # TODO: Implement
        data: dict[str, Any] = json.loads(json_string)
        if 'name' not in data.keys():
            raise KeyError("Passed json_string doesn't have 'name' field")
        
        if 'params' not in data.keys():
            raise KeyError("Passed json_string doesn't have 'params' field")
        
        if type(data['params']) is not dict:
            raise KeyError("'params' field  in the passed json_string is not of type dict")
        
        if not ticket_type.value.params_keys.issubset(data['params'].keys()):
            return False
        
        
                   
        return True
    