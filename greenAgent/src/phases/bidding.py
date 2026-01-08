from src.models.abstract.Phase import Phase
from src.models.Game import Game

class Bidding(Phase):
    def __init__(self, game:Game):
        super().__init__(game)
        
    def run(self):
        pass
    
    def get_prompt(self):
        pass
    
    