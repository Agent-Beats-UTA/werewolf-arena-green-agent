from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from greenAgent.src.a2a.agent import GreenAgent

class GreenAgentExecutor(AgentExecutor):
    """Executing A2A requests"""
    
    def __init__(self):
        self.agent = GreenAgent()
        
    async def execute(self, context, event_queue):
        response = await self.agent.invoke()
        await event_queue.enqueue_event(new_agent_text_message(response))
    
    async def cancel(self, context, event_queue):
        raise Exception('cancel not supported')
    