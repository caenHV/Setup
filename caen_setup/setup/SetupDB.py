"""
This module defines the database models for the module using SQLAlchemy.

It includes the following classes:
- `Base`: The base class for all SQLAlchemy declarative models.
- `Board`: Represents CAEN board in the database, 
    including its attributes and relationships to channels.
- `Channel`: Represents a channel associated with CAEN board, 
    including various parameters and attributes.
- `SetupDB_manager`: Manages the setup and connection to the database, 
    providing methods to create the database engine and manage sessions.

Usage
-----
To use the module, create an instance of the `SetupDB_manager` class with the desired database path.
You can then use the `get_session` method to obtain a session for performing database operations.

Example
-------
```python
db_manager = SetupDB_manager("sqlite:///example.db")
session = db_manager.get_session()

# Create a new board
new_board = Board(address="40000000", conet=0, link=0)
session.add(new_board)
session.commit()

# Query boards
boards = session.query(Board).all()
```
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import (
    sessionmaker,
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy declarative models.

    This class serves as the base for all ORM models in the application,
    inheriting from SQLAlchemy's DeclarativeBase.
    """


class Board(Base):
    """
    Represents a board in the database.

    Attributes
    ----------
    address : str
        The unique address of the board (primary key).
    conet : int
        The conet number associated with the board.
    link : int
        The link number associated with the board.
    handler : Optional[int]
        An optional handler for the board
        (it can be retrieved during board initialization).
    channels : list[Channel]
        A list of channels associated with the board,
        with a relationship to the Channel class.
    """

    __tablename__ = "boards"
    address: Mapped[str] = mapped_column(primary_key=True)
    conet: Mapped[int]
    link: Mapped[int]
    handler: Mapped[Optional[int]]

    channels: Mapped[list["Channel"]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
        single_parent=True,
        passive_deletes=True,
        lazy="selectin",
    )


class Channel(Base):
    """
    Represents a channel associated with a board in the database.

    Attributes
    ----------

    channel : int
        The unique channel number (primary key).
    alias : Optional[str]
        An optional name alias for the channel.
    layer : Optional[int]
        An optional layer number for the channel.
    last_update : Optional[datetime]
        The timestamp of the last update for the channel.
    ... : Optional[...]
        Channel parameters of the board
        (descriptions can be found in the official CAEN V65XX docs).
    board_address : str
        The address of the associated board (foreign key).
    board : Board
        The board associated with the channel,
        with a relationship to the Board class.
    """

    __tablename__ = "channels"
    channel: Mapped[int] = mapped_column(primary_key=True)

    alias: Mapped[Optional[str]]
    layer: Mapped[Optional[int]]
    last_update: Mapped[Optional[datetime]]

    Pw: Mapped[Optional[float]]

    VSet: Mapped[Optional[float]]
    VMon: Mapped[Optional[float]]
    ISet: Mapped[Optional[float]]
    IMon: Mapped[Optional[float]]
    ImonRange: Mapped[Optional[float]]
    IMonH: Mapped[Optional[float]]
    IMonL: Mapped[Optional[float]]
    ChStatus: Mapped[Optional[float]]
    Trip: Mapped[Optional[float]]
    SVMax: Mapped[Optional[float]]

    RUp: Mapped[Optional[float]]
    RDWn: Mapped[Optional[float]]
    PDwn: Mapped[Optional[float]]
    Temp: Mapped[Optional[float]]
    Polarity: Mapped[Optional[float]]

    board_address: Mapped[str] = mapped_column(
        ForeignKey("boards.address", ondelete="CASCADE"), primary_key=True
    )
    board: Mapped["Board"] = relationship(back_populates="channels")


class SetupDB_manager:
    """
    Manages the setup and connection to the database.

    This class is responsible for creating the database engine,
    establishing connections, and managing sessions for database operations.

    Attributes
    ----------
    __engine : Engine
        The SQLAlchemy engine used to connect to the database.

    Parameters
    ----------
    dbpath : str
        The database connection string (e.g., "sqlite:///example.db").
    """

    def __init__(self, dbpath: str):
        """
        Initializes the SetupDB_manager with the specified database path.

        This method creates the database engine and establishes a connection.
        It also creates the necessary tables in the database based on the
        defined SQLAlchemy models.

        Parameters
        ----------
        dbpath : str
            The database connection string (e.g., "sqlite:///example.db").
        """
        self.__engine = create_engine(dbpath)
        self.__engine.connect()
        Base.metadata.create_all(self.__engine)

    def get_session(self):
        """
        Creates and returns a new database session.

        This method uses the sessionmaker to create a session bound to the
        database engine, allowing for database operations.

        Returns
        -------
        A new SQLAlchemy session for interacting with the database.
        """
        Session = sessionmaker(bind=self.__engine)
        return Session()
