import random
from typing import Dict, List

class FakeBoard:
    @staticmethod
    def initialize(address: str, conet: int, link: int) -> int:
        handler = random.randint(0, 100)
        return handler

    @staticmethod
    def deinitialize(handler: int) -> None:
        return

    @staticmethod
    def nchannels(handler: int) -> int:
        return 6

    @staticmethod
    def channel_parameters(handler: int) -> List[str]:
        return ["VSet", "ISet", "Temperature"]

    @staticmethod
    def get_parameters(
        handler: int, channels: List[int], parameters: List[str]
    ) -> Dict[int, Dict[str, float]]:
        res_dict = {}
        for ch in channels:
            res_dict[ch] = {p: 0 for p in parameters}
        return res_dict

    @staticmethod
    def set_parameters(
        handler: int, channels: List[int], parameters: Dict[str, float]
    ) -> None:
        return
