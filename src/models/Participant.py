import json
from typing import Optional, TYPE_CHECKING, Any

from pydantic import BaseModel
from src.models.enum.Role import Role
from src.services.llm import LLM
from src.a2a.messenger import Messenger

if TYPE_CHECKING:
    from src.game.AgentState import AgentState
    from src.game.GameData import GameData

class Participant(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    id: str
    role: Role
    game_data: Any  # GameData at runtime
    use_llm: bool
    messenger: Any  # Messenger at runtime
    llm_state: Optional[Any] = None  # AgentState at runtime
    url: Optional[str] = None
    llm: Optional[Any] = None  # LLM at runtime

    #Messaging
    async def talk_to_agent(self, prompt: str):
        if not prompt or not prompt.strip():
            raise ValueError(f"[Participant {self.id[:8]}] Attempted to send empty prompt")

        if self.use_llm:
            response = self.llm.execute_prompt(prompt=prompt)
        else:
            # Use new_conversation=True to avoid context continuation issues
            response = await self.messenger.talk_to_agent(
                message=prompt,
                url=self.url,
                new_conversation=True
            )

        parsed = self.parse_json_response(response)
        return parsed
        
    def parse_json_response(self, response: str) -> dict:
        """
        Parse JSON response from agent.
        Expected format varies by phase, but generally: {"key": "value", ...}
        """
        try:
            # Try to parse the entire response as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from markdown code blocks
            # Sometimes LLMs wrap JSON in ```json ... ```
            json_match = response.find("```json")
            if json_match != -1:
                start = response.find("\n", json_match) + 1
                end = response.find("```", start)
                json_str = response[start:end].strip()
                return json.loads(json_str)

            # Try without the json marker
            json_match = response.find("```")
            if json_match != -1:
                start = response.find("\n", json_match) + 1
                end = response.find("```", start)
                json_str = response[start:end].strip()
                return json.loads(json_str)

            # If all else fails, raise an error with the response
            raise ValueError(f"Could not parse JSON from agent response: {response}")
        
    
    #Helpers
    def get_context_prompt(self):
        return f"""
            You are a participant in a game of werewolf.
            Your player ID: {self.id}
            Your role: {self.role.name}
        """
            
    # Prompts
    def get_vote_prompt(self) -> str:
        current_round = self.game_data.current_round
        messages = self.game_data.chat_history.get(current_round, [])
        participants = self.game_data.participants.get(current_round, [])

        messages_w_ids = [f"{msg.sender_id} - {msg.content}" for msg in messages]
        participant_ids = [p.id for p in participants if p.id != self.id]

        context = self.get_context_prompt()

        return f"""
            {context}

            It's time to vote for a player to eliminate.

            Your role is: {self.role.name}

            Here is all of the conversations from this round:
            {chr(10).join(messages_w_ids)}

            Pick a single player to eliminate and provide an explanation as to why.
            Here are the players to choose from:
            {chr(10).join(participant_ids)}

            Respond in JSON format:
            {{
                "player_id": "the player ID you want to eliminate",
                "reason": "your explanation for why you are eliminating this player"
            }}

            IMPORTANT: You MUST respond with valid JSON only. Do not include any text, markdown, or explanation before or after the JSON object.
        """

    def get_werewolf_prompt(self) -> str:
        current_round = self.game_data.current_round
        participants = self.game_data.participants.get(current_round, [])
        participant_ids = [p.id for p in participants if p.id != self.id]

        context = self.get_context_prompt()
        participants_list = "\n".join([f"- {p}" for p in participant_ids])

        return f"""
            {context}

            ROUND {current_round}:

            YOU ARE THE WEREWOLF

            Pick one participant to eliminate. Here is a list of the participants:
            {participants_list}

            Be sure to also explain why you are choosing to eliminate this player.

            Respond with a JSON object in the following format:
            {{
                "player_id": "the player ID you want to eliminate",
                "reason": "your explanation for why you are eliminating this player"
            }}

            IMPORTANT: You MUST respond with valid JSON only. Do not include any text, markdown, or explanation before or after the JSON object.
        """

    def get_seer_prompt(self) -> str:
        current_round = self.game_data.current_round
        participants = self.game_data.participants.get(current_round, [])
        previous_checks = self.game_data.seer_checks

        context = self.get_context_prompt()

        previous_checked_names = [name for name, _ in previous_checks]
        remaining = [p.id for p in participants if p.id not in previous_checked_names and p.id != self.id]
        remaining_list = "\n".join([f"- {p}" for p in remaining])
        checked_list = "\n".join([f"- {name} is werewolf: {result}" for name, result in previous_checks])

        return f"""
            {context}

            ROUND {current_round}:

            YOU ARE THE SEER

            Pick one participant to investigate. If you already know who the werewolf is, you don't have
            to investigate someone again.

            Participants you have not checked:
            {remaining_list if remaining_list else "None"}

            Participants you have checked:
            {checked_list if checked_list else "None"}

            Explain why you are choosing to investigate this player.

            Respond with a JSON object in the following format:
            {{
                "player_id": "the player ID you want to investigate",
                "reason": "your explanation for why you are investigating this player"
            }}

            IMPORTANT: You MUST respond with valid JSON only. Do not include any text, markdown, or explanation before or after the JSON object.
        """

    def get_seer_reveal_prompt(self, player_id: str, is_werewolf: bool) -> str:
        context = self.get_context_prompt()

        return f"""
            {context}

            Here are the results of your investigation:

            You investigated player: {player_id}
            They {"are" if is_werewolf else "are not"} the werewolf
        """

    def get_bid_prompt(self) -> str:
        current_round = self.game_data.current_round
        bids = self.game_data.bids.get(current_round, [])

        context = self.get_context_prompt()
        bids_list = "\n".join([f"- Participant {bid.participant_id}: {bid.amount} points" for bid in bids])

        return f"""
            {context}

            It is time to place your bid for speaking order in the upcoming debate round.
            You are playing as a {self.role.name}.

            Place a bid between 0 and 100 points to determine your speaking order.

            Remember, your bid will determine when you get to speak, with higher bids allowing you to speak earlier.
            Consider your strategy carefully based on the current state of the game.

            Current bids from other participants:
            {bids_list if bids_list else "No bids yet."}

            Respond in JSON format:
            {{
                "bid_amount": <your_bid_amount>,
                "reason": "your explanation for your bid"
            }}

            IMPORTANT: You MUST respond with valid JSON only. Do not include any text, markdown, or explanation before or after the JSON object.
        """

    def get_debate_prompt(self) -> str:
        current_round = self.game_data.current_round
        messages = self.game_data.chat_history.get(current_round, [])
        speaking_order = self.game_data.speaking_order.get(current_round, [])
        latest_kill = self.game_data.latest_werewolf_kill

        context = self.get_context_prompt()
        messages_str = "\n".join([f"{msg.sender_id}: {msg.content}" for msg in messages])
        order_str = ", ".join(speaking_order)

        night_info = f"Last night, {latest_kill} was eliminated by the werewolf." if latest_kill else ""

        return f"""
            {context}

            ROUND {current_round} - Debate Phase

            Your role is: {self.role.name}

            {night_info}

            Speaking order: {order_str}

            Conversation so far:
            {messages_str if messages_str else "No messages yet."}

            Share your thoughts with the group. Try to identify the werewolf (or deflect suspicion if you are the werewolf).

            Respond in JSON format:
            {{
                "message": "your message to the group"
            }}

            IMPORTANT: You MUST respond with valid JSON only. Do not include any text, markdown, or explanation before or after the JSON object.
        """