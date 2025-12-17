from a2a.types import AgentCard, AgentCapabilities
from lib.skills import hello_world_skill, extended_skill

green_agent_card = AgentCard(
    id='green_agent',
    name='Returns Hello World',
    description='Evaluates agents',
    url='http://localhost:9999',
    skills=[hello_world_skill],
    version='1.0.0',
    default_input_modes=['text'],
    default_output_modes=['text'],
    capabilities=AgentCapabilities(streaming=True),
    supports_authenticated_extended_card=True
)

specific_extended_agent_card = green_agent_card.model_copy(
    update={
        'name': 'Hello World Agent - Extended Edition',  # Different name for clarity
        'description': 'The full-featured hello world agent for authenticated users.',
        'version': '1.0.1',  # Could even be a different version
        # Capabilities and other fields like url, default_input_modes, default_output_modes,
        # supports_authenticated_extended_card are inherited from public_agent_card unless specified here.
        'skills': [
            hello_world_skill,
            extended_skill,
        ],  # Both skills for the extended card
    }
)