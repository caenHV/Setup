from typing import Dict, List
import pycaenhv
from pycaenhv.errors import CAENHVError
from pycaenhv.enums import CAENHV_SYSTEM_TYPE, LinkType
from pycaenhv.wrappers import (
    init_system,
    deinit_system,
    get_crate_map,
    get_channel_parameter,
    get_channel_parameters,
    set_channel_parameter,
    get_board_parameters,
)


class BoardCAEN:
    system_type = CAENHV_SYSTEM_TYPE.V65XX
    link_type = LinkType.OPTLINK
    slot = 0

    @staticmethod
    def initialize(address: str, conet: int, link: int) -> int:
        handler = init_system(
            BoardCAEN.system_type, BoardCAEN.link_type, f"{link}_{conet}_{address}"
        )
        return handler

    @staticmethod
    def deinitialize(handler: int) -> None:
        deinit_system(handler)
        return

    @staticmethod
    def nchannels(handler: int) -> int:
        return 6

    @staticmethod
    def channel_parameters(handler: int, channel: int = 0) -> List[str]:
        parameters = get_channel_parameters(handler, BoardCAEN.slot, channel)
        return parameters

    @staticmethod
    def get_parameters(
        handler: int, channels: List[int], parameters: List[str]
    ) -> Dict[int, Dict[str, float]]:
        res_dict = {}
        for ch in channels:
            res_dict[ch] = dict()
            for par_name in parameters:
                res_dict[ch][par_name] = get_channel_parameter(
                    handler, BoardCAEN.slot, ch, par_name
                )
        return res_dict

    @staticmethod
    def set_parameters(
        handler: int, channels: List[int], parameters: Dict[str, float]
    ) -> None:
        for ch in channels:
            for par_name, par_val in parameters.items():
                set_channel_parameter(handler, BoardCAEN.slot, ch, par_name, par_val)
        return
