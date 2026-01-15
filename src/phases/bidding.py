from typing import TYPE_CHECKING

from src.models.abstract.Phase import Phase
from src.models.Bid import Bid
from src.models.Event import Event
from src.models.enum.EventType import EventType

if TYPE_CHECKING:
    from src.game.Game import Game
    from src.a2a.messenger import Messenger

class Bidding(Phase):
    def __init__(self, game: "Game", messenger: "Messenger"):
        super().__init__(game, messenger)

    async def run(self):
        await self.game.log("[Bidding] Collecting bids...")
        await self.collect_round_bids()
        self.tally_bids_and_set_order()

    async def collect_round_bids(self):
        game_state = self.game.state
        current_round = game_state.current_round

        current_participants = game_state.participants[current_round]

        for participant in current_participants:
            await self.game.log(f"[Bidding] {participant.id[:8]} placing bid...")
            response = await participant.talk_to_agent(
                prompt=participant.get_bid_prompt(),
            )

            bid_amount = response["bid_amount"]
            reason = response["reason"]
            await self.game.log(f"[Bidding] {participant.id[:8]} bid {bid_amount}")

            player_bid = Bid(
                participant_id=participant.id,
                amount=bid_amount
            )

            if current_round not in game_state.bids:
                game_state.bids[current_round] = []

            game_state.bids[current_round].append(player_bid)

            # Log Event
            bid_event = Event(
                type=EventType.BID_PLACED,
                player=participant.id,
                description=f"Placed a bid of {bid_amount} points for rationale: {reason}"
            )

            self.game.log_event(current_round, bid_event)

    def tally_bids_and_set_order(self):
        game_state = self.game.state
        current_round = game_state.current_round
        round_bids = game_state.bids[current_round]
        
        # Sort bids in descending order
        sorted_bids = sorted(round_bids, key=lambda bid: bid.amount, reverse=True)
        
        # Set speaking order based on bids
        speaking_order = [bid.participant_id for bid in sorted_bids]
        game_state.speaking_order[current_round] = speaking_order
        
        # Log Event
        order_event = Event(
            type=EventType.SPEAKING_ORDER_SET,
            player="System",
            description=f"Speaking order for round {current_round} set as: {', '.join(speaking_order)}"
        )

        self.game.log_event(current_round, order_event)