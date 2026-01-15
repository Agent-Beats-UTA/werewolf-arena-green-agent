
import random

from typing import Any, List
from pydantic import BaseModel, HttpUrl, ValidationError

from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskState, Part, TextPart, DataPart
from a2a.utils import get_message_text, new_agent_text_message

from src.a2a.messenger import Messenger
from src.models.EvalRequest import EvalRequest
from src.game.Game import Game
from src.models.Participant import Participant
from src.models.enum.Phase import Phase

from uuid import uuid4

from src.models.enum.Role import Role
from src.services.llm import LLM

class GreenAgent:
    """Runs Werewolf evaluation"""

    # Required roles for game participants
    required_roles: set = set()  # No required roles - participant can be any role

    # Required config keys for game setup
    required_config_keys: set = set()  # No required config keys by default

    def __init__(self):
        self.messenger = Messenger()
        self.game = Game([])
    
        
    async def run(self, message: Message, updater: TaskUpdater) -> None:
        """Implement your agent logic here.

        Args:
            message: The incoming message
            updater: Report progress (update_status) and results (add_artifact)

        Use self.messenger.talk_to_agent(message, url) to call other agents.
        """
        # Reset state for new evaluation
        self.messenger.reset()
        self.game = Game([])

        game_over = False
        input_text = get_message_text(message)

        try:
            request: EvalRequest = EvalRequest.model_validate_json(input_text)
            ok, msg = self.validate_request(request)
            if not ok:
                await updater.reject(new_agent_text_message(msg))
                return
        except ValidationError as e:
            await updater.reject(new_agent_text_message(f"Invalid request: {e}"))
            return

        # Get the participant's role and URL
        participant_role = request.config.get("role")
        participant_url = next(iter(request.participants.values()))
        
        await updater.update_status(
            TaskState.working, new_agent_text_message(f"Parsed participant {participant_url} with role: {participant_role} from request")
        )

        self.init_game(participant_url, participant_role)
        while game_over == False:
            
            #Night Phase
            self.game.run_night_phase()
            await updater.update_status(
                TaskState.working, new_agent_text_message("Night phase ended, starting bidding")
            )
            
            #Bidding phase
            self.game.run_bidding_phase()
            await updater.update_status(
                TaskState.working, new_agent_text_message("Bidding phase ended, started discussion")
            )
            
            #Debate phase
            self.game.run_debate_phase()
            await updater.update_status(
                TaskState.working, new_agent_text_message("debate phase ended, starting voting")
            )
            
            #Voting phase
            self.game.run_voting_phase()
            await updater.update_status(
                TaskState.working, new_agent_text_message("Voting phase ended")
            )
            
            #Round end
            self.game.run_round_end_phase()
            await updater.update_status(
                TaskState.working, new_agent_text_message("Round end")
            )
            
            # Check if game ends
            if self.game.current_phase == Phase.GAME_END:
                game_over = True
                await updater.update_status(
                TaskState.working, new_agent_text_message("Game ended, compiling results and analytics")
            )
            
        analytics = await self.game.run_game_end_phase()

        await updater.add_artifact(
            parts=[
                Part(root=TextPart(text=analytics.get("summary_text", "Game complete."))),
                Part(root=DataPart(data=analytics))# structured assessment results
            ],
            name="Result",
        )

    def init_game(self, participant_url: str, participant_role: Role):
        """
        Takes one participant URL and their role, then creates LLM-based participants
        to fill out the rest of the game (3 villagers, 2 werewolves, 1 seer total)

        :param participant_url: URL of the real participant agent
        :type participant_url: str
        :param participant_role: Role assigned to the real participant
        :type participant_role: Role
        """
        # Game composition: 3 villagers, 2 werewolves, 1 seer
        needed_roles = {
            Role.VILLAGER: 3,
            Role.WEREWOLF: 2,
            Role.SEER: 1
        }

        # Decrease the count for the real participant's role
        needed_roles[participant_role] -= 1

        all_participants = []

        # Create the real participant (uses URL to talk to external agent)
        real_participant = Participant(
            id=str(uuid4()),
            url=participant_url,
            role=participant_role,
            use_llm=False,
            game_data=self.game.state,
            messenger=self.messenger
        )
        all_participants.append(real_participant)

        # Track werewolves and seer for special role references
        werewolves = []
        seer = None

        if participant_role == Role.WEREWOLF:
            werewolves.append(real_participant)
        elif participant_role == Role.SEER:
            seer = real_participant

        # Create LLM-based participants for remaining roles
        for role, count in needed_roles.items():
            for _ in range(count):
                llm_participant = Participant(
                    id=str(uuid4()),
                    role=role,
                    use_llm=True,
                    game_data=self.game.state,
                    messenger=self.messenger,
                    llm=LLM()
                )
                all_participants.append(llm_participant)

                # Track special roles
                if role == Role.WEREWOLF:
                    werewolves.append(llm_participant)
                elif role == Role.SEER:
                    seer = llm_participant

        # Store participants by round number (round 1 initially)
        self.game.state.participants[1] = all_participants

        # Assign special role references (use first werewolf for night kill decisions)
        self.game.state.werewolf = werewolves[0] if werewolves else None
        self.game.state.seer = seer

        # Set random speaking order for round 1
        shuffled_participants = all_participants.copy()
        random.shuffle(shuffled_participants)
        self.game.state.speaking_order[1] = [p.id for p in shuffled_participants]
    
    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
      if not request.participants:
          return False, "No participant provided"

      if not request.config.get("role"):
          return False, "No participant role specified in config"

      return True, "ok"
