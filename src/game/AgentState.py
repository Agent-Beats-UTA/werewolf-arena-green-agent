from typing import List, TYPE_CHECKING, Any

from pydantic import BaseModel
from src.models.Suspect import Suspect

if TYPE_CHECKING:
    from src.game.GameData import GameData

class AgentState(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    suspects: List[Suspect] = []
    game_data: Any = None  # GameData at runtime
        
    def get_werewolf_kill_prompt(self):
        pass
    
    def get_seer_reveal_prompt(self):
        pass
    
    def get_bidding_prompt(self):
        pass
    
    def get_debate_prompt(self):
        pass
    
    def get_voting_prompt(self):
        pass
    
    def get_suspect_prompt(self):
        pass
    