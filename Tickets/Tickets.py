from abc import ABC, abstractmethod

from Setup.Handler import Handler
from Tickets.TicketInfo import Ticket_info, Ticket_Type_info

class Ticket(ABC):
    @abstractmethod
    def __init__(self, params: dict):
        pass
    
    @abstractmethod
    def execute(self, handler: Handler):
        pass
    
    @property
    @abstractmethod
    def type_description(self)->Ticket_Type_info:
        pass
    
    @property
    @abstractmethod
    def description(self)->Ticket_info:
        pass

class Down_Ticket(Ticket):
    params_keys: set[str] = set()
    def __init__(self, params: dict):
        pass
    
    def execute(self, handler: Handler):
        handler.pw_down(None)
        
    @property
    def type_description(self)->Ticket_Type_info:
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
    
    def execute(self, handler: Handler):
        handler.set_voltage(None, self.__target)
        
    @property
    def type_description(self)->Ticket_Type_info:
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
    
    def execute(self, handler: Handler):
        res = handler.get_params(None, None)
        # TODO: Prepare the return value.
        
    @property
    def type_description(self)->Ticket_Type_info:
        return Ticket_Type_info(name='GetParams', args={})
    
    @property
    def description(self) -> Ticket_info:
        return Ticket_info(name='GetParams', args={})
    