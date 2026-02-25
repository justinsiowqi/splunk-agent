import io
import json
import os
import time

from h2ogpte import H2OGPTE

MCP_CONFIG_PATH = "mcp_config.json"
_PLACEHOLDER = "YOUR_SPLUNK_MCP_URL"

def _load_mcp_config() -> str:
    """Read mcp_config.json and substitute the MCP URL from the environment."""
    splunk_mcp_url = os.getenv("SPLUNK_MCP_URL")
    if not splunk_mcp_url:
        raise ValueError("SPLUNK_MCP_URL must be set in .env")

    with open(MCP_CONFIG_PATH, "r") as f:
        content = f.read()

    if _PLACEHOLDER not in content:
        raise ValueError(
            f"Expected placeholder '{_PLACEHOLDER}' not found in {MCP_CONFIG_PATH}"
        )

    return content.replace(_PLACEHOLDER, splunk_mcp_url)


def create_collection(client: H2OGPTE) -> str:
    """Create a new H2OGPTE collection for the Splunk agent."""
    collection_id = client.create_collection(
        name="Splunk Explorer Agent",
        description="Splunk Explorer Agent with Splunk Remote MCP Tool Capabilities",
    )
    print(f"Collection created: {collection_id}")
    return collection_id


def upload_and_ingest_mcp_config(client: H2OGPTE, collection_id: str) -> str:
    """Upload and ingest the MCP config file into the collection."""
    json_bytes = _load_mcp_config().encode()
    upload_id = client.upload(MCP_CONFIG_PATH, io.BytesIO(json_bytes))

    ingest_job = client.ingest_uploads(
        collection_id=collection_id,
        upload_ids=[upload_id],
        ingest_mode="agent_only",
    )

    print("Waiting for ingestion...")
    while True:
        job_status = client.get_job(ingest_job.id)
        if job_status.completed:
            print("Ingestion complete.")
            break
        if job_status.failed:
            raise RuntimeError(f"Ingestion failed: {job_status.errors}")
        time.sleep(2)

    return upload_id


def register_mcp_tool(client: H2OGPTE) -> list:
    """Register the Splunk MCP tool with H2OGPTE."""
    json_str = _load_mcp_config()

    tool_ids = client.add_custom_agent_tool(
        tool_type="remote_mcp",
        tool_args={
            "mcp_config_json": json_str,
            "enable_by_default": False,
        },
        custom_tool_path=MCP_CONFIG_PATH,
    )
    print(f"MCP tool registered: {tool_ids}")
    return tool_ids


def setup_agent_keys(client: H2OGPTE) -> None:
    """Ensure agent keys for MCP env vars exist, reusing or creating as needed."""
    required_keys = {
        "H2OGPTE_API_KEY": os.getenv("H2OGPTE_API_KEY"),
        "H2OGPTE_ADDRESS": os.getenv("H2OGPTE_ADDRESS"),
        "SPLUNK_MCP_TOKEN": os.getenv("SPLUNK_MCP_TOKEN"),
    }

    existing = {
        k["name"]: k["id"]
        for k in client.get_agent_keys()
        if k["name"] in required_keys
    }

    for name, value in required_keys.items():
        if name not in existing:
            result = client.add_agent_key([
                {
                    "name": name,
                    "value": value,
                    "key_type": "private",
                    "description": f"{name} for MCP server",
                }
            ])
            existing[name] = result[0]["agent_key_id"]
            print(f"  Created agent key: {name}")
        else:
            print(f"  Reusing agent key: {name}")

    client.assign_agent_key_for_tool([{
        "tool_dict": {
            "tool": MCP_CONFIG_PATH,
            "keys": [{"name": name, "key_id": kid} for name, kid in existing.items()],
        }
    }])
    print("Agent keys associated with MCP tool.")
