from enum import Enum, auto

class EventType(Enum):
    VILLAGE_ELIMINATION = auto()
    WEREWOLF_ELIMINATION = auto()
    SEER_INVESTIGATION = auto()
    VOTE = auto()
    DISCUSSION = auto()
    NIGHT_END = auto()
    ROUND_END = auto()
    GAME_END = auto()
    