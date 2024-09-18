from datetime import datetime, timedelta
from typing import ClassVar
from dataclasses import dataclass
import json
import pathlib

from sqlalchemy import and_, delete, select, update
from sqlalchemy.exc import MultipleResultsFound, NoResultFound, IntegrityError

from caen_setup.Setup.SetupDB import Channel, Board, SetupDB_manager


@dataclass
class _Channel_LayerPair:
    """Defines a channel mappings"""
    channel: int
    alias: str
    layer: int | None = None


@dataclass
class Board_info:
    """Defines a board structure"""

    board_address: str
    conet: int
    link: int
    handler: int | None = None
    channels: list[_Channel_LayerPair] | None = None
    """list[Channel_LayerPair[channel_num, channel_layer, alias]]
    """

    def tuple(self) -> tuple[str, int, int, int | None]:
        return (self.board_address, self.conet, self.link, self.handler)

    def to_dict(self):
        res = {
            self.board_address : {
                "conet" : self.conet,
                "link" : self.link
            }
        }
        return res

    @classmethod
    def from_db_object(cls, board: Board) -> "Board_info":
        """Creates an instance of Board_info from current database"""

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
        """Opens a given config and provides some test of it
        
        Parameters
        ----------
        path : str
            path to the config file

        Returns
        -------
        dict
            parsed config        
        """

        filepath = pathlib.Path(path)

        if not filepath.exists():
            raise ValueError(f"Path {path} doesn't exist")
        if filepath.suffix != ".json" or not filepath.is_file():
            raise ValueError(f"Path {path} doesn't point to .json file")

        with open(filepath, 'r', encoding="utf-8") as f:
            raw_data: dict[str, dict[str, dict[str, int | dict[str, list[int]]]]] = json.load(f)

        Board_info.__validate_config(raw_data)
        return raw_data

    @staticmethod
    def __validate_config(parsed_json: dict):
        """Tests a given config"""

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
        }
        """
        try:
            if not isinstance(parsed_json, dict):
                raise ValueError("Wrong parsed config type (must be dict)")
            if 'board_info' not in parsed_json:
                raise ValueError("board_info field is not found")
            if "default_voltages" not in parsed_json:
                raise ValueError("default_voltages field is not found")
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
        """Creates an instance of Board_info from JSON config file"""

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
    """Defines a board channel structure"""

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
        ch_info = cls(
            board_info=Board_info.from_db_object(board),
            channel_num=channel.channel,
            layer=channel.layer,
            alias=channel.alias,
        )
        return ch_info

    @property
    def dict(self):
        res_dict = {
            "channel_num": self.channel_num,
            "layer": self.layer,
            "par_names": self.par_names,
            "alias": self.alias,
            "board_info": self.board_info.to_dict(),
        }
        return res_dict


class Handler:
    """A class for dealing with the current state of the CAEN board

    Parameters
    ----------
    path: str
        path to database
    refresh_time: int
        the time limit in seconds when database data is considered as fresh
    fake_board: bool
        use fake board interface (for development purposes)
    """

    def __init__(self, config_path: str, refresh_time: int = 10, fake_board: bool = True):
        self.refresh_time = timedelta(seconds=refresh_time) # seconds
        self.db_manager = SetupDB_manager("sqlite://") # use in-memory database (to speed up)
        boards = Board_info.from_json(config_path)

        if fake_board:
            from caen_setup.Setup.board import FakeBoard
            self.BoardCAEN = FakeBoard
        else:
            from caen_setup.Setup.boardcaen import BoardCAEN
            self.BoardCAEN = BoardCAEN

        with open(config_path, encoding="utf-8") as f:
            self.__default_voltages: dict[str, int] = json.load(f)['default_voltages']
        self.__max_default_voltage = max(self.__default_voltages.values())

        self.__remove_DB_records()
        self.__initialize_boards(config=boards)

        chs = self.__get_channels()
        if chs is not None:
            for ch in chs:
                channel_info = Channel_info.from_db_object(ch["Channel"], ch["Board"]) # type:ignore
                self.__set_parameters(
                    channel_info,
                    [
                        ("ImonRange", 0),
                        ("Trip", 0.2),
                        ("RUp", 10),
                        ("RDWn", 100),
                        ("PDwn", 1),
                    ],
                )

    def __del__(self) -> None:
        self.__deinitialize_boards()

    def __initialize_boards(self, config: list[Board_info]):
        """Inits available in DB boards and fills actual information"""
        boards = self.__get_boards()
        config_board_addresses = [b.board_address for b in config]
        for board in boards:
            board_address, conet, link, _ = board.tuple()
            if board_address not in config_board_addresses:
                self.__remove_board(board)
                continue
            board.handler = self.BoardCAEN.initialize(board_address, conet=conet, link=link)
            self.__reserve_board_channels(board)
            self.__fill_board_handler(board)

        for b in config:
            self.__add_board(b)
        self.__remove_none_boards()

    def __deinitialize_boards(self) -> None:
        """Deinits working boards"""
        boards = self.__get_boards()
        self.set_voltage(None, 0, 100)
        self.pw_down(None)
        for board in boards:
            if board.handler is not None:
                self.BoardCAEN.deinitialize(board.handler)
                board.handler = None
                self.__fill_board_handler(board)
                # self.__remove_DB_records()
        return

    def __add_board(self, info: Board_info) -> int:
        """Adds a board in the database and inits it"""
        if self.__get_board_handler(info) is not None:
            raise ValueError("This board already exists.")

        info.handler = self.BoardCAEN.initialize(
            info.board_address, conet=info.conet, link=info.link
        )
        self.__fill_board_handler(info)
        self.__reserve_board_channels(info)
        return info.handler

    def __reserve_board_channels(self, board_info: Board_info) -> bool:
        """Reserves rows for all channels in the board's config"""
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
        """Fills handler for the board"""
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
        """Returns a list of available boards

        Returns
        -------
        List[Board_info]
        """
        with self.db_manager.get_session() as session:
            boards = session.execute(select(Board)).all()
            bs = [Board_info.from_db_object(b._tuple()[-1]) for b in boards]
        return bs

    def __get_board_handler(self, board: Board_info) -> int | None:
        """Returns handler corresponding to the board
        Returns
        -------
        int | None
            handler
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
            except (MultipleResultsFound, NoResultFound) as e:
                return None
        return handler.tuple()[-1]

    def __get_channels(
        self, channel: Channel_info | None = None
    ) -> list[dict[str, Channel | Board]] | None:
        """Returns a list of available channels in the corresponding board.
        If board_info is None returns a list of all available channels.

        Returns
        -------
        list[dict[str, str | int | float]]
            a list of all available information about channels
            (board_address, channel, conet, link, handler, last_update, parameters)
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
            except (MultipleResultsFound, NoResultFound) as e:
                return None
            return [query_res._asdict()]

    def __get_channel(self, channel: Channel_info) -> dict[str, Channel | Board] | None:
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

    def set_voltage(self, layer: int | None = None, voltage_multiplier: float = 0., default_speed: int = 20)->None:
        if voltage_multiplier < 0 or voltage_multiplier > 1.5:
            raise ValueError("Voltage is either less than zero or bigger than 3000 V <=> voltage_multiplier > 1.5.")

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

            rup_speed = round(default_speed * def_volt / self.__max_default_voltage) if layer != '-1' else default_speed
            # print(str(channel_info.layer), def_volt, voltage_multiplier, rup_speed)
            self.__set_parameters(channel_info, [('VSet', voltage), ('RUp', rup_speed), ('RDown', rup_speed)])              

        self.pw_up(layer=layer)

    def pw_down(self, layer: int | None = None) -> None:
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
            self.__set_parameters(channel_info, [('VSet', 0), ('Pw', 0), ('RDown', 100)])

        list(map(self.__update_parameters, ch_info_list))

    def pw_up(self, layer: int | None = None) -> None:
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
            self.__set_parameters(channel_info, [('Pw', 1)])
        list(map(self.__update_parameters, ch_info_list))

    def get_params(
        self, layer: int | None = None, params: set[str] | None = None
    ) -> dict[str, dict | None]:
        requested_params: set[str] = set(Channel_info.par_names)
        if params is not None:
            requested_params: set[str] = params.intersection(Channel_info.par_names)

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
            return {name: val for name, val in results.items() if name in params}

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
