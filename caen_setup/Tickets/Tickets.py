from abc import ABC, abstractmethod
import json

from caen_setup.Setup.Handler import Handler
from caen_setup.Tickets.TicketInfo import Ticket_info, Ticket_Type_info


class Ticket(ABC):
    @abstractmethod
    def __init__(self, params: dict):
        pass

    @abstractmethod
    def execute(self, handler: Handler) -> str:
        pass

    @staticmethod
    @abstractmethod
    def type_description() -> Ticket_Type_info:
        pass

    @property
    @abstractmethod
    def description(self) -> Ticket_info:
        pass


class Down_Ticket(Ticket):
    params_keys: set[str] = set()

    def __init__(self, params: dict):
        pass

    def execute(self, handler: Handler) -> str:
        try:
            handler.pw_down(None)
            return json.dumps({"status": True, "body": {}})
        except Exception as e:
            return json.dumps({"status": False, "body": {"error": str(e)}})

    @staticmethod
    def type_description() -> Ticket_Type_info:
        return Ticket_Type_info(name="Down", params={})

    @property
    def description(self) -> Ticket_info:
        return Ticket_info(name="Down", params={})


class SetVoltage_Ticket(Ticket):
    params_keys: set[str] = set({'target_voltage'})

    def __init__(self, params: dict):
        if not self.params_keys.issubset(params.keys()):
            raise KeyError(f"Passed params dict doesn't contain all required fields ({self.params_keys})")
        self.__target = float(params['target_voltage'])

    def execute(self, handler: Handler) -> str:
        try:                
            Ramp_Up_Down_speed: int = 10
            handler.set_voltage(None, self.__target, Ramp_Up_Down_speed)

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
                'max_value' : 1.2,
                'description' : 'Voltage multiplier to be set.'
            }
        })

    @property
    def description(self) -> Ticket_info:
        return Ticket_info(name='SetVoltage', params={'target_voltage' : self.__target})


class GetParams_Ticket(Ticket):
    params_keys: set[str] = set({"select_params"})

    def __init__(self, params: dict):
        self.sel_params = params.get("select_params", None)

    def execute(self, handler: Handler) -> str:

        try:
            ch_params = handler.get_params(None, params=self.sel_params)
            return json.dumps({"status": True, "body": {"params": ch_params}})
        except Exception as e:
            return json.dumps({"status": False, "body": {"error": str(e)}})

    @staticmethod
    def type_description() -> Ticket_Type_info:
        return Ticket_Type_info(name="GetParams", params={})

    @property
    def description(self) -> Ticket_info:
        return Ticket_info(name='GetParams', params={})
