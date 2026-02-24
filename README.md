# H2O Splunk Agent

A Python agent that integrates [H2OGPTE](https://h2o.ai/platform/h2ogpte/) with Splunk via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), enabling natural language queries against your Splunk instance using H2O's LLM platform.

## Overview

This project sets up an H2OGPTE multi-agent pipeline that:

1. Creates a document collection and ingests an MCP server configuration
2. Registers a remote Splunk MCP tool on the H2OGPTE platform
3. Configures secure agent keys for credential management
4. Enables natural language querying of Splunk data through an LLM agent

```
User Prompt
    │
    ▼
H2OGPTE LLM Agent
    │   (mcp_tool_runner)
    ▼
Splunk MCP Server  ──►  Splunk Instance
```

## Prerequisites

- Python 3.9+
- Node.js with `npx` available in `PATH` (used by `mcp-remote`)
- An H2OGPTE instance with API access
- A running Splunk MCP server accessible over HTTPS (e.g. exposed via [ngrok](https://ngrok.com/))

## Installation

```bash
git clone https://github.com/your-org/splunk-agent.git
cd splunk-agent
pip install -r requirements.txt
```

## Configuration

### 1. Environment variables

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `H2OGPTE_API_KEY` | Your H2OGPTE API key |
| `H2OGPTE_ADDRESS` | H2OGPTE server URL (e.g. `https://your-instance.h2o.ai`) |
| `SPLUNK_MCP_TOKEN` | Bearer token for your Splunk MCP server |

### 2. MCP server config

Edit `mcp_config.json` to point to your Splunk MCP server endpoint:

```json
{
  "mcpServers": {
    "splunk": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://<your-splunk-mcp-host>/services/mcp",
        "--header",
        "Authorization: Bearer os.environ/SPLUNK_MCP_TOKEN"
      ],
      "env": {
        "SPLUNK_MCP_TOKEN": "os.environ/SPLUNK_MCP_TOKEN",
        "NODE_TLS_REJECT_UNAUTHORIZED": "0"
      },
      "tool_usage_mode": ["runner", "creator"]
    }
  }
}
```

## Usage

Run the full setup and execute a sample query:

```bash
python main.py
```

### Using the package in your own scripts

After the one-time setup, you can query the agent directly:

```python
from splunk_agent import create_client, query_splunk_agent

client = create_client()

response = query_splunk_agent(
    client=client,
    collection_id="<your-collection-id>",
    user_prompt="Show me the last 10 error events from index=main",
    system_prompt="You are a Splunk expert. Use the available Splunk tools.",
)
print(response)
```

## Project Structure

```
splunk-agent/
├── splunk_agent/
│   ├── __init__.py       # Public API exports
│   ├── client.py         # H2OGPTE client initialisation
│   ├── setup.py          # Collection, ingestion, and tool registration
│   └── query.py          # Chat session and LLM querying
├── main.py               # Entry point — runs full setup + sample query
├── mcp_config.json       # Splunk MCP server configuration
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## License

MIT
