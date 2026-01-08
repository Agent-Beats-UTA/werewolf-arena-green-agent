import logging

from typing import List, Tuple
from src.models.abstract.Phase import Phase
from src.models.Game import Game
from src.a2a.messenger import Messenger

class Night(Phase):
    def __init__(self, game:Game, messenger:Messenger):
        super().__init__(game, messenger)
        
    def run(self):
        self.execute_werewolf_kill()
        self.execute_seer_investigation()

    def execute_werewolf_kill(self):
        game_state = self.game.state
        ## In this phase I need to do the following:
        ## 1. Send the werewolf an A2A task asking it to pick one participant to kill and explain why, wait for a response
        response = self.messenger.talk_to_agent(
            message=self.get_werewolf_prompt(
                round_num=game_state.current_round,
                participants=list(game_state.participants.keys())
            ),
            url=game_state.werewolf.url
        )

        # TODO: How do we parse a player Id and a reason from the A2A agent response.
        # The shape of the model response is to be defined by the purple agent. in this case I would just expect
        # Vote: <<player Id>>
        # Reason: <<vote reason>>

        player, rationale = response
        self.game.eliminate_player(reason)

        logger.log(f"Werewolf eliminated player: {player} for this reason. {rationale}")
        game_state.latest_werewolf_kill = player

    def execute_seer_investigation(self):
        game_state = self.game.state

        response = self.messenger.talk_to_agent(
            message=get_seer_prompt(
            round_num=game_state.current_round,
            participants=list(game_state.participants.keys()),
            previous_checks=game_state.seer_checks
            ),
            url=game_state.seer.url
        )

        #TODO: Need to figure out how to properly parse specific info from agent response

        player, rationale = response
        logger.log(f"Seer chose to investigate player: {player} for this reason: {rationale}")

        response = self.messenger.talk_to_agent(
            message=self.get_seer_reveal_prompt(
                player_id=player,
                is_werewolf=self.is_werewolf(player)
            )
        )

        logger.log(f"Seer investigation concluded")

    # Helpers    
    def is_werewolf(self, player_id:str):
        return game_state.werewolf.id == player_id
    
    # Prompts
    def get_prompt(self):
        return ""
    
    def get_seer_prompt(self, round_num:int, participants:List[str], previous_checks:List[Tuple[str, bool]]):
        previous_checked_names = [name for name, _ in previous_checks]
        remaining_participants = "\n".join([f"- {p}" for p in participants if p not in previous_checked_names])
        seen_participants  = "\n".join([f"- {p[0]} is werewolf: {p[1]}" for p in previous_checks])
        return f"""
            ROUND {round_num}:

            YOU ARE THE SEER

            Pick one participant to investigate. If you already know who the werewolf is, you don't have
            to investigate someone again.

            Here is the list of participants you have not checked:
            {remaining_participants}

            Here is a list of participants you have checked:
            {seen_participants}

            Be sure to also explain why you are choosing to investigate this player.
        """

    def get_werewolf_prompt(self, round_num:int, participants:List[str]):
        participants_list = "\n".join([f"- {p}" for p in participants])
        return f"""
            ROUND {round_num}:

            YOU ARE THE WEREWOLF

            Pick one participant to eliminate. Here is a list of the participants:
            {participants_list}

            Be sure to also explain why you are choosing to eliminate this player.
        """

    def get_seer_reveal_prompt(self, player_id:str, is_werewolf:bool):
        return f"""
            Here are the results of your investigation:

            You investigated player: {player_id}
            They {"are" if is_werewolf else "are not"} the werewolf

        """