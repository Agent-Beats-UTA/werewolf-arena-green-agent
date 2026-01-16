
import random

from typing import Any, Dict, List
from pydantic import BaseModel, HttpUrl, ValidationError

from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskState, Part, TextPart, DataPart
from a2a.utils import get_message_text, new_agent_text_message

from src.a2a.messenger import Messenger
from src.models.EvalRequest import EvalRequest
from src.game.Game import Game
from src.models.Participant import Participant
from src.models.enum.Phase import Phase

from uuid import uuid4

from src.models.enum.Role import Role
from src.services.llm import LLM

# Number of games to play per role
GAMES_PER_ROLE = 5
ROLES_TO_EVALUATE = [Role.VILLAGER, Role.WEREWOLF, Role.SEER]

class GreenAgent:
    """Runs Werewolf evaluation across multiple games and roles."""

    def __init__(self):
        self.messenger = Messenger()
        self.game = Game([])
    
        
    async def run(self, message: Message, updater: TaskUpdater) -> None:
        """Implement your agent logic here.

        Args:
            message: The incoming message
            updater: Report progress (update_status) and results (add_artifact)

        Use self.messenger.talk_to_agent(message, url) to call other agents.
        """
        input_text = get_message_text(message)

        try:
            request: EvalRequest = EvalRequest.model_validate_json(input_text)
            ok, msg = self.validate_request(request)
            if not ok:
                await updater.reject(new_agent_text_message(msg))
                return
        except ValidationError as e:
            await updater.reject(new_agent_text_message(f"Invalid request: {e}"))
            return

        participant_url = str(next(iter(request.participants.values())))

        # Data structure to store results from all games, grouped by role
        all_game_results: Dict[Role, List[Dict[str, Any]]] = {
            role: [] for role in ROLES_TO_EVALUATE
        }

        total_games = GAMES_PER_ROLE * len(ROLES_TO_EVALUATE)
        games_completed = 0

        await updater.update_status(
            TaskState.working,
            new_agent_text_message(f"Starting evaluation: {total_games} games ({GAMES_PER_ROLE} per role)")
        )

        # Run games for each role
        for role in ROLES_TO_EVALUATE:
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(f"Starting {GAMES_PER_ROLE} games as {role.name}")
            )

            for game_num in range(1, GAMES_PER_ROLE + 1):
                games_completed += 1

                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(f"Game {games_completed}/{total_games}: Playing as {role.name} (game {game_num}/{GAMES_PER_ROLE})")
                )

                # Run a single game and collect analytics
                game_analytics = await self.run_single_game(participant_url, role, updater)
                all_game_results[role].append(game_analytics)

        await updater.update_status(
            TaskState.working, new_agent_text_message("All games completed, compiling aggregate analytics")
        )

        # Compute aggregate analytics across all games
        aggregate_analytics = self.compute_aggregate_analytics(all_game_results, participant_url)
        summary_text = self.render_aggregate_summary(aggregate_analytics)

        await updater.add_artifact(
            parts=[
                Part(root=TextPart(text=summary_text)),
                Part(root=DataPart(data=aggregate_analytics))
            ],
            name="Result",
        )

    async def run_single_game(self, participant_url: str, participant_role: Role, updater: TaskUpdater) -> Dict[str, Any]:
        """Run a single game and return the analytics."""
        # Reset state for new game
        self.messenger.reset()
        self.game = Game([])

        self.init_game(participant_url, participant_role)
        self.game.updater = updater

        # Store participant ID before game starts (they may be eliminated during the game)
        participant_id = self.get_participant_id_by_url(participant_url)

        game_over = False
        while game_over == False:
            await self.game.run_night_phase()
            await self.game.run_bidding_phase()
            await self.game.run_debate_phase()
            await self.game.run_voting_phase()
            await self.game.run_round_end_phase()

            if self.game.current_phase == Phase.GAME_END:
                game_over = True

        analytics = await self.game.run_game_end_phase()

        # Add participant-specific info to analytics
        if participant_id:
            analytics["participant_id"] = participant_id
            analytics["participant_role"] = participant_role.name
            analytics["participant_score"] = analytics.get("scores", {}).get(participant_id, 0)
            # Check if participant survived by seeing if they're still in the final round's participants
            final_round = self.game.state.current_round
            final_participants = self.game.state.participants.get(final_round, [])
            analytics["participant_survived"] = any(p.id == participant_id for p in final_participants)

        return analytics

    def get_participant_id_by_url(self, url: str) -> str | None:
        """Find the participant ID for the given URL from round 1."""
        round_1_participants = self.game.state.participants.get(1, [])
        for p in round_1_participants:
            if hasattr(p, 'url') and p.url == url:
                return p.id
        return None

    def compute_aggregate_analytics(self, all_results: Dict[Role, List[Dict[str, Any]]], participant_url: str) -> Dict[str, Any]:
        """Compute aggregate analytics across all games, grouped by role."""
        aggregate = {
            "total_games": sum(len(games) for games in all_results.values()),
            "games_per_role": GAMES_PER_ROLE,
            "participant_url": participant_url,
            "by_role": {}
        }

        for role, games in all_results.items():
            if not games:
                continue

            role_stats = {
                "games_played": len(games),
                "wins": 0,
                "losses": 0,
                "survival_rate": 0,
                "avg_score": 0,
                "avg_rounds": 0,
                "total_score": 0,
                "games": games  # Store individual game data
            }

            survived_count = 0
            total_rounds = 0
            total_score = 0

            for game in games:
                winner = game.get("winner")
                participant_role = game.get("participant_role")

                # Determine if participant won
                if participant_role == "WEREWOLF":
                    won = winner == "werewolf"
                else:  # VILLAGER or SEER
                    won = winner == "villagers"

                if won:
                    role_stats["wins"] += 1
                else:
                    role_stats["losses"] += 1

                if game.get("participant_survived", False):
                    survived_count += 1

                total_rounds += game.get("rounds_played", 0)
                total_score += game.get("participant_score", 0)

            role_stats["survival_rate"] = survived_count / len(games) if games else 0
            role_stats["avg_rounds"] = total_rounds / len(games) if games else 0
            role_stats["avg_score"] = total_score / len(games) if games else 0
            role_stats["total_score"] = total_score
            role_stats["win_rate"] = role_stats["wins"] / len(games) if games else 0

            aggregate["by_role"][role.name] = role_stats

        # Overall stats
        total_wins = sum(stats["wins"] for stats in aggregate["by_role"].values())
        total_games = aggregate["total_games"]
        aggregate["overall_win_rate"] = total_wins / total_games if total_games else 0
        aggregate["overall_total_score"] = sum(stats["total_score"] for stats in aggregate["by_role"].values())

        return aggregate

    def render_aggregate_summary(self, analytics: Dict[str, Any]) -> str:
        """Render a human-readable summary of aggregate analytics."""
        lines = [
            "=" * 60,
            "WEREWOLF ARENA - EVALUATION COMPLETE",
            "=" * 60,
            f"Total Games Played: {analytics['total_games']}",
            f"Games Per Role: {analytics['games_per_role']}",
            f"Overall Win Rate: {analytics['overall_win_rate']:.1%}",
            f"Overall Total Score: {analytics['overall_total_score']}",
            "",
            "-" * 60,
            "PERFORMANCE BY ROLE",
            "-" * 60,
        ]

        for role_name, stats in analytics.get("by_role", {}).items():
            lines.extend([
                "",
                f"  {role_name}:",
                f"    Games Played: {stats['games_played']}",
                f"    Wins: {stats['wins']} | Losses: {stats['losses']}",
                f"    Win Rate: {stats['win_rate']:.1%}",
                f"    Survival Rate: {stats['survival_rate']:.1%}",
                f"    Avg Rounds per Game: {stats['avg_rounds']:.1f}",
                f"    Avg Score: {stats['avg_score']:.1f}",
                f"    Total Score: {stats['total_score']}",
            ])

        lines.extend([
            "",
            "=" * 60,
        ])

        return "\n".join(lines)

    def init_game(self, participant_url: str, participant_role: Role):
        """
        Takes one participant URL and their role, then creates LLM-based participants
        to fill out the rest of the game (3 villagers, 2 werewolves, 1 seer total)

        :param participant_url: URL of the real participant agent
        :type participant_url: str
        :param participant_role: Role assigned to the real participant
        :type participant_role: Role
        """
        # Game composition: 3 villagers, 2 werewolves, 1 seer
        needed_roles = {
            Role.VILLAGER: 3,
            Role.WEREWOLF: 2,
            Role.SEER: 1
        }

        # Decrease the count for the real participant's role
        needed_roles[participant_role] -= 1

        all_participants = []

        # Create the real participant (uses URL to talk to external agent)
        real_participant = Participant(
            id=str(uuid4()),
            url=participant_url,
            role=participant_role,
            use_llm=False,
            game_data=self.game.state,
            messenger=self.messenger
        )
        all_participants.append(real_participant)

        # Track werewolves and seer for special role references
        werewolves = []
        seer = None

        if participant_role == Role.WEREWOLF:
            werewolves.append(real_participant)
        elif participant_role == Role.SEER:
            seer = real_participant

        # Create LLM-based participants for remaining roles
        for role, count in needed_roles.items():
            for _ in range(count):
                llm_participant = Participant(
                    id=str(uuid4()),
                    role=role,
                    use_llm=True,
                    game_data=self.game.state,
                    messenger=self.messenger,
                    llm=LLM()
                )
                all_participants.append(llm_participant)

                # Track special roles
                if role == Role.WEREWOLF:
                    werewolves.append(llm_participant)
                elif role == Role.SEER:
                    seer = llm_participant

        # Store participants by round number (round 1 initially)
        self.game.state.participants[1] = all_participants

        # Assign special role references (use first werewolf for night kill decisions)
        self.game.state.werewolf = werewolves[0] if werewolves else None
        self.game.state.seer = seer

        # Set random speaking order for round 1
        shuffled_participants = all_participants.copy()
        random.shuffle(shuffled_participants)
        self.game.state.speaking_order[1] = [p.id for p in shuffled_participants]
    
    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
      if not request.participants:
          return False, "No participant provided"

      return True, "ok"
