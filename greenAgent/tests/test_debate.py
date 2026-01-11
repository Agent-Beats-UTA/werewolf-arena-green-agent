import pytest
from unittest.mock import Mock, AsyncMock
import json

from src.phases.debate import Debate
from src.models.Message import Message
from src.models.enum.Role import Role


class TestDebatePhase:
    """Test suite for the Debate phase."""

    @pytest.mark.asyncio
    async def test_debate_phase_initialization(self, mock_game, mock_messenger):
        """Test that debate phase initializes correctly."""
        debate = Debate(mock_game, mock_messenger)

        assert debate.game == mock_game
        assert debate.messenger == mock_messenger

    @pytest.mark.asyncio
    async def test_debate_phase_run(self, mock_game, mock_messenger, debate_message_response, sample_participants):
        """Test that debate phase executes complete flow."""
        # Setup
        debate = Debate(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = debate_message_response

        mock_game.state.current_round = 1
        mock_game.state.turns_to_speak_per_round = 1
        participant_list = list(sample_participants.values())
        mock_game.state.participants = {1: participant_list}
        mock_game.state.speaking_order = {1: [p.id for p in participant_list]}
        mock_game.state.chat_history = {}
        mock_game.get_night_elimination_message.return_value = "Player X was eliminated"

        # Execute
        await debate.run()

        # Verify all participants spoke
        assert mock_messenger.talk_to_agent.call_count == len(sample_participants)

    @pytest.mark.asyncio
    async def test_debate_follows_speaking_order(self, mock_game, mock_messenger, debate_message_response, sample_participants):
        """Test that debate follows the established speaking order from bidding."""
        # Setup
        debate = Debate(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = debate_message_response

        mock_game.state.current_round = 1
        mock_game.state.turns_to_speak_per_round = 1
        participant_list = list(sample_participants.values())
        mock_game.state.participants = {1: participant_list}

        # Set specific speaking order
        custom_order = ["seer_1", "werewolf_1", "villager_1", "villager_2", "villager_3"]
        mock_game.state.speaking_order = {1: custom_order}
        mock_game.state.chat_history = {}
        mock_game.get_night_elimination_message.return_value = "Player X was eliminated"

        # Execute
        await debate.run()

        # Verify participants were called in correct order
        call_urls = [call.kwargs['url'] for call in mock_messenger.talk_to_agent.call_args_list]
        expected_urls = [sample_participants[key].url for key in ["seer", "werewolf", "villager1", "villager2", "villager3"]]
        assert call_urls == expected_urls

    @pytest.mark.asyncio
    async def test_debate_respects_turn_limits(self, mock_game, mock_messenger, debate_message_response, sample_participants):
        """Test that debate respects the turns_to_speak_per_round limit."""
        # Setup
        debate = Debate(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = debate_message_response

        mock_game.state.current_round = 1
        mock_game.state.turns_to_speak_per_round = 2  # Each player speaks twice
        participant_list = list(sample_participants.values())
        mock_game.state.participants = {1: participant_list}
        mock_game.state.speaking_order = {1: [p.id for p in participant_list]}
        mock_game.state.chat_history = {}
        mock_game.get_night_elimination_message.return_value = "Player X was eliminated"

        # Execute
        await debate.run()

        # Verify each participant spoke twice (2 turns * 5 participants = 10 calls)
        assert mock_messenger.talk_to_agent.call_count == len(sample_participants) * 2

    @pytest.mark.asyncio
    async def test_debate_stores_chat_history(self, mock_game, mock_messenger, debate_message_response, sample_participants):
        """Test that debate stores all messages in chat history."""
        # Setup
        debate = Debate(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = debate_message_response

        mock_game.state.current_round = 1
        mock_game.state.turns_to_speak_per_round = 1
        participant_list = list(sample_participants.values())
        mock_game.state.participants = {1: participant_list}
        mock_game.state.speaking_order = {1: [p.id for p in participant_list]}
        mock_game.state.chat_history = {}
        mock_game.get_night_elimination_message.return_value = "Player X was eliminated"

        # Execute
        await debate.run()

        # Verify chat history was created and populated
        assert 1 in mock_game.state.chat_history
        assert len(mock_game.state.chat_history[1]) == len(sample_participants)

        # Verify messages have correct structure
        for msg in mock_game.state.chat_history[1]:
            assert isinstance(msg, Message)
            assert msg.sender_id in [p.id for p in participant_list]

    @pytest.mark.asyncio
    async def test_debate_prompt_includes_role(self, mock_game, mock_messenger, debate_message_response, sample_participants):
        """Test that debate prompt includes player's role."""
        # Setup
        debate = Debate(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = debate_message_response

        mock_game.state.current_round = 1
        mock_game.state.turns_to_speak_per_round = 1
        mock_game.state.participants = {1: [sample_participants["werewolf"]]}
        mock_game.state.speaking_order = {1: ["werewolf_1"]}
        mock_game.state.chat_history = {}
        mock_game.get_night_elimination_message.return_value = "Player X was eliminated"

        # Execute
        await debate.run()

        # Verify role was included in the prompt
        call_args = mock_messenger.talk_to_agent.call_args
        assert "WEREWOLF" in call_args.kwargs['message']

    @pytest.mark.asyncio
    async def test_debate_prompt_includes_chat_history(self, mock_game, mock_messenger, debate_message_response, sample_participants):
        """Test that debate prompt includes previous messages."""
        # Setup
        debate = Debate(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = debate_message_response

        existing_messages = [
            Message(sender_id="villager_1", content="I think player X is suspicious"),
            Message(sender_id="werewolf_1", content="I agree with villager_1")
        ]

        mock_game.state.current_round = 1
        mock_game.state.turns_to_speak_per_round = 1
        mock_game.state.participants = {1: [sample_participants["seer"]]}
        mock_game.state.speaking_order = {1: ["seer_1"]}
        mock_game.state.chat_history = {1: existing_messages}
        mock_game.get_night_elimination_message.return_value = "Player X was eliminated"

        # Execute
        await debate.run()

        # Verify chat history was included in the prompt
        call_args = mock_messenger.talk_to_agent.call_args
        assert "villager_1" in call_args.kwargs['message']
        assert "I think player X is suspicious" in call_args.kwargs['message']
        assert "werewolf_1" in call_args.kwargs['message']

    @pytest.mark.asyncio
    async def test_debate_prompt_includes_night_elimination(self, mock_game, mock_messenger, debate_message_response, sample_participants):
        """Test that debate prompt includes night elimination information."""
        # Setup
        debate = Debate(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = debate_message_response

        mock_game.state.current_round = 1
        mock_game.state.turns_to_speak_per_round = 1
        mock_game.state.participants = {1: [sample_participants["villager1"]]}
        mock_game.state.speaking_order = {1: ["villager_1"]}
        mock_game.state.chat_history = {}
        mock_game.get_night_elimination_message.return_value = "Villager_2 was eliminated by the werewolf"

        # Execute
        await debate.run()

        # Verify night elimination was included in the prompt
        call_args = mock_messenger.talk_to_agent.call_args
        assert "Villager_2 was eliminated by the werewolf" in call_args.kwargs['message']

    @pytest.mark.asyncio
    async def test_debate_prompt_includes_speaking_order(self, mock_game, mock_messenger, debate_message_response, sample_participants):
        """Test that debate prompt includes the speaking order."""
        # Setup
        debate = Debate(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = debate_message_response

        mock_game.state.current_round = 1
        mock_game.state.turns_to_speak_per_round = 1
        participant_list = list(sample_participants.values())
        mock_game.state.participants = {1: participant_list}
        mock_game.state.speaking_order = {1: [p.id for p in participant_list]}
        mock_game.state.chat_history = {}
        mock_game.get_night_elimination_message.return_value = "Player X was eliminated"

        # Execute
        await debate.run()

        # Verify speaking order was included in prompt
        call_args = mock_messenger.talk_to_agent.call_args
        for participant_id in [p.id for p in participant_list]:
            assert participant_id in call_args.kwargs['message']

    def test_debate_prompt_format(self, mock_game, mock_messenger):
        """Test that debate prompt is properly formatted."""
        # Setup
        debate = Debate(mock_game, mock_messenger)

        chat_history = [
            Message(sender_id="player_1", content="Message 1"),
            Message(sender_id="player_2", content="Message 2")
        ]
        speaking_order = ["player_1", "player_2", "player_3"]
        night_elimination = "Player X was killed"

        prompt = debate.get_debate_prompt(
            user_role=Role.SEER,
            chat_history=chat_history,
            speaking_order=speaking_order,
            night_elimination_message=night_elimination
        )

        # Verify prompt structure
        assert "Debate phase" in prompt
        assert "SEER" in prompt
        assert "player_1: Message 1" in prompt
        assert "player_2: Message 2" in prompt
        assert "player_1, player_2, player_3" in prompt
        assert "Player X was killed" in prompt
        assert "message" in prompt

    @pytest.mark.asyncio
    async def test_parse_json_response_valid_message(self, mock_game, mock_messenger):
        """Test parsing a valid debate message JSON response."""
        debate = Debate(mock_game, mock_messenger)
        valid_json = '{"message": "I believe we should vote for player X"}'

        result = debate._parse_json_response(valid_json)

        assert result['message'] == 'I believe we should vote for player X'

    @pytest.mark.asyncio
    async def test_parse_json_response_with_markdown(self, mock_game, mock_messenger):
        """Test parsing debate message JSON wrapped in markdown code blocks."""
        debate = Debate(mock_game, mock_messenger)
        markdown_json = '''```json
{
    "message": "Based on the evidence, I suspect player Y"
}
```'''

        result = debate._parse_json_response(markdown_json)

        assert result['message'] == 'Based on the evidence, I suspect player Y'

    @pytest.mark.asyncio
    async def test_debate_with_empty_chat_history(self, mock_game, mock_messenger, debate_message_response, sample_participants):
        """Test that debate works correctly on first turn with empty chat history."""
        # Setup
        debate = Debate(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = debate_message_response

        mock_game.state.current_round = 1
        mock_game.state.turns_to_speak_per_round = 1
        mock_game.state.participants = {1: [sample_participants["villager1"]]}
        mock_game.state.speaking_order = {1: ["villager_1"]}
        mock_game.state.chat_history = {}  # Empty chat history
        mock_game.get_night_elimination_message.return_value = "Player X was eliminated"

        # Execute - should not raise errors
        await debate.run()

        # Verify message was sent and stored
        assert mock_messenger.talk_to_agent.call_count == 1
        assert len(mock_game.state.chat_history[1]) == 1

    @pytest.mark.asyncio
    async def test_debate_messages_accumulate_across_turns(self, mock_game, mock_messenger, sample_participants):
        """Test that messages accumulate in chat history across multiple turns."""
        # Setup
        debate = Debate(mock_game, mock_messenger)

        # Return different messages for each call
        mock_messenger.talk_to_agent.side_effect = [
            '{"message": "Turn 1 message"}',
            '{"message": "Turn 2 message"}',
            '{"message": "Turn 3 message"}'
        ]

        mock_game.state.current_round = 1
        mock_game.state.turns_to_speak_per_round = 3
        mock_game.state.participants = {1: [sample_participants["villager1"]]}
        mock_game.state.speaking_order = {1: ["villager_1"]}
        mock_game.state.chat_history = {}
        mock_game.get_night_elimination_message.return_value = "Player X was eliminated"

        # Execute
        await debate.run()

        # Verify all 3 messages are in chat history
        assert len(mock_game.state.chat_history[1]) == 3
        assert mock_game.state.chat_history[1][0].content == "Turn 1 message"
        assert mock_game.state.chat_history[1][1].content == "Turn 2 message"
        assert mock_game.state.chat_history[1][2].content == "Turn 3 message"

    @pytest.mark.asyncio
    async def test_debate_later_speakers_see_earlier_messages(self, mock_game, mock_messenger, sample_participants):
        """Test that later speakers in the order see messages from earlier speakers."""
        # Setup
        debate = Debate(mock_game, mock_messenger)
        mock_messenger.talk_to_agent.return_value = '{"message": "My response"}'

        mock_game.state.current_round = 1
        mock_game.state.turns_to_speak_per_round = 1
        mock_game.state.participants = {1: [sample_participants["villager1"], sample_participants["villager2"]]}
        mock_game.state.speaking_order = {1: ["villager_1", "villager_2"]}
        mock_game.state.chat_history = {}
        mock_game.get_night_elimination_message.return_value = "Player X was eliminated"

        # Execute
        await debate.run()

        # Check that second speaker's prompt included first speaker's message
        second_call = mock_messenger.talk_to_agent.call_args_list[1]
        assert "villager_1" in second_call.kwargs['message']
        assert "My response" in second_call.kwargs['message']
