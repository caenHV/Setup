"""
This module contains the Handler class, which is responsible 
for managing the state and operations of the CAEN system 
(a lot of boards). The Handler class provides methods to initialize
and deinitialize boards, set voltages, power channels up or down, 
and retrieve channel parameters.

Usage
-----
To use the Handler class, create an instance by providing the necessary configuration
path and optional parameters. The instance can then be used to interact with the
CAEN board, including setting voltages, powering channels, and retrieving channel
information.
"""

from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import ClassVar
from dataclasses import dataclass
import json
import pathlib

from sqlalchemy import and_, delete, select, update
from sqlalchemy.exc import MultipleResultsFound, NoResultFound, IntegrityError

from caen_setup.setup.SetupDB import Channel, Board, SetupDB_manager


@dataclass
class _Channel_LayerPair:
    """Defines a channel mappings.

    Parameters
    ----------
    channel : int
        The channel number.
    alias : str
        The alias of the channel.
    layer : int, optional
        The layer number associated with the channel (default is None).
    """

    channel: int
    alias: str
    layer: int | None = None


@dataclass
class Board_info:
    """Defines a board structure.

    Attributes
    ----------
    board_address : str
        The address of the board.
    conet : int
        The conet number.
    link : int
        The link number.
    handler : int | None, optional
        The handler number (default is None).
    channels : list[_Channel_LayerPair] | None, optional
        A list of channel-layer pairs (default is None).
    """

    board_address: str
    conet: int
    link: int
    handler: int | None = None
    channels: list[_Channel_LayerPair] | None = None

    def tuple(self) -> tuple[str, int, int, int | None]:
        """Returns a tuple representation of the board information.

        Returns
        -------
        tuple[str, int, int, int | None]
            A tuple containing the board address, conet, link, and handler.
        """
        return (self.board_address, self.conet, self.link, self.handler)

    def to_dict(self):
        """Converts the board information to a dictionary.

        Returns
        -------
        dict
            A dictionary representation of the board information.
        """
        res = {self.board_address: {"conet": self.conet, "link": self.link}}
        return res

    @classmethod
    def from_db_object(cls, board: Board) -> "Board_info":
        """Creates an instance of Board_info from a database object.

        Parameters
        ----------
        board : Board
            The board object from which to create the Board_info instance.

        Returns
        -------
        Board_info
            An instance of Board_info populated with data from the board object.
        """

        b_info = cls(
            board_address=board.address,
            conet=board.conet,
            link=board.link,
            handler=board.handler,
            channels=[
                _Channel_LayerPair(channel=ch.channel, layer=ch.layer, alias=ch.alias)
                for ch in board.channels
            ],
        )
        return b_info

    @staticmethod
    def __open_config(path: str) -> dict:
        """Opens a given config and provides some test of it.

        Parameters
        ----------
        path : str
            Path to the config file.

        Returns
        -------
        dict
            Parsed config.

        Raises
        ------
        ValueError
            If the path does not exist or does not point to a .json file.
        """

        filepath = pathlib.Path(path)

        if not filepath.exists():
            raise ValueError(f"Path {path} doesn't exist")
        if filepath.suffix != ".json" or not filepath.is_file():
            raise ValueError(f"Path {path} doesn't point to .json file")

        with open(filepath, "r", encoding="utf-8") as f:
            raw_data: dict[str, dict[str, dict[str, int | dict[str, list[int]]]]] = (
                json.load(f)
            )

        Board_info.__validate_config(raw_data)
        return raw_data

    @staticmethod
    def __validate_config(parsed_json: dict):
        """Tests a given config for validity.

        Parameters
        ----------
        parsed_json : dict
            The parsed JSON configuration to validate.

        Raises
        ------
        ValueError
            If the configuration does not meet the required structure.
        """

        wrong_note = """
        Make sure that config file is formatted as json dict:
        "board_info" : {
                "some_board_address" : {
                    "conet" : conet_num,
                    "link" : link_num
                    "channels_by_layer" : {
                        "*layer_num*" : [*ch_nums*]
                    },
                    "aliases" : [...],
                }
            },
        "default_voltages" : {
            ...
        },
        "default_max_current" : {
            ...
        }
        """
        try:
            if not isinstance(parsed_json, dict):
                raise ValueError("Wrong parsed config type (must be dict)")
            if "board_info" not in parsed_json:
                raise ValueError("board_info field is not found")
            if "default_voltages" not in parsed_json:
                raise ValueError("default_voltages field is not found")
            if "default_max_current" not in parsed_json:
                raise ValueError("default_max_current field is not found")
            need_fields = set(["conet", "link", "channels_by_layer", "aliases"])
            if not all(
                need_fields == set(v.keys()) for v in parsed_json["board_info"].values()
            ):
                raise ValueError("Wrong set of fields for the specific board")

        except Exception as e:
            e.add_note(wrong_note)
            raise
        return

    @classmethod
    def from_json(cls, path: str):
        """Creates an instance of Board_info from a JSON config file.

        This method reads a JSON configuration file, validates its contents,
        and creates a list of Board_info instances based on the data found
        in the file.

        Parameters
        ----------
        path : str
            The path to the JSON config file.

        Returns
        -------
        list[Board_info]
            A list of Board_info instances created from the JSON data.

        Raises
        ------
        ValueError
            If the JSON file is not valid or does not contain the required fields.
        """

        raw_data = Board_info.__open_config(path)
        data = raw_data["board_info"]

        def get_channels(one_board_info: dict) -> list[_Channel_LayerPair]:
            channels = []
            for layer, chs in one_board_info["channels_by_layer"].items():
                channels.extend(
                    [
                        _Channel_LayerPair(
                            channel=ch,
                            layer=int(layer),
                            alias=one_board_info["aliases"][ch],
                        )
                        for ch in chs
                    ]
                )
            return channels

        res = []
        for b_address, info in data.items():
            res.append(
                cls(
                    board_address=b_address,
                    conet=info["conet"],
                    link=info["link"],
                    handler=None,
                    channels=get_channels(info),
                )
            )
        return res


