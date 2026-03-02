# pylint: disable=logging-fstring-interpolation

import asyncio
import sys

from contextlib import asynccontextmanager
from typing import Any

import click
import uvicorn
from dotenv import load_dotenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from src.core.client import create_client
from src.core.setup import (
    create_collection,
    register_mcp_tool,
    setup_agent_keys,
    upload_and_ingest_mcp_config,
)
from .jira_agent import build_agent_card
from .jira_executor import JiraActionAgentExecutor


load_dotenv(override=True)

app_context: dict[str, Any] = {}

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8084
DEFAULT_LOG_LEVEL = "info"
COLLECTION_NAME = "Jira Action Agent"
COLLECTION_DESC = "Jira Action Agent with Jira Remote MCP Tool Capabilities"


@asynccontextmanager
async def app_lifespan(context: dict[str, Any]):
    """Manage lifecycle of shared resources like H2OGPTE client and MCP tools."""
    print("Lifespan: Initializing H2OGPTE client and Jira MCP tools...")

    try:
        client = create_client()
        collection_id = create_collection(client, COLLECTION_NAME, COLLECTION_DESC)
        upload_and_ingest_mcp_config(client, collection_id)
        register_mcp_tool(client)
        setup_agent_keys(client)

        context["client"] = client
        context["collection_id"] = collection_id

        print("Lifespan: H2OGPTE client and Jira MCP tools initialized.")
        yield
    except Exception as e:
        print(f"Lifespan: Error during initialization: {e}", file=sys.stderr)
        raise
    finally:
        print("Lifespan: Shutting down...")
        print("Lifespan: Clearing application context.")
        context.clear()


def main(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    log_level: str = DEFAULT_LOG_LEVEL,
):
    """Start the Jira Action Agent A2A server."""

    async def run_server_async():
        async with app_lifespan(app_context):
            if not app_context.get("client"):
                print(
                    "Warning: H2OGPTE client was not initialized. "
                    "Agent may not function correctly.",
                    file=sys.stderr,
                )

            jira_agent_executor = JiraActionAgentExecutor(
                client=app_context["client"],
                collection_id=app_context["collection_id"],
            )

            request_handler = DefaultRequestHandler(
                agent_executor=jira_agent_executor,
                task_store=InMemoryTaskStore(),
            )

            a2a_server = A2AStarletteApplication(
                agent_card=build_agent_card(host, port),
                http_handler=request_handler,
            )

            asgi_app = a2a_server.build()

            config = uvicorn.Config(
                app=asgi_app,
                host=host,
                port=port,
                log_level=log_level.lower(),
                lifespan="auto",
            )

            uvicorn_server = uvicorn.Server(config)

            print(
                f"Starting Jira Action Agent at http://{host}:{port} "
                f"with log-level {log_level}..."
            )
            try:
                await uvicorn_server.serve()
            except KeyboardInterrupt:
                print("Server shutdown requested (KeyboardInterrupt).")
            finally:
                print("Uvicorn server has stopped.")

    try:
        asyncio.run(run_server_async())
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            print(
                "Critical Error: Attempted to nest asyncio.run().",
                file=sys.stderr,
            )
        else:
            print(f"RuntimeError in main: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred in main: {e}", file=sys.stderr)
        sys.exit(1)


@click.command()
@click.option(
    "--host",
    "host",
    default=DEFAULT_HOST,
    help="Hostname to bind the server to.",
)
@click.option(
    "--port",
    "port",
    default=DEFAULT_PORT,
    type=int,
    help="Port to bind the server to.",
)
@click.option(
    "--log-level",
    "log_level",
    default=DEFAULT_LOG_LEVEL,
    help="Uvicorn log level.",
)
def cli(host: str, port: int, log_level: str):
    main(host, port, log_level)


if __name__ == "__main__":
    main()
