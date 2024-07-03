from abc import ABC, abstractmethod
import json
import time

from caen_setup.Setup.Handler import Handler
from caen_setup.Tickets.TicketInfo import Ticket_info, Ticket_Type_info

default_voltages = {
            "1" : 1880, 
            "2" : 1880,
            "3" : 2000,
            "4" : 2000,
            "5" : 2000,
            "6" : 2000,
            "7" : 2000,
            "8" : 2000,
            "9" : 2000,
            "10" : 2000,
            "11" : 2000,
            "12" : 2000,
            "13" : 2000,
            "14" : 2000,
            "15" : 2000,
            "16" : 1970,
            "17" : 1970,
            "18" : 1900,
            "19" : 1950,
            "20" : 1550,
            "21" : 1265,
            "-1" : 0.0
        }
max_default_voltage = max(default_voltages.values())   

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
        return Ticket_Type_info(name='Down', params={})

    @property
    def description(self) -> Ticket_info:
        return Ticket_info(name='Down', params={}) 
    
class SetVoltage_Ticket(Ticket):
    params_keys: set[str] = set({'target_voltage'})
    
    def __init__(self, params: dict):
        if not self.params_keys.issubset(params.keys()):
            raise KeyError(f"Passed params dict doesn't contain all required fields ({self.params_keys})")
        self.__target = float(params['target_voltage'])
    
    def execute(self, handler: Handler) -> str:
        try:                
            Ramp_Up_Down_speed: int = 10
            for layer, volt in default_voltages.items():
                rup_speed = round(Ramp_Up_Down_speed * volt / max_default_voltage) if layer != '-1' else Ramp_Up_Down_speed
                handler.set_voltage(int(layer), self.__target * volt, rup_speed)
                
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
            params={'target_voltage' : {
                'min_value' : 0, 
                'max_value' : 2500,
                'description' : 'Voltage to be set.'
            }
        })

    @property
    def description(self) -> Ticket_info:
        return Ticket_info(name='SetVoltage', params={'target_voltage' : self.__target})

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
        return Ticket_Type_info(name='GetParams', params={})
    
    @property
    def description(self) -> Ticket_info:
        return Ticket_info(name='GetParams', params={})

class StepByStepRUp_Ticket(Ticket):
    params_keys: set[str] = set({'target_voltage', 'steps'})
    
    def __init__(self, params: dict):
        if not self.params_keys.issubset(params.keys()):
            raise KeyError(f"Passed params dict doesn't contain all required fields ({self.params_keys})")
        self.__target = float(params['target_voltage'])
        self.__steps = int(params['steps'])
        self.__steps_size = self.__target / self.__steps
    
    def execute(self, handler: Handler) -> str:
        try:     
            for step_num in range(1, self.__steps):  
                for layer, volt in default_voltages.items():
                    handler.set_voltage(int(layer), self.__steps_size * step_num * volt)
                time.sleep(10)
                    
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
            name='StepByStepRUp', 
            params={'target_voltage' : {
                'min_value' : 0, 
                'max_value' : 2500,
                'description' : 'Voltage to be set.'
            },
            'steps' : {
                'min_value' : 1,
                'max_value' : 100,
                'description' : 'Number of steps to be made in the process of setting target voltage.'
            }
        })

    @property
    def description(self) -> Ticket_info:
        return Ticket_info(name='SetVoltage', params={'target_voltage' : self.__target})
