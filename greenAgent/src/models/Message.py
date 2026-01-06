from pydantic import BaseModel
from greenAgent.models.enum.Phase import Phase

class Message(BaseModel):
    sender_id:str
    content:str
    phase:Phase