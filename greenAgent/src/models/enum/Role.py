from enum import Enum, auto
from pydantic import BaseModel

class Role(BaseModel):
    WEREWOLF = auto()
    VILLAGER = auto()
    SEER = auto()