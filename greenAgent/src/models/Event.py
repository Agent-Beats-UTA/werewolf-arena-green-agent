from pydantic import BaseModel
from src.models.enum.EventType import EventType

class Event(BaseModel):
    type:EventType
    eliminated_player: str = None
    player: str = None
    description:str = None