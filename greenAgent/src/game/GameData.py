from pydantic import BaseModel
from typing import Dict, List, Optional

from src.models.enum.EliminationType import EliminationType
from src.models.enum.Status import Status
from src.models.Participant import Participant
from src.models.Message import Message
from src.models.Vote import Vote
from src.models.Elimination import Elimination
from src.models.Event import Event

from src.models.enum.Role import Role
from src.models.enum.Status import Status

class GameData(BaseModel):
    current_round: int
    winner: Optional[str]  # "werewolves", "villagers", or None
    turns_to_speak_per_round: int
    participants: Dict[int, List[Participant]]
    werewolf:Participant
    seer: Participant
    villagers:List[Participant]
    speaking_order: Dict[int, List[str]]
    chat_history: Dict[int, List[Message]]
    bids: Dict[int, List[str]]
    votes: Dict[int, List[Vote]]
    eliminations: Dict[int, List[Elimination]]
    events: Dict[int, List[Event]]

    def set_status(self, status: str):  # assignment | player_actions | bidding | discussion | voting | end | reset
        pass

    def declare_winner(self, winner: str):
        self.winner = winner

    def place_bid(self, participant_id: str, bid_amount: int):
        pass

    def cast_vote(self, voter: str, voting_for: str, rationale: str):
        vote = Vote(voter_id=voter, voted_for_id=voting_for, rationale=rationale)
        if self.current_round not in self.votes:
            self.votes[self.current_round] = []
        self.votes[self.current_round].append(vote)

    def add_participant(self, participant_id: str, url: str):
        # Assuming Participant needs id and url, role and status default
        participant = Participant(id=participant_id, url=url, role=Role.VILLAGER, status=Status.ACTIVE)
        self.participants[participant_id] = participant

    def assign_role_to_participant(self, participant_id: str, role: str):
        if participant_id in self.participants:
            self.participants[participant_id].role = getattr(Role, role.upper())

    def eliminate_player(self, participant_id: str):
        if participant_id in self.participants:
            self.participants[participant_id].status = Status.ELIMINATED
            # Add to eliminations
            elimination = Elimination(eliminated_participant=participant_id, elimination_type=EliminationType.VOTED_OUT)
            if self.current_round not in self.eliminations:
                self.eliminations[self.current_round] = []
            self.eliminations[self.current_round].append(elimination)