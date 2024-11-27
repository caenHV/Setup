"""
This module provides an interface for interacting with the CAEN V65XX system.

It defines the `BoardCAEN` class, which includes methods for initializing and deinitializing
a board installed in CAEN V65XX system, retrieving and setting channel parameters.

The `BoardCAEN` class utilizes the `pycaenhv` library to communicate with the hardware,
allowing users to manage and configure the CAEN system effectively.
"""

from pycaenhv.enums import CAENHV_SYSTEM_TYPE, LinkType
from pycaenhv.wrappers import (
    init_system,
    deinit_system,
    get_channel_parameter,
    get_channel_parameters,
    set_channel_parameter,
)


class BoardCAEN:
    """
    A class to interface with the boards in the CAEN V65XX system.

    Attributes
    ----------
    system_type : CAENHV_SYSTEM_TYPE
        The type of the CAEN system being used.
    link_type : LinkType
        The type of link used to connect to the CAEN system.
    slot : int
        The slot number for the CAEN system.
    """

    system_type = CAENHV_SYSTEM_TYPE.V65XX
    link_type = LinkType.OPTLINK
    slot = 0

    @staticmethod
    def initialize(address: str, conet: int, link: int) -> int:
        """
        Initializes the CAEN board and returns a handler.

        Parameters
        ----------
        address : str
            The address of the CAEN board.
        conet : int
            The conet number for the connection.
        link : int
            The link number for the connection.

        Returns
        -------
        int
            A handler for the initialized CAEN board.
        """
        handler = init_system(
            BoardCAEN.system_type, BoardCAEN.link_type, f"{link}_{conet}_{address}"
        )
        return handler

    @staticmethod
    def deinitialize(handler: int) -> None:
        """
        Deinitializes the CAEN board using the provided handler.

        Parameters
        ----------
        handler : int
            The handler for the initialized CAEN board.
        """
        deinit_system(handler)
        return

    @staticmethod
    def nchannels(handler: int) -> int:
        """
        Returns the number of channels available in the CAEN board.

        Parameters
        ----------
        handler : int
            The handler for the initialized CAEN board.
        """
        return 6

    @staticmethod
    def channel_parameters(handler: int, channel: int = 0) -> list[str]:
        """
        Retrieves the parameters for a specific channel.

        Parameters
        ----------
        handler : int
            The handler for the initialized CAEN board.
        channel : int, optional
            The channel number (default is 0).

        Returns
        -------
        list[str]
            A list of parameters for the specified channel.
        """
        parameters = get_channel_parameters(handler, BoardCAEN.slot, channel)
        return parameters

    @staticmethod
    def get_parameters(
        handler: int, channels: list[int], parameters: list[str]
    ) -> dict[int, dict[str, float]]:
        """
        Gets the specified parameters for the given channels.

        Parameters
        ----------
        handler : int
            The handler for the initialized CAEN board.
        channels : list[int]
            A list of channel numbers to retrieve parameters for.
        parameters : list[str]
            A list of parameter names to retrieve.

        Returns
        -------
        dict[int, dict[str, float]]
            A dictionary where keys are channel numbers and values are dictionaries
            of parameter names and their corresponding values.
        """
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
        handler: int, channels: list[int], parameters: list[tuple[str, float]]
    ) -> None:
        """
        Sets the specified parameters for the given channels.

        Parameters
        ----------
        handler : int
            The handler for the initialized CAEN board.
        channels : list[int]
            A list of channel numbers to set parameters for.
        parameters : list[tuple[str, float]]
            A list of tuples where each tuple contains a parameter name and its value.
        """
        for ch in channels:
            for par_name, par_val in parameters:
                set_channel_parameter(handler, BoardCAEN.slot, ch, par_name, par_val)
        return
