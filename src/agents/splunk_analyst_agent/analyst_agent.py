import os
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

def build_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="H2O Splunk Analyst Agent",
        description="Writes, refines, and executes SPL search queries against Splunk. Retrieves knowledge objects such as saved searches, alerts, and macros. Gets detailed index configuration. Does NOT discover or list indexes.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="splunk_query",
                name="Splunk Query Execution",
                description="Write and execute SPL queries against Splunk, retrieve knowledge objects, and get detailed index configuration.",
                tags=["splunk", "mcp", "query", "spl", "analysis"],
                inputModes=["text/plain"],
                outputModes=["text/plain"],
            )
        ],
    )
