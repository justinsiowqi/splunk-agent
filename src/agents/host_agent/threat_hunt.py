from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.prompt_loader import load_message

if TYPE_CHECKING:
    from .routing_agent import RoutingAgent


def _find_agent_by_type(
    remote_agent_connections: dict, agent_type: str
) -> str:
    """Find a connected agent by type keyword (e.g., 'query', 'jira')."""
    for name in remote_agent_connections:
        if agent_type.lower() in name.lower():
            return name
    raise ValueError(f"No agent found matching type '{agent_type}'")


def _format_report(workflow_state: dict[str, str]) -> str:
    """Assemble the complete threat hunt results as a markdown report."""
    return (
        "# Threat Hunting Investigation Report\n\n"
        f"## Hypothesis\n"
        f"{workflow_state['hypothesis']}\n\n"
        f"## Phase 1: Discovery & Reconnaissance\n"
        f"{workflow_state.get('discovery', '')}\n\n"
        f"## Phase 2: Investigation\n"
        f"{workflow_state.get('investigation', '')}\n\n"
        f"## Phase 3: Jira Ticket\n"
        f"{workflow_state.get('ticket', '')}\n"
    )


async def execute_threat_hunt(
    routing_agent: RoutingAgent, user_message: str
) -> str:
    """Execute the three-phase threat hunting workflow.

    The user's message IS the hypothesis. No LLM generation needed.

    Args:
        routing_agent: The RoutingAgent instance (provides send_message).
        user_message: The user-provided hypothesis / investigation request.

    Returns:
        A markdown investigation report.
    """
    connections = routing_agent.remote_agent_connections
    workflow_state: dict[str, str] = {"hypothesis": user_message}

    # Phase 1: Discovery & Reconnaissance (Splunk Inventory Agent)
    print("[Threat Hunt] Phase 1: Discovery & Reconnaissance...")
    discovery_msg = load_message("inventory").format(
        hypothesis=user_message,
    )
    inventory_agent = _find_agent_by_type(connections, "inventory")
    discovery_result = await routing_agent.send_message(
        inventory_agent, discovery_msg
    )
    if discovery_result is None:
        return "Error: No response from inventory agent during discovery phase."
    workflow_state["discovery"] = discovery_result

    # Phase 2: Investigation (Splunk Query Agent)
    print("[Threat Hunt] Phase 2: Investigation...")
    investigation_msg = load_message("query").format(
        hypothesis=user_message,
        discovery_findings=workflow_state["discovery"],
    )
    query_agent = _find_agent_by_type(connections, "query")
    investigation_result = await routing_agent.send_message(
        query_agent, investigation_msg
    )
    if investigation_result is None:
        return "Error: No response from query agent during investigation phase."
    workflow_state["investigation"] = investigation_result

    # Phase 3: Ticket Creation (Jira Ticket Agent)
    print("[Threat Hunt] Phase 3: Creating Jira ticket...")
    ticket_msg = load_message("ticket").format(
        hypothesis=user_message,
        discovery_findings=workflow_state["discovery"],
        investigation_evidence=workflow_state["investigation"],
    )
    jira_agent = _find_agent_by_type(connections, "jira")
    ticket_result = await routing_agent.send_message(jira_agent, ticket_msg)
    if ticket_result is None:
        return "Error: No response from Jira agent during ticket creation phase."
    workflow_state["ticket"] = ticket_result

    return _format_report(workflow_state)
