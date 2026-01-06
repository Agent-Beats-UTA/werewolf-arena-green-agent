from pydantic import BaseModel
from greenAgent.models.enum.Role import Role
from greenAgent.models.enum.Status import Status

class Participant(BaseModel):
    id:str
    url:str
    role: Role
    status: Status