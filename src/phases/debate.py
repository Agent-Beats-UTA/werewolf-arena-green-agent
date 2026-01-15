from typing import TYPE_CHECKING

from src.models.abstract.Phase import Phase as PhaseBase
from src.models.Message import Message
from src.models.enum.Phase import Phase as PhaseEnum

if TYPE_CHECKING:
    from src.game.Game import Game
    from src.a2a.messenger import Messenger

class Debate(PhaseBase):
    def __init__(self, game: "Game", messenger: "Messenger"):
        super().__init__(game, messenger)

    async def run(self):
        game_state = self.game.state
        current_round = game_state.current_round
        speaking_order = game_state.speaking_order.get(current_round, [])
        participants = game_state.participants.get(current_round, [])

        # Create a dict for easy lookup by participant_id
        participants_dict = {p.id: p for p in participants}

        # Filter speaking order to only include current participants (exclude eliminated)
        active_speaking_order = [pid for pid in speaking_order if pid in participants_dict]

        await self.game.log(f"[Debate] {len(active_speaking_order)} participants debating...")

        for _ in range(self.game.state.turns_to_speak_per_round):
            for participant_id in active_speaking_order:
                participant = participants_dict[participant_id]

                await self.game.log(f"[Debate] {participant_id[:8]} speaking...")
                response = await participant.talk_to_agent(
                    prompt=participant.get_debate_prompt(),
                )

                message_content = response["message"]
                await self.game.log(f"[Debate] {participant_id[:8]}: {message_content[:50]}...")

                # Store response in chat history
                message = Message(
                    sender_id=participant_id,
                    content=message_content,
                    phase=PhaseEnum.DISCUSSION
                )
                if current_round not in game_state.chat_history:
                    game_state.chat_history[current_round] = []

                game_state.chat_history[current_round].append(message)