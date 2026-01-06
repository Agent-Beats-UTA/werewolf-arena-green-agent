from pydantic import BaseModel

class Vote(BaseModel):
    voter_id:str
    voted_for_id:str
    rationale:str