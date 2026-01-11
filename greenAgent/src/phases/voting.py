from src.models.abstract.Phase import Phase
from src.models import Message, Participant, Event, Vote
from src.models.enum.EventType import EventType
from src.game.Game import Game
from src.a2a.messenger import Messenger
from typing import List

class Voting(Phase):
    def __init__(self, game:Game, messenger:Messenger):
        super().__init__(game, messenger)
        
    def run(self):
        self.collect_round_votes()
        self.tally_and_eliminate()
        
    def collect_round_votes(self) :        
        game_state = self.game.state
        current_round = game_state.current_round
        
        current_participants = game_state.participants[current_round]
        round_discussion = game_state.chat_history[current_round]
        
        #Send prompt for player vote
        for participant in current_participants:
            response = self.messenger.talk_to_agent(
                message=self.get_vote_prompt(
                    user_role=participant.role,
                    participants=current_participants,
                    messages=round_discussion
                ),
                url=participant.url
            )
            
            parsed = self._parse_json_response(response)
            voted_for = parsed["player_id"]
            rationale = parsed["reason"]
            
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
            
            self.game.log_event(player_vote_event)
        
    def tally_and_eliminate(self):
        game_state = self.game.state
        current_round = game_state.current_round
        round_votes = game_state.votes[current_round]
        
        player_votes = dict()
        player_to_eliminate = None
        
        # Tally votes
        for v in round_votes:
            voted_for_id = v.voted_for_id
            if player_votes[voted_for_id] is None:
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
        game_state.eliminate_player(player_tup[0])
            
    # Prompts
    def get_vote_prompt(self, user_role:str, messages:List[Message], participants:List[Participant]):
        messages_w_ids = [f"{message.sender_id} - {message.content}" for message in messages]
        participant_ids = [p.id for p in participants]
        
        return f"""
            It's time to vote for a player to eliminate:
            
            remember your role is: {user_role}
            
            Here is all of the conversations from this round:
            {"\n".join(messages_w_ids)}
            
            Pick a single player to eliminate and provide an explination as to why.
            Here are a list of players to chose from:
            {"\n".join(participant_ids)}
            
            Be sure to provide you response in JSON format as follows:
            {{
                "player_id": "the player ID you want to eliminate",
                "reason": "your explanation for why you are eliminating this player"
            }}
        """