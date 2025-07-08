from .adidasRunnersEventModel import AdidasRunnersEvent
from typing import List, Self
class AdidasCommunity:

    events : List[AdidasRunnersEvent]
    id: str
    name: str

    def __init__(self: Self, id:str, name:str):
        self.id = id
        self.name = "Adidas Runners " + name
    
    def setEvents(self: Self, events: List[AdidasRunnersEvent]):
        self.events = events

        