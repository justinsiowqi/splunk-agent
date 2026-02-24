from splunk_agent import (
    create_client,
    create_collection,
    query_splunk_agent,
    register_mcp_tool,
    setup_agent_keys,
    upload_and_ingest_mcp_config,
)


def main() -> None:
    # 1. Initialise client
    client = create_client()

    # 2. Create collection and ingest MCP config
    collection_id = create_collection(client)
    upload_and_ingest_mcp_config(client, collection_id)

    # 3. Register remote MCP tool and configure secure agent keys
    register_mcp_tool(client)
    setup_agent_keys(client)

    # 4. Run a sample query against the Splunk agent
    response = query_splunk_agent(
        client=client,
        collection_id=collection_id,
        user_prompt="Tell me the Splunk version.",
        system_prompt="Use the splunk_get_info tool.",
    )

    print("\n--- Agent Response ---")
    print(response)


if __name__ == "__main__":
    main()
