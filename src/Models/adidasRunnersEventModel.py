from typing import Self

class AdidasRunnersEvent:
    id : str
    name : str
    category: str
    startDate: str

    def __init__(self: Self, id:str, name:str, category:str, startDate:str):
        self.id = id
        self.name = name
        self.category = category
        self.startDate = startDate