@dataclass
class Channel_info:
    """Defines a board channel structure.

    Parameters
    ----------
    board_info : Board_info
        Information about the CAEN board associated with the channel.
    channel_num : int
        The channel number.
    layer : int, optional
        The layer number associated with the channel (default is None).
    alias : str, optional
        An alias of the channel (default is None).

    Attributes
    ----------
    par_names : tuple of str
        A tuple containing all parameters of the channel.
    """

    board_info: Board_info
    channel_num: int
    layer: int | None = None
    alias: str | None = None
    par_names: ClassVar[tuple[str, ...]] = (
        "VSet",
        "ISet",
        "VMon",
        "IMonH",
        "Pw",
        "ChStatus",
        "Trip",
        "SVMax",
        "RDWn",
        "RUp",
        "PDwn",
        "Polarity",
        "Temp",
        "ImonRange",
        "IMonL",
    )

    @classmethod
    def from_db_object(cls, channel: Channel, board: Board) -> "Channel_info":
        """Creates a Channel_info instance from a database object.

        Parameters
        ----------
        channel : Channel
            The channel database object.
        board : Board
            The board database object.

        Returns
        -------
        Channel_info
            An instance of Channel_info populated with data from the provided objects.
        """
        ch_info = cls(
            board_info=Board_info.from_db_object(board),
            channel_num=channel.channel,
            layer=channel.layer,
            alias=channel.alias,
        )
        return ch_info

    @property
    def dict(self) -> dict:
        """Returns a dictionary representation of the Channel_info instance.

        Returns
        -------
        dict
            A dictionary containing the channel number, layer,
            parameter names, alias, and board information.
        """
        res_dict = {
            "channel_num": self.channel_num,
            "layer": self.layer,
            "par_names": self.par_names,
            "alias": self.alias,
            "board_info": self.board_info.to_dict(),
        }
        return res_dict


