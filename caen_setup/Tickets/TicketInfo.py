from dataclasses import dataclass
import json
from typing import Any


@dataclass
class Ticket_Type_info:
    name: str
    args: dict[str, dict[str, Any]]
    """dictionary of (arg_name: str, arg_info: dict) that describes (somehow) Ticket."""
    
    @property
    def json(self)->str:
        return json.dumps(self.__dict__)
    
@dataclass
class Ticket_info:
    name: str
    args: dict[str, Any]
    """dictionary of (arg_name: str, arg_info: dict[par_name: str, par_val: Any]) that describes the ticket."""
    
    @property
    def json(self)->str:
        return json.dumps(self.__dict__)
