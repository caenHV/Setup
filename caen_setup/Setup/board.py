import random
from typing import Dict, List, Tuple


class FakeBoard:
    board_state = {"VMon": {}}

    @staticmethod
    def initialize(address: str, conet: int, link: int) -> int:
        handler = int(f"{address}{conet}{link}")
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
            if "VMon" in parameters:
                res_dict[ch]["VMon"] = FakeBoard.board_state.get("VMon", {}).get(handler, {}).get(ch, 0)
        return res_dict

    @staticmethod
    def set_parameters(
        handler: int, channels: List[int], parameters: List[Tuple[str, float]]
    ) -> None:
        for pname, pval in parameters:
            if pname == "VSet":
                for ch in channels:
                    if handler not in FakeBoard.board_state["VMon"]:
                        FakeBoard.board_state["VMon"][handler] = {}
                    FakeBoard.board_state["VMon"][handler].update({ch: pval})
        return
