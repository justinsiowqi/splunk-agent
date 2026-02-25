import os
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

def build_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="H2O Splunk Explorer Agent",
        description="Discovers and describes the Splunk environment: lists indexes, retrieves metadata about hosts/sources/sourcetypes, checks instance info, and inspects KV Store collections. Does NOT run search queries.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="splunk_explore",
                name="Splunk Environment Discovery",
                description="Discover available indexes, metadata, instance info, and KV Store collections in the Splunk environment.",
                tags=["splunk", "mcp", "exploration", "metadata"],
                inputModes=["text/plain"],
                outputModes=["text/plain"],
            )
        ],
    )
