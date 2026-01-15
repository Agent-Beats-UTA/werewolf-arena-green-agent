from pydantic import BaseModel
from typing import List, Optional, Any

from src.models.enum.EventType import EventType
from src.models.enum.Phase import Phase
from src.game.GameData import GameData
from src.models.Event import Event
from src.a2a.messenger import Messenger

from a2a.types import TaskState
from a2a.utils import new_agent_text_message

from src.phases.night import Night
from src.phases.bidding import Bidding
from src.phases.voting import Voting
from src.phases.debate import Debate
from src.phases.round_end import RoundEnd
from src.phases.game_end import GameEnd

class Game(BaseModel):
    current_phase: Phase
    state: GameData
    messenger: Optional[Messenger] = None
    updater: Optional[Any] = None  # TaskUpdater at runtime
    night_controller: Optional[Night] = None
    bidding_controller: Optional[Bidding] = None
    debate_controller: Optional[Debate] = None
    voting_controller: Optional[Voting] = None
    round_end_controller: Optional[RoundEnd] = None
    game_end_controller: Optional[GameEnd] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, participants: List[str], messenger: Optional[Messenger] = None):
        super().__init__(
            current_phase=Phase.NIGHT,
            state=GameData(
                current_round=1,
                turns_to_speak_per_round=1
            ),
            messenger=messenger
        )

        # Initialize phase controllers with game and messenger references
        self.night_controller = Night(self, messenger)
        self.voting_controller = Voting(self, messenger)
        self.bidding_controller = Bidding(self, messenger)
        self.debate_controller = Debate(self, messenger)
        self.round_end_controller = RoundEnd(self, messenger)
        self.game_end_controller = GameEnd(self, messenger)

        for p in participants:
            self.state.add_participant(p, "")
       
    #Logs
    def log_event(self, round:int, event:Event):
         self.state.events.setdefault(round, []).append(event)

    async def log(self, message: str):
        """Log a message via the updater if available"""
        if self.updater:
            await self.updater.update_status(
                TaskState.working, new_agent_text_message(message)
            )
         
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
    async def run_night_phase(self):
        await self.log("Starting night phase...")
        await self.night_controller.run()

    async def run_bidding_phase(self):
        await self.log("Starting bidding phase...")
        await self.bidding_controller.run()

    async def run_debate_phase(self):
        await self.log("Starting debate phase...")
        await self.debate_controller.run()

    async def run_voting_phase(self):
        await self.log("Starting voting phase...")
        await self.voting_controller.run()

    async def run_round_end_phase(self):
        await self.log("Starting round end phase...")
        await self.round_end_controller.run()
        
    async def run_game_end_phase(self):
        if self.game_end_controller:
            return await self.game_end_controller.run()