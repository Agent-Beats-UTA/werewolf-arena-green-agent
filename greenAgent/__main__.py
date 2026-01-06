import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from greenAgent.src.a2a.executor import GreenAgentExecutor
from greenAgent.src.a2a.agent_card import green_agent_card, specific_extended_agent_card

if __name__ == '__main__':
    request_handler = DefaultRequestHandler(
        agent_executor=GreenAgentExecutor(),
        task_store=InMemoryTaskStore()
    )
    
    server = A2AStarletteApplication(
        agent_card=green_agent_card,
        http_handler=request_handler,
        extended_agent_card=specific_extended_agent_card
    )
    
    uvicorn.run(server.build(), host='0.0.0.0', port=9999)