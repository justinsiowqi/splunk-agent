from h2ogpte import H2OGPTE

from src.core.config import get_agent_config
from src.core.prompt_loader import load_prompt

jira_action_config = get_agent_config("jira_action")
prompt = load_prompt("jira_action")


def query_jira_action_agent(
    client: H2OGPTE,
    collection_id: str,
    jira_schema: str,
    user_prompt: str,
) -> str:
    """Create a chat session and query the Jira action agent."""
    system_prompt = prompt.format(jira_schema=jira_schema)

    chat_session_id = client.create_chat_session(collection_id)
    print(f"Chat session created: {chat_session_id}")

    with client.connect(chat_session_id) as session:
        reply = session.query(
            message=user_prompt,
            system_prompt=system_prompt,
            llm=jira_action_config["llm"],
            llm_args=dict(
                temperature=jira_action_config["temperature"],
                use_agent=True,
                agent_accuracy=jira_action_config["agent_accuracy"],
                agent_type=jira_action_config["agent_type"],
                agent_tools=jira_action_config["agent_tools"],
            ),
            rag_config={"rag_type": "llm_only"},
        )

    return reply.content
