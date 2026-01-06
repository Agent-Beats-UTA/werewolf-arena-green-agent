from pydantic import BaseModel
from greenAgent.models.enum.EliminationType import EliminationType

class Elimination(BaseModel):
    eliminated_participant: str
    elimination_type:EliminationType