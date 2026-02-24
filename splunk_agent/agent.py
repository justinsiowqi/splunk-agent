import os
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

def build_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="H2O Splunk Agent",
        description="Answers natural language questions about a Splunk instance via H2OGPTE and MCP.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="splunk_query",
                name="Splunk Query",
                description="Execute a natural language query against Splunk.",
                tags=["splunk", "mcp"],
                inputModes=["text/plain"],
                outputModes=["text/plain"],
            )
        ],
    )
