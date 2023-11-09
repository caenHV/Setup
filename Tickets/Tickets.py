from abc import ABC, abstractmethod

import sys
sys.path.append('C:/work/Science/BINP/Caen/controller/Monitor/setup/')
from Handler import Handler
from Tickets.TicketInfo import Ticket_info

class Ticket(ABC):
    @abstractmethod
    def __init__(self, params: dict):
        pass
    
    @abstractmethod
    def execute(self, handler: Handler):
        pass
    
    @property
    @abstractmethod
    def description(self)->Ticket_info:
        pass
    

class Down_Ticket(Ticket):
    def __init__(self, params: dict):
        pass
    
    def execute(self, handler: Handler):
        handler.pw_down(None)
        
    @property
    def description(self)->Ticket_info:
        return Ticket_info(name='Down', args={})
    
    
class SetVoltage_Ticket(Ticket):
    def __init__(self, params: dict):
        if 'target_voltage' not in params.keys():
            raise KeyError("Passed params dict doesn't have 'target_voltage' field")
        self.target = float(params['target_voltage'])
    
    def execute(self, handler: Handler):
        handler.set_voltage(None, self.target)
        
    @property
    def description(self)->Ticket_info:
        return Ticket_info(name='SetVoltage', args={'target_voltage' : [0, 2500, 'Voltage to be set.']})
    