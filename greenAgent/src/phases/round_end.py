from typing import TYPE_CHECKING

from src.models.abstract.Phase import Phase
from src.models.Event import Event
from src.models.enum.EventType import EventType
from src.models.enum.Phase import Phase as PhaseEnum
from src.models.enum.Role import Role

if TYPE_CHECKING:
    from src.game.Game import Game
    from src.a2a.messenger import Messenger

class RoundEnd(Phase):
    def __init__(self, game: "Game", messenger: "Messenger"):
        super().__init__(game, messenger)
        
    async def run(self):
        self.check_win_conditions()
        self.log_event(EventType.ROUND_END)
        
    #Check if the game is over 
    def check_win_conditions(self):
        game_state = self.game.state
        current_round = game_state.current_round
        current_participants = game_state.participants.get(current_round, [])
        
        if not current_participants:
            return
        
        werewolf_alive = self.is_werewolf_alive(current_participants)
        villager_count = self.count_villagers(current_participants)
        
        #villagers win
        if not werewolf_alive:
            game_state.declare_winner("villagers")
            self.game.current_phase = PhaseEnum.GAME_END

        #werewolves win
        elif werewolf_alive and villager_count <= 1:
            game_state.declare_winner("werewolves")
            self.game.current_phase = PhaseEnum.GAME_END
        else:
            game_state.current_round += 1
            game_state.initialize_next_round()
            self.game.current_phase = PhaseEnum.NIGHT
    
    #Check if the werewolf is alive
    def is_werewolf_alive(self, participants):
        if not self.game.state.werewolf:
            return False
        werewolf_id = self.game.state.werewolf.id
        return any(p.id == werewolf_id for p in participants)
    
    #Check for number of villagers and seers
    def count_villagers(self, participants):
        return sum(1 for p in participants if p.role in [Role.VILLAGER, Role.SEER])
    
    #end of round logging
    def log_event(self, event_type: EventType):
        game_state = self.game.state
        current_round = game_state.current_round
        event = Event(type=event_type)
        self.game.log_event(current_round, event)
    