import os
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

def build_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="Splunk Inventory Agent",
        description="ENVIRONMENT INVENTORY — Enumerates what exists in Splunk: index names, sourcetypes, hosts, instance version/status, and KV Store collections. Answers 'what do we have?' CANNOT search logs, run SPL, or read event data.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="splunk_inventory",
                name="Splunk Environment Inventory",
                description="List and describe Splunk infrastructure: index names, sourcetypes, hosts, instance version/status, and KV Store collections. Read-only; no SPL execution.",
                tags=["inventory", "list_indexes", "list_sourcetypes", "instance_info", "kv_store"],
                inputModes=["text/plain"],
                outputModes=["text/plain"],
            )
        ],
    )
