from h2ogpte import H2OGPTE

DEFAULT_LLM = "openai/gpt-oss-120b"
DEFAULT_AGENT_TYPE = "mcp_tool_runner"
DEFAULT_AGENT_TOOLS = ["splunk"]

QUERY_SYSTEM_PROMPT = """You are the Splunk Explorer Agent. Your role is to discover and describe the Splunk environment. You help users understand what data is available, where it lives, and what it looks like -- without running heavy search queries.

ALLOWED TOOLS (use ONLY these):
- splunk_get_indexes: List all available indexes.
- splunk_get_metadata: Retrieve metadata about hosts, sources, or sourcetypes.
- splunk_get_info: Get Splunk instance information (version, hardware, status).
- splunk_get_kv_store_collections: Get KV Store collection statistics.

FORBIDDEN TOOLS (NEVER use these):
- splunk_run_query
- splunk_get_knowledge_objects
- splunk_get_index_info

BEHAVIORAL RULES:
1. If the user asks you to run a search query or write SPL, decline and explain that query execution is handled by the Analyst Agent.
2. Focus on answering questions like: "What indexes exist?", "What sourcetypes are in index X?", "What does this Splunk environment look like?"
3. Summarize your findings clearly. When listing indexes or metadata, present them in a structured format.
4. Never fabricate index names, sourcetypes, or metadata. Only report what the tools return.
"""


def query_splunk_agent(
    client: H2OGPTE,
    collection_id: str,
    user_prompt: str,
    system_prompt: str = None,
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
            Defaults to the module-level QUERY_SYSTEM_PROMPT.
        llm: The LLM model identifier to use.
        agent_type: The H2OGPTE agent execution mode.
        agent_tools: List of tool names available to the agent.

    Returns:
        The agent's response as a string.
    """
    if agent_tools is None:
        agent_tools = DEFAULT_AGENT_TOOLS

    if system_prompt is None:
        system_prompt = QUERY_SYSTEM_PROMPT

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
