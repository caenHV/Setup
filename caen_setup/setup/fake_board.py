"""
This module provides a mock implementation (partial mock currently) 
of a hardware CAEN board interface.

The `FakeBoard` class simulates the behavior of a hardware board, allowing for
initialization, deinitialization, and management of channels and parameters.
It is designed for testing and development purposes, providing random values
for monitoring parameters to mimic real hardware behavior without requiring
actual hardware connections.
"""

import random


class FakeBoard:
    """
    A mock class to simulate the behavior of a hardware CAEN board.

    This class provides methods to initialize and deinitialize the board,
    retrieve the number of channels, and get or set parameters for each channel.
    It simulates the board's state using random values for monitoring parameters.

    Attributes
    ----------
    board_state : dict
        A dictionary to hold the state of the board, including set voltages.
    """

    board_state = {"VSet": {}}

    @staticmethod
    def initialize(address: str, conet: int, link: int) -> int:
        """
        Initializes the fake board and returns a handler.

        Parameters
        ----------
        address : str
            The address of the fake board.
        conet : int
            The conet number for the connection.
        link : int
            The link number for the connection.

        Returns
        -------
        int
            A handler for the initialized fake board.
        """
        handler = int(f"{address}{conet}{link}")
        return handler

    @staticmethod
    def deinitialize(handler: int) -> None:
        """
        Deinitializes the fake board using the provided handler.

        Parameters
        ----------
        handler : int
            The handler for the initialized fake board.
        """
        return

    @staticmethod
    def nchannels(handler: int) -> int:
        """
        Returns the number of channels available in the fake board.

        Parameters
        ----------
        handler : int
            The handler for the initialized fake board.
        """
        return 6

    @staticmethod
    def channel_parameters(handler: int) -> list[str]:
        """
        Retrieves the parameters available for the channels.

        Parameters
        ----------
        handler : int
            The handler for the initialized fake board.

        Returns
        -------
        list[str]
            A list of parameters available for the channels.
        """
        return ["VSet", "ISet", "Temperature", "IMonH", "IMonL"]

    @staticmethod
    def get_parameters(
        handler: int, channels: list[int], parameters: list[str]
    ) -> dict[int, dict[str, float]]:
        """
        Gets the specified parameters for the given channels, simulating random values.

        Parameters
        ----------
        handler : int
            The handler for the initialized fake board.
        channels : list[int]
            A list of channel numbers to retrieve parameters for.
        parameters : list[str]
            A list of parameter names to retrieve.

        Returns
        -------
        dict[int, dict[str, float]]
            A dictionary where keys are channel numbers and values are dictionaries
            of parameter names and their corresponding simulated values.
        """
        res_dict = {}
        for ch in channels:
            res_dict[ch] = {p: 0 for p in parameters}
            if "VMon" in parameters:
                res_dict[ch]["VMon"] = int(
                    FakeBoard.board_state.get("VSet", {}).get(handler, {}).get(ch, 0)
                    * random.gauss(1, 0.02)
                )
            if "IMonH" in parameters:
                res_dict[ch]["IMonH"] = random.expovariate(10)
            if "IMonL" in parameters:
                res_dict[ch]["IMonL"] = random.expovariate(10)
            if "VSet" in parameters:
                res_dict[ch]["VSet"] = (
                    FakeBoard.board_state.get("VSet", {}).get(handler, {}).get(ch, 0)
                )
        return res_dict

    @staticmethod
    def set_parameters(
        handler: int, channels: list[int], parameters: list[tuple[str, float]]
    ) -> None:
        """
        Sets the specified parameters for the given channels in the board state.

        Parameters
        ----------
        handler : int
            The handler for the initialized fake board.
        channels : list[int]
            A list of channel numbers to set parameters for.
        parameters : list[tuple[str, float]]
            A list of tuples where each tuple contains a parameter name and its value.
        """
        for pname, pval in parameters:
            if pname == "VSet":
                for ch in channels:
                    if handler not in FakeBoard.board_state["VSet"]:
                        FakeBoard.board_state["VSet"][handler] = {}
                    FakeBoard.board_state["VSet"][handler].update({ch: pval})
        return
