# Splunk Multi-Agent System

A multi-agent system that integrates [H2OGPTE](https://h2o.ai/platform/h2ogpte/) with Splunk and Jira via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) and the [Agent-to-Agent (A2A)](https://github.com/google/A2A) protocol. Users can query Splunk data and create Jira tickets using natural language through a Gradio UI, with requests routed to specialized agents.

## Architecture

```
YOUR MACHINE
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  User (Gradio UI)                              port 8083        │
│       │                                                         │
│       ▼                                                         │
│  Routing Agent (host_agent/)                                    │
│       │ H2OGPTE LLM decides which agent(s) to invoke            │
│       │                                                         │
│       ├──── A2A ────► Inventory Agent          port 8080        │
│       │                (discovery & metadata)                   │
│       │                                                         │
│       ├──── A2A ────► Query Agent              port 8082        │
│       │                (SPL query execution)                    │
│       │                                                         │
│       └──── A2A ────► Jira Ticket Agent        port 8084        │
│                        (ticket actions)                         │
│                                                                 │
│  Workflows:                                                     │
│    Single agent  ─  Route directly to one agent                 │
│    Jira          ─  Upstream agent → Jira (grounded in findings)│
│    Threat hunt   ─  Inventory → Query → Jira (3-phase)          │
│                                                                 │
│  Splunk Web UI                                 port 8000        │
│  Splunk MCP Server                             port 8089        │
│  Atlassian MCP Server                          port 9000        │
│       ▲                                                         │
│       │ cloudflared tunnels these ports                         │
└───────┼─────────────────────────────────────────────────────────┘
        │
        │ public HTTPS (trycloudflare.com)
        ▼
   Cloudflare URLs  ──►  H2OGPTE (cloud)  ──►  MCP Tool Runner
```

**Inventory Agent** — Discovers the Splunk environment. Tools: `splunk_get_indexes`, `splunk_get_metadata`, `splunk_get_info`, `splunk_get_kv_store_collections`, `splunk_run_query`, `splunk_get_index_info`

**Query Agent** — Writes and executes SPL queries. Tools: `splunk_run_query`, `splunk_get_knowledge_objects`

**Jira Ticket Agent** — Creates and updates Jira tickets. Tools: `jira_create_issue`

## Prerequisites

- Python 3.9+
- Node.js with `npx` available in `PATH` (used by `mcp-remote`)
- An [H2OGPTE](https://h2o.ai/platform/h2ogpte/) instance with API access
- A running Splunk instance with the MCP Server app installed
- A [Jira](https://www.atlassian.com/software/jira) instance with an [API token](https://id.atlassian.com/manage-profile/security/api-tokens)
- [mcp-atlassian](https://mcp-atlassian.soomiles.com/docs) (`uvx mcp-atlassian`)
- [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) to expose Splunk MCP and Atlassian MCP to H2OGPTE

> **First time?** See [SETUP.md](SETUP.md) for step-by-step instructions on setting up Splunk Enterprise, Atlassian MCP, and cloudflared locally.

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/justinsiowqi/splunk-agent.git
cd splunk-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

| Variable | Description |
|---|---|
| `H2OGPTE_API_KEY` | Your H2OGPTE API key |
| `H2OGPTE_ADDRESS` | H2OGPTE server URL (e.g. `https://your-instance.h2o.ai`) |
| `SPLUNK_HEC_TOKEN` | HEC token from Splunk app |
| `SPLUNK_HEC_URL` | URL pointing to Splunk HEC (port 8088) |
| `SPLUNK_HOST` | Splunk host address (default: `localhost`) |
| `SPLUNK_MGMT_PORT` | Splunk management port (default: `8089`) |
| `SPLUNK_USERNAME` | Splunk admin username |
| `SPLUNK_PASSWORD` | Splunk admin password |
| `SPLUNK_MCP_TOKEN` | Bearer token from Splunk MCP Server app |
| `SPLUNK_MCP_URL` | Cloudflare tunnel URL pointing to Splunk MCP |
| `JIRA_URL` | Your Jira instance URL (e.g. `https://your-instance.atlassian.net/`) |
| `JIRA_USERNAME` | Your Jira/Atlassian email |
| `JIRA_API_TOKEN` | Jira API token from [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |
| `JIRA_MCP_URL` | Cloudflare tunnel URL pointing to Atlassian MCP |
| `A2A_HOST` | A2A server host (default: `localhost`) |
| `A2A_PORT` | A2A server port (default: `8080`) |
| `SPLUNK_INVENTORY_AGENT_URL` | Inventory Agent URL (default: `http://localhost:8080`) |
| `SPLUNK_QUERY_AGENT_URL` | Query Agent URL (default: `http://localhost:8082`) |
| `JIRA_TICKET_AGENT_URL` | Jira Ticket Agent URL (default: `http://localhost:8084`) |

### 3. Start everything

```bash
./start.sh
```

This starts Splunk, Atlassian MCP, cloudflared tunnels, and all agents. The script automatically detects the cloudflared tunnel URLs and updates `.env` (`SPLUNK_MCP_URL` and `JIRA_MCP_URL`) before launching the agents.

Open http://localhost:8083 in your browser.

## Project Structure

```
splunk-agent/
├── src/
│   ├── agents/
│   │   ├── splunk_inventory_agent/    # Inventory Agent
│   │   │   ├── __main__.py            # A2A server entry point
│   │   │   ├── inventory_agent.py     # Inventory agent card definition
│   │   │   ├── inventory_executor.py  # A2A Inventory Agent Executor
│   │   │   └── run.py                 # Chat session and LLM querying
│   │   ├── splunk_query_agent/        # Query Agent
│   │   │   ├── __main__.py            # A2A server entry point
│   │   │   ├── query_agent.py         # Query agent card definition
│   │   │   ├── query_executor.py      # A2A Query Agent Executor
│   │   │   ├── schema.py              # Query request/response schemas
│   │   │   └── run.py                 # Chat session and LLM querying
│   │   ├── jira_ticket_agent/         # Jira Ticket Agent
│   │   │   ├── __main__.py            # A2A server entry point
│   │   │   ├── jira_agent.py          # Agent card definition
│   │   │   ├── jira_executor.py       # A2A Agent Executor
│   │   │   ├── schema.py              # Jira request/response schemas
│   │   │   └── run.py                 # Chat session and LLM querying
│   │   └── host_agent/                # Routing Agent (orchestrator + Gradio UI)
│   │       ├── __main__.py            # Gradio UI entry point
│   │       ├── routing_agent.py       # H2OGPTE-powered routing logic
│   │       ├── remote_agent_connection.py # A2A client connections
│   │       └── threat_hunt.py         # Multi-phase threat hunting workflow
│   ├── core/
│   │   ├── client.py                  # H2OGPTE client initialization
│   │   ├── config.py                  # YAML config loader
│   │   ├── prompt_loader.py           # System prompt loader
│   │   └── setup.py                   # Collection, ingestion, and tool registration
│   └── prompts/
│       ├── host_sys.md                # Routing agent system prompt
│       ├── inventory_sys.md           # Inventory agent system prompt
│       ├── inventory_message.md       # Inventory agent message template
│       ├── query_sys.md               # Query agent system prompt
│       ├── query_message.md           # Query agent message template
│       ├── ticket_sys.md              # Jira ticket agent system prompt
│       └── ticket_message.md          # Jira ticket agent message template
├── data/
│   ├── README.md                      # Data scripts usage guide
│   ├── ingest.py                      # Bulk-loads a dataset into Splunk
│   ├── replay.py                      # Streams a dataset into Splunk in real-time
│   └── delete.py                      # Deletes all events from a Splunk index
├── config/
│   ├── agents.yaml                    # Agent configuration (LLM, tools, temperature)
│   └── mcp_config.json                # Splunk MCP server configuration
├── start.sh                           # Start everything (Splunk, MCP, tunnels, agents)
├── run_agents.sh                      # Start agents only
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── SETUP.md                           # Splunk, Atlassian MCP & cloudflared setup guide
└── README.md
```

## License

MIT
