from datetime import datetime, timedelta
from typing import ClassVar
from dataclasses import dataclass
import json
import pathlib

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.exc import MultipleResultsFound, NoResultFound, IntegrityError

from Setup.board import FakeBoard as BoardCAEN
# from .boardcaen import BoardCAEN
from Setup.SetupDB import Channel, Board, SetupDB_manager

@dataclass
class Board_info:
    board_address: str
    conet: int
    link: int
    handler: int | None = None
    
    def tuple(self)->tuple[str, int, int, int | None]:
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
    def from_db_object(cls, board: Board)->"Board_info":
        b_info = cls(board_address = board.address, conet = board.conet, link = board.link, handler = board.handler)
        return b_info
        
    @classmethod
    def from_json(cls, path: str):
        filepath = pathlib.Path(path)
        if not filepath.exists():
            raise ValueError("Path %s doesn't exist.", path)

        if filepath.suffix != '.json' or not filepath.is_file():
            raise ValueError("Path %s doesn't point to .json file.", path)
        
        with open(filepath) as f:
            data: dict[str, dict[str, int]] = json.load(f)
            
        if type(data) is not dict:
            e = ValueError("Config file is wrong.")
            e.add_note("""Make sure that config file is formatted as json dict:
                        {
                            "some_board_address" : {
                                "conet" : conet_num,
                                "link" : link_num
                            }
                        }""")
            raise e
                
        res = [cls(board_address=b_address, conet=info['conet'], link=info['link'], handler=None) 
               for b_address, info in data.items() 
               if set(['conet', 'link']).issubset(info.keys())]
        return res
    
@dataclass
class Channel_info:
    board_info: Board_info
    channel_num: int
    layer: int | None = None
    par_names: ClassVar[tuple[str, ...]] = ("Pw", "VSet", "RUp", "RDWn", "ISet", "Temp", "VMon")
    
    @classmethod
    def from_db_object(cls, channel: Channel, board: Board)->"Channel_info":
        ch_info = cls(board_info = Board_info.from_db_object(board), channel_num = channel.channel, layer = channel.layer)
        return ch_info
    
