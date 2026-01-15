import argparse
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from src.a2a.executor import GreenAgentExecutor
from src.a2a.agent_card import green_agent_card, specific_extended_agent_card


def main():
    parser = argparse.ArgumentParser(description="Run the Green Agent A2A server.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=9009, help="Port to bind the server")
    parser.add_argument("--card-url", type=str, help="URL to advertise in the agent card")
    args = parser.parse_args()

    # Update agent card URL if provided
    agent_card = green_agent_card.model_copy(
        update={"url": args.card_url} if args.card_url else {}
    )
    extended_card = specific_extended_agent_card.model_copy(
        update={"url": args.card_url} if args.card_url else {}
    )

    request_handler = DefaultRequestHandler(
        agent_executor=GreenAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
        extended_agent_card=extended_card,
    )
    uvicorn.run(server.build(), host=args.host, port=args.port)


if __name__ == '__main__':
    main()
