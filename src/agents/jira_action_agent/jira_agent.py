from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="Jira Action Agent",
        description=(
            "Creates and updates Jira issues based on validated findings from "
            "discovery and analyst outputs."
        ),
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="jira_actions",
                name="Jira Ticket Actions",
                description=(
                    "Create, update, transition, and comment on Jira issues from "
                    "structured findings."
                ),
                tags=["jira", "mcp", "ticketing", "incident-response"],
                inputModes=["text/plain"],
                outputModes=["text/plain"],
            )
        ],
    )
