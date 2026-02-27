import os
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

def build_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="Splunk Query Agent",
        description="SPL EXECUTION & INVESTIGATION — Writes and runs SPL queries, searches/filters event logs, counts events, and retrieves saved searches/alerts/macros. Answers 'what happened?' Requires a known index name.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="splunk_query",
                name="Splunk SPL Search & Investigation",
                description="SPL EXECUTION & INVESTIGATION — Writes and runs SPL queries, searches/filters event logs, counts events, and retrieves saved searches/alerts/macros. Answers 'what happened?' Can discover index schema when needed.",
                tags=["SPL", "search", "query", "investigation", "alerts", "saved_searches", "macros"],
                inputModes=["text/plain"],
                outputModes=["text/plain"],
            )
        ],
    )
