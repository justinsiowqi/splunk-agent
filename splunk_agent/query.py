from h2ogpte import H2OGPTE

DEFAULT_LLM = "openai/gpt-oss-120b"
DEFAULT_AGENT_TYPE = "mcp_tool_runner"
DEFAULT_AGENT_TOOLS = ["splunk"]


def query_splunk_agent(
    client: H2OGPTE,
    collection_id: str,
    user_prompt: str,
    system_prompt: str = "You are a helpful assistant with access to Splunk.",
    llm: str = DEFAULT_LLM,
    agent_type: str = DEFAULT_AGENT_TYPE,
    agent_tools: list = None,
) -> str:
    """Create a chat session and query the Splunk agent.

    Args:
        client: An authenticated H2OGPTE client.
        collection_id: The collection to associate the chat session with.
        user_prompt: The natural language question to ask.
        system_prompt: Instructions passed to the LLM as a system message.
        llm: The LLM model identifier to use.
        agent_type: The H2OGPTE agent execution mode.
        agent_tools: List of tool names available to the agent.

    Returns:
        The agent's response as a string.
    """
    if agent_tools is None:
        agent_tools = DEFAULT_AGENT_TOOLS

    chat_session_id = client.create_chat_session(collection_id)
    print(f"Chat session created: {chat_session_id}")

    with client.connect(chat_session_id) as session:
        reply = session.query(
            message=user_prompt,
            system_prompt=system_prompt,
            llm=llm,
            llm_args=dict(
                use_agent=True,
                agent_type=agent_type,
                agent_tools=agent_tools,
            ),
        )

    return reply.content
