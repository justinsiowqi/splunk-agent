from .client import create_client
from .query import query_splunk_agent
from .setup import (
    create_collection,
    register_mcp_tool,
    setup_agent_keys,
    upload_and_ingest_mcp_config,
)

__all__ = [
    "create_client",
    "create_collection",
    "upload_and_ingest_mcp_config",
    "register_mcp_tool",
    "setup_agent_keys",
    "query_splunk_agent",
]
