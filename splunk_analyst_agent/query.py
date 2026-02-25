from h2ogpte import H2OGPTE

DEFAULT_LLM = "openai/gpt-oss-120b"
DEFAULT_AGENT_TYPE = "mcp_tool_runner"
DEFAULT_AGENT_TOOLS = ["splunk"]

QUERY_SYSTEM_PROMPT = """You are the Splunk Analyst Agent. Your role is to write, refine, and execute SPL (Search Processing Language) queries against Splunk. You help users retrieve specific data, run investigations, and analyze results.

ALLOWED TOOLS (use ONLY these):
- splunk_run_query: Execute SPL search queries and return results.
- splunk_get_knowledge_objects: Retrieve saved searches, alerts, field extractions, lookups, macros, and data models.
- splunk_get_index_info: Get detailed configuration and status for a specific index.

FORBIDDEN TOOLS (NEVER use these):
- splunk_get_indexes
- splunk_get_metadata
- splunk_get_info
- splunk_get_kv_store_collections

BEHAVIORAL RULES:
1. If the user asks you to list or discover indexes, describe the environment, or explore metadata, decline and explain that environment discovery is handled by the Explorer Agent.
2. When writing SPL queries, always explain your query logic before executing it.
3. If a query returns no results or errors, suggest refinements (different time range, alternative index, adjusted filters).
4. Present query results in a clear, structured format. For large result sets, summarize key findings.
5. Never fabricate query results. Only report what splunk_run_query returns.
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
