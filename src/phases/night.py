from typing import TYPE_CHECKING

from src.models.abstract.Phase import Phase
from src.models.Event import Event
from src.models.enum.EventType import EventType
from src.models.enum.EliminationType import EliminationType

if TYPE_CHECKING:
    from src.game.Game import Game
    from src.a2a.messenger import Messenger

class Night(Phase):
    def __init__(self, game: "Game", messenger: "Messenger"):
        super().__init__(game, messenger)

    async def run(self):
        await self.game.log(f"[Night] Round {self.game.state.current_round}")
        await self.execute_werewolf_kill()
        await self.execute_seer_investigation()

        self.game.log_event(self.game.state.current_round, Event(type=EventType.NIGHT_END))

    async def execute_werewolf_kill(self):
        game_state = self.game.state

        # Check if werewolf is still alive
        if game_state.werewolf is None:
            await self.game.log("[Night] Werewolf is dead, skipping kill")
            return

        await self.game.log(f"[Night] Werewolf {game_state.werewolf.id[:8]} choosing victim...")
        response = await game_state.werewolf.talk_to_agent(
            prompt=game_state.werewolf.get_werewolf_prompt(),
        )

        player = response["player_id"]
        rationale = response["reason"]
        await self.game.log(f"[Night] Werewolf eliminated {player[:8]}: {rationale[:50]}...")

        self.game.state.eliminate_player(player, EliminationType.NIGHT_KILL)
        werewolf_elimination_event = Event(
            type=EventType.WEREWOLF_ELIMINATION,
            eliminated_player=player,
            description=rationale
        )
        self.game.log_event(game_state.current_round, werewolf_elimination_event)
        game_state.latest_werewolf_kill = player

    async def execute_seer_investigation(self):
        game_state = self.game.state
        seer = game_state.seer

        # Check if seer is still alive
        if seer is None:
            await self.game.log("[Night] Seer is dead, skipping investigation")
            return

        await self.game.log(f"[Night] Seer {seer.id[:8]} choosing target...")
        response = await seer.talk_to_agent(
            prompt=seer.get_seer_prompt(),
        )

        player = response["player_id"]
        rationale = response["reason"]

        seer_investigation_event = Event(
            type=EventType.SEER_INVESTIGATION,
            player=seer.id,
            description=rationale
        )

        self.game.log_event(game_state.current_round, seer_investigation_event)

        # Reveal investigation result to seer
        is_werewolf = game_state.werewolf.id == player if game_state.werewolf else False
        await self.game.log(f"[Night] Seer investigated {player[:8]}: {'WEREWOLF' if is_werewolf else 'not werewolf'}")
        await seer.talk_to_agent(
            prompt=seer.get_seer_reveal_prompt(player_id=player, is_werewolf=is_werewolf),
        )

        # Store the seer check for future reference
        game_state.seer_checks.append((player, is_werewolf))