from h2ogpte import H2OGPTE
from src.core.config import get_agent_config
from src.core.prompt_loader import load_prompt

query_config = get_agent_config("query")
prompt = load_prompt("query")


def run_splunk_agent(
    client: H2OGPTE,
    chat_id: str,
    schema_context: str,
    user_prompt: str,
) -> str:
    """Run the Splunk agent on an existing chat session.

    Args:
        client: An authenticated H2OGPTE client.
        chat_id: The persistent chat session ID.
        schema_context: Pre-built markdown schema of Splunk indexes/fields.
        user_prompt: The natural language question to ask.

    Returns:
        The agent's response as a string.
    """
    system_prompt = prompt.format(
        schema_context=schema_context
    )

    with client.connect(chat_id) as session:
        reply = session.query(
            message=user_prompt,
            system_prompt=system_prompt,
            llm=query_config["llm"],
            llm_args=dict(
                temperature=query_config["temperature"],
                enable_vision="off",
                use_agent=True,
                agent_accuracy=query_config["agent_accuracy"],
                agent_type=query_config["agent_type"],
                agent_tools=query_config["agent_tools"],
            ),
            rag_config={"rag_type": "llm_only"},
            include_chat_history="on"
        )

    return reply.content
