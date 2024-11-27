"""
Module for ticket management in a handler system.

This module defines an abstract base class `Ticket` and 
its concrete implementations for managing various ticket 
types in a handler system. Each ticket type encapsulates 
specific actions that can be executed by a handler, 
along with the necessary parameters and descriptions.
"""

from abc import ABC, abstractmethod
import json

from caen_setup import Handler
from caen_setup.tickets.TicketInfo import Ticket_info, Ticket_Type_info


class Ticket(ABC):
    """Abstract base class for all ticket types.

    This class defines the interface that all ticket types must implement, including
    methods for execution and description retrieval.
    """

    @abstractmethod
    def __init__(self, params: dict):
        """Initializes the ticket with the given parameters.

        Parameters
        ----------
        params : dict
            A dictionary of parameters required for the ticket.
        """

    @abstractmethod
    def execute(self, handler: Handler) -> str:
        """Executes the ticket action using the provided handler.

        Parameters
        ----------
        handler : Handler
            The handler to execute the ticket action.

        Returns
        -------
        str
            A JSON string representing the result of the execution.
        """

    @staticmethod
    @abstractmethod
    def type_description() -> Ticket_Type_info:
        """Returns the type description of the ticket.

        Returns
        -------
        Ticket_Type_info
            An object containing the name and parameters of the ticket type.
        """

    @property
    @abstractmethod
    def description(self) -> Ticket_info:
        """Returns the description of the ticket.

        Returns
        -------
        Ticket_info
            An object containing the name and parameters of the ticket.
        """


class Down_Ticket(Ticket):
    """Concrete implementation of Ticket for bringing the system down.

    This ticket executes a command to bring the system down.
    """

    params_keys: set[str] = set()

    def __init__(self, params: dict):
        """Initializes the Down_Ticket.

        Parameters
        ----------
        params : dict
            A dictionary of parameters (not used in this ticket).
        """

    def execute(self, handler: Handler) -> str:
        """Executes the action to bring the system down.

        Parameters
        ----------
        handler : Handler
            The handler to execute the ticket action.

        Returns
        -------
        str
            A JSON string representing the result of the execution.
        """
        try:
            handler.pw_down(None)
            return json.dumps({"status": True, "body": {}})
        except Exception as e:
            return json.dumps({"status": False, "body": {"error": str(e)}})

    @staticmethod
    def type_description() -> Ticket_Type_info:
        """Returns the type description of the Down_Ticket.

        Returns
        -------
        Ticket_Type_info
            An object containing the name and parameters of the Down_Ticket type.
        """
        return Ticket_Type_info(name="Down", params={})

    @property
    def description(self) -> Ticket_info:
        """Returns the description of the Down_Ticket.

        Returns
        -------
        Ticket_info
            An object containing the name and parameters of the Down_Ticket.
        """
        return Ticket_info(name="Down", params={})


class SetVoltage_Ticket(Ticket):
    """Concrete implementation of Ticket for setting a target voltage.

    This ticket executes a command to set a specified voltage.
    """

    params_keys: set[str] = set({"target_voltage"})

    def __init__(self, params: dict):
        """Initializes the SetVoltage_Ticket.

        Parameters
        ----------
        params : dict
            A dictionary of parameters required for the ticket, must include 'target_voltage'.

        Raises
        ------
        KeyError
            If the required parameters are not provided.
        """
        if not self.params_keys.issubset(params.keys()):
            raise KeyError(
                f"Passed params dict doesn't contain all required fields ({self.params_keys})"
            )
        self.__target = float(params["target_voltage"])

    def execute(self, handler: Handler) -> str:
        """Executes the action to set the target voltage.

        Parameters
        ----------
        handler : Handler
            The handler to execute the ticket action.

        Returns
        -------
        str
            A JSON string representing the result of the execution.
        """
        try:
            handler.set_voltage(None, self.__target)

            return json.dumps({"status": True, "body": {}})
        except Exception as e:
            return json.dumps({"status": False, "body": {"error": str(e)}})

    @staticmethod
    def type_description() -> Ticket_Type_info:
        """Returns the type description of the SetVoltage_Ticket.

        Returns
        -------
        Ticket_Type_info
            An object containing the name and parameters of the SetVoltage_Ticket type.
        """
        return Ticket_Type_info(
            name="SetVoltage",
            params={
                "target_voltage": {
                    "min_value": 0,
                    "max_value": 1.2,
                    "description": "Voltage multiplier to be set.",
                }
            },
        )

    @property
    def description(self) -> Ticket_info:
        """Returns the description of the SetVoltage_Ticket.

        Returns
        -------
        Ticket_info
            An object containing the name and parameters of the SetVoltage_Ticket.
        """
        return Ticket_info(name="SetVoltage", params={"target_voltage": self.__target})


class GetParams_Ticket(Ticket):
    """Concrete implementation of Ticket for retrieving parameters.

    This ticket executes a command to get specific parameters from the handler.
    """

    params_keys: set[str] = set({"select_params"})

    def __init__(self, params: dict):
        """Initializes the GetParams_Ticket.

        Parameters
        ----------
        params : dict
            A dictionary of parameters required for the ticket, must include 'select_params'.
        """
        self.sel_params = params.get("select_params", None)

    def execute(self, handler: Handler) -> str:
        """Executes the action to retrieve parameters.

        Parameters
        ----------
        handler : Handler
            The handler to execute the ticket action.

        Returns
        -------
        str
            A JSON string representing the result of the execution.
        """

        try:
            ch_params = handler.get_params(None, params=self.sel_params)
            return json.dumps({"status": True, "body": {"params": ch_params}})
        except Exception as e:
            return json.dumps({"status": False, "body": {"error": str(e)}})

    @staticmethod
    def type_description() -> Ticket_Type_info:
        """Returns the type description of the GetParams_Ticket.

        Returns
        -------
        Ticket_Type_info
            An object containing the name and parameters of the GetParams_Ticket type.
        """
        return Ticket_Type_info(name="GetParams", params={})

    @property
    def description(self) -> Ticket_info:
        """Returns the description of the GetParams_Ticket.

        Returns
        -------
        Ticket_info
            An object containing the name and parameters of the GetParams_Ticket.
        """
        return Ticket_info(name="GetParams", params={})
