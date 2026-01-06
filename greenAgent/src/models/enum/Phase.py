from enum import Enum, auto

class Phase(Enum):
    NIGHT = auto()
    BIDDING = auto()
    VOTE = auto()
    DISCUSSION = auto()
    ROUND_END = auto()
    GAME_END = auto()