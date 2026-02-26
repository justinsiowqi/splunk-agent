from h2ogpte import H2OGPTE
from src.core.config import get_agent_config
from src.core.prompt_loader import load_prompt

query_config = get_agent_config("query")
prompt = load_prompt("query")


def run_splunk_agent(
    client: H2OGPTE,
    collection_id: str,
    user_prompt: str,
) -> str:
    """Create a chat session and run the Splunk agent.

    Args:
        client: An authenticated H2OGPTE client.
        collection_id: The collection to associate the chat session with.
        user_prompt: The natural language question to ask.

    Returns:
        The agent's response as a string.
    """

    chat_session_id = client.create_chat_session(collection_id)
    print(f"Chat session created: {chat_session_id}")

    with client.connect(chat_session_id) as session:
        reply = session.query(
            message=user_prompt,
            system_prompt=prompt,
            llm=query_config["llm"],
            llm_args=dict(
                temperature=query_config["temperature"],
                use_agent=True,
                agent_type=query_config["agent_type"],
                agent_tools=query_config["agent_tools"],
            ),
        )

    return reply.content
