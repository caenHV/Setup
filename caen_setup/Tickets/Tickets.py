from abc import ABC, abstractmethod
import json

from caen_setup.Setup.Handler import Handler
from caen_setup.Tickets.TicketInfo import Ticket_info, Ticket_Type_info

class Ticket(ABC):
    @abstractmethod
    def __init__(self, params: dict):
        pass
    
    @abstractmethod
    def execute(self, handler: Handler)->str:
        pass
    
    @staticmethod
    @abstractmethod
    def type_description()->Ticket_Type_info:
        pass
    
    @property
    @abstractmethod
    def description(self)->Ticket_info:
        pass

class Down_Ticket(Ticket):
    params_keys: set[str] = set()
    def __init__(self, params: dict):
        pass
    
    def execute(self, handler: Handler) -> str:
        try:
            handler.pw_down(None)
            return json.dumps({
                "status": True,
                "body" : {}
            })
        except Exception as e:
            return json.dumps({
                "status": False,
                "body" : {
                    "error" : str(e) 
                }
            })
        
    @staticmethod
    def type_description()->Ticket_Type_info:
        return Ticket_Type_info(name='Down', args={})

    @property
    def description(self) -> Ticket_info:
        return Ticket_info(name='Down', args={}) 
    
class SetVoltage_Ticket(Ticket):
    params_keys: set[str] = set({'target_voltage'})
    
    def __init__(self, params: dict):
        if not self.params_keys.issubset(params.keys()):
            raise KeyError(f"Passed params dict doesn't contain all required fields ({self.params_keys})")
        self.__target = float(params['target_voltage'])
    
    def execute(self, handler: Handler) -> str:
        try:
            handler.set_voltage(None, self.__target)
            return json.dumps({
                "status": True,
                "body" : {}
            })
        except Exception as e:
            return json.dumps({
                "status": False,
                "body" : {
                    "error" : str(e) 
                }
            })
        
    @staticmethod
    def type_description()->Ticket_Type_info:
        return Ticket_Type_info(
            name='SetVoltage', 
            args={'target_voltage' : {
                'min_value' : 0, 
                'max_value' : 2500,
                'description' : 'Voltage to be set.'
            }
        })

    @property
    def description(self) -> Ticket_info:
        return Ticket_info(name='SetVoltage', args={'target_voltage' : self.__target})

class GetParams_Ticket(Ticket):
    params_keys: set[str] = set({})
    
    def __init__(self, params: dict):
        if not self.params_keys.issubset(params.keys()):
            raise KeyError(f"Passed params dict doesn't contain all required fields ({self.params_keys})")
        
    def execute(self, handler: Handler) -> str:
        
        try:
            ch_params = handler.get_params(None, None)
            
            res = {ch : {} if pars is None else pars  for ch, pars in ch_params.items()}
            return json.dumps({
                "status" : True,
                "body" : {
                    "params" : res
                }
            })
        except Exception as e:
            return json.dumps({
                "status" : False,
                "body" : {
                    "error" : str(e)
                }
            })
            
    @staticmethod
    def type_description()->Ticket_Type_info:
        return Ticket_Type_info(name='GetParams', args={})
    
    @property
    def description(self) -> Ticket_info:
        return Ticket_info(name='GetParams', args={})
        