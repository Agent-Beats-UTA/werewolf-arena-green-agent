from src.models.abstract.Phase import Phase
from src.game.Game import Game

class Voting(Phase):
    def __init__(self, game:Game):
        super().__init__(game)
        
    def run(self):
        pass
    