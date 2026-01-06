from a2a.types import (
    AgentSkill
)

hello_world_skill = AgentSkill(
    id='hello_world',
    name='Returns hello world',
    description='Just returns hello world',
    tags=['hello world'],
    examples=['hi','hello world']
)

extended_skill = AgentSkill(
    id='super_hello_world',
    name='Returns a SUPER Hello World',
    description='A more enthusiastic greeting, only for authenticated users.',
    tags=['hello world', 'super', 'extended'],
    examples=['super hi', 'give me a super hello'],
)