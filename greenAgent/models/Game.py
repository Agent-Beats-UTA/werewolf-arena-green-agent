from pydantic import BaseModel
from typing import List
from greenAgent.models.enum.Phase import Phase
from greenAgent.models.GameData import GameData

class Game(BaseModel):
    current_phase: Phase
    state: GameData

    def __init__(self, participants: List[str]):
        super().__init__(
            current_phase=Phase.NIGHT, 
            state=GameData(
                current_round=1,
                winner=None,
                turns_to_speak_per_round=1,  # Default
                participants={},
                speaking_order={},
                chat_history={},
                bids={},
                votes={},
                eliminations={}
            )
        )
        
        for p in participants:
            self.state.add_participant(p, "")
            
    def run_night_phase(self):
        # Implementation here
        pass

    def run_bidding_phase(self):
        # Implementation here
        pass

    def run_discussion_phase(self):
        # Implementation here
        pass

    def run_voting_phase(self):
        # Implementation here
        pass

    def run_round_end_phase(self):
        # Implementation here
        pass

    def run_game_end_phase(self):
        # Implementation here
        pass