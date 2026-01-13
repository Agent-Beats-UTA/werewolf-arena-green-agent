from typing import TYPE_CHECKING, Dict, Any

from src.models.abstract.Phase import Phase
from src.game.analytics import compute_game_analytics, render_summary_text

if TYPE_CHECKING:
    from src.game.Game import Game
    from src.a2a.messenger import Messenger

class GameEnd(Phase):
    def __init__(self, game: "Game", messenger: "Messenger"):
        super().__init__(game, messenger)
        self.analytics: Dict[str, Any] = {}
        
    async def run(self) -> Dict[str, Any]:
        analytics = compute_game_analytics(self.game.state)
        analytics["summary_text"] = render_summary_text(analytics)
        return analytics
