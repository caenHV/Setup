
from dataclasses import dataclass
import json


@dataclass
class Ticket_info:
    name: str
    args: dict[str, list]
    """dictionary of (arg_name: str, arg_info: list) that describes (somehow) Ticket."""
    # TODO: Add __repr__.
    
    @property
    def json(self)->str:
        return json.dumps(self.__dict__)