class Handler:
    def __init__(self, config_path: str, refresh_time: int = 10, dev_mode: bool = False):
        """
        Parameters
        ----------
        path: str
            path to database
        refresh_time: int
            the time limit in seconds when database data is considered as fresh
        dev_mode: bool
            developing mode: using of sqlite in memory cache database (default False)
        """
        self.refresh_time = timedelta(seconds=refresh_time) # seconds
        self.db_manager = SetupDB_manager("sqlite://") if dev_mode else SetupDB_manager.from_args()
        boards = Board_info.from_json(config_path)
        self.__initialize_boards(config = boards)
        

    def __del__(self):
        self.__deinitialize_boards()

    
    def __initialize_boards(self, config: list[Board_info]):
        """Inits available in DB boards and fills actual information"""
        boards = self.__get_boards()
        config_board_addresses = [b.board_address for b in config]
        for board in boards:
            board_address, conet, link, _ = board.tuple()
            if board_address not in config_board_addresses:
                self.__remove_board(board)
                print(board_address)
                continue
            handler = BoardCAEN.initialize(board_address, conet=conet, link=link)
            nchannels = BoardCAEN.nchannels(handler)
            self.__reserve_board_channels(Board_info(board_address=board_address, conet=conet, link=link), nchannels)
            self.__fill_board_handler(Board_info(board_address, conet, link, handler))
        
        for b in config:
            try:
                self.__add_board(b)
                # print('add_board')
            except ValueError:
                continue
        self.__remove_none_boards()
            
    def __deinitialize_boards(self) -> None:
        """Deinits working boards"""
        boards = self.__get_boards()
        for board in boards:
            if board.handler is not None:
                BoardCAEN.deinitialize(board.handler)
                board.handler = None
                self.__fill_board_handler(board)
        return
    
    def __get_boards(self) -> list[Board_info]:
        """Returns a list of available boards

        Returns
        -------
        List[Tuple[str, int, int, Optional[int]]]
            a list of all available boards
            (board_address, conet, link, handler)
        """
        with self.db_manager.get_session() as session:
            boards = session.execute(select(Board.address, 
                                              Board.conet, 
                                              Board.link, 
                                              Board.handler)).all()
        return [Board_info(*ch.tuple()) for ch in boards]
    
    def __get_board_handler(self, board: Board_info) -> int | None:
        """Returns handler corresponding to the board
        Returns
        -------
        int | None
            handler
        """
        stmt = select(Board.handler).where(and_(
            Board.address == board.board_address,
            Board.conet == board.conet,
            Board.link == board.link
        ))
        with self.db_manager.get_session() as session:
            try:
                handler = session.execute(stmt).one()
            except (MultipleResultsFound, NoResultFound) as e:
                # TODO: Log me!
                return None
        return handler.tuple()[-1]
            
    def __add_board(self, info: Board_info)->int:
        """Adds a board in the database and inits it"""
        if self.__get_board_handler(info) is not None:
            raise ValueError("This board already exists.")

        info.handler = BoardCAEN.initialize(info.board_address, conet=info.conet, link=info.link)
        nchannels = BoardCAEN.nchannels(info.handler)
        self.__fill_board_handler(info)
        self.__reserve_board_channels(info, nchannels)
        return info.handler
    
    def __remove_board(self, board: Board_info)->None:
        """Removes a board from the database and turns off it"""
        board.handler = None
        self.__fill_board_handler(board)
        self.__remove_none_boards()
        return

    def __get_channels(self, channel: Channel_info | None = None)->list[dict[str, Channel | Board]] | None:
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
            stmt = stmt.where(and_(
                Board.address == board_address,
                Board.conet == conet,
                Board.link == link,
                Channel.channel == ch_num
            ))                
            
        with self.db_manager.get_session() as session:
            query_res = session.execute(stmt)
            # BUG: Or not. If I move this shit out of with context it will stop working because "sqlalchemy cannot be converted to 'persistent' state, as this identity map is no longer valid."
            if channel is None:
                return [res._asdict() for res in query_res.all()]
        
            try:
                query_res =query_res.one()
            except (MultipleResultsFound, NoResultFound) as e:
                # TODO: Log exception
                return None
            return [query_res._asdict()]
        
    def __get_channel(self, channel: Channel_info )->dict[str, Channel | Board] | None:
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
    
    def __reserve_board_channels(
        self, board_info: Board_info, nchannels: int
    ) -> bool:
        """Reserves rows for all available channels in the board"""
        with self.db_manager.get_session() as session:
            try:
                board = session.scalar(select(Board).where(Board.address == board_info.board_address))
                if board is not None:
                    # Drop all extra channels and orphans.
                    drop_stmt = delete(Channel).where(or_(
                        and_(Channel.board_address == board.address, Channel.channel >= nchannels),
                        Channel.board_address.is_(None)
                        ))
                    session.execute(drop_stmt)
                    session.commit()
            except MultipleResultsFound as e:
                # TODO: Log exception.
                pass              
             
            # Insert or Ignore channels. 
            data = [Channel(
                channel = chidx,
                board_address = board_info.board_address
                ) for chidx in range(nchannels)]
            
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
                session.merge(Board(address=board.board_address, conet=board.conet, link=board.link, handler=board.handler))
                session.commit()
            except IntegrityError:
                session.rollback()
                
        with self.db_manager.get_session() as session:
                stmt = (
                    update(Board)
                    .where(Board.address == board.board_address)
                    .values(address=board.board_address,
                            conet=board.conet,
                            link=board.link,
                            handler=board.handler)
                )
                session.execute(stmt)
                session.commit()
    

    def __remove_none_boards(self) -> None:
        with self.db_manager.get_session() as session:
            stmt = delete(Board).where(Board.handler.is_(None))
            session.execute(stmt)
            session.commit()

    def __get_parameters(self, channel: Channel_info) -> dict[str, str | float | int | datetime | None] | None:
        data = self.__get_channel(channel)
        if data is None:
            return None
        ch: Channel = data['Channel'] # type: ignore
        board: Board = data['Board'] # type: ignore
        if data is None:
            return None
        
        if (ch["last_update"] is None or datetime.now() - ch["last_update"] > self.refresh_time): # type: ignore
            params = BoardCAEN.get_parameters(board["handler"], [channel.channel_num], list(Channel_info.par_names)) # type: ignore
            self.__update_parameters(channel, params[channel.channel_num])
            
            data = self.__get_channel(channel)
            if data is None:
                return None
            ch: Channel = data['Channel'] # type: ignore
            
        return {par : ch.__getattribute__(par) for par in Channel_info.par_names}

    def __update_parameters(self, channel: Channel_info, params: dict[str, float]) -> None:
        """Updates parameters from `params` dictionary in the database"""
        update_data: dict[str, float | datetime | str] = params # type: ignore
        update_data["last_update"] = datetime.now()
        stmt = (
            update(Channel)
            .where(and_(
                Channel.channel == channel.channel_num,
                Channel.board.address == channel.board_info.board_address,
                Channel.board.conet == channel.board_info.conet,
                Channel.board.link == channel.board_info.link
                )
            )
            .values(**update_data)
        )
        with self.db_manager.get_session() as session:
            session.execute(stmt)
        
    def __set_parameters(self, channel: Channel_info, params_dict: dict[str, float]) -> bool:
        """Sets parameters from `params_dict` to CAEN and updates database information"""
        data = self.__get_channel(channel)
        if data is None:
            return False
        try:
            BoardCAEN.set_parameters(data["handler"], [channel.channel_num], params_dict) # type: ignore
            params = BoardCAEN.get_parameters(data["handler"], [channel.channel_num], Channel_info.par_names) # type: ignore
        except:
            # TODO: Log about troubles.
            return False
        
        self.__update_parameters(channel, params[channel.channel_num])
        return True
    
    def set_voltage(self, layer: int | None, voltage: float)->None:
        if voltage < 0 or voltage > 3e3:
            raise ValueError("Voltage is either less than zero or bigger than 3000 V.")
        
        if layer is None:
            channels = self.__get_channels()
        else:
            channels = self.__get_channels_by_layer(layer)
        
        if channels is None: 
            return 
        
        for ch in channels:
            channel_info = Channel_info.from_db_object(ch["Channel"], ch["Board"])  # type: ignore
            self.__set_parameters(channel_info, {'VSet' : voltage})
    
    def pw_down(self, layer: int | None)->None:
        if layer is None:
            channels = self.__get_channels()
        else:
            channels = self.__get_channels_by_layer(layer)
        
        if channels is None: 
            return 
        
        for ch in channels:
            channel_info = Channel_info.from_db_object(ch["Channel"], ch["Board"])  # type: ignore
            self.__set_parameters(channel_info, {'Pw' : 0})
    
    def get_params(self, layer: int | None, params: set[str] | None)->dict[Channel_info, dict | None]:
        requested_params: set[str] = set(Channel_info.par_names)
        if params is not None:
            requested_params: set[str] = params.intersection(Channel_info.par_names)
        
        query = select(Channel, Board).join(Board)
        if layer is not None:
            query = query.where(Channel.layer == layer)
                
        with self.db_manager.get_session() as session:
            channels = [row._asdict() for row in session.execute(query).all()]
        channels = [Channel_info.from_db_object(channel = ch['Channel'], board = ch['Board']) for ch in channels]
        
        def select_requested(params: set[str], ch: Channel_info)->dict | None:
            results = self.__get_parameters(ch)
            if results is None:
                return None
            return {name : val for name, val in results.items() if name in params}
            
        res: dict[Channel_info, dict | None] = {ch : select_requested(requested_params, ch) for ch in channels}
        return res        