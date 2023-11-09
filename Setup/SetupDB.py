from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class Board(Base):
    __tablename__ = "boards"    
    address: Mapped[str] = mapped_column(primary_key=True)
    conet: Mapped[int]
    link: Mapped[int]
    handler: Mapped[Optional[int]]

    channels: Mapped[list["Channel"]] = relationship(back_populates="board", cascade="all, delete-orphan", single_parent=True, passive_deletes=True)
    
class Channel(Base):
    __tablename__ = "channels"
    channel: Mapped[int] = mapped_column(primary_key=True)
    
    layer: Mapped[Optional[int]]
    last_update: Mapped[Optional[datetime]]
    
    Pw: Mapped[Optional[float]]
    
    VSet: Mapped[Optional[float]]
    VMon: Mapped[Optional[float]]
    ISet: Mapped[Optional[float]]
    IMon: Mapped[Optional[float]]
    
    RUp: Mapped[Optional[float]]
    RDWn: Mapped[Optional[float]]
    Temp: Mapped[Optional[float]]
    
    
    board_address: Mapped[str] = mapped_column(ForeignKey("boards.address", ondelete='CASCADE'), primary_key=True)
    board: Mapped["Board"] = relationship(back_populates="channels")

class SetupDB_manager:
    def __init__(self, drivername: str ="postgresql+psycopg2", username: str ="postgres", password: str ="qwerty", database: str="caen_handler"):
        self.__engine = create_engine(f"{drivername}://{username}:{password}@localhost/{database}")
        connection = self.__engine.connect()
        Base.metadata.create_all(self.__engine)

    def get_session(self):
        Session = sessionmaker(bind=self.__engine)
        return Session()