import pytest
from unittest.mock import Mock, AsyncMock
import json

from src.phases.bidding import Bidding
from src.models.Bid import Bid
from src.models.enum.EventType import EventType
from src.models.enum.Role import Role


class TestBiddingPhase:
    """Test suite for the Bidding phase."""

    @pytest.mark.asyncio
    async def test_bidding_phase_initialization(self, mock_game, mock_messenger):
        """Test that bidding phase initializes correctly."""
        bidding = Bidding(mock_game, mock_messenger)

        assert bidding.game == mock_game
        assert bidding.messenger == mock_messenger

    @pytest.mark.asyncio
    async def test_bidding_phase_complete_flow(self, mock_game, mock_messenger, bid_response, sample_participants):
        """Test that bidding phase executes complete flow: collect bids and set speaking order."""
        # Setup
        bidding = Bidding(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = bid_response

        mock_game.state.current_round = 1
        mock_game.state.participants = {1: list(sample_participants.values())}
        mock_game.state.bids = {}

        # Execute
        await bidding.run()

        # Verify bids were collected from all participants
        assert mock_messenger.talk_to_agent.call_count == len(sample_participants)

        # Verify speaking order was set
        assert 1 in mock_game.state.speaking_order

    @pytest.mark.asyncio
    async def test_collect_round_bids(self, mock_game, mock_messenger, bid_response, sample_participants):
        """Test that bids are collected from all active participants."""
        # Setup
        bidding = Bidding(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = bid_response

        mock_game.state.current_round = 1
        mock_game.state.participants = {1: list(sample_participants.values())}
        mock_game.state.bids = {}

        # Execute
        await bidding.collect_round_bids()

        # Verify all participants were asked to bid
        assert mock_messenger.talk_to_agent.call_count == len(sample_participants)

        # Verify bids were stored
        assert 1 in mock_game.state.bids
        assert len(mock_game.state.bids[1]) == len(sample_participants)

        # Verify each bid has correct structure
        for bid in mock_game.state.bids[1]:
            assert isinstance(bid, Bid)
            assert bid.participant_id in [p.id for p in sample_participants.values()]
            assert bid.amount == 50  # From fixture

        # Verify events were logged
        assert mock_game.log_event.call_count == len(sample_participants)

    @pytest.mark.asyncio
    async def test_tally_bids_and_set_order(self, mock_game, mock_messenger):
        """Test that bids are tallied and speaking order is set correctly."""
        # Setup
        bidding = Bidding(mock_game, mock_messenger)
        mock_game.state.current_round = 1

        # Create bids with different amounts
        mock_game.state.bids = {1: [
            Bid(participant_id="villager_1", amount=30),
            Bid(participant_id="werewolf_1", amount=80),
            Bid(participant_id="seer_1", amount=50),
            Bid(participant_id="villager_2", amount=60),
            Bid(participant_id="villager_3", amount=20)
        ]}

        # Execute
        await bidding.tally_bids_and_set_order()

        # Verify speaking order is set correctly (highest bid first)
        expected_order = ["werewolf_1", "villager_2", "seer_1", "villager_1", "villager_3"]
        assert mock_game.state.speaking_order[1] == expected_order

        # Verify event was logged
        assert mock_game.log_event.called

    @pytest.mark.asyncio
    async def test_bidding_with_tie_bids(self, mock_game, mock_messenger):
        """Test that tied bids maintain stable ordering."""
        # Setup
        bidding = Bidding(mock_game, mock_messenger)
        mock_game.state.current_round = 1

        # Create bids with ties
        mock_game.state.bids = {1: [
            Bid(participant_id="villager_1", amount=50),
            Bid(participant_id="werewolf_1", amount=50),
            Bid(participant_id="seer_1", amount=50)
        ]}

        # Execute
        await bidding.tally_bids_and_set_order()

        # Verify speaking order exists and has all participants
        assert 1 in mock_game.state.speaking_order
        assert len(mock_game.state.speaking_order[1]) == 3
        assert set(mock_game.state.speaking_order[1]) == {"villager_1", "werewolf_1", "seer_1"}

    @pytest.mark.asyncio
    async def test_bidding_prompt_format(self, mock_game, mock_messenger):
        """Test that bidding prompt is properly formatted."""
        # Setup
        bidding = Bidding(mock_game, mock_messenger)
        existing_bids = [
            Bid(participant_id="player_1", amount=30),
            Bid(participant_id="player_2", amount=50)
        ]

        prompt = bidding.get_bid_prompt(user_role=Role.VILLAGER, bids=existing_bids)

        # Verify prompt structure
        assert "bid for speaking order" in prompt
        assert "VILLAGER" in prompt
        assert "0 and 100" in prompt
        assert "player_1" in prompt
        assert "30 points" in prompt
        assert "player_2" in prompt
        assert "50 points" in prompt
        assert "bid_amount" in prompt
        assert "reason" in prompt

    @pytest.mark.asyncio
    async def test_bidding_logs_events(self, mock_game, mock_messenger, bid_response, sample_participants):
        """Test that bidding phase logs all required events."""
        # Setup
        bidding = Bidding(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = bid_response

        mock_game.state.current_round = 1
        mock_game.state.participants = {1: list(sample_participants.values())}
        mock_game.state.bids = {}

        # Execute
        await bidding.collect_round_bids()

        # Verify events were logged for each bid
        logged_events = [call.args[0] for call in mock_game.log_event.call_args_list]
        bid_events = [e for e in logged_events if e.type == EventType.BID_PLACED]

        assert len(bid_events) == len(sample_participants)

    @pytest.mark.asyncio
    async def test_parse_json_response_valid_bid(self, mock_game, mock_messenger):
        """Test parsing a valid bid JSON response."""
        bidding = Bidding(mock_game, mock_messenger)
        valid_json = '{"bid_amount": 75, "reason": "I need to speak first"}'

        result = bidding._parse_json_response(valid_json)

        assert result['bid_amount'] == 75
        assert result['reason'] == 'I need to speak first'

    @pytest.mark.asyncio
    async def test_parse_json_response_with_markdown(self, mock_game, mock_messenger):
        """Test parsing bid JSON wrapped in markdown code blocks."""
        bidding = Bidding(mock_game, mock_messenger)
        markdown_json = '''```json
{
    "bid_amount": 90,
    "reason": "Strategic positioning"
}
```'''

        result = bidding._parse_json_response(markdown_json)

        assert result['bid_amount'] == 90
        assert result['reason'] == 'Strategic positioning'

    @pytest.mark.asyncio
    async def test_bidding_with_zero_bid(self, mock_game, mock_messenger):
        """Test that zero bids are handled correctly (speak last)."""
        # Setup
        bidding = Bidding(mock_game, mock_messenger)
        mock_game.state.current_round = 1

        # Create bids including zero
        mock_game.state.bids = {1: [
            Bid(participant_id="villager_1", amount=30),
            Bid(participant_id="werewolf_1", amount=0),
            Bid(participant_id="seer_1", amount=50)
        ]}

        # Execute
        await bidding.tally_bids_and_set_order()

        # Verify zero bid is last in speaking order
        assert mock_game.state.speaking_order[1][-1] == "werewolf_1"
        assert mock_game.state.speaking_order[1][0] == "seer_1"

    @pytest.mark.asyncio
    async def test_bidding_with_max_bid(self, mock_game, mock_messenger):
        """Test that maximum bid (100) is handled correctly."""
        # Setup
        bidding = Bidding(mock_game, mock_messenger)
        mock_game.state.current_round = 1

        # Create bids including max
        mock_game.state.bids = {1: [
            Bid(participant_id="villager_1", amount=30),
            Bid(participant_id="werewolf_1", amount=100),
            Bid(participant_id="seer_1", amount=50)
        ]}

        # Execute
        await bidding.tally_bids_and_set_order()

        # Verify max bid is first in speaking order
        assert mock_game.state.speaking_order[1][0] == "werewolf_1"

    @pytest.mark.asyncio
    async def test_bidding_includes_role_in_prompt(self, mock_game, mock_messenger, sample_participants):
        """Test that bid prompt includes player's role information."""
        # Setup
        bidding = Bidding(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = '{"bid_amount": 50, "reason": "test"}'

        mock_game.state.current_round = 1
        mock_game.state.participants = {1: [sample_participants["werewolf"]]}
        mock_game.state.bids = {}

        # Execute
        await bidding.collect_round_bids()

        # Verify role was included in the prompt
        call_args = mock_messenger.talk_to_agent.call_args
        assert "WEREWOLF" in call_args.kwargs['message']

    @pytest.mark.asyncio
    async def test_bidding_shows_current_bids_in_prompt(self, mock_game, mock_messenger, sample_participants):
        """Test that bid prompt shows current bids from other players."""
        # Setup
        bidding = Bidding(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = '{"bid_amount": 50, "reason": "test"}'

        mock_game.state.current_round = 1
        mock_game.state.participants = {1: [sample_participants["villager1"], sample_participants["villager2"]]}
        mock_game.state.bids = {1: [Bid(participant_id="villager_1", amount=40)]}

        # Execute - second player should see first player's bid
        await bidding.collect_round_bids()

        # Check that second call included the first bid in prompt
        second_call = mock_messenger.talk_to_agent.call_args_list[1]
        assert "villager_1" in second_call.kwargs['message']
        assert "40 points" in second_call.kwargs['message']
