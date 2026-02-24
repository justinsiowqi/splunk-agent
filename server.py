import os
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from splunk_agent import (create_client, create_collection,
    upload_and_ingest_mcp_config, register_mcp_tool, setup_agent_keys)
from splunk_agent.agent_executor import SplunkAgentExecutor
from splunk_agent.agent import build_agent_card

def main():
    client = create_client()
    collection_id = create_collection(client)
    upload_and_ingest_mcp_config(client, collection_id)
    register_mcp_tool(client)
    setup_agent_keys(client)

    host = os.getenv("A2A_HOST", "localhost")
    port = int(os.getenv("A2A_PORT", "8080"))

    app = A2AStarletteApplication(
        agent_card=build_agent_card(host, port),
        http_handler=DefaultRequestHandler(
            agent_executor=SplunkAgentExecutor(client, collection_id),
            task_store=InMemoryTaskStore(),
        ),
    )
    uvicorn.run(app.build(), host=host, port=port)

if __name__ == "__main__":
    main()