class Handler:
    """A class for dealing with the current state 
    of the overall CAEN system (a lot of boards).

    Parameters
    ----------
    config_path : str
        Path to the configuration database.
    refresh_time : int, optional
        The time limit in seconds when database data is considered fresh (default is 10 seconds).
    fake_board : bool, optional
        Use fake board interface for development purposes (default is True).
    ramp_up : int, optional
        The ramp-up voltage speed in voltage/second (default is 10 V/s).
    ramp_down : int, optional
        The ramp-down voltage speed in voltage/second (default is 100 V/s).
    is_high_range : bool, optional
        Use IMonH field for reading current, if false IMonL. (default is True).
    """

    def __init__(
        self,
        config_path: str,
        refresh_time: int = 10,
        fake_board: bool = True,
        ramp_up: int = 10,
        ramp_down: int = 100,
        is_high_range: bool = True,
    ):
        self.refresh_time = timedelta(seconds=refresh_time)  # seconds
        self.db_manager = SetupDB_manager(
            "sqlite://"
        )  # use in-memory database (to speed up)
        boards = Board_info.from_json(config_path)
        self.__ramp_up = ramp_up
        self.__ramp_down = ramp_down
        self.__imon_range = 0 if is_high_range else 1
        if fake_board:
            from caen_setup.setup.fake_board import FakeBoard

            self.BoardCAEN = FakeBoard
        else:
            from caen_setup.setup.caen_board import BoardCAEN

            self.BoardCAEN = BoardCAEN

        with open(config_path, encoding="utf-8") as f:
            json_file = json.load(f)
            self.__default_voltages: dict[str, int] = json_file["default_voltages"]
            self.__default_max_current: dict[str, float] = json_file[
                "default_max_current"
            ]
        self.__max_default_voltage = max(self.__default_voltages.values())

        self.__remove_DB_records()
        self.__initialize_boards(config=boards)

        chs = self.__get_channels()
        if chs is not None:
            for ch in chs:
                channel_info = Channel_info.from_db_object(ch["Channel"], ch["Board"])
                max_current = self.__default_max_current.get(
                    str(channel_info.layer), 50.0
                )
                self.__set_parameters(
                    channel_info,
                    [
                        ("ImonRange", self.__imon_range),
                        ("ISet", max_current),
                        ("Trip", 0.2),
                        ("RUp", ramp_up),
                        ("RDWn", ramp_down),
                        ("PDwn", 1),
                    ],
                )

    def __del__(self) -> None:
        """Destructor for the Handler class."""
        self.__deinitialize_boards()

    def __initialize_boards(self, config: list[Board_info]):
        """Initializes available boards in the database
        and fills actual information.

        This method checks the boards present in the database
        against the provided configuration.
        It initializes the boards, reserves their channels,
        and fills the board handler with the necessary information.

        Parameters
        ----------
        config : list of Board_info
            A list of Board_info objects containing
            the configuration for the boards to be initialized.
        """
        boards = self.__get_boards()
        config_board_addresses = [b.board_address for b in config]
        for board in boards:
            board_address, conet, link, _ = board.tuple()
            if board_address not in config_board_addresses:
                self.__remove_board(board)
                continue
            board.handler = self.BoardCAEN.initialize(
                board_address, conet=conet, link=link
            )
            self.__reserve_board_channels(board)
            self.__fill_board_handler(board)

        for b in config:
            self.__add_board(b)
        self.__remove_none_boards()

    def __deinitialize_boards(self) -> None:
        """Deinitializes working boards.

        This method deinitializes all currently active boards
        by setting their voltage to 0,
        powering them down, and clearing their handlers.
        It ensures that boards are absolutely turned off
        when they are no longer in use.
        """
        boards = self.__get_boards()
        self.set_voltage(None, 0)
        self.pw_down(None)
        for board in boards:
            if board.handler is not None:
                self.BoardCAEN.deinitialize(board.handler)
                board.handler = None
                self.__fill_board_handler(board)
                # self.__remove_DB_records()
        return

    def __add_board(self, info: Board_info) -> int:
        """Adds a board to the database and initializes it.

        This method checks if the board already exists in the database.
        If it does not, it initializes the board and reserves its channels.
        The handler for the board is set up for further operations.

        Parameters
        ----------
        info : Board_info
            The Board_info object containing the information of the board to be added.

        Returns
        -------
        int
            The handler associated with the newly added board.

        Raises
        ------
        ValueError
            If the board already exists in the database.
        """
        if self.__get_board_handler(info) is not None:
            raise ValueError("This board already exists.")

        info.handler = self.BoardCAEN.initialize(
            info.board_address, conet=info.conet, link=info.link
        )
        self.__fill_board_handler(info)
        self.__reserve_board_channels(info)
        return info.handler

    def __reserve_board_channels(self, board_info: Board_info) -> bool:
        """Reserves rows for all channels in the board's configuration.

        This method drops all existing channel entries
        associated with the specified board address
        and reserves new rows for all channels defined
        in the board's configuration. It ensures that
        the database reflects the current state
        of the board's channels.

        Parameters
        ----------
        board_info : Board_info
            The Board_info object containing the configuration
            of the board, including its channels.

        Returns
        -------
        bool
            Returns True if the channels were successfully reserved.

        Raises
        ------
        ValueError
            If the board_info does not store information about channels.
        """
        with self.db_manager.get_session() as session:
            # Drop all channels.
            drop_stmt = delete(Channel).where(
                Channel.board_address == board_info.board_address
            )
            session.execute(drop_stmt)
            session.commit()

            if board_info.channels is None:
                raise ValueError(
                    "board_info does not store information about channels."
                )
            data = [
                Channel(
                    channel=ch.channel,
                    layer=ch.layer,
                    alias=ch.alias,
                    board_address=board_info.board_address,
                )
                for ch in board_info.channels
            ]

            try:
                for ch in data:
                    session.merge(ch)
                session.commit()
            except IntegrityError:
                session.rollback()
        return True

    def __fill_board_handler(self, board: Board_info) -> None:
        """Fills the handler for the specified board.

        This method updates the database with the current
        handler information for the given board.
        It first attempts to merge the board's information
        into the database and then updates the
        handler details if necessary.

        Parameters
        ----------
        board : Board_info
            The Board_info object containing the information
            of the board to be updated, including
            its address, conet, link, and handler.

        Raises
        ------
        IntegrityError
            If there is a violation of database integrity constraints
            during the merge or update operations.
        """
        with self.db_manager.get_session() as session:
            try:
                session.merge(
                    Board(
                        address=board.board_address,
                        conet=board.conet,
                        link=board.link,
                        handler=board.handler,
                    )
                )
                session.commit()
            except IntegrityError:
                session.rollback()

        with self.db_manager.get_session() as session:
            stmt = (
                update(Board)
                .where(Board.address == board.board_address)
                .values(
                    address=board.board_address,
                    conet=board.conet,
                    link=board.link,
                    handler=board.handler,
                )
            )
            session.execute(stmt)
            session.commit()

    def __get_boards(self) -> list[Board_info]:
        """Returns a list of available boards.

        This method retrieves all boards from the database
        and converts them into a list of Board_info objects.

        Returns
        -------
        list of Board_info
            A list containing Board_info objects representing
            the available boards in the database.
        """
        with self.db_manager.get_session() as session:
            boards = session.execute(select(Board)).all()
            bs = [Board_info.from_db_object(b._tuple()[-1]) for b in boards]
        return bs

    def __get_board_handler(self, board: Board_info) -> int | None:
        """Returns the handler corresponding to the specified board.

        This method queries the database for the handler
        associated with the given board's address,
        conet, and link. If no handler is found or
        if multiple results are found, it returns None.

        Parameters
        ----------
        board : Board_info
            The Board_info object containing the information
            of the board for which the handler is requested.

        Returns
        -------
        int | None
            The handler associated with the board if found; otherwise, None.
        """
        stmt = select(Board.handler).where(
            and_(
                Board.address == board.board_address,
                Board.conet == board.conet,
                Board.link == board.link,
            )
        )
        with self.db_manager.get_session() as session:
            try:
                handler = session.execute(stmt).one()
            except (MultipleResultsFound, NoResultFound):
                return None
        return handler.tuple()[-1]

    def __get_channels(
        self, channel: Channel_info | None = None
    ) -> list[dict[str, Channel | Board]] | None:
        """Returns a list of available channels in the corresponding board.

        If a specific channel is provided, it returns information about that channel.
        If no channel is specified, it returns a list of all available channels.

        Parameters
        ----------
        channel : Channel_info, optional
            The Channel_info object for which to retrieve channel information.
            If None, retrieves all available channels.

        Returns
        -------
        list[dict[str, Channel | Board]] | None
            A list of dictionaries containing information about the channels, including
            board_address, channel, conet, link, handler, last_update, and parameters.
            Returns None if the specified channel is not found or if there are multiple results
            for the specified channel.
        """
        stmt = select(Channel, Board).join(Board)

        if channel is not None:
            board_address = channel.board_info.board_address
            conet = channel.board_info.conet
            link = channel.board_info.link
            ch_num = channel.channel_num
            stmt = stmt.where(
                and_(
                    Board.address == board_address,
                    Board.conet == conet,
                    Board.link == link,
                    Channel.channel == ch_num,
                )
            )

        with self.db_manager.get_session() as session:
            query_res = session.execute(stmt)
            # BUG: Or not. If I move this shit out of with context it will stop working because "sqlalchemy cannot be converted to 'persistent' state, as this identity map is no longer valid."
            if channel is None:
                return [res._asdict() for res in query_res.all()]

            try:
                query_res = query_res.one()
            except (MultipleResultsFound, NoResultFound):
                return None
            return [query_res._asdict()]

    def __get_channel(self, channel: Channel_info) -> dict[str, Channel | Board] | None:
        """Retrieves information for a specific channel.

        This method calls the __get_channels method to fetch channel information.
        If the channel is found, it returns the corresponding data; otherwise, it returns None.

        Parameters
        ----------
        channel : Channel_info
            The Channel_info object for which to retrieve channel information.

        Returns
        -------
        dict[str, Channel | Board] | None
            A dictionary containing information about the specified channel, including
            details from both the Channel and Board. Returns None if the channel is not found
            or if multiple results are returned.
        """
        data = self.__get_channels(channel)
        if data is None or len(data) != 1:
            return None
        return data[-1]

    def __get_channels_by_layer(
        self, layer: int | None
    ) -> list[dict[str, Channel | Board]] | None:
        """Returns all available information about channels for the specific layer from the database"""
        if layer is None:
            return None
        stmt = select(Channel, Board).join(Board).where(Channel.layer == layer)
        with self.db_manager.get_session() as session:
            query_res = session.execute(stmt).all()
        query_res = [res._asdict() for res in query_res]
        return query_res

    def __remove_board(self, board: Board_info) -> None:
        """Removes a board from the database and turns off it"""
        board.handler = None
        self.__fill_board_handler(board)
        self.__remove_none_boards()
        return

    def __remove_DB_records(self) -> None:
        with self.db_manager.get_session() as session:
            stmt = delete(Board)
            session.execute(stmt)
            stmt = delete(Channel)
            session.execute(stmt)
            session.commit()

    def __remove_none_boards(self) -> None:
        with self.db_manager.get_session() as session:
            stmt = delete(Board).where(Board.handler.is_(None))
            session.execute(stmt)
            session.commit()

    def __get_parameters(
        self, channel: Channel_info
    ) -> dict[str, str | float | int | datetime | None] | None:
        data = self.__get_channel(channel)
        if data is None:
            return None
        ch: Channel = data["Channel"]  # type: ignore
        board: Board = data["Board"]  # type: ignore
        if data is None:
            return None

        if ch.last_update is None or datetime.now() - ch.last_update > self.refresh_time:  # type: ignore
            self.__update_parameters(channel)

            data = self.__get_channel(channel)
            if data is None:
                return None
            ch: Channel = data["Channel"]  # type: ignore

        return {par: ch.__getattribute__(par) for par in Channel_info.par_names}

    def __update_parameters(self, channel: Channel_info) -> None:
        """Updates parameters from `params` dictionary in the database"""
        data = self.__get_channel(channel)
        if data is None:
            return None
        try:
            params = self.BoardCAEN.get_parameters(data["Board"].handler, [channel.channel_num], Channel_info.par_names)  # type: ignore
        except:
            return
        update_data: dict[str, float | datetime | str] = params[channel.channel_num]  # type: ignore
        update_data["last_update"] = datetime.now()
        stmt = (
            update(Channel)
            .where(
                and_(
                    Channel.channel == channel.channel_num,
                    Channel.board_address == channel.board_info.board_address,
                )
            )
            .values(**update_data)
        )
        with self.db_manager.get_session() as session:
            session.execute(stmt)
            session.commit()

    def __set_parameters(
        self, channel: Channel_info, params_dict: list[tuple[str, float]]
    ) -> bool:
        """Sets parameters from `params_dict` to CAEN and updates database information"""
        data = self.__get_channel(channel)
        if data is None:
            return False
        try:
            self.BoardCAEN.set_parameters(data["Board"].handler, [channel.channel_num], params_dict)  # type: ignore
        except:
            return False
        return True

    def set_voltage(
        self, layer: int | None = None, voltage_multiplier: float = 0.0
    ) -> None:
        """Sets the voltage for the specified layer or for all layers if no layer is specified.

        Parameters
        ----------
        layer : int, optional
            The layer for which to set the voltage. If None, sets the voltage for all layers.
        voltage_multiplier : float, optional
            A multiplier to adjust the default voltage. Must be between 0 and 1.2 (default is 0.0).

        Raises
        ------
        ValueError
            If the voltage_multiplier is less than 0 or greater than 1.2.
        """
        if voltage_multiplier < 0 or voltage_multiplier > 1.2:
            raise ValueError(
                "Voltage is either less than zero or bigger than 2400 V <=> voltage_multiplier > 1.2."
            )

        if layer is None:
            channels = self.__get_channels()
        else:
            channels = self.__get_channels_by_layer(layer)

        if channels is None:
            return
        ch_info_list = list()
        for ch in channels:
            channel_info = Channel_info.from_db_object(ch["Channel"], ch["Board"])  # type: ignore
            ch_info_list.append(channel_info)
            def_volt = self.__default_voltages.get(str(channel_info.layer), 0.0)
            voltage = def_volt * voltage_multiplier

            layer_speed_mod = (
                def_volt / self.__max_default_voltage
                if str(channel_info.layer) != "-1"
                else 1
            )
            ramp_up = round(self.__ramp_up * layer_speed_mod)
            ramp_down = round(self.__ramp_down * layer_speed_mod)
            self.__set_parameters(
                channel_info,
                [("VSet", voltage), ("RUp", ramp_up), ("RDown", ramp_down)],
            )

        self.pw_up(layer=layer)

    def pw_down(self, layer: int | None = None) -> None:
        """Powers down the specified layer or all layer channels if no layer is specified.

        This method sets the voltage to zero and powers down the channels for the given layer.

        Parameters
        ----------
        layer : int, optional
            The layer to be powered down. If None, powers down all channels.
        """
        if layer is None:
            channels = self.__get_channels()
        else:
            channels = self.__get_channels_by_layer(layer)

        if channels is None:
            return

        ch_info_list = list()
        for ch in channels:
            channel_info = Channel_info.from_db_object(ch["Channel"], ch["Board"])  # type: ignore
            ch_info_list.append(channel_info)
            self.__set_parameters(
                channel_info, [("VSet", 0), ("Pw", 0), ("RDown", 100)]
            )

        list(map(self.__update_parameters, ch_info_list))

    def pw_up(self, layer: int | None = None) -> None:
        """Powers up the specified layer or all layer channels if no layer is specified.

        This method sets the power state to 'on' for the channels in the specified layer.

        Parameters
        ----------
        layer : int, optional
            The layer to be powered up. If None, powers up all layers.
        """
        if layer is None:
            channels = self.__get_channels()
        else:
            channels = self.__get_channels_by_layer(layer)

        if channels is None:
            return
        ch_info_list = list()
        for ch in channels:
            channel_info = Channel_info.from_db_object(ch["Channel"], ch["Board"])  # type: ignore
            ch_info_list.append(channel_info)
            self.__set_parameters(channel_info, [("Pw", 1)])
        list(map(self.__update_parameters, ch_info_list))

    def get_params(
        self, layer: int | None = None, params: Iterable | None = None
    ) -> list[dict[str, dict | None]]:
        """Retrieves parameters for channels in the specified layer
        or all layer channels if no layer is specified.

        Parameters
        ----------
        layer : int, optional
            The layer for which to retrieve parameters.
            If None, retrieves parameters for all layers.
        params : Iterable, optional
            A collection of parameter names to retrieve.
            If None, retrieves all available parameters.

        Returns
        -------
        list[dict[str, dict | None]]
            A list of dictionaries, each containing channel
            information and the requested parameters.
            Each dictionary has a "channel" key with channel
            details and a "params" key with the requested parameters.
            Returns None if no parameters are found for a channel.
        """
        requested_params: set[str] = set(Channel_info.par_names) | set(["VDef"])
        if params is not None:
            requested_params: set[str] = set(params).intersection(requested_params)

        query = select(Channel, Board).join(Board)
        if layer is not None:
            query = query.where(Channel.layer == layer)

        with self.db_manager.get_session() as session:
            channels = [row._asdict() for row in session.execute(query).all()]
        channels = [
            Channel_info.from_db_object(channel=ch["Channel"], board=ch["Board"])
            for ch in channels
        ]

        def select_requested(params: set[str], ch: Channel_info) -> dict | None:
            results = self.__get_parameters(ch)

            if results is None:
                return None
            result_dict = {name: val for name, val in results.items() if name in params}

            if "VDef" in params:
                default_voltage = self.__default_voltages.get(str(ch.layer), 0.0)
                result_dict.update({"VDef": default_voltage})

            return result_dict

        res = [
            {
                "channel": {
                    key: ch.dict[key]
                    for key in ["alias", "channel_num", "layer", "board_info"]
                },
                "params": select_requested(requested_params, ch),
            }
            for ch in channels
        ]
        return res
