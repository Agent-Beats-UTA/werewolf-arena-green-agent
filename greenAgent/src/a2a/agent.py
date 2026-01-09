
import random

from typing import Any, List
from pydantic import BaseModel, HttpUrl, ValidationError

from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskState, Part, TextPart, DataPart
from a2a.utils import get_message_text, new_agent_text_message

from src.a2a.messenger import Messenger
from src.models.EvalRequest import EvalRequest
from greenAgent.src.game.Game import Game
from src.models.Participant import Participant
from src.models.enum.Phase import Phase

from uuid import uuid4

from src.models.enum.Status import Status
from src.models.enum.Role import Role

class GreenAgent:
    """Runs Werewolf evaluation"""
    
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

        # Replace example code below with your agent logic
        # Use request.participants to get participant agent URLs by role
        # Use request.config for assessment parameters
        
        self.init_game(request.participants)
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
            
            #Discussion phase
            self.game.run_discussion_phase()
            await updater.update_status(
                TaskState.working, new_agent_text_message("discussion phase ended, starting voting")
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
            
            
        # await updater.add_artifact(
        #     parts=[
        #         Part(root=TextPart(text="The agent performed well.")),
        #         Part(root=DataPart(data={
        #             # structured assessment results
        #         }))
        #     ],
        #     name="Result",
        # )
        
        #Helpers
        def init_game(self, participant_urls:List[str]):
            """
            Takes a list of agent particpants and assigns roles for the game, creates participant objects
            and sets inital speaking order 
            
            :param participant_urls: Description
            :type participant_urls: List[str]
            """
            roles = [Role.VILLAGER, Role.WEREWOLF, Role.SEER]
            
            villagers = []
            werewolves = []
            seer = None
            
            #Assign roles to participants
            for url in participant_urls:
                    random_num = random.randint(1, 3)
                    role_assigned = False
                    
                    participant = Participant(
                        id=str(uuid4()),
                        url=url,
                        status=Status.ACTIVE
                    )
                    
                    while role_assigned == False:
                        selected_role = roles[random_num - 1]
                        
                        if selected_role == 1 and villagers.count < 3:
                            updated_participant = participant.role = selected_role
                            villagers.append(updated_participant)
                            role_assigned = True
                            
                        elif selected_role == 2 and werewolves.count < 2:
                            updated_participant = participant.role = selected_role
                            werewolves.append(updated_participant)
                            role_assigned = True
                            
                        elif selected_role == 3 and seer == None:
                            updated_participant = participant.role = selected_role
                            seer = updated_participant
                            role_assigned = True
                            
            all_participants = [*villagers, *werewolves, seer]
            self.game.state.participants = {p.id: p for p in all_participants}
            
            # Set random speaking order for round 1
            shuffled_participants = all_participants.copy()
            random.shuffle(shuffled_participants)
            self.game.state.speaking_order[1] = [p.id for p in shuffled_participants]
            
        def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
            missing_roles = set(self.required_roles) - set(request.participants.keys())
            if missing_roles:
                return False, f"Missing roles: {missing_roles}"

            missing_config_keys = set(self.required_config_keys) - set(request.config.keys())
            if missing_config_keys:
                return False, f"Missing config keys: {missing_config_keys}"

            # Add additional request validation here

            return True, "ok"

    