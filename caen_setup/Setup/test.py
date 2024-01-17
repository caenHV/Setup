# from caen_setup.Setup.board import FakeBoard as BoardCAEN
from caen_setup.Setup.boardcaen import BoardCAEN
from caen_setup.Setup.SetupDB import Channel, Board, SetupDB_manager


handler = BoardCAEN.initialize("32100000", conet=0, link=0)

print(BoardCAEN.channel_parameters(handler))

BoardCAEN.deinitialize(handler)
