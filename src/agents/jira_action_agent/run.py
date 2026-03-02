from h2ogpte import H2OGPTE

from src.core.config import get_agent_config
from src.core.prompt_loader import load_prompt

jira_action_config = get_agent_config("jira_action")
prompt = load_prompt("jira_action")


def query_jira_action_agent(
    client: H2OGPTE,
    collection_id: str,
    user_prompt: str,
) -> str:
    """Create a chat session and query the Jira action agent."""
    chat_session_id = client.create_chat_session(collection_id)
    print(f"Chat session created: {chat_session_id}")

    with client.connect(chat_session_id) as session:
        reply = session.query(
            message=user_prompt,
            system_prompt=prompt,
            llm=jira_action_config["llm"],
            llm_args=dict(
                temperature=jira_action_config["temperature"],
                use_agent=True,
                agent_type=jira_action_config["agent_type"],
                agent_tools=jira_action_config["agent_tools"],
            ),
        )

    return reply.content
