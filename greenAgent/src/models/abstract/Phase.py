from pydantic import BaseModel
from abc import ABC, abstractmethod
from src.models.Game import Game
from src.a2a.messenger import Messenger

class Phase(ABC):
    
    def __init__(self, game:Game, messenger:Messenger):
        self.game = game
        self.messenger = messenger
    
    @abstractmethod
    def run(self):
        pass
    
    @abstractmethod
    def get_prompt(self):
        pass