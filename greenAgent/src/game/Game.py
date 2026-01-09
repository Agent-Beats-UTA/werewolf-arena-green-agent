from pydantic import BaseModel
from typing import List

from src.models.enum.EventType import EventType
from src.models.enum.Phase import Phase
from greenAgent.src.game.GameData import GameData
from src.models.Event import Event

from src.phases.night import Night
from src.phases.bidding import Bidding
from src.phases.voting import Voting
from src.phases.discussion import Discussion
from src.phases.round_end import RoundEnd
from src.phases.game_end import GameEnd

class Game(BaseModel):
    current_phase: Phase
    state: GameData
    night_controller: Night
    bidding_controller: Bidding
    discussion_controller: Discussion
    voting_controller: Voting

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
            ),
            night_controller = Night(),
            voting_controller = Voting(),
            bidding_controller = Bidding(),
            discussion_controller = Discussion()
        )
        
        for p in participants:
            self.state.add_participant(p, "")
       
    #Logs     
    def log_event(self, round:int, event:Event):
         self.state.events.setdefault(round, []).append(event)
         
    # Prompts
    def get_night_elimination_message(self, round_num:int):
        round_events = self.state.events[round_num]
        eliminated_player = [e.eliminated_player for e in round_events if e.type == EventType.WEREWOLF_ELIMINATION]
        
        return f"In the middle of the night, the werewolf eliminated player {eliminated_player}"
        
    def get_vote_elimination_message(self, round_num:int):
        round_events = self.state.events[round_num]
        eliminated_player = [e.eliminated_player for e in round_events if e.type == EventType.VILLAGE_ELIMINATION]
        
        return f"You all voted to eliminate player {eliminated_player}. They are not the werewolf."
        
        
    # Execute Phases
    def run_night_phase(self):
        self.night_controller.run()

    def run_bidding_phase(self):
        self.bidding_controller.run()

    def run_discussion_phase(self):
        self.discussion_controller.run()

    def run_voting_phase(self):
        self.voting_controller.run()

    def run_round_end_phase(self):
        pass
        
    def run_game_end_phase(self):
        pass