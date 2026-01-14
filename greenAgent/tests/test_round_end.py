import pytest
from unittest.mock import Mock

from src.phases.round_end import RoundEnd
from src.models.enum.Phase import Phase
from src.models.enum.Role import Role
from src.models.enum.EventType import EventType


class TestRoundEndPhase:
   

    def test_round_end_phase_initialization(self, mock_game):
        """Test round end phase initializes correctly"""
        round_end = RoundEnd(mock_game, mock_game.messenger)

        assert round_end.game == mock_game
        assert round_end.messenger == mock_game.messenger

    def test_round_end_phase_run(self, mock_game):
        """Test that round end phase run method executes without error"""
        round_end = RoundEnd(mock_game, mock_game.messenger)

        round_end.run()

        mock_game.log_event.assert_called_once()
        call_args = mock_game.log_event.call_args
        assert call_args[0][0] == mock_game.state.current_round
        assert call_args[0][1].type == EventType.ROUND_END

    def test_round_end_checks_win_conditions(self, mock_game):
        """Test that round end phase checks win conditions."""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.current_round = 1
        mock_game.state.participants = {1: []}
        mock_game.current_phase = Phase.NIGHT

        round_end.run()

        assert mock_game.log_event.called

    def test_round_end_villagers_win_condition(self, mock_game, sample_participants):
        """Test that round end detects villagers win when werewolf is eliminated"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.current_round = 1
        mock_game.state.werewolf = sample_participants["werewolf"]
        mock_game.state.participants = {
            1: [
                sample_participants["seer"],
                sample_participants["villager1"],
                sample_participants["villager2"],
                sample_participants["villager3"]
            ]
        }
        mock_game.state.declare_winner = Mock()
        mock_game.current_phase = Phase.NIGHT

        round_end.run()

        mock_game.state.declare_winner.assert_called_once_with("villagers")
        assert mock_game.current_phase == Phase.GAME_END

    def test_round_end_werewolf_win_condition(self, mock_game, sample_participants):
        """Test that round end detects werewolf win when villagers <= 1."""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.current_round = 1
        mock_game.state.werewolf = sample_participants["werewolf"]
        mock_game.state.participants = {
            1: [
                sample_participants["werewolf"],
                sample_participants["seer"]
            ]
        }
        mock_game.state.declare_winner = Mock()
        mock_game.current_phase = Phase.NIGHT

        round_end.run()

        mock_game.state.declare_winner.assert_called_once_with("werewolf")
        assert mock_game.current_phase == Phase.GAME_END

    def test_round_end_werewolf_win_with_only_werewolf(self, mock_game, sample_participants):
        """Test that round end detects werewolf win when only werewolf remains"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.current_round = 1
        mock_game.state.werewolf = sample_participants["werewolf"]
        mock_game.state.participants = {
            1: [sample_participants["werewolf"]]
        }
        mock_game.state.declare_winner = Mock()
        mock_game.current_phase = Phase.NIGHT

        round_end.run()

        mock_game.state.declare_winner.assert_called_once_with("werewolf")
        assert mock_game.current_phase == Phase.GAME_END

    def test_round_end_continues_game(self, mock_game, sample_participants):
        """Test that round end continues to next round if no win condition is met"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.current_round = 1
        mock_game.state.werewolf = sample_participants["werewolf"]
        mock_game.state.participants = {
            1: [
                sample_participants["werewolf"],
                sample_participants["seer"],
                sample_participants["villager1"],
                sample_participants["villager2"]
            ]
        }
        mock_game.state.declare_winner = Mock()
        mock_game.state.initialize_next_round = Mock()
        mock_game.current_phase = Phase.NIGHT

        round_end.run()

        mock_game.state.declare_winner.assert_not_called()
        assert mock_game.state.current_round == 2
        mock_game.state.initialize_next_round.assert_called_once()
        assert mock_game.current_phase == Phase.NIGHT

    def test_round_end_increments_round_number(self, mock_game, sample_participants):
        """Test that round end increments the round number when game continues"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        initial_round = 1
        mock_game.state.current_round = initial_round
        mock_game.state.werewolf = sample_participants["werewolf"]
        mock_game.state.participants = {
            1: [
                sample_participants["werewolf"],
                sample_participants["seer"],
                sample_participants["villager1"],
                sample_participants["villager2"]
            ]
        }
        mock_game.state.initialize_next_round = Mock()
        mock_game.current_phase = Phase.NIGHT

        round_end.run()

        assert mock_game.state.current_round == initial_round + 1

    def test_round_end_logs_events(self, mock_game, sample_participants):
        """Test that round end phase logs all required events."""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.current_round = 1
        mock_game.state.werewolf = sample_participants["werewolf"]
        mock_game.state.participants = {
            1: [
                sample_participants["werewolf"],
                sample_participants["seer"],
                sample_participants["villager1"]
            ]
        }
        mock_game.log_event.reset_mock()

        round_end.run()

        assert mock_game.log_event.called
        call_args = mock_game.log_event.call_args
        assert call_args[0][0] == 1
        assert call_args[0][1].type == EventType.ROUND_END

    def test_round_end_with_no_active_players(self, mock_game):
        """Test that round end handles edge case of no active players gracefully"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.current_round = 1
        mock_game.state.participants = {1: []}
        mock_game.state.declare_winner = Mock()
        mock_game.current_phase = Phase.NIGHT

        round_end.run()

        mock_game.state.declare_winner.assert_not_called()
        assert mock_game.log_event.called


class TestWinConditionLogic:
    """Test suite for win condition checking logic."""

    def test_is_werewolf_alive_when_present(self, mock_game, sample_participants):
        """Test that is_werewolf_alive returns True when werewolf is in participants"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.werewolf = sample_participants["werewolf"]
        participants = [
            sample_participants["werewolf"],
            sample_participants["seer"],
            sample_participants["villager1"]
        ]

        result = round_end.is_werewolf_alive(participants)

        assert result is True

    def test_is_werewolf_alive_when_eliminated(self, mock_game, sample_participants):
        """Test that is_werewolf_alive returns False when werewolf is not in participants"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.werewolf = sample_participants["werewolf"]
        participants = [
            sample_participants["seer"],
            sample_participants["villager1"],
            sample_participants["villager2"]
        ]

        result = round_end.is_werewolf_alive(participants)

        assert result is False

    def test_is_werewolf_alive_when_no_werewolf(self, mock_game, sample_participants):
        """Test that is_werewolf_alive returns False when game has no werewolf"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.werewolf = None
        participants = [
            sample_participants["seer"],
            sample_participants["villager1"]
        ]

        result = round_end.is_werewolf_alive(participants)

        assert result is False

    def test_count_villagers(self, mock_game, sample_participants):
        """Test counting active villagers (including thr seer)"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        participants = [
            sample_participants["seer"],
            sample_participants["villager1"],
            sample_participants["villager2"],
            sample_participants["werewolf"]
        ]

        result = round_end.count_villagers(participants)

        assert result == 3

    def test_count_villagers_only_seer(self, mock_game, sample_participants):
        """Test counting villagers when only seer remains"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        participants = [
            sample_participants["seer"],
            sample_participants["werewolf"]
        ]

        result = round_end.count_villagers(participants)

        assert result == 1

    def test_count_villagers_empty(self, mock_game):
        """Test counting villagers when list is empty"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        participants = []

        result = round_end.count_villagers(participants)

        assert result == 0

    def test_check_werewolf_eliminated(self, mock_game, sample_participants):
        """Test checking if werewolf has been eliminated"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.current_round = 1
        mock_game.state.werewolf = sample_participants["werewolf"]
        mock_game.state.participants = {
            1: [
                sample_participants["seer"],
                sample_participants["villager1"]
            ]
        }
        mock_game.state.declare_winner = Mock()
        mock_game.current_phase = Phase.NIGHT

        round_end.check_win_conditions()

        mock_game.state.declare_winner.assert_called_once_with("villagers")
        assert mock_game.current_phase == Phase.GAME_END

    def test_check_werewolf_majority(self, mock_game, sample_participants):
        """Test checking if werewolf equals or outnumbers villagers"""
        round_end = RoundEnd(mock_game, mock_game.messenger)
        
        mock_game.state.current_round = 1
        mock_game.state.werewolf = sample_participants["werewolf"]
        mock_game.state.participants = {
            1: [
                sample_participants["werewolf"],
                sample_participants["seer"]
            ]
        }
        mock_game.state.declare_winner = Mock()
        mock_game.current_phase = Phase.NIGHT

        round_end.check_win_conditions()

        mock_game.state.declare_winner.assert_called_once_with("werewolf")
        assert mock_game.current_phase == Phase.GAME_END
