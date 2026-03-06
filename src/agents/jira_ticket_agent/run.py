from h2ogpte import H2OGPTE

from src.core.config import get_agent_config
from src.core.prompt_loader import load_prompt

jira_ticket_config = get_agent_config("ticket")
prompt = load_prompt("ticket")


def query_jira_ticket_agent(
    client: H2OGPTE,
    collection_id: str,
    jira_schema: str,
    user_prompt: str,
) -> str:
    """Create a chat session and query the Jira ticket agent."""
    system_prompt = prompt.format(jira_schema=jira_schema)

    chat_session_id = client.create_chat_session(collection_id)
    print(f"Chat session created: {chat_session_id}")

    with client.connect(chat_session_id) as session:
        reply = session.query(
            message=user_prompt,
            system_prompt=system_prompt,
            llm=jira_ticket_config["llm"],
            llm_args=dict(
                temperature=jira_ticket_config["temperature"],
                use_agent=True,
                agent_accuracy=jira_ticket_config["agent_accuracy"],
                agent_max_turns=jira_ticket_config["agent_max_turns"],
                agent_type=jira_ticket_config["agent_type"],
                agent_timeout=jira_ticket_config["agent_timeout"],
                agent_total_timeout=jira_ticket_config["agent_total_timeout"],
                agent_tools=jira_ticket_config["agent_tools"],
            ),
            rag_config={"rag_type": "llm_only"},
        )

    return reply.content
