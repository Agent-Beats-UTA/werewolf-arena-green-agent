from typing import TYPE_CHECKING

from src.models.abstract.Phase import Phase
from src.models import Event, Vote
from src.models.enum.EventType import EventType
from src.models.enum.EliminationType import EliminationType

if TYPE_CHECKING:
    from src.game.Game import Game
    from src.a2a.messenger import Messenger

class Voting(Phase):
    def __init__(self, game: "Game", messenger: "Messenger"):
        super().__init__(game, messenger)

    async def run(self):
        await self.game.log("[Voting] Collecting votes...")
        await self.collect_round_votes()
        await self.tally_and_eliminate()

    async def collect_round_votes(self):
        game_state = self.game.state
        current_round = game_state.current_round

        current_participants = game_state.participants[current_round]

        #Send prompt for player vote
        for participant in current_participants:
            await self.game.log(f"[Voting] {participant.id[:8]} voting...")
            response = await participant.talk_to_agent(
                prompt=participant.get_vote_prompt(),
            )

            voted_for = response["player_id"]
            rationale = response["reason"]
            await self.game.log(f"[Voting] {participant.id[:8]} voted for {voted_for[:8]}")

            round_votes = game_state.votes[current_round]

            player_vote = Vote(
                voter_id=participant.id,
                voted_for_id=voted_for,
                rationale=rationale
            )

            round_votes.append(player_vote)

            # Log Event
            player_vote_event = Event(
                type=EventType.VOTE,
                player=participant.id,
                description=f"Voted for {voted_for} for rationale: {rationale}"
            )

            self.game.log_event(current_round, player_vote_event)
        
    async def tally_and_eliminate(self):
        game_state = self.game.state
        current_round = game_state.current_round
        round_votes = game_state.votes[current_round]

        player_votes = dict()
        player_to_eliminate = None

        # Tally votes
        for v in round_votes:
            voted_for_id = v.voted_for_id
            if voted_for_id not in player_votes:
                player_votes[voted_for_id] = 1
            else:
                player_votes[voted_for_id] += 1

        # Find player with most votes
        for player, num_votes in player_votes.items():
            player_tup = (player,num_votes)

            if player_to_eliminate == None:
                player_to_eliminate = player_tup
            elif num_votes > player_to_eliminate[1]:
                player_to_eliminate = player_tup

        #Eliminate player
        if player_to_eliminate is not None:
            eliminated_player_id = player_to_eliminate[0]
            await self.game.log(f"[Voting] {eliminated_player_id[:8]} eliminated with {player_to_eliminate[1]} votes")
            game_state.eliminate_player(eliminated_player_id, EliminationType.VOTED_OUT)

            # Log elimination event
            elimination_event = Event(
                type=EventType.VILLAGE_ELIMINATION,
                eliminated_player=eliminated_player_id,
                description=f"Player {eliminated_player_id} was eliminated by village vote with {player_to_eliminate[1]} votes"
            )
            self.game.log_event(current_round, elimination_event)